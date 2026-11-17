---
name: battal-spec
description: Battal reposunda normatif spec yazma, güncelleme ve gözden geçirme süreci. docs/spec/ altında bir spec (S0–S7 veya yenisi) yazılırken, değiştirilirken, bir spec'ten JSON Schema veya test vektörü üretilirken ya da bir spec kabul edilmeden önce kontrol edilirken kullan. Bir spec'ten koda veya görevlere geçerken de bu skill'deki kurallar geçerlidir.
---

# Battal spec'leri

Battal'da kod spec'ten yazılır. Spec, sistemin **tam olarak** nasıl davrandığını tanımlar.
Bu skill spec'lerin biçimini ve yazılma sürecini tanımlar. Spec listesi ve durumları
`docs/spec/index.md` dosyasındadır.

## Belge türleri

| Tür | Yer | Cevapladığı soru | Değişir mi? |
|---|---|---|---|
| Araştırma raporu | `docs/research/` | Ne var, neyi neden seçtik? | Hayır, tarihî belgedir |
| ADR | `docs/decisions/` | Bu karar neden verildi? | Hayır, yeni ADR ile geçersiz kılınır |
| Spec | `docs/spec/` | Sistem tam olarak nasıl davranır? | Evet, sürümlenir ve kodla birlikte güncellenir |

- Kod ile spec çelişirse ya kodda bug vardır ya da önce spec değiştirilir. Kod, spec'te olmayan
  davranış eklemez.
- Bir spec bir ADR kararıyla çelişemez. Çelişki gerekiyorsa önce yeni bir ADR yazılır.

## Bir spec'in üç parçası

1. **Düzyazı:** `docs/spec/<kimlik>-<ad>.md`. Davranışın tarifi.
2. **Şema:** `schemas/` altında JSON Schema (draft 2020-12). Yalnızca veri yapısı tanımlayan
   spec'lerde bulunur (API, policy, `bindings.yaml`, test dosyaları, karar kaydı).
3. **Normatif örnekler:** `testvectors/<alan>/` altında JSON test vektörleri. Formatı S0'da
   tanımlanır.

**Düzyazı ile bir vektör çelişirse vektör kazanır.** Çelişki spec'te bir bug olarak düzeltilir.

## Yazım kuralları

- Dil Türkçedir. Teknik terimler ve koddaki isimler İngilizce kalır.
- Zorunluluk seviyeleri RFC 2119 anahtar kelimeleriyle, kalın ve büyük harfle yazılır: **MUST**,
  **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**. Bu kelimeler yalnızca normatif cümlelerde
  kullanılır. Örnek: "Sunucu, 1 MiB'den büyük isteği **MUST** 413 ile reddetmelidir."
- Her normatif gerekliliğin bir kimliği olur: `S3-PII-012` (spec kimliği, alan, sıra). Kimlikler
  yeniden kullanılmaz; kaldırılan gereklilik "kaldırıldı" olarak işaretlenir.
- Ölçüm gerektiren değerler (eşik, model seçimi, gecikme bütçesi) uydurulmaz. `TBD` olarak
  işaretlenir, hangi ölçümle doldurulacağı yazılır: `TBD (E4.3 kalibrasyonu)`.
- Örnekler gerçekçi ama sentetiktir. Gerçek kişisel veri kullanılmaz. TCKN ve IBAN örnekleri
  checksum'ı geçerli, kimseye ait olmayan test numaralarıdır.
- Gerekçe spec'e girmez, ilgili ADR'ye ya da rapora link verilir.

## Süreç

Her spec için sırasıyla:

1. **Grilling.** Spec'e özgü açık soruları kullanıcıyla netleştir (`grilling` skill'i). Daha önce
   kararlaştırılmış konular (ADR'ler, `docs/urun.md`) yeniden sorulmaz.
2. **Taslak.** Düzyazıyı [şablona](references/spec-template.md) göre yaz; şemayı ve vektörleri
   üret. Durum: `taslak`.
3. **Kontrol.** Aşağıdaki listeyi geç.
4. **Okuma.** Kullanıcı okur; düzeltmeler yapılır.
5. **Kabul.** Durum `kabul edildi` olur, `docs/spec/index.md` tablosu güncellenir, spec kendi
   commit'iyle girer. Commit yalnızca kullanıcının onayıyla yapılır.

Kabul edilmiş bir spec değiştiğinde: sürüm artırılır (geriye uyumsuz değişiklik → major),
değişiklik geçmişine satır eklenir, etkilenen vektörler aynı commit'te güncellenir.

## Kabul öncesi kontrol listesi

- [ ] Başlık bilgileri tam: durum, sürüm, ilgili ADR'ler, değişiklik geçmişi.
- [ ] Her **MUST** / **MUST NOT** gerekliliğinin en az bir test vektörü var ve vektör
      gereklilik kimliğine atıf yapıyor.
- [ ] Hata ve sınır durumları tanımlı: boş girdi, aşırı büyük girdi, geçersiz girdi, bağımlı
      bileşenin çökmesi.
- [ ] Ölçüm gerektiren her değer `TBD (<ölçüm>)` olarak işaretli; uydurulmuş sayı yok.
- [ ] Şema varsa vektörlerdeki bütün örnekler şemaya göre geçerli.
- [ ] Deterministik davranış (ADR 0003): global state yok, I/O yok, girdi ve çıktı açık.
      Rust implementasyonu yalnızca bu spec ve vektörlerle yazılabilir mi?
- [ ] ADR'lerle ve diğer kabul edilmiş spec'lerle çelişki yok.
- [ ] Kapsam dışı olanlar açıkça yazılmış.
- [ ] İçerikte özel bilgi (kurum adı, gerçek kişisel veri) yok.

## Spec'ten koda

- Görevler `planning-and-task-breakdown` skill'iyle çıkarılır, ama `tasks/` dizini kullanılmaz.
  Görevler raporun backlog'undaki ilgili PBI'ların altına ya da kullanıcının belirlediği
  tracker'a yazılır.
- Kod `test-driven-development` ile yazılır. İlk kırmızı testler spec'in vektörleridir.
- API ve interface tasarımında `api-and-interface-design` skill'i kullanılır; spec ile
  çelişirse spec geçerlidir.
