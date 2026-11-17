# Battal'a katkı

İlginiz için teşekkürler. Battal erken araştırma ve tasarım aşamasındadır.

## Contributor License Agreement (CLA)

Kod katkıları için Contributor License Agreement (CLA) imzalanması gerekecek. CLA henüz hazır
olmadığı için **kod içeren pull request'ler şimdilik merge edilemez**. Issue, tartışma, bug raporu
ve tasarım geri bildirimi memnuniyetle karşılanır.

## Dil

- Dokümantasyon, issue'lar, ADR'ler, spec'ler ve araştırma raporları **Türkçe** yazılır.
- Teknik terimler İngilizce bırakılır (örneğin guardrail, prompt injection, policy, tool call).
- Kod **İngilizcedir**: isimler (değişken, fonksiyon, sınıf, API alanları), yorumlar,
  docstring'ler, log mesajları ve test adları. Büyük bir modülün Türkçe anlatımı gerekiyorsa
  docs sitesine yazılır ([ADR 0005](https://github.com/battal-ai/battal/blob/main/docs/decisions/0005-code-language-english.md)).

## Kapsam kuralları

- Her detector, model veya policy bileşeni belgelenmiş bir interface üzerinden değiştirilebilir
  olmalıdır.
- Model ağırlıkları ve veri setleri, koddan ayrı olarak kendi lisanslarını belirtmelidir.

## Güvenlik açıkları

Güvenlik açıkları için herkese açık issue açmayın. [SECURITY.md](https://github.com/battal-ai/battal/blob/main/SECURITY.md) dosyasına bakın.
