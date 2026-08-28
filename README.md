# urai

> The chat conventions every backend shares.
urai is the layer between [aidialog](https://github.com/AnswerDotAI/aidialog), which says what a message is, and a backend package such as [rishi](https://github.com/vedicreader/rishi), which knows how to talk to one engine. It holds everything in between: how a conversation is stored, how tools are called and approved, how a turn is streamed, and how a model is named and configured.

A backend registers itself, implements one way to send a message, and inherits the rest.

## Install

```sh
pip install uraiyadal
```

## Configuring a chat

The problem this package exists to fix: the same setting has a different name in every backend. A context window is `n_ctx` on llama.cpp, `eng_kw['max_num_tokens']` on litert, and `ctx_limit` on a hosted model, so anything wrapping several of them ends up carrying a translation table that drifts.

In urai there is one name per setting, and each backend says once what it calls that thing.

```python
from urai import mk_chat, resolve, ChatOpts

chat = mk_chat('gpt-5.1', sp='Be brief.', ctx=32_000, temp=0.2)
chat('what is 6 times 7?')
```

`resolve` works out the runtime and the window ahead of time, and the result can be cached, compared and passed around:

```python
spec = resolve('claude-sonnet-4.6')
spec.runtime, spec.ctx, spec.local
chat = mk_chat(spec, tools=[my_tool])
```

Generation settings can also be set for one turn, without rebuilding anything:

```python
chat('a hard question', effort='high', temp=0.9)
```

Options a backend cannot honour are dropped with a warning rather than in silence, and `extra` carries anything the portable names do not cover.

## What is in it

| module | holds |
|---|---|
| `core` | usage counting, the callback protocol, how a reply renders |
| `tags` | reading `<think>` and `<tool_call>` out of plain text, in batch and streamed |
| `caps` | what a model takes and returns, without loading it |
| `msgs` | the canonical message shape and its conversions in and out |
| `opts` | `ChatOpts`, `ModelSpec`, the runtime registry, `resolve` |
| `chat` | the `Chat` base class, `mk_chat`, `AsyncChat`, approval policies |
| `loop` | the tool loop: approval, budget, parallel calls, context recovery |
| `eval` | `classify`, `structured`, `grades`, `check` |
| `sandbox` | running ```python fences a model writes, and feeding results back |
| `record` | recording model calls to disk and replaying them in tests |
| `broker` | many isolated conversations over one shared local engine |

## Writing a backend

A backend subclasses `Chat`, says what it calls the portable options, and registers itself. `ToolLoopMixin` supplies the tool loop for anything that gets tool calls back as data.

```python
from urai import Chat, ToolLoopMixin, Runtime, register_runtime

class MyChat(ToolLoopMixin, Chat):
    _runtime  = 'mine'
    _opt_map  = {'ctx': 'n_ctx'}        # what this backend calls a context window
    _opt_skip = ('effort',)             # ...and what it cannot do at all

    def _model_step(self, **kw): ...    # one completion, as a `Resp`
    def _stream_step(self, **kw): ...   # ...and the streamed version

register_runtime(Runtime('mine', 'mypkg.chat.MyChat', pats=('.mine',)))
```

`Chat('model.mine')` now returns a `MyChat`.

## Develop

The notebooks in `nbs/` are the source; everything in `urai/` is generated from them.

```sh
uv sync --all-extras --group dev
uv run nbdev-export           # notebooks -> urai/*.py
uv run nbdev-test             # execute every notebook
uv run nbdev-clean            # before committing
```

Nothing in the test suite loads a model. Every notebook tests itself against a scripted backend, so `nbdev-test` runs offline in a few seconds.
