# Battal

Açık kaynak, Türkçe öncelikli AI Safety & Agent Security platformu.

Battal; AI gateway'lerin, code studio/IDE ortamlarının ve agent runtime'ların, içlerinden geçen
içeriği değerlendirmek için çağırdığı bir güvenlik servisidir. Değerlendirilen içerik şunlardır:
kullanıcı girdisi, model yanıtı (streaming dahil), RAG içeriği, tool call'lar ve tool result'lar.
Battal, takılıp çıkarılabilen detector'ları (Türkçe ve Türkçe–İngilizce karışık metin, PII ve
secret, prompt injection, içerik güvenliği) deterministik policy uygulamasıyla tek bir evaluation
API arkasında birleştirir.

- **Proxy değildir.** LiteLLM gibi gateway'ler gateway olarak kalır; Battal onların çağırdığı
  guard'dır.
- **Değiştirilebilir bileşenler.** Modeller, scanner'lar ve policy engine'ler sabit interface'lerin
  arkasına takılır.
- **Self-hosted.** Kendi altyapınızda çalışacak şekilde tasarlanır; hassas içeriğin dışarı çıkması
  gerekmez.
- **Açıklanabilir kararlar.** Detector skorları, policy kararı ve gerekçe ayrı alanlardır;
  sürümlenir ve denetlenebilir.

Planlanan dağıtım: Python SDK (`pip install battal`) ve Battal Server (container/Helm).

> **Durum:** erken araştırma ve tasarım aşaması. Henüz kullanılabilir bir sürüm yok.

## Lisans

Apache-2.0. Modeller, veri setleri ve marka için [LICENSING.md](LICENSING.md) dosyasına bakın.

## Katkı ve güvenlik

[CONTRIBUTING.md](CONTRIBUTING.md) ve [SECURITY.md](SECURITY.md) dosyalarına bakın.
