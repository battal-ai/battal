# S5: Policy, binding ve bundle

- Durum: kabul edildi
- Sürüm: 1.1.0
- İlgili ADR'ler: [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0004](../decisions/0004-policy-binding-and-playground.md)
- İlgili backlog: E5 (PBI 5.1–5.5)
- Şema: `schemas/bundle.schema.json`, `schemas/bindings.schema.json`,
  `schemas/policy.schema.json`
- Test vektörleri: `testvectors/s5-policy/`

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-17 | İlk taslak |
| 1.0.0 | 2026-11-17 | Kabul edildi |
| 1.0.1 | 2026-11-18 | Binding tablosunda `surface` satırının kaynağı S6 yerine E13 olarak düzeltildi |
| 1.1.0 | 2026-11-18 | S4 için detection koşuluna `signature` ve `truncated`, yeni `detector_unavailable` koşulu; örneklerde `tr-injection` yerine `injection.model` |

## 1. Amaç ve kapsam

Bu spec; policy dosyalarının, `bindings.yaml`'ın ve `bundle.yaml`'ın biçimini, bir bundle'ın
nasıl doğrulandığını ve hash'lendiğini, bir istek için hangi policy'lerin uygulanacağını, kuralların
nasıl değerlendirilip birleştirildiğini ve bunun sonucunda S1'deki `decision`, `transforms` ve
`rationale` alanlarının nasıl üretildiğini tanımlar. Ayrıca policy testlerinin ve
`battal policy` CLI'ının davranışını tanımlar.

**Kapsam dışı:**

- Detection'ların nasıl üretildiği (S3, S4) ve normalizasyon sinyallerinin tanımı (S2). Bu spec
  detection'ları ve sinyalleri girdi olarak alır.
- Çalışma anında shadow mod ve canary. MVP'de yerel karşılığı `battal policy diff`'tir.
- Policy playground (E18).
- Karar kaydına yazılan alanlar (S7).

## 2. Terimler

Terimler [sözlükteki](../sozluk.md) anlamlarıyla kullanılır. Bu spec'e özgü olanlar:

| Terim | Tanım |
|---|---|
| Katman | Bir istekte uygulanan iki policy'den biri: taban katman ve spesifik katman |
| Taban binding | `match: {}` olan, taban policy'yi bağlayan tek binding |
| Detection koşulu | `detector` alanı olan, tek bir detection'ın sağladığı koşul |
| Segment koşulu | `trust`, `source`, `role` alanlarına bakan koşul |
| Sinyal koşulu | Normalizasyon sinyallerine bakan koşul |

## 3. Bundle

### 3.1 Dosya düzeni

```text
<bundle>/
├── bundle.yaml          bundle adı, sürümü ve checkpoint fail mode'ları
├── bindings.yaml        binding listesi
├── policies/*.yaml      her dosyada bir policy
└── tests/*.test.yaml    policy testleri (S0, kind: policy_test)
```

- **S5-BND-001.** Bundle dosyaları **MUST** YAML 1.2 core schema ile ayrıştırılmalıdır. Aynı
  nesnede tekrarlanan anahtar **MUST** `YAML_DUPLICATE_KEY` hatasıyla reddedilmelidir. (YAML 1.1
  ayrıştırıcıları `on`, `yes`, `no` gibi değerleri boolean'a çevirir; bu davranış kabul edilmez.)
  *[doğrulama: CI]*
- **S5-BND-002.** `bundle.yaml`, `bindings.yaml` ve her policy dosyası kendi şemasına göre
  **MUST** geçerli olmalıdır.

### 3.2 `bundle.yaml`

```yaml
name: ornek-kurum
version: 1.4.0
fail_modes:
  input: closed
  output: open
```

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `name` | string | evet | Bundle adı |
| `version` | semver | evet | Bundle sürümü |
| `fail_modes` | object | hayır | Checkpoint → `open` \| `closed` |

- **S5-BND-003.** Bir checkpoint için fail mode verilmemişse varsayılan **MUST** şu olmalıdır:
  `input`: `closed`, `output`: `open`, diğer bütün checkpoint'ler: `closed`.
- **S5-BND-004.** Fail mode yalnızca `bundle.yaml`'da tanımlanır; policy dosyaları ve binding'ler
  fail mode **MUST NOT** tanımlayamaz. *[doğrulama: şema]*

### 3.3 Bundle hash'i

- **S5-BND-005.** `bundle_hash` şöyle hesaplanır:
    1. Şu nesne kurulur: `{"bundle": <bundle.yaml>, "bindings": <bindings.yaml>,
       "policies": [<policy>...]}`. `policies` dizisi policy `id`'sine göre (code point sırası)
       artan sıralanır. Testler (`tests/`) dahil edilmez.
    2. Nesne RFC 8785 (JSON Canonicalization Scheme) ile kanonik JSON'a çevrilir.
    3. UTF-8 baytlarının SHA-256'sı alınır; sonuç `sha256:<64 küçük hex>` biçimindedir.

    Bu nedenle yorumlar, boşluklar, anahtar sırası ve dosya adları hash'i **MUST NOT**
    değiştirmemelidir; kurallardaki her değişiklik **MUST** değiştirmelidir.

### 3.4 Yükleme ve hot reload

- **S5-BND-006.** Bir bundle, bütün doğrulamalardan (§3.5) hatasız geçmeden **MUST NOT**
  devreye alınmamalıdır. *[doğrulama: CI]*
- **S5-BND-007.** Yeni bundle atomik olarak devreye alınır: devam eden bir evaluation ya eski ya
  yeni bundle'ı bütünüyle görür, ikisinin karışımını **MUST NOT** görmemelidir. *[doğrulama: CI]*
- **S5-BND-008.** Yeni bundle geçersizse eski bundle **MUST** çalışmaya devam etmeli; olay hata
  düzeyinde loglanmalı ve bir metrik/alarm üretilmelidir. *[doğrulama: CI]*
- **S5-BND-009.** Geçerli bir bundle hiç yüklenmemişse `evaluate()` S1'deki `NO_BUNDLE_LOADED`
  hatasını verir. Değişikliğin nasıl algılandığı (dosya izleme, periyodik kontrol, sinyal)
  implementasyon ayrıntısıdır ve config ile seçilir.

### 3.5 Doğrulama

`bundle.validate` bir bundle'ı doğrular ve `{"valid", "issues", "warnings"}` döndürür. Sorun kodları:

| Kod | Ne zaman | Gereklilik |
|---|---|---|
| `SCHEMA_INVALID` | Bir dosya kendi şemasına göre geçersiz | S5-BND-002 |
| `FLOOR_MISSING` | `match: {}` olan binding yok | S5-BIN-002 |
| `FLOOR_DUPLICATE` | Birden fazla `match: {}` binding'i var | S5-BIN-002 |
| `DUPLICATE_BINDING_ID` | Aynı binding `id`'si iki kez | S5-BIN-001 |
| `DUPLICATE_POLICY_ID` | Aynı policy `id`'si iki dosyada | S5-POL-001 |
| `DUPLICATE_RULE_ID` | Aynı kural `id`'si bundle içinde iki kez | S5-POL-002 |
| `UNKNOWN_POLICY` | Binding'in `policy` ya da `selectable` alanı olmayan bir policy'ye işaret ediyor | S5-BIN-001 |
| `BINDING_FIELD_NOT_SUPPORTED` | Binding, bu sürümde çalışmayan bir eşleşme alanı kullanıyor | S5-BIN-003 |
| `BINDING_CONFLICT` | Aynı spesifiklikte, ayrık olduğu kanıtlanamayan iki binding | S5-BIN-006 |
| `MASK_RULE_WITHOUT_DETECTION` | `mask` kuralında olumsuzlanmamış detection koşulu yok | S5-ACT-002 |
| `SCORE_CONDITION_CONFLICT` | Aynı koşulda hem `min_score` hem `above_threshold` | S5-RUL-006 |

Uyarı kodları (bundle geçerli kalır):

| Kod | Ne zaman |
|---|---|
| `ASK_ACTS_AS_BLOCK_ON_GATEWAY` | Bundle'da `ask` eylemli kural var; gateway yüzeyinde `block` olarak uygulanır (ADR 0004 karar 8) |

- **S5-BND-010.** Bir bundle'da birden fazla sorun varsa `issues` bütün sorunları, yukarıdaki
  tablonun sırasıyla ve her kodu bir kez **MUST** içermelidir. `SCHEMA_INVALID` varsa diğer
  denetimler yapılmaz ve `issues` yalnızca `["SCHEMA_INVALID"]` olur.

## 4. Binding'ler

```yaml
bindings:
  - id: global
    policy: default-tr
    match: {}
  - id: finans
    policy: strict-pii
    match: {team: finans, checkpoint: [input, output]}
    selectable: [strict-pii, strict-pii-test]
```

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | string | evet | Binding kimliği; yanıtta `matched_bindings` içinde görünür |
| `policy` | string | evet | Bağlanan policy'nin `id`'si |
| `match` | object | evet | Eşleşme koşulları; boşsa taban binding |
| `selectable` | string[] | hayır | İsteğin `policy.id` ile seçebileceği policy'ler |

**Eşleşme alanları ve istekteki karşılıkları:**

| Alan | İstekteki alan | MVP'de çalışır | Glob |
|---|---|---|---|
| `checkpoint` | `checkpoint` | evet | hayır |
| `tenant` | `tenant` | evet | hayır |
| `team` | `principal.team_id` | evet | hayır |
| `key` | `principal.key_hash` | evet | hayır |
| `model` | `target.model` | evet | evet (`*`, `?`) |
| `user` | `principal.user_id` | hayır | hayır |
| `surface` | (E13) | hayır | hayır |
| `agent` | `agent.id` | hayır | hayır |
| `tool` | (E12) | hayır | hayır |

- **S5-BIN-001.** Binding `id`'leri bundle içinde benzersiz olmalı; `policy` ve `selectable`
  içindeki her değer bundle'daki bir policy'ye **MUST** karşılık gelmelidir.
- **S5-BIN-002.** Bundle'da `match: {}` olan **tam olarak bir** binding (taban binding) **MUST**
  bulunmalıdır.
- **S5-BIN-003.** MVP'de çalışmayan bir eşleşme alanını kullanan bundle **MUST**
  `BINDING_FIELD_NOT_SUPPORTED` ile reddedilmelidir; bu alanlar sessizce yok sayılmaz.
- **S5-BIN-004.** Bir binding bir isteğe ancak `match`'teki **her** alan eşleşirse eşleşir (AND).
  Alanın değeri bir liste ise değerlerden biri eşleşmesi yeterlidir (OR). İstekte karşılığı
  olmayan bir alan eşleşmez. Karşılaştırma büyük/küçük harfe duyarlı, birebir yapılır.
- **S5-BIN-005.** `model` alanında `*` sıfır ya da daha fazla karakterle, `?` tek bir karakterle
  eşleşir; desen değerin tamamıyla eşleşmelidir.
- **S5-BIN-006.** Bir binding'in **spesifikliği** `match`'teki alan sayısıdır. Aynı spesifiklikte
  iki binding, birbirinden **kanıtlanabilir şekilde ayrık** değilse bundle **MUST**
  `BINDING_CONFLICT` ile reddedilmelidir. İki binding yalnızca ikisinde de bulunan en az bir alanın
  değer kümeleri kesişmiyorsa ve bu alanda glob kullanılmıyorsa ayrıktır.

### 4.1 Katmanların seçimi

- **S5-SEL-001.** Taban katman her zaman taban binding'in policy'sidir.
- **S5-SEL-002.** Spesifik katman, isteğe eşleşen taban dışı binding'ler arasından spesifikliği en
  yüksek olanın policy'sidir. Taban dışında eşleşen binding yoksa spesifik katman yoktur.
- **S5-SEL-003.** İstek `policy.id` içeriyorsa: isteğe eşleşen en spesifik binding (taban binding
  dahil) `selectable` listesinde bu id'yi içermelidir; içeriyorsa seçilen policy spesifik katman
  olur ve `decided_by.binding` için bu binding kullanılır. İçermiyorsa ya da policy yoksa
  `evaluate()` **MUST** `POLICY_NOT_ALLOWED` hatası vermelidir.
- **S5-SEL-004.** Seçilen policy taban katmanın yerini **MUST NOT** alamaz; taban policy her
  durumda değerlendirilir.
- **S5-SEL-005.** `matched_bindings`, uygulanan binding'leri içerir: önce taban binding, spesifik
  katman varsa ardından onun binding'i.

## 5. Policy

```yaml
id: default-tr
version: 1.0.0
description: Türkçe varsayılan policy
rules:
  - id: pii.mask_tckn
    when: {detector: pii.tckn, checksum_valid: true}
    action: mask
  - id: pi.block_untrusted
    checkpoints: [input]
    when:
      all:
        - {detector: injection.model, above_threshold: true}
        - {trust: untrusted}
    action: block
    rationale: {code: PROMPT_INJECTION, message_tr: İstek güvenlik politikası nedeniyle engellendi.}
```

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | string | evet | Policy kimliği |
| `version` | semver | evet | Policy sürümü |
| `description` | string | hayır | |
| `rules` | array | evet | Sıralı kural listesi (boş olabilir) |

**Kural:**

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | string | evet | Bundle içinde benzersiz kural kimliği |
| `description` | string | hayır | |
| `checkpoints` | string[] | hayır | Kuralın geçerli olduğu checkpoint'ler; yoksa hepsi |
| `when` | koşul | evet | Bkz. §6 |
| `action` | enum | evet | `allow`, `mask`, `block`, `ask` |
| `rationale` | object | hayır | `code`, `message_tr`; yoksa §7.4'teki varsayılan |
| `placeholder` | string | hayır | Yalnızca `mask`: yer tutucu; yoksa §7.3'teki varsayılan |

- **S5-POL-001.** Policy `id`'leri bundle içinde **MUST** benzersiz olmalıdır.
- **S5-POL-002.** Kural `id`'leri bütün bundle içinde **MUST** benzersiz olmalıdır; böylece
  `rule_id` tek başına bir kuralı tanımlar.
- **S5-POL-003.** `checkpoints` verilmiş bir kural, isteğin checkpoint'i listede değilse
  değerlendirilmez.

## 6. Koşullar

```text
koşul := {all: [koşul, ...]} | {any: [koşul, ...]} | {not: koşul}
       | detection koşulu | segment koşulu | sinyal koşulu | erişilemezlik koşulu
```

- **S5-RUL-001.** Bir kural **segment başına** değerlendirilir: kuralın koşulu isteğin
  segment'lerinden en az birinde sağlanıyorsa kural eşleşir. `all`, `any` ve `not` aynı segment
  üzerinde birleşir; bir koşulun bir kısmı bir segment'te, diğer kısmı başka bir segment'te
  sağlanarak kural **MUST NOT** eşleşmemelidir.
- **S5-RUL-002.** **Detection koşulu** (`detector` alanı olan nesne), o segment'teki **tek bir**
  detection koşulun bütün alanlarını sağlıyorsa doğrudur. Alanlar:
    - `detector`: detector adı; `*` ve `?` glob karakterleri kullanılabilir (`pii.*`).
    - `checksum_valid`, `context_hit`, `truncated`: boolean; detection'daki aynı adlı alanla eşit
      olmalıdır. Detection'da alan yoksa koşul sağlanmaz.
    - `signature`: glob; detection'ın `signature` alanıyla (S4) eşleşmelidir. Detection'da alan
      yoksa koşul sağlanmaz.
    - `min_score`: sayı; detection'ın `raw_score` değeri `>=` olmalıdır.
    - `above_threshold: true`: detection'ın `raw_score` değeri kendi `threshold` değerine `>=`
      olmalıdır.
- **S5-RUL-003.** **Segment koşulu** (`trust`, `source`, `role` alanlarından en az birini
  içeren, `detector` ve `signal` içermeyen nesne) segment'in bu alanlarının hepsi eşleşiyorsa
  doğrudur. Değer bir liste ise biri eşleşmesi yeterlidir. Segment'te gönderilmemiş `role` ya da
  `source` hiçbir değerle eşleşmez (S1-SEG-004); `trust` her zaman vardır (S1-SEG-003).
- **S5-RUL-004.** **Sinyal koşulu** (`{signal: <ad>, min_count: <n>}`; `min_count` varsayılan 1)
  o segment için girdi olarak verilen sinyalin sayısı `>= min_count` ise doğrudur. Sinyal adları
  S2'de tanımlanır.
- **S5-RUL-005.** `{not: k}`, `k` o segment'te doğru değilse doğrudur. Dolayısıyla
  `{not: {detector: x}}` "bu segment'te x detection'ı yok" anlamına gelir.
- **S5-RUL-006.** Bir detection koşulunda `min_score` ile `above_threshold` birlikte
  **MUST NOT** kullanılmamalıdır (`SCORE_CONDITION_CONFLICT`). `min_score` veya
  `above_threshold`, `raw_score` alanı olmayan detection'larla **MUST NOT** eşleşmemelidir.
- **S5-RUL-008.** **Erişilemezlik koşulu** (`{detector_unavailable: <glob>}`), `policy.evaluate`
  girdisindeki `detector_failures` listesinde desenle eşleşen bir ad varsa doğrudur. İstek
  düzeyindedir: her segment'te aynı sonucu verir. Policy, model detector'ı çalışmadığında ne
  yapılacağını bu koşulla açıkça yazar (örneğin `input`'ta `block`); bu koşul detection
  içermediği için tek başına bir `mask` kuralının koşulu **MUST NOT** olamaz (S5-ACT-002).
- **S5-RUL-007.** Koşul nesnesinde tanımlı olmayan bir alan bulunan policy **MUST**
  `SCHEMA_INVALID` ile reddedilmelidir. *[doğrulama: şema]*

## 7. Karar

### 7.1 Bir katmanın kararı

- **S5-DEC-001.** Bir katman içinde, isteğin checkpoint'i için geçerli olan ve eşleşen kurallar
  arasından eylem önceliği en yüksek olan kazanır: `block` > `ask` > `mask` > `allow`. Aynı
  öncelikte, policy dosyasında **önce yazılan** kural kazanır.

### 7.2 Katmanların birleştirilmesi

- **S5-DEC-002.** İki katmanın kazanan kuralları arasından eylem önceliği yüksek olan alınır. Eşit
  öncelikte spesifik katmanın kuralı kazanır.
- **S5-DEC-003.** Hiçbir katmanda kural eşleşmezse eylem **MUST** `allow` olmalıdır;
  `rule_id` `null`, `decided_by` `{kind: "default", binding: null}` olur. `decision.policy`
  spesifik katman varsa onun, yoksa taban katmanın policy'sidir.
- **S5-DEC-004.** Bir kural kazandığında `decision.rule_id` o kuralın `id`'si, `decision.policy`
  kuralın policy'sinin `{id, version}`'ı, `decided_by` `{kind: "rule", binding: <kuralın geldiği
  binding>}` olur.
- **S5-DEC-005.** Taban katmanın `block` kararı, spesifik katmanın hiçbir kuralıyla
  **MUST NOT** gevşetilememelidir. (S5-DEC-002'nin doğrudan sonucudur; ayrıca vektörle
  sabitlenir.)

### 7.3 Maskeleme

- **S5-ACT-001.** Son eylem `mask` ise, **iki katmanda da** eşleşen ve isteğin checkpoint'i için
  geçerli olan **bütün** `mask` kurallarının maskeleri uygulanır. Son eylem `mask` değilse
  `transforms` **MUST** boş olmalıdır.
- **S5-ACT-002.** Bir `mask` kuralının maskelediği detection'lar: kuralın sağlandığı segment'te,
  kuralda **olumsuzlanmamış** (bir `not` altında olmayan) herhangi bir detection koşulunu
  sağlayan bütün detection'lardır. Olumsuzlanmamış detection koşulu içermeyen bir `mask` kuralı
  **MUST** `MASK_RULE_WITHOUT_DETECTION` ile reddedilmelidir.
- **S5-ACT-003.** Bir detection'ın yer tutucusu, onu maskeleyen kuralın `placeholder` alanıdır;
  yoksa `<` + detector adının son `.` sonrası kısmının büyük harfli hâli + `>` olur
  (`pii.tckn` → `<TCKN>`, `pii.email` → `<EMAIL>`). Aynı detection'ı birden fazla kural
  maskeliyorsa, kazanma sırasına (S5-DEC-001, S5-DEC-002) göre ilk kuralın yer tutucusu kullanılır.
- **S5-ACT-004.** Bir segment'teki maskelenecek span'ler çakışıyorsa (`a.start < b.end` ve
  `b.start < a.end`) tek bir edit'e birleştirilir; edit'in span'i birleşimdir. Yer tutucu, en
  solda başlayan detection'ınkidir; eşitlikte en uzun olanınki; yine eşitlikte detector adı code
  point sırasına göre küçük olanınki. Bitişik (çakışmayan) span'ler birleştirilmez.
- **S5-ACT-005.** Her maskelenen segment için `transforms`'a tek bir kayıt eklenir: `edits`
  span'e göre artan sırada, `text` orijinal metne edit'ler uygulanmış hâlidir (S1-TRF-003).
  `transforms` segment `id`'sine göre artan sıradadır.

### 7.4 Rationale

- **S5-RAT-001.** Son eylem `allow` değilse `rationale` **MUST** bulunmalıdır. Kazanan kuralın
  `rationale` alanı varsa o kullanılır; yoksa eyleme göre varsayılan:

    | Eylem | `code` | `message_tr` |
    |---|---|---|
    | `block` | `POLICY_BLOCKED` | İstek güvenlik politikası nedeniyle engellendi. |
    | `mask` | `POLICY_MASKED` | İstekteki bazı bilgiler gizlendi. |
    | `ask` | `CONFIRMATION_REQUIRED` | Bu işlem için onay gerekiyor. |

- **S5-RAT-002.** Son eylem `allow` ise `rationale` **MUST NOT** bulunmamalıdır.
- **S5-RAT-003.** Policy yazarının `message_tr` içine detector adı, skor ya da eşleşen metin
  yazmaması gerekir (S1-RAT-002); Battal bu metni değiştirmez. *[doğrulama: CI]*

### 7.5 Arıza, degraded ve fail mode

`policy.evaluate` saf bir fonksiyondur; arızalar ona girdi olarak bildirilir (§9).

- **S5-FLT-001.** `detector_failures` boş değilse `degraded` **MUST** `true` olmalıdır; karar
  kalan detection'larla normal kurallara göre verilir (S1-EVAL-003).
- **S5-FLT-002.** `engine_failure: true` ise kurallar değerlendirilmez; eylem checkpoint'in fail
  mode'una göre `closed` → `block`, `open` → `allow` **MUST** olmalıdır. `rule_id` `null`,
  `decided_by` `{kind: "fail_mode", binding: null}`, `degraded` `true`, `decision.policy` taban
  policy, `transforms` boş olur. Eylem `block` ise `rationale` `{code: "UNAVAILABLE",
  message_tr: "İstek şu anda değerlendirilemiyor."}` olur.
- **S5-FLT-003.** `decision.fail_mode` her kararda isteğin checkpoint'i için `bundle.yaml`'daki
  (ya da varsayılan) fail mode'dur.
- **S5-FLT-004.** `session` ve `agent` alanları kararı etkilemez (S1-REQ-006).

## 8. Policy testleri

- **S5-TST-001.** Policy testleri bundle'ın `tests/` dizininde, S0 1.1.0'daki `kind: policy_test`
  suite'leri olarak, YAML sözdizimiyle yazılır; `function` **MUST** `policy.evaluate`
  olmalıdır. *[doğrulama: CI]*
- **S5-TST-002.** Policy testlerinde `input.bundle` verilmez; test, içinde bulunduğu bundle'a karşı
  çalışır. *[doğrulama: CI]*
- **S5-TST-003.** `input.text` kullanan (tam pipeline) testler `tags: [model]` ile işaretlenmelidir
  (S0-FMT-011); `input.detections` kullanan testler deterministiktir. *[doğrulama: CI]*

## 9. `policy.evaluate`

```text
policy.evaluate(input) -> {decision, transforms, rationale?} | hata
```

`input`:

| Alan | Açıklama |
|---|---|
| `bundle` | `{"bundle": ..., "bindings": ..., "policies": [...]}`; policy testlerinde verilmez |
| `request` | S1 `EvaluationRequest` (S1'e göre ayrıştırılmış) |
| `detections` | S1 detection nesneleri |
| `signals` | `[{segment, signal, count}]`; isteğe bağlı |
| `detector_failures` | Çalışmayan detector adları; isteğe bağlı |
| `engine_failure` | `true` ise fail mode uygulanır; isteğe bağlı |

Çıktı, S1 `EvaluationResponse`'un `decision`, `transforms` ve (varsa) `rationale` alanlarıdır.
Bundle geçersizse `NO_BUNDLE_LOADED`, policy seçimi reddedilirse `POLICY_NOT_ALLOWED` hatası verir.

## 10. CLI

| Komut | 0 | 1 | 2 |
|---|---|---|---|
| `battal policy validate <bundle>` | geçerli | — | geçersiz |
| `battal policy test <bundle>` | bütün testler geçti | en az bir test başarısız | bundle geçersiz |
| `battal policy diff <aktif> <taslak>` | tamamlandı | `--fail-on-change` ile değişiklik var | bundle'lardan biri geçersiz |

- **S5-CLI-001.** Komutlar yukarıdaki çıkış kodlarını **MUST** kullanmalıdır. *[doğrulama: CI]*
- **S5-CLI-002.** `diff`, iki bundle'ı taslak bundle'ın `tests/` dizinindeki testlerin girdileriyle
  çalıştırır ve kararı değişen her case için `id`, eski ve yeni `action` ile `rule_id`'yi
  listeler. *[doğrulama: CI]*
- **S5-CLI-003.** `validate`, uyarıları (`warnings`) gösterir ama uyarılar çıkış kodunu
  **MUST NOT** değiştirmemelidir. *[doğrulama: CI]*

## 11. Normatif örnekler (vektörler)

| Suite | Function | Ne test eder |
|---|---|---|
| `s5-policy/validate.json` | `bundle.validate` | Bundle doğrulama ve sorun kodları |
| `s5-policy/hash.json` | `bundle.hash` | Kanonik hash |
| `s5-policy/select.json` | `policy.evaluate` | Binding eşleşmesi, katman seçimi, policy seçimi |
| `s5-policy/rules.json` | `policy.evaluate` | Koşullar ve segment başına değerlendirme |
| `s5-policy/combine.json` | `policy.evaluate` | Katman birleştirme, varsayılan karar, rationale |
| `s5-policy/mask.json` | `policy.evaluate` | Maskeleme ve span birleştirme |
| `s5-policy/failure.json` | `policy.evaluate` | Degraded ve fail mode |

`bundle.validate` girdisi `{"bundle": ...}`, çıktısı `{"valid", "issues", "warnings"}`;
`bundle.hash` girdisi `{"bundle": ...}`, çıktısı `{"bundle_hash"}`.

## 12. Uyumluluk

- Bundle dosya biçimleri bu spec'in sürümüyle birlikte değişir. Yeni isteğe bağlı alan eklemek
  minor, alan kaldırmak veya anlamını değiştirmek major sürüm gerektirir.
- Hash algoritmasının (§3.3) her değişikliği major sürümdür, çünkü bütün kayıtlı `bundle_hash`
  değerlerini geçersiz kılar.
- ADR 0004'teki test örneği (`name`, `context`, `expect`) bu spec'te `id`/`description`,
  `input.request` ve `expected` olarak yer alır.
