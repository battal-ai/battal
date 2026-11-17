# S7: Karar kaydı

- Durum: kabul edildi
- Sürüm: 1.0.0
- İlgili ADR'ler: [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0004](../decisions/0004-policy-binding-and-playground.md)
- İlgili backlog: E8 (PBI 8.1, 8.2)
- Şema: `schemas/decision-record.schema.json`
- Test vektörleri: `testvectors/s7-audit/`
- Araştırma: [rapor §4.7](../research/index.md#47-ham-veriyi-saklamadan-izlenebilirlik),
  [Ek 6](../research/ekler/06-compliance.md) (tablo satırı 16)

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-18 | İlk taslak |
| 1.0.0 | 2026-11-18 | Kabul edildi |

## 1. Amaç ve kapsam

Bu spec, her evaluation için üretilen karar kaydını tanımlar: hangi olayların kayıt ürettiği,
kayıttaki alanlar, içerik ve kullanıcı kimliği için HMAC, kayıtların yazılması, yazım hatası
davranışı ve kayıtların bütünlüğünü doğrulayan zincir. Kayıt ham metin içermez.

**Kapsam dışı:**

- SIEM bağlayıcıları ve OpenTelemetry çıkışı (sonraki faz).
- Kayıtların saklanması, saklama süresi ve imhası. Battal kaydı yazar, saklamaz. BTK
  yönetmeliği erişim kayıtları için 2 yıl, AI Act Art. 19 ve 26(6) yüksek risk sistemleri için en
  az 6 ay öngörür; KVKK ise gereğinden uzun saklamamayı ister. Süreyi kurum belirler; Battal bir
  varsayılan önermez ([Ek 6](../research/ekler/06-compliance.md)).
- Kurcalamaya karşı koruma (WORM depolama, SIEM). Zincir (§8) kurcalamayı yalnızca tespit eder.
- Shadow mod kayıtları (shadow mod ile gelir).
- Uygulama log'ları (stderr): biçimleri bu spec'in konusu değildir; S6-LOG-001 geçerlidir.

## 2. Terimler

| Terim | Tanım |
|---|---|
| Kayıt | Bir evaluation için üretilen, `schemas/decision-record.schema.json` biçimindeki tek JSON nesnesi |
| Kanal | Evaluation'ın geldiği yol: `sdk`, `http` (`/v1/evaluate`), `litellm` |
| Sink | Kayıtların yazıldığı yer: stdout, dosya ya da SDK'da kullanıcının verdiği fonksiyon |
| Zincir | Bir sink'in kayıtlarını `seq` ve `prev_hash` ile birbirine bağlayan dizi |
| HMAC anahtarı | Segment metinlerinin ve `user_id`'nin HMAC'inde kullanılan gizli anahtar |

Diğer terimler [sözlükteki](../sozluk.md) anlamlarıyla kullanılır.

## 3. Olaylar

- **S7-EVT-001.** Her `evaluate()` çağrısı tam olarak bir kayıt **MUST** üretmelidir: `allow`
  ve fail mode kararları dahil her karar ve her S1 hatası.
- **S7-EVT-002.** `evaluate()`'e ulaşmayan istekler (S6'daki HTTP hataları; boş `texts` nedeniyle
  değerlendirilmeyen LiteLLM istekleri) kayıt **MUST NOT** üretmemelidir; bunlar uygulama
  log'una yazılır. *[doğrulama: CI]*

## 4. Kayıt

Şema: `schemas/decision-record.schema.json`. Kayıt `audit.build_record` saf fonksiyonuyla
üretilir; zaman, zincir bilgisi, anahtar ve kanal girdi olarak verilir (§9).

| Alan | Kaynak |
|---|---|
| `record_version` | `1` |
| `type` | `"battal.decision"` |
| `timestamp` | UTC, milisaniyeli RFC 3339 (`2026-11-18T09:30:00.125Z`) |
| `chain` | `{id, seq, prev_hash}` (§8) |
| `battal_version` | Battal paket sürümü |
| `channel` | `sdk`, `http`, `litellm` |
| `channel_result` | Kanalın çağırana döndüğü sonuç: `status` ve LiteLLM'de `action`; SDK'da yok |
| `hmac_key_id` | §6 |
| `request_id`, `checkpoint`, `tenant` | İstek; `request_id` yanıttakidir (üretilmiş olabilir) |
| `principal` | `team_id`, `key_hash` aynen; `user_id` yerine `user_id_hmac` (§6) |
| `session`, `agent`, `target` | İstekteki gibi |
| `requested_policy` | İstekteki `policy.id` |
| `segments` | Her segment için `id`, `role`, `source`, `trust`, `length`, `hmac` |
| `decision` | Yanıttaki `decision` nesnesinin tamamı |
| `rationale_code` | Yanıttaki `rationale.code` |
| `detections` | Yanıttaki `detections` |
| `edits` | Her transform edit'i için `{segment, span, replacement}` |
| `timing_ms` | Yanıttaki `timing_ms` |
| `error` | Hata kaydında `{code}` |

- **S7-REC-001.** Kayıt şemaya **MUST** uymalıdır; şema `decision` ile `error`'dan tam olarak
  birini ister.
- **S7-REC-002.** İsteğin bağlam alanları (`tenant`, `principal.team_id`, `principal.key_hash`,
  `session`, `agent`, `target`) kayda **MUST** aynen yazılmalıdır. `request_id` kararlarda
  yanıttaki değerdir.
- **S7-REC-003.** Her segment için `length` orijinal metnin code point sayısıdır; `trust`
  verilmemişse `untrusted` yazılır (S1-SEG-003); `role` ve `source` yalnızca istekte varsa
  yazılır. Segment metni kayda **MUST NOT** yazılmamalıdır.
- **S7-REC-004.** Maskelenmiş metin (`transforms[].text`) kayda **MUST NOT** yazılmamalıdır;
  yalnızca edit'lerin `span` ve `replacement` alanları yazılır. Maskeleme anonimleştirme
  değildir; maskelenmiş metin bağlamı nedeniyle hâlâ kişisel veri içerebilir.
- **S7-REC-005.** `rationale.message_tr` kayda yazılmaz; `rationale_code` yeterlidir.
  Detection'lar S1-DET-001 gereği metin içermez ve aynen yazılır.
- **S7-REC-006.** `channel` `http` ya da `litellm` ise `channel_result.status` çağırana dönen
  HTTP status'tur; `litellm`'de `channel_result.action` LiteLLM'e dönen eylemdir (S6 §7.2,
  §7.3). Böylece hatanın kanalda neye dönüştüğü (örneğin `INPUT_TOO_LARGE` → `BLOCKED`) kayıtta
  görülür.

## 5. Hata kayıtları

- **S7-ERR-001.** Hata `UNSUPPORTED_API_VERSION` ya da `INVALID_REQUEST` ise istek
  doğrulanmamıştır; kayda istekten yalnızca S1-REQ-004'e uyan `request_id` ve S1 enum'undaki
  `checkpoint` alınır. Diğer alanlar **MUST NOT** alınmamalıdır: geçersiz bir istekte herhangi
  bir alana PII konmuş olabilir.
- **S7-ERR-002.** Diğer hatalarda istek doğrulanmıştır; kayıt kararlardaki gibi bağlam,
  `requested_policy` ve segment'leri **MUST** içermeli, `decision`, `rationale_code`,
  `detections` ve `edits` içermemelidir. (`POLICY_NOT_ALLOWED` denemeleri bu sayede hangi key'den
  geldiğiyle birlikte görülür.)
- **S7-ERR-003.** `INPUT_TOO_LARGE` kaydında segment'lerin `hmac`'i **MUST NOT**
  hesaplanmamalıdır; `length` yazılır. (Sınırı aşan metin için ek iş yapılmaz.)

## 6. HMAC

- **S7-HMAC-001.** Segment HMAC'i HMAC-SHA256'dır; mesaj `"battal/segment"`, bir `0x00` baytı
  ve orijinal segment metninin UTF-8 baytlarıdır. Normalizasyon uygulanmaz. Değer
  `hmac-sha256:<64 küçük hex>` biçiminde **MUST** yazılmalıdır.
- **S7-UID-001.** `principal.user_id` kayda yazılmaz; yerine `user_id_hmac` yazılır: mesaj
  `"battal/user_id"`, `0x00` ve `user_id`'nin UTF-8 baytlarıdır. `user_id` kayda düz hâliyle
  **MUST NOT** yazılmamalıdır. (LiteLLM'de `user_id` çoğu zaman bir e-posta adresidir.)
- **S7-HMAC-002.** Alan önekleri (`segment`, `user_id`) farklı olduğundan aynı değer iki alanda
  farklı HMAC üretir; bu ayrım **MUST** korunmalıdır. Yeni bir HMAC alanı yeni bir önek alır.
- **S7-HMAC-003.** `hmac_key_id`, `"battal-audit-kid"`, `0x00` ve anahtar baytlarının
  SHA-256'sının ilk 16 küçük hex hanesidir. Anahtar değiştiğinde **MUST** değişmelidir; bir
  kaydın hangi anahtarla üretildiği bu alandan anlaşılır.
- **S7-HMAC-004.** Anahtar `BATTAL_AUDIT_HMAC_KEY` ortam değişkeninin UTF-8 baytlarıdır ve en
  az 32 bayt olmalıdır; daha kısa anahtarla `battal serve` **MUST** 2 koduyla çıkmalıdır.
  *[doğrulama: CI]*
- **S7-HMAC-005.** Anahtar verilmemişse süreç başlarken kriptografik olarak güvenli 32 baytlık
  rastgele bir anahtar üretilir ve uyarı loglanır. Kayıtlar yine ham veri içermez, ama süreç
  yeniden başlatıldığında önceki kayıtlarla ilişkilendirilemez. Anahtar log'a ya da kayda
  **MUST NOT** yazılmamalıdır. *[doğrulama: CI]*

Düz SHA-256 kullanılmaz: TCKN gibi kısa ve yapısı bilinen değerlerin hash'i kaba kuvvetle geri
çevrilebilir. HMAC anahtarı olmadan bu yapılamaz.

## 7. Yazım

| Kanal | Varsayılan sink | Seçenek |
|---|---|---|
| Server (`http`, `litellm`) | stdout | `--audit-file <yol>` / `BATTAL_AUDIT_FILE`: dosyanın sonuna ekler |
| SDK (`sdk`) | yok | Kullanıcının verdiği sink fonksiyonu |

- **S7-WRT-001.** Her kayıt, kaydın RFC 8785 (JCS) kanonik JSON'u ve ardından tek bir `\n`
  olarak, tek satıra **MUST** yazılmalıdır (JSON Lines). Uygulama log'ları stdout'a yazılmaz
  (stderr), böylece stdout yalnızca kayıt taşır.
- **S7-WRT-002.** Server kaydı, yanıtı döndürmeden önce yazar ve flush eder. Aynı sink'e
  yazılan kayıtlar `seq` sırasıyla yazılır; eşzamanlı istekler `seq` ataması ve yazım için
  sıraya alınır. *[doğrulama: CI]*
- **S7-WRT-003.** Dosya rotasyonu Battal'ın işi değildir (`logrotate` vb.); Battal dosyayı
  yalnızca ekleme modunda açar. *[doğrulama: CI]*
- **S7-WRT-004.** Kayıt yazılamazsa (`audit_failure`, varsayılan `open`):
    - `open`: karar yine döner; hata stderr'e loglanır.
    - `closed`: server **MUST** 503 ve S6'daki `AUDIT_UNAVAILABLE` koduyla dönmelidir; karar
      çağırana iletilmez. LiteLLM'de bu, `unreachable_fallback` ayarını devreye sokar.

    Ayar: `--audit-failure open|closed` / `BATTAL_AUDIT_FAILURE`. *[doğrulama: CI]*
- **S7-WRT-005.** SDK, sink verilmemişse kayıt üretmez ve hiçbir yere yazmaz; verilmişse her
  `evaluate()` sonrası kaydı sink'e verir. SDK kendi süreç zincirini tutar. *[doğrulama: CI]*

## 8. Bütünlük zinciri

- **S7-CHN-001.** Her sink için süreç başlarken 32 küçük hex hanelik rastgele bir `chain.id`
  üretilir; `seq` 0'dan başlar ve her kayıtta bir artar. Farklı `chain.id`'li kayıtlar aynı
  dosyada iç içe bulunabilir (çok worker'lı kurulum) ve **MUST** ayrı zincirler olarak
  doğrulanmalıdır.
- **S7-CHN-002.** `prev_hash`, aynı zincirdeki bir önceki kaydın satırının (sondaki `\n`
  hariç) UTF-8 baytlarının SHA-256'sıdır: `sha256:<64 küçük hex>`. İlk kayıtta (`seq` = 0)
  **MUST** `null` olmalıdır.
- **S7-CHN-003.** `audit.verify_chain` satırları sırayla okur ve şu sorunları bildirir:

    | Kod | Ne zaman |
    |---|---|
    | `LINE_NOT_JSON` | Satır JSON değil |
    | `SCHEMA_INVALID` | Kayıt şemaya uymuyor |
    | `NOT_CANONICAL` | Satır, kaydın JCS biçimi değil |
    | `SEQ_GAP` | Aynı zincirde `seq` bir öncekinin bir fazlası değil |
    | `PREV_HASH_MISMATCH` | `prev_hash`, önceki satırın hash'i değil |

    Sonuç `{"valid", "issues"}`'tur; `issues` her biri `{line, code}` olan, satır sırasıyla
    dizilmiş bir listedir (satırlar 1'den başlar). Bildirimler **MUST** bu tabloya uymalıdır.
- **S7-CHN-004.** Bir zincirin dosyada görülen ilk kaydının `seq`'i 0 değilse (rotasyon) önceki
  kayda bağlılığı denetlenmez. Zincirin son kaydındaki değişiklik ya da sondan silinen kayıtlar
  bu yöntemle bulunamaz; bu sınır bilinçlidir ve kurcalamaya karşı koruma WORM depolama ya da
  SIEM'in işidir. *[doğrulama: S7 vektörleri, `son-kayit-degisimi`, `ortadan-baslayan`]*
- **S7-CLI-001.** `battal audit verify <dosya>`, dosyayı `audit.verify_chain` ile doğrular;
  çıkış kodu sorun yoksa 0, sorun varsa 1, dosya okunamıyorsa 2 olur. *[doğrulama: CI]*

## 9. Ham PII denetimi

- **S7-PII-001.** S7 vektörlerinin ürettiği bütün kayıtlardaki string değerler S3
  detector'larından geçirildiğinde sıfır detection **MUST** çıkmalıdır. Hash biçimindeki
  alanlar (`hmac`, `user_id_hmac`, `prev_hash`, `bundle_hash`, `key_hash`, `hmac_key_id`,
  `chain.id`) taranmaz: hex dizileri içinde tesadüfen TCKN ya da telefon biçiminde rakam dizisi
  bulunabilir. Vektör girdileri bilinçli olarak TCKN, e-posta ve e-posta biçiminde `user_id`
  içerir. *[doğrulama: CI]*

## 10. Hata ve sınır durumları

| Durum | Davranış | Gereklilik |
|---|---|---|
| Geçersiz istek | Yalnızca `request_id`, `checkpoint`, `error.code` | S7-ERR-001 |
| `POLICY_NOT_ALLOWED`, `NO_BUNDLE_LOADED` | Bağlam ve segment'ler, karar yok | S7-ERR-002 |
| Çok büyük girdi | Segment uzunlukları, HMAC yok | S7-ERR-003 |
| Boş segment metni | `length` 0, HMAC boş mesajın HMAC'i | S7-REC-003, S7-HMAC-001 |
| HMAC anahtarı yok | Geçici anahtar, uyarı | S7-HMAC-005 |
| Kayıt yazılamıyor | `audit_failure`'a göre | S7-WRT-004 |

## 11. Ölçüm bekleyen değerler

Yok. Kayıt yazımının gecikmeye etkisi E6.1 yük testinde ayrıca raporlanır.

## 12. Normatif örnekler (vektörler)

| Suite | Function | Ne test eder |
|---|---|---|
| `s7-audit/build-record.json` | `audit.build_record` | Alanlar, HMAC, hata kayıtları |
| `s7-audit/verify-chain.json` | `audit.verify_chain` | Zincir doğrulama ve sorun kodları |

- `audit.build_record`: `input` = `{"request", "result", "context"}`. `request` istemcinin
  gönderdiği JSON'dur (geçersiz olabilir); `result` bir `EvaluationResponse` ya da
  `EvaluationError`'dır; `context` = `{"timestamp", "chain_id", "seq", "prev_hash",
  "hmac_key", "channel", "battal_version", "channel_result"?}`. Çıktı kaydın kendisidir.
- `audit.verify_chain`: `input` = `{"lines": [...]}` (sondaki `\n` olmadan satırlar); çıktı
  `{"valid", "issues"}`.

## 13. Uyumluluk

- `record_version` 1'dir. Kayda isteğe bağlı alan eklemek geriye uyumludur; alan kaldırmak,
  anlamını değiştirmek, HMAC ya da zincir hesabını değiştirmek `record_version`'ı artırır.
- Kayıtları okuyan araçlar bilinmeyen alanları **SHOULD** yok saymalıdır.
- Rust motoru (E11) yalnızca çekirdeğin yerini alır; `audit` modülü Python'da kalır.
