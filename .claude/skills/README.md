# Claude Code skill'leri

Bu dizindeki skill'ler, projede Claude Code ile çalışırken kullanılan iş akışlarını tanımlar.
Repoyu Claude Code ile açan herkes bunları otomatik olarak kullanabilir.

| Skill | Ne için | Kaynak |
|---|---|---|
| `battal-spec` | Normatif spec yazma süreci ve şablonu | Bu proje (Apache-2.0) |
| `grilling`, `grill-me` | Bir planı veya kararı soru turlarıyla sorgulama | [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) |
| `api-and-interface-design` | API ve interface tasarımı | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |
| `planning-and-task-breakdown` | Spec'ten görevlere geçiş | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |
| `test-driven-development` | Vektörlerden red-green-refactor | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |

Üçüncü taraf skill'ler değiştirilmeden, belirli bir commit'e pinlenerek kopyalanmıştır. Her birinin
dizininde `LICENSE` (orijinal MIT lisansı) ve `SOURCE.md` (upstream adresi ve commit) bulunur.
Güncelleme elle yapılır: yeni sürüm okunur, kopyalanır ve `SOURCE.md` güncellenir.

Proje kuralları üçüncü taraf skill'lerle çelişirse proje kuralları geçerlidir. Örneğin
`planning-and-task-breakdown` görevleri `tasks/` dizinine yazmayı önerir; bu projede görevler
backlog'a yazılır (bkz. `battal-spec`).
