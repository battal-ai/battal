# S2: Türkçe normalizasyon

- Durum: kabul edildi
- Sürüm: 1.0.0
- İlgili ADR'ler: [ADR 0002](../decisions/0002-mvp-scope.md),
  [ADR 0003](../decisions/0003-language-python-then-rust.md)
- İlgili backlog: E2 (PBI 2.1–2.5)
- Veri: `data/unicode/confusables-fold-15.1.0.json` (türetme: `scripts/derive_confusables.py`)
- Test vektörleri: `testvectors/s2-normalize/`
- Araştırma: [Ek 3 §3](../research/ekler/03-pii-secrets-turkish.md)

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1.0 | 2026-11-17 | İlk taslak |
| 1.0.0 | 2026-11-17 | Kabul edildi |

## 1. Amaç ve kapsam

Bu spec, bir segment metninden detector'ların çalıştığı **görünümleri**, policy'lerin kullandığı
**sinyalleri** ve kodlanmış parçaların çözülmüş hâllerini nasıl üretildiğini; görünümlerdeki bir
konumun orijinal metne nasıl geri eşlendiğini tanımlar. Normalizasyon orijinal metni hiçbir zaman
değiştirmez; maskeleme her zaman orijinal metin üzerinde yapılır (S5 §7.3).

**Kapsam dışı:**

- Mojibake onarımı (ftfy), rakama benzeyen harf düzeltmesi (`O→0`, `l→1`), rot13 çözme ve
  deasciifier. Benchmark (E7) gerekli olduklarını gösterirse eklenir.
- Stemming ve kural eşleşmesi: S4. PII tanıyıcıları, rakam gruplama ve Türkçe ek toleransı: S3.
- Görünmez karakter içeren metnin engellenip engellenmeyeceği: bu bir policy kararıdır (S5).

## 2. Terimler

| Terim | Tanım |
|---|---|
| Görünüm | Normalizasyonun orijinal metinden ürettiği, offset haritalı metin |
| Offset haritası | Bir görünümün her code point'i için orijinal metindeki `[start, end)` aralığı |
| Chunk | NFKC'nin uygulandığı birim: bir starter (ccc = 0) ve onu izleyen non-starter'lar |
| Token | `L*`, `M*`, `Nd` kategorilerindeki ya da `@`, `$` karakterlerinin en uzun kesintisiz dizisi |
| Sinyal | Normalizasyon sırasında sayılan şüpheli özellik; adı sabit, değeri bir sayı |
| Çözülmüş parça | Metindeki base64, hex, URL-encoded ya da tag kodlu bir parçanın çözülmüş hâli |

## 3. Interface

```text
normalize(text, config?) -> Normalized
Normalized.views:     {orig, clean, pii, match, match_ascii}   (her biri metin + offset haritası)
Normalized.signals:   {<sinyal>: <sayı>}                        (yalnızca sıfırdan büyükler)
Normalized.decoded:   [Decoded]
Normalized.to_orig(view, span) -> span
Decoded: {encoding, depth, span, text, match, match_ascii}
```

- **S2-GEN-001.** `normalize` saf bir fonksiyondur: aynı `text` ve `config` için **MUST** aynı
  sonucu vermeli; global state, I/O, saat ve rastgelelik kullanmamalıdır. *[doğrulama: CI]*
- **S2-GEN-002.** `orig` görünümü girdi metninin kendisidir; normalizasyon onu **MUST NOT**
  değiştirmemelidir.
- **S2-GEN-003.** Boş metin için bütün görünümler boş, `signals` ve `decoded` boş **MUST**
  olmalıdır.
- **S2-GEN-004.** Bütün span'ler S0-SPAN-001'e uyar: code point cinsinden `[start, end)`.

## 4. `clean` görünümü

`clean` iki adımda üretilir: silme, ardından chunk bazında NFKC.

### 4.1 Silme

- **S2-CLN-001.** Aşağıdaki code point'ler **MUST** silinmelidir:
    - Genel kategori `Cf` (format: zero-width, bidi, tag, soft hyphen, word joiner, BOM…),
      `Co` (özel kullanım), `Cn` (atanmamış), `Cs` (eşlenmemiş surrogate);
    - TAB (U+0009), LF (U+000A) ve CR (U+000D) dışındaki bütün `Cc` karakterleri;
    - Variation selector'lar: U+FE00–FE0F ve U+E0100–E01EF.
- **S2-CLN-002.** Birleşen işaretler (`Mn`, `Me`; variation selector'lar hariç) **MUST NOT**
  silinmemelidir.

### 4.2 NFKC

- **S2-NFK-001.** Silmeden sonra kalan metin chunk'lara bölünür. Bir chunk, `ccc = 0` olan bir
  code point ile başlar ve onu izleyen `ccc ≠ 0` code point'leri içerir; metnin başındaki
  `ccc ≠ 0` code point'ler kendi başlarına bir chunk oluşturur. `clean`, her chunk'a ayrı ayrı
  NFKC uygulanıp sonuçların birleştirilmesiyle **MUST** elde edilmelidir.
- **S2-NFK-002.** Bir chunk'ın NFKC çıktısındaki her code point, chunk'ın orijinal metindeki
  aralığına (ilk code point'inin başından son code point'inin sonuna) **MUST** eşlenmelidir.
  Arada silinmiş code point'ler bu aralığın içinde kalır.

Not: Chunk bazında NFKC, bütün metne uygulanan NFKC'den yalnızca birden fazla starter'ı birleştiren
nadir durumlarda (örneğin Hangul conjoining jamo dizileri) ayrılır. Normatif tanım chunk bazlıdır.

## 5. `match` ve `match_ascii` görünümleri

`match`, `clean` üzerinden şu sırayla üretilir: confusable katlama, leet katlama, Türkçe küçük
harf. `match_ascii`, `match`'e diakritik düşürme uygulanarak üretilir.

### 5.1 Token'lar

- **S2-TOK-001.** Token'lar `clean` üzerinde belirlenir: genel kategorisi `L*`, `M*` ya da `Nd`
  olan veya `@`, `$` olan code point'lerin en uzun kesintisiz dizisi.
- **S2-TOK-002.** Bir token, Unicode Script özelliği `Latin` olan en az bir code point ve
  `Cyrillic` ya da `Greek` olan en az bir code point içeriyorsa **karışık script** token'dır.

### 5.2 Confusable katlama

- **S2-CNF-001.** Yalnızca karışık script token'larda, tablodaki (`data/unicode/confusables-fold-15.1.0.json`)
  her code point **MUST** tablodaki hedefiyle değiştirilmelidir. Tablo dışındaki code point'ler
  ve karışık script olmayan token'lar **MUST NOT** değiştirilmemelidir.
- **S2-CNF-002.** Tablo, UTS #39 `confusables.txt` 15.1.0'dan şöyle türetilir: kaynağı tek bir
  `Cyrillic` ya da `Greek` code point, hedefi yalnızca `[A-Za-z]` harflerinden oluşan eşlemeler
  alınır; kaynağı büyük harf (`Lu`) ve hedefi `l` olan eşlemelerin hedefi `I` yapılır. Latin
  harfler (Türkçe harfler dahil) kaynak olarak tabloda yer almaz. *[doğrulama: CI]*
- **S2-CNF-003.** Hedefi birden fazla harf olan bir eşlemede (`ӕ → ae`) bütün hedef harfler
  kaynak code point'in aralığına eşlenir.

### 5.3 Leet katlama

- **S2-LEET-001.** En az iki harf (`L*`) içeren bir token'da şu karakterler **MUST**
  değiştirilmelidir: `0→o`, `1→i`, `3→e`, `4→a`, `5→s`, `7→t`, `@→a`, `$→s`. İkiden az harf
  içeren token'larda (`5G`, `2026`) değişiklik **MUST NOT** yapılmamalıdır.

### 5.4 Türkçe küçük harf

- **S2-LOW-001.** Küçük harf dönüşümü code point bazında, bağlamdan bağımsız yapılır: `I → ı`,
  `İ → i`; diğer bütün code point'ler Unicode küçük harf eşlemesiyle (`Lowercase_Mapping`)
  dönüştürülür. Bağlama duyarlı kurallar (örneğin Yunan son sigma) **MUST NOT**
  uygulanmamalıdır: `Σ` her zaman `σ` olur.
- **S2-LOW-002.** Sonuçta `i` + U+0307 (birleşen üst nokta) dizisi **MUST NOT** üretilmemelidir:
  `İSTANBUL → istanbul`, `IĞDIR → ığdır`.

### 5.5 Diakritik düşürme (`match_ascii`)

- **S2-ASC-001.** `match_ascii`, `match`'in her code point'i için: `ı → i`; diğerleri için
  code point'in NFD ayrışımından bütün `Mn` code point'leri çıkarılarak **MUST** üretilmelidir.
  Örnek: `ş→s`, `ğ→g`, `ç→c`, `ö→o`, `ü→u`, `â→a`, `é→e`. Ayrışmayan harfler (`ł`, `ß`, Kiril
  harfler) olduğu gibi kalır.

## 6. `pii` görünümü

- **S2-PII-001.** `pii`, `clean`'deki genel kategorisi `Nd` olan her code point'in, onun ondalık
  değerine karşılık gelen ASCII rakamla değiştirilmesiyle **MUST** üretilmelidir (Arapça-Hint,
  Devanagari, matematiksel rakamlar…). Diğer code point'ler değişmez; harf dönüşümü yapılmaz.

## 7. Sinyaller

Sinyaller `orig` üzerinde sayılır (aksi belirtilmedikçe). Çıktıda yalnızca sıfırdan büyük
sinyaller yer alır.

| Sinyal | Sayılan |
|---|---|
| `zero_width` | U+200B, U+200C, U+200D, U+2060, U+FEFF, U+180E; emoji dizilerindeki U+200D hariç (S2-SIG-004) |
| `soft_hyphen` | U+00AD |
| `bidi_control` | U+202A–202E, U+2066–2069, U+200E, U+200F, U+061C |
| `unicode_tag` | U+E0000–E007F; bayrak dizilerindekiler hariç (S2-SIG-002) |
| `other_format` | Yukarıdakilerin dışında kalan `Cf` code point'leri |
| `variation_selector` | U+FE00–FE0F, U+E0100–E01EF; emoji dizilerindekiler hariç (S2-SIG-004) |
| `control_char` | TAB, LF, CR dışındaki `Cc` |
| `private_use` | `Co` |
| `unassigned` | `Cn` |
| `lone_surrogate` | `Cs` |
| `nfkc_changed` | NFKC'nin değiştirdiği chunk sayısı (S2-NFK-001) |
| `mixed_script` | Karışık script token sayısı (S2-TOK-002) |
| `encoded_base64`, `encoded_hex`, `encoded_url`, `encoded_tag` | Kabul edilen çözülmüş parça sayısı, kodlamaya göre |
| `decode_limit_reached` | Çözme sınırına ulaşıldıysa 1 |

- **S2-SIG-001.** Sinyal adları ve tanımları bu tablodakilerdir; bir implementasyon başka adla
  sinyal **MUST NOT** üretmemelidir. Policy'ler bu adları kullanır (S5-RUL-004).
- **S2-SIG-002.** **Bayrak dizisi**: U+1F3F4, ardından bir ya da daha fazla
  U+E0030–E0039 / U+E0061–E007A, ardından U+E007F. Bayrak dizisindeki tag karakterleri hiçbir
  sinyale **MUST NOT** sayılmamalı ve çözülmemelidir; yine de `clean`'den silinirler
  (S2-CLN-001).
- **S2-SIG-003.** Her code point en fazla bir sinyale sayılır; tablo sırası önceliği belirler.
- **S2-SIG-004.** **Emoji dizileri.** Meşru emoji'lerin sinyal üretmemesi için şu code point'ler
  hiçbir sinyale **MUST NOT** sayılmamalıdır (yine de `clean`'den silinirler):
    - Hemen önceki code point'i `Extended_Pictographic` olan U+FE0E ve U+FE0F (❤️);
    - Önceki code point'i `[0-9#*]` ve sonraki code point'i U+20E3 olan U+FE0F (1️⃣ keycap);
    - Önceki code point'i (aradaki U+FE0E, U+FE0F ve U+1F3FB–1F3FF ten rengi modifier'ları
      atlanarak) ve sonraki code point'i `Extended_Pictographic` olan U+200D (👨‍👩‍👧).

    Bu istisnalar dışındaki U+200D ve variation selector'lar (örneğin iki harf arasındaki ZWJ)
    sayılmaya devam eder.

## 8. Çözülmüş parçalar (`decoded`)

### 8.1 Adaylar

Adaylar `clean` üzerinde, soldan sağa aranır.

- **S2-DEC-001. Tag.** Bayrak dizisine ait olmayan U+E0020–E007E tag karakterlerinin `orig`'deki
  her en uzun kesintisiz dizisi (araya giren U+E0000, U+E0001, U+E007F atlanır) bir adaydır.
  Çözümü her tag karakteri için `code point − 0xE0000`'dır. Bu aday `orig` üzerinde aranır, çünkü
  tag karakterleri `clean`'de yoktur. Kodlama adı: `tag`.
- **S2-DEC-002. URL.** Boşluk (`White_Space`) içermeyen en uzun dizilerden, `%[0-9A-Fa-f]{2}`
  kalıbını en az iki kez içerenler adaydır. Çözüm: her `%XX` bir bayt, diğer karakterler UTF-8
  baytlarıdır; `+` dönüştürülmez. Kodlama adı: `url`.
- **S2-DEC-003. Hex ve base64.** `[A-Za-z0-9+/_-]` karakterlerinin en uzun dizisi, ardından en
  fazla iki `=`, bir **koşu**dur. Bir URL adayının içinde kalan koşular atlanır.
    - Koşu `=` içermiyor, yalnızca `[0-9A-Fa-f]` içeriyor, uzunluğu çift ve `min_encoded_length`
      veya daha fazlaysa **hex** adayıdır. Kodlama adı: `hex`.
    - Değilse, `=` hariç uzunluğu `min_encoded_length` veya daha fazla, `uzunluk mod 4 ≠ 1` ve
      hem `+`/`/` hem `-`/`_` içermiyorsa **base64** adayıdır (standart ya da URL-safe; eksik
      `=` tamamlanır). Kodlama adı: `base64`.

### 8.2 Kabul

- **S2-DEC-004.** Bir adayın çözümü ancak şu koşullarda kabul **MUST** edilmelidir: baytlar
  geçerli UTF-8, metin boş değil ve yazdırılabilir code point oranı `min_printable_ratio`
  veya daha fazla. Yazdırılabilir: genel kategorisi `Cc` (TAB, LF, CR hariç), `Cf`, `Cn`, `Co`,
  `Cs` olmayan. Tag adayları her zaman kabul edilir.
- **S2-DEC-005.** Kabul edilen her parça şunları içerir: `encoding`, `depth` (1 ya da 2),
  `span` (orijinal metindeki aralık), `text` (çözülmüş metin, olduğu gibi), `match` ve
  `match_ascii` (çözülmüş metne §4–§5 uygulanarak).
- **S2-DEC-006.** Derinlik 1 parçasının `span`'i adayın `clean` aralığının `orig`'e eşlenmiş
  hâlidir. Derinlik 2 parçaları, çözülmüş bir parçanın `clean` hâlinde aranır ve `span`'leri
  ebeveynlerinin `span`'idir. Derinlik 2'den sonra çözme yapılmaz.

### 8.3 Sıra ve sınırlar

- **S2-DEC-007.** Parçalar şu sırayla üretilir: önce tag adayları (konum sırasıyla), sonra
  `clean` üzerindeki adaylar konum sırasıyla; her derinlik 1 parçasının hemen ardından onun
  derinlik 2 parçaları gelir.
- **S2-DEC-008.** Yeni bir parça `max_decoded_items` sayısını ya da toplam çözülmüş UTF-8 bayt
  sayısı `max_decoded_bytes`'ı aşacaksa çözme **MUST** durmalı, o parça ve sonrakiler
  eklenmemeli ve `decode_limit_reached` sinyali 1 olmalıdır. Kabul edilmeyen adaylar sınıra
  sayılmaz.

| Config | Varsayılan |
|---|---|
| `min_encoded_length` | 16 |
| `min_printable_ratio` | 0.9 |
| `max_decode_depth` | 2 |
| `max_decoded_items` | 16 |
| `max_decoded_bytes` | 65536 |

Bu değerler ölçüm değil, decode bombasına karşı güvenlik sınırlarıdır (PBI 2.5).

## 9. Geri eşleme

- **S2-MAP-001.** `to_orig(view, [a, b))`, `a < b` için `[map[a].start, map[b−1].end)`
  **MUST** döndürmelidir; `map`, görünümün offset haritasıdır.
- **S2-MAP-002.** `a >= b` ya da `b` görünümün uzunluğundan büyükse `to_orig` **MUST**
  `INVALID_SPAN` hatası vermelidir.
- **S2-MAP-003.** `pii` ve `match_ascii` görünümleri sırasıyla `clean` ve `match` ile code point
  sayısı aynı olmak zorunda değildir; her görünümün kendi haritası vardır. *[doğrulama: S2
  vektörleri ve S3 vektörleri]*

## 10. Unicode sürümü

- **S2-UNI-001.** Referans Unicode sürümü 15.1.0'dır. Bir implementasyon kullandığı Unicode
  sürümünü raporlamalı; sürüm 15.1.0'ın altındaysa CI **MUST** başarısız olmalıdır.
  *[doğrulama: CI]*
- **S2-UNI-002.** Vektörler yalnızca Unicode 15.1.0'da atanmış ve sonraki sürümlerde
  özelliklerinin değişmesi beklenmeyen code point'leri kullanır. *[doğrulama: CI]*

## 11. Normatif örnekler (vektörler)

| Suite | Function | Ne test eder |
|---|---|---|
| `s2-normalize/clean.json` | `normalize.text` | Silme, NFKC, `pii` görünümü |
| `s2-normalize/match.json` | `normalize.text` | Confusable, leet, küçük harf, `match_ascii` |
| `s2-normalize/signals.json` | `normalize.signals` | Sinyal sayıları |
| `s2-normalize/decode.json` | `normalize.text` | Çözülmüş parçalar ve sınırlar |
| `s2-normalize/map.json` | `normalize.map_span` | Geri eşleme |
| `s2-normalize/lower.json` | `text.tr_lower` | Türkçe küçük harf |
| `s2-normalize/fold.json` | `text.fold_diacritics` | Diakritik düşürme |

- `normalize.text`: `input` = `{"text", "config"?}`; çıktı = `{"views": {"orig", "clean", "pii", "match",
  "match_ascii"}, "signals", "decoded"}`.
- `normalize.signals`: `input` = `{"text", "config"?}`; çıktı = `{"signals"}`.
- `normalize.map_span`: `input` = `{"text", "view", "span"}`; çıktı = `{"span"}`.
- `text.tr_lower`, `text.fold_diacritics`: `input` = `{"text"}`; çıktı = `{"text"}`.

## 12. Uyumluluk

- Sinyal adları policy'lerde kullanıldığı için bir sinyalin kaldırılması ya da anlamının
  değişmesi major sürümdür; yeni sinyal eklemek minor sürümdür.
- Confusable tablosunun yeni bir Unicode sürümünden türetilmesi minor sürümdür ve vektörlerle
  birlikte yapılır.
- Rust implementasyonu için: `char::to_lowercase` bağlamdan bağımsızdır (S2-LOW-001 ile uyumlu);
  `str::to_lowercase` ise son sigma kuralını uygular ve kullanılmamalıdır. Script özelliği için
  `unicode-script`, NFKC için `unicode-normalization` crate'leri kullanılabilir;
  `Extended_Pictographic` özelliği için Python'da `regex` (`\p{Extended_Pictographic}`), Rust'ta
  bu özelliği sağlayan bir crate kullanılır. Unicode sürümleri S2-UNI-001'e uymalıdır.
