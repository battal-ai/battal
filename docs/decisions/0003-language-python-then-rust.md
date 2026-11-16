# ADR 0003: Dil seçimi — önce Python, sonra Rust çekirdek

- Durum: kabul edildi
- Tarih: 2026-11-16

## Bağlam

Rust, deterministik ve yoğun string işleyen kodda (Unicode normalizasyonu, regex, checksum, policy
değerlendirmesi) belirgin hız ve bellek kazancı sağlar. Model inference'ta ise kazanç sınırlıdır,
çünkü ONNX Runtime zaten C++ ile çalışır ve dilin etkisi azdır. Geliştiricinin Rust deneyimi
yoktur ve projeye haftada yaklaşık 8–10 saat ayrılmaktadır.

LiteLLM de aynı yolu izlemiştir. Önce Python'la benimsenmiş, sonra yalnızca hot path'i Rust'a
taşımıştır. Bu geçişte config ve API değişmemiş, Rust motoru model bazında açılıp kapatılabilir
hâle getirilmiş ve en sık kullanılan istek türleri önce taşınmıştır.
([LiteLLM Rust gateway](https://docs.litellm.ai/docs/proxy/rust_gateway.md),
[rust migration rerouted](https://docs.litellm.ai/blog/rust-migration-rerouted))

## Kararlar

1. **Aşama 1 (MVP): Python.** Çekirdek kütüphane, FastAPI sunucu, ONNX inference, SDK, LiteLLM
   adapter, eğitim ve benchmark Python'da yazılır.
2. **Rust'a hazır tasarım.** Deterministik çekirdek (normalizasyon, PII tespiti ve checksum, policy
   değerlendirmesi) saf fonksiyonlarla yazılır: global state yoktur, girdi ve çıktı açıkça
   tanımlıdır, I/O içermez.
3. **Dilden bağımsız test vektörleri.** Deterministik çekirdeğin davranışı, ilk günden JSON fixture
   olarak tanımlanır (girdi → beklenen çıktı). Python implementasyonu bu vektörlerle test edilir.
4. **Aşama 2 (MVP'den sonra): Rust `battal-core`.** Deterministik çekirdek Rust'a taşınır ve
   PyO3/maturin ile Python'a bağlanır. Python API değişmez. Rust motoru, test vektörlerinin
   tamamını geçmeden varsayılan motor olmaz. Geçiş süresince iki motor yan yana çalışır ve config
   ile seçilir.
5. **Aşama 3 (gerekirse): Rust sunucu.** Ölçümler sunucu katmanının darboğaz olduğunu gösterirse,
   ikinci bir motor olarak Rust sunucu (axum + `ort`) eklenir. Evaluation API ve config değişmez.

## Elenen alternatifler

- **İlk günden Rust:** Rust'ı öğrenmek ile ürünü bulmak aynı anda yapılırsa MVP önemli ölçüde
  gecikir. Ayrıca darboğaz ölçülmeden yapılan optimizasyon, model inference baskınsa boşa gider.
- **Yalnızca Python:** Yüksek throughput'ta deterministik katmanın hızını ve GIL'in getirdiği
  eşzamanlılık sınırlarını kalıcı olarak kabul etmek anlamına gelir.

## Sonuçlar

- Python implementasyonu, Rust geçişinde referans implementasyon (oracle) görevi görür.
- Test vektörleri, iki motorun aynı davrandığının kanıtıdır. Güvenlik ürününde, yeni yazılan bir
  implementasyonun sessizce farklı davranması kabul edilemez.
- Rust kodu güvenlik açısından kritik olduğu için, yazan kim olursa olsun bakımcı tarafından
  okunup anlaşılmadan merge edilmez.
