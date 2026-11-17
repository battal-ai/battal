# Injection imzaları

| Dosya | Kaynak | Kullanan |
|---|---|---|
| `injection.json` | Battal'ın kendi imza seti | S4 §4–§6 (`injection.rules`) |

- Biçim `schemas/injection-rules.schema.json`'dadır; eşleşme kuralları S4 §5'tedir.
- Dosyanın `version` alanı S4'ün sürümüne eşittir. İmza ya da girdi eklemek minor, çıkarmak
  major sürümdür; her değişiklik `testvectors/s4-injection/` vektörleriyle birlikte yapılır.
- Her imzanın en az bir pozitif ve bir negatif vektörü bulunur (S4-DATA-001).
- Lisans: Apache-2.0 (reponun lisansı).
