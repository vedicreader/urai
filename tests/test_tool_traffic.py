"""Replay captured tool traffic through the whole parse and coercion path.

Each fixture record is a `(tools schema, raw model output)` pair. The notebook cells pin named
cases with named expectations; this file asserts only what must hold for every input, whatever
the model said. Grow the corpus from a real run:

    URAI_RAW_DUMP=/tmp/raw.jsonl python your_agent.py
    python tests/harvest_tool_traffic.py /tmp/raw.jsonl
"""
import json
from pathlib import Path

import pytest

from urai import coerce_args, coerce_tcs, parse_tool_tags_ex, split_think, toolspec_params

FIXTURE = Path(__file__).parent/'fixtures'/'tool_traffic.jsonl'
#: markup that must never reach visible content, whichever family emitted it
LEAK_TAGS = ('<think>', '</think>', '<tool_call', '</tool_call>', '<function=', '<parameter=')


def records():
    "Every `(tools, raw, note)` triple in the corpus."
    out = []
    for i, line in enumerate(FIXTURE.read_text().splitlines()):
        if not line.strip(): continue
        d = json.loads(line)
        out.append(pytest.param(d['tools'], d['raw'], id=f"{i:02d}-{d.get('note', '')[:44]}"))
    return out


def tool_names(tools):
    return [(t.get('function') or t).get('name') for t in tools]


def conforms(v, sch):
    "Does `v` already carry the type `sch` declares? Undeclared and union types are vacuously fine."
    t = (sch or {}).get('type')
    if not isinstance(t, str): return True
    if t == 'string': return isinstance(v, str)
    if t == 'integer': return isinstance(v, int) and not isinstance(v, bool)
    if t == 'number': return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == 'boolean': return isinstance(v, bool)
    if t == 'array': return isinstance(v, list)
    if t == 'object': return isinstance(v, dict)
    if t == 'null': return v is None
    return True


def n_conforming(args, params):
    "How many of `args` carry the type the schema declares for them."
    props = (params or {}).get('properties') or {}
    return sum(conforms(v, props.get(k)) for k, v in (args or {}).items())


def parsed(tools, raw):
    "The corpus record run through exactly the path a live turn runs it through."
    text, thought = split_think(raw)        # thinking comes off first, as every backend does it
    text, tcs, failed = parse_tool_tags_ex(text, names=tool_names(tools))
    return text, coerce_tcs(tcs, tools), failed, thought


@pytest.mark.parametrize('tools,raw', records())
def test_emitted_arguments_are_always_a_serializable_object(tools, raw):
    for tc in parsed(tools, raw)[1]:
        args = tc['function']['arguments']
        assert isinstance(args, dict), f'arguments must be an object, got {type(args).__name__}'
        json.dumps(args)                       # and must survive the trip back onto the wire


@pytest.mark.parametrize('tools,raw', records())
def test_every_declared_argument_type_is_carried_or_was_undecidable(tools, raw):
    for tc in parsed(tools, raw)[1]:
        params = toolspec_params(tools, tc['function']['name'])
        args = tc['function']['arguments']
        before = n_conforming(args, params)
        assert n_conforming(coerce_args(args, params), params) >= before, 'coercion made conformance worse'


@pytest.mark.parametrize('tools,raw', records())
def test_coercing_twice_is_the_same_as_coercing_once(tools, raw):
    for tc in parsed(tools, raw)[1]:
        params = toolspec_params(tools, tc['function']['name'])
        once = coerce_args(tc['function']['arguments'], params)
        assert coerce_args(once, params) == once


@pytest.mark.parametrize('tools,raw', records())
def test_arguments_that_already_conform_are_left_exactly_alone(tools, raw):
    "The auto-correct layer is only ever allowed to touch input that is actually broken."
    for tc in parsed(tools, raw)[1]:
        params = toolspec_params(tools, tc['function']['name'])
        props = (params or {}).get('properties') or {}
        args = tc['function']['arguments']
        clean = {k: v for k, v in args.items() if conforms(v, props.get(k))}
        assert coerce_args(clean, params) == clean


@pytest.mark.parametrize('tools,raw', records())
def test_visible_content_never_carries_control_markup(tools, raw):
    text, tcs, failed, _ = parsed(tools, raw)
    for tag in LEAK_TAGS:
        assert tag not in text, f'{tag!r} leaked into visible content: {text[:120]!r}'


@pytest.mark.parametrize('tools,raw', records())
def test_a_parsed_call_always_names_a_declared_tool_or_is_reported(tools, raw):
    "A call we hand back must be runnable. Anything unreadable is reported, never silently dropped."
    text, tcs, failed, thought = parsed(tools, raw)
    names = tool_names(tools)
    for tc in tcs: assert tc['function']['name'] in names, f"undeclared tool {tc['function']['name']!r}"
    assert tcs or failed or text or thought or not raw.strip(), \
        'a reply became nothing at all: no text, no thought, no call, no report'


def test_the_corpus_covers_the_shapes_the_parse_chain_claims_to_handle():
    recs = [json.loads(l) for l in FIXTURE.read_text().splitlines() if l.strip()]
    kinds = {'clean': 0, 'xml': 0, 'mangled': 0, 'truncated': 0, 'no-call': 0}
    for d in recs:
        text, tcs, failed, _ = parsed(d['tools'], d['raw'])
        if '<function=' in d['raw']: kinds['xml'] += 1
        if not tcs: kinds['no-call'] += 1
        if '</tool_call>' not in d['raw'] and '<tool_call>' in d['raw']: kinds['truncated'] += 1
    assert len(recs) >= 40
    for k in ('xml', 'no-call', 'truncated'): assert kinds[k] >= 3, f'thin coverage of {k}'
