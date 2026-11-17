# Sözlük

Battal'a özgü terimlerin tek anlamı. Spec'ler, ADR'ler, kod ve dokümanlar bu terimleri buradaki
anlamlarıyla kullanır. Genel programlama terimleri (timeout, cache, interface…) burada yer almaz.

Her terimde kullanılması gereken ad kalın yazılır; aynı kavram için kullanılmaması gereken
sözcükler _Kaçın_ satırındadır.

## Değerlendirme

**Evaluation**:
Bir içeriğin Battal'a gönderilip karar alınması işlemi; tek bir `EvaluationRequest` ve onun
`EvaluationResponse`'u.
_Kaçın_: tarama, scan, kontrol (genel anlamda)

**Checkpoint**:
İçeriğin değerlendirildiği akış noktası: `input`, `output`, `retrieval`, `tool_call`,
`tool_result`, `memory_write`.
_Kaçın_: hook, aşama, stage

**Segment**:
Bir evaluation içindeki, kaynağı ve güven seviyesi ayrı tutulan tek bir metin parçası.
_Kaçın_: mesaj, chunk (RAG bağlamı dışında)

**Source**:
Bir segment'in nereden geldiği; örneğin `user`, `tool`, `retrieval`.
_Kaçın_: origin

**Trust**:
Bir segment'e ne kadar güvenildiği: `trusted` ya da `untrusted`.
_Kaçın_: güvenilirlik skoru

**Principal**:
İsteği yapan kimlik (kullanıcı, takım, key); Battal kimliği doğrulamaz, yalnızca tüketir.
_Kaçın_: kullanıcı (tek başına), identity

**Tenant**:
Policy ve kayıtların ayrıldığı en üst kurum ya da müşteri birimi.
_Kaçın_: organizasyon, hesap

**Target**:
Değerlendirilen içeriğin gideceği model ve sağlayıcı bölgesi (`target.model`,
`target.provider_region`).
_Kaçın_: hedef model (alan adı yerine)

**Adapter**:
Bir dış sistemin (örneğin LiteLLM) kendi biçimindeki isteğini `EvaluationRequest`'e, kararı da o
sistemin yanıt biçimine çeviren katman; karar mantığı içermez (S6).
_Kaçın_: plugin, connector, entegrasyon (tek bileşen için)

**Yüzey**:
Battal'ı çağıran entegrasyon türü: `gateway`, `ide`, `agent`.
_Kaçın_: platform, kanal

## Tespit

**Detector**:
Bir segment'te belirli bir riski arayan, sürümlenmiş bileşen; örneğin `pii.tckn`,
`tr-injection`.
_Kaçın_: scanner, guard (tek bir bileşen için), recognizer (Presidio bağlamı dışında)

**Detection**:
Bir detector'ın bir segment'te bulduğu tek bulgu; span'i, skoru ve sürümüyle birlikte.
_Kaçın_: finding (yanıt alanlarında), match, hit

**Raw score**:
Bir model detector'ının ürettiği, kalibre edilmemiş skor; olasılık olarak sunulmaz.
_Kaçın_: olasılık, confidence

**Span**:
Orijinal metinde Unicode code point cinsinden, yarı açık `[start, end)` aralığı.
_Kaçın_: offset (tek başına), konum, range

**Görünüm (view)**:
Normalizasyonun aynı metinden ürettiği, offset haritasıyla orijinal metne bağlı biçimlerden biri:
`orig`, `clean`, `pii`, `match`, `match_ascii` (S2).
_Kaçın_: normalize edilmiş metin (tek bir metin varmış gibi), `v_pii`/`v_match` (eski adlar)

**Offset haritası**:
Bir görünümün her code point'ini orijinal metindeki aralığa bağlayan eşleme; görünümde bulunan
bir span'i orijinal metne geri çevirmeyi sağlar.
_Kaçın_: index map, hizalama

**Sinyal**:
Normalizasyon sırasında sayılan, adı sabit şüpheli özellik; örneğin `zero_width`,
`bidi_control`, `mixed_script` (tam liste: S2 §7). Policy koşullarında adıyla kullanılır.
_Kaçın_: uyarı, flag

**Çözülmüş parça**:
Metindeki base64, hex, URL-encoded ya da tag karakterleriyle kodlanmış bir parçanın çözülmüş
hâli; kaynak parçanın orijinal aralığını taşır.
_Kaçın_: decoded view (tek bir görünüm varmış gibi), payload

**Karışık script token**:
Hem Latin hem Kiril ya da Yunan harf içeren token; confusable katlama yalnızca bu token'lara
uygulanır.
_Kaçın_: homoglyph kelime

**Katlama (folding)**:
Görünüm üretirken bir karakteri eşdeğer kabul edilen başka bir karaktere çevirme: confusable
katlama (`а → a`), leet katlama (`3 → e`), diakritik düşürme (`ş → s`).
_Kaçın_: normalizasyon (genel süreç için ayrılmıştır), dönüştürme

**Aday (candidate)**:
Bir PII detector'ının biçimine uyan metin parçası; checksum'ı geçmesi gerekmez. Her aday bir
detection olur; checksum sonucu `checksum_valid` alanında taşınır (S3).
_Kaçın_: eşleşme, potansiyel PII

**Bağlam kelimesi**:
Bir adayın yakınında geçtiğinde adayın gerçekten o türden olma olasılığını artıran kelime
(`kimlik`, `vergi`, `cep`); sonucu `context_hit` alanında taşınır.
_Kaçın_: anahtar kelime (injection kurallarıyla karışır), keyword

**Checksum doğrulaması**:
TCKN, VKN, IBAN ve Luhn için numaranın kendi kontrol hanesiyle tutarlılığının hesaplanması.
_Kaçın_: validasyon (tek başına)

## Karar

**Decision**:
Policy'nin bir evaluation için verdiği tek sonuç: `action`, `rule_id`, policy sürümü, fail mode ve
`degraded` bilgisi.
_Kaçın_: verdict, sonuç (tek başına)

**Action**:
Decision'ın eylemi: `allow`, `mask`, `block`, `ask`. Öncelik: `block` > `ask` > `mask` > `allow`.
_Kaçın_: karar (action yerine), outcome

**Rule**:
Policy içinde bir koşulu bir action'a bağlayan, kimliği (`rule_id`) olan tek kural.
_Kaçın_: politika (rule yerine)

**Transform**:
`mask` action'ının bir segment'e uyguladığı değişiklik; sonucu yer tutuculu metindir
(`<TCKN>`).
_Kaçın_: redaction, anonimleştirme

**Rationale**:
Decision'ın istemciye gösterilebilen kısa gerekçesi: bir kod ve Türkçe bir mesaj. Detector
ayrıntısı içermez.
_Kaçın_: açıklama, reason

**Degraded**:
Bir model detector'ı çalışmadığı için kararın yalnızca deterministik kurallarla verildiğini
belirten durum.
_Kaçın_: kısmi karar, fallback

**Fail mode**:
Battal karar veremediğinde uygulanacak davranış: `open` (içerik geçer) ya da `closed` (içerik
engellenir); checkpoint bazında policy ile belirlenir.
_Kaçın_: hata modu, failover

## Policy

**Policy**:
Detection'ları action'lara bağlayan rule'ların kimliği ve sürümü olan kümesi; "ne yapılır"
sorusunu cevaplar.
_Kaçın_: kural seti (policy yerine), config

**Binding**:
Bir policy'nin hangi bağlamda (checkpoint, tenant, team, key, model…) uygulanacağını tanımlayan
kayıt; "nerede uygulanır" sorusunu cevaplar.
_Kaçın_: atama, assignment, mapping

**Taban policy**:
Her bağlamda her zaman çalışan global policy; diğer binding'ler onu gevşetemez, yalnızca
sıkılaştırabilir.
_Kaçın_: floor (metin içinde; ADR 0004'te parantez içinde geçer), varsayılan policy, global policy

**Spesifiklik**:
Bir binding'in eşleşen alan sayısı; birden çok binding eşleştiğinde hangisinin taban policy'nin
üstüne ekleneceğini belirler.
_Kaçın_: öncelik (action önceliğiyle karışır)

**Bundle**:
Policy dosyaları ile `bindings.yaml`'ın semver ve içerik hash'iyle (`bundle_hash`) sürümlenen,
birlikte yüklenen bütünü.
_Kaçın_: paket (Python paketiyle karışır), policy seti

**Shadow mod**:
Yeni bir bundle'ın ya da modelin karar vermeden çalışıp yalnızca sonuçlarının kaydedildiği ve
mevcut olanla karşılaştırıldığı mod.
_Kaçın_: dry run, test modu

## Kayıt

**Karar kaydı**:
Her evaluation (karar ya da hata) için tutulan, ham içerik içermeyen yapılandırılmış kayıt:
kimlikler, span'ler, skorlar, sürümler, `bundle_hash` ve içeriğin HMAC'i (S7).
_Kaçın_: audit log (tek başına), log

**Kayıt zinciri**:
Bir sink'e yazılan karar kayıtlarını `seq` ve önceki kaydın hash'iyle (`prev_hash`) birbirine
bağlayan dizi; silinen ya da değiştirilen kaydı tespit eder, engellemez (S7).
_Kaçın_: blockchain, imzalı log

**HMAC anahtarı (kayıt)**:
Karar kaydında segment metinlerinin ve `user_id`'nin yerine yazılan HMAC'lerin gizli anahtarı;
kimliği `hmac_key_id` ile kayda yazılır (S7).
_Kaçın_: tuz (salt), şifreleme anahtarı

## Spec ve test

**Spec**:
Bir bileşenin davranışını tanımlayan, sürümlenen normatif belge: düzyazı, JSON Schema ve test
vektörleri.
_Kaçın_: doküman (tek başına), tasarım

**Gereklilik**:
Bir spec'teki, kimliği olan (`S3-PII-012`) tek normatif cümle.
_Kaçın_: madde, requirement (metin içinde)

**Test vektörü (case)**:
Tek bir girdi ve beklenen sonuç çifti; Python ve Rust implementasyonlarının ortak testi.
_Kaçın_: fixture, örnek (normatif olmayan örneklerle karışır)

**Suite**:
Aynı function'ı test eden case'lerin bulunduğu tek bir vektör dosyası.
_Kaçın_: test dosyası

**Function (vektör)**:
Bir suite'in test ettiği fonksiyonun dilden bağımsız adı; örneğin `pii.tckn.validate`.
_Kaçın_: fonksiyon adı (dile bağlı olduğu için)

**Runner**:
Bir dilde suite'leri okuyup function'ları çalıştıran test bileşeni.
_Kaçın_: harness (benchmark harness'ıyla karışır)
