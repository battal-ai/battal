# S4: Türkçe injection tespiti

- Durum: kabul edildi
- Sürüm: 1.0.0
- İlgili ADR'ler: [ADR 0001](../decisions/0001-product-shape-and-licensing.md),
  [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0003](../decisions/0003-language-python-then-rust.md)
- İlgili backlog: E4 (PBI 4.1–4.3)
- Şema: `schemas/injection-rules.schema.json`
- Veri: `data/rules/injection.json`
- Test vektörleri: `testvectors/s4-injection/`
- Araştırma: [rapor §6.1](../research/index.md#61-baslangc-mvp-fine-tune-yok),
  [Ek 2](../research/ekler/02-models.md), [Ek 5](../research/ekler/05-eval-datasets.md)

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-18 | İlk taslak |
| 1.0.0 | 2026-11-18 | Kabul edildi |

## 1. Amaç ve kapsam

Bu spec, MVP'nin iki injection detector'ını tanımlar: deterministik imzalarla çalışan
`injection.rules` ve ONNX sınıflandırıcıyla çalışan `injection.model`. İmza dili, imza seti,
pencereleme, skorların detection'a dönüşmesi, model paketinin biçimi ve arıza davranışı burada
tanımlanır. Hangi detection'ın hangi eyleme yol açacağı policy'nin kararıdır (S5).

Kurallar tek başına zayıftır (rapor §6.1: keyword kurallarının F1'i 0.03–0.31); açıklanabilir bir
sinyal ve hızlı yoldur, sınıflandırıcının yerine geçmez. İmzalar bu yüzden recall değil precision
için yazılır.

**Kapsam dışı:**

- Model seçimi, eşik ve kalibrasyon yöntemi: E4.3'te ölçülür ve bir ADR ile kaydedilir. Bu
  spec'te ilgili değerler `TBD`'dir (§9).
- Benchmark (E7), fine-tune (E10), content safety ve jailbreak kategorileri (E16).
- Lisansı varsayılan imaja girmeyen modeller (örneğin Llama Prompt Guard 2) için "kullanıcı kendi
  ağırlığını getirir" adapter'ı (MVP sonrası).
- Kurumların kendi imzalarını bundle'da tanımlaması (sonraki sürüm).
- Dolaylı injection'a özgü davranış: `retrieval` ve `tool_result` checkpoint'leri MVP'de yoktur
  (S1-CHK-001).

## 2. Terimler

| Terim | Tanım |
|---|---|
| İmza | İmza setindeki, kimliği olan tek desen (`tr.ignore_instructions`) |
| Aile | İmzanın ait olduğu saldırı türü (`ignore_instructions`, `reveal_system`, `role_override`, `remove_restrictions`, `delimiter`) |
| Slot | Token imzasında bir konum için kabul edilen girdilerin listesi |
| Girdi | Bir slot'taki tek kelime ya da kelime dizisi (`yok saymani`, `=sistem`) |
| Pencere | Modelin tek seferde skorladığı, tokenizer token'larıyla ölçülen metin aralığı |
| Model paketi | `model.onnx`, tokenizer dosyaları ve `battal-model.json`'dan oluşan dizin |

Diğer terimler [sözlükteki](../sozluk.md) anlamlarıyla kullanılır.

## 3. Detector'lar

| Detector | Modül | Görünüm | Skor | Ek alanlar |
|---|---|---|---|---|
| `injection.rules` | `core/rules` | `match_ascii` | yok | `signature`, `encoding` |
| `injection.model` | `detectors` | `clean` | `raw_score` | `calibrated`, `threshold`, `model`, `truncated`, `encoding` |

Policy'de kullanım örneği (normatif değildir):

```yaml
rules:
  - id: inj.model_down_input
    checkpoints: [input]
    when: {detector_unavailable: injection.model}
    action: block
  - id: inj.model_high
    when: {all: [{detector: injection.model, above_threshold: true}, {trust: untrusted}]}
    action: block
  - id: inj.role_override
    when: {detector: injection.rules, signature: "*.role_override"}
    action: ask
```

## 4. İmza seti

İmza seti paketle gelen sabit veridir: `data/rules/injection.json`, şema
`schemas/injection-rules.schema.json`. Çalışma anında değiştirilmez (`docs/mimari.md` §3.1).

- **S4-DATA-001.** İmza dosyası şemaya uymalı, `version` alanı bu spec'in sürümüne eşit olmalı,
  imza kimlikleri benzersiz olmalıdır. Her imzanın en az bir pozitif ve en az bir negatif vektörü
  **MUST** bulunmalıdır. *[doğrulama: CI]*
- **S4-DATA-002.** Girdiler `match_ascii` biçiminde yazılır: küçük harf, `ı` yerine `i`,
  diakritiksiz (`gormezden gel`). Literal'ler küçük harfli yazdırılabilir ASCII'dir.
  *[doğrulama: şema]*
- **S4-DATA-003.** Türkçe fiiller kök öneki olarak değil, emir ve 2. kişi biçimleriyle
  **SHOULD** yazılmalıdır (`=yok say`, `=yok sayin`, `yok saymani`, `yok saymalisin`,
  `yok sayacaksin`). Böylece olumsuz biçimler (`yok sayma`, `unutmamalısın`) ayrıca
  dışlanmadan eşleşmez. Olumsuz emrin saldırı olduğu fiiller (`=dikkate alma`) açıkça listelenir.

| Aile | İmzalar (v1.0.0) |
|---|---|
| `ignore_instructions` | `tr.ignore_instructions`, `en.ignore_instructions`, `en.ignore_above` |
| `reveal_system` | `tr.reveal_system`, `en.reveal_system` |
| `role_override` | `tr.role_override`, `en.role_override`, `en.dan` |
| `remove_restrictions` | `tr.remove_restrictions`, `en.remove_restrictions` |
| `delimiter` | `any.delimiter` |

## 5. İmza dili

Eşleşme segment'in `match_ascii` görünümü (S2) üzerinde yapılır. **Token**, S3-CTX-001'deki gibi
`match_ascii` üzerinde S2-TOK-001'in karakter sınıfına uyan en uzun dizidir.

- **S4-SIG-001. Girdi.** Bir girdi tek boşlukla ayrılmış kelimelerden oluşur. `=` ile başlıyorsa
  bütün kelimeler token'a birebir eşit olmalıdır; aksi hâlde son kelime dışındakiler birebir, son
  kelime token'ın öneki olmalıdır (önek kelimesi en az 3 karakterdir, şema). Çok kelimeli bir
  girdinin ardışık token'ları arasında yalnızca satır sonu olmayan boşluk karakterleri
  (`White_Space`) bulunabilir; aksi hâlde girdi **MUST NOT** eşleşmemelidir.
- **S4-SIG-002. Slot.** Bir slot, bir token konumunda girdilerinden biri eşleşiyorsa eşleşir;
  birden fazla girdi eşleşiyorsa en çok token kapsayan alınır. Eşleşen girdinin son token'ı slot'un
  `except` listesindeki bir girdinin son kelimesiyle (aynı birebir/önek kuralıyla) eşleşiyorsa
  slot **MUST NOT** eşleşmemelidir.
- **S4-SIG-003. Sıralı eşleşme.** Bir imza, `i` konumunda ilk slot eşleşirse oradan başlar.
  Sonraki her slot, bir önceki slot'un bittiği token'dan itibaren en fazla `max_gap` (varsayılan
  3) token sonrasına kadar, en erken eşleştiği konumda aranır; bulunamazsa `i`'de eşleşme yoktur
  (geri izleme yapılmaz). Eşleşmenin span'i ilk slot'un ilk token'ının başından son slot'un son
  token'ının sonuna kadardır ve **MUST** offset haritasıyla orijinal metne eşlenmelidir.
- **S4-SIG-004. Cümle sınırı.** Bir slot aranırken önceki slot'un son token'ı ile aday token
  arasında `.`, `!`, `?`, `;`, LF ya da CR varsa arama o noktada durur; slot **MUST NOT**
  sınırın ötesinde eşleşmemelidir.
- **S4-SIG-005. Sırasız eşleşme.** `unordered: true` olan imza tam olarak iki slot içerir
  (şema). Her `i` konumunda önce verilen sıra, eşleşmezse ters sıra denenir.
- **S4-SIG-006. Veto.** `veto_before` listesi varsa, `i` konumundan hemen önceki en fazla iki
  token'dan biri listedeki bir girdiyle eşleşiyorsa `i`'de eşleşme **MUST NOT** başlamamalıdır
  (`do not ignore`, `don't forget`).
- **S4-LIT-001. Literal.** `kind: literal` imzalar `match_ascii` metninde alt dizgi olarak
  aranır: soldan sağa, her konumda eşleşen en uzun literal alınır, eşleşmeler çakışmaz, sınır
  koşulu yoktur (`### instruction`, `### instructions`'ı da kapsar). Span **MUST** orijinal
  metne eşlenmelidir.

İmza dili regex kullanmaz; Python ve Rust implementasyonu aynı algoritmayı izler ve geri izleme
olmadığı için çalışma süresi metin uzunluğuyla doğrusaldır (slot ve girdi sayısı sabittir).

## 6. Kural detection'ları

- **S4-DEC-001.** S2'nin her çözülmüş parçası (`decoded`), parçanın kendi `match_ascii`'si
  üzerinde bütün imzalarla taranır. Bulunan detection'ın span'i parçanın `span`'idir ve
  detection'a parçanın `encoding`'i **MUST** eklenmelidir.
- **S4-OUT-001.** Detection alanları: `detector` (`injection.rules`), `version` (bu spec'in
  sürümü), `segment`, `span`, `signature` ve yalnızca çözülmüş parçalarda `encoding`. Skor alanı
  yoktur. Detection eşleşen metni **MUST NOT** içermemelidir (S1-DET-001).
- **S4-OUT-002.** Bir imza bir metinde soldan sağa taranır; bir eşleşme bulunduğunda tarama
  eşleşmenin bittiği token'dan devam eder, yani aynı imzanın eşleşmeleri çakışmaz. Bir
  segment'in detection'ları span başlangıcı, span sonu, `signature` (code point sırası), ardından
  önce metin sonra çözülmüş parçalar (S2 sırasıyla) olacak biçimde **MUST** sıralanmalıdır.
- **S4-OUT-003.** Sıralamadan sonra segment başına en fazla `max_detections_per_segment` (imza
  dosyasında, 32) detection tutulur; fazlası **MUST** atılmalıdır. Policy için bir detection
  yeterlidir; sınır, yanıtın ve karar kaydının büyümesini önler.

## 7. Model detector'ı

### 7.1 Girdi

- **S4-MOD-005.** Model segment'in `clean` görünümünü (S2) skorlar; `match` ve `match_ascii`
  kullanılmaz, çünkü küçük harf ve leet katlaması modelin eğitildiği doğal metni bozar. Çözülmüş
  parçaların `text`'i ayrı girdiler olarak skorlanır. *[doğrulama: CI]*

### 7.2 Pencereleme

`injection.model.windows(token_count, window, stride, max_windows)`:

- **S4-WIN-001.** Token sayısı `n` 0 ise pencere yoktur. Aksi hâlde `k = 0, 1, …` için
  `[k·stride, min(k·stride + window, n))` pencereleri üretilir; sonu `n` olan ilk pencereden
  sonra durulur. Pencereler **MUST** bu algoritmayla üretilmelidir.
- **S4-WIN-002.** Pencere sayısı `max_windows`'u aşarsa ilk `max_windows` pencere skorlanır ve
  sonuçta `truncated` **MUST** `true` olmalıdır. Bütçe segment başınadır: önce metnin
  pencereleri, sonra çözülmüş parçaların pencereleri (S2 sırasıyla) aynı `max_windows` bütçesini
  kullanır.
- **S4-WIN-003.** `window < 1`, `stride < 1`, `stride > window` (pencereler arasında boşluk
  kalır) ya da `max_windows < 1` geçersizdir: fonksiyon **MUST** `INVALID_WINDOW_CONFIG` hatası
  vermeli, server başlarken 2 koduyla çıkmalıdır.
- **S4-WIN-004.** Pencerenin span'i, tokenizer'ın karakter offset'leriyle `clean` görünümünde
  bulunan aralığın S2 offset haritasıyla orijinal metne eşlenmiş hâlidir; çözülmüş parçanın
  pencerelerinde parçanın `span`'idir. *[doğrulama: CI]*

`truncated` bir saldırı yüzeyidir: uzun bir metnin sonuna konan saldırı skorlanmayabilir. Policy
bunu `{detector: injection.model, truncated: true}` koşuluyla (S5 1.1.0) yakalayabilir.
`max_windows` varsayılanı, S1'in `max_segment_code_points` sınırındaki bir segment kesilmeyecek
biçimde **SHOULD** seçilmelidir (E6.1).

### 7.3 Detection

`injection.model.aggregate(segment, model, windows, truncated)`:

- **S4-MOD-001.** `raw_score` pencere skorlarının en büyüğüdür; eşitlikte listedeki ilk pencere
  seçilir. Detection'ın `span`'i seçilen pencerenin span'idir. Bu kural **MUST** uygulanmalıdır.
- **S4-MOD-002.** En az bir penceresi olan her segment için, skor ne kadar düşük olursa olsun
  tam olarak bir detection **MUST** üretilmelidir; böylece policy `min_score` ile karar verir.
  Penceresi olmayan (boş) segment detection üretmez.
- **S4-MOD-003.** Seçilen pencere bir çözülmüş parçaya aitse detection'a parçanın `encoding`'i
  **MUST** eklenmelidir.
- **S4-MOD-004.** Detection alanları: `detector` (`injection.model`), `version` (model paketinin
  sürümü), `segment`, `span`, `raw_score`, `calibrated`, `threshold`, `model` (model kimliği),
  `truncated` (her zaman bulunur) ve gerekiyorsa `encoding`. Bu alanlar **MUST** bulunmalıdır.
- **S4-MOD-006.** `raw_score`, model çıktısının softmax'ında `battal-model.json`'daki
  `injection_label`'ın olasılığıdır. `calibrated` `false` iken skor olasılık olarak sunulmaz
  (S1-DET-002). *[doğrulama: CI, `model` etiketli testler]*

### 7.4 Arıza

- **S4-MOD-007.** Model paketi yüklenirken `model.onnx` ve tokenizer dosyalarının SHA-256'sı
  `battal-model.json`'daki değerlerle karşılaştırılır. Eşleşmezse ya da paket okunamazsa model
  yüklenmez; her istekte `injection.model` detector'ı çalışmamış sayılır (`detector_failures`,
  `degraded: true`, S5-RUL-008) ve hata loglanır. *[doğrulama: CI]*
- **S4-MOD-008.** Inference hata verirse ya da `model_timeout_ms` aşılırsa o istek için
  `injection.model` çalışmamış sayılır; `injection.rules` etkilenmez. *[doğrulama: CI]*

### 7.5 Model paketi

`battal-model.json`:

| Alan | Açıklama |
|---|---|
| `id`, `version` | Model kimliği ve paket sürümü |
| `license` | SPDX kimliği |
| `source` | Ağırlıkların kaynağı ve commit'i |
| `files` | `{dosya adı: "sha256:<hex>"}` |
| `labels`, `injection_label` | Sınıf adları ve injection sınıfının adı |
| `window`, `stride`, `max_windows` | §7.2 |
| `threshold`, `calibrated` | Varsayılan eşik ve kalibrasyon durumu |

- **S4-PKG-001.** Paket bu alanları **MUST** içermelidir; eksik alanlı paket yüklenmez
  (S4-MOD-007). *[doğrulama: CI]*
- **S4-LIC-001.** Varsayılan imaja yalnızca `license` alanı `MIT` ya da `Apache-2.0` olan model
  paketi **MUST** girmelidir (ADR 0001). Adaylar: halilneed v2 (MIT), wolf-defender (Apache-2.0),
  proventra mDeBERTa (MIT). *[doğrulama: CI, imaj üretimi]*

## 8. Hata ve sınır durumları

| Durum | Davranış | Gereklilik |
|---|---|---|
| Boş segment | Kural ve model detection'ı yok | S4-OUT-002, S4-MOD-002 |
| Çok sayıda eşleşme | İlk 32 kural detection'ı | S4-OUT-003 |
| Uzun segment | İlk `max_windows` pencere, `truncated: true` | S4-WIN-002 |
| Kodlanmış saldırı | Çözülmüş parça taranır, `encoding` alanı | S4-DEC-001, S4-MOD-003 |
| Model paketi bozuk | Model çalışmaz, `degraded` | S4-MOD-007 |
| Inference hatası ya da timeout | O istekte model çalışmaz | S4-MOD-008 |
| Geçersiz pencere ayarı | `INVALID_WINDOW_CONFIG`, server başlamaz | S4-WIN-003 |

**Bilinen sınırlar** (imzalar precision için yazılmıştır; bunlar model ve benchmark'ın işidir):

- Listede olmayan çekimler (`yok sayar mısın`), eş anlamlı yeniden ifade ve İngilizce/Türkçe
  dışındaki diller eşleşmez.
- Harfleri boşlukla ayrılmış yazım (`i g n o r e`) eşleşmez.
- İngilizcede olumsuzluk yalnızca `veto_before` ile, Türkçede yalnızca listelenen biçimlerle
  ayırt edilir.
- `delimiter` ailesi işaretten bahseden belgeleri de yakalar (`Kullanım: [INST] etiketi`); bu
  ailenin policy'de daha hafif bir eyleme (`ask`) bağlanması önerilir.
- Sıralı eşleşme geri izleme yapmaz (S4-SIG-003); bir slot'un daha geç bir eşleşmesiyle
  tamamlanabilecek nadir dizilimler kaçabilir.

## 9. Ölçüm bekleyen değerler

| Değer | Durum | Nasıl belirlenecek |
|---|---|---|
| Varsayılan model | TBD | E4.3 ölçümü ve ADR |
| `threshold`, `calibrated` | TBD | E4.3 kalibrasyonu (temperature scaling) |
| `window`, `stride` | TBD | E4.2; modelin bağlam uzunluğu (512–2048) |
| `max_windows` | TBD | E6.1 yük testi, S1 sınırlarıyla birlikte |
| `model_timeout_ms` | TBD | E6.1 p99 ölçümü |

## 10. Normatif örnekler (vektörler)

| Suite | Function | Ne test eder |
|---|---|---|
| `s4-injection/rules-tr.json` | `injection.rules.detect` | Türkçe imzalar, zor negatifler, cümle sınırı |
| `s4-injection/rules-en.json` | `injection.rules.detect` | İngilizce imzalar, veto, literal'ler, çözülmüş parçalar, sıralama, üst sınır |
| `s4-injection/model-windows.json` | `injection.model.windows` | Pencereleme |
| `s4-injection/model-aggregate.json` | `injection.model.aggregate` | Pencere skorlarından detection |

- `injection.rules.detect`: `input` = `{"text"}` (tek segment, `segment` = 0); çıktı
  `{"detections"}`. Paketle gelen imza dosyası kullanılır.
- `injection.model.windows`: `input` = `{"token_count", "window", "stride", "max_windows"}`;
  çıktı `{"windows", "truncated"}`.
- `injection.model.aggregate`: `input` = `{"segment", "model": {"id", "version", "threshold",
  "calibrated"}, "windows": [{"span", "score", "encoding"?}], "truncated"}`; çıktı
  `{"detections"}`.

Gerçek model çıktıları dilden bağımsız vektörlerle test edilmez: ONNX Runtime sürümleri ve
donanım arasında küçük sayısal farklar olur. Bunlar CI'da ayrı job'da, toleranslı `model`
etiketli testlerle koşar.

## 11. Uyumluluk

- İmza ya da girdi eklemek minor, imza ya da girdi çıkarmak ve eşleşme kurallarını (§5)
  değiştirmek major sürümdür; kural detection'larının `version` alanı değişir.
- Model paketinin değişmesi bu spec'in sürümünü değiştirmez; model detection'ının `version` ve
  `model` alanları değişir. Varsayılan modelin değişmesi bir ADR gerektirir.
- Rust motoru `injection.rules`'u (`core/rules`) uygular; `injection.model` ONNX Runtime ile
  Python'da kalır (`docs/mimari.md` §3.2).
