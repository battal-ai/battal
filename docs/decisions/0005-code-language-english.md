# ADR 0005: Kod ve kod dokümantasyonu İngilizce

- Durum: kabul edildi
- Tarih: 2026-11-17
- Değiştirdiği karar: [ADR 0001](0001-product-shape-and-licensing.md), karar 8 (kod yorumları)

## Bağlam

ADR 0001, dokümantasyonun ve kod yorumlarının Türkçe yazılmasını öngörüyordu. Kod yazımına
geçerken iki durum öne çıktı. Birincisi, kod büyük ölçüde AI destekli yazılacak ve İngilizce
docstring ile yorumlar hem daha tutarlı üretiliyor hem de koddaki İngilizce isimlerle aynı dilde
okunuyor. İkincisi, Python ve Rust ekosistemlerindeki araçlar, kütüphane dokümanları ve olası
katkıcıların büyük kısmı kod düzeyinde İngilizce çalışıyor. Öte yandan Battal'ın okurları ve
kullanıcıları için Türkçe öncelikli olması ürünün kimliğinin parçası.

## Kararlar

1. **Kod İngilizcedir.** İsimler, yorumlar, docstring'ler, tip açıklamaları, kod içi `README`
   dosyaları, log mesajları, CLI yardım metinleri ve testlerin adları İngilizce yazılır.
2. **Okura yönelik dokümantasyon Türkçedir.** Docs sitesi, kök `README`, ADR'ler, spec'ler
   (test vektörlerinin `description` alanları dahil), mimari belgesi, sözlük, araştırma raporları
   ve issue'lar Türkçe kalır; teknik terimler İngilizce bırakılır.
3. **Büyük modüller için Türkçe anlatım.** Bir modül, kullanıcının ya da katkıcının okuması
   gereken kadar büyükse, Türkçe anlatımı docstring'e değil docs sitesine yazılır (örneğin
   `docs/mimari.md` ya da modüle ayrılmış bir sayfa) ve koda link verilir. Kodun içinde Türkçe
   ile İngilizce aynı açıklamayı tekrar etmez.
4. **Son kullanıcıya gösterilen mesajlar Türkçedir.** Battal'ın bir karar sonucunda son
   kullanıcıya döndürdüğü metinler (örneğin `rationale.message_tr`) Türkçe kalır.

## Elenen alternatifler

- **Kod yorumlarının da Türkçe olması (ADR 0001'deki hâli):** Aynı dosyada İngilizce isimler ile
  Türkçe açıklamalar karışır; AI destekli yazımda tutarlılık düşer ve uluslararası katkıcılar
  kodu okuyamaz.
- **Her şeyin İngilizce olması:** Türkçe öncelikli ürün kimliğiyle ve Türkçe okur kitlesiyle
  çelişir.

## Sonuçlar

- Kod ile spec arasında dil geçişi olur: spec Türkçe, ona karşılık gelen kod İngilizcedir.
  Gereklilik kimlikleri (`S3-PII-012`) ve [sözlükteki](../sozluk.md) İngilizce terimler bu iki
  dünyayı bağlar; koddaki isimler sözlük terimleriyle aynı olmalıdır.
- `CONTRIBUTING.md` ve `CLAUDE.md` bu kurala göre güncellenir.
