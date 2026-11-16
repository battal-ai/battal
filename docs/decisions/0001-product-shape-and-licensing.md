# ADR 0001: Ürün biçimi ve lisanslama

- Durum: kabul edildi
- Tarih: 2026-11-16

## Bağlam

Battal açık kaynak olarak kullanılabilmeli, ileride ücretli bir ticari sürümü de destekleyebilmelidir.
Hedefi, LLM'leri kendi altyapısında çalıştıran ve birincil dili Türkçe olan kurumlardır. İlk
aşamadaki asıl risk ürünün benimsenmemesidir; büyük bir oyuncunun çekirdeği kopyalaması daha
küçük bir risktir.

## Kararlar

1. **Biçim.** Battal, gateway'lerin ve agent runtime'ların çağırdığı bir güvenlik servisi ve SDK'dır.
   LLM proxy değildir. Tek bir evaluation API, değiştirilebilir detector ve policy bileşenlerinin
   önünde durur.
2. **Dağıtım.** Python SDK (in-process) ve Battal Server (container/Helm).
3. **Şimdilik tamamen açık kaynak.** Tüm repo Apache-2.0'dır. Ticari enterprise sürüm sonraki bir
   aşamaya bırakılmıştır. Geldiğinde open-core modelini izler: yeni kod ayrı lisanslı bir
   `enterprise/` dizinine eklenir, production kullanımı license key gerektirir. Daha önce
   yayınlanmış kod Apache-2.0 olarak kalır.
4. **İleriki açık/ücretli sınırı.** Güvenliğin tabanı açık kalır: engine, API/SDK, adapter'lar,
   temel Türkçe detector'lar, deterministik policy, eval harness, herkese açık benchmark. Ücretli
   sürüm için adaylar ölçek, yönetişim ve sektör uzmanlığıdır: multi-tenant control plane, SSO/RBAC,
   denetim kanıtı paketleri, policy canary/rollback, premium ve sektöre özel modeller, destek.
5. **Katkılar.** Kod katkıları için CLA zorunludur; bu, ileride dual licensing seçeneğini açık
   tutar. CLA hazır olana kadar kod PR'ları merge edilmez.
6. **Modeller ve veri.** Koddan ayrı lisanslanır. Temel bir Türkçe güvenlik modeli açıktır; daha
   yüksek doğruluklu ve sektöre özel modeller ticaridir. Kendi lisansı olan üçüncü taraf modeller
   yeniden dağıtılmaz, adapter'larla desteklenir.
7. **Marka.** Ad, kod lisansından ayrı olarak korunur. Fork'lar farklı bir ad kullanmalıdır.
8. **Dil.** Dokümantasyon ve kod yorumları Türkçedir; teknik terimler ve koddaki isimler
   İngilizcedir.

## Elenen alternatifler

- **AGPL çekirdek + ticari lisans:** Kopyalanmaya karşı daha güçlü koruma sağlar, ama kurumsal
  benimsenmeyi yavaşlatır. Ayrıca SDK ve adapter'ların başka ürünlere gömülmesiyle çelişir; buna
  LiteLLM'e upstream entegrasyon da dahildir. İleride yine de mümkündür: Apache-2.0 kod AGPLv3
  çalışmalara dahil edilebilir ve CLA yeniden lisanslamaya izin verir.
- **Source-available çekirdek (BSL/FSL/ELv2):** Açık kaynak değildir, temel bir hedefle çelişir.
- **Ücretli özellikler için ayrı private repo'lar:** CI ve release yükünü artırır; müşteri kodu
  denetleyemez.

## Sonuçlar

- Herkes çekirdeği fork edebilir. Ticari avantaj kod lisansına değil, enterprise özelliklere,
  modellere, markaya ve desteğe dayanır.
- İleride ücretli sürüme ayrılacak özellikler açık çekirdeğe erken eklenmemelidir, çünkü yayınlanan
  kod geri alınamaz. Bunların sonradan ayrı modüller olarak eklenebilmesi için extension point'ler
  bırakılır.
- İlk ticari satıştan önce hukuki inceleme gereklidir.
