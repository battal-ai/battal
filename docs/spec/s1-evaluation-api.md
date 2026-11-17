# S1: Evaluation API sözleşmesi

- Durum: kabul edildi
- Sürüm: 1.0.0
- İlgili ADR'ler: [ADR 0001](../decisions/0001-product-shape-and-licensing.md),
  [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0004](../decisions/0004-policy-binding-and-playground.md)
- İlgili backlog: E1 (PBI 1.1, 1.2)
- Şema: `schemas/evaluation-request.schema.json`, `schemas/evaluation-response.schema.json`,
  `schemas/evaluation-error.schema.json`
- Test vektörleri: `testvectors/s1-api/`

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-17 | İlk taslak |
| 1.0.0 | 2026-11-17 | Kabul edildi |

## 1. Amaç ve kapsam

Bu spec, Battal'a gönderilen değerlendirme isteğinin (`EvaluationRequest`), dönen yanıtın
(`EvaluationResponse`) ve hatanın (`EvaluationError`) yapısını; `evaluate()` fonksiyonunun ne zaman
karar döndürüp ne zaman hata verdiğini tanımlar. SDK (in-process) ve Battal Server aynı sözleşmeyi
kullanır.

**Kapsam dışı:**

- HTTP endpoint'leri, status kodları, body boyut sınırı ve LiteLLM eşlemesi: S6.
- Normalizasyon ve görünümler: S2. Detector'ların ürettiği alanların ayrıntısı: S3, S4.
- Policy, binding, bundle, kural değerlendirme ve fail mode'un policy'de nasıl tanımlandığı: S5.
- Karar kaydının alanları: S7.

## 2. Terimler

Terimler [sözlükteki](../sozluk.md) anlamlarıyla kullanılır: evaluation, checkpoint, segment,
source, trust, principal, tenant, target, detection, decision, action, transform, rationale,
degraded, fail mode, binding, taban policy, bundle.

## 3. Genel kurallar

- **S1-GEN-001.** Bütün alan adları **MUST** snake_case olmalıdır.
- **S1-GEN-002.** Bütün span'ler S0-SPAN-001'e uyar: orijinal segment metninde, code point
  cinsinden, yarı açık `[start, end)` aralığı. *[doğrulama: S2, S3 vektörleri]*
- **S1-GEN-003.** İsteğe bağlı bir alanın yokluğu, alanın gönderilmemesiyle ifade edilir. İstekte
  isteğe bağlı alanlara `null` değeri **MUST NOT** verilmemelidir; `null` içeren istek
  `INVALID_REQUEST` ile reddedilir.

## 4. İstek: `EvaluationRequest`

Şema: `schemas/evaluation-request.schema.json`.

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `api_version` | string | evet | `"v1"` |
| `request_id` | string | hayır | Çağıranın kimliği; yoksa Battal üretir |
| `checkpoint` | enum | evet | `input`, `output`, `retrieval`, `tool_call`, `tool_result`, `memory_write` |
| `tenant` | string | hayır | Tenant kimliği |
| `principal` | object | hayır | `user_id`, `team_id`, `key_hash` (hepsi isteğe bağlı string) |
| `session` | object | hayır | `id` (string), `turn` (≥ 0 tam sayı) |
| `agent` | object | hayır | `id` (string), `name` (string) |
| `target` | object | hayır | `model`, `provider_region` (string) |
| `policy` | object | hayır | `id` (string): istenen spesifik policy |
| `segments` | array | evet | En az bir segment |

**Segment:**

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | integer ≥ 0 | evet | İstek içinde benzersiz |
| `text` | string | evet | Boş olabilir |
| `role` | enum | hayır | `system`, `user`, `assistant`, `tool` |
| `source` | enum | hayır | `user`, `system`, `model`, `tool`, `retrieval` |
| `trust` | enum | hayır | `trusted`, `untrusted`; varsayılan `untrusted` |

- **S1-REQ-001.** İstek **MUST** `api_version`, `checkpoint` ve `segments` alanlarını
  içermelidir.
- **S1-REQ-002.** Şemada tanımlı olmayan bir alan (istek, segment veya alt nesne düzeyinde)
  içeren istek **MUST** `INVALID_REQUEST` ile reddedilmelidir.
- **S1-REQ-003.** `request_id` gönderilmişse yanıtta **MUST** aynen dönmelidir. Gönderilmemişse
  Battal **MUST** bir kimlik üretmeli ve yanıtta döndürmelidir. *[doğrulama: CI]* (Üretilen
  değer rastgele olduğu için vektörle değil, birim testiyle doğrulanır.)
- **S1-REQ-004.** `request_id` 1–128 karakterden oluşmalı ve yalnızca `A–Z a–z 0–9 . _ : -`
  içermelidir; aksi hâlde istek **MUST** `INVALID_REQUEST` ile reddedilmelidir.
- **S1-REQ-005.** `principal.key_hash` çağıranın ürettiği opak bir değerdir. Battal ham API
  key'i **MUST NOT** kabul etmemelidir; şemada ham key için bir alan yoktur.
  *[doğrulama: şema]*
- **S1-REQ-006.** `session` ve `agent` MVP'de kararı **MUST NOT** etkilememelidir; yalnızca
  karar kaydına aktarılır. *[doğrulama: S5 vektörleri]*
- **S1-REQ-007.** `policy` alanında yalnızca `id` bulunur. Policy sürümü istekte seçilemez;
  yüklü bundle'daki sürüm kullanılır ve yanıtta döner. *[doğrulama: şema]*

### 4.1 Segment kuralları

- **S1-SEG-001.** `segments` en az bir eleman **MUST** içermelidir.
- **S1-SEG-002.** Segment `id` değerleri istek içinde **MUST** benzersiz olmalıdır; aksi hâlde
  istek `INVALID_REQUEST` ile reddedilir.
- **S1-SEG-003.** `trust` gönderilmemişse segment **MUST** `untrusted` kabul edilmelidir.
- **S1-SEG-004.** `role` veya `source` gönderilmemişse değer "bilinmiyor" kabul edilir; Battal
  bu alanlar için varsayılan bir değer **MUST NOT** uydurmamalıdır. Bu alanlara dayanan policy
  koşulları eşleşmez (S5).
- **S1-SEG-005.** MVP yalnızca metin segment'lerini destekler. Segment'in sırası, `segments`
  dizisindeki sırasıdır ve yanıtta korunur. *[doğrulama: S6 vektörleri]*

### 4.2 Desteklenen checkpoint'ler

- **S1-CHK-001.** Enum altı checkpoint'i de içerir. MVP'de yalnızca `input` ve `output`
  desteklenir; diğerleri için `evaluate()` **MUST** `CHECKPOINT_NOT_SUPPORTED` hatası
  vermelidir.

### 4.3 Girdi sınırları

| Sınır | Anlamı | Varsayılan |
|---|---|---|
| `max_segments` | Bir istekteki segment sayısı | TBD (E6.1 yük testi) |
| `max_segment_code_points` | Tek bir segment metninin code point sayısı | TBD (E6.1 yük testi) |
| `max_total_code_points` | Bütün segment metinlerinin toplam code point sayısı | TBD (E6.1 yük testi) |

- **S1-LIM-001.** Sınırlar config ile ayarlanabilir **MUST** olmalıdır.
  *[doğrulama: CI]*
- **S1-LIM-002.** Herhangi bir sınır aşılırsa `evaluate()` **MUST** `INPUT_TOO_LARGE` hatası
  vermeli ve hiçbir detector'ı çalıştırmamalıdır.
- **S1-LIM-003.** Sınırlar orijinal metnin code point sayısı üzerinden, normalizasyon ve
  pencerelemeden **önce** uygulanır. Sınıra eşit girdi kabul edilir, aşan girdi reddedilir.

## 5. Yanıt: `EvaluationResponse`

Şema: `schemas/evaluation-response.schema.json`.

| Alan | Tip | Açıklama |
|---|---|---|
| `api_version` | string | `"v1"` |
| `request_id` | string | İstekteki ya da üretilen kimlik |
| `decision` | object | Bkz. §5.1 |
| `detections` | array | Bkz. §5.2 |
| `transforms` | array | Bkz. §5.3 |
| `rationale` | object | `code`, `message_tr`; bkz. §5.4 |
| `timing_ms` | object | Aşama süreleri; anahtarlar bilgi amaçlıdır |

### 5.1 Decision

| Alan | Tip | Açıklama |
|---|---|---|
| `action` | enum | `allow`, `mask`, `block`, `ask` |
| `rule_id` | string \| null | Kararı belirleyen kural; kural eşleşmediyse veya fail mode uygulandıysa `null` |
| `policy` | object | Kararı veren policy'nin `id` ve `version` değerleri; fail mode'da taban policy |
| `bundle_hash` | string | Yüklü bundle'ın içerik hash'i |
| `matched_bindings` | string[] | Eşleşen binding kimlikleri; taban policy'ninki ilk sırada |
| `decided_by` | object | `kind` (`rule`, `default`, `fail_mode`) ve `binding` (string \| null) |
| `fail_mode` | enum | Bu checkpoint için geçerli fail mode: `open`, `closed` |
| `degraded` | boolean | Karar, bir detector çalışmadan verildiyse `true` |

- **S1-DEC-001.** `decided_by.kind` değeri: bir kural kararı belirlediyse `rule` (ve `binding`
  o kuralın geldiği binding), hiçbir kural eşleşmediyse `default` (S5'teki varsayılan action),
  fail mode uygulandıysa `fail_mode` (`binding` = `null`) **MUST** olmalıdır.
  *[doğrulama: S5 vektörleri]*
- **S1-DEC-002.** `rule_id`, yalnızca `decided_by.kind` `rule` ise **MUST** dolu olmalıdır;
  diğer durumlarda `null`'dır.
- **S1-DEC-003.** `matched_bindings` taban policy'nin binding'ini her zaman **MUST** ilk sırada
  içermelidir. *[doğrulama: S5 vektörleri]*

### 5.2 Detections

Her detection en az şu alanları içerir: `detector` (string), `version` (string), `segment`
(integer), `span` (`[start, end]`). Detector'a özgü ek alanlar (`raw_score`, `calibrated`,
`threshold`, `checksum_valid`, `context_hit`…) S3 ve S4'te tanımlanır.

- **S1-DET-001.** Yanıt, detection'ın eşleştiği metni ya da onun herhangi bir parçasını hiçbir
  alanda **MUST NOT** içermemelidir. Detection'lar konumu yalnızca `segment` ve `span` ile
  bildirir. Şema, detection nesnelerinde `text`, `value`, `match` ve `excerpt` alanlarını yasaklar.
- **S1-DET-002.** Model skorları yalnızca `raw_score` adıyla ve `calibrated` alanıyla birlikte
  verilir; kalibre edilmemiş skor olasılık olarak **MUST NOT** sunulmamalıdır.
  *[doğrulama: S4 vektörleri]*

### 5.3 Transforms

| Alan | Tip | Açıklama |
|---|---|---|
| `segment` | integer | Maskelenen segment'in `id`'si |
| `text` | string | Segment'in maskelenmiş tam metni |
| `edits` | array | `{span, replacement}`; span orijinal metne göre |

- **S1-TRF-001.** `transforms` yalnızca metni değişen segment'leri **MUST** içermelidir; her
  segment en fazla bir kez geçer.
- **S1-TRF-002.** `edits` span'e göre artan sırada olmalı ve span'ler **MUST NOT**
  çakışmamalıdır.
- **S1-TRF-003.** `text`, orijinal segment metnine `edits` uygulanarak elde edilen metne
  **MUST** eşit olmalıdır.
- **S1-TRF-004.** `action` `mask` değilse `transforms` **MUST** boş olmalıdır.
  *[doğrulama: S5 vektörleri]*

### 5.4 Rationale

- **S1-RAT-001.** `action` `block`, `mask` veya `ask` ise `rationale` **MUST** bulunmalıdır;
  `allow` ise **MAY** bulunmayabilir. *[doğrulama: S5 vektörleri]*
- **S1-RAT-002.** `rationale.message_tr` son kullanıcıya gösterilebilecek Türkçe bir metindir;
  detector adı, skor, span ya da eşleşen metin **MUST NOT** içermemelidir.
  *[doğrulama: S5 vektörleri]*

## 6. Hata: `EvaluationError`

Şema: `schemas/evaluation-error.schema.json`. Biçim: `{"error": {"code", "message",
"request_id"}}`; `request_id` istekten okunabildiyse bulunur.

| Kod | Ne zaman |
|---|---|
| `UNSUPPORTED_API_VERSION` | `api_version` desteklenmiyor |
| `INVALID_REQUEST` | İstek şemaya göre geçersiz, bilinmeyen alan, `null`, tekrarlanan segment `id`'si |
| `CHECKPOINT_NOT_SUPPORTED` | Checkpoint bu sürümde desteklenmiyor |
| `INPUT_TOO_LARGE` | Girdi sınırı aşıldı |
| `NO_BUNDLE_LOADED` | Yüklü ve geçerli bir bundle yok |
| `POLICY_NOT_ALLOWED` | İstenen `policy.id` bu bağlam için izinli değil ya da yok |

- **S1-ERR-001.** Bir istekte birden fazla sorun varsa, dönen hata **MUST** şu sıradaki ilk
  sorunun kodu olmalıdır: `UNSUPPORTED_API_VERSION`, `INVALID_REQUEST`,
  `CHECKPOINT_NOT_SUPPORTED`, `INPUT_TOO_LARGE`, `NO_BUNDLE_LOADED`, `POLICY_NOT_ALLOWED`.
- **S1-ERR-002.** Var olmayan bir `policy.id` ile izinli olmayan bir `policy.id` aynı kodla
  (`POLICY_NOT_ALLOWED`) **MUST** reddedilmelidir; hata, policy'nin var olup olmadığını
  açığa vermez. *[doğrulama: S5 vektörleri]*
- **S1-ERR-003.** Hata `message` alanı bilgi amaçlıdır; istekteki segment metnini **MUST NOT**
  içermemelidir. *[doğrulama: CI]* (S0-CMP-008 gereği mesajlar vektörlerde karşılaştırılmaz.)

## 7. `evaluate()` davranışı

```text
evaluate(request) -> EvaluationResponse | EvaluationError
```

- **S1-EVAL-001.** `evaluate()`, §6'daki koşullardan biri varsa **MUST** hata vermeli ve karar
  döndürmemelidir. Bu koşullar çağıranın düzeltebileceği durumlardır.
- **S1-EVAL-002.** İstek geçerli ve bir bundle yüklüyse `evaluate()` **MUST** her zaman bir
  karar döndürmelidir; iç arızalar hata olarak dışarı sızmaz. *[doğrulama: S5 vektörleri]*
- **S1-EVAL-003.** Bir model detector'ı çalışmazsa (yüklenemedi, timeout, çöktü) karar kalan
  detector'lar ve deterministik kurallarla verilir ve `degraded` **MUST** `true` olmalıdır.
  *[doğrulama: S5 vektörleri]*
- **S1-EVAL-004.** Karar hiç verilemiyorsa (örneğin policy değerlendirmesi çöktü), checkpoint'in
  fail mode'u uygulanır: `closed` ise `action` `block`, `open` ise `allow` **MUST** olmalı;
  `decided_by.kind` `fail_mode` ve `degraded` `true` olur. *[doğrulama: S5 vektörleri]*
- **S1-EVAL-005.** `evaluate()` isteği değiştirmez ve dışarıya yazmaz; karar kaydı yazımı
  `audit` modülünün işidir (S7). *[doğrulama: CI]*

## 8. Normatif örnekler (vektörler)

Bu spec'in deterministik kısmı, isteği ayrıştıran ve doğrulayan fonksiyonla test edilir. Karar
üreten davranış (S1-DEC, S1-EVAL) bundle gerektirdiği için S5 vektörlerinde test edilir.

| Suite | Function | Ne test eder |
|---|---|---|
| `s1-api/parse-request.json` | `contract.parse_request` | İstek doğrulama, varsayılanlar, hata önceliği, sınırlar |
| `s1-api/validate-response.json` | `contract.validate_response` | Yanıt şeması ve S1-DET-001, S1-TRF kuralları |

- `contract.parse_request`: `input` = `{"request": <json>, "limits"?: {...}, "supported_checkpoints"?: [...]}`.
  Çıktı: varsayılanları uygulanmış istek. Hata durumunda `expected_error`.
  `supported_checkpoints` verilmezse `["input", "output"]` kabul edilir; `limits` verilmezse
  sınır uygulanmaz (vektörlerin TBD varsayılanlara bağlı olmaması için).
- `contract.validate_response`: `input` = `{"response": <json>, "segments"?: [...]}`. Çıktı:
  `{"valid": bool, "issues": [...]}`. `segments` verilirse S1-TRF-003 de denetlenir. Sorun
  kodları: `SCHEMA_INVALID`, `TRANSFORM_TEXT_MISMATCH`, `TRANSFORM_EDITS_OVERLAP`,
  `TRANSFORM_DUPLICATE_SEGMENT`, `RULE_ID_INCONSISTENT`.

## 9. Uyumluluk

- `api_version` `"v1"`'dir. İsteğe yeni isteğe bağlı alan eklemek ve yanıta yeni alan eklemek
  geriye uyumludur; alan kaldırmak, anlamını değiştirmek veya isteğe zorunlu alan eklemek
  `api_version`'ı artırır.
- **S1-VER-001.** Yanıtı okuyan istemciler bilinmeyen alanları **SHOULD** yok saymalıdır.
- Rapordaki §4.4 örneği bu spec'ten önce yazılmıştır; farklar: `policy.version` istekten
  kaldırıldı, `decision` alanına `bundle_hash`, `matched_bindings` ve `decided_by` eklendi,
  `transforms` alanına `edits` eklendi, `agent: null` yerine alan gönderilmez.
