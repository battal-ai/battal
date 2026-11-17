# Ürüne genel bakış

Bu sayfa, Battal'ın bugüne kadar alınan kararlarla nasıl şekillendiğini tek yerde özetler.
Ayrıntılar ve gerekçeler [araştırma raporunda](research/index.md) ve
[mimari karar kayıtlarında (ADR)](decisions/0001-product-shape-and-licensing.md) bulunur.
Bu sayfa ile bir ADR çelişirse ADR geçerlidir.

!!! warning "Durum"
    Tasarım aşaması. Kararlar verildi, kod henüz yazılmadı. Sıradaki adım, backlog'daki E0
    (repo iskeleti) ve E1'dir (değerlendirme sözleşmesi).

## Battal nedir?

Battal, LLM'leri kendi altyapısında çalıştıran ve birincil dili Türkçe olan kurumlar için bir
güvenlik katmanıdır. Self-hosted ve CPU'da çalışan bir **evaluation service** ve SDK olarak
tasarlanmıştır. Gateway'ler, code studio'lar ve agent runtime'lar Battal'a bir içeriği gönderir ve
"bu içerik ne olsun?" diye sorar. Battal bir karar (`allow`, `mask`, `block`, `ask`) ve gerekçesini
döner.

Battal bir **LLM proxy'si değildir**. Trafik Battal'ın üzerinden geçmez; Battal yalnızca çağrılır.

## Hangi sorunu çözer?

- Değerlendirilen guardrail framework'lerinin hiçbirinde Türkçe desteğine dair açık bir kanıt yok.
  Büyük üreticilerin guard modelleri de Türkçe sonuçlarını ayrıca raporlamıyor.
- Çok dilli injection sınıflandırıcıları Türkçe saldırıları yakalıyor, ancak talimata benzeyen
  zararsız Türkçe metinlerin %60–77'sini yanlışlıkla işaretliyor (üçüncü taraf ölçümü, küçük
  örneklem).
- Hazır PII tanıyıcıları Türkçe yazım biçimlerini kaçırıyor: `10000000146dır`, gruplu yazım,
  tam genişlikli rakam, sıfır genişlikli boşlukla bölünmüş numara.
- Herkese açık, yeniden üretilebilir bir Türkçe injection benchmark'ı yok.

| Kullanıcı | Battal'ın yanıtı |
|---|---|
| Platform ekibi (LLM'i kendi altyapısında çalıştıran kurum) | Gateway'e config ile eklenen, Türkçe-farkında guard |
| Güvenlik ve uyum ekibi | Ham veri saklamayan, sürümlenmiş ve açıklanabilir karar kayıtları |
| Agent ve code studio kullanan ekipler | Aynı API'yi kullanan Claude Code, Hermes ve MCP adapter'ları (faz 2) |
| Türkçe NLP topluluğu | CC-BY-4.0 lisanslı Türkçe benchmark ve açık temel model |

## Nasıl çalışır?

Her istek tek bir sözleşmeden (`/v1/evaluate`) geçer ve beş adımda işlenir:

1. **Normalize.** Türkçe-farkında normalizasyon: `ı/İ` doğru işlenir; görünmez karakterler, bidi,
   confusable karakterler ve base64/hex gibi kodlamalar çözülür. Bulgular orijinal metindeki doğru
   konuma geri eşlenir.
2. **Detector'lar.**
    - **Türkçe PII:** TCKN, IBAN, telefon ve e-posta. TCKN ve IBAN için checksum doğrulanır; ekli
      yazımlar (`…146dır`) ve gruplu yazım yakalanır.
    - **Prompt injection:** Türkçe ve Türkçe–İngilizce karışık metinde. Önce yüksek precision'lı
      kurallar, ardından kalibre edilmiş küçük bir ONNX sınıflandırıcı çalışır.
3. **Policy.** Deklaratif YAML kurallar, tespit sonucunu bir eyleme bağlar. Ham model skoru, policy
   kararı ve gerekçe ayrı alanlardır; kalibre edilmemiş skorlar olasılık olarak sunulmaz.
4. **Eylem.** Tip etiketli yer tutucularla (`<TCKN>`) maskeleme ya da engelleme.
5. **Karar kaydı.** Ham içerik saklanmaz. Kayıtta içeriğin HMAC'i, span offset'leri, detector ve
   policy sürümleri ve `bundle_hash` tutulur.

Ayrıntılar: [Referans mimari](research/index.md#4-referans-mimari),
[Ortak API sözleşmesi](research/index.md#44-ortak-api-sozlesmesi).

## Policy modeli

Ayrıntılar: [ADR 0004](decisions/0004-policy-binding-and-playground.md).

- **Policy ve binding ayrıdır.** Policy dosyası "ne yapılır" sorusunu, `bindings.yaml` "nerede
  uygulanır" sorusunu cevaplar. Bağlama boyutları checkpoint, tenant/team/key ve modeldir. Yüzey
  (gateway, IDE, agent) ve tool boyutları sonraki fazlarda eklenir.
- **Katmanlı yapı.** Global taban policy her zaman çalışır. Ekip veya model policy'si tabanı
  yalnızca sıkılaştırabilir, gevşetemez. İstek içinden policy seçimi de tabanı atlatamaz.
- **Bundle.** Policy dosyaları ve binding'ler birlikte semver ve içerik hash'iyle sürümlenir. Hot
  reload önce doğrular, sonra atomik olarak devreye alır; bundle geçersizse eskisi çalışmaya devam
  eder.
- **Testler kod olarak yazılır.** Policy'lerin yanında `*.test.yaml` dosyaları durur;
  `battal policy validate`, `test` ve `diff` komutlarıyla ve CI'da koşar.
- **Playground.** Yerel çalışır (`battal serve --playground`). Policy yazılıp denenir, aynı girdi
  farklı bağlamlarda karşılaştırılır, ve bir değişikliğin hangi kararları değiştireceği
  kaydetmeden önce görülür.

## Nereye bağlanır?

| Faz | Yüzey | Entegrasyon yolu |
|---|---|---|
| MVP | AI gateway | LiteLLM `generic_guardrail_api`; LiteLLM'de kod değişikliği gerekmez |
| 2 | Code studio | Claude Code `PreToolUse` hook'u |
| 2 | Agent runtime | Hermes Agent `pre_tool_call` plugin'i |
| 2+ | MCP ve OpenShift AI | MCP gateway adapter'ları, FMS Detector API |

**Hata davranışı** her checkpoint için policy'de belirlenir. Varsayılan olarak `input` ve
`tool_call` fail-closed çalışır. Model tabanlı bir detector düşerse karar deterministik kurallarla
verilir ve yanıta `degraded: true` yazılır.

Ayrıntılar: [Üç entegrasyon senaryosu](research/index.md#5-uc-entegrasyon-senaryosu),
[Hata ve erişilemezlik](research/index.md#46-hata-ve-erisilemezlik).

## Battal'ın yapmadıkları

- Kimlik doğrulama, yetkilendirme, sandbox ve ağ çıkışı (egress) kontrolünün yerine geçmez. Bunlara
  ek bir katmandır.
- Model tabanlı tespit olasılıksaldır ve atlatılabilir. Birincil karar katmanı deterministik
  policy'dir.
- Uyum sertifikası vermez; uyum çalışmaları için kanıt üretir.

## Teknik temel

- **Dil.** Önce Python: FastAPI sunucu, ONNX Runtime, orkestratör olarak Presidio. MVP'den sonra
  deterministik çekirdek (normalizasyon, PII, policy) Rust'a (PyO3) taşınır. İki motorun aynı
  davrandığını dilden bağımsız JSON test vektörleri kanıtlar; Python implementasyonu referans
  görevi görür. ([ADR 0003](decisions/0003-language-python-then-rust.md))
- **Dağıtım.** Python SDK (in-process) ve Battal Server (container/Helm).
- **CPU-first.** Varsayılan detector'lar küçük ONNX sınıflandırıcılar ve deterministik kurallardır.
  Büyük LLM guard'lar yalnızca adapter üzerinden, kullanıcının kendi model sunucusunda çalışır.
- **Gecikme hedefi.** CPU'da p95 ≤ 150 ms ek gecikme. Bu bir hedeftir, henüz ölçülmemiştir.

## Açık kaynak ve lisans

Ayrıntılar: [ADR 0001](decisions/0001-product-shape-and-licensing.md),
[Lisanslama](proje/lisanslama.md).

- Kodun tamamı Apache-2.0'dır.
- Kod, model ağırlıkları ve veri ayrı lisanslanır. Varsayılan imaja yalnızca Apache-2.0 veya MIT
  lisanslı ağırlıklar girer; diğer lisanslı modeller adapter ile desteklenir ve kullanıcı ağırlığı
  kendisi indirir.
- Güvenliğin tabanı açık kalır: engine, API/SDK, adapter'lar, temel Türkçe detector'lar,
  deterministik policy, eval harness ve benchmark.
- İleride open-core modelinde bir enterprise sürüm planlanmaktadır (multi-tenant control plane,
  SSO/RBAC, policy onay akışı, sektöre özel modeller gibi). Bu özellikler bugün kodda yer almaz;
  yalnızca extension point'leri bulunur.
- Kod katkıları için CLA gereklidir.

## İlk sürüm (MVP)

Ayrıntılar: [ADR 0002](decisions/0002-mvp-scope.md),
[Geliştirme backlog'u](research/index.md#9-gelistirme-backlogu-bagmllk-srasna-gore).

**Kapsamda:** `input` ve `output` checkpoint'leri; Türkçe normalizasyon; Türkçe PII tespiti ve
maskeleme; Türkçe ve karışık dilde injection tespiti; YAML policy, binding ve policy testleri;
ham veri içermeyen karar kaydı; LiteLLM adapter'ı.

**Kapsam dışı:** streaming denetimi, tool call güvenliği, RAG denetimi, IDE ve agent adapter'ları.

**Kanıt:**

- Herkese açık (CC-BY-4.0), yeniden üretilebilir bir Türkçe injection benchmark'ı.
- `docker compose up` ile çalışan bir LiteLLM + Battal demosu.

**Sonrası (bağımlılık sırasıyla):** Türkçe injection modelinin fine-tune'u (E10), Rust çekirdek
(E11), tool call güvenliği ve Cedar (E12), Claude Code ve Hermes adapter'ları (E13), output
streaming (E14), MCP adapter'ları (E15), content safety (E16), secret detection ve NER (E17),
policy playground (E18).
