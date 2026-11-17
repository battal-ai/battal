# Claude Code skill'leri

Bu dizindeki skill'ler, projede Claude Code ile çalışırken kullanılan iş akışlarını tanımlar.
Repoyu Claude Code ile açan herkes bunları otomatik olarak kullanabilir.

| Skill | Ne için | Kaynak |
|---|---|---|
| `battal-spec` | Normatif spec yazma süreci ve şablonu | Bu proje (Apache-2.0) |
| `grilling`, `grill-me` | Bir planı veya kararı soru turlarıyla sorgulama | [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) |
| `grill-with-docs` | Sorgularken sözlüğü ve ADR'leri de yazma | [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) |
| `domain-modeling` | Terimleri netleştirme, sözlük ve ADR tutma | [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) |
| `codebase-design` | Modül, interface ve seam tasarımı | [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) |
| `documentation-and-adrs` | ADR yazımı, dokümanın koddan kopmasını yakalama | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |
| `api-and-interface-design` | API ve interface tasarımı | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |
| `planning-and-task-breakdown` | Spec'ten görevlere geçiş | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |
| `test-driven-development` | Vektörlerden red-green-refactor | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT) |

Üçüncü taraf skill'ler değiştirilmeden, belirli bir commit'e pinlenerek kopyalanmıştır. Her birinin
dizininde `LICENSE` (orijinal MIT lisansı) ve `SOURCE.md` (upstream adresi ve commit) bulunur.
Güncelleme elle yapılır: yeni sürüm okunur, kopyalanır ve `SOURCE.md` güncellenir.

## Proje kuralları önce gelir

Üçüncü taraf skill'ler kendi varsayılanlarını önerir. Bu projede aşağıdaki kurallar onların yerine
geçer (ayrıntı: kökteki `CLAUDE.md`):

| Skill'in varsayılanı | Bu projede |
|---|---|
| ADR'ler `docs/adr/` altında, kısa format (`domain-modeling`) | ADR'ler `docs/decisions/NNNN-slug.md` altında, mevcut format: Durum/Tarih, Bağlam, Kararlar, Elenen alternatifler, Sonuçlar |
| Sözlük kökte `GLOSSARY.md` (`domain-modeling`) | Sözlük `docs/sozluk.md` |
| İngilizce içerik | Okura yönelik dokümanlar Türkçe (terimler İngilizce); kod, yorumlar ve docstring'ler İngilizce (ADR 0005) |
| Görevler `tasks/plan.md`, `tasks/todo.md` (`planning-and-task-breakdown`) | Görevler raporun backlog'unda (bkz. `battal-spec`) |
| Her önemli karar ADR olur (`documentation-and-adrs`) | ADR yalnızca üç koşulda yazılır: geri alması pahalı, bağlamsız okuyana şaşırtıcı, gerçek bir seçim. Diğer kararlar spec'e veya `docs/mimari.md`'ye yazılır |
