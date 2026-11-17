# Unicode verileri

| Dosya | Kaynak | Kullanan |
|---|---|---|
| `confusables-fold-15.1.0.json` | UTS #39 `confusables.txt` 15.1.0'dan türetilmiş katlama tablosu | S2 §5.2 (confusable katlama) |

- Türetme kuralı S2 §5.2'de tanımlıdır. Tabloyu yeniden üretmek için:
  `python scripts/derive_confusables.py confusables.txt data/unicode/confusables-fold-15.1.0.json`
- Kaynak dosyanın SHA-256 değeri tablonun `source_sha256` alanındadır; farklı bir kaynakla
  üretilen tablo kabul edilmez.
- Lisans: Unicode License V3 (`LICENSE`).
