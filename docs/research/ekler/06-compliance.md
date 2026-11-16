# 06 — Uyum, Çerçeveler ve Saldırı Taksonomileri: Battal için Kontrol Eşlemesi

**Araştırma tarihi:** 2026-11-16 · **Kapsam:** EU AI Act (+ Digital Omnibus on AI), KVKK, BTK, Siber Güvenlik Kanunu, NIST AI RMF / AI 600-1 / AML taksonomisi, MITRE ATLAS, OWASP LLM Top 10 2025 ve OWASP Agentic çalışmaları.

> **Hukuki uyarı:** Bu belge hukuki görüş değildir. Mühendislik ve ürün planlaması için hazırlanmış bir kaynak taramasıdır. Bir kurumun hangi yükümlülüğe tabi olduğu (rol, risk sınıfı, sektör, sınır ötesi veri akışı) hukuk birimi veya dış danışman tarafından değerlendirilmelidir. **Battal'ı kullanmak, bir kurumu tek başına hiçbir mevzuata "uyumlu" hâle getirmez.** Battal ancak kurumun kendi uyum programının teknik kanıt üreten bir parçası olabilir.

**Etiketler:**
- **[D]** Doğrulandı: birincil kaynak metni bu çalışmada okundu.
- **[Ç]** Çıkarım: kaynaklara dayanan yorum. Metinde açıkça yazmıyor.
- **[DY]** Doğrulanamadı: birincil kaynaktan teyit edilemedi.

---

## 0. Yönetici özeti

1. **Üç ayrı katman var ve birbirine karıştırılmamalı:** (a) **hukuki yükümlülükler** (EU AI Act, KVKK, BTK yönetmelikleri, 7545 sayılı Kanun), (b) **gönüllü risk yönetimi çerçeveleri** (NIST AI RMF, AI 600-1, Cyber AI Profile taslağı), (c) **saldırı taksonomileri / tehdit listeleri** (MITRE ATLAS, OWASP LLM Top 10 2025, OWASP Agentic Top 10 2026, NIST AML taksonomisi). Bağlayıcı olan yalnızca (a)'dır ve o da role ve risk sınıfına göre değişir.
2. **EU AI Act yüksek risk tarihleri ertelendi ve bu artık yürürlükte olan hukuktur.** Regulation (EU) 2026/1744 ("Digital Omnibus on AI") 24.7.2026'da OJ'de yayımlandı ve 27.7.2026'da yürürlüğe girdi. Annex III yüksek risk yükümlülükleri **2 Aralık 2027**'ye, Annex I (ürün mevzuatı) yükümlülükleri **2 Ağustos 2028**'e kaydı. [D]
3. **GDPR'ı değiştiren ayrı "Digital Omnibus" (COM(2025) 837) hâlâ müzakerede, kabul edilmedi.** [DY: birincil statü sayfası okunamadı. İkincil kaynaklara göre Konsey Ekim 2026'da müzakere pozisyonunu belirledi.]
4. **KVKK, Kasım 2025'te üretken YZ rehberi yayımladı.** Rehber; istem enjeksiyonu, jailbreak, model ters çevirme ve üyelik çıkarımına karşı teknik kontrolleri, red teaming'i ve log tutmayı **açıkça** iyi uygulama olarak sayıyor. Battal'ın Türkiye için en güçlü dayanağı budur. [D]
5. **Telekom için BTK'nın 2020 tarihli yönetmeliği** iki somut gereklilik getiriyor: erişim işlem kayıtlarının **2 yıl** saklanması ve trafik/konum verisinin **yurt dışına çıkarılmaması esası**. [D]
6. **OWASP Top 10 for Agentic Applications 2026 gerçekten var.** 9 Aralık 2025'te yayımlandı. Kodları ASI01–ASI10. [D]
7. **MITRE ATLAS veri sürümü 2026.10 (28.10.2026).** Prompt injection AML.T0051 (.000 Direct, .001 Indirect, .002 Triggered), jailbreak AML.T0054, RAG poisoning AML.T0070. Eski "AML.T0057 LLM Data Leakage" ve "AML.T0056" güncel veride **bulunmuyor**. [D]

---

## 1. Hukuki yükümlülükler (bağlayıcı, kapsama ve role bağlı)

### 1.1 EU AI Act — Regulation (EU) 2024/1689

**Kaynaklar:**
- Konsolide edilmemiş OJ metni: https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- HTML: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689
- Değiştiren tüzük: https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng

#### 1.1.1 Kimlik ve tarihler [D]

- OJ L serisi, 2024/1689, **12.7.2024**. Tüzük OJ'de yayımdan sonraki **20. günde** yürürlüğe girer (Art. 113). Bu hesapla yürürlük 1.8.2024'tür. [Ç: tarih hesaplaması bize ait, metin gün sayısını veriyor.]
- **Art. 113 (orijinal):**
  - Genel uygulama tarihi 2 Ağustos 2026.
  - (a) Chapter I–II (tanımlar, AI literacy, yasaklı uygulamalar): 2 Şubat 2025.
  - (b) Chapter III Section 4 (notifying authorities/notified bodies), **Chapter V (GPAI)**, Chapter VII (governance), Chapter XII (cezalar) ve Art. 78: **2 Ağustos 2025**. Art. 101 (GPAI sağlayıcılarına para cezası) bu tarihe dahil değildir.
  - (c) Art. 6(1) ve ilgili yükümlülükler: 2 Ağustos 2027.
- **Regulation (EU) 2026/1744 ile yapılan değişiklikler** (8.7.2026 tarihli; OJ 24.7.2026; yayımdan sonraki 3. gün yürürlük; https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202601744):
  - Art. 113(3)(c) yeniden yazıldı. Chapter III Section 1–3 (Art. 6(5) hariç):
    - (i) Art. 6(2) + **Annex III** yüksek risk sistemleri için **2 Aralık 2027**,
    - (ii) Art. 6(1) + **Annex I** için **2 Ağustos 2028**.
  - Art. 113(3)(a): Yeni Art. 5(1) (ba), (bb) ve Art. 5(1a), (1b) yasakları **2 Aralık 2026**'dan itibaren uygulanır. Bu yasaklar, rıza olmadan cinsel içerikli/mahrem sentetik görüntü üretimi ve 2011/93/EU kapsamındaki materyalle ilgilidir.
  - Yeni Art. 113(3)(d): Art. 102–110 **27 Temmuz 2026**'dan itibaren uygulanır.
  - Yeni Art. 111(4): 2 Ağustos 2026'dan önce piyasaya sürülmüş sentetik içerik üreten sistemlerin sağlayıcıları **Art. 50(2)**'ye **2 Aralık 2026**'ya kadar uymalıdır.
  - Art. 111(2): Kamu otoritelerince kullanılacak yüksek risk sistemlerinin sağlayıcı ve deployer'ları için son tarih **2 Ağustos 2030**.
  - Art. 4 (AI literacy) yumuşatıldı. Önceki "ensure" ifadesi "take measures to support" oldu. Belirli bir yetkinlik düzeyini garanti etme zorunluluğu yoktur.
  - **Yeni Art. 42(3):** Regulation (EU) 2024/2847 (Cyber Resilience Act) kapsamındaki yüksek risk sistemleri, CRA Art. 12(1) koşulları sağlanırsa **Art. 15'in siber güvenlik gerekliliklerine uygun sayılır**.
  - Art. 50(7) değişti: Commission, code of practice'i yetersiz bulursa implementing act çıkarabilir.
  - Yeni Art. 4a: Bias tespiti için özel nitelikli veri işlenmesine dair koşullar getirildi.
- **Değişmeyen tarihler** [Ç]: Art. 50'nin genel uygulama tarihi, Art. 113'teki genel tarih olan **2 Ağustos 2026**'dır. Omnibus Art. 113'ün ilk paragrafındaki genel tarihi değiştirmedi. Okunan metinde Art. 12, 14 ve 15'in içeriğinde bir değişiklik görülmedi.

#### 1.1.2 Kapsam, rol ve risk sınıfı — "otomatik uygulanmaz" [D + Ç]

- Yükümlülükler **role** göre ayrılır. **Provider** (Art. 3(3)), sistemi kendi adıyla piyasaya süren veya hizmete sokandır. **Deployer** (Art. 3(4)), sistemi kendi yetkisi altında kullanandır. Yükümlülükler ayrıca **sınıfa** göre değişir: yasaklı, yüksek risk, Art. 50 şeffaflık, GPAI modeli veya hiçbiri. Bir chatbot'un yüksek risk sayılması, Annex III'teki kullanım amacına (ör. kredi değerliliği, istihdam, temel kamu hizmetleri) bağlıdır. "LLM kullanıyoruz" demek tek başına sistemi yüksek risk yapmaz. [Ç]
- **Türkiye'deki kuruluşlar:** Art. 2(1)(c) uyarınca, üçüncü ülkede yerleşik provider/deployer'lar da **çıktının AB'de kullanılması** hâlinde kapsamdadır. [D]
- **Battal'ın kendisi:**
  - Art. 2(12), açık kaynak lisanslı YZ sistemlerini kapsam dışı tutar. İstisna şudur: sistem yüksek risk olarak ya da Art. 5 veya Art. 50 kapsamında piyasaya sürülürse kapsam dışı sayılmaz. [D]
  - Art. 25(4), yüksek risk sistemine bileşen sağlayan üçüncü tarafla yazılı sözleşme şartını getirir. Ancak bu şart, GPAI modeli dışındaki araç/bileşenleri **free and open-source lisansla kamuya açan** üçüncü taraflara uygulanmaz. [D]
  - Omnibus Art. 25(2)'yi değiştirdi. 25(4)'te değişiklik görülmedi. [Ç]
  - Battal'ı bir yüksek risk sistemine entegre eden kurum, o sistemin provider'ı olarak Art. 9–15 yükümlülüklerini **kendisi** taşır. Battal bu yükümlülüklerin bir kısmı için **teknik kanıt** üretebilir. [Ç]
  - Battal'ın ücretli/yönetilen hizmet olarak sunulmasının açık kaynak istisnasını etkileyip etkilemeyeceği bu çalışmada incelenmedi. [DY]

#### 1.1.3 Battal ile ilgili maddeler (yalnızca yüksek risk sistemleri için bağlayıcı) [D]

| Madde | Özü (kısaltılmış) | Battal ilgisi [Ç] |
|---|---|---|
| **Art. 12 Record-keeping** | (1) Yüksek risk sistemleri, yaşam döngüsü boyunca olayların (logs) **otomatik kaydına teknik olarak izin vermelidir**. (2) Kayıt, Art. 79(1) riskleri, post-market monitoring (Art. 72) ve Art. 26(5) izlemesi için ilgili olayları kapsamalıdır. | Guardrail kararlarının yapılandırılmış, değiştirilemez audit log'u |
| **Art. 19 / Art. 26(6)** | Provider ve deployer, kontrolündeki logları amaca uygun bir süre ve **en az 6 ay** saklar. Birlik veya ulusal hukuk (özellikle veri koruma) aksini öngörebilir. | Saklama süresi yapılandırılabilir olmalı. Süreyi kurum belirler. |
| **Art. 14 Human oversight** | Sistem, doğal kişilerce etkin şekilde gözetilebilecek biçimde (HMI araçları dahil) tasarlanmalıdır. Önlemler risk, otonomi düzeyi ve bağlamla orantılı olmalıdır. | Tool-call'lar için onay (HITL) kancaları, inceleme kuyruğu, kill-switch |
| **Art. 15 Accuracy, robustness, cybersecurity** | (3) Doğruluk seviyeleri ve metrikleri kullanım talimatında beyan edilir. (5) Sistem, zafiyetleri istismar ederek kullanımı, çıktıları veya performansı değiştirmeye çalışan yetkisiz üçüncü taraflara karşı dayanıklı olmalıdır. YZ'ye özgü önlemler, uygun olduğu yerde data poisoning, model poisoning, adversarial examples/model evasion, gizlilik saldırıları ve model kusurlarını önleme, tespit, müdahale ve kontrol etmeyi içerir. | Prompt injection, jailbreak ve evasion tespiti. Kendi dedektörleri için yayımlanmış doğruluk/FPR metrikleri. Not: madde metninde "prompt injection" terimi **geçmiyor**. Eşleme [Ç]'dir. |
| **Art. 50 Transparency** | (1) Doğal kişiyle doğrudan etkileşen sistemlerin provider'ı, kişinin YZ ile etkileştiğini bildirir. (2) Sentetik ses/görüntü/video/metin üreten sistemlerin provider'ı, çıktıları makine-okunur biçimde işaretler. (4) Deepfake deployer'ı ifşa eder. | Esasen provider/deployer yükümlülüğüdür. Battal en fazla bir "AI-generated" metadata alanı veya etiketleme kancası sağlayabilir. Etkinliği değerlendirilmedi. |
| **Art. 55(1)(a),(d)** | Sistemik riskli GPAI provider'ı adversarial testing yapar ve yeterli siber güvenlik sağlar. | Battal kullanıcılarının çoğu GPAI provider'ı değildir. Doğrudan ilgisi düşüktür. |

**Harmonised standard durumu:** Art. 15 siber güvenlik için CEN-CENELEC'in **prEN 18282** taslağı ikincil kaynaklarda geçiyor. OJ'de atıf yapılmış bir harmonised standard bulunduğu **doğrulanamadı**. [DY] Omnibus Art. 42(3)'teki CRA üzerinden uygunluk karinesi ise doğrulandı. [D]

#### 1.1.4 GDPR'ı değiştiren "Digital Omnibus" (COM(2025) 837) [DY]

Bu paket, AI Omnibus'tan (2026/1744) **ayrıdır**. İkincil kaynaklara göre Konsey Ekim 2026'da müzakere pozisyonunu belirledi, Parlamento pozisyonu ve trilog ise bekleniyor (ör. https://www.cuatrecasas.com/en/latam/intellectual-property/art/digital-omnibus-eu-council-establishes-position — ikincil). Birincil kaynak olarak EP Legislative Observatory 2025/0360(COD) kontrol edilmelidir. **Yürürlükte varsayılmamalı.**

### 1.2 KVKK — 6698 sayılı Kanun ve Kurul düzenlemeleri

**Kaynak (Kanun metni):** https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6698.pdf (RG 7.4.2016/29677) [D]

- **Art. 12 (Veri güvenliği)** [D]
  - (1) Veri sorumlusu; hukuka aykırı işlemeyi ve hukuka aykırı erişimi önlemek ve verilerin muhafazasını sağlamak için uygun güvenlik düzeyini temin eden "her türlü teknik ve idari tedbiri" almak zorundadır.
  - (2) Veri işleyenle birlikte **müştereken sorumludur**.
  - (5) Veri ihlalinde ilgiliye ve Kurula **"en kısa sürede"** bildirim yapılır.
  - Kurul'un 24.01.2019 tarihli ve **2019/10** sayılı kararı bu süreyi **72 saat** olarak yorumlar. Kaynak: https://www.kvkk.gov.tr/Icerik/5362/Veri-Ihlali-Bildirimi [D: KVKK sayfası arama özetinden. Karar tam metni okunmadı.]
- **Art. 9 (Yurt dışına aktarım)** 2.3.2024 tarihli ve 7499 sayılı Kanunla değişti [D]. Sıralama şöyle:
  1. (1) Yeterlilik kararı.
  2. (4) Yeterlilik kararı yoksa **uygun güvenceler**: (a) kamu kurumları arası anlaşma + Kurul izni, (b) bağlayıcı şirket kuralları, (c) **Kurul'un ilan ettiği standart sözleşme**, (ç) yazılı taahhütname + Kurul izni.
  3. (6) Bunlar da yoksa yalnızca **arızi** hâller.
  - Geçici Madde 3: Eski 9(1), 1/9/2024'e kadar yeni hâliyle birlikte uygulanmaya devam etti.
  - Standart sözleşmenin imzadan sonra **5 iş günü** içinde Kurum'a bildirilmesi: Kurum duyurusu https://www.kvkk.gov.tr/Icerik/8170/Yurt-Disina-Kisisel-Veri-Aktariminda-Kullanilacak-Standart-Sozlesmelerde-Dikkat-Edilmesi-Gereken-Hususlara-Iliskin-Kamuoyu-Duyurusu [D: arama özeti. Madde fıkra metni ayrıca okunmalı.]
- **Yurt Dışına Aktarım Yönetmeliği** — "Kişisel Verilerin Yurt Dışına Aktarılmasına İlişkin Usul ve Esaslar Hakkında Yönetmelik", RG **10.07.2024 / 32598**. [D: KVKK üretken YZ rehberi s. 47–48 bu künyeyi veriyor.]
- **Üretken YZ Rehberi** — "Üretken Yapay Zekâ ve Kişisel Verilerin Korunması Rehberi (15 Soruda)", Yayın No 113, **Kasım 2025** (sayfada 24.11.2025).
  - Sayfa: https://www.kvkk.gov.tr/Icerik/8547/uretken-yapay-zeka-ve-kisisel-verilerin-korunmasi-rehberi-15-soruda
  - PDF: https://www.kvkk.gov.tr/SharedFolderServer/CMSFiles/MTY5MjNmNmIwZWY3YTE.pdf [D]
  - **Soru 10:** Yurt dışında yerleşik sağlayıcılar üzerinden ÜYZ kullanılıp kişisel veri aktarılıyorsa, aktarım Art. 9'a ve Yönetmeliğe uygun olmalıdır. [D]
  - **Soru 13, güvenlik tedbirleri** ("örnek mahiyetinde"), metinden: [D]
    - privacy by design/default
    - **veri koruma etki değerlendirmesi** (iyi uygulama olarak; Kanunda genel bir DPIA zorunluluğu olarak değil)
    - mahremiyet artırıcı teknolojiler
    - *"…modeli ters çevirme saldırıları, **istem enjeksiyonu, jailbreak girişimleri** ve üyelik çıkarımı saldırıları gibi… zafiyetlere karşı teknik kontrollerin entegre edilmesi ve… düzenli olarak izlenip gözden geçirilmesi"*
    - red teaming
    - güvenilir veri kümeleri
    - düzenli risk değerlendirmesi
    - eğitim
    - yama yönetimi
    - MFA
    - **işlem kayıtları ve sistem günlüklerinin güvenli ve denetlenebilir biçimde saklanması**
  - Rehber, Kişisel Veri Güvenliği Rehberi'ne (Teknik ve İdari Tedbirler) atıf yapar: https://www.kvkk.gov.tr/SharedFolderServer/CMSFiles/7512d0d4-f345-41cb-bc5b-8d5cf125e3a1.pdf [D: link rehberden alındı. Rehberin içeriği bu çalışmada okunmadı.]
- **"İş Yerlerinde Üretken Yapay Zekâ Araçlarının Kullanımı"** (KVKK, 5.3.2026): "Gölge YZ" riskini ele alır, tamamen yasaklayıcı yaklaşım yerine yönlendirici politika önerir ve hassas veri girilmemesini tavsiye eder. Kaynak: https://www.kvkk.gov.tr/Icerik/8674/is-yerlerinde-uretken-yapay-zeka-araclarinin-kullanimi [D: kvkk.gov.tr arama özeti. Tam metin okunmadı.]
- **İdari para cezaları** (Art. 18): Tutarlar her yıl yeniden değerleme ile güncellendiği için burada rakam verilmedi.
- **Kritik çıkarım** [Ç]: Maskeleme ve takma ad (pseudonymisation) kullanmak veriyi **anonim** yapmaz. Maskelenmiş bir istem, bağlamı nedeniyle hâlâ kişisel veri içerebilir. Dolayısıyla Battal'ın maskelemesi yurt dışı aktarımı Art. 9 dışına **otomatik olarak çıkarmaz**. Bu değerlendirmeyi hukuk birimi yapmalıdır.

### 1.3 BTK — elektronik haberleşme sektörü (telekom işletmecileri)

- **"Elektronik Haberleşme Sektöründe Kişisel Verilerin İşlenmesi ve Gizliliğin Korunmasına İlişkin Yönetmelik"**, RG **04.12.2020 / 31324**, mevzuat no 38663. Yürürlük (m.18): yayımdan altı ay sonra.
  - Mevzuat: https://www.mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=7&MevzuatNo=38663&MevzuatTertip=5
  - BTK listesi: https://www.btk.gov.tr/yonetmelikler
  - Kapsam (m.2): İşletmecilerin elektronik haberleşme hizmeti kapsamında elde ettiği veriler.
  - **m.5(2):** *"Milli güvenlik gerekçesiyle trafik ve konum verilerinin yurt dışına çıkarılmaması esastır."* [D]
  - **m.6 Güvenlik:** [D]
    - (1) Kanun, 6698 ve ulusal/uluslararası standartlara uygun teknik ve idari tedbirler alınır.
    - (2) Asgari tedbirler: güvenlik politikaları, yetkisiz işleme ve ifşaya karşı koruma, yalnızca yetkili erişim.
    - **(4)** *"İşletmeciler, kişisel verilere ve ilişkili diğer sistemlere yapılan erişimlere ilişkin işlem kayıtlarını **iki yıl** saklamakla yükümlüdür."*
    - (5) İşletmeci, yetkilendirdiği tarafların ihlallerinden de sorumludur.
  - **m.7:** Risk ve kişisel veri ihlali bildirimi. İhlal hâlinde BTK'ya, KVKK'ya ve ilgili abonelere "en kısa sürede" bildirim yapılır. [D]
  - **İlgisi** [Ç]: Bir telekom operatörü, müşteri verisi (trafik/konum dahil) içeren istemleri yurt dışındaki bir LLM API'sine gönderirse m.5(2) ve KVKK m.9 birlikte değerlendirilmelidir. Battal'ın egress politikası ve maskelemesi yardımcı olur, ancak veri sınıflandırması ve hukuki karar operatöre aittir.
- **"Elektronik Haberleşme Sektöründe Şebeke ve Bilgi Güvenliği Yönetmeliği"** (RG 13.07.2014 / 29059): Varlığı ikincil kaynaklarda doğrulandı. BTK'nın güncel yönetmelik listesinde görünmüyor. **Yürürlük durumu doğrulanamadı.** [DY] Bu yönetmeliğe dayanarak madde numarası verilmemeli.
- 7571 sayılı Kanun kapsamında BTK'nın 2026 ikincil düzenleme taslakları var (https://www.btk.gov.tr/uploads/boarddecisions/...67-2026-web.pdf). İçeriği incelenmedi. [DY]

### 1.4 7545 sayılı Siber Güvenlik Kanunu [D: künye]

Kabul 12.3.2025, RG **19.3.2025 / 32846**. Kaynak: https://www.mevzuat.gov.tr/MevzuatMetin/1.5.7545.pdf

Kapsamı kamu kurumlarını ve siber uzayda faaliyet gösteren gerçek/tüzel kişileri içerir (m.1, amaç). YZ sistemlerine özgü maddeleri ve ikincil düzenlemeleri bu çalışmada incelenmedi. [DY] Regüle sektörler (telekom, bankacılık, kamu) için ayrıca değerlendirilmelidir.

### 1.5 Bu çalışmada doğrulanmayan sektörel düzenlemeler [DY]

Aşağıdakiler muhtemelen ilgilidir ancak birincil metinleri okunmadı. Madde atfı yapılmamalı:
- Bankacılık için BDDK'nın bilgi sistemleri yönetmeliği
- Kamu için Cumhurbaşkanlığı Dijital Dönüşüm Ofisi Bilgi ve İletişim Güvenliği Rehberi
- AB'deki benimseyenler için DORA (2022/2554), NIS2 ve GDPR Art. 25/32/35

---

## 2. Risk yönetimi çerçeveleri (gönüllü, bağlayıcı değil)

| Çerçeve | Durum | Kaynak |
|---|---|---|
| **NIST AI RMF 1.0** (NIST AI 100-1) | 26.01.2023. Sayfaya göre "White House AI Action Plan kapsamında revize ediliyor" (tarih yok). Fonksiyonlar: GOVERN, MAP, MEASURE, MANAGE. [D] | https://www.nist.gov/itl/ai-risk-management-framework |
| **NIST AI 600-1** Generative AI Profile | 26.07.2024 [D] | aynı sayfa |
| **AI RMF Profile on Trustworthy AI in Critical Infrastructure** | Concept note, 7.4.2026 [D: AI RMF sayfası] | aynı sayfa |
| **NIST IR 8596 (iprd)** Cybersecurity Framework Profile for AI ("Cyber AI Profile") | Preliminary draft 16.12.2025, yorum süresi 30.1.2026. Nihai sürümü doğrulanamadı. [D: CSRC arama özeti] | https://csrc.nist.gov/pubs/ir/8596/iprd |
| **CAISI RFI — Security Considerations for AI Agents** | Federal Register 8.1.2026 (2026-00206) [D: arama özeti] | https://www.nist.gov/news-events/news/2026/01/caisi-issues-request-information-about-securing-ai-agent-systems |
| **AI Agent Standards Initiative** (CAISI) | 17.2.2026. ITL'nin "AI Agent Identity and Authorization Concept Paper"ına atıf var. Somut çıktı listesi yok. [D] | https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure |

---

## 3. Saldırı taksonomileri ve tehdit listeleri

### 3.1 NIST AML taksonomisi

- **NIST AI 100-2 E2025**, "Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations", **Mart 2025** (final 24.3.2025). Predictive ve generative AI'ı kapsar. GenAI tarafında prompt injection, supply chain, misuse ve agent saldırıları yer alır. [D] https://csrc.nist.gov/pubs/ai/100/2/e2025/final
- **Yeni taslak: NIST SP 2400-102e2026 (ipd)**, aynı başlıkla. CSRC haberi 9.11.2026 tarihli, yorum süresi **18.12.2026**'da kapanıyor. Taslak "Agentic … Attacks Taxonomy" indeksi ekliyor. [D] https://csrc.nist.gov/News/2026/adversarial-machine-learning-taxonomy-2026-draft
  - Not: Sayfa "SI (Super Intelligence) systems" terimini kullanıyor. Bu alışılmadık bir terim; PDF'te ayrıca kontrol edilmeli. Taslak olduğu için normatif atıfta kullanılmamalı.

### 3.2 MITRE ATLAS [D]

**Kaynaklar:** https://atlas.mitre.org/ · veri: https://github.com/mitre-atlas/atlas-data (`dist/v6/ATLAS-2026.10.yaml`, release **2026.10**, 28.10.2026)

**Yapı:** 16 tactic, 221 technique/sub-technique, 44 mitigation. Tactic'ler:
AI Model Access (TA0000), AI Attack Adaptation (TA0001; eski adı "AI Attack Staging"), Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, Impact.

**Battal ile ilgili teknikler** (2026.10 verisinden; parantez içi tactic):

| ID | Ad | Tactic |
|---|---|---|
| AML.T0051 / .000 / .001 / .002 | LLM Prompt Injection / Direct / Indirect / Triggered | Execution |
| AML.T0054 | LLM Jailbreak | Defense Evasion, Privilege Escalation |
| AML.T0068 | LLM Prompt Obfuscation | — |
| AML.T0069.002 | Discover LLM System Information: System Prompt | — |
| AML.T0070 | RAG Poisoning | Persistence |
| AML.T0080 / .000 / .001 | AI Agent Context Poisoning / Memory / Thread | Persistence |
| AML.T0053 | AI Agent Tool Invocation | Execution, Privilege Escalation, Lateral Movement |
| AML.T0086 | Exfiltration via AI Agent Tool Invocation | Exfiltration |
| AML.T0101 | Data Destruction via AI Agent Tool Invocation | — |
| AML.T0110 (.000 Definition and Instructions, .001 Implementation, .002 Runtime Response) | AI Agent Tool Poisoning | Persistence |
| AML.T0099 | AI Agent Tool Data Poisoning | — |
| AML.T0024 | Exfiltration via AI Inference API | Exfiltration |
| AML.T0136 | Exfiltration via AI User Interface | Exfiltration |
| AML.T0077 | LLM Response Rendering | — |
| AML.T0020 | Training Data Poisoning (eski adı "Poison Training Data") | Persistence |
| AML.T0018.000 | Manipulate AI Model: Poison AI Model | — |
| AML.T0010 (.005 AI Agent Tool) | Supply Chain Compromise | — |
| AML.T0034 (.002 Agentic Resource Consumption) | Cost Harvesting | Impact |
| AML.T0029 | Denial of AI Service | — |

- **İlgili mitigation'lar:** AML.M0020 Generative AI Guardrails, M0024 AI Telemetry Logging and Monitoring, M0028 Enforce Access Controls for AI Agent Tools, M0029 Human In-the-Loop for AI Agent Actions, M0030 Restrict AI Agent Tool Invocation on Untrusted Data, M0031 Memory Hardening, M0033 Input and Output Validation for AI Agent Components, M0037 AI Agent Authority Expansion Controls, M0038 AI Agent Scope Drift Detection, M0004 Limit AI Service Query Volume and Rate, M0035 AI Red Team. M0020'nin "mitigates" ilişkisi T0051, T0054, T0070, T0080, T0086 ve T0110.000/.002'yi kapsıyor.
- **Uyarılar:**
  - 5.x sürümünde bulunan **AML.T0056 (Extract LLM System Prompt)** ve **AML.T0057 (LLM Data Leakage)** 2026.10 verisinde **yok**. Yeniden numaralandırılmış veya birleştirilmiş olabilirler; nedeni doğrulanamadı. [DY] Battal dokümantasyonu bu ID'leri kullanmamalı. Yerine T0069.002, T0024 ve T0136 kullanılabilir.
  - Yukarıdaki tablodaki "—" işaretleri, tactic ilişkisinin bu çalışmada çıkarılmadığını gösterir.
  - Battal, eşleme tablosunu release etiketiyle (ör. `ATLAS 2026.10`) sabitlemeli. ATLAS aylık sürüm yayımlıyor. [Ç]

### 3.3 OWASP Top 10 for LLM Applications 2025 [D]

https://genai.owasp.org/llm-top-10/ (sürüm sayfası 17.11.2024; https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)

| Kod | Ad |
|---|---|
| LLM01:2025 | Prompt Injection |
| LLM02:2025 | Sensitive Information Disclosure |
| LLM03:2025 | Supply Chain |
| LLM04:2025 | Data and Model Poisoning |
| LLM05:2025 | Improper Output Handling |
| LLM06:2025 | Excessive Agency |
| LLM07:2025 | System Prompt Leakage |
| LLM08:2025 | Vector and Embedding Weaknesses |
| LLM09:2025 | Misinformation |
| LLM10:2025 | Unbounded Consumption |

### 3.4 OWASP agentic çalışmaları [D]

- **OWASP Top 10 for Agentic Applications 2026:** 9.12.2025'te yayımlandı. PDF kapağında "Version 2026, December 2025" yazıyor. https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

| Kod | Ad |
|---|---|
| ASI01 | Agent Goal Hijack |
| ASI02 | Tool Misuse & Exploitation |
| ASI03 | Identity & Privilege Abuse |
| ASI04 | Agentic Supply Chain Vulnerabilities |
| ASI05 | Unexpected Code Execution |
| ASI06 | Memory & Context Poisoning |
| ASI07 | Insecure Inter-Agent Communication |
| ASI08 | Cascading Failures |
| ASI09 | Human-Agent Trust Exploitation |
| ASI10 | Rogue Agents |

- **Agentic AI – Threats and Mitigations:** v1.0, 17.2.2025. Aynı indirme bağlantısı şu anda **v1.1 (Aralık 2025)** veriyor. https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/
  - Tehditler: T1 Memory Poisoning, T2 Tool Misuse, T3 Privilege Compromise, T4 Resource Overload, T5 Cascading Hallucination Attacks, T6 Intent Breaking & Goal Manipulation, T7 Misaligned & Deceptive Behavior, T8 Repudiation & Untraceability, T9 Identity Spoofing & Impersonation, T10 Overwhelming Human-in-the-Loop, T11 Unexpected RCE and Code Attacks, T12 Agent Communication Poisoning, T13 Rogue Agents in Multi-Agent Systems, T14 Human Attacks on Multi-Agent Systems, T15 Human Manipulation, T16 Insecure Inter-Agent Protocol Abuse, T17 Supply Chain Compromise.
  - ASI PDF'indeki eşlemeler: ASI02→T2, ASI03→T3, ASI04→T17, ASI05→T11, ASI06→T1.

---

## 4. Eşleme tablosu: gereksinim veya tehdit → Battal kontrolü

**"Kim" sütunu:**
- **B:** Battal teknik olarak destekleyebilir (kontrol + kanıt).
- **B/K:** Battal kısmen destekler, kurum tamamlamalı.
- **K:** Yalnızca kurum yapabilir (yönetişim, hukuki değerlendirme, DPIA vb.).

**Uygulama noktaları:** input · output · retrieval · tool-call · tool-result · policy · audit

**Tablodaki tüm "Battal kontrolü" hücreleri [Ç]'dir.** Bunlar tasarım önerisidir; mevzuat bu kontrolleri adıyla istemez.

| # | Gereksinim / tehdit (kaynak) | Teknik kontrol (Battal) | Uygulama noktası | Doğrulama testi | Denetim kanıtı | Kalan risk | Kim |
|---|---|---|---|---|---|---|---|
| 1 | Doğrudan prompt injection — LLM01:2025; AML.T0051.000; ASI01; KVKK ÜYZ Rehberi S.13 ("istem enjeksiyonu"); AI Act Art. 15(5) yalnızca yüksek risk için [Ç] | TR+EN sınıflandırıcı + kural/heuristik katmanı; risk skoru; policy'ye göre block/flag/sanitize | input | TR/EN etiketli saldırı + benign korpusta TPR/FPR; yeni sürümde regresyon; adaptif red-team turu | Eval raporu (korpus hash, model sürümü, eşik); karar logu | Yeni ve adaptif saldırılar; %100 tespit yok; false positive iş etkisi | B (kurum eşik ve risk kabulünü yapar) |
| 2 | Dolaylı prompt injection (RAG, web, e-posta, dosya) — LLM01; AML.T0051.001; AML.T0070; ASI01, ASI06; ATLAS M0030 | Retrieval chunk'larının ve tool çıktılarının taranması; kaynak/güven etiketi; güvenilmeyen içerikte tool-call kısıtı (M0030 benzeri) | retrieval, tool-result, policy | İçine talimat gömülmüş belge setiyle uçtan uca test; "untrusted → tool-call" engelleme testi | Chunk başına tarama kararı + kaynak ID'si içeren log | Talimat/veri ayrımı LLM'de çözülmüş değil; semantik olarak masum görünen saldırılar | B/K |
| 3 | Jailbreak — AML.T0054; LLM01 | Jailbreak sınıflandırıcı; çok turlu konuşma bağlamı analizi; output policy kontrolü | input, output | Bilinen jailbreak aileleri + TR çevirileri; çok turlu senaryolar | Eval raporu; block oranı dashboard'u | Model hizalamasına bağlı kalan kısım; yeni teknikler | B |
| 4 | Gizleme/obfuscation (homoglyph, Türkçe karakter oyunları, base64, leetspeak) — AML.T0068 | Unicode normalizasyonu (NFKC, confusables), decode denemeleri, TR'ye özgü (ı/İ, ş/s) normalizasyon | input, retrieval, tool-result | Mutasyon tabanlı fuzz testi (aynı saldırının N varyantı) | Fuzz sonuç raporu | Sınırsız kodlama uzayı | B |
| 5 | İstemde kişisel veri (TCKN, IBAN, telefon, e-posta, adres) — LLM02:2025; KVKK m.4 ölçülülük [Ç], m.12; BTK Yön. m.6 | PII tespiti + checksum doğrulama (TCKN algoritması, IBAN mod-97); maskeleme veya tokenizasyon; geri dönüştürme (reversible vault) opsiyonel | input, output, audit | Sentetik TR PII korpusunda precision/recall; checksum'lı ve checksum'sız negatif örnekler; log'da ham PII bulunmadığını doğrulayan test | PII tespit metrikleri; maskeleme politikası sürümü; örneklem log incelemesi | Serbest metindeki dolaylı tanımlayıcılar (isim + şehir + meslek); maskeleme ≠ anonimleştirme | B/K |
| 6 | Yurt dışına aktarım (yabancı LLM API'si) — KVKK m.9 + Yönetmelik (RG 10.07.2024/32598); ÜYZ Rehberi S.10 | Egress politikası: sağlayıcı/bölge allowlist'i; PII varsa maskele veya engelle; "transfer" olayının audit'e yazılması | policy, input, audit | Policy birim testleri (PII + yabancı uç nokta → block/mask); konfigürasyon drift testi | Policy-as-code sürüm geçmişi; egress logları | Hukuki dayanak (yeterlilik / standart sözleşme + 5 iş günü bildirimi) teknikle sağlanamaz | **K** (Battal yalnızca uygulamayı zorlar ve kanıt üretir) |
| 7 | Telekom trafik/konum verisi — BTK Yön. m.5(2) | Veri sınıfı etiketine göre yurt dışı egress'i engelleme; konum/MSISDN/IMSI desen dedektörleri [Ç: tespit güvenilirliği doğrulanmadı] | policy, input | Etiketli test verisiyle engelleme testi | Egress engelleme logları | Desenle yakalanamayan trafik/konum verisi; veri sınıflandırması operatöre ait | B/K |
| 8 | System prompt sızıntısı — LLM07:2025; AML.T0069.002 | Çıktıda canary/fingerprint tespiti; system prompt'a sır koymama rehberi | output | Canary sızdırma testleri | Tespit logları | Parafraz edilmiş sızıntılar; asıl çözüm sırları prompt'a koymamaktır | B/K |
| 9 | Güvensiz çıktı işleme / render ile exfiltration — LLM05:2025; AML.T0077; AML.T0136 | Markdown/HTML/URL sanitizasyonu; harici görsel/link allowlist'i; çıktıda kod/SQL tespiti ve işaretleme | output | Markdown görsel exfil PoC'leri; XSS payload testleri | Sanitizasyon karar logu | Downstream uygulamanın çıktıyı nasıl kullandığı (ör. SQL'e verilmesi) Battal dışında | B/K |
| 10 | Aşırı yetki / tool misuse — LLM06:2025; ASI02; AML.T0053, T0086, T0101; ATLAS M0028, M0029, M0037 | Tool-call yetkilendirme: allowlist, argüman şeması doğrulaması, en az yetki, oran/limit, yüksek etkili eylemler için HITL onayı | tool-call, policy, audit | Yetkisiz tool/argüman denemeleri; HITL bypass testi; injection → tool-call zinciri | Tool-call karar logu (kim, ne, hangi policy, onaylayan) | Yetkili tool'un meşru argümanla kötüye kullanımı; onay yorgunluğu (OWASP T10) | B/K |
| 11 | Kimlik ve yetki istismarı — ASI03; OWASP T3, T9 | Ajan başına kimlik; scoped/kısa ömürlü token; kullanıcı yetkisinin aşılmaması (delegation check) | tool-call, policy | Yetki yükseltme senaryoları; token kapsam testleri | Kimlik/policy eşleme kayıtları | IAM tasarımı kuruma ait; NIST ajan kimlik çalışması henüz concept paper aşamasında | B/K |
| 12 | Tool tanımı veya tool yanıtı zehirleme (MCP vb.) — ASI04; AML.T0110 (.000/.002), T0099, T0010.005 | Tool tanım manifestinin pinlenmesi/hash'lenmesi; tanım değişikliği uyarısı; tool-result taraması | tool-result, policy | "Rug pull" (tanım değişikliği) simülasyonu; zehirli yanıt testleri | Manifest hash geçmişi; tarama logu | Tool'un kendi implementasyonundaki kötü niyet (T0110.001) | B/K |
| 13 | Bellek ve bağlam zehirleme — ASI06; AML.T0080; OWASP T1; ATLAS M0031 | Belleğe yazma öncesi tarama; kaynak etiketi; TTL/izolasyon (kullanıcı/tenant bazında) | retrieval, tool-result, policy | Kalıcı enjeksiyon senaryosu (oturum A'da yaz, oturum B'de tetikle) | Bellek yazma logları | Ajan çerçevesinin bellek mimarisi Battal dışında olabilir | B/K |
| 14 | RAG / vektör zafiyetleri — LLM08:2025; AML.T0070 | Retrieval'da tenant/ACL filtresinin doğrulanması; kaynak allowlist'i; chunk taraması | retrieval | Çapraz tenant sızıntı testi; zehirli doküman testi | Retrieval karar logu | İndeksleme hattının güvenliği (ingest tarafı) | B/K |
| 15 | Sınırsız tüketim / maliyet — LLM10:2025; AML.T0034 (.002), T0029; ATLAS M0004 | Rate limit; token/istek bütçesi; ajan döngü sayacı; circuit breaker | input, tool-call, policy | Yük testi; sonsuz döngü senaryosu | Kota olay logları | Dağıtık kötüye kullanım; LLM sağlayıcı tarafı limitleri | B |
| 16 | İzlenebilirlik ve log — AI Act Art. 12, 19, 26(6) (yüksek risk); BTK Yön. m.6(4) (2 yıl erişim kaydı); ÜYZ Rehberi S.13; OWASP T8; ATLAS M0024 | Yapılandırılmış, PII'si maskelenmiş, değişikliğe karşı korumalı (hash-chain/WORM'a aktarım) audit log; policy/model sürüm damgası; SIEM'e aktarım | audit | Log bütünlük doğrulaması; örnek bir olaydan geriye iz sürme tatbikatı; log'da ham PII taraması | Log şeması; saklama konfigürasyonu; bütünlük doğrulama çıktısı | Saklama süresi çatışması (≥6 ay / 2 yıl / KVKK'nın saklama ilkesi): **kurum karar verir**. Log'un kendisi kişisel veri içerir. | B/K |
| 17 | İnsan gözetimi — AI Act Art. 14 (yüksek risk); ASI09; ATLAS M0029 | HITL onay kancası; inceleme kuyruğu; override; kill-switch; kararın gerekçesinin gösterilmesi | tool-call, output, policy | Onay akışı testi; kill-switch tatbikatı | Onay/override kayıtları | Yetkin ve yetkili kişi atamak, eğitim vermek ve otomasyon önyargısıyla mücadele kurumun işidir | B/K |
| 18 | Doğruluk/dayanıklılık beyanı — AI Act Art. 15(3) | Battal dedektörleri için sürüm başına yayımlanan doğruluk/FPR metrikleri ve bilinen sınırlamalar ("model card") | policy, audit | Yeniden üretilebilir benchmark | Sürümlü eval raporu | Kurumun kendi verisindeki performans farklı olabilir; yerel doğrulama gerekir | B/K |
| 19 | Battal'ın kendi tedarik zinciri — LLM03:2025; AML.T0010; ASI04 | İmzalı release'ler, SBOM, model artefakt hash'leri, bağımlılık taraması | (build/deploy) | İmza/hash doğrulama CI adımı | SBOM, imza, CVE tarama raporu | Upstream model/kütüphane zafiyetleri | B |
| 20 | Battal sınıflandırıcısının zehirlenmesi — LLM04:2025; AML.T0020, T0018.000; ATLAS M0025 | Eğitim verisi provenance'ı; eval regresyon kapısı; topluluk katkılarının incelenmesi | (eğitim hattı) | Arka kapı/tetikleyici testleri; holdout regresyonu | Dataset kartı + hash; eval geçmişi | Açık kaynak katkı modelinde hedefli zehirleme | B |
| 21 | Yanlış bilgi / halüsinasyon — LLM09:2025 | (Opsiyonel) grounding/citation tutarlılık kontrolü; yüksek riskli alanlarda uyarı etiketi | output | Grounding test seti | Uyarı logları | Battal'ın kapsamı sınırlı; doğruluk sorumluluğu uygulama sahibine aittir | K (B sınırlı) |
| 22 | Şeffaflık — AI Act Art. 50(1), 50(2) | Çıktıya "AI-generated" metadata alanı veya etiket kancası [Ç]; kullanıcı bilgilendirme metni Battal'ın işi değil | output | Metadata'nın varlığını kontrol eden test | Konfigürasyon | 50(2)'nin "machine-readable marking" gereği için metin metadata'sının yeterliliği **doğrulanmadı** | K (B sınırlı) |
| 23 | İhlal bildirimi — KVKK m.12(5) + Kurul 2019/10 (72 saat); BTK Yön. m.7 | Kritik olaylar (toplu PII sızıntısı denemesi, exfil tespiti) için alarm ve SIEM/webhook | audit | Alarm tatbikatı | Alarm kayıtları + zaman damgaları | İhlal olup olmadığına karar vermek ve bildirmek tamamen kuruma aittir | **K** |
| 24 | Risk değerlendirmesi / DPIA — ÜYZ Rehberi S.13 (iyi uygulama); NIST AI RMF MAP/MEASURE | Battal'ın tehdit modeli dokümanı ve kontrol kataloğu girdi olarak verilebilir | — | — | DPIA dokümanı (kurum) | — | **K** |
| 25 | AI literacy — AI Act Art. 4 (2026/1744 ile değişik) | — | — | — | Eğitim kayıtları | — | **K** |
| 26 | Rol ve risk sınıflandırması — AI Act Art. 3, 6, Annex III | — | — | — | Hukuki değerlendirme notu | Yanlış sınıflandırma | **K** |
| 27 | Ajanlar arası iletişim — ASI07; OWASP T12, T16 | Ajan-ajan mesaj sınırında policy kontrolü, mesaj imzası/doğrulaması (yol haritası) | tool-call, tool-result | Sahte ajan mesajı testi | Mesaj doğrulama logları | Protokol (A2A/MCP) güvenlik olgunluğu | B/K (gelecek) |
| 28 | Zincirleme hatalar / kontrolden çıkan ajan — ASI08, ASI10; ATLAS M0038 | Anomali ve scope-drift tespiti, devre kesici, kill-switch | policy, tool-call, audit | Kaos/arıza enjeksiyonu tatbikatı | Olay zaman çizelgesi | Emergent davranış; tespit gecikmesi | B/K |

---

## 5. Battal için ürün çıkarımları [Ç]

1. **Kanıt üretimi birinci sınıf özellik olmalı.** Her karar logunda şunlar bulunmalı: istek ID, uygulama noktası, dedektör + sürüm, skor, eşik, policy sürümü, eylem, maskelenmiş özet. Bu, AI Act Art. 12, BTK m.6(4) ve KVKK rehberindeki "denetlenebilir kayıt" beklentilerine **katkı** sağlar.
2. **Saklama süresi parametrik olmalı, varsayılan "hukuki tavsiye" gibi sunulmamalı.** Örneğin: "BTK m.6(4) erişim kayıtları için 2 yıl öngörür; AI Act Art. 26(6) yüksek risk için en az 6 ay öngörür; kararı kurumunuz verir."
3. **Eşleme dosyaları sürümlenmeli:** `mappings/owasp-llm-2025.yaml`, `owasp-asi-2026.yaml`, `atlas-2026.10.yaml`. ATLAS ID'leri değişebiliyor (bkz. T0056/T0057).
4. **Türkçe değerlendirme korpusu ve yayımlanmış metrikler**, KVKK rehberindeki "teknik kontrollerin düzenli izlenmesi" beklentisine ve Art. 15(3)'e katkı sağlar.
5. **Dokümantasyon dili:** "KVKK/AI Act uyumlu" ifadesi **kullanılmamalı**. Doğru ifade şudur: "şu gerekliliklere yönelik teknik kontroller ve kanıt sağlar; uyum değerlendirmesi kullanıcı kuruma aittir."

---

## 6. Belirsizlikler ve doğrulanamayanlar

- GDPR'ı değiştiren Digital Omnibus (COM(2025) 837) güncel aşaması: birincil kaynak okunmadı. [DY]
- Art. 15 için harmonised standard (prEN 18282) durumu: yalnızca ikincil kaynaklar var. [DY]
- BTK 2014 Şebeke ve Bilgi Güvenliği Yönetmeliği'nin yürürlük durumu ve 7571 sayılı Kanun kapsamındaki 2026 taslakları. [DY]
- 7545 sayılı Kanun'un YZ'ye uygulanabilir somut maddeleri ve ikincil düzenlemeleri incelenmedi. [DY]
- KVKK 2019/10 kararının tam metni ve 2025/2451 sayılı karar (ihlal ilanlarının yayında kalma süresi) birincil metinden okunmadı. [DY]
- KVKK Kişisel Veri Güvenliği Rehberi (Teknik ve İdari Tedbirler) içeriği okunmadı. Yalnızca linki doğrulandı.
- ATLAS T0056/T0057'nin kaldırılma veya yeniden numaralandırılma nedeni. [DY]
- NIST SP 2400-102e2026 taslağındaki "SI" terminolojisi ve ajan taksonomisinin içeriği. [DY]
- Açık kaynak istisnasının (Art. 2(12)) Battal'ın ücretli/yönetilen sunumuna etkisi. [DY]
- BDDK, kamu (DDO rehberi), DORA ve NIS2 bu çalışmada doğrulanmadı.
