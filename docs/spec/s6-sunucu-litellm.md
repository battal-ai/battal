# S6: Sunucu ve LiteLLM adapter'ı

- Durum: kabul edildi
- Sürüm: 1.0.0
- İlgili ADR'ler: [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0004](../decisions/0004-policy-binding-and-playground.md)
- İlgili backlog: E6 (PBI 6.1, 6.2)
- Şema: `schemas/http-error.schema.json`
- Test vektörleri: `testvectors/s6-server/`
- Araştırma: [Ek 4 §1.4](../research/ekler/04-integrations.md),
  [rapor §4.6](../research/index.md#46-hata-ve-erisilemezlik)

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-18 | İlk taslak |
| 1.0.0 | 2026-11-18 | Kabul edildi |

## 1. Amaç ve kapsam

Bu spec, Battal Server'ın HTTP arayüzünü tanımlar: endpoint'ler, status kodları, kimlik
doğrulama, gövde boyutu sınırı, health ve readiness, bundle'ın yeniden yüklenmesinin tetiklenmesi,
`battal serve` ayarları ve LiteLLM Generic Guardrail API adapter'ı. Server, S1'deki `evaluate()`
fonksiyonunu çağırır; kendi karar mantığı yoktur.

**Kapsam dışı:**

- Playground (`--playground`, E18), output streaming (E14), MCP modları (`pre_mcp_call` vb.,
  E15), `tool_calls` ve `tools` denetimi (E12), `/metrics` endpoint'i (PBI 6.4).
- Karar kaydının alanları ve yazımı: S7.
- `docker compose` demosu (PBI 6.3): README'de anlatılır, spec konusu değildir.
- TLS sonlandırma: Battal düz HTTP konuşur; TLS, ingress ya da service mesh'in işidir.
- `surface` boyutu: S1'de alanı yoktur, binding'de MVP'de çalışmaz (E13).

## 2. Terimler

| Terim | Tanım |
|---|---|
| Adapter | Bir dış sistemin istek biçimini `EvaluationRequest`'e, kararı da o sistemin yanıt biçimine çeviren katman |
| LiteLLM payload | LiteLLM'in `generic_guardrail_api` guardrail'inin Battal'a gönderdiği JSON gövdesi |
| HTTP hatası | Evaluation'a ulaşmadan HTTP katmanında verilen hata (`HttpError`) |
| Loopback adresi | `127.0.0.0/8`, `::1` ya da `localhost` |

Diğer terimler [sözlükteki](../sozluk.md) anlamlarıyla kullanılır.

## 3. Endpoint'ler

| Metot | Yol | Kimlik doğrulama | Ne yapar |
|---|---|---|---|
| `POST` | `/v1/evaluate` | evet | S1 `evaluate()` |
| `POST` | `/beta/litellm_basic_guardrail_api` | evet | LiteLLM adapter'ı (§7) |
| `GET` | `/healthz` | hayır | Liveness (§8) |
| `GET` | `/readyz` | hayır | Readiness (§8) |

LiteLLM, guardrail config'indeki `api_base`'in sonuna `/beta/litellm_basic_guardrail_api`
ekler; bu yüzden `api_base` Battal'ın kök adresidir (`http://battal:8080`).

## 4. Genel HTTP kuralları

- **S6-HTTP-001.** Bir istek şu sırayla denetlenir ve ilk başarısız denetimin yanıtı döner:
  yol ve metot (S6-HTTP-002), kimlik doğrulama (§5), gövde boyutu (S6-HTTP-004), içerik türü ve
  JSON (S6-HTTP-003), ardından endpoint'in kendi kuralları. Sıra **MUST** bu olmalıdır.
- **S6-HTTP-002.** Tanımsız yol **MUST** 404 `NOT_FOUND`, tanımlı yola yanlış metot **MUST**
  405 `METHOD_NOT_ALLOWED` ile dönmelidir.
- **S6-HTTP-003.** `POST` gövdesi `Content-Type: application/json` olmalıdır (medya türü
  büyük-küçük harf duyarsız, `charset` gibi parametreler serbest), UTF-8 olmalı ve JSON olarak
  ayrıştırılabilmelidir; aksi hâlde istek **MUST** 400 ile ve `INVALID_REQUEST` koduyla
  reddedilmelidir. Başlık adları büyük-küçük harf duyarsızdır.
- **S6-HTTP-004.** Gövde `max_body_bytes`'tan büyükse istek ayrıştırılmadan **MUST** 413 ile ve
  `INPUT_TOO_LARGE` koduyla reddedilmelidir. `Content-Length` sınırı aşıyorsa gövde okunmaz;
  `Content-Length` yoksa ya da gövde `chunked` gönderilmişse okuma sınır aşıldığı anda kesilir.
  Sınıra eşit gövde kabul edilir. Bu sınır bayt cinsindendir ve S1 §4.3'teki code point
  sınırlarına ek olarak uygulanır.
- **S6-HTTP-005.** Evaluation'a ulaşmadan verilen hatalar (`UNAUTHORIZED`, `NOT_FOUND`,
  `METHOD_NOT_ALLOWED`, `INTERNAL`) `schemas/http-error.schema.json` biçimindedir; S1 kodlarıyla
  verilen hatalar (`INVALID_REQUEST`, `INPUT_TOO_LARGE`…) `EvaluationError` biçimindedir. İkisi de
  `{"error": {"code", "message"}}` yapısındadır. *[doğrulama: şema]*
- **S6-HTTP-006.** Beklenmeyen bir istisna **MUST** 500 `INTERNAL` ile dönmeli; `message` genel
  bir metin olmalı, istisna ayrıntısı ve istek içeriği yanıta yazılmamalıdır. *[doğrulama: CI]*
- **S6-LOG-001.** Server, istek ve yanıt gövdelerini, segment metinlerini, `x-api-key` ve
  `Authorization` başlıklarının değerlerini **MUST NOT** loglamamalıdır. *[doğrulama: CI]*

## 5. Kimlik doğrulama

Battal kullanıcıyı doğrulamaz (principal bilgisini çağırandan alır). Bu bölüm yalnızca çağıranın
yetkili bir istemci (LiteLLM ya da bir uygulama) olduğunu doğrular.

- **S6-AUTH-001.** `BATTAL_API_KEY` ayarlıysa `/v1/evaluate` ve LiteLLM route'u, `x-api-key`
  başlığı ya da `Authorization: Bearer <anahtar>` başlığı anahtara eşit değilse **MUST** 401
  `UNAUTHORIZED` ile dönmelidir. İki başlıktan biri eşleşirse istek kabul edilir. LiteLLM,
  guardrail config'indeki `api_key`'i `x-api-key` başlığıyla gönderir.
- **S6-AUTH-002.** `/healthz` ve `/readyz` kimlik doğrulama **MUST NOT** istememelidir.
- **S6-AUTH-003.** Anahtar karşılaştırması sabit zamanlı (constant-time) **MUST** yapılmalıdır.
  *[doğrulama: CI]*
- **S6-AUTH-004.** `--host` loopback dışı bir adresse ve `BATTAL_API_KEY` ayarlı değilse
  `battal serve` **MUST** başlamayı reddetmeli ve 2 koduyla çıkmalıdır. Bu yalnızca
  `--insecure-no-auth` bayrağıyla aşılabilir; bayrak kullanıldığında başlangıçta uyarı loglanır.
  *[doğrulama: CI]*

## 6. `/v1/evaluate`

Gövde S1 `EvaluationRequest`'tir; yanıt S1 `EvaluationResponse` ya da `EvaluationError`'dır.

| Sonuç | HTTP status |
|---|---|
| Karar (`allow`, `mask`, `block`, `ask`; fail mode kararı dahil) | 200 |
| `UNSUPPORTED_API_VERSION`, `INVALID_REQUEST`, `CHECKPOINT_NOT_SUPPORTED` | 400 |
| `POLICY_NOT_ALLOWED` | 403 |
| `INPUT_TOO_LARGE` | 413 |
| `NO_BUNDLE_LOADED` | 503 |

- **S6-EVAL-001.** `evaluate()` bir karar döndürürse yanıt, eylemden bağımsız olarak **MUST**
  200 olmalıdır.
- **S6-EVAL-002.** `evaluate()` bir hata döndürürse status **MUST** yukarıdaki tabloya uymalı,
  gövde `EvaluationError` olmalıdır.
- **S6-EVAL-003.** Server ile SDK aynı istek için aynı kararı **MUST** üretmelidir; server
  `evaluate()`'in sonucunu değiştirmez, yalnızca HTTP'ye çevirir. *[doğrulama: CI]*

## 7. LiteLLM adapter'ı

Adapter iki saf fonksiyondan oluşur: `litellm.to_request` (payload → `EvaluationRequest`) ve
`litellm.from_result` (sonuç → LiteLLM yanıtı). Route, ikisinin arasında `evaluate()`'i çağırır.
Payload alanları LiteLLM'in `GenericGuardrailAPIRequest` tipinden gelir
([Ek 4 §1.4](../research/ekler/04-integrations.md)).

### 7.1 İstek eşlemesi

- **S6-LLM-001.** `input_type` `request` ise checkpoint **MUST** `input`, `response` ise
  `output` olmalıdır.
- **S6-LLM-002.** `texts` dizisinin her elemanı, dizideki sırasıyla bir segment olur:
  `id` = sıra (0'dan başlar), `text` = eleman, `trust` = `untrusted`, `source` = `user`
  (`request`) ya da `model` (`response`). `role` gönderilmez. Bu eşleme **MUST** birebir
  olmalıdır; boş string de bir segment'tir.
- **S6-LLM-003.** Diğer alanlar şöyle eşlenir:

    | LiteLLM alanı | `EvaluationRequest` alanı |
    |---|---|
    | `litellm_call_id` | `request_id`; S1-REQ-004'e uymuyorsa eşlenmez |
    | `request_data.user_api_key_hash` | `principal.key_hash` |
    | `request_data.user_api_key_team_id` | `principal.team_id` |
    | `request_data.user_api_key_user_id` | `principal.user_id` |
    | `request_data.user_api_key_org_id` | `tenant` |
    | `litellm_trace_id` | `session.id` |
    | `model` | `target.model` |
    | `additional_provider_specific_params.policy_id` | `policy.id` |

    Eşleme **MUST** bu tabloya uymalıdır. `api_version` `"v1"`'dir. `policy_id`'yi istemci
    LiteLLM'de guardrail'in `extra_body`'si ile gönderir.
- **S6-LLM-004.** Tablodaki bir alan yoksa, `null` ise ya da boş string ise istekte o alan
  **MUST NOT** bulunmamalıdır (S1-GEN-003).
- **S6-LLM-005.** Payload'daki diğer alanlar (`structured_messages`, `images`, `tools`,
  `tool_calls`, `request_headers`, `litellm_version`, `request_data`'nın tablo dışı alanları ve
  bilinmeyen alanlar) **MUST** yok sayılmalıdır. Sistem prompt'u `structured_messages`'tan ayırt
  edilmez; bütün `texts` `untrusted` değerlendirilir.
- **S6-LLM-006.** `texts` yoksa ya da boşsa `evaluate()` çağrılmaz; route **MUST** 200 ve
  `{"action": "NONE"}` döndürmelidir. (MVP'de değerlendirilecek başka içerik türü yoktur.)
- **S6-LLM-007.** Payload bir nesne değilse; `input_type` yoksa ya da `request`/`response`
  değilse; `texts` dizi değilse ya da string olmayan eleman içeriyorsa; `request_data` ya da
  `additional_provider_specific_params` nesne değilse; tablodaki bir alan `null` ya da string
  dışında bir değer taşıyorsa payload **MUST** `INVALID_REQUEST` ile reddedilmelidir.

### 7.2 Yanıt eşlemesi

| Karar | LiteLLM yanıtı |
|---|---|
| `allow` | `{"action": "NONE"}` |
| `mask` | `{"action": "GUARDRAIL_INTERVENED", "texts": [...]}` |
| `block` | `{"action": "BLOCKED", "blocked_reason": "..."}` |
| `ask` | `block` ile aynı |

- **S6-LLM-010.** `allow` **MUST** `{"action": "NONE"}` olmalıdır.
- **S6-LLM-011.** `mask` için `texts`, gönderilen `texts` ile aynı uzunlukta ve sırada **MUST**
  olmalıdır: `transforms`'ta bulunan segment'in yerine onun `text`'i, bulunmayanın yerine
  gönderilen metin aynen yazılır.
- **S6-LLM-012.** `block` için `blocked_reason` **MUST** `rationale.message_tr` + ` (karar: ` +
  `request_id` + `)` olmalıdır. LiteLLM bu metni istemciye aynen iletir; S1-RAT-002 gereği
  detector ayrıntısı içermez.
- **S6-LLM-013.** `ask` gateway yüzeyinde **MUST** `block` gibi eşlenmelidir (ADR 0004 karar 8).
- Bütün kararlar 200 ile döner; LiteLLM `BLOCKED`'ı istemciye kendisi 400 olarak iletir.

### 7.3 Hata eşlemesi

LiteLLM'in hata ayarları kabadır: `fail_on_error` (varsayılan açık) her 2xx olmayan yanıtta
isteği engeller; `unreachable_fallback` yalnızca ağ hatası, timeout ve 502/503/504'te uygulanır.
Bu yüzden policy'nin bildiği durumlar 2xx kararlara çevrilir.

| `evaluate()` hatası | Yanıt |
|---|---|
| `INPUT_TOO_LARGE`, fail mode `closed` | 200 `BLOCKED`, "İstek değerlendirilemeyecek kadar büyük." |
| `INPUT_TOO_LARGE`, fail mode `open` | 200 `NONE` |
| `POLICY_NOT_ALLOWED` | 200 `BLOCKED`, "İstenen policy kullanılamıyor." |
| `NO_BUNDLE_LOADED`; bundle yokken `INPUT_TOO_LARGE` | 503, `EvaluationError` |
| `UNSUPPORTED_API_VERSION`, `INVALID_REQUEST`, `CHECKPOINT_NOT_SUPPORTED` | 400, `EvaluationError` |

- **S6-LLM-014.** `INPUT_TOO_LARGE` hatasında yüklü bundle'ın isteğin checkpoint'i için fail
  mode'u (S5-BND-003) uygulanır ve yanıt **MUST** tabloya uymalıdır. `blocked_reason`'ın sonuna,
  hatada `request_id` varsa S6-LLM-012'deki gibi karar kimliği eklenir.
- **S6-LLM-015.** Bundle yüklü değilse yanıt **MUST** 503 olmalıdır; LiteLLM'in
  `unreachable_fallback` ayarı uygulanır.
- **S6-LLM-016.** `POLICY_NOT_ALLOWED` fail mode'dan bağımsız olarak **MUST** `BLOCKED`
  olmalıdır.
- **S6-LLM-017.** Geçersiz payload (S6-LLM-007) ve diğer S1 istek hataları **MUST** 400 ile
  dönmelidir; LiteLLM'in `fail_on_error` ayarı uygulanır.
- **S6-LLM-018.** Bayt sınırı (S6-HTTP-004) LiteLLM route'unda da 413 döner: gövde
  okunmadığından checkpoint ve fail mode bilinemez; LiteLLM `fail_on_error` ile isteği engeller.
  *[doğrulama: S6 vektörleri, `litellm-govde-sinir-asimi`]*

### 7.4 LiteLLM tarafındaki config

- **S6-LLM-020.** Battal, LiteLLM'in hangi modda (`pre_call`, `during_call`, `post_call`)
  çağırdığını bilemez. `input` için yalnızca `pre_call`, `output` için yalnızca `post_call`
  **SHOULD** kullanılmalıdır; `during_call` maskeleme yapamaz. `fail_on_error: false`
  **MUST NOT** kullanılmamalıdır (rapor §4.6). *[doğrulama: README örneği]*

Örnek (normatif değildir; `timeout` değeri E6.1 ölçümüyle belirlenir):

```yaml
guardrails:
  - guardrail_name: battal-input
    litellm_params:
      guardrail: generic_guardrail_api
      mode: pre_call
      api_base: http://battal:8080
      api_key: os.environ/BATTAL_API_KEY
      unreachable_fallback: fail_closed
      default_on: true
      timeout: TBD
  - guardrail_name: battal-output
    litellm_params:
      guardrail: generic_guardrail_api
      mode: post_call
      api_base: http://battal:8080
      api_key: os.environ/BATTAL_API_KEY
      default_on: true
      timeout: TBD
```

## 8. Health ve readiness

- **S6-HLT-001.** `/healthz`, süreç çalışıyorsa **MUST** 200 ve `{"status": "ok"}` döndürmelidir.
- **S6-HLT-002.** `/readyz`, geçerli bir bundle yüklüyse **MUST** 200 ve `{"status": "ready",
  "bundle_hash", "bundle_version"}`, yüklü değilse 503 ve `{"status": "not_ready"}`
  döndürmelidir. `bundle_version`, `bundle.yaml`'daki `version`'dır.

## 9. Bundle'ın yeniden yüklenmesi

S5 §3.4 yeniden yüklemenin atomik olmasını ve geçersiz bundle'ın eskisinin yerini almamasını
tanımlar; bu bölüm yalnızca tetiklemeyi tanımlar.

- **S6-RLD-001.** Server, bundle dizinini her `reload_interval_s` saniyede bir okur ve S5
  `bundle_hash`'i yüklü olandan farklıysa yeni bundle'ı S5 §3.4'e göre yükler.
  *[doğrulama: CI]*
- **S6-RLD-002.** `SIGHUP` sinyali alındığında server bir sonraki aralığı beklemeden bundle'ı
  **MUST** yeniden okumalıdır. *[doğrulama: CI]*
- **S6-RLD-003.** Bundle'ı yükleyen, değiştiren ya da yeniden yükleme tetikleyen bir HTTP
  endpoint'i **MUST NOT** bulunmamalıdır. *[doğrulama: S6 vektörleri, `bilinmeyen-yol`; CI]*
- **S6-RLD-004.** Başlangıçta bundle geçersizse ya da okunamıyorsa server yine de başlar,
  `/readyz` 503 döner ve evaluation'lar `NO_BUNDLE_LOADED` alır; hata loglanır ve periyodik
  okuma devam eder. *[doğrulama: CI]*

Dosya sistemi olayları (inotify vb.) kullanılmaz; container volume'larında (ConfigMap
symlink'leri) güvenilir değildir.

## 10. `battal serve` ve ayarlar

| Ayar | CLI | Ortam değişkeni | Varsayılan |
|---|---|---|---|
| Bundle dizini | `--bundle` | `BATTAL_BUNDLE` | zorunlu |
| Dinlenen adres | `--host` | `BATTAL_HOST` | `127.0.0.1` |
| Port | `--port` | `BATTAL_PORT` | `8080` |
| API key | yok | `BATTAL_API_KEY` | yok |
| Gövde sınırı | `--max-body-bytes` | `BATTAL_MAX_BODY_BYTES` | TBD (E6.1 yük testi) |
| S1 girdi sınırları | `--max-segments`, `--max-segment-code-points`, `--max-total-code-points` | `BATTAL_MAX_SEGMENTS`, `BATTAL_MAX_SEGMENT_CODE_POINTS`, `BATTAL_MAX_TOTAL_CODE_POINTS` | S1 §4.3 |
| Yeniden okuma aralığı | `--reload-interval` | `BATTAL_RELOAD_INTERVAL_S` | `5` |
| Kimlik doğrulamasız dış dinleme | `--insecure-no-auth` | yok | kapalı |

- **S6-CFG-001.** Bir ayar hem CLI'da hem ortam değişkeninde verilmişse CLI değeri **MUST**
  kullanılmalıdır. *[doğrulama: CI]*
- **S6-CFG-002.** API key yalnızca ortam değişkeniyle verilir; süreç listesinde görünmemesi için
  CLI bayrağı yoktur. `--insecure-no-auth` yalnızca CLI bayrağıdır; ortamdan yanlışlıkla
  açılmaz. *[doğrulama: CI]*
- **S6-CFG-003.** Geçersiz bir ayar değeri (negatif sınır, sayı olmayan port) **MUST**
  başlangıçta 2 koduyla çıkışa yol açmalıdır. *[doğrulama: CI]*

Config dosyası MVP'de yoktur.

## 11. OpenAPI

- **S6-API-001.** OpenAPI belgesi S1 şemalarından üretilir ve `docs/api/openapi.json` olarak
  commit'lenir. CI, üretilen belge commit'lenenden farklıysa **MUST** başarısız olmalıdır.
  *[doğrulama: CI]*

## 12. Contract test

- **S6-CT-001.** LiteLLM adapter'ı, sabitlenmiş bir LiteLLM sürümüne karşı CI'da uçtan uca test
  edilir: LiteLLM, `/guardrails/apply_guardrail` endpoint'i üzerinden Battal'ı model çağrısı
  yapmadan çağırır; allow, mask ve block için beklenen yanıt **MUST** alınmalıdır. Sürüm:
  TBD (PBI 6.2 başlangıcındaki son kararlı LiteLLM release'i). *[doğrulama: CI]*

## 13. Hata ve sınır durumları

| Durum | Davranış | Gereklilik |
|---|---|---|
| Boş `texts` (LiteLLM) | 200 `NONE`, evaluate çağrılmaz | S6-LLM-006 |
| Boş segment metni | Segment olarak değerlendirilir | S6-LLM-002 |
| Bayt sınırını aşan gövde | 413, ayrıştırılmaz | S6-HTTP-004, S6-LLM-018 |
| Code point sınırını aşan girdi | `/v1`: 413; LiteLLM: fail mode | S6-EVAL-002, S6-LLM-014 |
| Bozuk JSON, yanlış içerik türü | 400 `INVALID_REQUEST` | S6-HTTP-003 |
| Bundle yok | 503; `/readyz` 503 | S6-EVAL-002, S6-LLM-015, S6-HLT-002 |
| Motor arızası | 200, fail mode kararı (S5-FLT-002) | S6-EVAL-001 |
| Beklenmeyen istisna | 500 `INTERNAL` | S6-HTTP-006 |

## 14. Ölçüm bekleyen değerler

| Değer | Durum | Nasıl belirlenecek |
|---|---|---|
| `max_body_bytes` varsayılanı | TBD | E6.1 yük testi; S1 sınırlarıyla birlikte |
| LiteLLM `timeout` önerisi | TBD | E6.1: p99 gecikme + pay |
| Contract test LiteLLM sürümü | TBD | PBI 6.2 başlangıcı |

## 15. Normatif örnekler (vektörler)

| Suite | Function | Ne test eder |
|---|---|---|
| `s6-server/litellm-to-request.json` | `litellm.to_request` | Payload → `EvaluationRequest` |
| `s6-server/litellm-from-result.json` | `litellm.from_result` | Karar ve hata → LiteLLM yanıtı |
| `s6-server/http.json` | `server.http` | Endpoint'ler, status kodları, kimlik doğrulama, boyut, health |

- `litellm.to_request`: `input` = `{"payload"}`; çıktı = `{"request"}` ya da `{"skip": true}`
  (S6-LLM-006).
- `litellm.from_result`: `input` = `{"result", "texts", "fail_mode"?}`; `result` bir
  `EvaluationResponse` ya da `EvaluationError`'dır, `fail_mode` bundle yüklüyse isteğin
  checkpoint'inin fail mode'udur. Çıktı = `{"status", "body"}`.
- `server.http`: `input` = `{"request", "bundle"?, "config"?}`.
    - `request` = `{"method", "path", "headers"?, "body"? | "body_raw"?}`. `body` bir JSON
      değeridir ve runner onu UTF-8 JSON'a çevirir; `body_raw` gövdenin kendisidir (bozuk JSON
      ve bayt sınırı case'leri bunu kullanır). Gövde varsa ve `headers`'ta `Content-Type` yoksa
      runner `application/json` ekler.
    - `bundle` S5 vektörlerindeki biçimdedir; yoksa bundle yüklü değildir. Vektörlerdeki
      bundle'larda kural yoktur, böylece kararlar detector'lara (S3, S4) bağlı değildir.
    - `config` = `{"api_key"?, "max_body_bytes"?, "limits"?}`; verilmeyen sınır uygulanmaz.
    - Çıktı = `{"status", "body"}`. Hata gövdelerinde yalnızca `code` (ve varsa `request_id`)
      karşılaştırılır (S0-CMP-008 ile aynı gerekçe).

## 16. Uyumluluk

- LiteLLM route'unun yolu ve payload'ı LiteLLM'e aittir ve `/beta/` altındadır. LiteLLM bu
  sözleşmeyi değiştirirse adapter'ın davranışı yeni bir minor sürümle güncellenir; contract test
  (S6-CT-001) bu değişikliği yakalar.
- Yeni bir endpoint ya da ayar eklemek minor, bir status kodunu ya da eşlemeyi değiştirmek major
  sürümdür.
- Rust motoru (E11) yalnızca çekirdeğin yerini alır; server ve adapter Python'da kalır
  (`docs/mimari.md` §3.2).
