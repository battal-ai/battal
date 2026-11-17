# ADR 0002: İlk sürüm (MVP) kapsamı ve doğrulama ilkeleri

- Durum: kabul edildi
- Tarih: 2026-11-16
- Güncelleme: 2026-11-17 (policy binding ve policy testleri, ADR 0004)

## Bağlam

Battal'ı şimdilik tek bir geliştirici, haftada yaklaşık 8–10 saat ayırarak geliştiriyor. Bir pilot
kurum ya da kurumsal GPU kümesi yok. Bu yüzden ilk sürümün dar olması, tek bir geliştiricinin
bitirebileceği büyüklükte kalması ve herkesin kendi bilgisayarında yeniden üretebileceği şekilde
kanıtlanması gerekiyor.

## Kararlar

1. **Önce gateway.** İlk entegrasyon LiteLLM'dir. Hedef, Battal'ın LiteLLM'in guardrail
   entegrasyonlarından biri olarak upstream'e girmesidir. Code studio entegrasyonu (önce Claude Code)
   ve agent runtime entegrasyonu (Nous Research Hermes Agent) sonraki sürümlere kalır.
2. **Önce CPU.** Battal, GPU olmadan sıradan bir CPU'da çalışmalıdır. Varsayılan detector'lar küçük
   sınıflandırıcılar (ONNX) ve deterministik kurallardır. Büyük LLM tabanlı guard'lar yalnızca
   adapter üzerinden kullanılır; kullanıcı kendi model sunucusunu (vLLM, Ollama) sağlar.
3. **Önce sözleşme.** İlk sürüm bir çekirdek kütüphane ve onun üstünde ince bir HTTP sunucusundan
   (FastAPI) oluşur. LiteLLM adapter'ı Battal'a evaluation API üzerinden bağlanır, böylece Battal
   gateway'e bağımlı olmaz.
4. **Demo senaryosu.**
   - Input'ta Türkçe ve Türkçe–İngilizce karışık prompt injection ve jailbreak tespiti; Unicode ve
     görünmez karakterlerle gizlenmiş içerik dahil.
   - Input ve output'ta TCKN, IBAN, telefon ve e-posta maskeleme; TCKN ve IBAN için checksum
     doğrulaması.
   - Kapsam dışı: streaming denetimi, tool call güvenliği, RAG denetimi.
5. **Policy.** Basit bir YAML policy, tespit sonucunu bir eyleme bağlar: izin ver, maskele, engelle.
   Policy engine bir interface'in arkasında durur. OPA/Rego veya Cedar, tool call yetkilendirmesi
   geldiğinde değerlendirilir. Policy'ler `bindings.yaml` ile checkpoint, tenant/team/key ve
   model düzeyinde bağlanır; global taban policy her zaman çalışır (ADR 0004).
6. **Policy testleri.** Policy test formatı (`*.test.yaml`) ve CLI (`battal policy validate`,
   `test`, `diff`) MVP'dedir. Görsel policy playground MVP'den hemen sonra gelir (ADR 0004).
7. **Hata davranışı.** Fail-open veya fail-closed davranışı her kontrol noktası için policy ile
   belirlenir.
8. **Kanıt.** İlk sürümün kanıtı iki şeydir: herkese açık, yeniden üretilebilir bir Türkçe
   benchmark ve `docker compose up` ile çalışan bir LiteLLM + Battal demosu.

## Başarı ölçütleri

Ölçütlerin yapısı şimdiden belirlenmiştir. Sayısal hedefler ilk baseline ölçümünden sonra konacaktır.

- **Injection ve jailbreak:** Zararsız Türkçe veri üzerinde sabitlenmiş bir yanlış engelleme
  oranında, Battal'ın recall değeri hazır baseline'lardan yüksek olmalıdır.
- **PII:** Checksum ile doğrulanabilen alanlarda (TCKN, IBAN) kaçırma oranı sıfıra yakın olmalıdır.
  Hatalı maskeleme ayrıca ölçülür. Karşılaştırma Presidio'nun varsayılan ayarlarıyla yapılır.
- **Gecikme:** Hedef, CPU'da p95 ≤ 150 ms ek gecikmedir. Bu bir hedeftir, ölçülmüş bir değer
  değildir.

## Benchmark verisi

- Herkese açık yayınlanır: CC-BY-4.0 lisansıyla Hugging Face'te.
- Yalnızca kendi yazdığımız örnekler, sentetik örnekler ve lisansı izin veren kaynaklar kullanılır.
  Production trafiği kullanılmaz.
- Train, calibration ve test bölümleri saldırı şablonu ailesine göre ayrılır. Böylece aynı
  saldırının çevirileri ve yakın kopyaları farklı bölümlere sızmaz.

## Sonuçlar

- İlk sürüm dar ama baştan sona gösterilebilir.
- Streaming, tool call ve RAG kontrolleri sonraki sürümlerde gelir. Çekirdeğin interface'leri
  bunları baştan hesaba katmalıdır.
