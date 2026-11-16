# 01 — Guardrail orkestrasyon framework'leri ve policy engine'ler (Battal araştırması)

- Tarih: 2026-11-16
- Kapsam: (1) guardrail ve safety orkestrasyon framework'leri, MCP/agent security gateway'leri; (2) policy engine ve action authorization bileşenleri.
- Yöntem: GitHub API (`gh api repos/...`, releases, commits, code search), PyPI JSON API, Hugging Face API ve model card'ları, arXiv abstract sayfaları ve resmî README dosyaları. Bakım ve lisans verileri **2026-11-16 tarihinde canlı olarak** çekildi.
- Etiketler: **[Geliştirici iddiası]** = projenin kendi dokümanı veya paperı. **[Bağımsız ölçüm]** = üçüncü tarafın ölçümü. **[Çıkarım]** = bu raporun yorumu. "doğrulanamadı" = birincil kaynakta bulunamadı.
- Türkçe kanıtı kuralı: "multilingual" veya "119 dil" gibi ifadeler Türkçe kanıtı sayılmadı. Yalnızca açık "Turkish/tr" ifadesi kanıt kabul edildi. Ayrıca bu repolarda `Turkish` için GitHub code search yapıldı: NeMo-Guardrails, PurpleLlama, guardrails, llm-guard, fms-guardrails-orchestrator, invariant, openguardrails ve OpenGuardrailsBench repolarının **hiçbirinde** eşleşme çıkmadı (her biri 0 sonuç).

---

## 0. Yönetici özeti (TL;DR)

1. **Hiçbir guardrail framework'ünde açık Türkçe desteği kanıtı yok.** Doğrudan dil listesi veren model kartları Türkçeyi açıkça **dışarıda** bırakıyor: Llama Prompt Guard 2 (en, fr, de, hi, it, pt, es, th) ve Nemotron Safety Guard 8B v3 (9 dil ve 20+ dil zero-shot; listede `tr` yok). Battal'ın Türkçe odaklı detection katmanını **kendimiz yazmamız** gerekiyor. Bu, projenin varlık nedenini de doğruluyor.
2. **Framework'leri runtime bağımlılığı olarak almıyoruz.** NeMo Guardrails (Colang, LLM-merkezli, telemetri varsayılan olarak açık), Guardrails AI (Hub 25 Ağustos 2026'da kapatıldı) ve LlamaFirewall (Ağustos 2025'ten beri PyPI release'i yok, torch ağır) Battal'ın "CPU-first, evaluation API" modeline uymuyor. **LLM Guard 2026'da arşivlendi.** Mimari ve scanner fikirleri için referans olarak kullanılabilirler.
3. **Entegrasyonun asıl kaldıracı LiteLLM `generic_guardrail_api`.** LiteLLM, kendi kodunda bir "Generic Guardrail API" sözleşmesi tanımlıyor: `input_type`, `texts`, `structured_messages`, `tools`, `tool_calls` alanları ve `action: NONE|BLOCKED|GUARDRAIL_INTERVENED` yanıtı. Battal ilk sürümde **bu sözleşmeyi uygulamalı**; böylece LiteLLM'e PR göndermeye gerek kalmıyor. İkinci seçenek: LiteLLM'in `ibm_guardrails` hook'u FMS **Detector API**'yi doğrudan çağırabiliyor.
4. **Policy:** MVP için **kendi küçük YAML policy evaluator'ımızı** bir `PolicyEngine` interface'i arkasında yazıyoruz. Tool-call authorization fazı için birincil aday **Cedar** (`cedarpy`, Apache-2.0, in-process, Rust). Cedar ekibinin `cedar-for-agents` reposu MCP tool şemasından Cedar şeması üretiyor. **OPA/Rego** opsiyonel ikinci adapter olarak sidecar biçiminde kalıyor. OpenFGA ve Casbin MVP'de kapsam dışı.

---

## 1. Karşılaştırma tablosu — Guardrail / orkestrasyon framework'leri

| Aday | Görev | Türkçe kanıtı | Son release / aktivite (2026-11-16) | Lisans (kod / model) | Offline | LiteLLM entegrasyonu | Battal kararı |
|---|---|---|---|---|---|---|---|
| NVIDIA NeMo Guardrails | Programlanabilir rails (Colang), input/output/dialog/tool rails, sunucu | Yok (code search: 0) | v0.24.1, 2026-09-16; günlük commit | Apache-2.0 / NemoGuard modelleri NVIDIA Open Model License | Evet; telemetri opt-out gerekli | Yerleşik hook doğrulanamadı | **Out of scope** (dependency olarak); referans |
| Guardrails AI | Validator tabanlı Guard (input/output, structured output) | Yok | v0.11.0, 2026-08-14; son commit 2026-08-26 | Apache-2.0 / validator'a göre değişiyor | Evet (Hub sonrası yerel) | Var (`guardrails_ai` hook) | **Out of scope**; validator'larla interop opsiyonel |
| Protect AI LLM Guard | Input/output scanner seti (PI, PII, toxicity…) | Yok | **ARŞİVLENDİ**; PyPI 0.3.16, 2025-05-19 | MIT / PI modeli Apache-2.0 (yalnızca `en`) | Evet | Yok (hook listesinde değil) | **Reddedildi**; yalnızca ONNX DeBERTa pipeline'ına referans |
| Meta LlamaFirewall (PurpleLlama) | Agent firewall: PromptGuard2 + AlignmentCheck + CodeShield + regex | Yok; PG2 dil listesinde `tr` yok | PyPI 1.0.3, 2025-05-29; son commit 2026-10-30 (tip düzeltmeleri) | Kod MIT / PG2 HF `license:other` (Llama) | Kısmen (AlignmentCheck LLM API istiyor) | Yok | **Out of scope**; scanner arayüzü fikir kaynağı |
| OpenGuardrails | (2025) LLM-tabanlı guard platformu; (2026) Node CLI ile agent tool-call gate'ine pivot etti | Yok ("119 dil" iddiası) | GitHub release yok; son commit 2026-11-04; PyPI `openguardrails` 0.2.0, 2026-08-11 | Apache-2.0 / orijinal HF modelleri **kaldırılmış** | CLI yerel; model API'si henüz yayımlanmamış | Yok | **Reddedildi** (kararsız yön, modeller erişilemez) |
| FMS Guardrails Orchestrator (IBM / TrustyAI) | Rust orkestratör: detector server'ları ve chunker'ları çağırır | Yok | 0.18.4, 2026-10-15; aktif | Apache-2.0 | Evet | **Var** (`ibm_guardrails`, Detector API) | **Build adapter**: Detector API uyumlu endpoint (P1) |
| TrustyAI guardrails-detectors | FMS'e uygun HF/regex detector server'ları | Yok | v0.3.0, 2025-05-22; 3 yıldız | Apache-2.0 | Evet | `ibm_guardrails` üzerinden dolaylı | **Out of scope** |
| Invariant Guardrails (Snyk) | Kural dili (tool-call flow), MCP/LLM proxy | Yok | PyPI `invariant-ai` 0.3.5, 2025-07-28; son commit 2026-01-12 | Apache-2.0 | Evet (kütüphane) | Yok | **Out of scope**; kural dili tasarım referansı |
| Snyk Agent Scan (eski mcp-scan) | Agent/MCP/skill tarayıcı (statik ve hook) | Yok | `snyk-agent-scan` 0.6.11, 2026-11-06 | Apache-2.0 | **Hayır** (Snyk API, free-tier günlük limit) | Yok | **Out of scope** |
| IBM ContextForge MCP Gateway | MCP/A2A/REST gateway, plugin framework, Unified PDP (OPA, Cedar, RBAC, MAC) | Yok | v1.1.1, 2026-11-10 | Apache-2.0 | Evet | — | **Build adapter** (sonraki faz): Battal external plugin |
| agentgateway (LF) | Agent ve MCP proxy, CEL RBAC, guardrail webhook | Yok | v1.7.0, 2026-10-27 | Apache-2.0 | Evet | — | **Build adapter** (sonraki faz): custom webhook |

## 2. Karşılaştırma tablosu — Policy engine'ler

| Aday | Model | Python'a gömülebilirlik | Son release | Lisans | Latency kanıtı | Battal kararı |
|---|---|---|---|---|---|---|
| **Cedar** | PARC (principal/action/resource/context), RBAC+ABAC, statik analiz, Lean ile doğrulanmış | `cedarpy` (topluluk, PyO3, in-process): 4.12.2, 2026-10-14 | Core v4.15.0, 2026-11-16 | Apache-2.0 | [Geliştirici iddiası] paper: Rego ve OpenFGA'dan "far better" | **Configure + adapter** (tool-call authZ fazı, birincil) |
| cedar-for-agents | MCP tool açıklamasından Cedar şeması üretici | PyPI `cedar-policy-mcp-schema-generator` | v0.7.0, 2026-10-22 | Apache-2.0 | — | **Use as-is** (MCP fazında) |
| **OPA / Rego** | Genel amaçlı policy, Go server/sidecar, WASM | REST sidecar; in-process için `regopy` (rego-cpp, MIT, 1.5.2) veya `regorus` (MIT; PyPI'de yok) | OPA v1.22.4, 2026-11-12 | Apache-2.0 | [Geliştirici iddiası, regorus README]: regorus RVM, Cedar'dan 1.35–2.15x hızlı | **Build adapter** (opsiyonel, kurumsal müşteriler için) |
| OpenFGA | Zanzibar/ReBAC, ayrı Go server ve DB | Yalnızca SDK (`openfga-sdk` 0.10.6); server ayrı | v1.22.1, 2026-10-28 | Apache-2.0 | doğrulanamadı | **Out of scope** (MVP); ReBAC gerekirse yeniden değerlendirilecek |
| Casbin (pycasbin) | ACL/RBAC/ABAC model.conf + policy CSV/DB | Saf Python, in-process | v2.8.0, 2026-02-02; repo artık `apache/casbin-pycasbin` | Apache-2.0 | doğrulanamadı | **Out of scope** (yedek seçenek) |

---

## 3. Aday bazında notlar — Guardrail framework'leri

### 3.1 NVIDIA NeMo Guardrails
- **Görev:** LLM uygulamalarına "programmable rails" ekler: input, output, dialog (Colang 1.0/2.0), retrieval ve tool-call/tool-result rails. Python API ve `nemoguardrails server` HTTP sunucusu sunar. https://github.com/NVIDIA/NeMo-Guardrails#readme
- **Türkçe:** Açık kanıt yok; repoda "Turkish" için code search 0 sonuç verdi. Önerilen güvenlik modeli Llama-3.1-Nemotron-Safety-Guard-8B-v3 "9 languages: English, Spanish, Mandarin, German, French, Hindi, Japanese, Arabic, Thai" destekliyor, zero-shot listesi ise "en, ar, de, es, fr, hi, ja, th, zh, it, ko, nl, cs, da, fi, iw, pt-BR, pl, ru, sv". **Türkçe ikisinde de yok.** https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3
- **Bakım:** v0.24.1, 2026-09-16 (https://github.com/NVIDIA/NeMo-Guardrails/releases). Son commit 2026-11-16. Örnek: `fix(jailbreak)!: fail closed when the detector is unavailable` (2026-11-13). Sahibi NVIDIA. README'ye göre 0.25.0 sürümünden itibaren Python 3.10 desteği bırakılıyor ve 3.11–3.13 gerekiyor.
- **Lisans:** Kod Apache-2.0. `LICENSE.md` içinde SPDX başlığı var; GitHub bunu NOASSERTION gösteriyor çünkü birden fazla lisans dosyası bulunuyor. https://github.com/NVIDIA/NeMo-Guardrails/blob/develop/LICENSE.md. Modeller ayrı: NemoGuard-JailbreakDetect ve Nemotron Safety Guard **NVIDIA Open Model License** (+ Llama 3.1 Community License) altında. https://huggingface.co/nvidia/NemoGuard-JailbreakDetect
- **On-prem/offline:** Çalışıyor. Ancak **anonim kullanım telemetrisi varsayılan olarak açık**; kapatmak için `NEMO_GUARDRAILS_NO_USAGE_STATS=1` veya `DO_NOT_TRACK=1` gerekiyor (README "telemetry" bölümü). [Çıkarım] Air-gapped Türk kurumlarında bu ayar mutlaka yapılmalı.
- **Bağımlılıklar:** Async Python. Çoğu rail bir LLM çağrısı gerektiriyor (self-check, content safety). LangChain opsiyonel. JailbreakDetect modeli snowflake-arctic-embed-m-long embedding'i ve Random Forest kullanıyor.
- **Entegrasyon:** Python lib, HTTP server, Docker. LiteLLM'in guardrail hook dizininde NeMo'ya özel bir hook yok (https://github.com/BerriAI/litellm/tree/main/litellm/proxy/guardrails/guardrail_hooks). Yerleşik LiteLLM entegrasyonu: doğrulanamadı.
- **Performans:** README, "ABC Bot" örneği için bir koruma oranı tablosuna işaret ediyor [Geliştirici iddiası]. Bağımsız latency ölçümü: doğrulanamadı.
- **Kısıtlar:** Colang öğrenme eğrisi; LLM-in-the-loop maliyeti ve gecikmesi; diyalog odaklı tasarım. Battal'ın "stateless evaluation API" modeline uymuyor.
- **Karar: Out of scope (dependency olarak).** Battal'ın deterministik ve CPU-first çekirdeğine LLM-merkezli bir orkestratör eklemek gereksiz karmaşıklık getirir. "Fail closed when detector unavailable" ve rail kategorileri (input/output/tool call/tool result) tasarım referansı olarak alınmalı.

### 3.2 Guardrails AI
- **Görev:** `Guard` nesnesi ve validator'larla input/output doğrulama, structured output. https://github.com/guardrails-ai/guardrails
- **Türkçe:** Yok (code search 0).
- **Bakım:** v0.11.0, 2026-08-14 (PyPI). Son commit 2026-08-26, yaklaşık 3 aydır sessiz. **Önemli değişiklik:** Guardrails Hub (`guardrails hub install`, `pypi.guardrailsai.com`) ve hosted remote inference **25 Ağustos 2026'da kapatıldı**; validator'lar artık `guardrails-ai-<name>` adıyla public PyPI'da yayımlanıyor. Issue'ya göre "50 of the 64 validators are available on PyPI". https://github.com/guardrails-ai/guardrails/issues/1560
- **Lisans:** Apache-2.0 (kod). Validator modellerinin lisansları validator'a göre değişiyor; doğrulanamadı.
- **Offline:** Hub kapandıktan sonra validator'lar yerel çalışıyor (remote inference artık yok).
- **Entegrasyon:** Python lib ve `guardrails-api` server. LiteLLM'de `guardrails_ai` hook'u **mevcut** (yukarıdaki LiteLLM dizini).
- **Performans:** doğrulanamadı.
- **Kısıtlar:** Ekosistem geçiş döneminde; validator kalitesi heterojen; Türkçe validator yok.
- **Karar: Out of scope.** Rakip konumda bir orkestratör; Battal'a değer katmıyor. [Çıkarım] İleride Battal detector'larını bir `guardrails-ai-battal` validator paketi olarak yayımlamak dağıtım kanalı olabilir (düşük öncelik).

### 3.3 Protect AI LLM Guard
- **Görev:** Input/output scanner kütüphanesi: PromptInjection (DeBERTa), Anonymize (Presidio), Toxicity, Secrets ve diğerleri. ONNX desteği var.
- **Türkçe:** Yok. PI modeli `protectai/deberta-v3-base-prompt-injection-v2` için HF `language: ['en']`, lisans Apache-2.0. https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2
- **Bakım:** **Repo arşivlendi** (`archived: true`). README: "THIS PROJECT HAS BEEN ARCHIVED… and its associated models on Hugging Face… are no longer under active development". https://github.com/protectai/llm-guard. Son PyPI sürümü 0.3.16, 2025-05-19.
- **Lisans:** MIT (kod).
- **Karar: Reddedildi** (arşivlendi, Türkçe yok). [Çıkarım] Scanner'lara ayrılmış "input/output scanner + ONNX inference" kod düzeni, Battal'ın ONNX classifier pipeline'ı için iyi bir okuma kaynağı; kod MIT olduğu için parça alınırsa atıf yeterli.

### 3.4 Meta LlamaFirewall (PurpleLlama)
- **Görev:** Agent'lar için "final layer of defense". Bileşenler: PromptGuard 2 (BERT-style jailbreak/PI classifier), AlignmentCheck (CoT auditor, LLM tabanlı, deneysel), CodeShield (Semgrep ve regex), özel regex/LLM scanner'ları. Paper: https://arxiv.org/abs/2505.03574. README: https://github.com/meta-llama/PurpleLlama/tree/main/LlamaFirewall
- **Türkçe:** Yok. Llama-Prompt-Guard-2-86M HF dil etiketleri: en, fr, de, hi, it, pt, es, th; **tr yok**. https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
- **Bakım:** PyPI `llamafirewall` 1.0.3, 2025-05-29; o tarihten beri release yok. `LlamaFirewall/` dizinindeki son commit'ler 2026-10-30 ve 2026-08 tarihli; içerik Pyrefly tip bastırma ve unused import temizliği. [Çıkarım] Proje bakım modunda, yeni özellik gelmiyor.
- **Lisans:** `LlamaFirewall/LICENSE` **MIT**. Dikkat: PurpleLlama kök `LICENSE` dosyası **Llama 3.2 Community License**. https://github.com/meta-llama/PurpleLlama/blob/main/LICENSE. Prompt Guard 2 ağırlıkları HF'de `license:other` ve `llama4` etiketli; [Çıkarım] Llama 4 Community License (gated model). Kesin metin doğrulanamadı.
- **Offline:** PromptGuard ve CodeShield yerel çalışıyor (modeller HF'den indiriliyor). AlignmentCheck bir LLM API'si istiyor; pyproject'te `openai` bağımlılığı var.
- **Bağımlılıklar:** `torch>=2.4.1`, `transformers`, `huggingface_hub`, `codeshield`, `openai` (pyproject.toml). [Çıkarım] Battal'ın hafif ONNX hedefi için fazla ağır.
- **Performans:** Paper'da "PromptGuard 2… clear state of the art" [Geliştirici iddiası]. Bağımsız ölçüm: doğrulanamadı.
- **Karar: Out of scope.** Türkçe kapsamı yok, gated Llama lisanslı ağırlıklar Battal'ın Apache-2.0 dağıtımına sorun çıkarabilir ve paket ağır. Scanner/Trace soyutlaması, Battal'ın ileride agent trace değerlendirmesi için tasarım referansı.

### 3.5 OpenGuardrails
- **Görev:** 2025'teki sürüm, LLM tabanlı birleşik bir guard (content safety + prompt attack + data leakage) ve gateway idi. Paper (arXiv 2510.19169) "supports 119 languages" ve "14B → 3.3B GPTQ" diyor [Geliştirici iddiası]. https://arxiv.org/abs/2510.19169
- **2026 durumu:** Repo tamamen yeniden yazılmış: "AI agent guardrails for every builder. Local rules, a sandbox and a firewall for your agents". Node 22 CLI, tool-call gate olarak çalışıyor. README'de "The model API is not public yet" ve "The package is not on npm yet" yazıyor. https://github.com/openguardrails/openguardrails. PyPI `openguardrails` 0.2.0 (2026-08-11) bir "OGR reference runtime — GuardEvent to Verdict" protokol paketi.
- **Modeller:** `openguardrails/OpenGuardrails-Text-2510` ve `-4B-0124` HF sayfaları **401 dönüyor**; bir mirror kartı "The original repository is no longer available on Hugging Face" diyor. https://huggingface.co/kekwak/OpenGuardrails-Text-4B-0124-mirror. Ağırlık lisansı Apache-2.0 [Geliştirici iddiası].
- **Türkçe:** "119 dil" iddiası var ama **açık Türkçe değerlendirmesi yok**; bu Türkçe kanıtı sayılmaz.
- **Karar: Reddedildi.** Yön ani biçimde değişti, orijinal modeller resmî kaynaktan kaldırıldı ve GPU gerektiren 3–4B LLM'ler CPU-first MVP'ye uymuyor. Takip edilebilecek tek şey: OpenGuardrailsBench (Apache-2.0, 2026-11-06 aktif) Türkçe benchmark eklerse değerlendirme verisi kaynağı olabilir.

### 3.6 FMS Guardrails Orchestrator (IBM / TrustyAI)
- **Görev:** Rust ile yazılmış orkestratör sunucu. Generation input/output üzerinde **detector server'larını** (ve chunker'ları) çağırıyor, standalone detection endpoint'leri sunuyor. **Orchestrator API** ve **Detector API** OpenAPI ile tanımlı. https://github.com/foundation-model-stack/fms-guardrails-orchestrator, https://foundation-model-stack.github.io/fms-guardrails-orchestrator/?urls.primaryName=Detector+API
- **Türkçe:** Yok (orkestratör dilden bağımsız; detector'lara bağlı).
- **Bakım:** 0.18.4, 2026-10-15; son commit 2026-11-04. Sahibi foundation-model-stack (IBM); Red Hat OpenShift AI / TrustyAI tarafında kullanılıyor. TrustyAI tarafı: [Çıkarım] trustyai-explainability org'u.
- **Lisans:** Apache-2.0.
- **Entegrasyon:** **LiteLLM `ibm_guardrails` hook'u** hem detector server'ı doğrudan (`is_detector_server: true`) hem de orkestratörü çağırabiliyor; `detector_id`, `score_threshold` ve `block_on_detection` parametreleri var. https://github.com/BerriAI/litellm/blob/main/litellm/proxy/guardrails/guardrail_hooks/ibm_guardrails/example_config.yaml
- **Karar: Build adapter (P1).** Battal'ın bir FMS **Detector API uyumlu** endpoint sunması iki kapıyı aynı anda açar: LiteLLM'deki `ibm_guardrails` ile çalışır ve OpenShift AI / TrustyAI kullanıcıları Battal'ı detector olarak takabilir. Orkestratörün kendisini kullanmıyoruz.
- **TrustyAI guardrails-detectors:** v0.3.0, 2025-05-22; 3 yıldız. https://github.com/trustyai-explainability/guardrails-detectors. **Out of scope** (düşük aktivite); yalnızca Detector API'nin örnek implementasyonu olarak okunabilir.

### 3.7 Invariant Guardrails ve Snyk Agent Scan (eski Invariant Labs)
- **Görev:** Invariant Guardrails, Python'a benzeyen bir kural dili sunuyor. Tool-call akışlarını eşleştiriyor (ör. `(call: ToolCall) -> (call2: ToolCall)`) ve MCP/LLM proxy olarak konumlanıyor. https://github.com/invariantlabs-ai/invariant
- **Bakım:** `invariant-ai` 0.3.5, 2025-07-28. Son commit 2026-01-12 ("moving docs"). Invariant Gateway'in son commit'i 2025-11-06. `invariantlabs-ai/mcp-scan` artık **`snyk/agent-scan`'e yönleniyor**, yani sahiplik Snyk'e geçmiş: https://github.com/snyk/agent-scan. [Çıkarım] Guardrails kütüphanesi fiilen bakımsız; yatırım Snyk ürünlerine kaydırılmış.
- **Snyk Agent Scan:** 0.6.11, 2026-11-06. README, CLI çıktısının "experimental" olduğunu belirtiyor; free-tier'da günlük kullanım limiti var (2026-11-16 commit'i), yani Snyk servisine bağlı. **Offline değil.**
- **Türkçe:** Yok. **Lisans:** Apache-2.0.
- **Karar: Out of scope.** Kural dili, Battal'ın tool-call fazında **flow-based kurallar** (A tool'u çağrıldıktan sonra B tool'u yasak gibi) için en iyi tasarım referansı. Kodu dependency olarak almıyoruz.

### 3.8 MCP / agent security gateway'leri (sonraki fazlar için)
- **IBM ContextForge** (`IBM/mcp-context-forge`): v1.1.1, 2026-11-10, Apache-2.0. Plugin framework'ünde `unified_pdp` var: `tool_pre_invoke` ve `resource_pre_fetch` hook'ları üzerinden "Native RBAC | MAC | OPA | Cedar" motorlarına fan-out ediyor. Ayrıca `plugins/external/{opa,cedar,llmguard}` external plugin'leri var. https://github.com/IBM/mcp-context-forge/tree/main/plugins/unified_pdp. **Karar: Build adapter (MCP fazı).** Battal, `external/llmguard` örneğine benzer bir external plugin olarak takılabilir.
- **agentgateway** (`agentgateway/agentgateway`): v1.7.0, 2026-10-27, Apache-2.0. README: "fine-grained RBAC with CEL policy engine". Guardrails kısmında "regex, OpenAI moderation, AWS Bedrock Guardrails, Google Model Armor, and custom webhooks". **Karar: Build adapter (MCP/A2A fazı)** custom webhook üzerinden.
- **Microsoft mcp-gateway** (MIT, v1.0.1, 2026-11-16) ve **Docker mcp-gateway** (MIT): routing ve yönetim odaklılar. **Lasso mcp-gateway** (MIT, v1.2.0, 2026-01-21; son push 2026-01-22, yavaşlamış). Hepsi **out of scope (MVP)**; MCP fazında entegrasyon hedefi olarak yeniden değerlendirilecek.

### 3.9 Microsoft Presidio (yalnızca orkestrasyon açısından)
- presidio-analyzer 2.2.366, 2026-10-27, MIT. https://github.com/microsoft/presidio. LiteLLM'de yerleşik `presidio.py` hook'u var. PII ayrıntıları diğer agent'ın kapsamında. Orkestrasyon notu: Presidio'nun `RecognizerRegistry` ve custom `PatternRecognizer` modeli TCKN/IBAN recognizer'larını takmak için uygun. [Çıkarım] Battal PII'yi kendi içinde yapacaksa Presidio'ya bağımlı olmadan aynı "recognizer registry" desenini kopyalamak yeterli. **Karar: diğer araştırmaya bırakıldı.**

---

## 4. Aday bazında notlar — Policy engine'ler

### 4.1 Cedar (cedar-policy)
- **Görev:** Authorization policy dili ve motoru (PARC modeli: principal/action/resource/context). Validator ve şema var, Lean ile biçimsel olarak doğrulanmış, analiz edilebilir. https://github.com/cedar-policy/cedar. Paper: https://arxiv.org/abs/2403.04651
- **Bakım:** Core v4.15.0, **2026-11-16** (bugün); çok aktif. Sahibi cedar-policy (AWS kökenli).
- **Python:** `cedarpy` 4.12.2 (2026-10-14), **topluluk** paketi (k9securityio/cedar-py, Apache-2.0, son push 2026-11-02, 70 yıldız). PyO3 ile in-process çalışıyor. https://github.com/k9securityio/cedar-py, https://pypi.org/project/cedarpy/. [Çıkarım] Resmî Python binding yok, bu bir bus-factor riski. Rust core çok stabil olduğu için binding'i fork edip sürdürmek mümkün.
- **Agent'lara özel:** `cedar-policy/cedar-for-agents` (Apache-2.0, `cedar-policy-mcp-schema-generator-v0.7.0`, 2026-10-22). MCP tool açıklamalarından Cedar şeması ve authorization request'i üretiyor; PyPI'de `cedar-policy-mcp-schema-generator` olarak var. https://github.com/cedar-policy/cedar-for-agents
- **Performans:** Paper abstract: "Comparing Cedar to… OpenFGA and Rego… (objectively) performs far better" [Geliştirici iddiası]. Rakip bir taraf olan regorus README'si ise kendi RVM'inin aynı benchmark'larda Cedar'dan 1.35–2.15x hızlı olduğunu iddia ediyor [Geliştirici iddiası, rakip]. Bağımsız ölçüm: doğrulanamadı. [Çıkarım] Her iki iddiaya göre de değerlendirme süresi mikro/milisaniye altı düzeyde; Battal bütçesinde ihmal edilebilir. Kendi benchmark'ımızı yapmalıyız.
- **Kısıtlar:** Türkçe'den bağımsız. Dil bilerek kısıtlı tutulmuş (döngü yok, sınırlı fonksiyon); regex yok, yalnızca `like` var. Prompt içeriğine dayalı kararlar classifier skorlarının `context`'e verilmesiyle yapılmalı.
- **Karar: Configure + adapter (tool-call authorization fazı, birincil).** Apache-2.0, in-process, şema doğrulaması var ve MCP şema üreticisi hazır. YAML policy'den Cedar'a derleme (veya doğrudan Cedar) seçeneği `PolicyEngine` interface'i arkasında sunulmalı.

### 4.2 Open Policy Agent (OPA / Rego)
- **Görev:** Genel amaçlı policy engine; Go server/sidecar, REST API, bundle dağıtımı, WASM derleme. https://github.com/open-policy-agent/opa
- **Bakım:** v1.22.4, 2026-11-12; çok aktif. Lisans Apache-2.0.
- **Python'a gömme seçenekleri:**
  - Sidecar + REST: `opa-python-client` 3.0.0 (2026-09-30, MIT, topluluk: Turall/OPA-python-client). [Çıkarım] Her karar bir yerel HTTP round-trip ekler.
  - `regopy` 1.5.2 (2026-07-06, MIT): Microsoft rego-cpp'nin Python arayüzü, in-process. https://github.com/microsoft/rego-cpp
  - `regorus` (Microsoft, Rust, MIT, regorus-v0.15.0, 2026-11-09): Python binding var ama README "It is not yet available in PyPI, but can be manually built" diyor. README ayrıca "mostly compliant with… OPA v1.2.0… we don't yet support all the builtins" diyor. https://github.com/microsoft/regorus
- **Performans:** regorus README'sindeki hyperfine ölçümünde regorus CLI 4.6 ms, `opa eval` CLI 45.2 ms [Geliştirici iddiası]. [Çıkarım] Bu ölçüm process başlatmayı da içeriyor ve tek değerlendirmenin latency'sini temsil etmiyor.
- **Kısıtlar:** Rego öğrenme eğrisi yüksek. Python için resmî ve in-process bir yol yok. Alternatif implementasyonlar builtin uyumluluğunda eksik.
- **Karar: Build adapter (opsiyonel, P2).** OPA'yı zaten standart olarak kullanan kurumlar için `PolicyEngine` interface'inin bir OPA-sidecar implementasyonu yeterli. Varsayılan engine olmamalı.

### 4.3 OpenFGA
- **Görev:** Zanzibar tarzı ReBAC (ilişki tabanlı) authorization sunucusu; Go ile yazılmış, Postgres/MySQL/SQLite store kullanıyor. https://github.com/openfga/openfga
- **Bakım:** v1.22.1, 2026-10-28; çok aktif. Apache-2.0. Python SDK `openfga-sdk` 0.10.6 (2026-11-12) yalnızca bir client.
- **Kısıtlar:** In-process kullanılamıyor; ayrı bir servis ve veritabanı gerekiyor. Tool-call kararları (ABAC + context) için ReBAC birincil model değil.
- **Karar: Out of scope (MVP).** [Çıkarım] Çok kiracılı, "kim hangi agent'ın hangi tool'unu kullanabilir" tipinde ilişki grafiği gerekirse yeniden değerlendirilecek.

### 4.4 Casbin (pycasbin)
- **Görev:** PERM model.conf ve policy (CSV/DB adapter) ile ACL/RBAC/ABAC. Saf Python, in-process.
- **Bakım:** v2.8.0, 2026-02-02 (yaklaşık 9 aydır release yok); son push 2026-11-15. Repo `apache/casbin-pycasbin` adresine taşınmış. https://github.com/apache/casbin-pycasbin. Apache-2.0. Not: eski PyPI `casbin` adının son sürümü 1.43.0 (2025-05-10); güncel paket adı `pycasbin`.
- **Kısıtlar:** Şema doğrulaması ve statik analiz yok. ABAC ifadeleri string `eval` tabanlı. [Çıkarım] Güvenlik ürünü için denetlenebilirliği Cedar'dan zayıf.
- **Karar: Out of scope** (Cedar yetersiz kalırsa yedek seçenek).

---

## 5. LiteLLM entegrasyonu — kritik bulgu

- LiteLLM'in guardrail hook dizininde 60'tan fazla entegrasyon var (aporia, lakera, presidio, guardrails_ai, ibm_guardrails, tool_permission, tool_policy, mcp_security, **generic_guardrail_api** ve diğerleri). https://github.com/BerriAI/litellm/tree/main/litellm/proxy/guardrails/guardrail_hooks. LiteLLM'in son release'i v1.109.1, 2026-11-12.
- **`generic_guardrail_api`:** `api_base` değerine `/beta/litellm_basic_guardrail_api` path'ini ekleyerek POST atıyor. Konfigürasyon: `mode: pre_call | post_call | during_call`, `unreachable_fallback: fail_closed | fail_open`, `fail_on_error`, `num_retries`, streaming için `streaming_end_of_stream_only`, `streaming_sampling_rate` (varsayılan her 5 chunk) ve `streaming_transform_mode: block_only | incremental_diff`. https://github.com/BerriAI/litellm/blob/main/litellm/proxy/guardrails/guardrail_hooks/generic_guardrail_api/example_config.yaml
  - Request alanları: `input_type` ("request"|"response"), `texts`, `structured_messages`, `images`, `tools`, `tool_calls`, `model`, `request_data` (API key hash, team id ve benzeri metadata), `litellm_call_id`, `litellm_trace_id`, `additional_provider_specific_params`.
  - Response alanları: `action` (koddaki varsayılan `NONE`; `BLOCKED`, `GUARDRAIL_INTERVENED`), `blocked_reason`, değiştirilmiş `texts` (maskeleme için), `structured_messages`, `tools`, `stream_holdback_chars`. https://github.com/BerriAI/litellm/blob/main/litellm/types/proxy/guardrails/guardrail_hooks/generic_guardrail_api.py
  - [Çıkarım] Bu sözleşme Battal MVP'sinin ihtiyaçlarını doğrudan karşılıyor: PI tespiti `BLOCKED` ile, PII maskeleme `GUARDRAIL_INTERVENED` ve değiştirilmiş `texts` ile karşılanıyor. `tool_calls` alanı sonraki tool-call authorization fazını, streaming parametreleri de streaming fazını taşıyabilir. **LiteLLM'e kod katkısı gerekmiyor.** Endpoint path'inin `/beta/` altında olması, sözleşmenin değişebileceği anlamına geliyor; versiyon pinleme ve contract testi gerekli.
- **`ibm_guardrails`:** FMS Detector API veya Orchestrator API'yi çağırıyor (bkz. 3.6). Bu, Battal için ikinci uyumluluk yüzeyi.
- **`tool_permission` / `tool_policy`:** LiteLLM'in kendi yerleşik tool kısıtlama hook'ları. [Çıkarım] Battal'ın tool-call authorization'ı bunlarla rekabet etmek yerine Türkçe bağlam ve Cedar policy ile fark yaratmalı; içerikleri bu raporda incelenmedi (doğrulanamadı).

---

## 6. Battal için öneri

**Mimari karar:** Battal kendi ince orkestrasyon katmanını yazıyor (**build ourselves**). Mevcut framework'lerin hiçbiri (a) Türkçe destek, (b) CPU-first ONNX ve (c) stateless evaluation API kombinasyonunu sağlamıyor; en güçlü adaylardan LLM Guard arşivlendi, OpenGuardrails pivot etti, LlamaFirewall durgun. Yazacağımız orkestratör sade olacak: `Detector` interface (input/output, skor ve span) → `PolicyEngine` interface (karar) → `Action` (allow / block / mask / flag).

| Bileşen | Karar | Gerekçe |
|---|---|---|
| Orkestrasyon çekirdeği | **Build ourselves** | Hafif, deterministik, CPU-first; dış framework yükü yok. Tasarım referansları: NeMo rail kategorileri ve fail-closed yaklaşımı, LlamaFirewall Scanner/Trace, LLM Guard scanner düzeni. |
| LiteLLM entegrasyonu | **Use as-is** (`generic_guardrail_api` sözleşmesini uygulamak) | LiteLLM'e PR gerekmiyor; mask/block/streaming/tool_calls alanları hazır. Contract testi yazılmalı ve LiteLLM sürümü pinlenmeli. |
| FMS Detector API uyumluluğu | **Build adapter (P1)** | LiteLLM `ibm_guardrails` + OpenShift AI/TrustyAI ekosistemi; düşük maliyetli ikinci kapı. |
| MVP policy | **Build ourselves** (YAML → küçük evaluator, `PolicyEngine` interface'i arkasında) | MVP kuralları (eşik, kategori → aksiyon, kiracı override) için Cedar/OPA gereksiz karmaşıklık getirir. |
| Tool-call authorization (faz 2) | **Configure + adapter: Cedar** (`cedarpy`), MCP için `cedar-for-agents` şema üretici | Apache-2.0, in-process, şema doğrulaması ve biçimsel analiz var, agent'lara özel araçları mevcut. Risk: `cedarpy` topluluk paketi; gerekirse fork edilir. |
| OPA desteği | **Build adapter (P2, opsiyonel)** sidecar REST | Kurumsal standardı OPA olan müşteriler için. Varsayılan değil. |
| Flow-based agent kuralları (faz 2+) | **Build ourselves**, Invariant kural dilinden esinlenerek | Invariant bakımsız; fikir değerli (tool A → tool B akış kuralları). |
| MCP gateway entegrasyonu (faz 3) | **Build adapter**: ContextForge external plugin, agentgateway webhook | İkisi de aktif ve Apache-2.0; Battal proxy olmadan değerlendirme servisi olarak kalır. |
| NeMo / Guardrails AI / LlamaFirewall / LLM Guard / OpenGuardrails | **Out of scope / reddedildi** | Bkz. bölüm 3. |

**Türkçe:** Değerlendirilen hiçbir bileşen Türkçe PI/jailbreak tespiti sağlamıyor; açıkça listelenen dil setlerinde Türkçe yok. Türkçe classifier ve deterministik kurallar Battal'ın kendi işi (bu, model/veri araştırmasının konusu).

**Lisans uyarıları:** Battal Apache-2.0 olarak dağıtılacağı için aşağıdaki ağırlıklar **bundle edilmemeli**; yalnızca kullanıcı tarafından opsiyonel olarak indirilebilmeli. Llama Prompt Guard 2 (Llama lisansı, gated). NemoGuard ve Nemotron modelleri (NVIDIA Open Model License + Llama 3.1). PurpleLlama kök lisansı (Llama 3.2 Community License) LlamaFirewall koduna değil, repodaki diğer materyale uygulanıyor; LlamaFirewall kodu MIT.

**On-prem notu:** NeMo Guardrails ileride bir adapter ile kullanılırsa telemetri env değişkeniyle kapatılmalı. Snyk Agent Scan offline çalışmıyor.

## 7. Reddedilen alternatifler (özet)

| Alternatif | Neden reddedildi | Kaynak |
|---|---|---|
| Protect AI LLM Guard | Repo ve HF modelleri arşivlendi; PI modeli yalnızca `en` | https://github.com/protectai/llm-guard |
| Protect AI Rebuff | Arşivlendi (son push 2024-08-07) | https://github.com/protectai/rebuff |
| Vigil (deadbits/vigil-llm) | Son push 2024-01-31; bakımsız | https://github.com/deadbits/vigil-llm |
| OpenGuardrails (model platformu) | Node CLI'ya pivot etti, resmî HF modelleri erişilemez, model API'si yayımlanmamış | https://github.com/openguardrails/openguardrails |
| Invariant Guardrails (dependency olarak) | 2025-07'den beri release yok; sahiplik Snyk'e geçti | https://github.com/invariantlabs-ai/invariant |
| Snyk Agent Scan | SaaS'a bağlı, offline değil, çıktı formatı "experimental" | https://github.com/snyk/agent-scan |
| TrustyAI guardrails-detectors | Son release 2025-05, çok düşük aktivite | https://github.com/trustyai-explainability/guardrails-detectors |
| OpenFGA | Ayrı server ve DB gerektiriyor; ReBAC odaklı, MVP için fazla | https://github.com/openfga/openfga |
| Casbin | Şema doğrulaması ve analiz yok; Cedar daha denetlenebilir | https://github.com/apache/casbin-pycasbin |
| Cerbos | Open-core policy server (Go, Apache-2.0, v0.57.0); ayrı servis gerektiriyor, Cedar in-process ile aynı ihtiyacı karşılıyor | https://github.com/cerbos/cerbos |
| SpiceDB | Zanzibar ReBAC server; OpenFGA ile aynı gerekçe | https://github.com/authzed/spicedb |
| permitio/cedar-agent | Son release 0.2.2, 2025-10-16; `cedarpy` in-process daha basit | https://github.com/permitio/cedar-agent |
| regorus (in-process Rego) | PyPI'da yok ("can be manually built"), builtin uyumluluğu eksik | https://github.com/microsoft/regorus |

## 8. Açık belirsizlikler ve sonraki adımlar
- Hiçbir framework veya policy engine için **bağımsız latency ölçümü bulunamadı** (doğrulanamadı). Cedar (`cedarpy`), YAML evaluator ve OPA sidecar için Battal'ın kendi microbenchmark'ı yapılmalı.
- LiteLLM `generic_guardrail_api` endpoint'i `/beta/` path'inde; sözleşme değişikliğini takip etmek için CI'da LiteLLM'in belirli bir sürümüne karşı contract testi çalıştırılmalı.
- Llama Prompt Guard 2'nin kesin lisans metni gated olduğu için okunamadı (HF etiketi `license:other`, `llama4`).
- LiteLLM'in `tool_permission` ve `tool_policy` hook'larının kapsamı incelenmedi; tool-call fazından önce Battal ile örtüşmesi değerlendirilmeli.
- `cedarpy` topluluk paketi: bakımcı riski izlenmeli.
