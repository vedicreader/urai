"""A tool call whose arguments were lost is never dispatched, and a stray tag does not lose them."""
import json
from urai import Chat, ChatOpts, Resp, Runtime, ToolLoopMixin, parse_tool_tags_ex, register_runtime
from urai.tags import mk_tc

T = "<tool_" + "call>"; E = "</tool_" + "call>"
CALL = '{"name": "grep", "arguments": {"pattern": "x", "path_filter": "vr/"}}'
WANT = {"pattern": "x", "path_filter": "vr/"}


def _one(text):
    _, tcs, failed = parse_tool_tags_ex(text)
    assert len(tcs) == 1 and not failed
    return tcs[0]


def test_stray_tag_pair_keeps_arguments():
    tc = _one(T + "\n<grep>\n</grep>\n" + CALL + "\n" + E)
    assert tc['function'] == {'name': 'grep', 'arguments': WANT} and 'unread' not in tc


def test_doubled_opener_keeps_arguments():
    tc = _one(T + T + "\n" + CALL + "\n" + E)
    assert tc['function'] == {'name': 'grep', 'arguments': WANT} and 'unread' not in tc


def test_arguments_before_name():
    tc = _one(T + "\n<grep>\n" + '{"arguments": {"pattern": "x", "path_filter": "vr/"}, "name": "grep"}' + "\n" + E)
    assert tc['function'] == {'name': 'grep', 'arguments': WANT} and 'unread' not in tc


class _Script(ToolLoopMixin, Chat):
    _runtime, ctx_limit, token_count = 'uscript', 8192, 0

    def __init__(self, model=None, *, script=(), **kw):
        self.script, self.steps = list(script), 0
        o = ChatOpts.create(kw.pop('opts', None), **kw)
        self._setup(model, o)
        self._set_tools(self.tools)

    def _model_step(self, **kw):
        r = self.script[min(self.steps, len(self.script) - 1)]
        self.steps += 1
        return Resp({'role': 'assistant', 'usage': {'total_tokens': 10}, **r})


register_runtime(Runtime('uscript', _Script, ('uscript-',)))


def test_quoted_tags_in_a_string_argument_do_not_split_the_call():
    text = "see " + T + " and " + E + " there"
    body = json.dumps({"name": "write", "arguments": {"file": "a.md", "text": text}})
    clean, tcs, failed = parse_tool_tags_ex("before " + T + "\n" + body + "\n" + E + " after")
    assert not failed and len(tcs) == 1 and 'unread' not in tcs[0]
    assert tcs[0]['function'] == {'name': 'write', 'arguments': {'file': 'a.md', 'text': text}}
    assert clean.strip() == "before  after"


def test_300_identical_calls_run_the_tool_once():
    seen = []
    def view_file(path: str) -> str:
        "Record the call."
        seen.append(path); return 'ran'
    calls = [mk_tc('view_file', {'path': 'a.py'}) for _ in range(300)]
    c = Chat('uscript-1', runtime='uscript', tools=[view_file], script=[
        {'content': '', 'tool_calls': calls}, {'content': 'done'}])
    c('go')
    tools = [m for m in c.hist if m.get('role') == 'tool']
    assert seen == ['a.py'] and len(tools) == 300
    assert tools[0]['content'] == 'ran' and all('collapsed' in m['content'] for m in tools[1:])


def test_two_unreadable_calls_in_one_turn_are_never_dispatched():
    seen = []
    def rec(pattern: str) -> str:
        "Record the call."
        seen.append(pattern); return 'ran'
    bad = lambda: {**mk_tc('rec'), 'unread': True}
    c = Chat('uscript-1', runtime='uscript', tools=[rec], script=[
        {'content': '', 'tool_calls': [bad()]},
        {'content': '', 'tool_calls': [bad(), bad()]},
        {'content': 'done'}])
    c('go')
    tools = [m for m in c.hist if m.get('role') == 'tool']
    assert seen == []
    assert len(tools) == 2 and all('could not be read' in m['content'] for m in tools)