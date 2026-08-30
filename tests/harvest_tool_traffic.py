#!/usr/bin/env python
"""Merge a `$URAI_RAW_DUMP` capture into the replay corpus, dropping duplicates.

    URAI_RAW_DUMP=/tmp/raw.jsonl python your_agent.py
    python tests/harvest_tool_traffic.py /tmp/raw.jsonl [--note "qwen3 4b, edit-heavy session"]
"""
import argparse, json
from pathlib import Path

CORPUS = Path(__file__).parent/'fixtures'/'tool_traffic.jsonl'


def load(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dump', help='the file $URAI_RAW_DUMP was pointed at')
    ap.add_argument('--note', default='captured', help='what produced this traffic')
    ap.add_argument('--out', default=str(CORPUS))
    a = ap.parse_args()
    out = Path(a.out)
    have = load(out) if out.exists() else []
    seen = {r['raw'] for r in have}
    added = [{**d, 'note': a.note} for d in load(a.dump)
             if d.get('raw') and d['raw'] not in seen and not seen.add(d['raw'])]
    with out.open('a') as f:
        for r in added: f.write(json.dumps(r) + '\n')
    print(f'{len(added)} new of {len(load(a.dump))} captured; corpus now {len(have) + len(added)}')


if __name__ == '__main__': main()
