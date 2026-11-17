# Lisanslama

Bu repodaki tüm kod [Apache License 2.0](https://github.com/battal-ai/battal/blob/main/LICENSE) ile lisanslanmıştır.

İleride ticari bir enterprise sürüm sunulabilir. Sunulursa, ayrı lisanslı yeni kod olarak eklenir.
Apache-2.0 ile yayınlanmış her şey Apache-2.0 olarak kalır.

## Model ağırlıkları ve veri setleri

Model ağırlıkları ve veri setleri koddan ayrı lisanslanır; her birinin lisansı kendi model veya
dataset card'ında belirtilir. Kodun açık kaynak lisanslı olması, Battal ile kullanılan bir modelin
ya da veri setinin de açık olduğu anlamına gelmez. Kendi lisansı olan üçüncü taraf modeller (örneğin
Llama Community License modelleri) bu proje tarafından yeniden dağıtılmaz; adapter'lar sayesinde
bunları kendi lisans anlaşmanız kapsamında takabilirsiniz.

## Marka

"Battal" adı ve ilgili logolar proje sahibinin markasıdır. Apache License bunları kullanma izni
vermez (lisansın 6. maddesi). Fork'lar farklı bir ad kullanmalıdır.

## Üçüncü taraf dosyalar

`.claude/skills/` altındaki bazı Claude Code skill'leri üçüncü taraf projelerden, MIT lisansıyla
alınmıştır. Her birinin dizininde orijinal `LICENSE` dosyası ve kaynağını belirten bir `SOURCE.md`
bulunur. Bu dosyalar Apache-2.0 değil, kendi MIT lisanslarıyla dağıtılır.

`data/unicode/` altındaki veri dosyaları Unicode'un `confusables.txt` (UTS #39, 15.1.0) dosyasından
türetilmiştir ve [Unicode License V3](https://www.unicode.org/license.txt) ile dağıtılır
(`data/unicode/LICENSE`). Türetme kuralı S2 §5.2'de, türetme script'i
`scripts/derive_confusables.py` dosyasındadır.

S3'teki Türkiye telefon numaralandırma desenleri, `phonenumbers` 9.0.43 paketindeki
libphonenumber metadata'sından (Apache-2.0) alınmıştır; atıf `NOTICE` dosyasındadır.
