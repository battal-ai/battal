# Battal: proje kuralları

Battal, Türkçe öncelikli, self-hosted bir AI güvenlik servisi ve SDK'dır. Ürünün özeti:
`docs/urun.md`.

## Dil

Ayrıntı: ADR 0005.

- **Kod İngilizcedir:** isimler, yorumlar, docstring'ler, kod içi README'ler, log mesajları, CLI
  yardım metinleri, test adları.
- **Okura yönelik her şey Türkçedir:** docs sitesi, kök README, ADR'ler, spec'ler (vektör
  `description` alanları dahil), mimari, sözlük, raporlar, issue'lar. Teknik terimler (guardrail,
  policy, checkpoint, tool call…) İngilizce kalır; zorla Türkçeleştirilmez.
- **Büyük modüller:** okunması gereken kadar büyük bir modülün Türkçe anlatımı docstring'e değil
  docs sitesine yazılır ve koda link verilir.
- Son kullanıcıya dönen karar mesajları (`rationale.message_tr`) Türkçedir.
- `LICENSE` (resmî Apache metni) ve `NOTICE` İngilizce kalır.
- Terimler `docs/sozluk.md`'deki anlamlarıyla kullanılır. Sözlükle çelişen bir kullanım fark
  edilirse düzeltilir ya da sözlük güncellenir.

## Belge türleri

| Tür | Yer | Rolü | Değişir mi? |
|---|---|---|---|
| Araştırma raporu | `docs/research/` | Ne var, neyi neden seçtik | Hayır, tarihî belgedir |
| ADR | `docs/decisions/` | Bir kararın gerekçesi | Hayır, yeni ADR ile geçersiz kılınır |
| Spec | `docs/spec/`, `schemas/`, `testvectors/` | Sistemin tam davranışı | Evet, sürümlenir |
| Mimari | `docs/mimari.md` | Bileşenler, modüller, bağımlılık kuralları | Evet, kodla birlikte |
| Sözlük | `docs/sozluk.md` | Terimlerin tek anlamı | Evet |
| Ürün özeti | `docs/urun.md` | Kararların okunabilir özeti | Evet; ADR ile çelişirse ADR geçerlidir |

- **ADR yalnızca şu üç koşul birlikte sağlanınca yazılır:** geri alması pahalı, bağlamı bilmeyen
  okuyana şaşırtıcı, gerçek alternatifler arasından seçim. Diğer kararlar ilgili spec'e ya da
  `docs/mimari.md`'ye yazılır.
- ADR formatı mevcut ADR'leri izler: Durum/Tarih, Bağlam, Kararlar, Elenen alternatifler,
  Sonuçlar. Numaralar sırayla devam eder.

## Spec'ten koda

- Kod spec'ten yazılır. Spec süreci ve formatı `battal-spec` skill'indedir; spec listesi
  `docs/spec/index.md`'dedir.
- Kod ile spec çelişirse ya kodda bug vardır ya da önce spec değiştirilir.
- Deterministik çekirdek saf fonksiyonlardan oluşur: global state yok, I/O yok (ADR 0003).
  Modül sınırları ve bağımlılık yönü `docs/mimari.md`'dedir.
- Testler önce yazılır; spec'in test vektörleri ilk kırmızı testlerdir.

## Skill'ler

Projede kullanılan skill'ler `.claude/skills/` altındadır (liste: `.claude/skills/README.md`).
Üçüncü taraf skill'lerin varsayılanları (dizinler, formatlar, dil) bu dosyadaki kurallarla
çelişirse bu dosya geçerlidir. Yeni bir skill eklenmeden önce baştan sona okunur, bir commit'e
pinlenir ve `LICENSE` ile `SOURCE.md` dosyalarıyla birlikte kopyalanır.

## Açık kaynak sınırı

- Kodun tamamı Apache-2.0'dır. İleride ücretli sürüme ayrılacak özellikler (multi-tenant control
  plane, SSO/RBAC, onay akışları) açık koda eklenmez; yalnızca extension point bırakılır
  (ADR 0001).
- Public dosyalarda herhangi bir kurum adı ya da gerçek kişisel veri yer almaz. Örneklerde
  kullanılan TCKN, IBAN gibi değerler checksum'ı geçerli, sentetik test numaralarıdır.

## Commit

- Commit ve push yalnızca bakımcının onayıyla yapılır.
- Commit mesajları İngilizce ve kısa olur; spec'ler ve ADR'ler kendi commit'leriyle girer.
