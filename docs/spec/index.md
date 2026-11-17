# Spec'ler

Battal'da kod spec'ten yazılır. Bu sayfa MVP spec'lerinin listesi, yazım sırası ve durumudur.

## Belge türleri

| Tür | Cevapladığı soru | Değişir mi? |
|---|---|---|
| [Araştırma raporu](../research/index.md) | Ne var, neyi neden seçtik? | Hayır, tarihî belgedir |
| [ADR](../decisions/0001-product-shape-and-licensing.md) | Bu karar neden verildi? | Hayır, yeni ADR ile geçersiz kılınır |
| Spec | Sistem tam olarak nasıl davranır? | Evet, sürümlenir ve kodla birlikte güncellenir |

Kod ile spec çelişirse ya kodda bug vardır ya da önce spec değiştirilir.

## Bir spec'in parçaları

1. **Düzyazı:** bu dizindeki sayfa.
2. **Şema:** `schemas/` altında JSON Schema (veri yapısı tanımlayan spec'lerde).
3. **Normatif örnekler:** `testvectors/` altında JSON test vektörleri.

Düzyazı ile bir vektör çelişirse vektör kazanır ve çelişki spec'te düzeltilir. Vektörler aynı
zamanda Python ve Rust implementasyonlarının ortak test suite'idir
([ADR 0003](../decisions/0003-language-python-then-rust.md)).

## Normatif dil

Spec'ler Türkçedir. Zorunluluk seviyeleri RFC 2119 anahtar kelimeleriyle yazılır: **MUST**,
**MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**. Her gerekliliğin bir kimliği vardır
(örneğin `S3-PII-012`). Ölçülmeden bilinemeyecek değerler `TBD` olarak işaretlenir ve hangi
ölçümle belirleneceği yazılır.

## MVP spec'leri

| # | Spec | Kapsadığı backlog | Bağımlılık | Durum |
|---|---|---|---|---|
| S0 | [Spec ve test vektörü formatı](s0-test-vektorleri.md) | E0.2 | — | kabul edildi (1.1.0) |
| S1 | [Evaluation API sözleşmesi](s1-evaluation-api.md) | E1 | S0 | kabul edildi (1.0.0) |
| S2 | Türkçe normalizasyon | E2 | S0, S1 | planlandı |
| S3 | Türkçe PII | E3 | S0, S1, S2 | planlandı |
| S4 | Injection tespiti | E4 | S0, S1, S2 | planlandı |
| S5 | [Policy, binding ve bundle](s5-policy-binding-bundle.md) | E5 | S0, S1 | kabul edildi (1.0.0) |
| S6 | Sunucu ve LiteLLM adapter'ı | E6 | S1, S5 | planlandı |
| S7 | Karar kaydı | E8 | S1, S5 | planlandı |

**Yazım sırası:** S0 → S1 → S5 → S2 → S3 → S6 → S7 → S4. S4 en çok ölçüm bekleyen değeri
içerdiği için sona kalır.

Bütün MVP spec'leri koddan önce yazılır. Ölçüm gerektiren değerler (injection eşiği, model
seçimi, gecikme bütçesi) `TBD` olarak bırakılır ve ölçümden sonra doldurulur.

Benchmark (E7) ve policy playground (E18) spec'leri sıraları geldiğinde yazılacaktır.

## Süreç

Her spec için:

1. Spec'e özgü açık sorular netleştirilir.
2. Taslak yazılır: düzyazı, şema ve vektörler.
3. Kabul öncesi kontrol listesi geçilir.
4. Gözden geçirilir.
5. Kabul edilir, bu tablo güncellenir ve spec kendi commit'iyle repoya girer.
