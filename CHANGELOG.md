# Release notes

<!-- do not remove -->

## 0.0.19

- `call_tool` checks required arguments after hoisting and type conversion. A missing field returns a tool-call error without running the tool. The error lists all missing fields. Direct native calls and name-only JSON calls use the same check.
- `lone_tag_tc` keeps unreadable arguments marked `unread`. Before, they became readable calls with `{}`.
- `parse_args` returns `None` for empty or invalid native arguments. `norm_resp` marks these calls `unread` and sets `tool_parse_failed`. A bad call does not raise during the turn. A valid empty JSON object stays readable.
- Breaking for callers of `parse_args`: code that renders a stored call back into a provider's format must use `parse_args(s) or {}`. Before, `parse_args` never returned `None`.

## 0.0.18

- `split_think` reads only a reasoning block at the start of the text. A think tag that comes after answer text stays in the answer. Before, a quoted think tag anywhere cut the rest of the reply away as thought.
- The prefill rule of `split_think` does not fire when a tool-call or function-equals opener comes before the closing think tag. Before, a closing think tag inside a tool argument removed the whole call.
- A JSON call body is read as JSON only. A function-equals tag quoted inside its strings is never run. A JSON body that cannot be read is marked unread.
- `parse_tool_tags_ex` returns calls in text order when a reply mixes JSON blocks and function-equals calls.
- A function-equals call with no closing tag before the next call is marked unread. Before, it took the closing tag of the next call and ran with arguments from both.
- `StreamSplit` finds the closing tool-call tag only outside JSON strings. Streamed and finished replies now give the same calls.
- `coerce_args` keeps a string it cannot read as a number. Before, the value became `None`.
- `ChatOpts.create` accepts a dict of options like keyword options. Aliases are normalized, unknown keys go to `extra`, keywords win over the dict, and an explicit `extra=` is merged.
- `AsyncChat` passes `stream='raw'` through to the chat. `AsyncChat.__aexit__` runs `close` on a worker thread.
- When the tool budget runs out, the assistant reply is added to `hist` once. Before, it was added twice, with tool calls that had no answers.
- Closing a stream early closes the backend iterator.
- Summary insertion keeps a tool call and its result together.
- Parallel tool calls that have not started get `cancel_msg_` after `cancel()`, as sequential calls do.
- `mk_obj` rebuilds dataclasses inside lists, tuples and `Optional` fields.
- `CachedChat.structured` rebuilds nested dataclasses. A recording stores the full history after the turn. Old recordings still replay.
- `Broker.close` cancels open chats until their turns end or the timeout passes, and it does not block on the engine lock. A turn that waits for the engine does not start after `close`.

## 0.0.17

- A tool-call block with a stray empty tag, a doubled opening tag, or `arguments` before `name` parses to its real arguments. Before, the name was salvaged and the arguments dropped, so the call ran with `{}` and the tool raised `missing 1 required positional argument`.
- A call that cannot be read never runs. Each such call gets the answer `unread_msg_`. Before, the second unreadable call in a turn ran with empty arguments.
- Identical calls (same name and arguments) in one reply run once. Each repeat gets the answer `dup_msg_`. Before, a reply with 300 identical calls ran the tool 9 times.
- A tool-call tag quoted inside a string argument does not end or start a call. `tool_blocks` reads the whole JSON object of each block before it looks for the closing tag.

## 0.0.16

- A reply cut off at the output limit in the middle of a tool call is asked for again with `cut_msg_`, which asks for the call in smaller pieces. `reparse_msg_` asked for a cleaner `<tool_call>` block, which does not help a call that was too long.
- A backend can put its own re-ask message in the reply's `reparse` key, and its account of why the call was lost in `lost`. Neither key reaches `hist`.
- `ToolCallError` is raised when a reply with a `lost` reason fails after the model was already asked once in the turn to resend a call. The turn ended on a reply that hid the failure. A failure with no `lost` reason still ends the turn as before.

## 0.0.15

- `parse_tool_tags` strips `<parameter>` elements left outside any call. A degenerate Claude reply in the `<invoke>` dialect wrote stray `<parameter name="1">`, `</parameter>` and nested `<parameter>` blocks between its calls. Those stayed in the clean text, and a caller that shows the reply's last line as a status showed `</parameter>`. The strip runs only when the reply holds an `<invoke>` or `<function=...>` call.

## 0.0.14

- `mk_toolspec` describes a pydantic model by its own fields. It reads `model_json_schema`, inlines each `$ref` and drops the `title`s. Before, `get_schema` read the model's `__init__(**data)` and described one opaque `data` object. `structured` with a pydantic schema then returned an empty or wrong result. A tool loop that calls such a class passes its fields, not `data=`.
- A `Literal` field or parameter becomes an `enum` with its JSON type, alone or inside `Optional`, a union or a list. `get_schema` wrote the type `"object[object, object]"`, which is not JSON Schema, and Gemini refused the whole request. `lit_schema` builds the `enum`.

## 0.0.13

- README links to the docs again. nbdev takes `lib_name` from the distribution name `uraiyadal` and found no doc index under it. `strip_libs = "urai"` points it at the `urai` index.
- The comment on `CHARS_PER_TOKEN` says why the value is 3.25 and not the measured 3.50. The lower value keeps the estimate high.
- The `tbl_caps` test reads `gpt-image-1`. fastllm 0.0.65 dropped the retired `dall-e-3` from its model table, and CI failed.

## 0.0.12

- Tag calls in Claude's own dialect are read: `<invoke name="tool">` with `<parameter name="key">` values, inside `<tool_call>` blocks or a `<function_calls>` wrapper, streamed or whole. Claude falls back to it on the tags channel, most often when it sends several calls at once, and those calls used to be dropped.

## 0.0.11

- The tag protocol (`TAG_TOOLS_SP`) asks for independent calls together: each in its own `<tool_call>` block in one message, the reply ending after the last. It used to say "call one function at a time", so a model on the tags channel paid one round trip per call. The parser and the loop already took several.

## 0.0.10

- A tool can return pictures with `ToolMedia(str)` or with any result that has a non-empty `.media` list. After the tool messages of a step, one user message holds the pictures and a note that names the tools. Each step sends at most 8 pictures of at most 20 MB each.
- `Chat.media_in` decides whether pictures are sent; it defaults to the transport's `_media_ok`. When false, the note names the paths instead.
- `strip_hist_media(hist)` swaps image parts for a placeholder, for checkpoints.

## 0.0.9

- A tagged call keeps its arguments when the model sends them flat, under `args`, or drops the outer closing brace after a finished `arguments` object.
- A call whose arguments were lost is marked `unread`. `_fix_step` asks the model once to send it again rather than calling the tool with `{}`.
- `norm_resp` and `stream_resp` set `tool_parse_failed`, so the reparse request fires for a tool call block that nothing could read.
- A repaired string keeps the backslash of an unknown escape: a regex's `\w` stays `\w`.

## 0.0.8


## 0.0.7
`stream_resp` shared drain loop for all backends. `StreamSplit._held` is O(1) per chunk.
`CachedChat` covers `structured` and `runtime`, takes `env=`.
`split_think` handles a closing tag with no opener (prefill).

## 0.0.6
tool rows for easy access

## 0.0.5
tag parsing fixes for mlx models. adding usage stats to record

## 0.0.4
uraiyadal release

## 0.0.3
rename to uraiyadal

## 0.0.2
release

## 0.0.1
initial urai creation
