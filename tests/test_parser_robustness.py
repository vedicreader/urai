"""A tolerant parser is where an infinite loop hides.

The corpus pins what the parse chain does with shapes we can name. This pins what it does with
shapes nobody named: mutate real calls at random and require that every one of them terminates,
raises nothing, and still hands back arguments that can go back onto the wire.
"""
import json, random, signal, time

import pytest

from urai import StreamSplit, parse_tool_tags_ex, split_think

SEEDS = [
    '<tool_call>{"name": "edit", "arguments": {"file": "a.py", "old": "x\\ny", "new": "z"}}</tool_call>',
    '<tool_call>\n<function=edit>\n<parameter=file>\na.py\n</parameter>\n</function>\n</tool_call>',
    '<think>weighing it</think>text<tool_call>{"name": "ls", "arguments": {}}</tool_call>',
    '{"name": "read", "arguments": {"path": "a"}}',
    '```json\n{"name": "read", "arguments": {"path": "a"}}\n```',
]
ALPHABET = list('{}[]",:\\\'<>=/ \nabc0123') + [
    '<tool_call>', '</tool_call>', '<function=', '</function>', '<parameter=', '</parameter>',
    '<think>', '</think>', '"name"', '"arguments"']
NAMES = ['edit', 'ls', 'read']


def mutate(s, rnd):
    "Cut, insert, delete and duplicate at random: the ways a token cap and a weak model break output."
    for _ in range(rnd.randint(1, 6)):
        if not s: break
        i = rnd.randrange(len(s))
        op = rnd.choice(('cut', 'insert', 'delete', 'duplicate'))
        if op == 'cut': s = s[:i]
        elif op == 'insert': s = s[:i] + rnd.choice(ALPHABET) + s[i:]
        elif op == 'delete': s = s[:i] + s[i+1:]
        else: s = s[:i] + s[i:i+rnd.randint(1, 8)] * 2 + s[i:]
    return s


class _Timeout(Exception): pass


def _alarm(*a): raise _Timeout()


@pytest.mark.parametrize('seed', range(4))
def test_mutated_model_output_always_terminates_and_stays_serializable(seed):
    rnd = random.Random(seed)
    signal.signal(signal.SIGALRM, _alarm)
    worst = 0.0
    try:
        for _ in range(1500):
            raw = mutate(rnd.choice(SEEDS), rnd)
            signal.setitimer(signal.ITIMER_REAL, 5.0)
            t = time.perf_counter()
            try:
                _, tcs, _ = parse_tool_tags_ex(split_think(raw)[0], names=NAMES)
                for tc in tcs: json.dumps(tc['function']['arguments'])
                s = StreamSplit()
                for k in range(0, len(raw), 7): list(s.feed(raw[k:k+7]))
                list(s.finish())
                for tc in s.tool_calls: json.dumps(tc['function']['arguments'])
            except _Timeout: pytest.fail(f'parse did not terminate on {raw!r}')
            finally: signal.setitimer(signal.ITIMER_REAL, 0)
            worst = max(worst, time.perf_counter() - t)
    finally: signal.signal(signal.SIGALRM, signal.SIG_DFL)
    assert worst < 0.5, f'a single parse took {worst*1000:.0f} ms'
