# 05 — Red teaming / evaluation framework'leri, Türkçe & çok dilli veri setleri, değerlendirme metodolojisi

Battal araştırma notu · 2026-11-16 · kapsam: Türkçe ve Türkçe–İngilizce prompt injection/jailbreak tespiti + PII maskeleme (TCKN, IBAN, telefon, e-posta) için framework, dataset ve benchmark metodolojisi.

**Etiketler:** **[İddia]** = birincil kaynakta yazan ifade (URL yanında) · **[Ölçüm]** = bu araştırmada API/repo üzerinden canlı doğrulanan değer (2026-11-16) · **[Çıkarım]** = benim yorumum/tahminim · **doğrulanamadı** = kaynakta bulunamadı.

Canlı doğrulama yöntemi: GitHub REST API (`gh api repos/<r>` → license SPDX, `pushed_at`, `archived`), PyPI JSON API, npm registry, Hugging Face Hub API (`https://huggingface.co/api/datasets/<id>`), HF datasets-server (`/size`, `/statistics`, `/rows`), dataset README'leri (`/raw/main/README.md`). Büyük dataset indirilmedi.

> **Lisans uyarısı:** Bu belge hukuki görüş değildir. "Yeniden dağıtılabilir" kararları, dataset kartlarındaki lisans beyanına dayanır; kart beyanı ile kaynak verinin gerçek lisansı (ör. tweet, kazınmış web içeriği, LLM çıktısı) çelişebilir. Yayın öncesi her kaynak için `LICENSE` dosyası/kart revizyon hash'i arşivlenmelidir.

---

## 1. Framework'ler

### 1.1 Özet tablo

| Framework | Ana görev | Türkçe / çok dilli kabiliyet (kanıt) | Bakım [Ölçüm, 2026-11-16] | Lisans [Ölçüm] | Offline | Battal guard endpoint'i nasıl takılır | Sınırlamalar | Battal kararı |
|---|---|---|---|---|---|---|---|---|
| **NVIDIA garak** | LLM vulnerability scanner: probe → generator → detector | Probe/detector metinlerini çeviri ile hedef dile taşıma: Helsinki-NLP opus-mt, m2m100 (lokal), DeepL / Riva / Google (remote) [İddia, https://github.com/NVIDIA/garak/blob/main/docs/source/translation.rst]. Kendi limitasyon notu: "strongly coupled to BCP47 code 'en'", HF detector'ları çoğunlukla İngilizce [aynı URL]. Native Türkçe probe yok [Çıkarım: `garak/probes/` altında dil-özel dosya yok, https://github.com/NVIDIA/garak/tree/main/garak/probes] | Aktif: son push 2026-11-06, son release v0.17.1 (2026-10-16), ~10k yıldız (https://github.com/NVIDIA/garak) | Apache-2.0 | Evet (lokal HF/Ollama generator + lokal opus-mt/m2m100 çeviri) | `generators.rest` (REST generator, https://github.com/NVIDIA/garak/blob/main/docs/source/generators/rest.rst) veya `generators.function` ile Python callable; Battal'ı "guarded LLM app" proxy'si olarak hedef göster | Model/uygulama çıktısını puanlar; guard'ı **classifier** olarak (precision/FPR) ölçmez; makine çevirisi Türkçe kalitesi düşük olabilir [Çıkarım] | **Kullan (ikincil):** uçtan uca ASR regresyon taraması + encoding/latentinjection/smuggling probe'ları; Türkçe benchmark'ın yerine geçmez |
| **Microsoft PyRIT** | Red teaming orchestration: target, converter, scorer, multi-turn attack | `translation_converter`, `random_translation_converter`, `diacritic(s)_converter`, `unicode_confusable_converter`, `zero_width_converter`, `token_smuggler_converter`, `leetspeak`, `charswap` vb. [Ölçüm: repo ağacı https://github.com/microsoft/PyRIT/tree/main/pyrit/prompt_converter]; seed dataset loader'ları arasında `aya_redteaming_dataset.py`, `multilingual_vulnerability_dataset.py` [Ölçüm]. Çeviri LLM ile yapılır (Türkçe kalite LLM'e bağlı) [Çıkarım] | Aktif: repo `microsoft/PyRIT` (eski `Azure/PyRIT` **archived**), son push 2026-11-16, PyPI `pyrit` 1.2.0 (2026-11-13) | MIT | Kısmen: converter'ların çoğu deterministik/offline; LLM-tabanlı converter/scorer için lokal OpenAI-uyumlu endpoint gerekir | `HTTPTarget` / `httpx_api_target` (https://github.com/microsoft/PyRIT/blob/main/pyrit/prompt_target/http_target/http_target.py); `prompt_shield_target.py` örneği bir **guard'ın target olarak** nasıl sarılacağını gösterir (Azure Prompt Shield) [Ölçüm: dosya mevcut] | Ağır bağımlılık, API değişkenliği (1.x yeni) [Çıkarım]; skorlama çoğunlukla LLM-judge | **Kullan (birincil, üretim aracı):** Türkçe obfuscation varyantlarının (diakritik silme, confusable, zero-width) deterministik üretimi + Battal guard'ı `PromptShieldTarget` benzeri target olarak saran adaptör |
| **promptfoo** | Eval + red team CLI (YAML), CI entegrasyonu | Global `language: string\|string[]` ayarı tüm plugin/strategy'ler için test üretir [İddia, https://github.com/promptfoo/promptfoo/blob/main/site/docs/red-team/configuration.md]; eski `multilingual` strategy **deprecated** [Ölçüm: `src/redteam/strategies/multilingual.ts` yorum satırı]; `homoglyph`, `leetspeak`, `base64` strategy'leri var | Aktif: son push 2026-11-16, npm 0.125.1 (2026-10-25). OpenAI Mart 2026'da satın aldı, "current license altında open source kalacak" [İddia, https://openai.com/index/openai-to-acquire-promptfoo/ ; https://techcrunch.com/2026/03/09/openai-acquires-promptfoo-to-secure-its-ai-agents/] | MIT | Kısmen: red team üretimi varsayılan olarak remote generation servisi kullanır; `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` ile kapatılır, "lower quality" uyarısıyla [İddia, configuration.md] | HTTP provider (https://github.com/promptfoo/promptfoo/blob/main/site/docs/providers/http.md) ile Battal `/v1/check` endpoint'i; `transformResponse` ile skor/etiket çıkarılır; assertion ile beklenen label kontrolü | Test üretimi LLM'e bağımlı (non-deterministic → reproducible benchmark için uygun değil) [Çıkarım]; vendor yön değişikliği riski (OpenAI) [Çıkarım] | **Kullan (CI regresyon):** sabit Battal test set'ini `tests:` olarak koşturup PR'da FPR/recall eşiği kontrolü; üretici olarak değil |
| **Confident AI DeepTeam** | LLM red teaming (deepeval üstüne), vulnerability × attack matrisi | `multilingual` single-turn attack: LLM'e "low-resource dile çevir" prompt'u; `language` parametresi verilebilir [Ölçüm: https://github.com/confident-ai/deepteam/blob/main/deepteam/attacks/single_turn/multilingual/template.py]. Türkçe-özel bir şey yok | Aktif: push 2026-10-23, PyPI 1.0.10 (2026-10-16) | Apache-2.0 | Kısmen: simulator/evaluator model olarak lokal LLM (`DeepEvalBaseLLM`) takılabilir | Python callback (`model_callback`) içinde Battal'ı çağır | Tüm saldırı üretimi ve skor LLM-judge → yüksek varyans, maliyet [Çıkarım] | **Opsiyonel:** fikir/taksonomi kaynağı; benchmark üretiminde kullanma |
| **Giskard** | v3: agent testing (`giskard-checks`) + `giskard-scan` vulnerability scan | Türkçe/çok dilli özel destek kanıtı bulunamadı (**doğrulanamadı**) | Aktif ama **v3 yeniden yazım**: repo `Giskard-AI/giskard-oss`, push 2026-11-16, PyPI `giskard` 3.0.1; "v2 no longer actively maintained" [İddia, https://github.com/Giskard-AI/giskard-oss] | Apache-2.0 | Kısmen (LLM-judge için provider gerekir); telemetri varsayılan açık, `GISKARD_TELEMETRY_DISABLED=1` [İddia, README] | Target = herhangi bir sync/async callable `(inputs) -> outputs` [İddia, README] | API yeni/oynak; Türkçe kanıt yok | **Kullanma (şimdilik)** |
| **HarmBench** | Harmful behavior benchmark + otomatik red team yöntemleri + classifier (Llama-2-13b-cls) | Yalnızca İngilizce [Çıkarım: behavior set & classifier İngilizce, https://github.com/centerforaisafety/HarmBench] | **Durgun:** son push 2024-08-16 | MIT | Evet | Guard'ı model wrapper'ı içine koy (kod değişikliği) | Jailbreak'in *zararlı içerik üretimi* tarafını ölçer; injection classifier'ı değil | **Referans:** behavior taksonomisi/ASR tanımı için; veri **çevirip** kullanılabilir (MIT) ama çeviri provenance'ı işaretlenmeli |
| **JailbreakBench** | JBB-Behaviors (100 harmful + 100 benign) + artifact repo + judge | İngilizce [Çıkarım] | Durgun: push 2025-04-04; PyPI 1.0.0 | MIT (repo); JBB-Behaviors HF kartı `license:mit` [Ölçüm, https://huggingface.co/api/datasets/JailbreakBench/JBB-Behaviors] | Evet | Defense sınıfı olarak sar (kod) | Küçük, İngilizce; davranış kaynaklarının bir kısmı başka benchmark'lardan [İddia, README] | **Referans:** benign/harmful eşli tasarım fikri (over-refusal ölçümü) |
| **AgentDojo** | Agent + tool-use ortamında indirect prompt injection; utility vs. security | İngilizce görev suit'leri [Çıkarım] | Orta: push 2026-06-02, PyPI 0.1.35 (2025-10-27) | MIT | Evet (lokal model ile) | Agent pipeline'a defense elemanı olarak eklenir; örnek `transformers_pi_detector` run'ları repoda [Ölçüm: https://github.com/ethz-spylab/agentdojo/tree/main/runs ; docs/api/agent_pipeline/defenses.md]. Ayrıca Inspect'e port edilmiş (`inspect_evals/agentdojo`) [Ölçüm] | Türkçe yok; injection'lar İngilizce şablon | **Kullan (Faz 2, agent security):** Battal'ı tool-output filtresi olarak koyup ASR + utility düşüşünü ölç; injection şablonlarını Türkçeleştirilmiş bir "AgentDojo-TR" suit'i ileride |
| **InjecAgent** | Tool-integrated agent IPI benchmark: 1,054 test case, 17 user tool, 62 attacker tool [İddia, https://github.com/uiuc-kang-lab/InjecAgent] | İngilizce | **Durgun:** push 2024-07-02 | MIT | Evet | Tool response'u guard'dan geçiren wrapper (kod) | Statik, tek-turlu; İngilizce | **Referans:** attacker-tool taksonomisi (direct harm / data stealing) |
| **BIPIA** | Indirect prompt injection benchmark (email, QA, table, summarization, code) | İngilizce | **Archived** (`microsoft/BIPIA`, push 2024-04-15) | Kod MIT [Ölçüm: LICENSE dosyası]; GitHub SPDX `NOASSERTION`; WebQA/Summarization verisi "license issues" nedeniyle kullanıcının kaynaktan üretmesi gerekir, "only for research on IPI" [İddia, https://github.com/microsoft/BIPIA] | Evet | Kod düzeyinde | Arşivli; veri kısmen yeniden dağıtılamaz | **Kullanma (veri)**; görev kategorileri (email/table/code içinde gömülü talimat) taksonomiye ilham |
| **Inspect (UK AISI)** | Genel eval framework (task/solver/scorer, sandbox, log viewer) + `inspect_evals` paketleri | Dil-bağımsız altyapı; çok dilli safety eval'i hazır değil [Çıkarım]. `inspect_evals` içinde agentdojo, agentharm, b3, fortress, strong_reject, xstest, cyberseceval_2/3/4 vb. [Ölçüm: https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals] | Çok aktif: push 2026-11-16, PyPI `inspect-ai` 0.3.290 (2026-11-14) | MIT | Evet (lokal model provider'ları, vLLM/Ollama) | Custom model API provider veya solver içinde HTTP çağrısı; scorer olarak Battal etiketi | 0.x sürüm, sık değişen API [Çıkarım] | **Kullan (birincil eval harness):** Battal benchmark'ını Inspect `Task` olarak yayınla → reproducible log (eval log + config + seed) |

### 1.2 Çıkarım: framework'lerin ortak açığı
- Hiçbir framework **native Türkçe** saldırı/benign corpus'u içermiyor; çok dilli destek ya çeviri (garak, PyRIT, DeepTeam) ya da LLM ile yeniden üretim (promptfoo) üzerinden. [Çıkarım, yukarıdaki kanıtlardan]
- Çoğu framework **uçtan uca saldırı başarısını (ASR)** ölçer; bir guard'ın **sınıflandırıcı** olarak precision/recall/FPR'ını ölçmek için ayrı bir harness gerekir. Battal'ın asıl katkısı bu boşluk. [Çıkarım]
- Üretilen saldırılar LLM'e bağlı olduğunda (promptfoo, DeepTeam, PyRIT LLM converter'ları) benchmark **reproducible değildir**; benchmark'a girecek örnekler bir kez üretilip dondurulmalı, seed + model + prompt kayıt altına alınmalı. [Çıkarım]

---

## 2. Veri setleri

### 2.1 Lisans karar anahtarı
- ✅ **Dahil edilebilir** — permissive (CC0, CC-BY-4.0, MIT, Apache-2.0, ODC-BY) ve içerik provenance'ı temiz; atıf + `NOTICE` ile CC-BY-4.0 benchmark içinde yeniden dağıtılabilir. (MIT/Apache içeriğin CC-BY-4.0 paket içinde dağıtımı: orijinal lisans metni + atıf korunmalı; dosya bazında lisans alanı tutulmalı. [Çıkarım])
- ⚠️ **Şartlı** — lisans permissive ama provenance riski (tweet/kazınmış web, LLM-üretimi, makine çevirisi, belirsiz alt-kaynak) veya kart içi çelişki. Yalnız eğitim/iç kullanım veya sadece *ID referansı* ile.
- ❌ **Dahil edilemez** — NC/SA/research-only/unknown/gated-ToS veya CC-BY-4.0 ile uyumsuz.

### 2.2 Çok dilli jailbreak / injection / safety setleri

| Dataset | İçerik | Türkçe var mı (kanıt) | Boyut | Lisans [Ölçüm: HF tag / repo] | Provenance / çeviri | CC-BY-4.0 benchmark içinde? |
|---|---|---|---|---|---|---|
| **MultiJail** `DAMO-NLP-SG/MultiJail` | 315 İngilizce unsafe prompt, 9 dile çevrilmiş [İddia, https://huggingface.co/datasets/DAMO-NLP-SG/MultiJail] | **Hayır** — diller: en, zh, it, vi, ar, ko, th, bn, sw, jv [Ölçüm: HF tags] | n<1K | MIT | İnsan çevirisi/annotasyon [İddia, kart: "annotated into nine non-English languages"; arXiv 2310.06474] | ✅ (ama Türkçe yok; yalnız İngilizce kaynak prompt'ları kendi Türkçe çevirimize temel olabilir, `translated_from` alanıyla) |
| **XSafety** `Jarviswang94/Multilingual_safety_benchmark` | 14 safety kategorisi (Goal_Hijacking, Prompt_Leaking, Role_Play_Instruction dahil) × 10 dil [İddia, https://github.com/Jarviswang94/Multilingual_safety_benchmark; arXiv 2310.00905] | **Hayır** — klasörler: ar, bn, de, en, fr, hi, ja, ru, sp, zh [Ölçüm: repo ağacı] | doğrulanamadı (dosya bazında) | Apache-2.0 (repo) | Kaynak: kısmen Çince safety benchmark'larından, çeviri [Çıkarım; ayrıntı doğrulanamadı] | ⚠️ Lisans uygun; Türkçe yok; alt-kaynak lisansları doğrulanamadı |
| **Aya Red-teaming** `CohereLabs/aya_redteaming` | İnsan-yazımı harmful prompt'lar, 8 dil, 9 zarar kategorisi, global/local etiketi [İddia, kart] | **Hayır** — en, hi, fr, es, ar, ru, sr, tl [Ölçüm] | 1K–10K | Apache-2.0 | Native yazım + literal çeviri alanı [İddia] | ✅ (Türkçe yok) |
| **PolyGuardMix** `ToxicityPrompts/PolyGuardMix` | Prompt/response safety etiketleri, eğitim seti | **Hayır** — 17 dil: ar, zh, cs, nl, en, fr, de, hi, th, it, ja, ko, pl, pt, ru, es, sv [Ölçüm]; makale başlığı "17 Languages" [arXiv 2504.04377] | 1,910,372 satır (train) [Ölçüm: README dataset_info] | CC-BY-4.0 (tag) | Büyük ölçüde mevcut İngilizce setlerin (ör. WildGuardMix) makine çevirisi [Çıkarım; kaynak setlerin lisansları ayrıca bağlayıcı olabilir — doğrulanamadı] | ⚠️ Türkçe yok; alt-kaynak lisans zinciri doğrulanmalı |
| **PolyGuardPrompts** `ToxicityPrompts/PolyGuardPrompts` | PolyGuard test seti | **Hayır** (aynı 17 dil) [Ölçüm] | 10K–100K | CC-BY-4.0 | aynı | ⚠️ Türkçe yok |
| **RTP-LX** `ToxicityPrompts/RTP-LX` / `microsoft/RTP-LX` | RealToxicityPrompts alt kümesinin "human transcreated" çok dilli sürümü + yerel "zor" prompt'lar; toxicity annotasyonu [İddia, https://github.com/microsoft/RTP-LX] | **Evet — `Locale=TR` 1,049 satır** [Ölçüm: datasets-server `/statistics`, test split, toplam 30,253 satır] | 30,253 | HF: ODC-BY; GitHub: MIT + NOTICE'te orijinal RTP için Apache-2.0 [Ölçüm] | Prompt'lar insan transcreation + native annotasyon; completion'lar sentetik [İddia, README]; orijinal RTP metinleri OpenWebText'ten (web) [Çıkarım] | ⚠️ Lisans uygun, ama içerik **toksisite** (injection değil) ve web-kaynaklı. Kullanım: Türkçe **benign-ama-toksik hard negative** (guard "injection" demeli değil). Benchmark'a gömmek yerine HF ID + satır index referansı önerilir |
| **deepset/prompt-injections** | 546 train + 116 test, binary label [Ölçüm: README] | **Hayır**; ayrıca **~100+ Almanca satır** içerir [Ölçüm: train split'te Almanca işaret kelimeli 106 satır, kaba heuristik] | 662 | Kart içi **çelişki**: üst düzey `license: apache-2.0`, `dataset_info` içinde `license: cc-by-4.0` [Ölçüm, https://huggingface.co/datasets/deepset/prompt-injections] | Provenance belgesiz | ⚠️ İki lisans da permissive; çelişki yazılı olarak not edilmeli |
| **Lakera gandalf_ignore_instructions** | Gandalf oyununa gönderilen gerçek kullanıcı prompt'ları; embedding benzerliği ≥0.825 ile filtre, PII filtre, near-dup temizliği, 1000 örnek [İddia, kart] | Hayır | 1K–10K | MIT | **Gerçek kullanıcı trafiği** (oyun) | ⚠️ Lisans MIT ama Battal kuralı "production traffic yok" ruhuna aykırı olabilir [Çıkarım] → yalnız dış test referansı |
| **Lakera mosscap_prompt_injection** | Mosscap oyun prompt'ları | Hayır | 100K–1M | MIT | Gerçek kullanıcı trafiği | ⚠️ aynı |
| **Lakera gandalf_summarization** | Özetleme bağlamında injection | Hayır | n<1K | MIT | Gerçek kullanıcı trafiği | ⚠️ aynı |
| **jackhhao/jailbreak-classification** | Jailbreak vs benign | Hayır | 1K–10K | Apache-2.0 | Jailbreak'ler `verazuo/jailbreak_llms`'ten (Reddit/Discord/web toplanmış), benign GPTeacher'dan [İddia, kart] | ⚠️ Üçüncü taraf topluluk içeriği; yeniden lisanslama hakkı belirsiz |
| **SPML** `reshabhs/SPML_Chatbot_Prompt_Injection` | Sistem prompt'u + saldırı; sızdırılmış sistem prompt'larından GPT-4 ile genişletilmiş [İddia, kart] | Hayır | 10K–100K | MIT | LLM-üretimi; TensorTrust kaynaklı saldırılar "not licensed for distribution" olduğundan dışarıda bırakılmış [İddia, kart] | ⚠️ LLM-üretimi + sızdırılmış sistem prompt'u kökeni |
| **WildJailbreak** `allenai/wildjailbreak` | 262K civarı sentetik vanilla/adversarial harmful+benign [arXiv 2406.18510; sayı **doğrulanamadı** — kart gated] | Hayır (tag: 1 dil) | HF tag 1K–10K (çelişkili; doğrulanamadı) | ODC-BY; **gated: auto** [Ölçüm] | LLM-üretimi | ⚠️ Gated erişim + kullanım şartları → yeniden dağıtma |
| **BIPIA** | Indirect injection (email/table/QA/summarization/code) | Hayır | doğrulanamadı | Kod MIT; veri kısmen kaynak lisansına bağlı, "research only" ifadesi [İddia] | Karışık | ❌ (veri) |
| **JBB-Behaviors** | 100 harmful + 100 benign behavior | Hayır | 200 | MIT | Kısmen başka benchmark'lardan derleme [İddia] | ✅ (Türkçe yok; çeviri için kaynak olabilir) |
| **Aegis 2.0** `nvidia/Aegis-AI-Content-Safety-Dataset-2.0` | Content safety | Hayır [Ölçüm] | 10K–100K | CC-BY-4.0 | — | ✅ (Türkçe yok) |

### 2.3 Türkçe prompt injection / jailbreak setleri (HF'de 2026'da ortaya çıkanlar)

| Dataset | İçerik | Türkçe sayısı | Lisans [Ölçüm] | Provenance | Karar |
|---|---|---|---|---|---|
| **OnerAYTAS/Turkish_prompt_injection_jailbreak_dataset** | ~20.500 Türkçe injection/jailbreak prompt [İddia, kart]; makale: Applied Sciences 2026, 16(13), 6740, https://doi.org/10.3390/app16136740 | ~20.500 [İddia] | **CC-BY-NC-SA-4.0**; kartta `gated: auto` ve "sadece akademik" kullanım şartları [Ölçüm, https://huggingface.co/datasets/OnerAYTAS/Turkish_prompt_injection_jailbreak_dataset] | İngilizce setlerin **makine çevirisi** (translategemma:4b, Google Translate API, DeepL API); kaynaklar: xTRam1/safe-guard-prompt-injection, Yash0728/toxicity_prompt-injection, jackhhao/jailbreak-classification, rogue-security/prompt-injections-benchmark, PromptInjectionDataset/Injection-Attack-Detection-Dataset [İddia, kart]; "az bir kısmı mükerrer" [İddia] | ❌ NC + SA → CC-BY-4.0 ile **uyumsuz**; eğitimde de ticari kullanım engeli. Sadece makaledeki sonuçlara atıf |
| **3nesdeniz/turkish-prompt-injection-1k** | 1,000 Türkçe-native: 550 injection / 450 benign hard negative; 4 aile (agentic_toolabuse 141, instruction_override_extraction 140, obfuscation_exfiltration 136, jailbreak_persona 133); train/val/test 790/97/113, "scenario-isolated, no template leaks" [İddia, kart] | 1,000 | CC-BY-4.0 | İnsan-tasarımı şablon + slot, deterministik genişletme [İddia] | ✅ Dahil edilebilir; **ancak** şablon-tabanlı → Battal split'leriyle aile çakışması kontrol edilmeli. Aynı yazar/şablon stili → yalnızca *dış test* (OOD) olarak tutmak daha doğru [Çıkarım] |
| **3nesdeniz/turkish-conversation-prompt-injection** | 750: 450 doğal benign, 150 güvenlik-yakın benign hard negative, 150 saldırı; her saldırının eşli benign'i; Zenodo DOI 10.5281/zenodo.21379389 [İddia, kart] | 750 | CC-BY-4.0 | Kart metadata: `language_creators: machine-generated` [Ölçüm] | ✅ (LLM-üretimi olduğu not edilmeli); dış test |
| **fevziegeyurtsevenler/turkish-prompt-injection** | 107 kalıp, OWASP/ATLAS eşlemeli, morfolojik bypass, çeviri-bahanesi, code-switch [İddia, kart] | 107 | CC-BY-4.0 | Elle yazım (belirtilmemiş) | ✅ küçük; taksonomi + dış test |
| **beratcmn/turkish-prompt-injections** | `deepset/prompt-injections`'ın Türkçe çevirisi [İddia, kart] | n<1K | Apache-2.0 | Çeviri (yöntem belirtilmemiş; deepset'teki Almanca satırlar da çevrilmiş olabilir — doğrulanamadı) | ⚠️ İngilizce kaynağın çevirisi → İngilizce deepset ile aynı aile; split sızıntısı riski yüksek. Dış test için de deepset-görmüş modellerde şişirilmiş skor verir [İddia, halilneed kartı dipnotu] |
| **hoatac/prompt-injections-turkish** | 546 satır, text/label [Ölçüm: README] | 546 | **Lisans yok** [Ölçüm: tag yok] | deepset train ile aynı satır sayısı (546) → muhtemelen çeviri [Çıkarım] | ❌ (lisanssız) |
| **halilneed/turkish-prompt-injection-benchmark** | 3,372 satır: 317 saldırı (beş public Türkçe setten), 3,055 benign; "No new text was written" [İddia, kart]; üçüncü taraf ölçümler: ör. `proventra/mdeberta-v3-base-prompt-injection` 0.5 eşikte ortalama attack recall 0.865, false alarm %26.9 [İddia — yazarın kendi ölçümü] | 3,372 | `license: other` = "mixed-cc0-cc-by-4.0-apache-2.0", satır bazında `license` alanı [Ölçüm] | Derleme | ⚠️/✅ Bileşenleri permissive; doğrudan ID referansı ile **dış değerlendirme** seti olarak kullan, Battal benchmark'ına kopyalama (çifte sayım/sızıntı) |
| **halilneed/turkish-prompt-injection-false-alarm-benchmark** | 2,875 benign Türkçe (iş metni 1,125, bankacılık 750, PII görev talimatı 1,000); public guard'ların görev talimatlarında %31–77 false alarm verdiği iddiası [İddia, kart] | 2,875 | CC0-1.0 | Bileşenler CC0 sentetik setler | ✅ **Yüksek değer:** Battal FPR testi için hazır hard-negative; Battal'ın PII-masking talimatlarının injection sanılmaması tam bu senaryo |

### 2.4 Türkçe offensive / toxicity / hate setleri (benign-toksik hard negative ve kategori ayrımı için)

| Dataset | İçerik | Boyut | Lisans [Ölçüm] | Provenance | Karar |
|---|---|---|---|---|---|
| **OffensEval 2020 TR / Çöltekin** `coltekin/offenseval2020_tr` | Offensive (OFF/NOT) tweet'ler; eğitim dosyası 31,756 tweet [İddia, kart] | 10K–100K | CC-BY-2.0 (HF tag) | **Twitter/X içeriği** | ⚠️ CC-BY-2.0 permissive ama tweet metni yeniden dağıtımı platform ToS'una tabi [Çıkarım]; benchmark'a gömme, yalnız ID referansı / iç eğitim |
| **Toygar/turkish-offensive-language-detection** | 42,398 train / 8,851 test / 1,756 valid tweet, binary [İddia, kart] | ~53K | CC-BY-2.0 | Mevcut Türkçe offensive setlerin birleşimi + augmentation | ⚠️ aynı tweet riski + alt-kaynak lisans zinciri |
| **Overfit-GM/turkish-toxic-language** | 77,800 örnek; kaynaklar: Jigsaw Multilingual (35,624), Turkish Offensive (39,551), Cyberbullying (2,525); pseudo-label ile augment [İddia, kart] | 77.8K | Apache-2.0 (kart) | **Kaggle Jigsaw yarışma verisi** dahil — yarışma kuralları yeniden dağıtıma genelde izin vermez [Çıkarım; doğrulanamadı] | ❌ "license laundering" riski |
| **ctoraman/large-scale-hate-speech-turkish-v2** | Türkçe hate speech | 10K–100K | **CC-BY-NC-SA-4.0** | Tweet | ❌ |
| **turkish-nlp-suite/TurkishHateMap** | 52K örnek, 13 hedef grup, Ekşi Sözlük'ten kazınmış, Co-one annotasyonu [İddia, kart; arXiv 2512.22100] | 52K | **CC-BY-SA-4.0** | Kazınmış web | ❌ SA → CC-BY-4.0 ile uyumsuz (türev SA olmak zorunda) |

### 2.5 Türkçe NER / PII setleri

| Dataset | İçerik | Boyut | Lisans [Ölçüm] | Provenance | Karar |
|---|---|---|---|---|---|
| **cagrigungor/turkish-pii-masking-benchmark** | 1,000 test: tam 350 / beyaz_liste 200 / kara_liste 150 / kapsam_disi 100 / negatif 200; zor dilimler: ekli PII ("Cem Aslan'ın"), CAPS, sözle yazılmış sayılar, PII-benzeri tuzaklar; 53 mask etiketi [İddia, kart] | 1K | CC0-1.0 | "Fully synthetic, hand-built" [İddia] | ✅ **Doğrudan dahil edilebilir**; Battal PII miss/over-mask metriği için ideal |
| **BTX24/turkish-privacy-pii-ner** | Sentetik, karakter-span etiketli PII NER (isim, e-posta, telefon, adres, IBAN-benzeri, TCKN-benzeri, VKN-benzeri…) [İddia, kart] | 103,923 satır [Ölçüm: datasets-server] | CC-BY-4.0 | `machine-generated`, `synthetic-data` [Ölçüm, kart] | ✅ Eğitim için; "IBAN-like/TCKN-like" → checksum geçerliliği **doğrulanamadı** |
| **fevziegeyurtsevenler/turkish-pii-corpus** | Sentetik, **checksum-geçerli** TCKN/IBAN/VKN/plaka/kart + distractor [İddia, kart] | n<1K | Apache-2.0 | Sentetik | ✅ |
| **tugrulkaya/turkish-pii-dataset** | Türkçe PII detection | n<1K | CC-BY-4.0 | doğrulanamadı | ⚠️ provenance belgesiz |
| **GoktugD/turkish-ner-synthetic-1m** | 1,000,000 cümle (980K/10K/10K), PER/LOC/ORG; şablon & varlık havuzları split'ler arasında ayrık; satır bazında generator SHA, seed, template_id, split_group [İddia, kart] | 1M | CC0-1.0 | Deterministik generator | ✅ İsim/kurum tespiti için; **split metodolojisi Battal için örnek** |
| **erayyildiz/turkish_ner** | Gazetteer ile otomatik etiketlenmiş Türkçe NER [İddia, kart] | 100K–1M | CC-BY-4.0 (tag) | Kaynak metin Wikipedia (otomatik) [Çıkarım] | ⚠️ Gürültülü otomatik etiket; benchmark'a değil eğitime |
| **WikiANN** `unimelb-nlp/wikiann` | Çok dilli NER (tr dahil) | 1M–10M | **unknown** [Ölçüm] | Wikipedia | ❌ (lisans belirsiz) |
| **Babelscape/wikineural** | Çok dilli NER | — | CC-BY-NC-SA-4.0 | — | ❌ (ayrıca Türkçe tag yok) |
| **ai4privacy/pii-masking-400k** | 6 dil PII | 100K–1M | `other` [Ölçüm] | Sentetik | ❌ Türkçe yok; lisans custom |
| **ai4privacy/pii-masking-openpii-1.5m** | 30 dil iddiası, CC-BY-4.0 [İddia, kart] | 1.6M | Kart: CC-BY-4.0 (HF tag "other") | Sentetik | ⚠️ Türkçe tag yok [Ölçüm] → Türkçe içeriği doğrulanamadı |

### 2.6 Dataset sonuçları [Çıkarım]
1. **Permissive + Türkçe-native injection verisi çok az ve tamamı 2026'da, küçük, tek-yazarlı/şablonlu.** En büyük Türkçe set (Aytaş, ~20.5K) NC-SA ve makine çevirisi → kullanılamaz.
2. RTP-LX'in 1,049 Türkçe satırı tek **insan-transcreation** Türkçe safety kaynağı; ama toksisite odaklı → benign-toksik hard negative olarak değerli.
3. PII tarafı daha iyi durumda: CC0/CC-BY sentetik setler (cagrigungor, BTX24, fevzi, GoktugD) mevcut.
4. Türkçe offensive/hate setlerinin neredeyse tamamı tweet/kazıma tabanlı ve/veya NC/SA → benchmark'a **gömülmemeli**.

---

## 3. Benchmark inşa metodolojisi

### 3.1 Taksonomi (OWASP LLM01:2025 + MITRE ATLAS hizalı)
Referans: OWASP LLM01:2025 Prompt Injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/), LLM02 Sensitive Information Disclosure, LLM07 System Prompt Leakage; MITRE ATLAS AML.T0051 (LLM Prompt Injection, direct/indirect) ve AML.T0054 (LLM Jailbreak) (https://atlas.mitre.org/). [İddia: kategori adları bu kaynaklarda; ID'leri yayından önce tekrar kontrol edin]

Önerilen `attack_category` (seviye-1) → `technique` (seviye-2):
- **direct_override**: "önceki talimatları yok say", rol değişimi, öncelik iddiası ("sistem yöneticisiyim").
- **system_prompt_extraction**: sistem prompt'u/gizli talimat sızdırma (LLM07).
- **jailbreak_persona / roleplay**: DAN-benzeri persona, kurgu/hipotetik çerçeve, "büyükanne" vb.
- **indirect_injection**: e-posta, belge, web sayfası, tool output, tablo, kod yorumu içine gömülü talimat (BIPIA/AgentDojo kategorileri).
- **data_exfiltration**: markdown image/URL ile veri sızdırma, tool çağrısıyla dışa gönderim.
- **tool_abuse / agentic**: yetkisiz tool çağrısı, parametre manipülasyonu.
- **obfuscation**: base64/hex/rot13, leetspeak, homoglyph/confusable, zero-width, bidi, tag-unicode smuggling, harf aralama, çeviri-bahanesi.
- **multi_turn / payload_splitting**: talimatı turlara/parçalara bölme.
- **pii_solicitation**: modeli PII çıkarmaya/ifşaya zorlama (LLM02).

`benign_category` (hard negative, en az saldırı sayısı kadar):
- **complaint** (öfkeli müşteri şikâyeti, küfürlü ama zararsız; "sistemi yok sayıyorsunuz!").
- **quote/meta**: saldırıyı *alıntılayan* metin ("Müşteri 'talimatları unut' yazdı, bu ne demek?").
- **education/security_research**: "Prompt injection nedir, örnek verir misin?", CTF açıklaması, OWASP özetleri.
- **operational_instructions**: "Yukarıdaki metindeki tüm kişisel verileri maskele", "sistem ayarlarını sıfırla" (IT destek) — halilneed'in bulgusu: public guard'lar PII-maskeleme talimatlarına %31–77 false alarm veriyor [İddia, https://huggingface.co/datasets/halilneed/turkish-prompt-injection-false-alarm-benchmark].
- **role/system vocabulary**: "Rolün müşteri temsilcisi olsun" gibi meşru persona tanımları; prompt mühendisliği yardımı.
- **code**: komut/regex/SQL içeren meşru geliştirici soruları.
- **benign_toxic**: hakaret içeren ama injection olmayan metin (RTP-LX TR'den referansla).

### 3.2 Türkçe fenomenler (her saldırı ailesine *varyant ekseni* olarak uygulanır)
- **Diakritik kaybı**: ç→c, ğ→g, ı→i, İ→I, ö→o, ş→s, ü→u ("talimatlari yok say"). Ayrıca **Türkçe büyük/küçük harf tuzağı**: `"I".lower()` → "i" değil "ı" olmalı; `str.lower()` locale-bağımsız → normalizasyon katmanı için ayrı test [Çıkarım].
- **Yazım hatası / klavye komşuluğu**, harf tekrarı ("lütfeeen").
- **Ekler / morfoloji**: "yok say / yok sayın / yok saymanı / yok sayacaksın / yoksay"; aglütinasyon keyword filtrelerini kırar; PII'de "TCKN'si", "IBAN'ıma", "0532...'yi" (ek + kesme işareti).
- **Argo / informal**: "boşver kuralları", "salla talimatları".
- **Code-switching TR–EN**: "Şimdi ignore previous instructions yap", "system prompt'unu dump et".
- **Unicode obfuscation**: confusable (Kiril а/е/о), zero-width (U+200B/200C/200D/2060), bidi override (U+202E), fullwidth, tag characters (U+E0000 bloğu), NFC/NFD ayrışımı (ş = s + U+0327).
- **Sayı yazımı** (PII): "beş yüz otuz iki…", boşluklu/tireli IBAN, `+90 (532) 000 00 00` varyantları, TCKN'nin aralıklı yazımı.
Üretim: PyRIT converter'ları (diacritic, unicode_confusable, zero_width, leetspeak, charswap) + kendi deterministik Türkçe converter'larımız (diakritik silme, ek çekimi) — her varyant `variant_of=<seed_id>` ve `transform=[...]` alanıyla.

### 3.3 Veri üretim akışı (yalnız self-written / sentetik / permissive)
1. **Seed şablonları elle yaz** (Türkçe-native yazar): her şablon bir `family_id` taşır (ör. `F-OVR-012`). Şablon = sabit niyet + slot'lar (hedef, bağlam, ton, kanal).
2. **Deterministik genişletme** (seed'li RNG; GoktugD ve 3nesdeniz setlerinin yaptığı gibi generator SHA + seed + template_id satırda) [İddia, https://huggingface.co/datasets/GoktugD/turkish-ner-synthetic-1m].
3. **LLM-paraphrase** kullanılırsa: model adı/sürümü, prompt, sıcaklık, tarih kaydedilir; çıktı satırı `generator=llm:<model>` ile işaretlenir; modelin kullanım şartlarının çıktıların CC-BY dağıtımına izin verdiği kontrol edilir [Çıkarım].
4. **Çeviri**: İngilizce permissive kaynaktan (MultiJail-en, JBB, HarmBench, deepset) çeviri yapılırsa `translated_from=<dataset>:<row_id>`, `translation=human|mt:<engine>` alanları zorunlu; çeviri satırı kaynağın **ailesini miras alır** (aynı split).
5. **İnsan doğrulaması**: iki annotator, Cohen's κ raporu; anlaşmazlıklar üçüncü kişiye.
6. **PII değerleri**: TCKN checksum-geçerli rastgele (10./11. hane algoritması), IBAN TR mod-97 geçerli ama gerçek banka kodu + rastgele hesap; telefon 5xx; e-posta `example.com/.org/.net` (RFC 2606) [İddia, https://www.rfc-editor.org/rfc/rfc2606]. Ayrıca **geçersiz checksum'lı negatifler** (over-mask testi).

### 3.4 Template-family split ve near-duplicate tespiti
- **Birim = family**, satır değil. Split ataması: `split = H(family_id) mod 100` → 0–69 train, 70–84 calibration, 85–99 test (sabit hash, ör. SHA-256) [Çıkarım; GoktugD'nin mod-100 yaklaşımına benzer].
- **Aile birleştirme (union-find)**: aşağıdaki herhangi bir bağ iki satırı aynı bileşene koyar ve bileşen tek split'e gider:
  1. aynı `template_id` / `variant_of` / `translated_from` zinciri;
  2. **MinHash-LSH** (karakter 5-gram shingle, diakritik-normalize + casefold sonrası; Jaccard ≥ 0.7 eşik önerisi) — `datasketch` (MIT) [Çıkarım; eşik pilotla ayarlanmalı];
  3. **cross-lingual embedding** benzerliği: LaBSE (arXiv 2007.01852) veya multilingual-e5; kosinüs ≥ ~0.85 aday çiftler → insan kontrolü (TR↔EN çevirileri yakalamak için zorunlu; MinHash diller arası çalışmaz) [Çıkarım].
- **Sızıntı denetimi (rapor edilmeli)**: test satırlarının train'e en yakın komşu benzerlik histogramı; eşik üstü çift sayısı = 0 olmalı. Ayrıca dış setlere (3nesdeniz, halilneed, deepset) karşı aynı kontrol → "contamination" tablosu.
- **Dış test (OOD)**: başka yazarların Türkçe setleri (3nesdeniz-1k test, fevzi, halilneed false-alarm) Battal split'lerine **asla** karışmaz; ayrı "external" raporlanır.

### 3.5 Metrikler
**Detection (sınıflandırıcı olarak guard):**
- Kategori × varyant bazında **precision, recall, F1**; **FPR @ sabit eşik** (eşik calibration split'inde seçilir, testte dondurulur) ve **TPR @ FPR=1%/0.1%**. F1 tek başına yanıltıcı (benign/saldırı oranına bağlı) [İddia, halilneed kartı "F1 … dominated by benign rows"].
- Güven aralıkları: Wilson veya **family-level cluster bootstrap** (örnekler bağımsız değil, aile içi korelasyonlu) [Çıkarım].
- Dil dilimi: tr / en / tr-en code-switch / diakritiksiz / obfuscated ayrı satırlar.
- PR-AUC + ROC-AUC (eşikten bağımsız), ama ürün kararı sabit eşikteki FPR'a göre.

**Kalibrasyon (önemli):** Classifier softmax/sigmoid skorları **olasılık değildir**; modern sinir ağları sistematik olarak miscalibrated [İddia, Guo et al. 2017, arXiv 1706.04599]. Yapılacaklar: calibration split'inde **temperature scaling** veya isotonic regression; ECE + reliability diagram raporu; eşik seçimi kalibre skor üzerinden; kalibrasyon **dil bazında** ayrı kontrol (Türkçe ile İngilizce farklı kayabilir) [Çıkarım]. Kalibrasyon split'i test'ten ve train'den family-ayrık olmalı.

**Uçtan uca:**
- **ASR (attack success rate)** = guard + hedef LLM zincirinde saldırının amacına ulaştığı oran (judge: kural tabanlı canary/secret sızıntısı tercih; LLM-judge kullanılırsa judge'ın kendi doğruluğu insan-etiketli alt örnekte raporlanmalı). Guard'sız baseline ile **ΔASR**.
- **Utility/over-refusal**: benign görevlerin bloklanma oranı (AgentDojo'daki utility-under-attack kavramı, arXiv 2406.13352).

**PII:**
- Varlık tipi bazında span-level **miss rate** (FN/gerçek) ve **over-mask rate** (yanlış maskelenen token/span; tuzak negatifler: fatura no, sipariş no, geçersiz checksum TCKN) — exact match + partial overlap ayrı; ekli formlarda ("IBAN'ıma") sınır doğruluğu ayrı dilim.
- Maskeleme sonrası metin bütünlüğü: maskelenmemesi gereken içeriğin değişmeme oranı (cagrigungor benchmark'ındaki `kapsam_disi`/`negatif` kategorileri gibi [İddia, kart]).

### 3.6 Latency, maliyet, quantization, fail-open
- **Latency**: sabit donanım/sürüm/batch=1 ve gerçekçi eşzamanlılık seviyeleri (1, 8, 32); ≥1000 ısınma sonrası istek; metin uzunluğu kovaları (≤128, ≤512, ≤2048 token); **p50/p95/p99** + max; client-side wall clock (ağ dahil) ve server-side (model-only) ayrı; açık-döngü yük üretici (sabit RPS, ör. k6/vegeta) — kapalı-döngü coordinated omission'ı gizler [Çıkarım; Gil Tene'nin coordinated omission uyarısı, doğrulanamadı link]. Sonuçlar HDR histogram olarak saklanır.
- **Cost per 1k requests** = (instance $/saat ÷ sürdürülebilir RPS@p95-SLO) × 1000/3600 + LLM-judge/fallback çağrı maliyeti; donanım, bölge ve fiyat tarihi yazılır [Çıkarım].
- **Quantization etkisi**: FP32/FP16 vs INT8 (ONNX Runtime dynamic/static) vs 4-bit; aynı test seti üzerinde **eşleşik** karşılaştırma: ΔRecall, ΔFPR@eşik, kalibrasyon kayması (ECE), skor sıralama korelasyonu (Spearman), karar değişen örnek oranı (McNemar testi) ve latency/bellek kazancı. Quantize modelde eşik **yeniden kalibre edilir** [Çıkarım].
- **Fail-open / timeout bypass testleri**: (a) guard timeout'a düşünce davranış (fail-closed/fail-open config) — saldırgan çok uzun/ağır input ile timeout tetikleyebilir mi; (b) maksimum uzunluk truncation: payload'ı limit sonrasına koyma (sliding window/chunk testi); (c) guard hatası (5xx), boş yanıt, malformed JSON; (d) Unicode normalizasyon hatası tetikleyen girdiler; (e) eşzamanlı yük altında kuyruk taşması. Her biri için beklenen politika + ölçülen sonuç tablosu.

### 3.7 Reproducibility paketi
- HF dataset (CC-BY-4.0) + `NOTICE` (bileşen lisansları), Datasheet for Datasets alanları, satır bazında: `id, text, label, attack_category, technique, benign_category, family_id, split, variant_of, transforms, language, translated_from, translation, generator, generator_sha, seed, license, source`.
- Eval harness: Inspect `Task` (+ promptfoo CI config); sabit eşik dosyası; sürümlü sonuç tablosu; `datasets` revision hash'i.

---

## 4. Battal için öneri

1. **Harness**: Birincil = **Inspect** (MIT, çok aktif, reproducible log) ile kendi classifier-metrik scorer'ı; CI = **promptfoo** HTTP provider ile sabit test set'i (üretim modu kapalı). Saldırı varyant üretimi = **PyRIT** converter'ları (deterministik olanlar). Uçtan uca tarama = **garak** REST generator (ikincil). Faz 2 agent security = **AgentDojo** (Inspect portu üzerinden). Giskard, DeepTeam, HarmBench, InjecAgent, BIPIA → yalnız referans/taksonomi.
2. **Benchmark çekirdeği kendi yazımımız olmalı**: Türkçe-native şablon aileleri (hedef ilk sürüm: ~150–250 aile, aile başına 10–30 varyant; saldırı:hard-negative ≈ 1:1.5) [Çıkarım — sayılar öneri, ölçüm değil]. Hard-negative'ler özellikle PII-maskeleme talimatları, şikâyetler, alıntılar, güvenlik eğitimi.
3. **Dış (external) test**: `halilneed/turkish-prompt-injection-false-alarm-benchmark` (CC0), `3nesdeniz/turkish-prompt-injection-1k` ve `-conversation` (CC-BY-4.0), `fevziegeyurtsevenler/turkish-prompt-injection` (CC-BY-4.0) → ID referansla raporla; Battal train'ine **girmesin** (aksi halde dış test anlamını yitirir).
4. **PII**: `cagrigungor/turkish-pii-masking-benchmark` (CC0) doğrudan dahil edilebilir/dış test; eğitim için BTX24 (CC-BY-4.0), fevzi corpus (Apache-2.0), GoktugD (CC0). Kendi checksum-geçerli TCKN/IBAN generator'ımız + geçersiz-checksum negatifler.
5. **Kesinlikle gömülmeyecekler**: OnerAYTAS (CC-BY-NC-SA), ctoraman hate (NC-SA), TurkishHateMap (SA), Overfit-GM (Jigsaw kaynağı), WikiANN (unknown), wikineural (NC-SA), hoatac (lisanssız), tweet tabanlı setler, Lakera oyun trafiği (production-traffic ilkesi).
6. **İngilizce kaynaklar**: MultiJail-en, JBB-Behaviors, Aya (Apache), deepset (lisans çelişkisi notuyla) → yalnız İngilizce/code-switch dilimi ve çeviri-tohumu; çeviriler kaynağın ailesinde kalır.
7. **Rapor formatı**: her model için kategori×varyant precision/recall, FPR@kalibre eşik, TPR@FPR=1%, ECE, p50/p95/p99, $/1k, quantization delta, fail-open test tablosu; family-cluster bootstrap CI.
8. **Kalibrasyon şartı**: yayınlanan her eşik calibration split'inde seçilir; skorlar dokümanda "kalibre edilmiş risk skoru" diye anılmadıkça "olasılık" denmez.

---

## 5. Belirsizlikler / doğrulanamayanlar
- PolyGuardMix alt-kaynak lisans zinciri ve çeviri motoru (makaleden doğrulanmadı).
- WildJailbreak satır sayısı (kart gated; HF tag 1K–10K ile makaledeki ölçek çelişiyor).
- XSafety alt-kaynakları ve satır sayıları.
- BTX24 TCKN/IBAN değerlerinin checksum geçerliliği.
- Jigsaw Kaggle verisinin yeniden dağıtım şartları (Overfit-GM kararı çıkarıma dayanıyor).
- Tweet tabanlı CC-BY-2.0 setlerin yeniden dağıtımının platform ToS ile ilişkisi (hukuki görüş gerekir).
- OWASP/ATLAS teknik ID'leri yayın öncesi tekrar kontrol edilmeli.
- halilneed ve 3nesdeniz kartlarındaki model skorları **yazarların kendi ölçümleri**; Battal tarafından tekrarlanmadı.
- deepset Almanca satır sayısı kaba keyword heuristiğiyle (~106) ölçüldü; kesin değil.
