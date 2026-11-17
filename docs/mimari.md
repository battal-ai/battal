# Mimari

Bu belge Battal'ın bileşenlerini, Python paketinin modüllerini ve modüller arasındaki bağımlılık
kurallarını tanımlar. Kodla birlikte güncellenir. Rapordaki
[referans mimari](research/index.md#4-referans-mimari) tarihî belgedir; bu belge onun güncel ve
bağlayıcı hâlidir. Terimler [sözlükteki](sozluk.md) anlamlarıyla kullanılır.

!!! note "Durum"
    Taslak. Modül haritası E0 ve E1 ile kesinleşecek. Her modülün davranışı ilgili spec'te
    tanımlanır; bu belge yalnızca modüllerin yerini ve ilişkilerini gösterir.

## 1. Sistem bağlamı

```text
  Kullanıcı / uygulama
          │
          ▼
  ┌───────────────┐   pre_call / post_call    ┌───────────────────┐
  │ AI gateway    │ ────────────────────────► │                   │
  │ (LiteLLM)     │ ◄──────── decision ────── │                   │
  └───────┬───────┘                           │                   │
          │                                   │      Battal       │──► Karar kaydı
          ▼                                   │                   │    (log / SIEM)
  ┌───────────────┐                           │                   │
  │ Model sunucusu│   IDE ve agent hook'ları  │                   │◄── Bundle dosyaları
  └───────────────┘   (faz 2) ──────────────► │                   │    (git)
                                              └─────────┬─────────┘
                                                        │ opsiyonel adapter
                                                        ▼
                                              Büyük LLM guard'lar
                                              (kullanıcının vLLM/Ollama'sı)
```

- Battal proxy değildir: trafik Battal'ın üzerinden geçmez, gateway ve hook'lar Battal'ı çağırır.
- Battal kimlik doğrulamaz; principal bilgisini çağırandan alır.
- Battal dışarıya yalnızca karar kaydını yazar. Opsiyonel LLM guard adapter'ları dışında karar
  anında başka bir servise gitmez.

## 2. Container'lar

| Container | Ne | Nasıl çalışır | Spec |
|---|---|---|---|
| SDK | `battal` Python paketi | Çağıranın sürecinde (in-process) | S1 |
| Battal Server | `battal[server]`; FastAPI, `/v1/evaluate` ve LiteLLM route'u | Container / Helm | S6 |
| CLI | `battal policy validate / test / diff`, `battal serve` | Komut satırı | S5, S6 |
| Playground | `battal serve --playground`; yalnızca `127.0.0.1` | Server içinde, varsayılan kapalı | E18 (MVP sonrası) |

SDK ile Server aynı `evaluate()` fonksiyonunu çalıştırır. Server, SDK'nın üzerine HTTP ve
adapter katmanı ekler; kendi karar mantığı yoktur.

## 3. Modüller

Önerilen paket yapısı:

```text
battal/
├── contract/      EvaluationRequest/Response tipleri, hata kodları          S1
├── core/          Deterministik çekirdek (Rust'a taşınacak sınır)
│   ├── normalize/   görünümler, sinyaller, offset haritası, decoder'lar      S2
│   ├── pii/         checksum'lar, tanıyıcılar, bağlam skoru                  S3
│   ├── rules/       injection kural seti (deterministik kısım)               S4
│   ├── policy/      rule değerlendirme, binding eşleşmesi, birleştirme       S5
│   └── actions/     maskeleme ve transform üretimi                           S3, S5
├── detectors/     Model tabanlı detector'lar (ONNX), pencereleme            S4
├── pipeline/      evaluate(): normalize → detector'lar → policy → action
│                  zaman ölçümü, degraded karar, fail mode uygulaması         S1, S5
├── bundle/        Bundle yükleme, doğrulama, hot reload (dosya I/O)          S5
├── audit/         Karar kaydı üretimi ve yazımı                             S7
├── server/        FastAPI uygulaması (extra: [server])                      S6
├── adapters/      litellm (MVP); claude_code, hermes, fms (faz 2)           S6
├── cli/           battal komutları                                          S5, S6
└── testing/       Test vektörü runner'ı ve function registry'si             S0
```

### 3.1 Deterministik çekirdek

`battal.core` saf fonksiyonlardan oluşur (ADR 0003):

- global state yoktur, I/O yoktur, saat ve rastgelelik kullanılmaz;
- girdi ve çıktı `battal.contract` tipleri ya da çekirdeğin kendi değer tipleridir;
- davranışı tamamen S2, S3, S4 (kural kısmı) ve S5 vektörleriyle tanımlıdır;
- statik veri tabloları (örneğin `data/unicode/confusables-fold-15.1.0.json`) paketle birlikte
  gelen sabitlerdir: Python'da paket verisi olarak bir kez yüklenir, Rust'ta derleme anında
  gömülür (`include_str!`). Çalışma anında dosya sisteminden okunmaz ve config ile değiştirilmez.

Çekirdeğin dış bağımlılıkları bilinçli olarak az tutulur: Unicode Script özelliği için `regex`
(Python) / `unicode-script` (Rust), NFKC için standart kütüphane (Python) /
`unicode-normalization` (Rust). ICU, deasciifier ve mojibake onarımı kullanılmaz (S2 §1).

Rust `battal-core` (E11) bu modülün yerine geçer. Seam, `battal.core`'un public interface'idir;
Python ve Rust motorları aynı interface'i aynı vektörlerle karşılar ve config ile seçilir.

### 3.2 Çekirdeğin dışında kalanlar

- **Model inference** (`detectors`): ONNX Runtime zaten native çalıştığı için Rust'a taşınmaz.
- **I/O** (`bundle`, `audit`, `server`): dosya, ağ ve saat bu modüllerde kalır.
- **Orkestrasyon** (`pipeline`): zaman ölçümü ve hata yakalama burada yapılır; çekirdek
  fonksiyonları zaman ve hata durumunu parametre olarak alır.

## 4. Bağımlılık kuralları

Oklar "import edebilir" anlamına gelir; listede olmayan yön yasaktır.

```text
contract ◄── core ◄── detectors ◄── pipeline ◄── server, adapters, cli
   ▲          ▲                        ▲
   └──────────┴──── bundle, audit ─────┘
testing ──► (her modülün public interface'i; üretim kodu testing'i import etmez)
```

- `core` yalnızca `contract`'ı import eder.
- `detectors` `core` ve `contract`'ı import eder; `pipeline`'ı import etmez.
- `pipeline` bir bundle'ı parametre olarak alır; dosyadan okumaz (okuma `bundle`'ın işidir).
- `server`, `adapters` ve `cli` yalnızca `pipeline`, `bundle`, `audit` ve `contract`'ı kullanır;
  `core`'un iç modüllerine doğrudan erişmez.
- Hiçbir modül `server`'ı import etmez. Server bağımlılıkları (FastAPI vb.) `[server]` extra'sında
  kalır; SDK onlarsız kurulabilir.
- Enterprise özellikleri bu pakete eklenmez; yalnızca extension point bırakılır (ADR 0001).

Bu kurallar kod geldiğinde CI'da bir import denetimiyle (örneğin `import-linter`) zorunlu
hâle getirilir.

## 5. MVP kapsamındaki detector'lar

MVP yalnızca deterministik ve küçük model tabanlı tespit içerir:

| Detector | Yöntem | Modül |
|---|---|---|
| TCKN, VKN, IBAN, telefon, e-posta | Regex, checksum, bağlam sözlüğü | `core/pii` |
| Injection kuralları | TR ve EN imzalar, stem, n-gram | `core/rules` |
| Injection sınıflandırıcı | Küçük ONNX model (CPU) | `detectors` |

İsim ve adres tanıma (NER, örneğin spaCy ile) MVP'de yoktur; E17'de, model lisansı ve CPU
doğruluğu değerlendirildikten sonra eklenir. Presidio Battal'ın bir bağımlılığı değildir;
Presidio kullananlar için isteğe bağlı bir adapter E17'de gelir (ADR 0006).

## 6. Spec eşlemesi

| Modül | Davranışı tanımlayan spec |
|---|---|
| `contract` | [S1](spec/s1-evaluation-api.md) |
| `core/normalize` | [S2](spec/s2-turkce-normalizasyon.md) |
| `core/pii`, `core/actions` | [S3](spec/s3-turkce-pii.md) |
| `core/rules`, `detectors` | S4 |
| `core/policy`, `bundle`, `cli` | [S5](spec/s5-policy-binding-bundle.md) |
| `server`, `adapters` | [S6](spec/s6-sunucu-litellm.md) |
| `audit` | [S7](spec/s7-karar-kaydi.md) |
| `testing` | [S0](spec/s0-test-vektorleri.md) |
