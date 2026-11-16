# 02 — Prompt injection / jailbreak tespit modelleri ve content safety (guard) modelleri

> Battal araştırma notu · Tarih: 2026-11-16 · Kapsam: (1) prompt injection & jailbreak detection modelleri, (2) content safety / guard modelleri, (3) Türkçe'ye özgü sınıflandırıcılar ve fine-tune için encoder'lar.
>
> **Yöntem.** Varlık, lisans etiketi, gated durumu, parametre sayısı ve ONNX dosyaları Hugging Face API'den canlı çekildi (`https://huggingface.co/api/models/<id>`, 2026-11-16). Model card'lar (`/resolve/main/README.md`) ve lisans metinleri (Llama 4 / 3.2 / 3.1 Community License metinleri model card'ların gated bölümünden, Gemma Terms, NVIDIA Open Model License, OpenMDW-1.1) okundu. Ağırlık indirilmedi.
>
> **Etiketler:** **[GELİŞTİRİCİ]** = model sahibinin iddiası/ölçümü · **[BAĞIMSIZ]** = model sahibinden farklı bir tarafın ölçümü (yine de hakemli değilse "üçüncü taraf, doğrulanmamış") · **[ÇIKARIM]** = benim yorumum/tahminim · **doğrulanamadı** = kaynakta bulunamadı.
>
> **Önemli kural:** "Multilingual" ifadesi Türkçe kanıtı sayılmadı. Türkçe kanıtı = model card dil listesinde `tr` **veya** Türkçe'ye ayrılmış sayısal sonuç.

---

## 0. Yönetici özeti (TL;DR)

1. **Hiçbir büyük üreticinin (Meta, Google, IBM, NVIDIA, Qwen, AllenAI, OpenAI) guard modelinde Türkçe için ayrı raporlanmış sonuç yok.** Prompt Guard 2, Llama Guard 3/4, Nemotron Safety Guard/Content Safety dil listelerinde Türkçe yok; Granite Guardian "only trained and tested on English"; Qwen3Guard / OpenGuardrails "119 dil" diyor ama Türkçe sonucu ayrıca vermiyor (Qwen3Guard'da Türkçe, RTP-LX'in "Others (30 dil)" ortalamasının içinde kalıyor).
2. **Türkçe prompt injection için açıkça Türkçe kanıtı olan tek ciddi açık model:** `halilneed/turkish-prompt-injection-classifier` (mmBERT-base, 307M, MIT, Ekim 2026). Sonuçları tek kişinin kendi ölçümü, test setleri küçük (30/79/59 saldırı) ve sentetik/çeviri. Ayrıca aynı kartta proventra mDeBERTa ve wolf-defender-small için **üçüncü taraf** Türkçe ölçümleri var — şu an elimizdeki en somut Türkçe karşılaştırma bu.
3. **Lisans açısından en temiz CPU adayları:** Apache-2.0/MIT olan encoder sınıflandırıcıları — wolf-defender (Apache-2.0, ONNX int8 hazır, 2048 token), halilneed TR classifier (MIT), proventra mDeBERTa (MIT), PIGuard (MIT, İngilizce), ProtectAI v2 (Apache-2.0, İngilizce, **proje arşivlendi**).
4. **Llama Prompt Guard 2** teknik olarak güçlü ve CPU'ya uygun, ama **Llama 4 Community License** (gated, "Built with Llama", türev model adının "Llama" ile başlaması, AUP) Battal'ın Apache-2.0 dağıtımı içine gömülmeyi zorlaştırıyor ve Türkçe değerlendirme listesinde yok → **"kullanıcı kendi ağırlığını getirir" opsiyonel adapter**.
5. **Content safety (sonraki faz):** CPU'da makul tek açık-lisanslı LLM guard **Qwen3Guard-Gen-0.6B / Stream-0.6B** (Apache-2.0; jailbreak kategorisi de var). Büyükler (Qwen3Guard-4B/8B, gpt-oss-safeguard-20b, Nemotron 3.5 Content Safety, Llama Guard 3/4, Granite Guardian 4.1, WildGuard, ShieldGemma, PolyGuard, OpenGuardrails) yalnızca **vLLM/Ollama adapter** üzerinden.
6. **Öneri:** MVP = deterministik normalizasyon/çözücü + kurallar + **iki adet açık lisanslı encoder adayının Battal'ın kendi Türkçe/TR-EN eval setinde ölçülüp kalibre edilmesi**; ardından **mmBERT-small/base veya TabiBERT üzerinde Battal'ın kendi Apache-2.0 Türkçe injection modeli** (distilasyon öğretmeni yalnızca Apache-lisanslı modeller: Qwen3Guard, gpt-oss-safeguard).

---

## 1. Prompt injection / jailbreak modelleri — karşılaştırma tablosu

| Model (HF id) | Görev / etiketler | Param (HF API) | CPU uygunluğu | Türkçe kanıtı | Ağırlık lisansı | Bağlam | ONNX / quant | Battal kararı |
|---|---|---|---|---|---|---|---|---|
| [meta-llama/Llama-Prompt-Guard-2-86M](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M) | injection+jailbreak, binary BENIGN/MALICIOUS | 278.8M (86M backbone + ~190M embedding) | Evet (encoder) | **Yok** — değerlendirilen diller: en, fr, de, hi, it, pt, es, th | Llama 4 Community License, **gated (manual)** | 512 | Resmi yok; topluluk: [gravitee-io/...-86M-onnx](https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-86M-onnx) | **Adapter (BYO weights)** + karşılaştırma baseline'ı |
| [meta-llama/Llama-Prompt-Guard-2-22M](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M) | aynı | 70.8M | Evet, çok hızlı | **Yok**; card: 22M çok dilli ön-eğitimli değil, multilingual açığı büyük | Llama 4, gated | 512 | topluluk: [gravitee-io/...-22M-onnx](https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-22M-onnx) | Türkçe için **uygun değil** (İngilizce-only katman olarak opsiyonel) |
| [meta-llama/Prompt-Guard-86M](https://huggingface.co/meta-llama/Prompt-Guard-86M) (PG1) | BENIGN / INJECTION / JAILBREAK | 278.8M | Evet | Yok (card `language: en`; "multilingual base") | Llama 3.1 Community License, gated | 512 | topluluk | **Kapsam dışı** (PG2 tarafından geçildi; INJECTION etiketi aşırı tetikleniyor — Meta kendisi PG2'de kaldırdı) |
| [protectai/deberta-v3-base-prompt-injection-v2](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2) | injection (jailbreak **değil**) | 184.4M | Evet | **Yok** (card: "does not … handle non-English prompts"); üçüncü taraf TR ölçümü kötü (aşağıda) | Apache-2.0 | 512 [ÇIKARIM: deberta-v3 varsayılanı] | **Var** (`onnx/model.onnx`) | **Kapsam dışı** (yalnızca İngilizce referans); **proje arşivlendi** |
| [protectai/deberta-v3-small-prompt-injection-v2](https://huggingface.co/protectai/deberta-v3-small-prompt-injection-v2) | injection | 141.9M | Evet | Yok | Apache-2.0, gated (auto) | 512 [ÇIKARIM] | Var | Kapsam dışı |
| [deepset/deberta-v3-base-injection](https://huggingface.co/deepset/deberta-v3-base-injection) | LEGIT / INJECTION | 184.4M | Evet | Yok (`en`, `de`); ~660 örnekli küçük veri seti | MIT | 512 [ÇIKARIM] | Resmi yok; [protectai/deberta-v3-base-injection-onnx](https://huggingface.co/protectai/deberta-v3-base-injection-onnx) | **Kapsam dışı** (eski, aşırı tetiklenme kartta kabul ediliyor) |
| [leolee99/PIGuard](https://huggingface.co/leolee99/PIGuard) (eski adı InjecGuard) | injection, over-defense azaltma | 184.4M | Evet | Yok (`en`) | MIT | 512 [ÇIKARIM] | Resmi yok; topluluk ONNX var | İngilizce over-defense referansı; Türkçe için **kapsam dışı** |
| [patronus-studio/wolf-defender-prompt-injection](https://huggingface.co/patronus-studio/wolf-defender-prompt-injection) | injection+jailbreak, BENIGN/INJECTION | 307.5M (mmBERT-base) | Evet | **Zayıf**: card "English and German are the primary evaluated languages"; TR yalnızca üçüncü taraf ölçümü (small varyant) | **Apache-2.0** | **2048** | **Var**: int8/int4-embedding, fp16 | **Baseline adayı (configure)** |
| [patronus-studio/wolf-defender-prompt-injection-small](https://huggingface.co/patronus-studio/wolf-defender-prompt-injection-small) / [-edge](https://huggingface.co/patronus-studio/wolf-defender-prompt-injection-edge) | aynı | 140.6M / 80.0M | Evet, hızlı | Small için üçüncü taraf TR ölçümü var | Apache-2.0 | 2048 | Var | **Baseline adayı** (latency-öncelikli profil) |
| [halilneed/turkish-prompt-injection-classifier](https://huggingface.co/halilneed/turkish-prompt-injection-classifier) | **Türkçe** injection, BENIGN/INJECTION | 307.5M (v2, mmBERT-base); v1 = BERTurk | Evet (card: ~35 ms/metin, i5-12400F) | **Var** (`tr`, `en`; Türkçe test setleri, obfuscation, invisible Unicode, TR false-alarm benchmark) | **MIT** | 512 (eğitim 384) | Yok (ONNX'e çevrilebilir [ÇIKARIM]) | **Baseline adayı #1 (configure + kendi eval'imizde doğrula)** |
| [proventra/mdeberta-v3-base-prompt-injection](https://huggingface.co/proventra/mdeberta-v3-base-prompt-injection) | injection | 278.8M (mDeBERTa) | Evet | Yalnızca **üçüncü taraf** TR ölçümü (halilneed kartı) | MIT | 512 [ÇIKARIM] | Yok | Eval havuzuna al (yüksek recall, PII talimatlarında %77 FP) |
| [fevziegeyurtsevenler/turkish-prompt-injection-detector](https://huggingface.co/fevziegeyurtsevenler/turkish-prompt-injection-detector) | TR+EN injection; MiniLM embedding + logistic regression | doğrulanamadı (MiniLM-L12 tabanlı) | Evet | Var ama test n=75, eğitim 217 saldırı | Apache-2.0 | 128 [ÇIKARIM: MiniLM varsayılanı] | Yok; **`joblib` pickle** | **Kapsam dışı** (pickle = yükleme anında kod çalıştırma riski; veri çok küçük). Veri setleri eval için faydalı |
| [rogue-security/prompt-injection-jailbreak-sentinel-v2](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2) | injection+jailbreak (Qwen3-0.6B tabanlı) | 596M | Sınırlı | Yok (`en`; "retrain … for multilingual") | **"other" – Elastic license** (card: "ready for commercial use under Elastic license"), gated | 32K | Yok (GGUF var) | **Kapsam dışı** (Elastic lisansı managed-service sunumunu kısıtlar [ÇIKARIM: ELv2 tipik şartı; tam metin doğrulanamadı]) |
| [qualifire/prompt-injection-sentinel](https://huggingface.co/qualifire/prompt-injection-sentinel) | injection (ModernBERT-large) | 395.8M | Evet | Yok | "other", gated | doğrulanamadı | Yok | Kapsam dışı |
| [nvidia/NemoGuard-JailbreakDetect](https://huggingface.co/nvidia/NemoGuard-JailbreakDetect) | jailbreak; Random Forest on snowflake-arctic-embed-m-long embedding | RF + ~110M embedding modeli [ÇIKARIM] | Evet | Yok (İngilizce embedding modeli) | NVIDIA Open Model License | embedding modeline bağlı | **`snowflake.onnx` var** | Kapsam dışı (İngilizce; mimari fikir olarak not) |
| [vllm-sr/mmbert32k-jailbreak-detector-merged](https://huggingface.co/vllm-sr/mmbert32k-jailbreak-detector-merged) | jailbreak | 307.5M | Evet | Yok (`en`) | Apache-2.0 | 32K (YaRN) | Var | İzle; Türkçe kanıtı yok |
| [katanemo/Arch-Guard](https://huggingface.co/katanemo/Arch-Guard) | PG1 fine-tune | 278.8M | Evet | Yok | HF etiketi MIT **ama base = Prompt-Guard-86M (Llama 3.1 lisansı)** → lisans tutarsız [ÇIKARIM] | 512 | `-cpu` varyantı | Kapsam dışı (lisans belirsizliği) |
| Lakera Guard | Ticari SaaS API | — | — | — | Kapalı/ticari | — | — | **Kapsam dışı**; yalnızca ticari referans ([lakera.ai](https://www.lakera.ai/)) |

### 1.1 Türkçe üzerinde tek somut karşılaştırma (üçüncü taraf ölçümü)

Kaynak: [halilneed/turkish-prompt-injection-classifier model card](https://huggingface.co/halilneed/turkish-prompt-injection-classifier). Yazar: "I ran every model with the same script; these are my measurements, not the authors' published numbers." → Diğer modeller için **[BAĞIMSIZ, hakemsiz]**, kendi modeli için **[GELİŞTİRİCİ]**. Prompt Guard 2 gated olduğu için **ölçülmemiş**.

Saldırı setleri (F1; kaynak eğitimden çıkarılmış = "unseen source"):

| Model | conv (30 saldırı) | 1k (79) | berat (59)* | fevzi obfuscation recall (107) | invisible Unicode recall (42) |
|---|---|---|---|---|---|
| Keyword rule | 0.308 | 0.255 | 0.033 | — | — |
| protectai v2 (EN) | 0.320 | 0.603 | 0.422 | 0.935 | **0.024** |
| proventra mdeberta-v3 | **0.633** | 0.910 | **0.907*** | 0.925 | 0.976 |
| wolf-defender-small | 0.596 | 0.868 | 0.525 | 0.841 | 1.000 |
| halilneed v1 (BERTurk) | 0.588 | 0.823 | 0.290 | 0.832 | 0.405 |
| halilneed v2 (mmBERT) | 0.596 | **0.968** | 0.506 | **0.963** | 0.976 |

\* berat = `deepset/prompt-injections`'ın Türkçe çevirisi; deepset verisini görmüş modeller için sızıntı var (kartta belirtilmiş).

Türkçe zararsız metinde false-positive oranı (düşük = iyi):

| Model | KVKK (1,125) | Bankacılık (750) | PII görev talimatları (1,000) |
|---|---|---|---|
| protectai v2 | 0.080 | 0.141 | 0.315 |
| proventra mdeberta-v3 | 0.002 | 0.032 | **0.772** |
| wolf-defender-small | 0.011 | 0.076 | **0.607** |
| halilneed v2 ‡ | 0.011 | 0.021 | 0.000 |

‡ Kartta açıkça: bu domainler halilneed modeli için in-domain (eğitimde aynı domainden metin var), diğerleri için değil. "Trained without them, the v1 recipe flagged 65% of banking texts and 98.5% of task instructions."

**Battal için okuma [ÇIKARIM]:**
- İngilizce-only modeller (ProtectAI) Türkçe'de hem kaçırıyor hem yanlış alarm veriyor → **kullanılamaz**.
- Çok dilli encoder üzerine eğitilmiş genel modeller (proventra, wolf-defender) Türkçe saldırıyı şaşırtıcı iyi yakalıyor ama **"talimat gibi görünen ama zararsız" Türkçe metinde** (PII görev talimatları) FP'si çok yüksek. Battal'ın asıl riski bu: bir gateway'de meşru sistem/kullanıcı talimatlarını engellemek.
- Bu, **domain'e özgü hard-negative ile fine-tune / eşik kalibrasyonunun** zorunlu olduğuna dair en güçlü kanıt.
- Test setleri çok küçük; kartın kendisi iki seed arasında 0.056 F1 fark raporluyor. Bu sayılar **yön gösterir, karar vermez**. Battal kendi eval setini kurmalı.

---

## 2. Content safety / guard modelleri — karşılaştırma tablosu

| Model | Görev | Param (HF API) | CPU uygunluğu [ÇIKARIM] | Türkçe kanıtı | Ağırlık lisansı | Bağlam | Quant / ONNX | Battal kararı |
|---|---|---|---|---|---|---|---|---|
| [meta-llama/Llama-Guard-3-1B](https://huggingface.co/meta-llama/Llama-Guard-3-1B) | prompt/response safety, MLCommons 13+1 kategori | 1.50B | Zor ama mümkün (int4 [Llama-Guard-3-1B-INT4](https://huggingface.co/meta-llama/Llama-Guard-3-1B-INT4), GGUF) | **Yok** (en, fr, de, hi, it, pt, es, th) | Llama 3.2 Community License, gated; Llama 3.2 AUP'de multimodal modeller için AB kısıtı (bu model text-only) | doğrulanamadı | INT4 resmi, GGUF topluluk | **Adapter** |
| [meta-llama/Llama-Guard-3-8B](https://huggingface.co/meta-llama/Llama-Guard-3-8B) | aynı | 8.03B | Hayır | **Yok** (8 dil, TR yok) | Llama 3.1, gated | doğrulanamadı | [INT8](https://huggingface.co/meta-llama/Llama-Guard-3-8B-INT8) | **Adapter** |
| [meta-llama/Llama-Guard-4-12B](https://huggingface.co/meta-llama/Llama-Guard-4-12B) | text+image safety, S1–S14 | 12.0B | Hayır | **Yok**; "Multilingual" = LG3'ün 7 dili | Llama 4, gated. **Llama 4 AUP: multimodal modeller için AB'de yerleşik kişi/şirketlere 1(a) hakları verilmez** (son kullanıcılar hariç) | doğrulanamadı | — | **Adapter** (AB kullanıcıları için lisans uyarısı) |
| [google/shieldgemma-2b](https://huggingface.co/google/shieldgemma-2b) / [9b](https://huggingface.co/google/shieldgemma-9b) / [27b](https://huggingface.co/google/shieldgemma-27b) | policy-başına Yes/No (4 zarar türü) | 2.61B / 9.24B / 27.2B | 2B: zor | **Yok**; card: "available in English" | Gemma Terms of Use, gated | doğrulanamadı | GGUF topluluk | **Adapter** (düşük öncelik) |
| [google/shieldgemma-2-4b-it](https://huggingface.co/google/shieldgemma-2-4b-it) | **görüntü** güvenliği | 4.30B | Hayır | — | Gemma | — | — | **Kapsam dışı** (image) |
| [ibm-granite/granite-guardian-3.0-2b](https://huggingface.co/ibm-granite/granite-guardian-3.0-2b), [3.1-2b](https://huggingface.co/ibm-granite/granite-guardian-3.1-2b), [3.0/3.1-8b](https://huggingface.co/ibm-granite/granite-guardian-3.1-8b), [3.2-3b-a800m](https://huggingface.co/ibm-granite/granite-guardian-3.2-3b-a800m), [3.2-5b](https://huggingface.co/ibm-granite/granite-guardian-3.2-5b), [3.3-8b](https://huggingface.co/ibm-granite/granite-guardian-3.3-8b), [4.1-8b](https://huggingface.co/ibm-granite/granite-guardian-4.1-8b) | risk "criteria" (harm, jailbreak, groundedness, function-call hallucination, BYOC custom criteria) | 2.53B / 8B / 3.30B (MoE) / 5.78B / 8.17B / 8.38B | 3.2-3b-a800m (800M aktif) en makul; diğerleri hayır | **Yok — card: "The model is only trained and tested on English data."** (3.2-3b-a800m, 3.3-8b, 4.1-8b'de birebir) | **Apache-2.0** | doğrulanamadı | [4.1-8b-GGUF](https://huggingface.co/ibm-granite/granite-guardian-4.1-8b-GGUF), [3.3-8b-GGUF](https://huggingface.co/ibm-granite/granite-guardian-3.3-8b-GGUF) resmi | **Adapter** (RAG groundedness / agent function-call için değerli; Türkçe değil) |
| [ibm-granite/granite-guardian-hap-38m](https://huggingface.co/ibm-granite/granite-guardian-hap-38m) / [hap-125m](https://huggingface.co/ibm-granite/granite-guardian-hap-125m) | hate/abuse/profanity binary | 38M / 125M | **Evet** | **Yok** ("toxicity binary classifier for English") | Apache-2.0 | doğrulanamadı | Yok | Kapsam dışı (EN) |
| [ibm-granite/granitelib-guardian-r1.0](https://huggingface.co/ibm-granite/granitelib-guardian-r1.0) | Granite 4.x için LoRA adapter kütüphanesi (core, factuality, policy) | adapter | — | Yok (`en`) | Apache-2.0; imzalı (`model.sig`) | — | — | İzle |
| [Qwen/Qwen3Guard-Gen-0.6B](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B) / [4B](https://huggingface.co/Qwen/Qwen3Guard-Gen-4B) / [8B](https://huggingface.co/Qwen/Qwen3Guard-Gen-8B) | Safe/Controversial/Unsafe + 9 kategori (**Jailbreak dahil, yalnızca input**) | 0.75B / 4.41B / 8.19B | **0.6B: evet (yavaş ama mümkün)** | **Dolaylı**: "119 languages and dialects" (dil listesi card'da yok); [teknik rapor](https://arxiv.org/abs/2510.14276) Türkçe'yi ayrı raporlamıyor; RTP-LX (Türkçe içerir) "Others (30 dil)" ortalaması: 0.6B strict 72.2 / 8B strict 83.9 F1 | **Apache-2.0** | Örnek sglang komutunda `--context-length 32768` | GGUF, OpenVINO, MNN, topluluk ONNX ([nxp/Qwen3Guard-Gen-0.6B-ONNX](https://huggingface.co/nxp/Qwen3Guard-Gen-0.6B-ONNX)) | **0.6B: opsiyonel yerel katman / eval öğretmeni; 4B/8B: adapter + distilasyon öğretmeni** |
| [Qwen/Qwen3Guard-Stream-0.6B](https://huggingface.co/Qwen/Qwen3Guard-Stream-0.6B) / [4B](https://huggingface.co/Qwen/Qwen3Guard-Stream-4B) / 8B | token-seviyesi streaming moderasyon | 0.60B / 4.03B | 0.6B: evet | Aynı (dolaylı) | Apache-2.0 | örnekte 10000 | — | **Sonraki faz** (output streaming); Qwen3 tokenizer gerektirir → gateway'in modeli farklıysa yeniden tokenize |
| [nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3](https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3) | multilingual content safety (CultureGuard) | 8.03B | Hayır | **Yok** (en, es, zh, de, fr, hi, ja, ar, th) | NVIDIA Open Model License **+ Llama 3.1 Community License** ("Built with Llama") | 8K | GGUF topluluk | **Adapter** |
| [nvidia/Nemotron-3.5-Content-Safety](https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety) | text+image, custom policy, reasoning; Aegis 2.0 taksonomisi | 4.30B (Gemma-3-4B-it tabanlı) | Hayır (pratikte) | **Yok** (12 dil: en, ar, de, es, fr, hi, ja, th, nl, it, ko, zh); RTP-LX ortalaması 0.89 Harmful F1 (dil kırılımı yok) | **OpenMDW-1.1 + Gemma Terms of Use + Gemma Prohibited Use Policy** | 128K | FP8/GGUF topluluk | **Adapter**; distilasyon öğretmeni olarak **kullanma** (Gemma türev tanımı) |
| [nvidia/Nemotron-3-Content-Safety](https://huggingface.co/nvidia/Nemotron-3-Content-Safety) / [Nemotron-Content-Safety-Reasoning-4B](https://huggingface.co/nvidia/Nemotron-Content-Safety-Reasoning-4B) | önceki sürümler | 4.30B | Hayır | Yok | NVIDIA Nemotron Open Model License / NVIDIA Open Model License + Gemma | 128K | — | 3.5 tarafından kapsandı → atla |
| [nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0](https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0) / Permissive | LlamaGuard-7B PEFT | ~7B [ÇIKARIM] | Hayır | Yok (`en`) | Llama 2 | doğrulanamadı | — | **Kapsam dışı** (eski) |
| [allenai/wildguard](https://huggingface.co/allenai/wildguard) | prompt harm, response harm, refusal | 7.25B (Mistral-7B-v0.3) | Hayır | **Yok** ("Language(s): English") | Apache-2.0, gated (auto) | doğrulanamadı | GGUF topluluk | **Adapter** (EN refusal detection referansı) |
| [ToxicityPrompts/PolyGuard-Qwen-Smol](https://huggingface.co/ToxicityPrompts/PolyGuard-Qwen-Smol) / [-Qwen](https://huggingface.co/ToxicityPrompts/PolyGuard-Qwen) / [-Ministral](https://huggingface.co/ToxicityPrompts/PolyGuard-Ministral) | prompt harm, refusal, response harm + S1–S14 | 0.49B / 7.62B / 8.02B | Smol: evet | **Yok** — 17 dil, **Türkçe yok** ([paper](https://arxiv.org/abs/2504.04377)) | HF etiketi CC-BY-4.0; **Ministral varyantının tabanı Mistral Research License (MRL-0.1)** → ticari risk [ÇIKARIM] | doğrulanamadı | GGUF topluluk | Kapsam dışı (TR yok); veri seti fikirleri için referans |
| OpenGuardrails-Text ([kekwak/OpenGuardrails-Text-4B-0124-mirror](https://huggingface.co/kekwak/OpenGuardrails-Text-4B-0124-mirror)) | content safety + prompt attack (S9), 19 kategori | 4.02B | Hayır | **Dolaylı**: "119 languages" iddiası; Türkçe sonucu yok ([paper](https://arxiv.org/abs/2510.19169)) | Apache-2.0 (card + [GitHub](https://github.com/openguardrails/openguardrails)) | vLLM örneği 8192 | GGUF topluluk | **Adapter (düşük öncelik)** — **orijinal HF repo kaldırılmış**, yalnızca üçüncü taraf mirror var → supply-chain riski |
| [openai/gpt-oss-safeguard-20b](https://huggingface.co/openai/gpt-oss-safeguard-20b) / [120b](https://huggingface.co/openai/gpt-oss-safeguard-120b) | bring-your-own-policy reasoning sınıflandırıcı | 21.5B (3.6B aktif) / 117B (5.1B aktif) | Hayır (card: 16GB VRAM) | **Yok** (dil bilgisi card'da yok) | **Apache-2.0** | doğrulanamadı | MXFP4 / GGUF | **Adapter + distilasyon öğretmeni (lisans temiz)** |
| Lakera Guard | ticari | — | — | — | kapalı | — | — | Kapsam dışı |

### 2.1 Türkçe toxicity / offensive sınıflandırıcılar (Hugging Face)

| Model | Taban | Param | Türkçe kanıtı | Metrik | Lisans | Not / Karar |
|---|---|---|---|---|---|---|
| [Overfit-GM/distilbert-base-turkish-cased-offensive](https://huggingface.co/Overfit-GM/distilbert-base-turkish-cased-offensive) (+ aynı ailede bert/electra/convbert/[xlm-roberta-large](https://huggingface.co/Overfit-GM/xlm-roberta-large-turkish-offensive) varyantları) | DistilBERT-TR | doğrulanamadı (HF API safetensors yok) | `tr` | **Card'da metrik yok** (card yalnızca YAML) | Apache-2.0 | Muhtemel veri: [Overfit-GM/turkish-toxic-language](https://huggingface.co/datasets/Overfit-GM/turkish-toxic-language) (Apache-2.0) [ÇIKARIM]. Eval havuzu |
| [gokceuludogan/convbert-base-turkish-mc4-toxicity-uncased](https://huggingface.co/gokceuludogan/convbert-base-turkish-mc4-toxicity-uncased) | ConvBERT-TR (dbmdz) | doğrulanamadı | `tr`; Jigsaw Multilingual'den süzülmüş Türkçe yorumlar | metrik yok | BSD | Jigsaw verisinin kendi şartları ayrıca kontrol edilmeli |
| [cagrigungor/turkishtoxic-classifier](https://huggingface.co/cagrigungor/turkishtoxic-classifier) | sıfırdan eğitilmiş 12 katmanlı TR encoder | 54.7M | `tr` | [GELİŞTİRİCİ] val acc 0.9389, macro F1 0.9385 (100K yorum) | Apache-2.0 | Küçük ve hızlı; bağımsız ölçüm yok |
| [ariyul/turkish-toxic-language-detection](https://huggingface.co/ariyul/turkish-toxic-language-detection) | BERT | 110.6M | `tr` | [GELİŞTİRİCİ] acc/F1 0.96 (Overfit-GM veri seti) | MIT | Eval havuzu |

**Karar [ÇIKARIM]:** Bunlar "offensive language / küfür / hakaret" seviyesinde; LLM content-safety taksonomisini (silah, self-harm, CSAM, suç talimatı vb.) kapsamıyor. Output-safety fazında **"Türkçe küfür/hakaret" alt-sinyali** olarak kullanılabilir; ana content-safety çözümü değil. MVP kapsamı dışında.

---

## 3. Fine-tune için encoder'lar

| Encoder | Param | Türkçe kanıtı | Lisans | Max uzunluk | Not |
|---|---|---|---|---|---|
| [dbmdz/bert-base-turkish-cased](https://huggingface.co/dbmdz/bert-base-turkish-cased) (BERTurk) / [128k](https://huggingface.co/dbmdz/bert-base-turkish-128k-cased) | 111M / 185M | Monolingual TR, 35GB korpus | MIT | 512 | TabiBench'te güçlü (75.96 ort.) [BAĞIMSIZ: TabiBERT yazarları]; TR-EN karışık metinde İngilizce zayıf [ÇIKARIM] |
| [boun-tabilab/TabiBERT](https://huggingface.co/boun-tabilab/TabiBERT) | 149.5M | TR + ~%13 EN/kod/math; [paper](https://arxiv.org/abs/2512.23065); TabiBench 77.58 (BERTurk 75.96) [GELİŞTİRİCİ] | Apache-2.0 | **8192** | ModernBERT mimarisi → ONNX/hızlı CPU; **TR-EN karışık için en uygun TR-merkezli aday** |
| [jhu-clsp/mmBERT-base](https://huggingface.co/jhu-clsp/mmBERT-base) / [mmBERT-small](https://huggingface.co/jhu-clsp/mmBERT-small) | 307M (110M non-emb) / 140M (42M non-emb) | Dil listesinde `tur` var (1833 dil); Türkçe'ye özel sonuç card'da yok; **dolaylı kanıt: halilneed v2 ve wolf-defender bunun üzerine** | MIT | 8192 | Injection için kanıtlanmış taban; wolf-defender ONNX int8 gösteriyor ki export çalışıyor |
| [microsoft/mdeberta-v3-base](https://huggingface.co/microsoft/mdeberta-v3-base) | 86M backbone + 190M embedding (~279M) | XNLI zero-shot **tr: 79.5** (XLM-R-base 74.2) [GELİŞTİRİCİ] | MIT | 512 | Prompt Guard 2 86M'in tabanı; ONNX export olgun |
| [FacebookAI/xlm-roberta-base](https://huggingface.co/FacebookAI/xlm-roberta-base) / [large](https://huggingface.co/FacebookAI/xlm-roberta-large) | 279M / 561M | dil listesinde `tr` | MIT | 512 | halilneed seçim protokolünde XLM-R base 0.493 vs mmBERT-base 0.674 mean F1 [üçüncü taraf, tek seed] |
| [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) / [base](https://huggingface.co/intfloat/multilingual-e5-base) | 118M / 278M | dil listesinde `tr` | MIT | 512 | Embedding + hafif kafa (LogReg/MLP) ile hızlı prototip veya benzerlik-tabanlı "bilinen saldırı" araması |
| [99eren99/ModernBERT-base-Turkish-uncased-mlm](https://huggingface.co/99eren99/ModernBERT-base-Turkish-uncased-mlm) | 135.5M | `tr` | Apache-2.0 | doğrulanamadı | uncased → homoglyph/case sinyali kaybı [ÇIKARIM]; ikincil |

---

## 4. Model başına notlar

### 4.1 Llama Prompt Guard 2 (86M, 22M)
- **Kaynak:** [86M card](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M), [22M card](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M); [LlamaFirewall paper](https://arxiv.org/abs/2505.03574).
- **Görev:** binary benign/malicious; "explicitly attempts to override prior instructions". PG1'deki "injection" etiketi "too broad to be useful" diye kaldırılmış. Zararlı içerik tespiti yapmaz.
- **Teknik:** 86M → mDeBERTa-base; 22M → DeBERTa-xsmall. "Adversarial-attack resistant tokenization" (whitespace, fragmented token). Energy-based loss. **512 token**; uzun girdiler parçalanmalı.
- **Metrikler [GELİŞTİRİCİ, özel benchmark]:** AUC EN .998 / multilingual .995 (86M); Recall@1%FPR EN 97.5% (86M), 88.7% (22M); 22M multilingual AUC .942. AgentDojo APR@3% utility: 81.2% / 78.4% (ProtectAI 22.2%, Deepset 13.5%). Latency A100'de ölçülmüş, CPU ölçümü yok.
- **Bağımsız ölçümler:** Hakemli bağımsız çok dilli değerlendirme bulunamadı. Vendor raporları çelişkili (ör. Alice benchmark F1 0.621 / FPR 0.070 — rakip vendor, doğrulanmadı). Türkçe ölçümü **yok** (halilneed kartı gated olduğu için test etmemiş).
- **Türkçe:** card'daki 8 dilde yok → **Türkçe kanıtı yok**. mDeBERTa tabanı Türkçe görmüş olduğu için bir miktar transfer beklenebilir [ÇIKARIM]; ölçülmeli.
- **Lisans (Llama 4 Community License, card'daki tam metin okundu):** ticari kullanım serbest (700M MAU üstü hariç); dağıtımda lisans kopyası + "Built with Llama" ibaresi + NOTICE dosyası; **"If you use the Llama Materials or any outputs or results … to create, train, fine tune, or otherwise improve an AI model, which is distributed … include 'Llama' at the beginning of any such AI model name"**; AUP'ye uyma zorunluluğu; gated erişim (form, ad-soyad, doğum tarihi). Multimodal AB kısıtı PG2'ye (text-only) uygulanmaz.
- **ONNX:** resmi yok; topluluk dönüşümleri ([gravitee-io 86M](https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-86M-onnx), [22M](https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-22M-onnx)) — bunlar da Llama lisansına tabi; özel tokenizer davranışının ONNX pipeline'da korunduğu **doğrulanamadı**.
- **Battal kararı:** **Adapter / BYO weights.** Battal imajına gömülmesin; kullanıcı HF token + lisans kabulü ile kendi indirir. Eval'de karşılaştırma baseline'ı olarak ölçülsün. PG2 üzerine Türkçe fine-tune yayınlanırsa model adı "Llama…" ile başlamak zorunda ve Apache-2.0 olamaz → **PG2'yi fine-tune tabanı olarak seçme.**

### 4.2 Prompt Guard 1 (86M)
- [Card](https://huggingface.co/meta-llama/Prompt-Guard-86M): BENIGN/INJECTION/JAILBREAK; Llama 3.1 License (aynı "Llama" adlandırma ve "Built with Llama" şartları); `language: en`. Metrikler [GELİŞTİRİCİ]: Multilingual Jailbreak Set AUC 0.959 vb. PG2 card'ına göre Recall@1%FPR EN %21.2.
- **Karar: kapsam dışı.**

### 4.3 ProtectAI deberta-v3-base-prompt-injection-v2
- [Card](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2): "**THIS PROJECT HAS BEEN ARCHIVED**"; [llm-guard GitHub](https://github.com/protectai/llm-guard) API'de `archived: true` (son push 2026-07-08).
- Yalnızca İngilizce injection; jailbreak tespit etmiyor; sistem promptlarında FP uyarısı. Metrikler [GELİŞTİRİCİ]: 20k görülmemiş prompt'ta acc 95.25%, precision 91.59%, recall 99.74%.
- Türkçe [üçüncü taraf]: invisible Unicode recall 0.024, bankacılık FP 0.141 → **Türkçe'de kullanılamaz**.
- Lisans: Apache-2.0; ONNX resmi var.
- **Karar: kapsam dışı** (yalnızca İngilizce regresyon karşılaştırması için).

### 4.4 deepset/deberta-v3-base-injection
- [Card](https://huggingface.co/deepset/deberta-v3-base-injection): `JasperLS/prompt-injections` (~660 örnek) üzerinde 3 epoch; eval acc 0.9914 [GELİŞTİRİCİ, aynı dağılım]. Card kendi "trigger-happy" olabileceğini söylüyor. MIT. **Kapsam dışı.**

### 4.5 PIGuard (InjecGuard)
- [Card](https://huggingface.co/leolee99/PIGuard), [ACL 2025 paper](https://aclanthology.org/2025.acl-long.1468.pdf), [GitHub](https://github.com/leolee99/PIGuard). Over-defense (trigger-word bias) azaltma odağı; MIT; deberta-v3-base; İngilizce. **Türkçe kanıtı yok.** Fikir olarak önemli: "MOF (Mitigating Over-defense for Free)" stratejisi Battal fine-tune'unda hard-negative üretimi için referans. **Karar: kapsam dışı (model), referans (yöntem).**

### 4.6 Wolf Defender (patronus-studio) — base / small / edge
- [Card](https://huggingface.co/patronus-studio/wolf-defender-prompt-injection): mmBERT-base, 2048 token pencere, Apache-2.0, ONNX (int8 + int4 embedding, x86 varyantı, fp16). Red Hat AI üzerinden de yayınlanıyor.
- Metrikler [GELİŞTİRİCİ]: 13-benchmark ortalaması 92.29% (base) / 91.66% (small) / 91.44% (edge); validation FPR %0.5–0.64. Topluluk ölçümleri (AI-Parrot) küçük örneklem, [GELİŞTİRİCİ tarafından aktarılan üçüncü taraf].
- **Türkçe:** card: "English and German are the primary evaluated languages. Other languages were represented during training but have not received the same level of validation." Eğitim verisinde `rikka-snow/prompt-injection-multilingual` var (deepset'in 11 dile çevirisi; Türkçe içerip içermediği **doğrulanamadı**). Üçüncü taraf Türkçe ölçümü (small): iyi saldırı recall'u, ama PII-talimat FP %60.7.
- **Karar: baseline adayı (configure)** — eşik kalibrasyonu + Türkçe hard-negative ile birlikte. Lisans ve ONNX açısından en "hazır" seçenek.

### 4.7 halilneed/turkish-prompt-injection-classifier
- [Card](https://huggingface.co/halilneed/turkish-prompt-injection-classifier). v2 = mmBERT-base (307M), v1 = BERTurk (`revision="v1"`). MIT. Önerilen eşik **0.05** (v2.1, 14 Ekim 2026'da 0.3'ten değişti). Opsiyonel `detect.py` çözücü: base64, hex, Caesar, ters metin, harf aralama, leetspeak, Kiril homoglyph, invisible Unicode.
- Metrikler: §1.1 tablosu. Kendi modeli için **[GELİŞTİRİCİ]**; seçim/rapor ayrımı açıkça belgelenmiş (iyi pratik), ama tek yazar, küçük test setleri, seed varyansı yüksek (2 ek seed: 0.638 ve 0.529 ortalama F1 — yayınlanan seed şanslı olabilir, card bunu kendisi söylüyor).
- Eğitim verisi: 3nesdeniz TR setleri (CC-BY-4.0), beratcmn (Apache-2.0), 3nesdeniz İngilizce agentic setler (CC-BY-4.0), yazarın kendi KVKK/bankacılık/PII metinleri.
- Bilinen zayıflıklar (card): görülmemiş kaynaklı agentic saldırılar (memory poisoning, exfiltration, tool abuse 0/3); tüm TR veriler sentetik/çeviri; konuşma bağlamını görmüyor.
- `detect.py` / `guard.py` **uzak kod** — Battal bunları çalıştırmamalı; fikirleri kendi deterministik katmanında yeniden yazmalı [ÇIKARIM].
- **Karar: baseline adayı #1 (configure)**, Battal eval setinde wolf-defender ve proventra ile kafa kafaya ölçülecek. Tek-kişi bakımlı bir modele bağımlılık riski → orta vadede Battal kendi modelini eğitmeli.

### 4.8 proventra/mdeberta-v3-base-prompt-injection
- [Card](https://huggingface.co/proventra/mdeberta-v3-base-prompt-injection): mDeBERTa üzerinde jackhhao/deepset vb. İngilizce setler; MIT; card'da metrik yok. Türkçe üçüncü taraf: saldırı recall'u yüksek, PII-talimat FP %77.2. **Karar:** eval havuzunda kalsın; tek başına üretim için riskli.

### 4.9 Llama Guard 3 (1B, 8B) ve Llama Guard 4 (12B)
- [LG3-1B](https://huggingface.co/meta-llama/Llama-Guard-3-1B), [LG3-8B](https://huggingface.co/meta-llama/Llama-Guard-3-8B), [LG4-12B](https://huggingface.co/meta-llama/Llama-Guard-4-12B).
- Diller: en, fr, de, it, pt, hi, es, th — **Türkçe yok**. LG4 "multilingual" sonucu da bu 7 dilin ortalaması.
- Metrikler [GELİŞTİRİCİ, iç test seti]: LG3-1B F1/FPR EN 0.899/0.090, LG3-8B EN 0.939/0.040; LG4 EN R 69% / FPR 11% / F1 61%, multilingual F1 51% (output filtering).
- **Bağımsız [BAĞIMSIZ: Qwen ekibi, rakip]**: Qwen3Guard raporunda RTP-LX "Others (30 dil, Türkçe dahil)" F1: LlamaGuard3-8B 46.0, LlamaGuard4-12B 42.7 → Türkçe dahil düşük kaynaklı dillerde zayıf.
- Lisans: Llama 3.2 (1B), 3.1 (8B), 4 (12B). **Llama 4 AUP: "With respect to any multimodal models included in Llama 4, the rights granted under Section 1(a) … are not being granted to you if you are … domiciled in, or a company with a principal place of business in, the European Union"** ([Llama 4 AUP](https://www.llama.com/llama4/use-policy/)) — LG4 natively multimodal → AB'deki Battal operatörleri için risk.
- Prompt injection'a kendisi açık (LG4 card: "may be susceptible to adversarial attacks or prompt injection").
- **Karar: adapter** (kullanıcının vLLM/Ollama'sı). Türkçe için önerilmez.

### 4.10 ShieldGemma (2B/9B/27B) ve ShieldGemma 2
- [ShieldGemma-2b card](https://huggingface.co/google/shieldgemma-2b), [paper](https://arxiv.org/abs/2407.21772). "available in English". Policy-başına Yes/No olasılığı (eşiklenebilir skor → kalibrasyona uygun).
- Metrikler [GELİŞTİRİCİ]: Optimal F1/AU-PRC — 2B: SG Prompt 0.825/0.887, OpenAI Mod 0.812/0.887, ToxicChat 0.704/0.778. [BAĞIMSIZ: Qwen raporu] RTP-LX "Others": ShieldGemma-9B 51.6.
- ShieldGemma 2 (4B) **yalnızca görüntü** güvenliği.
- Lisans: **Gemma Terms of Use** ([metin](https://ai.google.dev/gemma/terms), son değişiklik 2026-04-01): Prohibited Use Policy'yi downstream sözleşmelere taşıma zorunluluğu (3.1), Google'ın "restrict (remotely or otherwise) usage" hakkı (3.2), **Model Derivatives tanımı Gemma çıktılarından üretilen sentetik veriyle eğitilen modelleri de kapsar** → Gemma tabanlı bir guard'dan distilasyon yapılan model Gemma şartlarına girer.
- **Karar: adapter (düşük öncelik); distilasyon öğretmeni olarak kullanma.**

### 4.11 IBM Granite Guardian (tüm boyutlar)
- 3.0-2b/8b, 3.1-2b/8b, 3.2-3b-a800m, 3.2-5b, 3.3-8b, **4.1-8b (2026-04)**, granitelib-guardian-r1.0 (Granite 4.x LoRA kütüphanesi, imzalı), HAP-38m/125m, 4.0-3b-toxicity-ja (Japonca).
- Kapsam: harm, jailbreak, profanity, social bias, groundedness, context relevance, function-call hallucination, **BYOC custom criteria** (4.1). Hybrid think/no-think.
- **Türkçe: yok — "The model is only trained and tested on English data."** ([3.3-8b](https://huggingface.co/ibm-granite/granite-guardian-3.3-8b), [4.1-8b](https://huggingface.co/ibm-granite/granite-guardian-4.1-8b), [3.2-3b-a800m](https://huggingface.co/ibm-granite/granite-guardian-3.2-3b-a800m)).
- Metrikler [GELİŞTİRİCİ]: 4.1-8b OOD safety F1 0.79 (no-think), RAG groundedness ort. BAcc 0.76 (think).
- Lisans: **Apache-2.0** (en temiz büyük guard lisanslarından). Resmi GGUF var.
- **Karar: adapter** — özellikle agent function-call hallucination ve RAG groundedness gibi Battal'ın sonraki "agent security" fazı için. Türkçe kalitesi Battal tarafından ölçülmeli.

### 4.12 Qwen3Guard (varlığı doğrulandı)
- [Gen-0.6B](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B), [Gen-4B](https://huggingface.co/Qwen/Qwen3Guard-Gen-4B), [Gen-8B](https://huggingface.co/Qwen/Qwen3Guard-Gen-8B), [Stream-0.6B](https://huggingface.co/Qwen/Qwen3Guard-Stream-0.6B), [Stream-4B](https://huggingface.co/Qwen/Qwen3Guard-Stream-4B), Stream-8B; 2025-09-23; [teknik rapor arXiv 2510.14276](https://arxiv.org/abs/2510.14276).
- Etiketler: Safe / Controversial / Unsafe (strict/loose modu); kategoriler: Violent, Non-violent Illegal Acts, Sexual, PII, Suicide & Self-Harm, Unethical Acts (hate, offensive language dahil), Politically Sensitive, Copyright, **Jailbreak (yalnızca input)**. Response için refusal etiketi.
- **Türkçe:** card "119 languages and dialects" diyor; rapora göre eğitim verisi Qwen-MT ile **15 ek dile** çevrilmiş (hangi diller olduğu raporda listelenmiyor → Türkçe'nin eğitimde olup olmadığı **doğrulanamadı**). RTP-LX değerlendirmesinde Türkçe yalnızca "Others (30 dil)" ortalamasında [GELİŞTİRİCİ]: 0.6B strict 72.2, 4B strict 79.8, 8B strict 83.9 F1. RTP-LX'in Türkçe içerdiği [RTP-LX repo](https://github.com/microsoft/RTP-LX)'dan doğrulandı.
- Lisans: **Apache-2.0** → Battal'a gömülebilir, distilasyon öğretmeni olabilir.
- CPU: 0.6B (~0.75B param) generatif; tek prompt için birkaç token üretir. CPU'da yüzlerce ms–saniye mertebesi [ÇIKARIM, ölçülmedi]. GGUF/OpenVINO/MNN/topluluk ONNX var.
- **Karar:** Gen-0.6B → opsiyonel "yerel LLM guard" katmanı (Ollama/llama.cpp adapter ile) ve Türkçe content-safety eval'de ilk aday; Gen-4B/8B → adapter + **etiketleme/distilasyon öğretmeni**. Stream → output faz.

### 4.13 NVIDIA Aegis / NemoGuard / Nemotron Safety
- **Aegis 1.0** ([Defensive](https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0)): LlamaGuard-7B PEFT, Llama 2 lisansı, İngilizce → kapsam dışı.
- **llama-3.1-nemoguard-8b-content-safety** ([card](https://huggingface.co/nvidia/llama-3.1-nemoguard-8b-content-safety)): `en`, lisans "other" → kapsam dışı (v3 ile geçildi).
- **Llama-3.1-Nemotron-Safety-Guard-8B-v3** ([card](https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3)): 9 dil, **Türkçe yok**; 8K bağlam; NVIDIA Open Model License + Llama 3.1. ("…Multilingual-8B-v3" adlı repo HF API'de bulunamadı; doğru ad bu.)
- **Nemotron-3.5-Content-Safety** ([card](https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety), 2026-05): Gemma-3-4B-it tabanlı, text+image, custom policy, 128K bağlam, 12 dil (**Türkçe yok**). [GELİŞTİRİCİ] RTP-LX Harmful F1 0.89 (ortalama, dil kırılımı yok); Dynaguardrail "Prompt Injection" custom policy 0.90. Lisans: **OpenMDW-1.1** ([metin](https://raw.githubusercontent.com/OpenMDW/OpenMDW/refs/heads/main/1.1/LICENSE.OpenMDW-1.1) — çok serbest: lisans kopyası + notice'ları koru, patent davası halinde fesih, çıktılar üzerinde kısıt yok) **+ Gemma Terms + Gemma Prohibited Use Policy** (base model nedeniyle) → efektif olarak Gemma şartları geçerli.
- **NVIDIA Open Model License** ([metin](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/), 2025-10-24): ticari kullanım ve türev dağıtımı serbest; NOTICE: "Licensed by NVIDIA Corporation under the NVIDIA Open Model License"; **guardrail'i devre dışı bırakma/azaltma halinde otomatik fesih**; patent/copyright davasında fesih.
- **NemoGuard-JailbreakDetect** ([card](https://huggingface.co/nvidia/NemoGuard-JailbreakDetect), [paper](https://arxiv.org/abs/2412.01547)): snowflake-arctic-embed-m-long embedding + Random Forest; [GELİŞTİRİCİ] JailbreakHub F1 0.9601, FPR 0.0042. İngilizce. **Mimari fikir:** "embedding + hafif sınıflandırıcı" Battal'da hızlı ikinci görüş / bilinen-saldırı benzerliği için kullanılabilir (çok dilli embedding ile).
- **Karar:** Nemotron 3.5 → adapter; diğerleri kapsam dışı.

### 4.14 WildGuard (AllenAI)
- [Card](https://huggingface.co/allenai/wildguard), [paper](https://arxiv.org/abs/2406.18495): Mistral-7B-v0.3, prompt harm + response harm + **refusal**; "Language(s): English"; Apache-2.0 (gated-auto). [BAĞIMSIZ: Qwen raporu] RTP-LX "Others" F1 37.5 → düşük kaynaklı dillerde zayıf. **Karar: adapter (EN), Türkçe için önerilmez.**

### 4.15 PolyGuard
- [Card](https://huggingface.co/ToxicityPrompts/PolyGuard-Qwen-Smol), [paper arXiv 2504.04377](https://arxiv.org/abs/2504.04377): "17 Languages" — ar, cs, zh, nl, en, fr, de, hi, th, it, ja, ko, pl, pt, ru, es, sv. **Türkçe yok** (paper metninde "Turkish" geçmiyor).
- Lisans etiketi CC-BY-4.0; ancak [PolyGuard-Ministral](https://huggingface.co/ToxicityPrompts/PolyGuard-Ministral)'ın tabanı Ministral-8B-Instruct-2410 = **Mistral Research License** ([MRL-0.1](https://mistral.ai/licenses/MRL-0.1.md)) → ticari kullanım riski [ÇIKARIM: türev ağırlık taban lisansını miras alır]. Qwen tabanlılar Apache-2.0 taban.
- **Karar: kapsam dışı** (Türkçe yok). PolyGuardMix veri setinin Türkçe genişletme için çeviri şablonu olarak incelenmesi önerilir.

### 4.16 OpenGuardrails
- [Paper arXiv 2510.19169](https://arxiv.org/abs/2510.19169), [GitHub openguardrails/openguardrails](https://github.com/openguardrails/openguardrails) (Apache-2.0, aktif: son push 2026-11-04).
- **HF durumu:** `OpenGuardrails/OpenGuardrails-Text-2510` HF API'de **yok**; `openguardrails` org'unda model listesi boş. Mevcut olanlar üçüncü taraf: [kekwak/…-4B-0124-mirror](https://huggingface.co/kekwak/OpenGuardrails-Text-4B-0124-mirror) ("The original repository is no longer available on Hugging Face"; SHA-256 verilmiş), [mradermacher GGUF](https://huggingface.co/mradermacher/OpenGuardrails-Text-4B-0124-GGUF), AXONVERTEX Q8 GGUF (2510).
- Paper: 2510 modeli 14B dense tabandan fine-tune + GPTQ ile "3.3B"; 4B-0124 için mirror metadata `base_model: Qwen/Qwen2.5-7B` diyor ama param 4.02B → **tutarsız; taban doğrulanamadı**.
- "119 dil" iddiası; Türkçe sonucu yok. Kategori seti Çin regülasyonuna yakın (S2 "Sensitive Political Topics", S3 "Insult to National Symbols or Leaders") [ÇIKARIM: Türkiye bağlamı için politika eşlemesi gerekir].
- **Karar: adapter (düşük öncelik)**; orijinal kaynak kaybolduğu için resmi olarak desteklenen model listesine alınmasın.

### 4.17 gpt-oss-safeguard (20B / 120B)
- [Card](https://huggingface.co/openai/gpt-oss-safeguard-20b): bring-your-own-policy reasoning; harmony formatı zorunlu; 20b = 21.5B (3.6B aktif), 16GB VRAM. **Apache-2.0.** Dil desteği card'da belirtilmemiş → **Türkçe doğrulanamadı.**
- **Karar: adapter + distilasyon/etiketleme öğretmeni** (lisans temiz; Türkçe politika metni yazılabilir).

### 4.18 Türkçe toxicity sınıflandırıcıları
- §2.1'e bakınız. Hiçbirinde bağımsız ölçüm yok; çoğunun card'ı boş/eksik. Output fazında "TR küfür/hakaret" yardımcı sinyali. **MVP: kapsam dışı.**

### 4.19 Diğer gözlemler
- [enguard/medium-guard-128m-xx-prompt-safety-binary-polyguard](https://huggingface.co/enguard/medium-guard-128m-xx-prompt-safety-binary-polyguard): model2vec statik embedding (potion-multilingual-128M) + kafa, MIT; PolyGuard verisi (Türkçe yok). Çok hızlı "statik embedding" yaklaşımının örneği; [ÇIKARIM] Battal'ın en ucuz ön-filtresi için ilham.
- [daniel315a/xlm-roberta-prompt-injection-multilingual](https://huggingface.co/daniel315a/xlm-roberta-prompt-injection-multilingual): en/es/fr/de; Türkçe yok.
- Türkçe/çok dilli değerlendirme için lisanslı veri setleri (HF API, 2026-11-16): [fevzi turkish-prompt-injection](https://huggingface.co/datasets/fevziegeyurtsevenler/turkish-prompt-injection) (CC-BY-4.0), [invisible-unicode-injection](https://huggingface.co/datasets/fevziegeyurtsevenler/invisible-unicode-injection) (CC-BY-4.0), [halilneed false-alarm benchmark](https://huggingface.co/datasets/halilneed/turkish-prompt-injection-false-alarm-benchmark) (CC0), [3nesdeniz 1k](https://huggingface.co/datasets/3nesdeniz/turkish-prompt-injection-1k) ve [conversation](https://huggingface.co/datasets/3nesdeniz/turkish-conversation-prompt-injection) (CC-BY-4.0), [beratcmn](https://huggingface.co/datasets/beratcmn/turkish-prompt-injections) (Apache-2.0), [Overfit-GM turkish-toxic-language](https://huggingface.co/datasets/Overfit-GM/turkish-toxic-language) (Apache-2.0), [RTP-LX](https://github.com/microsoft/RTP-LX) (MIT + NOTICE'teki üçüncü taraf lisansları; Türkçe dahil).
- Over-defense'in genel bir sorun olduğuna dair yakın tarihli çalışma: [PIDS-Bench, arXiv 2609.15017](https://arxiv.org/abs/2609.15017) — "F1 > 0.98" bir dedektör harici güvenlik-komşusu zararsız prompt'ların ~1/3'ünü yanlış sınıflıyor (özet sayfasından; model bazlı sayılar okunmadı).

---

## 5. Battal için öneri

### 5.1 MVP baseline (input: Türkçe + TR-EN karışık injection/jailbreak, CPU-only)

Katmanlı, her katmanın skoru ve gerekçesi ayrı döner:

1. **Deterministik normalizasyon & çözücü (kod, model değil):** Unicode NFKC, invisible/format karakterleri (Cf kategorisi, tag karakterleri U+E0000–E007F, zero-width, bidi override) **tespit + raporla + temizle**; Türkçe'ye duyarlı case-folding (İ/ı, I/i — `str.lower()` Türkçe'de yanlış); homoglyph (Kiril/Yunan) eşleme; base64/hex/rot/ters metin/harf aralama çözme; çözülmüş varyantların her biri sınıflandırıcıya da gönderilir (halilneed `detect.py` fikri; **kodu çalıştırmadan**, sıfırdan yazılmalı). Gerekçe: üçüncü taraf ölçümünde invisible Unicode'da ProtectAI recall 0.024 → decoder ile 0.500; BERTurk-v1 0.405 → 0.905.
2. **Kurallar:** TR + EN imza listesi (ör. "önceki talimatları yok say", "sistem promptunu göster", rol değiştirme kalıpları) — yalnızca **yüksek precision** kurallar; tek başına keyword rule üçüncü taraf ölçümünde F1 0.03–0.31 → kurallar sınıflandırıcının yerine geçemez, ancak açıklanabilir sinyal ve hızlı yol sağlar.
3. **Sınıflandırıcı (ONNX Runtime, CPU, int8):** Önce Battal eval setinde **üç aday** ölçülür, varsayılan olarak kazanan paketlenir:
   - `halilneed/turkish-prompt-injection-classifier` v2 (MIT) — Türkçe'ye özgü, en iyi TR hard-negative FP.
   - `patronus-studio/wolf-defender-prompt-injection-small` veya `-edge` (Apache-2.0) — ONNX int8 hazır, 2048 token, kurumsal kullanım kanıtı.
   - `proventra/mdeberta-v3-base-prompt-injection` (MIT) — recall referansı.
   - Ölçüm sonrası: **eşik kalibrasyonu** (hedef: TR hard-benign FPR ≤ %1–2'de max recall), gerekirse iki modelin ortalaması (latency bütçesi içinde).
4. **Opsiyonel adapter'lar (Battal imajında ağırlık yok):** Llama Prompt Guard 2 86M (BYO weights, Llama 4 lisansı kullanıcıda), Qwen3Guard-Gen-0.6B/4B/8B (Ollama/vLLM), Granite Guardian 4.1 `jailbreak` criteria (vLLM).

**Neden PG2 varsayılan değil:** (a) Türkçe değerlendirme listesinde yok; (b) gated + Llama 4 lisansı Apache-2.0 bir projenin varsayılan imajına gömülmesini (NOTICE, "Built with Llama", AUP geçişi) ve türev yayımlamayı ("Llama" ad öneki) zorlaştırıyor; (c) 512 token. Ama eval'de mutlaka ölçülmeli — Türkçe'de iyi çıkarsa "önerilen opsiyonel adapter" olarak belgelenir.

### 5.2 Yalnızca adapter olacak modeller (vLLM / Ollama / OpenAI-compatible)

| Model | Neden adapter | Öncelik |
|---|---|---|
| Qwen3Guard-Gen-4B / 8B | Apache-2.0, jailbreak + content safety, 119 dil iddiası, RTP-LX "Others" en iyi skorlar | **Yüksek** (output fazı ana aday) |
| gpt-oss-safeguard-20b | Apache-2.0, kendi Türkçe politikamızı yazabiliriz | Yüksek (custom policy) |
| Granite Guardian 4.1-8b / 3.3-8b | Apache-2.0, agent function-call & groundedness; yalnızca EN | Orta (agent security fazı) |
| Llama Guard 3-8B / 4-12B, 3-1B | Yaygın, MLCommons taksonomisi; TR yok; LG4'te AB multimodal kısıtı | Orta (uyumluluk) |
| Nemotron-3.5-Content-Safety | 128K, custom policy; TR yok; Gemma şartları | Orta |
| WildGuard, ShieldGemma | EN; refusal detection (WildGuard) | Düşük |
| OpenGuardrails-Text | Orijinal HF kaynağı kayıp | Düşük / resmi destek yok |
| PolyGuard, Aegis 1.0, PG1, Sentinel v2 | TR yok / eski / lisans sorunlu | Kapsam dışı |

### 5.3 Fine-tune / distilasyon ne zaman haklı?

**Baseline yeterli sayılır eğer** (Battal eval setinde, eşik kalibrasyonu sonrası): TR saldırı recall ≥ hedef (ör. ≥ %90) **ve** TR hard-benign FPR ≤ %1–2 **ve** TR-EN karışık ve obfuscation alt-kümelerinde belirgin çöküş yok. O zaman fine-tune yerine kural + eşik + ensemble ile devam.

**Fine-tune haklı çıkar eğer** (beklentim [ÇIKARIM]: büyük olasılıkla evet):
- Hard-benign FP yüksek kalıyorsa — üçüncü taraf ölçümleri genel çok dilli modellerde "talimat gibi görünen zararsız Türkçe" metinde %60–77 FP gösteriyor; bu eşikle düzelmez, **hard-negative ile eğitim** gerektirir.
- Türkçe morfolojik yeniden ifade, TR-EN code-mixing, Türkçe agentic (tool output, RAG, e-posta) dolaylı injection'da recall düşükse.
- Lisans bağımsızlığı istendiğinde: varsayılan modelin Battal'ın kendi Apache-2.0 ağırlığı olması, tek kişilik üçüncü taraf modele bağımlılığı kaldırır.

**Fine-tune planı:**
1. **Eval seti önce (Faz 0):** TR saldırı (doğrudan, dolaylı/agentic, jailbreak persona, morfolojik varyasyon), TR-EN karışık, obfuscation (invisible, homoglyph, encoding), **TR hard-benign** (KVKK, bankacılık, müşteri hizmetleri, kod/teknik, güvenlik eğitimi metinleri, kullanıcının kendi talimatını değiştirmesi). Kaynaklar: §4.19'daki lisanslı setler + elle yazılmış/gözden geçirilmiş örnekler. Test seti **eğitimden kaynak bazında ayrılmalı** (halilneed'in held-out-source protokolü iyi bir şablon).
2. **Taban seçimi:** `jhu-clsp/mmBERT-small` (140M, MIT, 8K) — CPU latency için birinci tercih; `mmBERT-base` (307M) kalite referansı; `boun-tabilab/TabiBERT` (149M, Apache-2.0, TR-merkezli, 8K) TR-ağırlıklı alternatif; `mdeberta-v3-base` (MIT) kontrol. **PG2 / Gemma / Llama tabanları kullanılmayacak** (lisans).
3. **Veri:** lisansı uyumlu TR setleri + İngilizce injection setlerinin kontrollü çevirisi (kaynak lisansları tek tek kontrol) + mekanik obfuscation augmentation (her iki sınıfa da uygulanmalı, aksi halde model "garip karakter = saldırı" öğrenir) + bol hard-negative (PIGuard'ın over-defense yaklaşımı).
4. **Distilasyon / etiketleme öğretmeni:** yalnızca **Apache-2.0** öğretmenler — Qwen3Guard-Gen-8B (jailbreak etiketi), gpt-oss-safeguard-20b (Türkçe yazılmış injection politikasıyla), Granite Guardian (EN alt-küme). **Llama Guard / Prompt Guard / Nemotron-3.5 (Gemma) / ShieldGemma çıktılarıyla eğitme**: Llama lisansı türeve "Llama" ad önekini zorunlu kılıyor; Gemma Terms sentetik-çıktı ile eğitilen modeli "Model Derivative" sayıyor. Öğretmen etiketleri insan gözden geçirmesiyle örneklenmeli (Türkçe kalitesi öğretmenlerde de doğrulanmamış).
5. **Çıktı:** ONNX (fp32 + int8 dinamik quant), 512–2048 token pencereleme, kalibre edilmiş olasılık (temperature scaling), model kartında held-out-source sonuçları, seed varyansı ve hard-benign FPR. Hedef latency: tek CPU çekirdek grubu ile p95 < 50 ms / 512 token [ÇIKARIM: halilneed'in i5-12400F'te 307M için ~35 ms ortalamasından türetilmiş hedef; Battal donanımında ölçülmeli].
6. **Content safety (sonraki faz):** önce Qwen3Guard-Gen-0.6B'yi (yerel, Apache) ve adapter üzerinden 4B/8B'yi RTP-LX Türkçe alt-kümesi + Battal TR output seti ile ölç; yetersizse aynı encoder tabanında çok-etiketli TR content-safety sınıflandırıcısı distile et (öğretmen: Qwen3Guard-8B / gpt-oss-safeguard). Türkçe küfür/hakaret için Overfit-GM / cagrigungor modelleri yardımcı sinyal.

### 5.4 Açık belirsizlikler
- Prompt Guard 2'nin Türkçe performansı **ölçülmemiş** (hiçbir kaynakta yok) — Battal ilk eval'de ölçmeli.
- Qwen3Guard eğitim verisinin çevrildiği 15 dilin listesi raporda yok; Türkçe eğitimde var mı **doğrulanamadı**.
- wolf-defender eğitim verisinde Türkçe oranı **doğrulanamadı**.
- halilneed modelinin sonuçları tek kaynak, küçük test, seed hassas; uzun vadeli bakım belirsiz.
- Sentinel v2'nin "Elastic license" tam metni card'da yok → kesin kısıtlar **doğrulanamadı**.
- OpenGuardrails 4B-0124 tabanı (Qwen2.5-7B etiketi vs 4B parametre) tutarsız.
- Tüm CPU latency rakamları (halilneed hariç) **ölçülmedi**; Battal'ın 14GB RAM dev makinesinde benchmark gerekli.
- Bu notta lisans yorumları hukuki görüş değildir; Llama/Gemma/NVIDIA şartları dağıtım modeline (self-host imaj, SaaS) göre hukuki incelemeden geçmeli.
