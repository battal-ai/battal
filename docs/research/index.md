# Battal araştırma raporu (v0.1)

- Tarih: 2026-11-16
- Okuyucu: Açık kaynak katkıcılar ve Battal'ı benimsemeyi değerlendiren kurumların mühendislik,
  güvenlik ve mimari ekipleri.
- Kapsam: Hangi açık kaynak bileşenler kullanılacak, hangi eksikler kendi mühendisliğimizle
  tamamlanacak ve bu yetenekler gateway, code studio ve agent sistemlerine bağlanan ortak bir
  güvenlik platformuna nasıl dönüştürülecek.
- Yöntem: Altı paralel araştırma. Bakım ve lisans bilgileri 2026-11-16'da canlı olarak kontrol
  edildi (GitHub API, PyPI, Hugging Face API). Entegrasyon iddiaları kaynak koduna permalink ile
  bağlandı. Kaynaklı ayrıntıların tamamı [eklerdedir](#ekler).

!!! note "İddiaların etiketlenmesi"
    Bu raporda **geliştirici beyanı**, **bağımsız ölçüm** ve **bizim çıkarımımız** ayrı tutulur.
    Ölçülmemiş hız, maliyet veya doğruluk rakamı verilmez. "Hedef" olarak işaretlenen sayılar ölçüm
    değil, öneridir. Lisans ve mevzuat yorumları hukuki görüş değildir.

---

## Yönetici özeti

**Sorun.** Türkçe için kullanılabilir bir LLM güvenlik katmanı yok. Değerlendirilen guardrail
framework'lerinin hiçbirinde açık bir Türkçe desteği kanıtı bulunmuyor. Büyük üreticilerin guard
modellerinde de Türkçe sonuçlar ayrıca raporlanmıyor: Prompt Guard 2, Llama Guard 3/4 ve Nemotron
Safety Guard'ın dil listelerinde Türkçe yok. Granite Guardian'ın model kartında "only trained and
tested on English" yazıyor. Qwen3Guard Türkçeyi yalnızca 30 dilin ortalaması içinde raporluyor.
Çok dilli injection sınıflandırıcıları Türkçe saldırıları iyi yakalıyor, ama talimata benzeyen
zararsız Türkçe metinlerin **%60–77'sini** yanlışlıkla işaretliyor (üçüncü taraf ölçümü, küçük
örneklem). Herkese açık, yeniden üretilebilir bir Türkçe injection benchmark'ı da yok.

**Ne geliştiriyoruz.** Battal, gateway'lerin, code studio'ların ve agent runtime'ların çağırdığı,
self-hosted, CPU'da çalışan bir **evaluation service** ve SDK'dır. Ürün; Türkçe-farkında bir
normalizasyon çekirdeği, Türkçe PII tespiti ve maskeleme, Türkçe ve Türkçe–İngilizce karışık
prompt injection tespiti ve deterministik policy uygulamasını tek bir API sözleşmesi arkasında
birleştirir. Battal bir proxy değildir.

**Temel bulgular.**

1. **Orkestrasyonu kendimiz yazmalıyız.** LLM Guard 2026'da arşivlendi. Guardrails AI, Hub'ını
   Ağustos 2026'da kapattı. LlamaFirewall durgun. NeMo Guardrails ise LLM-merkezli ve telemetri
   gönderiyor. Hiçbiri "CPU-first + Türkçe + stateless API" bileşimini sağlamıyor.
2. **LiteLLM entegrasyonu için kod PR'ı gerekmiyor.** LiteLLM'in `generic_guardrail_api`
   sözleşmesi engelleme, maskeleme, tool call'lar, kimlik bilgileri ve hata davranışını zaten
   taşıyor. Battal bu sözleşmeyi uygulayan bir endpoint sunar. Kısıt: endpoint `/beta/` altında
   duruyor, bu yüzden LiteLLM sürümü pinlenmeli ve contract test yazılmalı.
3. **Normalizasyon ürünün kendisi.** Presidio'nun 2026'da eklediği TCKN tanıyıcısı bile
   `10000000146dır`, gruplu yazım, tam genişlikli rakam ve sıfır genişlikli boşlukla bölünmüş
   TCKN'yi kaçırıyor (bizim ölçümümüz). UTS #39 confusables tablosu `ı→i` ve `I→l` eşlemesi
   yapıyor, bu yüzden naif uygulanırsa Türkçe metni bozuyor.
4. **Türkçe kalite farkı ince ayardan gelir.** Hard-negative'lerle eğitilmiş, kendi Apache-2.0
   Türkçe injection modelimiz ikinci aşamanın asıl yatırımıdır. Llama, Gemma ve NVIDIA lisanslı
   modeller ne varsayılan olarak gömülür ne de distillation öğretmeni olarak kullanılır.
5. **Uyum açısından en güçlü Türkiye dayanağı KVKK'nın üretken yapay zekâ rehberi** (Kasım 2025).
   Rehber; prompt injection ve jailbreak'e karşı teknik kontrolleri, red teaming'i ve denetlenebilir
   kayıtları iyi uygulama olarak sayıyor. EU AI Act'te Ek III kapsamındaki yüksek riskli sistem
   yükümlülükleri 2 Aralık 2027'ye ertelendi (Regulation (EU) 2026/1744).

**Net mühendislik kararı** (ayrıntısı [Karar](#karar) bölümünde):

> **Temel olarak** ONNX Runtime, Presidio (yalnızca orkestratör), phonenumbers ve LiteLLM'in
> Generic Guardrail API'si kullanılır. Değerlendirme aracı Inspect + promptfoo, saldırı varyantı
> üretimi PyRIT converter'ları, ikinci fazda policy engine olarak Cedar seçilir. **Kendi
> yatırımımız** Türkçe normalizasyon çekirdeği, Türkçe PII tanıyıcıları, Türkçe injection modeli ve
> herkese açık Türkçe benchmark'tır. **İlk sürüm** yalnızca LiteLLM'e bağlanır; input'ta Türkçe
> injection tespiti, input ve output'ta TCKN/IBAN/telefon/e-posta maskeleme yapar ve CPU'da çalışır.
> **Doğrulama** template-family split'li Türkçe benchmark, dış test setleri ve fail-open testleriyle
> yapılır. **Diğer platformlara** Claude Code `PreToolUse` hook'u, Hermes Agent `pre_tool_call`
> plugin'i, FMS Detector API ve MCP gateway adapter'larıyla bağlanılır.

---

## 1. Ürün önerisi

**Kimin hangi sorununu çözüyoruz?**

| Kullanıcı | Sorun | Battal'ın yanıtı |
|---|---|---|
| LLM'i kendi altyapısında çalıştıran kurum (platform ekibi) | Gateway'den geçen Türkçe trafikte injection ve kişisel veri sızıntısını görememek; hazır guard'ların Türkçede ya kaçırması ya yanlış alarm vermesi | Gateway'e tek satır config ile eklenen, Türkçe-farkında guard |
| Güvenlik ve uyum ekibi | Kararların neden verildiğini gösteren, ham veriyi saklamayan kanıt eksikliği | Skor, policy kararı ve gerekçenin ayrıldığı, sürümlenen karar kayıtları |
| Agent ve code studio kullanan geliştirici ekipleri | Tool call'ların ve tool sonuçlarının denetlenmemesi | Aynı API'yi kullanan Claude Code, Hermes ve MCP adapter'ları (ikinci fazdan itibaren) |
| Türkçe NLP topluluğu | Yeniden üretilebilir Türkçe güvenlik benchmark'ının olmaması | CC-BY-4.0 lisanslı Türkçe benchmark ve açık temel model |

**Battal'ın yapmadıkları.** Kimlik doğrulama, yetkilendirme, sandbox ve ağ kısıtlamalarının yerine
geçmez (bkz. [§4.2](#42-guven-snrlar-ve-model-tabanl-tespitin-snr)). LLM proxy'si değildir.
Uyum sertifikası vermez.

---

## 2. Açık kaynak bileşen karşılaştırması

Ayrıntılar: [Ek 1](ekler/01-frameworks-policy.md), [Ek 2](ekler/02-models.md),
[Ek 3](ekler/03-pii-secrets-turkish.md), [Ek 5](ekler/05-eval-datasets.md).

### 2.1 Seçilen bileşenler

| Kategori | Bileşen | Lisans | Karar | Gerekçe |
|---|---|---|---|---|
| Inference runtime | ONNX Runtime (int8) | MIT | **Hazır kullan** | CPU-first; model ve dil bağımsız |
| PII orkestrasyonu | Presidio analyzer/anonymizer (2.2.366, artık `data-privacy-stack` altında) | MIT | **Yapılandır + adapter** | Recognizer registry ve anonymizer olgun. Türkçe tanıyıcıları kendimiz yazıyoruz, çünkü upstream TCKN tanıyıcısı varsayılan olarak kapalı ve normalize edilmemiş girdide kaçırıyor |
| Telefon | phonenumbers | Apache-2.0 | **Hazır kullan** | TR mobil desenleri; operatör çıkarımı yapılmaz (numara taşınabilirliği) |
| Checksum'lar (TCKN, VKN, IBAN, Luhn) | Kendimiz | Apache-2.0 | **Kendimiz geliştir** | Her biri 30 satırdan az. python-stdnum (LGPL) yalnızca test oracle olarak kullanılır |
| Türkçe metin | turkish-deasciifier (Public Domain, vendor), snowballstemmer (BSD) | PD / BSD | **Hazır kullan** | Zemberek JVM gerektirdiği için MVP'de yok |
| Injection sınıflandırıcı (baseline) | halilneed TR classifier v2 (MIT), wolf-defender small/edge (Apache-2.0, ONNX hazır), proventra mDeBERTa (MIT) | MIT / Apache | **Yapılandır, sonra ölç ve seç** | Türkçe ölçümü olan tek açık modeller. Kendi eval setimizde ölçülüp kalibre edilecek, kazanan paketlenecek |
| Fine-tune tabanı | mmBERT-small/base (MIT), TabiBERT (Apache-2.0) | MIT / Apache | **Fine-tune et (faz 2)** | Lisans temiz, 8K bağlam, ONNX'e aktarılabilir |
| Distillation öğretmeni | Qwen3Guard-Gen-8B, gpt-oss-safeguard-20b | Apache-2.0 | **Adapter + öğretmen** | Lisans zinciri temiz |
| Gateway entegrasyonu | LiteLLM `generic_guardrail_api` | MIT (LiteLLM core) | **Hazır kullan** | PR gerektirmeyen sözleşme |
| İkinci entegrasyon yüzeyi | FMS Detector API (LiteLLM `ibm_guardrails`) | Apache-2.0 | **Adapter geliştir (P1)** | OpenShift AI / TrustyAI ekosistemi |
| Policy (MVP) | Kendi YAML evaluator'ımız | Apache-2.0 | **Kendimiz geliştir** | MVP kuralları (eşik → eylem) için Rego veya Cedar gereksiz karmaşıklık |
| Tool-call authorization | Cedar (`cedarpy`) + `cedar-for-agents` | Apache-2.0 | **Yapılandır + adapter (faz 2)** | In-process, şema doğrulama, biçimsel analiz, MCP şema üretici. Risk: `cedarpy` topluluk paketi |
| Eval harness | Inspect (MIT), promptfoo (CI), PyRIT converter'ları | MIT | **Hazır kullan** | Yeniden üretilebilir loglar; deterministik varyant üretimi |
| Secret detection | gitleaks kural TOML'u (MIT, 222 kural) | MIT | **Adapter (faz 2)** | Python `regex` ile yüklenir. TruffleHog AGPL olduğu için dışarıda |

### 2.2 Elenen alternatifler

| Alternatif | Neden elendi |
|---|---|
| Protect AI LLM Guard / Rebuff | Arşivlendi; PI modeli yalnızca İngilizce |
| NeMo Guardrails | LLM-in-the-loop; Colang; telemetri varsayılan olarak açık; Türkçe yok. Rail kategorileri ve fail-closed yaklaşımı tasarım referansı olarak alındı |
| Guardrails AI | Hub kapatıldı; Türkçe validator yok; rakip konumda bir orkestratör |
| LlamaFirewall | Mayıs 2025'ten beri release yok; torch bağımlılığı ağır; Llama lisanslı ağırlıklar |
| OpenGuardrails | Node CLI'ya pivot etti; orijinal Hugging Face modelleri kaldırıldı |
| Llama Prompt Guard 2 (varsayılan olarak) | Türkçe değerlendirilmemiş; gated; Llama 4 lisansı ("Built with Llama", türev model adı "Llama" ile başlamalı). **Kullanıcı kendi ağırlığını getirir** şeklinde adapter olarak kalıyor |
| Llama Guard 4 | Llama 4 kullanım politikası, multimodal modeller için AB'de yerleşik kurumlara hak tanımıyor |
| ShieldGemma / Nemotron 3.5 (öğretmen olarak) | Gemma şartları, çıktılarıyla eğitilen modelleri türev sayıyor |
| TruffleHog | AGPL-3.0 |
| OPA (varsayılan olarak) | Python için resmî in-process yol yok. Kurumsal müşteriler için opsiyonel sidecar adapter olarak kalıyor (P2) |
| OpenFGA / SpiceDB / Casbin | Ayrı servis gerektiriyor ya da şema doğrulaması zayıf |
| Lisanssız, NC veya SA lisanslı veri setleri | Ayrıntısı §6.3'te |

!!! warning "Kod, ağırlık ve veri ayrı lisanslanır"
    Battal kodu Apache-2.0'dır. Bu, varsayılan imaja yalnızca Apache-2.0 veya MIT lisanslı ağırlıklar
    girmesi anlamına gelir. Llama, Gemma, NVIDIA Open Model License ve Elastic lisanslı modeller
    yalnızca adapter olarak desteklenir; kullanıcı ağırlığı kendisi indirir.

---

## 3. Bizim katkımız

| Alan | Açık kaynak temel | Kendi geliştirmemiz | Beklenen fayda | Doğrulama yöntemi |
|---|---|---|---|---|
| Türkçe normalizasyon | Python `unicodedata` (NFKC), Unicode confusables.txt, deasciifier, snowball | Offset haritasını koruyan çoklu görünüm pipeline'ı (`orig`, `v_pii`, `v_match`, `v_decoded`). Türkçe-farkında casing ve confusable katlama (`ı/İ/I/i` istisnalı). Tag, zero-width ve bidi tespiti; base64/hex/rot çözme | Obfuscation ile yapılan bypass'ları kapatır; bulgular orijinal metne doğru konumla geri eşlenir | Dilden bağımsız JSON test vektörleri; obfuscation fuzz seti (aynı saldırının N varyantı); offset round-trip testleri |
| Türkçe PII | Presidio registry, phonenumbers | Ek ve kesme işareti toleranslı TCKN/IBAN/telefon tanıyıcıları; bağlam kelimesi ile skor; checksum'lar; telekom tanımlayıcıları (MSISDN/IMSI/ICCID/IMEI, faz 2) | Kaçırma oranının sıfıra yaklaşması ve düşük over-mask | Checksum'ı geçerli pozitifler + checksum'ı geçersiz distractor'lar; dış test: `cagrigungor` (CC0) |
| Türkçe injection | Baseline modeller, mmBERT/TabiBERT | Yüksek precision'lı TR+EN kurallar; eşik kalibrasyonu; faz 2'de hard-negative'lerle fine-tune edilmiş Apache-2.0 model | Hard-benign FPR'de büyük düşüş (asıl risk meşru talimatların engellenmesi) | Template-family split'li benchmark; TPR@FPR=%1; ECE; dış test setleri |
| Policy ve karar | — | YAML policy (ilerleyen fazda Cedar); checkpoint bazında fail-open/closed; sürümlü kararlar | Kararlar açıklanabilir, test edilebilir ve geri alınabilir | Policy birim testleri; karar kaydı replay'i |
| Kanıt | — | Ham içerik yerine hash, span offset, dedektör ve policy sürümü içeren karar kaydı | KVKK rehberi, AI Act Art. 12 ve BTK m.6(4) beklentilerine katkı | Kayıtlarda ham PII taraması; iz sürme tatbikatı |
| Türkçe benchmark | Inspect, PyRIT, datasketch, LaBSE/e5 | Türkçe-native şablon aileleri, hard-negative taksonomisi, aile bazlı split | Alandaki ilk yeniden üretilebilir Türkçe benchmark; benimsenme kaldıracı | Contamination raporu (test↔train en yakın komşu = 0) |

---

## 4. Referans mimari

### 4.1 Bileşenler ve kontrol noktaları

```text
                    ┌─────────────────────── Güven sınırı: kurum ağı ─────────────────────────┐
 Kullanıcı / IDE /  │                                                                          │
 Agent runtime ─────┼──► AI Gateway (LiteLLM) ──── pre_call ────┐                              │
                    │        │   ▲                             ▼                              │
                    │        │   └──── post_call ◄──── ┌─────────────────────┐                │
                    │        │                         │   Battal Server     │                │
                    │        ▼                         │  (FastAPI, ileride  │                │
                    │   Model sunucusu (vLLM vb.)      │   Rust motoru)      │                │
                    │                                  │                     │                │
 Agent runtime ─────┼── pre_tool_call / PreToolUse ──► │ Adapter katmanı     │                │
 (Hermes, Claude    │◄─ block / ask / modify ───────── │  litellm_generic    │                │
  Code)             │                                  │  fms_detector       │                │
                    │                                  │  claude_code_hook   │                │
 MCP gateway ───────┼── pre/post_mcp_call ───────────► │  hermes_plugin      │                │
                    │                                  ├─────────────────────┤                │
                    │                                  │ evaluate()          │                │
                    │                                  │  1 normalize (views)│                │
                    │                                  │  2 detectors ──────►│ ONNX modelleri │
                    │                                  │  3 policy engine    │ (yerel)        │
                    │                                  │  4 actions          │                │
                    │                                  │  5 decision record ─┼─► Audit/SIEM   │
                    │                                  └─────────────────────┘                │
                    │   Control plane (policy paketleri, model sürümleri) ──► imzalı bundle   │
                    └──────────────────────────────────────────────────────────────────────────┘
       Opsiyonel: büyük LLM guard'lar (Qwen3Guard-8B, Llama Guard...) kullanıcının vLLM/Ollama'sında, adapter ile
```

**Kontrol noktaları (checkpoint):** `input`, `output`, `retrieval`, `tool_call`, `tool_result`,
`memory_write`. MVP'de yalnızca `input` ve `output` uygulanır. Çekirdek interface'ler en baştan
altısını da kabul eder (ADR 0002).

**Control plane ile real-time denetim birbirinden ayrıdır.** Policy ve model sürümleri imzalı
paketler hâlinde dağıtılır. Data plane yalnızca yüklü paketlerle karar verir, karar anında control
plane'e gitmez. Bu sayede control plane çökerse data plane son geçerli paketle çalışmaya devam eder.
Çok kiracılı merkezî yönetim, ileride gelecek enterprise sürüm için ayrılmış bir alandır
(ADR 0001); açık çekirdekte yalnızca dosya veya bundle tabanlı yükleme vardır.

### 4.2 Güven sınırları ve model tabanlı tespitin sınırı

Model tabanlı tespit **olasılıksaldır ve atlatılabilir**. Aşağıdaki kontrollerin yerine geçmez.
Battal'ın mimarideki yeri bunlara ek bir katmandır:

| Kontrol | Nerede uygulanır | Battal'ın rolü |
|---|---|---|
| Kimlik doğrulama | Gateway (LiteLLM key'leri), IdP | Kimliği **tüketir** (`principal`); doğrulamaz |
| Yetkilendirme (kim hangi modeli ya da tool'u kullanır) | Gateway, agent runtime, MCP sunucusu (OAuth) | Faz 2'de Cedar ile tool-call kararı **önerir**. Enforcement yine runtime'daki hook'tadır |
| Sandbox / süreç izolasyonu | Agent runtime, container, OS | Yok. Terminal komutlarını analiz edebilir, ama sandbox değildir |
| Ağ çıkışı kısıtlaması (egress) | Firewall, service mesh, egress gateway | Policy'de egress kararı verebilir; ağ katmanının yerine geçmez |
| Deterministik kurallar | Battal policy engine | Birincil karar katmanı; model skorları burada yalnızca bir girdidir |

### 4.3 Korunan yüzeyler

| Yüzey | Gözlemleyebileceklerimiz | Engelleyebileceklerimiz | Kontrolün asıl yeri |
|---|---|---|---|
| Kullanıcı girdisi ve konuşma geçmişi | `texts`, `structured_messages` (LiteLLM request) | Evet: `pre_call` ile engelle veya maskele | Gateway hook'u. Çok turlu analiz için oturum kimliği header ile taşınmalı |
| Model yanıtı ve streaming | Yanıt metni; stream'de örneklenmiş chunk'lar | Streaming olmayan yanıtta engelle veya maskele. Stream'de LiteLLM varsayılan olarak yalnızca engelleme yapabiliyor (`block_only`); maskeleme yalnızca OpenAI chat completions'ta `incremental_diff` ile çalışıyor | Gateway. **`/v1/messages` stream'inde maskeleme yok**; ya tam tamponlama ya da yalnızca engelleme |
| RAG dokümanları | Uygulama gönderirse chunk'lar | Chunk düşürme, kaynak güven etiketi | **Uygulama/retriever içinde.** Gateway, prompt'a gömülmüş chunk'ı kullanıcı metninden ayıramaz |
| Tool tanımları, çağrıları ve sonuçları | `tools`, `tool_calls` (LiteLLM), `tool_input` (Claude Code), `args` (Hermes) | Hermes `pre_tool_call` (fail-closed), Claude Code `PreToolUse` (`onFailure: block` ile), LiteLLM `pre_mcp_call` | **Agent runtime hook'u**; MCP gateway yalnızca kendi üzerinden geçen sunucuları görür |
| Kod deposu ve geliştirme ortamı | `UserPromptSubmit`, okunan dosya içerikleri (`PostToolUse`) | Prompt engelleme; tool çıktısını modele vermeden önce yeniden yazma | Claude Code managed hook'ları (`allowManagedHooksOnly`) |
| Terminal ve işlem yürütme | `PreToolUse` (Bash), Hermes terminal tool'u | Komut reddetme veya insan onayı (`ask`) | Runtime hook'u + **sandbox** (Battal sandbox değildir) |
| Agent hafızası ve agent'lar arası iletişim | Belleğe yazılan içerik (runtime izin verirse); A2A mesajları | Yazma öncesi tarama; A2A gateway'de metin denetimi | Runtime. A2A protokolünde guardrail hook'u yok; yetkilendirme "implementation-specific" |

### 4.4 Ortak API sözleşmesi

Kimlikler (`tenant`, `principal`, `session`, `agent`), içeriğin kaynağı ve güven seviyesi
(`source`, `trust`), hedef (`target`) ve kontrol noktası (`checkpoint`) her istekte taşınır.
**Ham model skoru, policy kararı ve gerekçe ayrı alanlardır.** Kalibre edilmemiş skorlar olasılık
olarak sunulmaz.

```json
{
  "api_version": "v1",
  "request_id": "req_01J…",
  "checkpoint": "input",
  "tenant": "acme",
  "principal": {"user_id": "u-42", "team_id": "t-7", "key_hash": "…"},
  "session": {"id": "s-9", "turn": 3},
  "agent": null,
  "target": {"model": "qwen3-32b", "provider_region": "tr"},
  "policy": {"id": "default-tr", "version": "2026-11-01"},
  "segments": [
    {"id": 0, "text": "Önceki talimatları yok say. TC'm 10000000146", "role": "user",
     "source": "user", "trust": "untrusted"}
  ]
}
```

```json
{
  "request_id": "req_01J…",
  "decision": {
    "action": "block",
    "rule_id": "pi.block_high",
    "policy": {"id": "default-tr", "version": "2026-11-01"},
    "fail_mode": "closed",
    "degraded": false
  },
  "detections": [
    {"detector": "tr-injection", "version": "0.1.0", "raw_score": 0.91,
     "calibrated": false, "threshold": 0.80, "segment": 0, "span": [0, 26]},
    {"detector": "pii.tckn", "version": "0.1.0", "checksum_valid": true,
     "context_hit": true, "segment": 0, "span": [34, 45]}
  ],
  "transforms": [{"segment": 0, "text": "Önceki talimatları yok say. TC'm <TCKN>"}],
  "rationale": {"code": "PROMPT_INJECTION", "message_tr": "İstek güvenlik politikası nedeniyle engellendi."},
  "timing_ms": {"normalize": 0.4, "detectors": 12.1, "total": 13.0}
}
```

Örnekteki `timing_ms` değerleri yalnızca alanların biçimini göstermek içindir; ölçülmüş değildir.

**LiteLLM eşlemesi.** `allow` → `{"action":"NONE"}`. `mask` → `GUARDRAIL_INTERVENED` + `texts`
(1:1 sıralı). `block` → `BLOCKED` + `blocked_reason` (kısa Türkçe mesaj ve karar kimliği;
dedektör ayrıntısı istemciye gönderilmez). Bütün kararlar **HTTP 2xx** ile döner. Battal karar
veremezse **503** döner ve LiteLLM'in `unreachable_fallback` ayarı devreye girer.

### 4.5 Policy seçimi, öncelik ve sürümleme

- **Seçim sırası:** istek içindeki `policy.id` (izin verilmişse) → key/team eşlemesi → tenant
  varsayılanı → global varsayılan.
- **Çakışmalar:** `block` > `ask` > `mask` > `allow`. Aynı seviyede daha spesifik kural kazanır.
  Her karar `rule_id` ile kaydedilir.
- **Sürümleme:** Policy paketi = semver + içerik hash'i. Dedektör ve model sürümü her kararda
  kaydedilir. Yeni policy veya model önce **shadow modda** çalışır: karar verilmez, yalnızca
  kaydedilir ve eskisiyle karşılaştırılır. Sonra canary'ye alınır. Geri alma işlemi bir önceki
  hash'e dönmekten ibarettir.
- **Senkron/asenkron:** `input` ve `tool_call` her zaman senkron çalışır. `output` için streaming
  olmayan yanıtlar senkron değerlendirilir. Stream'de örneklenmiş değerlendirme yapılır; risk
  kabulü belgelenir. Ağır LLM guard'lar varsayılan olarak asenkron (audit) çalışır.

### 4.6 Hata ve erişilemezlik

| Durum | `input` / `tool_call` | `output` (düşük risk) | `output` (regüle) |
|---|---|---|---|
| Battal timeout veya erişilemez | Fail-closed (LiteLLM `unreachable_fallback: fail_closed`) | Fail-open + kritik alarm | Fail-closed |
| Model tabanlı dedektör düştü | Deterministik kurallarla karar verilir + `degraded: true` | Aynı | Aynı |
| Geçersiz istek veya policy yok | 4xx → LiteLLM `fail_on_error` (varsayılan: engelle) | Aynı | Aynı |

`fail_on_error: false` güvenlik sınırında **hiçbir zaman** kullanılmamalıdır (LiteLLM dokümanı bu
ayarı "complete bypass" olarak tanımlıyor). Saldırganın çok uzun girdiyle timeout tetiklemesine
karşı girdi uzunluğu sınırlandırılır ve uzun metin pencerelere bölünür.

### 4.7 Ham veriyi saklamadan izlenebilirlik

Karar kaydında şunlar tutulur: istek ID'si, `litellm_call_id` / `trace_id`, kontrol noktası,
dedektör ve sürümü, skor, eşik, policy sürümü, eylem, span offset'leri, içeriğin HMAC'i. **Ham
metin ve maskelenmemiş PII kaydedilmez.** Saklama süresi parametrik bir ayardır ve varsayılan bir
"hukuki öneri" olarak sunulmaz (bkz. §7).

---

## 5. Üç entegrasyon senaryosu

Ayrıntılar ve permalink'ler: [Ek 4](ekler/04-integrations.md).

| Hedef sistem | Kullanılabilir hook/API | Taşınan bağlam | Uygulanabilen kontrol | Bilinen sınırlama |
|---|---|---|---|---|
| LiteLLM (Generic Guardrail API) | `POST {api_base}/beta/litellm_basic_guardrail_api`; modlar `pre_call`, `during_call`, `post_call`, `pre/during/post_mcp_call` | `texts`, `structured_messages` (yalnızca request), `tools`, `tool_calls`, `model`, key/user/team/org kimlikleri, `litellm_call_id`/`trace_id`, allowlist'teki header'lar | `NONE` / `BLOCKED` (istemciye HTTP 400) / `GUARDRAIL_INTERVENED` (maskeleme) | `/beta/` yolunda; `during_call` maskeleyemez; stream'de maskeleme yalnızca OpenAI chat'te var; session id taşınmıyor (header ile taşınmalı) |
| LiteLLM (FMS Detector API) | `ibm_guardrails` hook'u | Metin | Tespit + eşik → engelleme | Yalnızca tespit; maskeleme yok |
| Claude Code | `PreToolUse` (`allow/deny/ask/defer` + `updatedInput`), `UserPromptSubmit`, `PostToolUse` (`updatedToolOutput`) | `session_id`, `cwd`, `tool_name`, `tool_input`, `prompt` | Tool çağrısını reddetme veya onaya yükseltme, prompt engelleme | Hook geliştirici makinesinde çalışır; timeout'ta varsayılan **fail-open**, bu yüzden `onFailure: "block"` gerekir; kullanıcı kimliği alanı yok; model I/O hook ile değil LiteLLM yönlendirmesiyle korunur |
| Hermes Agent (NousResearch, MIT) | Plugin `pre_tool_call` (`block/approve/modify`), `transform_tool_result`, `pre_llm_call`, `transform_llm_output` | `tool_name`, `args`, `session_id`, `conversation_id`, `turn_id` | Tool engelleme, insan onayı, argüman değiştirme | `pre_tool_call` hata durumunda fail-closed, ama middleware fail-open; payload'da kullanıcı kimliği yok |
| MCP (spec 2026-07-28) | Protokolde hook yok; enforcement istemcide, gateway'de (LiteLLM `/mcp`) veya sunucuda | `tools/call` adı ve argümanları, `tools/list` açıklamaları | Gateway'de engelleme ve maskeleme | Yetkilendirme OPTIONAL; human-in-the-loop yalnızca SHOULD; annotation'lar güvenilmez kabul ediliyor |
| A2A (v1.0.1) | Protokolde hook yok; gateway üzerinden | Mesaj `parts` | Gateway'de metin denetimi | Yetkilendirme "implementation-specific" |

!!! warning "MCP ve A2A desteği tek başına bir güvenlik kontrolü değildir"
    İki protokol de içerik güvenliği için zorunlu bir mekanizma tanımlamıyor. Gerçek engelleme
    noktası her zaman bir hook'tur: istemcideki runtime, gateway veya sunucu.

### 5.1 Senaryo A: AI gateway (MVP)

1. `docker compose up` ile LiteLLM, Battal ve bir model ayağa kalkar. Model sunucusu olarak
   Ollama veya herhangi bir OpenAI-uyumlu backend kullanılabilir.
2. LiteLLM config'ine iki guardrail girdisi eklenir:
   - `battal-input`: `mode: [pre_call]`, `unreachable_fallback: fail_closed`.
   - `battal-output`: `mode: [post_call]`, politika bazında.
   - İkisinde de `timeout` açıkça verilir.
3. Battal'ın adapter route'u LiteLLM payload'ını `EvaluationRequest`'e çevirir; kararı LiteLLM
   yanıtına geri eşler.
4. Contract test: pinlenmiş LiteLLM sürümüne karşı CI'da çalışır. LiteLLM'in
   `/guardrails/apply_guardrail` endpoint'i, LLM çağrısı yapmadan uçtan uca test imkânı veriyor.

### 5.2 Senaryo B: Code studio / IDE (faz 2)

- Model trafiği `ANTHROPIC_BASE_URL` ile LiteLLM'e yönlendirilir; LiteLLM'in `/v1/messages`
  endpoint'i Generic API ile korunur. Managed ayarlarda `allowedProviders: ["customEndpoint"]`
  ile bu yönlendirme sabitlenir.
- Tool'lar için managed bir `PreToolUse` HTTP hook'u Battal'ın `/v1/hooks/claude-code`
  endpoint'ine bağlanır. Hook `onFailure: "block"` ile çalışır ve `allowManagedHooksOnly` açılır.
- Kısıt: `/v1/messages` stream'inde çıktı maskelemesi yok. Çıktı politikası bu yolda yalnızca
  engelleme ya da audit olarak çalışır.

### 5.3 Senaryo C: Agent runtime (faz 2)

- Hermes Agent için bir `battal` plugin'i:
  - `pre_tool_call` → Battal (`tool_call` checkpoint'i).
  - `transform_tool_result` → PII ve injection maskeleme.
  - `pre_llm_call` → istek engelleme.
  - Model trafiği `provider: custom` ile LiteLLM'e yönlendirilir.
- Plugin içindeki HTTP timeout'u, Hermes'in `hook_callback_timeout` değerinden kısa tutulmalı.
  Python yazmadan bağlanmak isteyenler için alternatif: `fail_closed: true` shell hook + küçük
  bir `battal-hook` CLI.

---

## 6. Türkçe model ve veri stratejisi

Ayrıntılar: [Ek 2](ekler/02-models.md), [Ek 5](ekler/05-eval-datasets.md).

### 6.1 Başlangıç (MVP, fine-tune yok)

1. **Deterministik katman:** normalizasyon, çözme ve görünmez karakter sinyalleri. Üçüncü taraf
   ölçümünde (halilneed kartı), çözücü eklenmesi invisible Unicode recall'unu belirgin biçimde
   artırmış (örneğin BERTurk-v1: 0.405 → 0.905). Bu bir geliştirici beyanıdır; bizim
   benchmark'ımızda tekrar ölçülecek.
2. **Yüksek precision'lı kurallar:** TR ve EN imzalar, stem ve n-gram ile. Kurallar tek başına
   zayıf (aynı kaynakta keyword kuralının F1'i 0.03–0.31). Açıklanabilir bir sinyal ve hızlı yol
   olarak kullanılırlar; sınıflandırıcının yerine geçmezler.
3. **Üç adayın ölçülmesi:** halilneed v2, wolf-defender small/edge ve proventra kendi
   calibration split'imizde ölçülür. Eşik "TR hard-benign FPR ≤ hedef" koşulunda seçilir. Kazanan
   ONNX int8 olarak paketlenir.

### 6.2 İyileştirme (faz 2): fine-tune ne zaman haklı?

Kalibrasyondan sonra şu koşullardan biri sağlanıyorsa fine-tune yapılır:
- Hard-benign FPR hedefin üstünde kalıyorsa. Üçüncü taraf ölçümleri genel modellerde %60–77
  gösteriyor; bu sorun eşik ayarıyla çözülmez.
- TR-EN karışık metinde, morfolojik yeniden ifadede ya da dolaylı injection'da recall çöküyorsa.
- Varsayılan modelin tek kişinin bakımına bağlı kalması kabul edilmiyorsa.

Plan:
- Taban mmBERT-small (CPU) olur. Kalite referansı olarak mmBERT-base ve TabiBERT kullanılır.
- Veri: lisanslı Türkçe setler, kontrollü çeviriler ve iki sınıfa da uygulanan obfuscation
  augmentation. Augmentation tek sınıfa uygulanırsa model "garip karakter = saldırı" öğrenir.
  Hard-negative'ler bol tutulur.
- Etiketleme ve distillation için yalnızca Apache-2.0 öğretmenler kullanılır; öğretmen etiketleri
  insan gözden geçirmesiyle örneklenir.
- Çıktı: ONNX int8, temperature scaling ile kalibre edilmiş skor, model kartında held-out kaynak
  sonuçları ve seed varyansı.
- Gecikme hedefi CPU'da 512 token için **p95 < 50 ms**. Bu bir hedeftir, ölçüm değildir. Tek
  referans, geliştiricinin i5-12400F üzerinde 307M model için beyan ettiği ~35 ms ortalama.

### 6.3 Veri kaynakları ve lisans kararları

| Amaç | Kullanılabilir | Gömülmeyecek |
|---|---|---|
| Injection eğitimi ve tohum | Kendi şablon ailelerimiz; 3nesdeniz (CC-BY-4.0); İngilizce permissive setlerin kontrollü çevirisi | OnerAYTAS (CC-BY-NC-SA, makine çevirisi); Lakera oyun trafiği |
| Injection dış testi (**eğitime hiç girmez**) | halilneed false-alarm (CC0); 3nesdeniz 1k/conversation; fevzi (CC-BY-4.0) | — |
| PII | cagrigungor (CC0, dış test), BTX24 (CC-BY-4.0), fevzi corpus (Apache-2.0), GoktugD NER (CC0), nm-kvkk-pii-6K (Apache-2.0) | savasy NER (ağırlık lisansı yok), WikiANN (unknown), tr_core_news (CC-BY-SA) |
| Benign-toksik hard negative | RTP-LX TR (1.049 satır; ODC-BY) | ctoraman (NC-SA), TurkishHateMap (SA), tweet tabanlı setler |

Büyük çok dilli safety setlerinin (MultiJail, XSafety, Aya red-teaming, PolyGuard) hiçbirinde
Türkçe yok.

### 6.4 Bağımsız değerlendirme

- **Split:** satır yerine aile (`family_id`) bazında yapılır: `SHA-256(family_id) mod 100` →
  train %70, calibration %15, test %15. Çeviriler ve varyantlar kaynaklarının ailesine bağlanır
  (union-find). Yakın kopyalar MinHash-LSH ile, TR↔EN çeviriler LaBSE veya e5 benzerliğiyle
  yakalanır. Contamination raporunda test ile train arasındaki eşik üstü çift sayısı 0 olmalıdır.
- **Metrikler:** kategori × varyant bazında precision ve recall; dondurulmuş eşikte FPR;
  TPR@FPR=%1; ECE; aile bazında cluster bootstrap CI; uçtan uca ASR ve ΔASR; PII için miss ve
  over-mask oranı; açık-döngü yükte p50/p95/p99; 1.000 istek başına maliyet; quantization delta
  (McNemar); fail-open ve timeout testleri.
- **Harness:** Inspect (ana harness), promptfoo (CI), PyRIT converter'ları (varyant üretimi).

---

## 7. Güvenlik ve uyum eşleştirmesi

Ayrıntılar, kaynaklar ve 28 satırlık tam tablo: [Ek 6](ekler/06-compliance.md). Bu bölüm hukuki
tavsiye değildir.

**Kategoriler ayrı tutulur.**
- **Hukuki yükümlülükler:** EU AI Act, KVKK, BTK. Role ve risk sınıfına göre uygulanırlar,
  otomatik değil.
- **Risk yönetimi çerçeveleri:** NIST AI RMF 1.0, NIST AI 600-1. Gönüllüdür.
- **Saldırı taksonomileri:** MITRE ATLAS 2026.10, OWASP LLM Top 10 2025, OWASP Top 10 for
  Agentic Applications 2026 (ASI01–ASI10).

| Gereksinim / tehdit | Teknik kontrol | Uygulama noktası | Doğrulama testi | Denetim kanıtı | Kalan risk |
|---|---|---|---|---|---|
| Doğrudan prompt injection (LLM01; AML.T0051.000; ASI01; KVKK ÜYZ rehberi) | TR+EN sınıflandırıcı + kurallar + policy | input | TR benchmark TPR/FPR; regresyon; adaptif red team | Sürümlü eval raporu; karar kaydı | Adaptif saldırılar; %100 tespit yok |
| Dolaylı injection (LLM01; AML.T0051.001; AML.T0070) | Chunk ve tool çıktısı taraması; güvenilmeyen içerikten sonra tool-call kısıtı | retrieval, tool_result, policy | Talimat gömülü doküman setiyle uçtan uca test | Chunk bazlı karar + kaynak ID'si | Talimat/veri ayrımı LLM'de çözülmüş değil |
| Obfuscation (AML.T0068) | Türkçe-farkında normalizasyon, çözme | input, retrieval, tool_result | Mutasyon fuzz testi | Fuzz raporu | Sınırsız kodlama uzayı |
| İstemde kişisel veri (LLM02; KVKK m.12; BTK Yön. m.6) | Checksum + bağlam ile tespit, maskeleme | input, output, audit | Sentetik TR PII seti; kayıtlarda ham PII taraması | PII metrikleri; policy sürümü | Dolaylı tanımlayıcılar; **maskeleme anonimleştirme değildir** |
| Yurt dışına aktarım (KVKK m.9 + Yönetmelik, RG 10.07.2024/32598) | Sağlayıcı/bölge allowlist'i; PII varsa maskele veya engelle | policy, audit | Policy birim testleri | Policy-as-code geçmişi; egress kayıtları | Hukuki dayanak teknikle sağlanamaz; **kurumun kararıdır** |
| Telekom trafik/konum verisi (BTK Yön. m.5(2)) | Veri sınıfı etiketine göre egress engelleme | policy, input | Etiketli veriyle test | Engelleme kayıtları | Veri sınıflandırması operatöre aittir |
| Aşırı yetki / tool misuse (LLM06; ASI02) | Faz 2: Cedar ile tool-call yetkilendirme; HITL | tool_call, policy | Yetkisiz tool ve argüman denemeleri | Tool-call karar kaydı | Meşru argümanla kötüye kullanım; onay yorgunluğu |
| Tool poisoning (ASI04; AML.T0110) | Tool manifest hash'ini pinleme, değişiklik uyarısı | tool_result, policy | "Rug pull" simülasyonu | Manifest hash geçmişi | Tool'un kendi implementasyonu |
| İzlenebilirlik (AI Act Art. 12, yüksek risk; BTK m.6(4): 2 yıl) | Ham veri içermeyen, bütünlüğü korunan karar kaydı | audit | Bütünlük doğrulama; iz sürme tatbikatı | Log şeması; saklama ayarı | Saklama süresine **kurum karar verir** |
| Doğruluk ve dayanıklılık beyanı (AI Act Art. 15(3)) | Sürüm başına yayınlanan metrikler ve sınırlamalar | audit | Yeniden üretilebilir benchmark | Sürümlü eval raporu | Kurumun kendi verisinde performans farklı olabilir |
| Battal'ın kendi tedarik zinciri (LLM03; AML.T0010) | İmzalı release'ler, SBOM, model artefact hash'leri | build | CI'da imza doğrulama | SBOM, imza | Upstream zafiyetler |

**Yalnızca kurumun yapabilecekleri:** rol ve risk sınıflandırması (AI Act Art. 3, 6, Ek III),
DPIA, aktarım için hukuki dayanak, ihlal bildirimi (KVKK 72 saat), AI okuryazarlığı ve saklama
süresi kararı.

**Dikkat edilecekler.**
- **ATLAS ID'leri:** 2026.10 sürümünde `AML.T0056` ve `AML.T0057` yok. Bu yüzden eşleme
  dosyaları sürümlenir (`mappings/atlas-2026.10.yaml`).
- **Açık kaynak muafiyeti:** AI Act Art. 2(12), açık kaynak sistemleri yüksek risk, Art. 5 veya
  Art. 50 kapsamına girmedikçe muaf tutuyor. Battal'ı yüksek riskli bir sistemde kullanan kurum
  ise sağlayıcı yükümlülüklerini kendisi taşır.
- **Dokümanlarda kullanılmayacak ifade:** "KVKK/AI Act uyumlu". Doğru ifade: "şu gerekliliklere
  yönelik teknik kontroller ve kanıt sağlar; uyum değerlendirmesi kuruma aittir."

---

## 8. İlk ürün kapsamı (MVP)

ADR 0002, ADR 0003 ve ADR 0004 ile tutarlıdır.

**Kapsamda:**
- Python çekirdek kütüphane + FastAPI sunucu.
- `input` ve `output` checkpoint'leri.
- Türkçe normalizasyon (görünümler ve sinyaller).
- TCKN, IBAN, telefon ve e-posta tespiti, bağlam skoru ve maskeleme.
- TR ve TR-EN injection tespiti: kurallar + kalibre edilmiş ONNX sınıflandırıcı.
- YAML policy; checkpoint bazında fail modu.
- Policy binding (`bindings.yaml`, global taban policy), policy test formatı ve CLI (ADR 0004).
- Ham veri içermeyen karar kaydı.
- LiteLLM Generic Guardrail API adapter'ı.
- `docker compose` demosu.
- Türkçe benchmark v0 ve sonuç raporu.
- JSON test vektörleri (Rust geçişinin conformance suite'i).

**Kapsam dışı:**
- Streaming denetimi, tool-call güvenliği, RAG, MCP, Claude Code ve Hermes adapter'ları.
- İsim ve adres NER, secret detection, content safety, telekom tanımlayıcıları.
- Rust çekirdeği, fine-tune edilmiş model.

**Genişleme sırası (bağımlılığa göre):**
1. Benchmark sonuçlarına göre fine-tune edilmiş TR injection modeli.
2. Rust `battal-core` (ADR 0003).
3. Tool-call checkpoint'i + Cedar; Hermes plugin'i ve Claude Code `PreToolUse` adapter'ı.
4. Output streaming stratejisi; MCP gateway (`pre/post_mcp_call`), ContextForge ve agentgateway
   adapter'ları.
5. FMS Detector API.
6. Content safety (Qwen3Guard adapter → distillation).
7. Secret detection (gitleaks kuralları); telekom tanımlayıcıları; NER.

---

## 9. Geliştirme backlog'u (bağımlılık sırasına göre)

Takvim ve sprint ataması yapılmamıştır. MVP epic'leri ayrıntılı, sonraki fazlar epic düzeyindedir.

### E0 Repo iskeleti ve kalite altyapısı

- **PBI 0.1 Paket ve araç zinciri.** `pyproject.toml` (paket `battal`, extras `[server]`), ruff,
  mypy (strict), pytest, pre-commit kurulumu.
  *DoD:* `pip install -e .[server]` çalışır; CI'da lint, type check ve test yeşildir.
- **PBI 0.2 Test vektörü formatı.** `testvectors/` için bir JSON şeması (`input`, `expected`,
  `tags`) ve vektörleri çalıştıran bir pytest runner.
  *DoD:* Şema dokümante edilmiştir; runner örnek vektörlerle CI'da koşar.
- **PBI 0.3 Tedarik zinciri.** Release imzası, SBOM üretimi, bağımlılık taraması.
  *DoD:* Her tag'de SBOM ve imza artefact olarak yayınlanır.

### E1 Değerlendirme sözleşmesi

- **PBI 1.1 `EvaluationRequest` / `EvaluationResponse` tipleri.** Pydantic modelleri ve JSON
  Schema export'u; altı checkpoint'in tamamı enum'da yer alır.
  *DoD:* Şema `docs/` altında yayınlanır; geriye dönük uyumluluk testi vardır.
- **PBI 1.2 Detector, PolicyEngine ve Action interface'leri.** Saf fonksiyon sözleşmesi:
  global state yok, I/O yok.
  *DoD:* Örnek bir dummy detector'la uçtan uca birim testi geçer.

### E2 Türkçe normalizasyon çekirdeği

- **PBI 2.1 Sinyal çıkarma.** Tag, zero-width, bidi, karışık script ve Co/Cn karakterleri sayılır.
  *DoD:* Her sinyal türü için en az 10 test vektörü vardır; bayrak emoji dizileri yanlış pozitif
  üretmez.
- **PBI 2.2 Offset haritalı temizleme ve NFKC.**
  *DoD:* Round-trip testi geçer (her bulgu orijinal metindeki doğru span'e eşlenir).
- **PBI 2.3 Türkçe-farkında casing ve confusable katlama.**
  *DoD:* `İSTANBUL` → `istanbul`, `IĞDIR` → `ığdır`. `ışık` ve `IŞIK` bozulmaz (vektörlerle
  doğrulanır).
- **PBI 2.4 Diakritik görünümleri.** Deasciify ve diakritik düşürme formları üretilir.
  *DoD:* `onceki talimatlari` ile `önceki talimatları` aynı kurala eşleşir.
- **PBI 2.5 Çözücüler.** base64, hex, rot13, URL encoding ve tag→ASCII; özyineleme derinliği en
  fazla 2, boyut sınırlı.
  *DoD:* Decode bombası testi (çok büyük girdi ya da iç içe kodlama) sınırlar içinde kalır.

### E3 Türkçe PII

- **PBI 3.1 Checksum kütüphanesi.** TCKN, VKN, IBAN-TR (mod-97) ve Luhn.
  *DoD:* python-stdnum'a karşı 1 milyon rastgele örnekte sonuçlar birebir aynıdır (dev-dependency
  olarak); FP oranları belgelenir.
- **PBI 3.2 TCKN, IBAN, telefon ve e-posta tanıyıcıları.** Rakam-lookaround kullanılır; ek ve
  kesme işareti toleransı vardır; gruplu yazım desteklenir; Presidio registry'ye kaydedilir.
  *DoD:* `…146dır`, `100 000 001 46`, tam genişlikli rakamlar ve ZWSP'li TCKN yakalanır;
  `0532 123 4567den` yakalanır.
- **PBI 3.3 Bağlam skoru ve maskeleme.** Bağlam kelimeleri stem üzerinde aranır; tip etiketli
  yer tutucular (`<TCKN>`) kullanılır.
  *DoD:* Checksum'ı geçersiz distractor'larda over-mask oranı raporlanır; bağlamsız TCKN düşük
  güvenle işaretlenir.

### E4 Injection tespiti

- **PBI 4.1 Kural seti v0.** TR ve EN imzalar, stem ve n-gram ile.
  *DoD:* Her kural için pozitif ve negatif vektör vardır; kurallar benchmark'ta ayrı raporlanır.
- **PBI 4.2 ONNX detector adapter'ı.** Pencereleme (512–2048 token), int8 desteği.
  *DoD:* Üç aday model aynı interface ile çalışır; model hash'i doğrulanır.
- **PBI 4.3 Baseline seçimi ve kalibrasyon.** Temperature scaling; eşik calibration split'inde
  seçilir.
  *DoD:* Test split'inde TPR@FPR=%1, ECE ve hard-benign FPR raporlanır; seçilen model ve eşik
  ADR ile kaydedilir.

### E5 Policy engine

- **PBI 5.1 YAML policy şeması ve evaluator.** Eylemler: `allow`, `mask`, `block`, `ask`;
  öncelik kuralı tanımlıdır.
  *DoD:* Çakışma, öncelik ve `rule_id` için birim testleri vardır.
- **PBI 5.2 Fail modları ve degraded karar.**
  *DoD:* Dedektör çökmesi, timeout ve geçersiz policy senaryoları için beklenen davranış testlerle
  doğrulanır.
- **PBI 5.3 Policy binding ve katmanlı birleştirme** (ADR 0004). `bindings.yaml`; MVP boyutları
  `checkpoint`, `tenant`/`team`/`key`, `model` (glob); global taban policy + en spesifik policy.
  *DoD:* Aynı spesifiklikte çakışma yüklemede hata verir; alt katmanın tabanı gevşetemediği ve
  istek içindeki `policy.id`'nin tabanı atlatamadığı testlerle doğrulanır; yanıtta
  `matched_bindings` vardır.
- **PBI 5.4 Policy bundle ve hot reload.** Semver + içerik hash'i; validate → atomik değiştirme.
  *DoD:* Geçersiz bundle'da eski bundle çalışmaya devam eder ve alarm üretilir; her kararda
  `bundle_hash` vardır.
- **PBI 5.5 Policy test formatı ve CLI.** `*.test.yaml` (`context`, `input`, `expect`);
  `battal policy validate`, `test`, `diff`.
  *DoD:* Şema test vektörleriyle ortaktır; `tags: [model]` testleri CI'da ayrı job'da koşar;
  `diff` kararı değişen case'leri listeler.

### E6 Sunucu ve LiteLLM adapter'ı

- **PBI 6.1 FastAPI `/v1/evaluate`.**
  *DoD:* OpenAPI yayınlanır; girdi boyutu sınırı vardır; yük altında p50/p95/p99 ölçülür ve
  raporlanır.
- **PBI 6.2 Generic Guardrail API route'u.**
  *DoD:* Pinlenmiş LiteLLM sürümüne karşı contract test CI'da geçer; bütün kararlar 2xx döner;
  `texts` 1:1 sıralıdır.
- **PBI 6.3 `docker compose` demosu.**
  *DoD:* Temiz bir makinede tek komutla çalışır; README'deki üç örnek istek (engelle, maskele,
  geçir) beklenen sonucu verir.

### E7 Türkçe benchmark v0

- **PBI 7.1 Veri şeması ve aile tanımları.**
  *DoD:* Satır şeması (`family_id`, `variant_of`, `translated_from`, `license`…) ve datasheet
  hazırdır.
- **PBI 7.2 Şablon aileleri ve varyant üretimi.** Aile sayısı için öneri 150–250; bu bir
  hedeftir, ölçüm değildir.
  *DoD:* Saldırı:hard-negative oranı ≥ 1:1.5; iki annotator ile Cohen's κ raporlanır.
- **PBI 7.3 Split ve contamination denetimi.**
  *DoD:* Test↔train arasında eşik üstü çift sayısı 0'dır; dış setlere karşı contamination tablosu
  çıkarılır.
- **PBI 7.4 Inspect task'ları ve sonuç raporu.**
  *DoD:* Tek komutla yeniden üretilebilir; Presidio varsayılanı ve aday modellerle karşılaştırma
  tablosu yayınlanır.

### E8 Karar kaydı

- **PBI 8.1 Ham veri içermeyen yapılandırılmış log.**
  *DoD:* Log'larda ham PII taraması CI'da 0 bulgu verir; her karar `request_id` ile izlenebilir.

### E9 Yayın

- **PBI 9.1 PyPI paketi, container imajı, Hugging Face dataset'i, dokümantasyon.**
  *DoD:* `pip install battal` ve `docker run` çalışır; dataset CC-BY-4.0 ve NOTICE ile
  yayınlanır; sürüm notları vardır.

### Sonraki fazlar (epic düzeyi)

| Epic | Bağımlılık |
|---|---|
| E10 Fine-tune edilmiş TR injection modeli (Apache-2.0) | E7 sonuçları |
| E11 Rust `battal-core` (PyO3) + iki motorun yan yana çalışması | E0.2 vektörleri, E2, E3, E5 |
| E12 Tool-call checkpoint'i + Cedar adapter'ı | E1, E5 |
| E13 Hermes plugin'i, Claude Code `PreToolUse` adapter'ı | E12 |
| E14 Output streaming stratejisi | E6 |
| E15 MCP gateway, ContextForge ve agentgateway adapter'ları; FMS Detector API | E12 |
| E16 Content safety (Qwen3Guard adapter → distillation) | E7 |
| E17 Secret detection, telekom tanımlayıcıları, isim/adres NER | E3 |
| E18 Policy playground (yerel, `--playground`, htmx; ADR 0004) | E5, E6 |

---

## 10. Açık kaynak sürdürülebilirliği

- **Repo yapısı:**
  ```text
  python/battal/          # çekirdek (normalize, detectors, pii, policy, types)
  python/battal_server/   # FastAPI + adapter route'ları
  adapters/litellm/       # config örnekleri + contract testleri
  testvectors/            # dilden bağımsız JSON vektörleri (Rust conformance)
  bench/                  # veri üretimi, split, Inspect task'ları
  models/                 # model kartları ve hash'ler (ağırlık repoda tutulmaz)
  deploy/                 # compose, ileride Helm
  docs/                   # bu site
  rust/                   # ileride battal-core
  ```
- **Lisans:** Kod Apache-2.0 (ADR 0001). Ağırlıklar ve veri ayrı lisanslanır; benchmark
  CC-BY-4.0'dır. Dış katkılar CLA hazır olduktan sonra kabul edilir.
- **Sürümleme:** Paket için SemVer. API yolları sürümlenir (`/v1`). Policy şeması, dedektörler,
  modeller ve dataset ayrı ayrı sürümlenir ve her karar kaydında yer alır.
- **Katkı kuralları:** [CONTRIBUTING](../proje/katki.md). Her yeni dedektör için test vektörü ve
  benchmark sonucu zorunludur. Yeni bir model eklemek için model kartı, ağırlık lisansı ve hash
  gerekir.
- **Güvenlik açığı bildirimi:** [SECURITY](../proje/guvenlik.md). GitHub private vulnerability
  reporting açıktır. Detection bypass, policy bypass ve fail-open istismarı güvenlik açığı sayılır.
  Düzeltme yayınlanırken GitHub Security Advisory ile CVE talep edilir.
- **Yeniden üretilebilir testler:** Test vektörleri, sabit seed'li veri üretimi, pinlenmiş
  bağımlılıklar ve model hash'leri. Her release'te benchmark sonucu yeniden üretilip yayınlanır.

---

## Karar

> **Şu açık kaynak temelleri seçin:** ONNX Runtime; Presidio (yalnızca orkestratör olarak) +
> phonenumbers; LiteLLM Generic Guardrail API; Inspect, promptfoo ve PyRIT converter'ları;
> ikinci fazda Cedar (`cedarpy` + `cedar-for-agents`); fine-tune tabanı olarak mmBERT veya
> TabiBERT; öğretmen olarak yalnızca Apache-2.0 modeller (Qwen3Guard, gpt-oss-safeguard).
>
> **Kendi yatırımınızı şu özgün yeteneklere yapın:** Türkçe-farkında, offset korumalı
> normalizasyon çekirdeği; ek ve obfuscation toleranslı Türkçe PII tanıyıcıları; hard-negative'lerle
> eğitilmiş Apache-2.0 Türkçe injection modeli; template-family split'li, herkese açık Türkçe
> benchmark; ham veri saklamayan, sürümlü karar kaydı.
>
> **İlk sürümü şu kapsamda çıkarın:** LiteLLM `pre_call`/`post_call`; Türkçe ve TR-EN injection
> tespiti; TCKN, IBAN, telefon ve e-posta maskeleme; YAML policy; CPU'da ONNX; `docker compose`
> demosu.
>
> **Şu testlerle doğrulayın:** aile bazlı split ve sıfır contamination; dondurulmuş eşikte FPR ve
> TPR@FPR=%1; ECE; PII miss ve over-mask oranları; dış test setleri; p50/p95/p99 gecikme;
> fail-open, timeout ve truncation bypass testleri; pinlenmiş LiteLLM'e karşı contract test.
>
> **Farklı platformlara şu adapter'larla bağlayın:** LiteLLM Generic Guardrail API (MVP) → FMS
> Detector API → Claude Code `PreToolUse` HTTP hook'u + `/v1/messages` gateway yönlendirmesi →
> Hermes `battal` plugin'i (`pre_tool_call`, `transform_tool_result`) → MCP gateway
> (`pre/post_mcp_call`, ContextForge, agentgateway).

---

## Açık belirsizlikler

- Prompt Guard 2'nin Türkçe performansını kimse ölçmemiş. Kendi benchmark'ımızda adapter olarak
  ölçülecek.
- Türkçe modellerin (halilneed, wolf-defender, proventra) sonuçları küçük test setlerine ve tek
  bir yazarın ölçümüne dayanıyor. Bu sonuçlar yön gösterir, karar vermez.
- LiteLLM Generic API'nin `logging_only` desteği; timeout verilmediğinde kullanılan varsayılan
  değer; hangi alanların hangi kararlı sürümde geldiği. MVP'de LiteLLM sürümü pinlenecek ve bu
  noktalar çalıştırılarak test edilecek.
- TCKN ve VKN algoritmaları için resmî NVİ veya GİB yayını bulunamadı; tutarlı ikincil kaynaklar
  ve yaygın kütüphaneler kullanıldı.
- BTK'nın 2014 tarihli ağ ve bilgi güvenliği yönetmeliğinin yürürlük durumu ve 7545 sayılı Siber
  Güvenlik Kanunu'nun ayrıntıları; BDDK, kamu, DORA ve NIS2 düzenlemeleri doğrulanmadı.
- CPU gecikme değerleri ölçülmedi. Tek istisnalar: Presidio için bizim ölçümümüz (~1.2 ms/çağrı)
  ve halilneed modeli için geliştirici beyanı.

---

## Ekler

Ekler alt ajanların ham araştırma notlarıdır. Kaynak bağlantılarını, ölçüm etiketlerini ve
"doğrulanamadı" işaretlerini içerirler.

1. [Guardrail framework'leri ve policy engine'ler](ekler/01-frameworks-policy.md)
2. [Prompt injection ve content safety modelleri](ekler/02-models.md)
3. [PII, secret detection ve Türkçe normalizasyon](ekler/03-pii-secrets-turkish.md)
4. [Entegrasyon noktaları (LiteLLM, Claude Code, Hermes, MCP, A2A)](ekler/04-integrations.md)
5. [Değerlendirme framework'leri, veri setleri ve metodoloji](ekler/05-eval-datasets.md)
6. [Uyum, çerçeveler ve saldırı taksonomileri](ekler/06-compliance.md)
