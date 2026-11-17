# ADR 0006: PII tanıyıcıları çekirdekte, Presidio'suz

- Durum: kabul edildi
- Tarih: 2026-11-17
- Değiştirdiği karar: Araştırma raporu §2.1 ve Karar bölümündeki "Presidio (yalnızca orkestratör)"
  seçimi

## Bağlam

Araştırma raporu PII için Presidio'yu orkestratör olarak seçmiş, Türkçe tanıyıcıların Presidio
registry'sine kaydedilmesini öngörmüştü (PBI 3.2). S2 ve S3 yazılırken üç durum ortaya çıktı:

- Presidio'nun `AnalyzerEngine`'i bir NLP motoru verilmezse varsayılan olarak bir spaCy modeli
  oluşturup yüklüyor. Yalnızca regex tanıyıcılarıyla çalıştırmanın resmî olarak desteklenen bir
  yolu doğrulanamadı.
- Görünümler ve offset haritası (S2) Presidio'nun dışında üretiliyor; Presidio bu akışa bir şey
  katmadan bir katman ekliyor.
- Deterministik çekirdek Rust'a taşınacak (ADR 0003). Presidio Python'a bağlı olduğu için iki
  motorun aynı vektörlerle aynı davranması ancak tanıyıcılar Battal'ın kendi kodu olursa mümkün.

## Kararlar

1. PII tanıyıcıları ve checksum'lar `battal.core.pii` içinde saf fonksiyonlar olarak yazılır;
   davranışları S3'te tanımlanır.
2. Presidio Battal'ın bir bağımlılığı değildir.
3. Presidio kullanan kurumlar için, Battal tanıyıcılarını Presidio `PatternRecognizer`'ı olarak
   dışa aktaran isteğe bağlı bir adapter yazılır (MVP sonrası, E17).
4. Telefon numarası desenleri çalışma anında `phonenumbers` kütüphanesinden okunmaz; `phonenumbers`
   9.0.43'ün TR metadata'sından alınıp S3'e sabit olarak yazılır.

## Elenen alternatifler

- **Presidio'yu orkestratör olarak tutmak:** spaCy modeli ya da sahte bir NLP motoru gerektirir,
  çekirdeğe Rust'ta karşılığı olmayan bir bağımlılık ekler.
- **Telefon için çalışma anında `phonenumbers`:** Rust'taki karşılığı farklı bir metadata sürümü
  kullanır; aynı vektörde iki motor farklı sonuç verebilir.

## Sonuçlar

- Rapordaki Presidio karşılaştırması (benchmark'ta "Presidio varsayılan ayarları" ile kıyas) geçerli
  kalır; Presidio artık bir baseline'dır, bileşen değildir.
- PBI 3.2'deki "Presidio registry'ye kaydedilir" maddesi E17'deki adapter'a taşınır.
- Telefon desenleri yeni bir `phonenumbers` sürümüne göre güncellenirken S3'ün sürümü ve vektörleri
  birlikte değişir.
