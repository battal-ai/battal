# 04 — Entegrasyon Noktaları (LiteLLM, Claude Code, Hermes Agent, MCP, A2A)

> Araştırma tarihi: 2026-11-16. Tüm iddialar birincil kaynaktan (kaynak kodu veya resmi doküman) alınmıştır.
>
> **Etiketler**
> - **[KAYNAK]** = kaynak kodunda okunarak doğrulandı (permalink + satır)
> - **[DOK]** = resmi dokümanda yazıyor (kodla ayrıca doğrulanmadı)
> - **[ÇIKARIM]** = kaynak/dokümandan türetilen yorum; doğrudan yazılı değil
> - **[DOĞRULANAMADI]** = kontrol edilemedi
>
> **Sabitlenen sürümler (permalink tabanları)**
> - LiteLLM kodu: `BerriAI/litellm@57b9afa506771bc7c6b9460b709a3e0cbf1fc645` (main, 2026-11-16; `pyproject.toml` version `1.111.0`; son release etiketi `v1.111.0-dev.4`, `v1.110.0-rc.3`)
>   `LL = https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645`
> - LiteLLM dokümanı **ayrı repoya taşınmış**: `BerriAI/litellm-docs@ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a` ([LL/README.md#L730](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/README.md#L730): "The LiteLLM docs have moved to a separate repository: BerriAI/litellm-docs")
>   `LD = https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a`
> - Hermes Agent: `NousResearch/hermes-agent@ae2a81ccc00e9b7c06301523e5bb09608397149c` (MIT)
>   `HA = https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c`
> - Claude Code hooks: https://code.claude.com/docs/en/hooks (2026-11-16'da çekildi; dokümanda bahsi geçen sürümler v2.1.2xx)
> - MCP spec: **2026-07-28** (güncel/"Current" sürüm), repo `modelcontextprotocol/modelcontextprotocol@de3550c9fea3c5269e42ac95204eef44a2b2cb92`
>   `MCP = https://github.com/modelcontextprotocol/modelcontextprotocol/blob/de3550c9fea3c5269e42ac95204eef44a2b2cb92/docs/specification/2026-07-28`
> - A2A spec: **v1.0.1** (2026-05-28 release) — `https://github.com/a2aproject/A2A/blob/v1.0.1/docs/specification.md`

---

## 0. Özet tablo

| Hedef sistem | Kullanılabilir hook/API | Taşınan bağlam | Uygulanabilen kontrol | Bilinen sınırlama |
|---|---|---|---|---|
| **LiteLLM Proxy — Generic Guardrail API** (PR'sız, bugün çalışır) | `guardrail: generic_guardrail_api`; LiteLLM, Battal'a `POST {api_base}/beta/litellm_basic_guardrail_api` atar. Modlar: `pre_call`, `during_call`, `post_call`, `pre_mcp_call`, `during_mcp_call`, `post_mcp_call` [KAYNAK] | `texts`, `images`, `tools` (yalnız request), `tool_calls` (req+resp), `structured_messages` (yalnız request), `model`, `input_type`, `litellm_call_id`, `litellm_trace_id`, `request_data` (key hash/alias, user_id, user_email, team_id/alias, end_user_id, org_id), allowlist'li `request_headers`, `additional_provider_specific_params`, `litellm_version` [KAYNAK] | `NONE` (geçir), `BLOCKED` (+`blocked_reason` → istemciye HTTP 400), `GUARDRAIL_INTERVENED` (+`texts`/`images`/`structured_messages` ile maskeleme/yeniden yazma) [KAYNAK] | `tools`/`structured_messages` response tarafında yok; `during_call` maskeleyemez; streaming'de varsayılan `block_only` → metin değişikliği düşer (`incremental_diff` yalnız OpenAI chat completions); hata/timeout varsayılanı fail-closed; `BLOCKED` dahil verdict'ler HTTP 2xx olmalı |
| **LiteLLM Proxy — native provider (upstream PR)** | `CustomGuardrail` alt sınıfı + `apply_guardrail(inputs, request_data, input_type, logging_obj)`; alternatif: `async_pre_call_hook`, `async_moderation_hook`, `async_post_call_success_hook`, `async_post_call_streaming_iterator_hook` [KAYNAK] | Yukarıdakinin tamamı + tüm `request_data` dict'i (metadata, body), `UserAPIKeyAuth` nesnesi (native hook'larda), `logging_obj` [KAYNAK] | Engelle (exception), maskele (dönen `inputs`), stream chunk filtrele (iterator hook), loglarda maskele (`async_logging_hook`) [KAYNAK] | Python kodu LiteLLM'e girer → review/bakım yükü; repo'da sıkı lint "gate"leri var (AGENTS.md); doküman PR'ı ayrı repo |
| **LiteLLM — MCP Gateway** | `pre_mcp_call` / `during_mcp_call` / `post_mcp_call` modları; `tools/list` keşfinde açıklama taraması [DOK] | Tool argümanları, tool tanımı, `CallToolResult` metinleri, `structuredContent` string değerleri [DOK] | Tool çağrısını engelle, argüman/sonuç maskele, zehirli tool'u listeden gizle [DOK] | MCP alt-çağrıları istekteki `guardrails` seçimini miras almaz → `default_on: true` gerekir; blok varsayılan olarak tool hatası olarak modele döner (HTTP 200), `mcp_block_behavior: raise` ile 400 [DOK] |
| **Claude Code** | `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `PermissionRequest`, `PostToolBatch`, `Stop`, `Elicitation`… ; handler tipleri `command`, `http`, `mcp_tool`, `prompt`, `agent` [DOK] | `session_id`, `prompt_id`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`, `tool_input`, `tool_use_id`, `agent_id/agent_type`, `prompt` (UserPromptSubmit), tool çıktısı (PostToolUse) [DOK] | PreToolUse: `allow/deny/ask/defer` + `updatedInput`; UserPromptSubmit: prompt'u engelle/bağlam ekle; PostToolUse: `updatedToolOutput` ile modelin gördüğünü değiştir (yan etki geri alınmaz) [DOK] | Hook geliştirici makinesinde çalışır; timeout/çökme varsayılan olarak **fail-open** (`onFailure: "block"` gerekir, v2.1.295+); `MessageDisplay` yalnız ekran; model I/O'su hook ile değil `ANTHROPIC_BASE_URL`→LiteLLM ile korunur |
| **Hermes Agent** (NousResearch) | Plugin hook'ları (`ctx.register_hook`): `pre_tool_call`, `transform_tool_result`, `pre_llm_call`, `transform_llm_output`, `pre_api_request`…; shell hooks (`config.yaml` `hooks:`); middleware (`llm_request`, `tool_request`, `llm_execution`, `tool_execution`) [KAYNAK+DOK] | `pre_tool_call`: `tool_name`, `args`, `task_id`, `session_id`, `conversation_id`, `tool_call_id`, `turn_id`, `api_request_id`, `middleware_trace`; `pre_llm_call`: `user_message`, `conversation_history`, `model`, `platform`, `sender_id`… [DOK] | `pre_tool_call`: `block` / `approve` (insan onayına yükselt) / `modify` (args shallow-merge); `pre_llm_call`: turu engelle; `transform_tool_result` / `transform_llm_output`: içerik değiştir [DOK] | Python plugin hook'larında `pre_tool_call` timeout/exception'da **fail-closed**, diğerleri fail-open; middleware **fail-open** (enforcement için uygun değil); `pre_tool_call` payload'unda kullanıcı kimliği yok |
| **MCP (spec 2026-07-28)** | Protokolde "guardrail hook" yok. Uygulama noktaları: (a) istemci/host tarafı tool-call interception, (b) MCP gateway/proxy (ör. LiteLLM `/mcp`), (c) sunucu tarafı [ÇIKARIM, spec'e dayalı] | JSON-RPC `tools/call` (ad + argümanlar), `tools/list` (açıklama, şema); HTTP'de `Mcp-Method`/`Mcp-Name` başlıkları zorunlu; `_meta` içinde clientInfo/protocolVersion [DOK] | Proxy'de tam engelleme/maskeleme mümkün; OAuth 2.1 + RFC 8707 audience bağlama, token passthrough yasağı [DOK] | Yetkilendirme **OPTIONAL**; "human in the loop" yalnız **SHOULD**; annotations güvenilmez; spec içerik güvenliği garanti etmez |
| **A2A (v1.0.1)** | Protokolde guardrail hook yok; `AgentCard.securitySchemes`, `TASK_STATE_AUTH_REQUIRED`, Extensions; LiteLLM'in A2A endpoint'lerinde guardrail çevirisi var [DOK+KAYNAK] | Mesaj `parts` (text), task/context id, agent card | Gateway'de metin bloklama/maskeleme (LiteLLM a2a guardrail_translation) [KAYNAK] | Yetkilendirme mantığı "implementation-specific"; Agent Card imzası **MAY** |

---

## 1. LiteLLM (en önemli hedef)

### 1.1 Repo yapısı ve sağlayıcı dizini

- Guardrail sağlayıcıları: `litellm/proxy/guardrails/guardrail_hooks/` [KAYNAK]. HEAD'de mevcut alt dizin/dosyalar (kısmi): `aporia_ai`, `bedrock_guardrails.py`, `guardrails_ai`, `lakera_ai.py`, `lakera_ai_v2.py`, `presidio.py`, `pangea`, `pillar`, `panw_prisma_airs`, `model_armor`, `azure`, `openai`, `generic_guardrail_api`, `unified_guardrail`, `litellm_content_filter`, `mcp_security`, `tool_permission.py`, `tool_policy`, `custom_code`, `llm_as_a_judge` … (~70 entegrasyon). Dizin: [LL/litellm/proxy/guardrails/guardrail_hooks](https://github.com/BerriAI/litellm/tree/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_hooks)
- Otomatik keşif: `guardrail_registry.py` hooks dizinini `os.listdir` ile tarar, her modülde `guardrail_initializer_registry` ve `guardrail_class_registry` sözlüklerini arar [KAYNAK] — [LL/litellm/proxy/guardrails/guardrail_registry.py#L274-L403](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_registry.py#L274-L403)
- Tip enum'u: `SupportedGuardrailIntegrations` [KAYNAK] — [LL/litellm/types/guardrails.py#L101](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/guardrails.py#L101)
- Config şeması: `LitellmParams` birçok `*ConfigModel` mixin'inden türetilir (Presidio, Bedrock, LakeraV2, Pillar, …) [KAYNAK] — [LL/litellm/types/guardrails.py#L1402](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/guardrails.py#L1402); sağlayıcıya özel tipler `litellm/types/proxy/guardrails/guardrail_hooks/` altında.

### 1.2 Guardrail modları (event hooks)

`GuardrailEventHooks` enum'u [KAYNAK] — [LL/litellm/types/guardrails.py#L941-L949](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/guardrails.py#L941-L949):

```
pre_call, post_call, during_call, logging_only,
pre_mcp_call, during_mcp_call, post_mcp_call, realtime_input_transcription
```

- **Ayrı bir "streaming" modu YOK** [KAYNAK]. Streaming, `post_call` + `async_post_call_streaming_iterator_hook` (unified path) ile ve `stream_scope: streaming|non_streaming|both` ayarıyla yönetilir [DOK] — [LD/docs/proxy/guardrails/quick_start.md#L94](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/proxy/guardrails/quick_start.md#L94)
- Mod semantiği [DOK] — [LD/docs/proxy/guardrails/quick_start.md#L88-L92](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/proxy/guardrails/quick_start.md#L88-L92):
  - `pre_call`: LLM çağrısından önce, input üzerinde.
  - `during_call`: input üzerinde, LLM çağrısıyla **paralel**; yanıt guardrail bitene kadar dönmez.
  - `post_call`: çağrıdan sonra, input & output üzerinde.
  - `logging_only`: çağrı bittikten sonra arka plan logging worker'ında; yanıtı değiştirmez, gecikme eklemez; `logging_only_scope: input|output` [DOK] — [quick_start.md#L170](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/proxy/guardrails/quick_start.md#L170)
- Maskeleme yeteneği mod bazında [DOK] — [LD/docs/proxy/guardrails/custom_guardrail.md#L152-L166](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/proxy/guardrails/custom_guardrail.md#L152-L166): `pre_call` maskeler, `during_call` "Blocking only", `post_call` maskeler.

### 1.3 `CustomGuardrail` sınıfı ve hook imzaları (kaynaktan)

`CustomGuardrail(CustomLogger)` — [LL/litellm/integrations/custom_guardrail.py#L393](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_guardrail.py#L393). `__init__` parametreleri [KAYNAK, L417-L433]: `guardrail_name`, `supported_event_hooks`, `event_hook`, `default_on`, `mask_request_content`, `mask_response_content`, `violation_message_template`, `end_session_after_n_fails`, `on_violation`, `realtime_violation_message`, `on_sensitive_data` (`block`|`route`), `sensitive_data_route_to_model`, `sticky_session_routing`, `run_in_parallel`, `scan_raw_request`, `only_scan_new_messages`, `timeout`, `**kwargs` (`stream_scope` dahil). Sınıf alanları: `mcp_block_behavior`, `use_native_during_call_hook`, `use_native_lifecycle_hooks` (True ise `apply_guardrail` yerine native hook'lar çalışır) [KAYNAK, L394-L400].

**Birincil (önerilen) arayüz** [KAYNAK] — [custom_guardrail.py#L1670-L1698](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_guardrail.py#L1670-L1698):

```python
async def apply_guardrail(
    self,
    inputs: GenericGuardrailAPIInputs,
    request_data: dict,
    input_type: Literal["request", "response"],
    logging_obj: Optional["LiteLLMLoggingObj"] = None,
) -> GenericGuardrailAPIInputs
```

`GenericGuardrailAPIInputs` (TypedDict, total=False) [KAYNAK] — [LL/litellm/types/utils.py#L5478-L5489](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/utils.py#L5478-L5489): `texts`, `images`, `tools`, `tool_calls`, `structured_messages`, `model`, `stream_holdback_chars`.

**Native hook'lar** — tanımları `CustomLogger`'da [KAYNAK]:

| Hook | İmza (aynen) | Satır |
|---|---|---|
| `async_pre_call_hook` | `(self, user_api_key_dict: UserAPIKeyAuth, cache: "DualCache", data: dict, call_type: CallTypesLiteral) -> Exception \| str \| dict \| None` | [custom_logger.py#L425-L434](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L425-L434) |
| `async_moderation_hook` | `(self, data: dict, user_api_key_dict: UserAPIKeyAuth, call_type: CallTypesLiteral) -> object` | [#L524-L530](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L524-L530) |
| `async_post_call_success_hook` | `(self, data: dict, user_api_key_dict: UserAPIKeyAuth, response: LLMResponseTypes) -> Any` | [#L508-L514](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L508-L514) |
| `async_post_call_streaming_iterator_hook` | `(self, user_api_key_dict: UserAPIKeyAuth, response: Any, request_data: dict) -> AsyncGenerator[ModelResponseStream, None]` | [#L539-L546](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L539-L546) |
| `async_post_call_streaming_hook` | `(self, user_api_key_dict: UserAPIKeyAuth, response: str) -> Any` | [#L532-L537](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L532-L537) |
| `async_post_call_failure_hook` | `(self, request_data: dict, original_exception: Exception, user_api_key_dict: UserAPIKeyAuth, traceback_str: str \| None = None) -> Optional[HTTPException]` | [#L487-L493](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L487-L493) |
| `async_pre_call_deployment_hook` | `(self, kwargs: dict[str, object], call_type: CallTypes \| None) -> dict \| None` (deployment seçildikten sonra) | [#L288-L297](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L288-L297) |
| `async_logging_hook` | `(self, kwargs: dict, result: object, call_type: str) -> tuple[dict, object]` — loglanan istek/yanıtı maskelemek için | [#L516-L518](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/integrations/custom_logger.py#L516-L518) |

Proxy tarafındaki dağıtıcılar [KAYNAK] — `ProxyLogging.pre_call_hook` [LL/litellm/proxy/utils.py#L3522](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/utils.py#L3522), `during_call_hook` [#L4092](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/utils.py#L4092), `post_call_success_hook` [#L4731](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/utils.py#L4731), `async_post_call_streaming_iterator_hook` [#L5210](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/utils.py#L5210).

Dokümandaki yetenek matrisi [DOK] — [custom_guardrail.md#L708-L716](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/proxy/guardrails/custom_guardrail.md#L708-L716):
- `apply_guardrail`: input/output; input ve output'u değiştirebilir; çağrıyı düşürebilir.
- `async_pre_call_hook`: input değiştirir, düşürür.
- `async_moderation_hook`: değiştiremez, yalnız düşürür.
- `async_post_call_success_hook`: output değiştirir; **streaming'de yanıt teslim edildikten sonra çalışır (audit-only)**.
- `async_post_call_streaming_iterator_hook`: chunk'ları gerçek zamanlı filtreler/engeller.

### 1.4 Generic Guardrail API (harici HTTP servis — Battal için doğrudan uyumlu)

Kaynak: [LL/litellm/proxy/guardrails/guardrail_hooks/generic_guardrail_api/generic_guardrail_api.py](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_hooks/generic_guardrail_api/generic_guardrail_api.py), tipler: [LL/litellm/types/proxy/guardrails/guardrail_hooks/generic_guardrail_api.py](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/proxy/guardrails/guardrail_hooks/generic_guardrail_api.py), doküman: [LD/docs/adding_provider/generic_guardrail_api.md](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/adding_provider/generic_guardrail_api.md) (başlığı: "[BETA] Generic Guardrail API - Integrate Without a PR").

- **Endpoint**: `api_base` sonuna otomatik `/beta/litellm_basic_guardrail_api` eklenir [KAYNAK, generic_guardrail_api.py#L320-L322](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_hooks/generic_guardrail_api/generic_guardrail_api.py#L320-L322). `api_key` verilirse `x-api-key` başlığı olarak gider [KAYNAK, #L307-L309]. Statik `headers` ve istemciden yönlendirilecek `extra_headers` listesi desteklenir [KAYNAK+DOK, generic_guardrail_api.md#L314].
- **Desteklenen modlar**: `pre_call`, `post_call`, `during_call`, `pre_mcp_call`, `during_mcp_call`, `post_mcp_call` [KAYNAK, #L673-L680](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_hooks/generic_guardrail_api/generic_guardrail_api.py#L673-L680). (`logging_only` bu listede yok → [ÇIKARIM] generic API ile logging_only kullanımı doğrulanmadı; `LITELLM_STRICT_GUARDRAIL_MODES` varsayılanında başlangıçta hata verebilir — custom_guardrail.py#L159 / L491-L503.)
- **Desteklenen LiteLLM endpoint'leri** [DOK, generic_guardrail_api.md#L24-L35]: `/v1/chat/completions`, `/v1/completions`, `/v1/responses`, `/v1/images/generations`, `/v1/audio/transcriptions`, `/v1/audio/speech`, `/v1/messages` (Anthropic — Claude Code trafiği için kritik), `/v1/rerank`, pass-through endpoint'ler.

**İstek gövdesi** (`GenericGuardrailAPIRequest`) [KAYNAK] — [types/.../generic_guardrail_api.py#L143-L165](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/proxy/guardrails/guardrail_hooks/generic_guardrail_api.py#L143-L165):

```
input_type: "request" | "response"
litellm_call_id, litellm_trace_id
structured_messages: list[AllMessageValues] | None   # yalnız request (DOK)
images, tools (yalnız request, DOK), texts
request_data: GenericGuardrailAPIMetadata
request_headers: dict[str,str] | None   # allowlist dışı başlık değerleri "[present]"
litellm_version
additional_provider_specific_params: dict | None
tool_calls
model
```

`GenericGuardrailAPIMetadata` [KAYNAK, #L37-L45]: `user_api_key_hash`, `user_api_key_alias`, `user_api_key_user_id`, `user_api_key_user_email`, `user_api_key_team_id`, `user_api_key_team_alias`, `user_api_key_end_user_id`, `user_api_key_org_id`. Bu alanlar `request_data["metadata"]` ve `["litellm_metadata"]` birleştirilerek doldurulur [KAYNAK, generic_guardrail_api.py#L358-L401].

Başlık allowlist'i (değeri iletilenler): `host, accept-encoding, connection, accept, content-type, user-agent, x-stainless-*, x-litellm-*, content-length`; diğerleri `"[present]"` [KAYNAK, #L52-L64]. Dinamik parametre: istemci `guardrails=[{"isim": {"extra_body": {...}}}]` ile gönderir, `additional_provider_specific_params` içine birleşir [KAYNAK, #L581-L582; DOK].

**Yanıt gövdesi** (`GenericGuardrailAPIResponse.from_dict`) [KAYNAK, #L191-L237]: `action` (varsayılan `"NONE"`), `blocked_reason`, `texts`, `images`, `tools`, `structured_messages`, `stream_holdback_chars`.

- `BLOCKED` → `GuardrailRaisedException(..., blocked_content=True)` [KAYNAK, generic_guardrail_api.py#L629-L638]; bu exception'ın varsayılan `status_code=400` [KAYNAK, [LL/litellm/exceptions.py#L1235-L1258](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/exceptions.py#L1235-L1258)]. `blocked_reason` mesajı sarılmadan iletilir (`should_wrap_with_default_message=False`) → **istemciye görünür**.
- `GUARDRAIL_INTERVENED` / `NONE` → `texts` (dönen varsa) uygulanır; `images`, `tools`, `structured_messages` dönerse yazılır [KAYNAK, #L448-L484]. `texts` gönderilen `texts` ile birebir sıralı olmalı; mesaj bazında yeniden yazım için `structured_messages` (aynı sıra/rol) [DOK, generic_guardrail_api.md#L232].

**Hata / timeout davranışı** [KAYNAK+DOK]:
- `unreachable_fallback` (varsayılan `fail_closed`): yalnız ağ hatası, timeout, HTTP 502/503/504 için; `fail_open` seçilirse geçirir [KAYNAK, #L486-L505, #L650-L660; DOK #L272].
- `fail_on_error` (varsayılan `true`): **her** hata (non-2xx, bozuk JSON, ağ, serileştirme) için; `false` → tam fail-open, critical log [KAYNAK, types #L64-L72; DOK].
- Fail-closed hata yolu düz `Exception("Generic Guardrail API failed: ...")` fırlatır [KAYNAK, #L505] → [ÇIKARIM] istemciye büyük olasılıkla 500 döner (400 değil).
- `timeout` (saniye, `LitellmParams.timeout`) [KAYNAK, types/guardrails.py#L1272]; `num_retries` (0–5), yalnız bağlantı kurulduktan sonraki timeout/reset için, taze bağlantıyla; connect hataları, HTTP hata kodları ve `BLOCKED` tekrarlanmaz; en kötü gecikme `timeout × (num_retries+1)` [KAYNAK #L507-L534; DOK #L294].
- Varsayılan HTTP timeout değeri (timeout verilmezse) — **[DOĞRULANAMADI]**; config'de açıkça verilmeli.

**Streaming** [KAYNAK, generic init + unified_guardrail.py#L1128-L1200](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_hooks/unified_guardrail/unified_guardrail.py#L1128-L1200):
- `streaming_end_of_stream_only` (varsayılan `False`): her N. chunk'ta tara; `streaming_sampling_rate` varsayılan `5`.
- `streaming_transform_mode` varsayılan `block_only`: **stream'de metin değişiklikleri düşürülür**, yalnız `BLOCKED` stream'i keser. `incremental_diff`: ham chunk'lar tutulur, maskelenmiş metin diff olarak yeni delta'lar şeklinde yayılır — **yalnız OpenAI chat completions streaming yolu** için [KAYNAK, types #L109-L126].
- `streaming_buffer_until_moderated`: tüm chunk'ları tutup bitişte karar; `mask_response_content=True` ise **otomatik devre dışı** (orijinal chunk'ları replay edeceği için PII sızdırır) [KAYNAK, unified_guardrail.py#L1166-L1190].
- `stream_holdback_chars`: kelime sınırında bölünmeyi önlemek için metin başına geri tutulacak karakter sayısı [KAYNAK].

### 1.5 Hook içinde erişilebilen bağlam

- `apply_guardrail` → `request_data` tüm istek dict'i; `request_data["metadata"]` içinde `user_api_key_user_id`, `user_api_key_team_id` vb. [DOK, custom_guardrail.md#L88-L112]. `inputs` içinde `texts/images/tools/tool_calls/structured_messages/model`.
- Native hook'larda `UserAPIKeyAuth` nesnesi (`LiteLLM_VerificationToken` alanları: `token`, `key_alias`, `user_id`, `team_id`, `org_id`, `agent_id`, `project_id`, `metadata`, `models`, `allowed_routes`, `permissions`, `object_permission`, `access_group_ids`, …) [KAYNAK, [LL/litellm/models/verification_token.py#L16](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/models/verification_token.py#L16), [LL/litellm/types/proxy/auth/user_api_key_auth.py#L138](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/types/proxy/auth/user_api_key_auth.py#L138)].
- Generic API ile **iletilmeyenler** [KAYNAK]: key/team `metadata` dict'inin kendisi, istekteki serbest `metadata`, session id (yalnız `litellm_trace_id` var). Gerekirse `extra_headers` allowlist'i (ör. `x-battal-session`) veya `extra_body` dinamik paramları ile taşınır.

### 1.6 Diğer ilgili mekanizmalar

- `/guardrails/apply_guardrail` endpoint'i: bir guardrail'i LLM çağrısı olmadan doğrudan çağırma [KAYNAK, [guardrail_endpoints.py#L2565](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/litellm/proxy/guardrails/guardrail_endpoints.py#L2565)] — Battal entegrasyon testleri için yararlı.
- Guardrail seçimi: `default_on`, istek başına `guardrails: [...]`, team/key bazlı guardrail'ler, policy/tag'ler [DOK, `docs/proxy/guardrails/team_based_guardrails.md`, `guardrail_policies.md`, `policy_tags.md` dosyaları mevcut — içerikleri bu çalışmada okunmadı].
- Sonuçlar `StandardLoggingGuardrailInformation` olarak loglanır; maskelenmiş içerik loga "allow"/"mask" özetine indirgenir (prompt sızdırmamak için) [KAYNAK, custom_guardrail.py#L1734-L1760].
- A2A: `litellm/llms/a2a/chat/guardrail_translation/` ve `litellm/proxy/a2a/` (v0.3↔v1 dönüştürücü `version_convert.py` dahil) [KAYNAK, dosya varlığı].

### 1.7 Yeni sağlayıcıyı upstream'e katkı süreci

[DOK] — [LD/docs/adding_provider/simple_guardrail_tutorial.md](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/adding_provider/simple_guardrail_tutorial.md):
1. `litellm/proxy/guardrails/guardrail_hooks/<ad>/` altında `<ad>.py` (CustomGuardrail alt sınıfı) + `__init__.py` (`initialize_guardrail`, `guardrail_initializer_registry`, `guardrail_class_registry`).
2. `SupportedGuardrailIntegrations` enum'una değer ekle.
3. (Kaynaktaki desen) UI/config için `GuardrailConfigModel` alt sınıfı + `get_config_model()` (generic örneği: types #L128-L140; [KAYNAK]).
4. Testler: doküman `test_litellm/` der, ama HEAD'de testler `tests/unit/proxy/guardrails/guardrail_hooks/` altında [KAYNAK] → doküman eskimiş [ÇIKARIM].
5. Doküman PR'ı **ayrı repoya**: `BerriAI/litellm-docs` → `docs/proxy/guardrails/<ad>.md` (ör. `pillar_security.md`, `lakera_ai.md`) [KAYNAK, ağaç listesi].
6. LiteLLM'in `AGENTS.md`'si katı lint/type "gate"leri tanımlar (ruff_strict_gate, type_discipline_gate, test_quality_gate, openapi_docs_gate, type_check_gate; kural sayısı artamaz) [KAYNAK, [LL/AGENTS.md#L59](https://github.com/BerriAI/litellm/blob/57b9afa506771bc7c6b9460b709a3e0cbf1fc645/AGENTS.md#L59)].
- Emsal: Pillar Security hem Generic Guardrail API ile kullanılabiliyor hem de dokümanı var [DOK, generic_guardrail_api.md "Example: Pillar Security"].

---

## 2. Claude Code hooks

Kaynak: https://code.claude.com/docs/en/hooks (tümü [DOK]).

- **Olaylar**: `SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`, `PostModelSwitch`, `Elicitation`, `ElicitationResult`, `SessionEnd` ("Hook lifecycle" tablosu).
- **Ayar konumları**: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy settings, plugin `hooks/hooks.json`, skill/subagent frontmatter. Hook'lar seviyeler arası **birleşir**; `allowManagedHooksOnly` ile yalnız managed hook'lar çalışır; `disableAllHooks` managed hook'ları dışarıdan kapatamaz ("Hook locations").
- **Handler tipleri**: `command` (stdin JSON), `http` (POST gövdesi JSON; `url`, `headers`, `allowedEnvVars`, `onFailure`), `mcp_tool`, `prompt`, `agent`. HTTP allowlist: `allowedHttpHookUrls`, `httpHookAllowedEnvVars`.
- **Ortak input**: `session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode`, `effort`, `hook_event_name`, `agent_id`, `agent_type`. PreToolUse ek: `tool_name`, `tool_input`, `tool_use_id`. UserPromptSubmit ek: `prompt`, `session_title`. **Kullanıcı/kimlik alanı yok** (yalnız oturum/agent) — kimlik hook'un ortamından/başlık env'inden gelmeli [ÇIKARIM].
- **Engelleme/değiştirme**:
  - Exit `2` → engelleyebilen olaylarda aksiyonu durdurur (stderr = sebep). Exit `1` dahil diğer kodlar **non-blocking** (aksiyon devam eder).
  - `PreToolUse` JSON: `hookSpecificOutput.permissionDecision` ∈ `allow|deny|ask|defer`, `permissionDecisionReason`, `updatedInput` (tüm input'u değiştirir), `additionalContext`. Öncelik `deny > defer > ask > allow`. Deny/ask kuralları hook ne derse desin değerlendirilir.
  - `UserPromptSubmit`: engelle (prompt modele gitmez) veya bağlam ekle.
  - `PostToolUse`: `decision: "block"` yalnız sebep ekler; `updatedToolOutput` modelin gördüğü çıktıyı değiştirir — **araç zaten çalışmıştır**, yan etkiler geri alınmaz; OTel span'ları orijinal çıktıyı yakalar.
  - `PostToolBatch`: exit 2 bir sonraki model çağrısından önce döngüyü durdurur.
  - `MessageDisplay`: **yalnız ekran**; transcript ve modelin gördüğü değişmez.
- **Hata/timeout**: Command/http/mcp_tool hook timeout'unda çıktı atılır; `PreToolUse`'da timeout **aracı engellemez** (fail-open) — `onFailure: "block"` (v2.1.295+) ile fail-closed olur. HTTP hook'ta non-2xx/bağlantı hatası non-blocking error; bloklamak için 2xx + JSON karar dönülmeli. `UserPromptSubmit` varsayılan timeout 30 sn, diğer olaylarda 600 sn.
- **Model I/O**: Hook'lar model istek/yanıtını değiştirmez (UserPromptSubmit hariç giriş). Model trafiği `ANTHROPIC_BASE_URL` ile bir LLM gateway'e (LiteLLM `/v1/messages`) yönlendirilebilir; managed settings'te `allowedProviders: ["customEndpoint"]` ile gateway'e kilitlenebilir (v2.1.285+) — https://code.claude.com/docs/en/llm-gateway [DOK].

**Uygulanabilir vs yalnız gözlem**: Uygulanabilir → PreToolUse (deny/ask/updatedInput), UserPromptSubmit (block), PostToolBatch/Stop (devam ettir/durdur), Elicitation, ConfigChange. Yalnız gözlem/sonradan → PostToolUse (çıktı yeniden yazımı hariç), Notification, SessionStart/End, MessageDisplay (görsel), PermissionDenied.

---

## 3. Nous Research Hermes Agent

- **Doğrulama**: `github.com/NousResearch/hermes-agent` mevcut; açıklama "The agent that grows with you", MIT, Python, homepage `hermes-agent.nousresearch.com`, 2026-11-16'da aktif push [KAYNAK, `gh api repos/NousResearch/hermes-agent`]. Doğru proje.
- **Hook sistemleri** [DOK, [HA/website/docs/user-guide/features/hooks.md#L11-L16](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/website/docs/user-guide/features/hooks.md#L11-L16)]: Gateway hooks (yalnız gözlem), **Plugin hooks** (`ctx.register_hook`, CLI+Gateway; "Tool interception, metrics, guardrails"), **Shell hooks** (`config.yaml` `hooks:` bloğu, her dil), Outbound webhooks.
- **Geçerli olay adları** kaynakta `VALID_HOOKS` [KAYNAK, [HA/hermes_cli/plugins.py#L113](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/hermes_cli/plugins.py#L113)]: `pre_tool_call`, `post_tool_call`, `transform_terminal_output`, `transform_tool_result`, `transform_llm_output`, `pre_llm_call`, `post_llm_call`, `on_stream_start/delta/end`, `on_interim_message`, `pre_verify`, `pre_api_request`, `post_api_request`, `api_request_error`, `pre/post_auxiliary_call`, … `register_hook(hook_name, callback, *, hold_stream=False)` ve `register_middleware(kind, callback)` [KAYNAK, [HA/hermes_cli/plugins_context.py#L753-L757](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/hermes_cli/plugins_context.py#L753-L757)].
- **`pre_tool_call`** — güvenlik kontrolü için doğru nokta:
  - `model_tools.handle_function_call()` → `_pre_dispatch_guards()` içinde handler'dan önce çağrılır; `block` mesajı varsa araç `tool_error` ile kısa devre olur, `modified_args` uygulanır [KAYNAK, [HA/model_tools.py#L792-L830](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/model_tools.py#L792-L830), çağrı #L984].
  - Dönüş: `{"action":"block","message":...}`, `{"action":"approve","message":...,"rule_key":...}` (insan onayına yükselt; ret/timeout fail-closed), `{"action":"modify","args":{...}}` (shallow merge). Öncelik `block > approve`. Timeout (`plugins.hook_callback_timeout`, varsayılan 30 sn) veya exception → **fail-closed** [DOK, hooks.md#L554-L600 ve #L392-L400].
  - Payload: `tool_name`, `args`, `task_id`, `session_id`, `conversation_id`, `tool_call_id`, `turn_id`, `api_request_id`, `middleware_trace` [DOK, hooks.md#L455].
  - **MCP araçları da aynı registry'ye kaydedilir** (`registry.register(...)`, [HA/tools/mcp_tool_registration.py#L387](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/tools/mcp_tool_registration.py#L387)) → [ÇIKARIM, yüksek güven] MCP tool çağrıları da `handle_function_call` → `pre_tool_call` yolundan geçer.
- **Model I/O**: `pre_llm_call` (tur başında; `{"action":"block","message":...}` turu inference'tan önce bitirir; `user_message`, `conversation_history`, `model`, `platform`, `sender_id` taşır) [DOK, hooks.md#L460]; `transform_llm_output` (ilk string yanıtı değiştirir; `hold_stream=True` ile stream yeniden yazılana kadar tutulur) [DOK, hooks.md#L462, #L1886-L1912]; `transform_tool_result` (modele giden araç sonucunu değiştirir) [DOK, #L457]; `pre_api_request` yalnız gözlemci.
- **Middleware** (`llm_request`, `tool_request`, `llm_execution`, `tool_execution`) isteği/args'ı değiştirebilir ama **fail-open**: hata loglanır, zincir devam eder → güvenlik zorlaması için uygun değil [DOK, [HA/website/docs/developer-guide/middleware.md#L28-L124](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/website/docs/developer-guide/middleware.md#L28-L124)].
- **Shell hooks**: stdin JSON (`hook_event_name`, `tool_name`, `tool_input`, `session_id`, `cwd`, `profile`, `extra`), stdout'ta Claude Code uyumlu `{"decision":"block","reason":...}` veya Hermes `{"action":"block",...}`; `fail_closed: true` yalnız `pre_tool_call` için; timeout varsayılan 60 sn, max 300 [DOK, hooks.md#L1995-L2060]. İlk kullanımda onay (consent) gerekir; gateway/cron'da allowlist veya `--accept-hooks` gerekir.
- **Model trafiğini LiteLLM'e yönlendirme**: `provider: custom` + `base_url` (OpenAI-uyumlu) [DOK, [HA/cli-config.yaml.example#L107-L117](https://github.com/NousResearch/hermes-agent/blob/ae2a81ccc00e9b7c06301523e5bb09608397149c/cli-config.yaml.example#L107-L117)] → Battal LiteLLM üzerinden model I/O'yu da korur [ÇIKARIM].

**En az invaziv entegrasyon önerisi** [ÇIKARIM]: Hermes kodunu değiştirmeden bir **`battal` Hermes plugin'i** (Python, `register(ctx)`):
1. `pre_tool_call` → Battal `/v1/evaluate` (tool_call fazı); `block`/`approve`/`modify` eşlemesi. Hermes'in kendi fail-closed davranışından yararlanılır; plugin içi HTTP timeout'u `hook_callback_timeout`'tan kısa tutulmalı.
2. `transform_tool_result` → araç çıktısında PII/injection maskeleme (modelin bağlamına girmeden önce).
3. `pre_llm_call` → kullanıcı mesajında blok; maskeleme gerekiyorsa model trafiğini LiteLLM+Battal'a yönlendir (pre_llm_call mesajı yeniden yazamaz, yalnız bağlam ekler/blok eder [DOK]).
4. Alternatif (Python yazmadan): shell hook + `fail_closed: true`, küçük bir `battal-hook` CLI.

---

## 4. MCP ve A2A — gerçek enforcement nerede durabilir

### 4.1 MCP (spec 2026-07-28)

- **Sürüm**: "The current protocol version is 2026-07-28" (https://modelcontextprotocol.io/specification/versioning) [DOK]. Önceki: 2025-11-25. Büyük değişiklikler: protokol seviyesinde oturum (`Mcp-Session-Id`) ve `initialize` handshake'i kaldırıldı (stateless), `server/discover` zorunlu, HTTP POST'larda `Mcp-Method`/`Mcp-Name` başlıkları zorunlu, Roots/Sampling/Logging deprecated, MRTR deseni [DOK, [MCP/changelog.mdx](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/de3550c9fea3c5269e42ac95204eef44a2b2cb92/docs/specification/2026-07-28/changelog.mdx)].
  - [ÇIKARIM] `Mcp-Method`/`Mcp-Name` başlıkları bir L7 gateway'in gövdeyi parse etmeden `tools/call` + tool adına göre politika uygulamasını kolaylaştırır; ama gövde ile başlık uyumu doğrulanmalı (`HeaderMismatchError` tanımlı).
- **Spec'in garanti ETTİKLERİ / ETMEDİKLERİ**:
  - "For trust & safety and security, there **SHOULD** always be a human in the loop with the ability to deny tool invocations" — yalnız SHOULD [DOK, [MCP/server/tools.mdx#L33-L34](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/de3550c9fea3c5269e42ac95204eef44a2b2cb92/docs/specification/2026-07-28/server/tools.mdx#L33-L34)].
  - Tool annotations: "clients **MUST** consider tool annotations to be untrusted unless they come from trusted servers" [DOK, tools.mdx#L305-L306].
  - Security Considerations: sunucular input doğrulama/erişim kontrolü/rate limit/output sanitizasyonu **MUST**; istemciler onay, input gösterme, "Validate tool results before passing to LLM", timeout, audit log **SHOULD** [DOK, tools.mdx#L787-L803].
  - Authorization **OPTIONAL**; HTTP transport'ta SHOULD uyulmalı; STDIO'da SHOULD NOT (kimlik bilgisi ortamdan) [DOK, [MCP/basic/authorization/index.mdx#L18-L24](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/de3550c9fea3c5269e42ac95204eef44a2b2cb92/docs/specification/2026-07-28/basic/authorization/index.mdx#L18-L24)]. OAuth 2.1 (draft-13), istemci RFC 8707 `resource` **MUST**, sunucu audience doğrulaması **MUST**, token passthrough **MUST NOT** [DOK, authorization/index.mdx#L217-L306; security-considerations.mdx#L14-L23, #L116-L124].
  - Spec **içerik güvenliği** (prompt injection, tool poisoning, veri sızıntısı) için herhangi bir zorunlu mekanizma tanımlamaz [ÇIKARIM — yalnız SHOULD önerileri var].
- **Enforcement konumları** [ÇIKARIM]:
  1. **Host/istemci tarafı interception**: Claude Code `PreToolUse` (matcher `mcp__<server>__<tool>`), Hermes `pre_tool_call`. Avantaj: argümanlar ve kullanıcı bağlamı elde; dezavantaj: uç cihazda, atlatılabilir (managed ayarlar hariç).
  2. **MCP gateway/proxy**: LiteLLM `/mcp` + `pre_mcp_call`/`post_mcp_call` + tool açıklama taraması [DOK, [LD/docs/mcp_guardrail.md](https://github.com/BerriAI/litellm-docs/blob/ae7d2cbf7ea9f1ab433bd6012383c4ad89932a4a/docs/mcp_guardrail.md)]. Merkezi; ama yalnız gateway üzerinden geçen sunucuları korur (stdio yerel sunucular kapsam dışı).
  3. **Sunucu tarafı**: OAuth audience/scope; içerik denetimi sunucu sahibinin sorumluluğu.

### 4.2 A2A (v1.0.1)

- Kimlik "protocol layer"da değil; HTTPS/TLS **MUST**, sunucu her isteği doğrulamalı **MUST**; yetkilendirme "implementation-specific" (skill, aksiyon, veri, OAuth scope **MAY**) [DOK, [A2A spec §7](https://github.com/a2aproject/A2A/blob/v1.0.1/docs/specification.md#7-authentication-and-authorization), satır ~1871-1905].
- `TASK_STATE_AUTH_REQUIRED` ile görev içi yetkilendirme istemciye devredilebilir (§7.6) [DOK].
- Agent Card JWS imzası **MAY** (§ ~L2004) [DOK]. Extensions mekanizması (§4.6) [DOK].
- Spec'te içerik guardrail hook'u yok → enforcement: A2A gateway (LiteLLM `litellm/proxy/a2a/`, `litellm/llms/a2a/chat/guardrail_translation/` text part'ları çıkarıp guardrail uygular [KAYNAK, dosyalar]) veya agent runtime içi.
- Uyarı: LiteLLM'in A2A guardrail README'si v0.3 tarzı `message/send` / `kind: "text"` örneği gösteriyor; v1.0 spec'inde metot `SendMessage` [DOK]. LiteLLM'de `version_convert.py` var, fakat v1.0 mesajlarının guardrail çevirisinde tam desteklendiği **[DOĞRULANAMADI]**.

---

## 5. OpenShift / vLLM (yalnız dağıtım etkisi)

- LiteLLM repo'sunda `litellm/deploy/helm`, `docker`, `compose`, `terraform` dizinleri var [KAYNAK, dizin listesi]. vLLM, LiteLLM arkasında OpenAI-uyumlu backend olarak durur; Battal'ın vLLM'e doğrudan bağımlılığı yok [ÇIKARIM].
- Dağıtım etkisi [ÇIKARIM]: Battal ayrı bir Deployment/Service (FastAPI) olarak LiteLLM ile aynı namespace'te, ClusterIP üzerinden; `api_base` iç DNS. Generic API `unreachable_fallback` 502/503/504'ü "unreachable" saydığı için OpenShift Route/ingress hataları bu sınıfa düşer — politika buna göre seçilmeli. Ayrıntılı Helm tasarımı bu belgenin kapsamı dışı.

---

## 6. Battal için önerilen LiteLLM entegrasyon tasarımı

### 6.1 Strateji: iki aşama

**Aşama 1 (MVP, upstream PR gerekmez)** — Battal FastAPI sunucusu **Generic Guardrail API sözleşmesini birebir** uygular:
`POST /beta/litellm_basic_guardrail_api` (adapter route) → çekirdek `battal.evaluate()`.
Gerekçe: bugün çalışır, tüm LiteLLM endpoint'lerini (chat, responses, `/v1/messages`, MCP) kapsar; LiteLLM'in resmi olarak "Integrate Without a PR" diye sunduğu yol [DOK].

**Aşama 2 (upstream)** — iki seçenek:
- (a) `BerriAI/litellm-docs`'a `docs/proxy/guardrails/battal.md` sayfası (Pillar örneği gibi `guardrail: generic_guardrail_api` config'i ile). Kod PR'ı yok; bakım yükü en az.
- (b) Native sağlayıcı: `litellm/proxy/guardrails/guardrail_hooks/battal/{__init__.py,battal.py}` — `GenericGuardrailAPI`'yi alt sınıflayarak veya `CustomGuardrail.apply_guardrail` uygulayarak; `SupportedGuardrailIntegrations.BATTAL = "battal"`; `BattalGuardrailConfigModel` (UI alanları: `api_base`, `api_key`, `policy_id`, `language`, `fail_mode`); `tests/unit/proxy/guardrails/guardrail_hooks/test_battal.py`; docs PR ayrı repo. Native yalnız Generic API'nin taşımadığı bir şey gerektiğinde değer katar (ör. key/team `metadata`'sının tamamı, `UserAPIKeyAuth.object_permission`, özel streaming davranışı) [ÇIKARIM].

### 6.2 Hook / mod seçimi

| İhtiyaç | LiteLLM modu | Not |
|---|---|---|
| Prompt injection / jailbreak / PII (TR: TCKN, IBAN, telefon, adres) giriş kontrolü + maskeleme | `pre_call` | Maskeleme yalnız burada güvenilir [DOK] |
| Düşük gecikmeli yalnız-blok kontroller | `during_call` | Maskeleme etkisiz olabilir [DOK]; `run_in_parallel` yalnız blok-only için [KAYNAK] |
| Çıktı DLP / zararlı içerik | `post_call` | Non-stream: tam blok/maske. Stream: aşağıya bak |
| MCP tool argüman/sonuç + tool poisoning | `pre_mcp_call`, `post_mcp_call` | `default_on: true` şart; `mcp_block_behavior: raise` ile 400 |
| Yalnız gözlem / shadow mode | `logging_only` | Generic API'nin supported listesinde yok → native sağlayıcıda veya önce test edilmeli [ÇIKARIM] |

Örnek config (Aşama 1):

```yaml
guardrails:
  - guardrail_name: battal-input
    litellm_params:
      guardrail: generic_guardrail_api
      mode: [pre_call, pre_mcp_call]
      api_base: http://battal.battal.svc:8080
      api_key: os.environ/BATTAL_API_KEY
      default_on: true
      timeout: 2
      num_retries: 1            # yalnız Battal değerlendirmesi idempotent ise
      unreachable_fallback: fail_closed
      fail_on_error: true
      extra_headers: [x-battal-session, x-request-id]
      additional_provider_specific_params:
        policy_id: default-tr
        language: tr
  - guardrail_name: battal-output
    litellm_params:
      guardrail: generic_guardrail_api
      mode: [post_call, post_mcp_call]
      api_base: http://battal.battal.svc:8080
      api_key: os.environ/BATTAL_API_KEY
      default_on: true
      timeout: 3
      streaming_transform_mode: incremental_diff   # yalnız OpenAI chat completions
      streaming_sampling_rate: 5
```

### 6.3 İstek → Battal eşlemesi (LiteLLM payload → Battal `EvaluationRequest`)

| LiteLLM alanı | Battal alanı | Not |
|---|---|---|
| `input_type` + çağıran mod | `phase`: `input` / `output` / `tool_call` / `tool_result` | MCP fazı `request_data` içindeki `call_type` ile ayırt edilir; generic payload'da call_type **yok** → [ÇIKARIM] ayrı guardrail adı/`additional_provider_specific_params.phase` ile işaretle |
| `texts[]` | `segments[]` (indeks korunur) | Yanıtta aynı uzunluk/sıra zorunlu |
| `structured_messages[]` | `messages[]` (rol bazlı politika: system vs user) | Yalnız request |
| `tools[]`, `tool_calls[]` | `tools[]`, `tool_calls[]` | `tool_calls.function.arguments` JSON string |
| `images[]` | `images[]` (MVP'de opsiyonel) | |
| `model` | `target.model` | |
| `request_data.user_api_key_*` | `principal{key_hash, key_alias, user_id, user_email, team_id, team_alias, end_user_id, org_id}` | Politika seçimi team/org bazlı |
| `litellm_call_id`, `litellm_trace_id` | `correlation{call_id, trace_id}` | Audit log anahtarı |
| `request_headers` | `context.headers` | allowlist dışı değerler `[present]` |
| `additional_provider_specific_params` | `policy{policy_id, language, …}` | İstek başına `extra_body` ile override |

### 6.4 Battal kararı → LiteLLM yanıtı

| Battal kararı | HTTP | LiteLLM gövdesi |
|---|---|---|
| `allow` | 200 | `{"action":"NONE"}` |
| `mask` / `redact` / `rewrite` | 200 | `{"action":"GUARDRAIL_INTERVENED","texts":[...]}` (texts 1:1) **veya** `structured_messages` (satır sayısı/rol aynı; dokunulmayan satırlar aynen echo); streaming'de `stream_holdback_chars` |
| `block` | 200 | `{"action":"BLOCKED","blocked_reason":"<kullanıcıya gösterilecek TR mesaj + karar kimliği>"}` — dedektör ayrıntısı/eşleşen metin **koyma** (istemciye gider) |
| Battal iç hata / bağımlılık yok | **503** | LiteLLM `unreachable_fallback` uygular (operatör fail-open seçebilir) |
| Geçersiz istek / politika bulunamadı | 4xx/500 | `fail_on_error` uygular (varsayılan blok) |

Kritik: `BLOCKED` dahil tüm verdict'ler **2xx** dönmeli; non-2xx her zaman hata yoluna düşer [KAYNAK, `response.raise_for_status()` #L621].

### 6.5 Maskeleme nasıl uygulanır

- Maskeleme **Battal'da** yapılır; LiteLLM dönen `texts`/`structured_messages`'ı orijinal isteğe/yanıta geri yazar (endpoint'e özgü `guardrail_translation` handler'ları) [KAYNAK+DOK].
- Format önerisi: tip etiketli yer tutucu (`<TCKN>`, `<IBAN>`, `<TEL>`), deterministik; ters çevrilebilir pseudonym gerekiyorsa Battal'da `litellm_call_id`/oturum anahtarlı kasa (vault) + `post_call`'da geri çevirme. Stream'de geri çevirme yalnız `incremental_diff` ile mümkün [KAYNAK].
- `texts` uzunluk uyuşmazlığında `/v1/responses` isteği 500 ile reddedilir [DOK] → Battal adapter'ı invariant'ı test etmeli.
- Loglarda sızıntıyı önlemek için LiteLLM zaten verdict'i "allow/mask"a indirger [KAYNAK]; Battal kendi audit log'unda ham metni saklamamalı (hash + span offset).

### 6.6 Streaming

- `/v1/chat/completions` (OpenAI): `post_call` + `streaming_transform_mode: incremental_diff` → maskeleme stream'de uygulanır; `BLOCKED` stream'i keser.
- `/v1/messages` (Claude Code) ve diğer endpoint'ler: `incremental_diff` desteklenmez → `block_only` (metin değişikliği düşer) [KAYNAK]. Seçenekler: (i) çıktı politikası yalnız blok, (ii) `streaming_buffer_until_moderated: true` ile tam tampon (TTFT artar; `mask_response_content` ile birlikte otomatik kapanır), (iii) yalnız audit.
- Sampling (`streaming_sampling_rate`) nedeniyle iki tarama arasında sızan içerik istemciye ulaşmış olabilir [DOK: end-of-stream-only modunda açıkça belirtiliyor].

### 6.7 Fail-open / fail-closed

- Varsayılan önerisi: **giriş (pre_call, pre_mcp_call) fail-closed**; çıktı (post_call) politika bazında (regüle ortamlarda fail-closed, diğerlerinde `unreachable_fallback: fail_open` + critical log alarmı).
- `fail_on_error: false` asla güvenlik sınırında kullanılmamalı (doküman "complete bypass" uyarısı) [DOK].
- Battal tarafı: kendi bağımlılıkları (model tabanlı dedektörler) düşerse kural tabanlı TR dedektörleriyle **degraded** karar verip yanıtta `x-battal-degraded` benzeri işaret dönebilir; tamamen karar veremiyorsa 503 [ÇIKARIM].
- Gecikme bütçesi: `timeout × (num_retries+1)` toplam; pre_call p99 hedefi örn. <300 ms, `timeout: 2` [ÇIKARIM].

### 6.8 Claude Code / Hermes ile birleşik görünüm

- Claude Code: model I/O → `ANTHROPIC_BASE_URL` = LiteLLM (+Battal `/v1/messages` guardrail), managed `allowedProviders: ["customEndpoint"]`; araçlar → managed `PreToolUse` `http` hook (`onFailure: "block"`) → Battal `/v1/hooks/claude-code` adapter'ı (`hookSpecificOutput.permissionDecision` döner); `PostToolUse` → `updatedToolOutput` ile tool çıktısı maskesi; `allowManagedHooksOnly`.
- Hermes: `battal` plugin'i (`pre_tool_call`, `transform_tool_result`, `pre_llm_call`, `transform_llm_output` + `hold_stream`), model trafiği `provider: custom` → LiteLLM.
- Tek çekirdek `evaluate()`; adapter'lar: `litellm_generic`, `claude_code_hook`, `hermes_plugin`, `mcp_gateway` (LiteLLM üzerinden).

---

## 7. Belirsizlikler / doğrulanamayanlar

1. Generic Guardrail API'nin `logging_only` modunu destekleyip desteklemediği — `get_supported_event_hooks` listesinde yok; strict mod varsayılanında başlatma hatası olası. **[DOĞRULANAMADI — çalıştırılarak test edilmeli]**
2. Generic API'ye MCP çağrılarında `call_type` (`call_mcp_tool` / `list_mcp_tools`) bilgisinin payload'a geçip geçmediği — `GenericGuardrailAPIRequest`'te alan yok → geçmiyor gibi görünüyor [ÇIKARIM].
3. `timeout` verilmediğinde varsayılan HTTP timeout değeri. **[DOĞRULANAMADI]**
4. Fail-closed hata yolunda istemcinin gördüğü HTTP kodu (500 olduğu tahmini) [ÇIKARIM].
5. LiteLLM A2A guardrail çevirisinin A2A v1.0 (`SendMessage`) mesajlarını tam kapsadığı. **[DOĞRULANAMADI]**
6. Hermes `pre_tool_call`'un `execute_code` sandbox'ından RPC ile çağrılan araçlar için de tetiklendiği — kodda ayrıca izlenmedi. **[DOĞRULANAMADI]**
7. LiteLLM HEAD (1.111.0 dev) ile son kararlı release arasında generic API alanlarının (ör. `fail_on_error`, `num_retries`, `streaming_transform_mode`) hangi sürümde geldiği — MVP hedef sürümü sabitlenmeli. **[DOĞRULANAMADI]**
8. Claude Code doküman sürüm numaraları (v2.1.285, v2.1.295 vb.) dokümandan alındı; Battal'ın hedeflediği kurumsal dağıtımlardaki Claude Code sürümü bilinmiyor.
