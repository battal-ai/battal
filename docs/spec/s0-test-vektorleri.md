# S0: Spec ve test vektörü formatı

- Durum: kabul edildi
- Sürüm: 1.1.0
- İlgili ADR'ler: [ADR 0003](../decisions/0003-language-python-then-rust.md),
  [ADR 0004](../decisions/0004-policy-binding-and-playground.md)
- İlgili backlog: E0 (PBI 0.2)
- Şema: `schemas/testvector.schema.json`
- Test vektörleri: `testvectors/s0-format/`

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-17 | İlk taslak |
| 1.0.0 | 2026-11-17 | Kabul edildi |
| 1.1.0 | 2026-11-17 | Suite'e isteğe bağlı `kind` alanı (`policy_test`) ve `rule_refs` eklendi (S5 ile birlikte) |

## 1. Amaç ve kapsam

Bu spec, Battal spec'lerindeki normatif örneklerin (test vektörlerinin) dosya formatını, bir
çıktının beklenen değerle nasıl karşılaştırılacağını, metin konumlarının (span) birimini ve
vektörleri çalıştıran runner'ların uyması gereken sözleşmeyi tanımlar. Python ve Rust
implementasyonları aynı vektörleri bu kurallarla çalıştırır.

**Kapsam dışı:**

- Her spec'in kendi function'larının `input` ve `expected` yapısı. Bunları ilgili spec tanımlar.
- Rastgele üretilen, property-based ve fuzz testleri. Bunlar dile özgü test dizinlerinde
  (`tests/`) yaşar ve vektör değildir.
- Benchmark verisi (E7).

## 2. Terimler

| Terim | Tanım |
|---|---|
| Vektör (case) | Tek bir girdi ve beklenen sonuç çifti |
| Suite | Aynı function'ı test eden case'lerin bulunduğu tek bir dosya |
| Function | Test edilen fonksiyonun dilden bağımsız adı, örneğin `pii.tckn.validate` |
| Runner | Bir dilde suite'leri okuyup function'ları çalıştıran test bileşeni |
| Registry | Runner'ın function adlarını implementasyondaki fonksiyonlara bağladığı tablo |
| Gereklilik kimliği | Bir spec'teki normatif gerekliliğin değişmez adı, örneğin `S3-PII-012` |

## 3. Dosya formatı

### 3.1 Yerleşim

- **S0-FMT-001.** Spec vektörü suite'leri (`kind: spec`) **MUST** `testvectors/<spec-dizini>/<suite>.json` yolunda
  bulunmalıdır. `<spec-dizini>` spec kimliği ile kısa bir addan oluşur (`s3-pii`), `<suite>`
  küçük harf, rakam ve tire içerir. *[doğrulama: lint]*
- **S0-FMT-002.** Suite dosyaları **MUST** UTF-8 kodlu, BOM içermeyen geçerli JSON olmalıdır.
  *[doğrulama: lint]*
- **S0-FMT-003.** Her suite **MUST** `schemas/testvector.schema.json` şemasına göre geçerli
  olmalıdır.
- **S0-FMT-004.** Policy test dosyaları (`*.test.yaml`, ADR 0004) **MUST** aynı şemayı YAML
  sözdizimiyle kullanmalıdır. YAML dosyası JSON'a çevrildiğinde şemaya göre geçerli olmalıdır.
  *[doğrulama: S5 vektörleri]*

### 3.2 Suite

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `format_version` | integer | evet | Bu spec'in format sürümü. Şu an `1` |
| `kind` | `"spec"` \| `"policy_test"` | hayır | Suite türü; varsayılan `spec` (1.1.0) |
| `spec` | string | `kind: spec` ise evet | Suite'in ait olduğu spec kimliği, örneğin `S3` |
| `function` | string | evet | Test edilen fonksiyon; küçük harf, rakam, `_` ve `.` |
| `description` | string | hayır | Suite'in Türkçe açıklaması |
| `cases` | array | evet | En az bir case |

- **S0-FMT-012.** `kind: policy_test` suite'leri kullanıcıların policy testleridir (S5). Bu
  suite'lerde `spec` alanı ve case'lerde `spec_refs` alanı **MUST NOT** zorunlu tutulmamalıdır;
  case'ler bunların yerine isteğe bağlı `rule_refs` (test edilen kural kimlikleri) içerebilir.
  Bu suite'ler bundle'ın `tests/` dizininde durur, S0-FMT-001 yerleşim kuralına ve kapsam
  denetimine (§7) tabi değildir.
- **S0-FMT-005.** Bir suite'teki bütün case'ler **MUST** aynı function'ı test etmelidir.
  *[doğrulama: şema]*
- **S0-FMT-006.** `format_version` değeri runner'ın desteklediği sürümden farklıysa runner
  **MUST** suite'i çalıştırmadan `UNSUPPORTED_FORMAT_VERSION` hatası vermelidir.

### 3.3 Case

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | string | evet | Suite içinde benzersiz, değişmez; küçük harf, rakam ve tire |
| `description` | string | evet | Case'in neyi gösterdiğini anlatan Türkçe bir cümle |
| `spec_refs` | string[] | evet | Case'in test ettiği gereklilik kimlikleri, en az bir tane |
| `tags` | string[] | hayır | Serbest etiketler, örneğin `unicode`, `edge`, `model` |
| `input` | object | evet | Function'a verilen girdi; yapısını ilgili spec tanımlar |
| `expected` | herhangi bir JSON değeri | koşullu | Beklenen çıktı |
| `expected_error` | object | koşullu | Beklenen hata: `{"code": "..."}` |
| `match` | `"subset"` \| `"exact"` | hayır | Karşılaştırma modu; varsayılan `subset` |

- **S0-FMT-007.** Her case **MUST** `expected` ve `expected_error` alanlarından tam olarak birini
  içermelidir.
- **S0-FMT-008.** Bir suite içinde aynı `id` **MUST NOT** iki kez kullanılmamalıdır. Bir case'in
  tam adı `<spec-dizini>/<suite>::<id>` biçimindedir ve bütün repoda benzersizdir.
- **S0-FMT-009.** Yayınlanmış bir case'in `id`'si **SHOULD NOT** değiştirilmemelidir. Case'in
  anlamı değişirse yeni bir `id` ile yeni case yazılır.
- **S0-FMT-010.** `spec_refs` içindeki her değer **MUST** `S<sayı>-<ALAN>-<üç hane>` biçiminde
  olmalıdır, örneğin `S3-PII-012`.
- **S0-FMT-011.** `tags` içinde `model` etiketi bulunan case'ler, sonucu model sürümüne bağlı
  olan case'lerdir. Runner bu case'leri **MUST** ayrı çalıştırılabilecek şekilde işaretlemelidir
  (örneğin pytest marker). *[doğrulama: CI]*

### 3.4 Görünmez karakterler

- **S0-ESC-001.** Suite dosyalarının ham metninde aşağıdaki kategorilerden bir karakter
  **MUST NOT** bulunmamalıdır; bu karakterler **MUST** JSON `\uXXXX` kaçışıyla yazılmalıdır
  (BMP dışı karakterler surrogate çiftiyle):
    - `Cc` (kontrol), `Cf` (format: zero-width, bidi, tag karakterleri dahil), `Cs`, `Co`, `Cn`;
    - `Zl`, `Zp` ve U+0020 dışındaki bütün `Zs` karakterleri;
    - `Mn` ve `Me` (birleşen işaretler, variation selector'lar dahil).

    Satır sonu (U+000A) ve girinti (U+0020, U+0009) JSON sözdiziminin parçası olduğu için bu
    kuralın dışındadır; string değerlerinin içinde ise JSON'un kendi kuralı gereği kaçışla
    yazılırlar. Satır sonu olarak yalnızca LF kullanılır; CR (U+000D) ihlaldir.
- **S0-ESC-002.** Türkçe harfler (`ç ğ ı İ ö ş ü` ve büyükleri), emoji ve diğer görünür
  karakterler **MAY** ham olarak yazılabilir.

## 4. Karşılaştırma

Runner, function'ın gerçek çıktısını (`actual`) case'in `expected` değeriyle aşağıdaki kurallarla
karşılaştırır. Kurallar JSON değerleri üzerinde tanımlıdır; runner karşılaştırmadan önce çıktıyı
JSON veri modeline çevirir.

- **S0-CMP-001.** `subset` modunda, `expected` bir nesne ise `expected`'daki her anahtar
  **MUST** `actual`'da bulunmalı ve değeri aynı kurallarla eşleşmelidir. `actual`'daki fazladan
  anahtarlar yok sayılır.
- **S0-CMP-002.** Değeri `null` olan bir anahtar, yalnızca `actual`'da aynı anahtar `null`
  değeriyle bulunuyorsa eşleşir. Anahtarın hiç bulunmaması `null` ile **MUST NOT**
  eşleşmemelidir.
- **S0-CMP-003.** Diziler her iki modda da **MUST** aynı uzunlukta olmalı ve elemanlar sırasıyla
  eşleşmelidir. Dizideki nesneler o anki modla (subset veya exact) karşılaştırılır.
- **S0-CMP-004.** `exact` modunda nesneler **MUST** aynı anahtar kümesine sahip olmalıdır;
  fazladan anahtar eşleşmeyi bozar.
- **S0-CMP-005.** Sayılar değerleriyle karşılaştırılır: `1` ile `1.0` eşleşir. Tolerans
  **MUST NOT** uygulanmamalıdır.
- **S0-CMP-006.** Tipler **MUST** aynı olmalıdır: `"1"` ile `1`, `true` ile `1`, `false` ile
  `0` ve `null` ile `false` eşleşmez.
- **S0-CMP-007.** String'ler code point dizisi olarak birebir karşılaştırılır. Runner
  **MUST NOT** karşılaştırmadan önce Unicode normalizasyonu, büyük/küçük harf dönüşümü veya
  boşluk temizliği uygulamamalıdır.
- **S0-CMP-008.** `expected_error` içeren bir case, yalnızca function aynı `code` ile hata verirse
  geçer. Hata mesajı **MUST NOT** karşılaştırılmamalıdır. Function hata vermezse ya da başka bir
  kod verirse case başarısız olur. `expected` içeren bir case'te function hata verirse case
  başarısız olur.
- **S0-CMP-009.** Aralık, regex veya joker karakter gibi eşleştirme operatörleri yoktur.
  `expected` içindeki bütün değerler literal olarak karşılaştırılır.

## 5. Span'ler

- **S0-SPAN-001.** Bütün spec'lerde metin konumları **MUST** Unicode code point cinsinden,
  0 tabanlı, yarı açık `[start, end)` aralığı olarak ifade edilmelidir. UTF-8 byte veya UTF-16
  code unit offset'i kullanılmaz. *[doğrulama: S2, S3 vektörleri]*
- **S0-SPAN-002.** Geçerli bir span için `0 <= start <= end <= len(metin)` **MUST** sağlanmalıdır.
  Boş span (`start == end`) yalnızca ilgili spec izin veriyorsa kullanılır.
  *[doğrulama: S2, S3 vektörleri]*
- **S0-SPAN-003.** Bir span, aksi belirtilmedikçe, normalizasyondan önceki **orijinal** metne
  göre ifade edilir. *[doğrulama: S2 vektörleri]*

## 6. Runner sözleşmesi

- **S0-RUN-001.** Runner, registry'de bulunmayan bir function'ın suite'lerini çalıştırmaz ve
  sonuçta **MUST** "uygulanmadı" olarak, case sayısıyla birlikte raporlamalıdır. Uygulanmamış
  function'lar test çalıştırmasını başarısız **MUST NOT** saymamalıdır. *[doğrulama: CI]*
- **S0-RUN-002.** Registry'de bulunan bir function'ın bütün case'leri **MUST** geçmelidir.
  Tek tek case'leri atlamak (skip) veya beklenen hata (xfail) olarak işaretlemek **MUST NOT**
  mümkün olmamalıdır. *[doğrulama: CI]*
- **S0-RUN-003.** Her case **SHOULD** ayrı bir test olarak raporlanmalıdır; test adı case'in tam
  adıdır (`s3-pii/tckn-checksum::tckn-ek-dir`).
- **S0-RUN-004.** Runner, `input` değerini function'a değiştirmeden **MUST** iletmelidir.
  Function'ın beklediği tipe çevirme (örneğin JSON nesnesinden dil tipine) registry'deki
  adapter'ın işidir ve anlamı değiştirmemelidir. *[doğrulama: CI]*

## 7. Kapsam denetimi

Repodaki bir script, spec'lerdeki gereklilikleri vektörlerle karşılaştırır.

- **S0-COV-001.** Spec düzyazısında bir gereklilik, satır başında `- **<kimlik>.**` biçimiyle
  tanımlanır. Kaldırılan gereklilik silinmez, `- **<kimlik>.** *(kaldırıldı)*` olarak kalır ve
  kimliği yeniden kullanılmaz. *[doğrulama: CI]*
- **S0-COV-002.** **MUST** veya **MUST NOT** içeren her gereklilik ya en az bir case'in
  `spec_refs` alanında geçmeli ya da satırında `*[doğrulama: <yöntem>]*` etiketiyle başka bir
  doğrulama yöntemi (lint, şema, CI, başka bir spec'in vektörleri) belirtilmelidir.
  *[doğrulama: CI]*
- **S0-COV-003.** `spec_refs` içindeki her kimlik, var olan ve kaldırılmamış bir gerekliliğe
  karşılık gelmelidir. *[doğrulama: CI]*
- **S0-COV-004.** Spec'in `Durum` alanı `taslak` ise S0-COV-002 ve S0-COV-003 ihlalleri uyarı
  olarak raporlanır; `kabul edildi` ise CI'ı **MUST** başarısız kılmalıdır. *[doğrulama: CI]*

## 8. Hata ve bulgu kodları

| Kod | Ne zaman |
|---|---|
| `UNSUPPORTED_FORMAT_VERSION` | Suite'in `format_version` değeri desteklenmiyor (hata) |

Suite doğrulamasının (`testvector.validate`) döndürdüğü sorun (`issues`) kodları:

| Kod | Ne zaman |
|---|---|
| `SCHEMA_INVALID` | Suite şemaya göre geçersiz |
| `CASE_ID_DUPLICATE` | Aynı `id` suite'te birden fazla kez geçiyor |

Görünmez karakter denetimi (`testvector.lint_escapes`) ayrı bir function'dır ve ihlal ettiği
karakterleri listeler.

## 9. Normatif örnekler (vektörler)

S0'ın kendi davranışı da vektörlerle tanımlanır. Bu vektörler runner'ın iç fonksiyonlarını test
eder:

| Suite | Function | Ne test eder |
|---|---|---|
| `s0-format/match.json` | `testvector.match` | Karşılaştırma kuralları (§4) |
| `s0-format/escapes.json` | `testvector.lint_escapes` | Görünmez karakter kuralı (§3.4) |
| `s0-format/validate.json` | `testvector.validate` | Suite doğrulaması (§3) |

- `testvector.match`: `input` iki taraftan oluşur. Beklenen taraf `expected` ya da
  `expected_error`, gerçek taraf `actual` ya da `actual_error` (`{"code", "message"}`); isteğe
  bağlı `match` (`"subset"` | `"exact"`). Çıktı: `{"pass": bool}`.
- `testvector.lint_escapes`: `input` = `{"raw": "<dosyanın ham metni>"}`. Çıktı:
  `{"violations": ["U+XXXX", ...]}`, görünme sırasıyla.
- `testvector.validate`: `input` = `{"suite": <suite nesnesi>}`. Çıktı:
  `{"valid": bool, "issues": ["<kod>", ...]}`. Desteklenmeyen `format_version`'da
  `UNSUPPORTED_FORMAT_VERSION` hatası verir.

## 10. Uyumluluk

- Format, `format_version` ile sürümlenir. Yeni opsiyonel alan eklemek sürümü değiştirmez;
  alan kaldırmak veya anlamını değiştirmek `format_version`'ı artırır.
- Rust runner aynı vektörleri aynı kurallarla çalıştırır. Özellikle S0-CMP-006 (Python'da
  `True == 1`) ve S0-SPAN-001 (Rust'ta string indeksleri byte'tır) iki dil arasındaki bilinen
  tuzaklardır.
- ADR 0004'teki policy test örneği (`name`, `context`, `expect`) fikri göstermek içindir. Policy
  testleri bu spec'teki alan adlarını kullanır (`id`, `description`, `input`, `expected`);
  `context` alanı `input`'un içinde yer alır. Ayrıntıyı S5 tanımlar.
