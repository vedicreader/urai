# Release notes

<!-- do not remove -->

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
