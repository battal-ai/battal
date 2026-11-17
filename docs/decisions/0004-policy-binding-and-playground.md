# ADR 0004: Policy binding, policy testleri ve playground

- Durum: kabul edildi
- Tarih: 2026-11-17

## Bağlam

Policy yazan kişinin iki ihtiyacı vardır: farklı policy'leri farklı yerlere (ekip, model,
checkpoint…) uygulayabilmek ve bir policy değişikliğinin neyi değiştirdiğini production'a
almadan görebilmek. Raporun §4.5 bölümü bir policy seçim sırası tanımlıyordu, ama "yer" kavramı,
birden fazla eşleşmenin nasıl birleştirileceği ve policy'lerin nasıl test edileceği tanımlı
değildi. Proje tek bir geliştiriciyle, haftada 8–10 saatle ilerliyor; bu yüzden playground,
MVP demosunu geciktirmeyecek biçimde planlanmalıdır.

## Kararlar

### Kapsam

1. **Önce test formatı ve CLI, sonra arayüz.** MVP'ye policy test formatı ve CLI
   (`battal policy validate`, `battal policy test`, `battal policy diff`) girer. Görsel
   playground MVP'den hemen sonra gelir (E18, E5'e bağlı).
2. **Yerel playground.** Playground, policy'yi kuran operatörün kendi makinesinde ya da kendi
   sunucusunda çalışır. Docs sitesinde tarayıcıda çalışan bir sürüm, Rust çekirdeği WASM'a
   derlenebildiğinde (E11 sonrası) ayrıca değerlendirilir.

### Policy binding

3. **Binding policy'den ayrıdır.** Policy dosyası yalnızca kuralları içerir ("ne yapılır").
   Hangi policy'nin nerede uygulanacağı ayrı bir `bindings.yaml` dosyasında tanımlanır
   ("nerede uygulanır"). Aynı policy birden fazla yere bağlanabilir.

   ```yaml
   bindings:
     - id: global
       policy: default-tr
       match: {}
     - id: finans
       policy: strict-pii
       match: {team: finans, checkpoint: [input, output]}
   ```

4. **Boyutlar.** Şema şu boyutları baştan tanır: `checkpoint`; kimlik (`tenant`, `team`, `key`,
   `user`); hedef (`model`, `provider_region`); yüzey (`gateway`, `ide`, `agent`); agent ve tool
   adı. MVP'de yalnızca `checkpoint`, `tenant`/`team`/`key` ve `model` çalışır, çünkü bunlar
   LiteLLM'den gelir. Diğer boyutlar E12–E13 ile devreye girer; şema değişmez.
5. **Eşleşme.** Bir binding'deki farklı alanlar AND, aynı alandaki liste değerleri OR ile
   birleşir. `model` alanında glob kullanılabilir (`qwen3-*`). Spesifiklik eşleşen alan sayısıdır.
   Aynı spesifiklikte çakışan iki binding runtime'da değil, **bundle yüklenirken hata** verir.
6. **Katmanlı birleştirme.** Global **taban policy** (floor) her zaman çalışır. Üstüne en spesifik
   eşleşen policy eklenir. Sonuçlar `block > ask > mask > allow` önceliğiyle birleştirilir.
   Alt katman tabanı gevşetemez, yalnızca sıkılaştırabilir. Maskelemede iki katmanın span'lerinin
   birleşimi maskelenir. Yanıta ve karar kaydına eşleşen binding'ler (`matched_bindings`) ve
   kararı veren katman yazılır.
7. **İstek içinden policy seçimi.** İstek içindeki `policy.id` yalnızca o key için izin verilmiş
   spesifik policy'ler arasından seçim yapabilir. Taban policy'nin yerini hiçbir zaman alamaz.
8. **`ask` eylemi.** `ask` şemada yer alır. Gateway yüzeyinde (LiteLLM'de karşılığı olmadığı için)
   açıklayıcı bir mesajla `block` olarak uygulanır ve bundle yüklenirken uyarı verilir. Gerçek
   `ask` davranışı IDE ve agent yüzeyleriyle (E13) gelir.

### Policy bundle

9. **Bundle.** Policy dosyaları + `bindings.yaml` birlikte bir policy bundle'dır. Bundle semver ve
   içerik hash'i ile sürümlenir; her karara `bundle_hash` yazılır.
10. **Hot reload.** Dosya değişince yeni bundle önce validate edilir, sonra atomik olarak devreye
    alınır. Bundle geçersizse eskisi çalışmaya devam eder; alarm ve log üretilir. Geri alma, bir
    önceki hash'e dönmekten ibarettir.
11. **Kural dili.** MVP'de deklaratif YAML kullanılır: `detector`, `min_score`, `checksum_valid`,
    `context_hit`, `trust`, `source` alanları ve `all` / `any` / `not` birleştiricileri.

    ```yaml
    rules:
      - id: pii.block_tckn
        when: {all: [{detector: pii.tckn, checksum_valid: true}, {trust: untrusted}]}
        action: block
    ```

    CEL gibi bir ifade dili, gerçek bir ihtiyaç doğarsa PolicyEngine interface'inin arkasına ikinci
    bir motor olarak eklenir. Cedar, tool call yetkilendirmesi için ayrılmıştır (E12).

### Policy testleri

12. **Testler kod olarak yazılır.** Policy'lerin yanında `*.test.yaml` dosyaları durur. Testler tek
    bir policy'ye değil, bundle'a karşı koşar. Her case'te şunlar bulunur:
    - `context` (tenant, team, model, checkpoint…); verilmezse global bağlam kullanılır.
    - `input`: ya `text` (tam pipeline) ya da `detections` (yalnızca policy).
    - `expect`: `action`, `rule_id`; isteğe bağlı olarak `matched_bindings` ve `transforms`.

    ```yaml
    cases:
      - name: finans ekibinde TCKN engellenir
        context: {team: finans, checkpoint: input}
        input: {detections: [{detector: pii.tckn, checksum_valid: true}]}
        expect: {action: block, rule_id: pii.block_tckn, matched_bindings: [global, finans]}
    ```

13. **Deterministik ve model testleri ayrıdır.** `text` girdili testler model sürümüne bağlıdır ve
    `tags: [model]` ile etiketlenir. CI'da deterministik testler her zaman, model testleri ayrı bir
    job'da koşar.
14. **Ortak şema.** Test formatı, ADR 0003'teki JSON test vektörleriyle aynı şemayı paylaşır.
    Böylece Rust motoru da aynı testlerle doğrulanır.

### Playground

15. **Teknoloji.** FastAPI'nin sunduğu, sunucu tarafında render edilen sayfalar: Jinja + htmx ve
    CDN'den yüklenen bir YAML editörü (CodeMirror). Node veya build adımı gerekmez.
16. **Güvenli varsayılanlar.** Playground varsayılan olarak kapalıdır, yalnızca
    `battal serve --playground` ile açılır ve yalnızca `127.0.0.1`'e bağlanır. Production
    container imajında devre dışıdır.
17. **İki mod.** Yalnızca policy (detection'lar elle verilir) ve tam pipeline (metin girilir).
    İkisi de aynı `EvaluationResponse`'u gösterir.
18. **Bağlam ve açıklama.** Bağlam (tenant, team, model, checkpoint) seçilebilir. Aynı girdi farklı
    bağlamlarda yan yana denenebilir. Hangi binding'lerin eşleştiği, hangi koşulun neden tuttuğu
    ve kararı hangi katmanın verdiği gösterilir. Denenen bir senaryo tek tıkla test case olarak
    kaydedilebilir.
19. **Taslak ve kaydetme.** Playground bellekte bir taslak bundle üzerinde çalışır. "Kaydet"
    dosyaları diske yazar. Çalışan sunucunun aktif bundle'ı yalnızca dosya reload'u (karar 10)
    ile değişir; playground validate adımını atlatamaz. Sürüm geçmişini git tutar.
20. **Etki farkı.** Taslak her değiştiğinde test suite'i hem aktif hem taslak bundle'la koşulur ve
    kararı değişen case'ler (önceki ve yeni eylem, `rule_id`) gösterilir. Aynı karşılaştırma CLI'da
    `battal policy diff` ile yapılır. Bu, §4.5'teki shadow modun yerel ve ucuz bir karşılığıdır.

### Açık kaynak sınırı

21. Tek kullanıcılı, yerel playground'un tamamı Apache-2.0'dır. Çok kullanıcılı özellikler
    (paylaşılan workspace, RBAC, policy onay akışı ve sürüm geçmişi arayüzü) kodda yalnızca
    extension point olarak bulunur. Production trafiğinden replay, ham veri saklamama ilkesiyle
    (rapor §4.7) çeliştiği için açık kaynak sürümde yer almaz.

## Elenen alternatifler

- **Yalnızca en spesifik policy'nin çalışması:** Bir ekip policy'si global korumayı sessizce
  gevşetebilir.
- **Eşleşen bütün policy'lerin düz birleştirilmesi:** Binding sayısı arttıkça hangi kuralın neden
  çalıştığı anlaşılmaz hâle gelir.
- **Binding'in policy dosyasının içinde olması:** Aynı policy'yi yeniden kullanmak ve atamayı
  policy'ye dokunmadan değiştirmek zorlaşır.
- **React + Monaco SPA:** İkinci bir dil ve build zinciri, tek geliştirici için orantısız maliyet.
- **İlk günden ifade dili (CEL):** Açıklanabilirliği, Rust'a taşımayı ve test vektörleriyle
  doğrulamayı zorlaştırır.

## Sonuçlar

- `EvaluationResponse`'a `matched_bindings` ve `bundle_hash` alanları eklenir; karar kaydı da bu
  alanları tutar.
- E5 epic'i binding, bundle, test runner ve CLI ile genişler; E18 Policy playground eklenir.
- Policy davranışı (binding dahil) testlerle sabitlenir; Rust motoru aynı testleri geçmek zorundadır.
