# S3: Türkçe PII

- Durum: kabul edildi
- Sürüm: 1.0.0
- İlgili ADR'ler: [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0003](../decisions/0003-language-python-then-rust.md),
  [ADR 0006](../decisions/0006-pii-without-presidio.md)
- İlgili backlog: E3 (PBI 3.1–3.3)
- Test vektörleri: `testvectors/s3-pii/`
- Araştırma: [Ek 3 §2](../research/ekler/03-pii-secrets-turkish.md)

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-17 | İlk taslak |
| 1.0.0 | 2026-11-17 | Kabul edildi; kesme işaretsiz e-posta eki (S3-EML-003), VKN–telefon çakışması notu |

## 1. Amaç ve kapsam

Bu spec, MVP'nin PII detector'larını tanımlar: checksum algoritmaları, adayların S2 görünümlerinde
nasıl bulunduğu, bağlam kelimelerinin nasıl arandığı ve üretilen detection'ların alanları. Hangi
detection'ın maskeleneceği policy'nin kararıdır (S5); bu spec yalnızca tespiti tanımlar.

**Kapsam dışı:**

- TR dışındaki ülkelerin IBAN'ları, kart numaraları, IMEI, IMSI, ICCID, isim ve adres (E17).
  Luhn fonksiyonu tanımlıdır ama MVP'de onu kullanan bir detector yoktur.
- Numaranın gerçekten var olup olmadığının kontrolü (NVİ, GİB, banka sorgusu). Çekirdek I/O
  yapmaz.
- Telefon numarasından operatör çıkarımı (numara taşınabilirliği nedeniyle anlamsızdır).
- Presidio entegrasyonu (ADR 0006, E17).

## 2. Terimler

| Terim | Tanım |
|---|---|
| Aday | Bir detector'ın biçimine uyan metin parçası; checksum'ı geçmesi gerekmez |
| Ayırıcı | Rakam grupları arasında izin verilen tek karakter |
| Bağlam sözlüğü | Bir detector için bağlam kelimelerinin sabit listesi |
| Pencere | Adayın önündeki ve arkasındaki en fazla 4 token |

Diğer terimler [sözlükteki](../sozluk.md) anlamlarıyla kullanılır.

## 3. Detector'lar

| Detector | Görünüm | `checksum_valid` | `context_hit` | Yer tutucu (S5-ACT-003) |
|---|---|---|---|---|
| `pii.tckn` | `pii` | var | var | `<TCKN>` |
| `pii.vkn` | `pii` | var | var | `<VKN>` |
| `pii.iban` | `pii` | var | yok | `<IBAN>` |
| `pii.phone` | `pii` | yok | var | `<PHONE>` |
| `pii.email` | `pii` | yok | yok | `<EMAIL>` |

- **S3-GEN-001.** Detector'lar saf fonksiyonlardır; girdi olarak S2'nin `normalize` sonucunu
  alırlar. Aynı girdi için **MUST** aynı detection'ları üretmelidirler. *[doğrulama: CI]*
- **S3-GEN-002.** Bir detection'da yalnızca tablonun "var" dediği isteğe bağlı alanlar bulunur;
  "yok" denen alan **MUST NOT** üretilmemelidir. (S5'e göre olmayan alan koşulu sağlamaz.)
- **S3-GEN-003.** Detection'ın `span`'i, adayın `pii` görünümündeki aralığının S2-MAP-001 ile
  orijinal metne eşlenmiş hâlidir.
- **S3-GEN-004.** Detection'ın `version` alanı bu spec'in sürümüdür.
- **S3-GEN-005.** Detector'lar birbirinden bağımsızdır; aynı metin parçası birden fazla
  detector'ın detection'ı olabilir. Detection'lar segment, `span` başlangıcı ve detector adına
  göre (code point sırası) **MUST** sıralanmalıdır.

## 4. Checksum algoritmaları

Bütün fonksiyonlar bir string alır ve boolean döndürür; biçime uymayan girdi hata değil `false`'tur.

- **S3-CHK-001. TCKN.** `s` 11 ASCII rakam değilse ya da `d0 = 0` ise `false`. Aksi hâlde
  `O = d0+d2+d4+d6+d8`, `E = d1+d3+d5+d7`; geçerli olması için `(7·O − E) mod 10 = d9`
  (matematiksel mod: sonuç 0–9) ve `(d0+…+d9) mod 10 = d10` **MUST** sağlanmalıdır.
- **S3-CHK-002. VKN.** `s` 10 ASCII rakam değilse `false`. `t = 0`; `i = 1…9` için
  `c1 = (d[9−i] + i) mod 10`; `c1 ≠ 0` ise `c2 = (c1 · 2^i) mod 9`, `c2 = 0` ise `c2 = 9`,
  `t += c2`. Geçerli olması için `(10 − t mod 10) mod 10 = d9` **MUST** sağlanmalıdır.
- **S3-CHK-003. IBAN-TR.** `s`'deki boşluklar silinir, harfler büyütülür. Geçerli olması için:
  uzunluk 26, `s[0:2] = "TR"`, `s[2:10]` 8 rakam (kontrol hanesi 2, banka kodu 5, rezerv 1),
  `s[10:26]` 16 alfanümerik; `s[4:] + s[0:4]` dizisinde her harf `A=10 … Z=35` olarak yazılıp
  elde edilen tam sayı `mod 97 = 1` **MUST** olmalıdır.
- **S3-CHK-004. Luhn.** `s` en az 2 ASCII rakam değilse `false`. Sağdan sola, sağdan ikinci
  haneden başlayarak her ikinci hane iki ile çarpılır, sonuç 9'dan büyükse 9 çıkarılır; bütün
  hanelerin toplamı `mod 10 = 0` ise **MUST** `true` olmalıdır.

## 5. Aday bulma

Adaylar `pii` görünümünde aranır (S2 §6: bütün Unicode rakamlar ASCII'dir, görünmez karakterler
yoktur, NFKC uygulanmıştır). Kurallar regex lookaround'u gerektirmeyecek şekilde, sınır
koşullarıyla tanımlanır.

### 5.1 TCKN ve VKN

- **S3-CAND-001.** **Rakam koşusu**: bir ASCII rakamla başlayan, rakamlardan ve iki rakam
  arasındaki tek bir ayırıcıdan (` ` ya da `-`) oluşan en uzun dizidir. Koşunun başladığı rakamın
  hemen önünde rakam **MUST NOT** bulunmamalı ve önünde "rakam + ayırıcı" **MUST NOT**
  bulunmamalıdır. Nokta TCKN ve VKN için ayırıcı değildir (`10.000.000.146` bir para tutarıdır).
- **S3-CAND-002.** Bir koşu tam olarak 11 rakam içeriyor ve ilk rakamı `0` değilse `pii.tckn`
  adayıdır; tam olarak 10 rakam içeriyorsa `pii.vkn` adayıdır. Diğer koşular aday **MUST NOT**
  olmamalıdır; daha uzun bir koşunun parçası aday olamaz.
- **S3-CAND-003.** Adayın span'i koşunun ilk rakamından son rakamına kadardır. Koşudan sonra gelen
  harfler (Türkçe ek), kesme işareti ve noktalama span'e **MUST NOT** dahil edilmemelidir:
  `10000000146dır` ve `10000000146'dır` adaydır.
- **S3-CAND-004.** `checksum_valid`, koşudaki rakamların (ayırıcılar çıkarılarak) S3-CHK-001 ya
  da S3-CHK-002 sonucudur.

### 5.2 IBAN

- **S3-IBAN-001.** Aday `T`/`t` ile başlar, ardından `R`/`r` gelir; `T`'nin hemen önünde harf
  (`\p{L}`) ya da rakam **MUST NOT** bulunmamalıdır. Ardından 24 ASCII alfanümerik karakter
  gelir; herhangi iki karakter arasında (ve `R` ile ilk kontrol hanesi arasında) tek bir boşluk
  olabilir.
- **S3-IBAN-002.** Bu 24 karakterin ilk 8'i rakam değilse aday **MUST NOT** üretilmemelidir
  (biçim: kontrol hanesi 2, banka kodu 5, rezerv 1).
- **S3-IBAN-003.** 24. karakterden hemen sonra rakam gelmemelidir. Harf geliyorsa 24. karakter
  rakam olmalıdır (Türkçe ek: `…26ya`); aksi hâlde aday **MUST NOT** üretilmemelidir.
- **S3-IBAN-004.** Span `T`'den 24. karakterin sonuna kadardır; `checksum_valid` S3-CHK-003
  sonucudur.

### 5.3 Telefon

Ayırıcılar: ` `, `.`, `-`. `S` en fazla bir ayırıcıyı, `A` üç rakamlık alan/operatör kodunu (isteğe
bağlı parantez içinde: `(532)`), `R` her birinin önünde en fazla bir ayırıcı olabilen yedi rakamı
gösterir.

| Biçim | Örnek |
|---|---|
| F1: `+90` S A R | `+90 532 123 45 67` |
| F2: `0090` S A R | `0090 532 123 4567` |
| F3: `0` S A R | `0532 123 45 67`, `0 (532) 123-45-67` |
| F4: `(0` 3 rakam `)` R | `(0532) 123 45 67` |
| F5: A R (öneksiz) | `532 123 45 67` |

- **S3-PHN-001.** Metin soldan sağa taranır; her konumda F1–F5 bu sırayla denenir, ilk eşleşen
  biçim alınır ve tarama eşleşmenin sonundan devam eder. Eşleşmenin başlangıcının hemen önünde
  rakam, `+` ya da "rakam + ayırıcı" **MUST NOT** bulunmamalı; sonunun hemen arkasında rakam ya da
  "ayırıcı + rakam" **MUST NOT** bulunmamalıdır.
- **S3-PHN-002.** Ulusal numara (A ve R'nin 10 rakamı) aşağıdaki **mobil** ya da **sabit hat**
  desenlerinden biriyle tamamen eşleşmelidir; F5 biçiminde yalnızca mobil desen kabul edilir.
  Eşleşmeyen eşleşme aday **MUST NOT** olmamalıdır.
    - Mobil: `5(?:61(?:011|61\d)|82[2-5]\d\d)\d{4}|5(?:[03-5]\d|1[06]|24|6[24]|7[245]|9[46])\d{7}`
    - Sabit hat: `(?:2(?:1[26]|[28][2468]|[3-5][268]|[67][246])|3(?:[13][28]|[24-6][2468]|[78][02468]|92)|4(?:[16][246]|[23578][2468]|4[26]))\d{7}`

    Kaynak: `phonenumbers` 9.0.43 TR metadata (`region_TR.py`, Apache-2.0). Bu desenler
    lookaround içermez.
- Öneksiz 10 haneli bir mobil numara (`532 123 45 67`) aynı zamanda bir `pii.vkn` adayıdır
  (S3-GEN-005). İki detection'ın span'i eşittir; ikisi de maskelenirse S5-ACT-004'e göre yer
  tutucu `<PHONE>` olur (`pii.phone` < `pii.vkn`). VKN'yi telefondan ayırmak için policy
  `context_hit` koşulunu kullanır.
- **S3-PHN-003.** Span biçimin ilk karakterinden (`+`, `0` ya da `(`) son rakamına kadardır.
  Kısa numaralar (`444 …`), ücretsiz hatlar (`800`), `850` ve premium hatlar MVP'de aday değildir.

### 5.4 E-posta

- **S3-EML-001.** Aday: yerel kısım (`\p{L}`, `\p{N}`, `.`, `_`, `%`, `+`, `-` karakterlerinden
  en az biri), `@`, en az iki etiketten oluşan alan adı. Etiketler `\p{L}`, `\p{N}` ve `-`
  karakterlerinden oluşur ve `.` ile ayrılır; son etiket yalnızca harflerden (`\p{L}`) oluşur ve en
  az 2 karakterdir. Yerel kısmın hemen önünde yerel kısım karakteri **MUST NOT** bulunmamalıdır.
- **S3-EML-002.** Alan adı mümkün olan en uzun biçimde alınır; sondaki `.` ya da `-` span'e
  dahil edilmez. Kesme işaretli ekler (`ali@ornek.com'a`) span dışında kalır.
- **S3-EML-003.** Son etiketin S2-LOW-001'e göre küçük harfli hâli TLD listesinde değilse ve
  `T + E` biçimindeyse (`T` TLD listesinde, `E` ek listesinde), span **MUST** `T`'nin sonunda
  bitmelidir: `ali@ornek.comdan` → `ali@ornek.com`, `veli@ornek.com.trye` → `veli@ornek.com.tr`.
  Bu biçimde olmayan etiketler (`ornek.community`, `ornek.travel`) olduğu gibi kalır.

    | Liste | Girdiler |
    |---|---|
    | TLD | `com`, `net`, `org`, `edu`, `gov`, `mil`, `info`, `biz`, `io`, `tr` |
    | Ek | `a`, `e`, `ı`, `i`, `u`, `ü`, `ya`, `ye`, `yı`, `yi`, `yu`, `yü`, `da`, `de`, `ta`, `te`, `dan`, `den`, `tan`, `ten`, `daki`, `deki`, `taki`, `teki`, `ın`, `in`, `un`, `ün`, `nın`, `nin`, `nun`, `nün`, `la`, `le`, `yla`, `yle`, `dır`, `dir`, `dur`, `dür`, `tır`, `tir`, `tur`, `tür` |

    Listede olmayan bir TLD'ye kesme işaretsiz eklenen ek (`ali@ornek.dedan`) son etiketin
    parçası sayılır; bu durumda span metni fazladan kapsar, eksik kapsamaz.

## 6. Bağlam

- **S3-CTX-001.** `match_ascii` görünümü S2-TOK-001'e göre token'lara bölünür; her token'ın
  orijinal metindeki aralığı offset haritasıyla bulunur. Adayın orijinal aralığından tamamen önce
  biten son 4 token ve tamamen sonra başlayan ilk 4 token **pencere**dir. Pencere aynı
  segment'le sınırlıdır.
- **S3-CTX-002.** Penceredeki bir token detector'ın bağlam sözlüğündeki bir girdiyle eşleşirse
  `context_hit` **MUST** `true`, aksi hâlde `false` olmalıdır. Girdi `=` ile başlıyorsa token
  girdiye birebir eşit olmalıdır; aksi hâlde token girdiyle başlamalıdır. Boşluk içeren girdi
  (örneğin `=t c`), penceredeki ardışık token'larla sırasıyla birebir eşleşmelidir.

| Detector | Bağlam sözlüğü (`match_ascii` biçiminde) |
|---|---|
| `pii.tckn` | `=tc`, `=t c`, `tckn`, `tckimlik`, `kimlik`, `kimlig`, `nufus`, `vatandas` |
| `pii.vkn` | `vkn`, `vergi`, `=vd` |
| `pii.phone` | `tel`, `cep`, `gsm`, `whatsapp`, `=wp`, `mobil`, `phone`, `=ara`, `aray`, `ariy` |

Kökler Türkçe ünsüz yumuşamasını açıkça içerir (`kimlik` → `kimliğim` → `kimlig`); stemmer
kullanılmaz.

## 7. Detection alanları

| Alan | Açıklama |
|---|---|
| `detector`, `version`, `segment`, `span` | S1 §5.2 |
| `checksum_valid` | §4'teki fonksiyonun sonucu (yalnızca `pii.tckn`, `pii.vkn`, `pii.iban`) |
| `context_hit` | §6 (yalnızca `pii.tckn`, `pii.vkn`, `pii.phone`) |

- **S3-OUT-001.** Detection eşleşen metni **MUST NOT** içermemelidir (S1-DET-001).
  *[doğrulama: şema]*

## 8. Normatif örnekler (vektörler)

| Suite | Function | Ne test eder |
|---|---|---|
| `s3-pii/tckn.json` | `pii.tckn.validate` | TCKN checksum |
| `s3-pii/vkn.json` | `pii.vkn.validate` | VKN checksum |
| `s3-pii/iban.json` | `pii.iban.validate` | IBAN-TR checksum |
| `s3-pii/luhn.json` | `pii.luhn.validate` | Luhn |
| `s3-pii/detect-ids.json` | `pii.detect` | TCKN ve VKN adayları, bağlam |
| `s3-pii/detect-iban-email.json` | `pii.detect` | IBAN ve e-posta adayları |
| `s3-pii/detect-phone.json` | `pii.detect` | Telefon biçimleri |

- `pii.*.validate`: `input` = `{"value"}`; çıktı = `{"valid"}`.
- `pii.detect`: `input` = `{"text"}` (tek segment, `segment` = 0); çıktı = `{"detections"}`.

Örneklerdeki numaralar checksum'ı bilinçli olarak hesaplanmış sentetik değerlerdir; gerçek kişi ya
da kuruma ait değildir.

## 9. Uyumluluk

- Telefon desenleri yeni bir `phonenumbers` sürümüne göre güncellendiğinde minor sürüm artar ve
  vektörler birlikte güncellenir.
- S3-EML-003'teki TLD ya da ek listesine girdi eklemek minor, girdi çıkarmak major sürümdür.
- Bağlam sözlüğüne girdi eklemek minor, girdi çıkarmak major sürümdür (policy'lerin davranışı
  değişir).
- Rust implementasyonu için: aday kuralları lookaround gerektirmez; `\p{L}` ve `\p{N}` sınıfları
  `regex` crate'inde desteklenir.
