# Release notes

<!-- do not remove -->

## 0.0.15

- `parse_tool_tags` strips `<parameter>` elements left outside any call. A degenerate Claude reply in the `<invoke>` dialect wrote stray `<parameter name="1">`, `</parameter>` and nested `<parameter>` blocks between its calls. Those stayed in the clean text, and a caller that shows the reply's last line as a status showed `</parameter>`. The strip runs only when the reply holds an `<invoke>` or `<function=...>` call.

## 0.0.14

- `mk_toolspec` describes a pydantic model by its own fields. It reads `model_json_schema`, inlines each `$ref` and drops the `title`s; `get_schema` read the model's `__init__(**data)` and handed the model one opaque `data` object, so `structured` with a pydantic schema came back empty or wrong. A tool loop calling such a class now passes its fields, not `data=`.
- A `Literal` field or parameter becomes an `enum` with its JSON type, alone or inside `Optional`, a union or a list. `get_schema` wrote the type `"object[object, object]"`, which is not JSON Schema, and Gemini refused the whole request. `lit_schema` builds the `enum`.

## 0.0.13

- README links to the docs again. nbdev takes `lib_name` from the distribution name `uraiyadal` and found no doc index under it; `strip_libs = "urai"` points it at the `urai` index.
- The comment on `CHARS_PER_TOKEN` says why it is 3.25 when the measured models give 3.50: the lower figure keeps the estimate high.
- The `tbl_caps` test reads `gpt-image-1`; fastllm 0.0.65 dropped the retired `dall-e-3` from its model table, which failed CI.

## 0.0.12

- Tag calls in Claude's own dialect are read: `<invoke name="tool">` with `<parameter name="key">` values, inside `<tool_call>` blocks or a `<function_calls>` wrapper, streamed or whole. Claude falls back to it on the tags channel, most often when it sends several calls at once, and those calls used to be dropped.

## 0.0.11

- The tag protocol (`TAG_TOOLS_SP`) asks for independent calls together: each in its own `<tool_call>` block in one message, the reply ending after the last. It used to say "call one function at a time", so a model on the tags channel paid one round trip per call. The parser and the loop already took several.

## 0.0.10

- A tool can return pictures: `ToolMedia(str)`, or any result with a non-empty `.media` list. After a step's tool messages, one user message carries them with a note naming the tools. At most 8 pictures of 20 MB each per step.
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
