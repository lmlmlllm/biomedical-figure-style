#!/usr/bin/env python3
"""Read reviewed guidance excerpts without expanding historical appendices."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def unique_pos(text, anchor):
    if text.count(anchor) != 1:
        raise ValueError(f'Boundary missing or ambiguous: {anchor[:70]!r}')
    return text.index(anchor)


def excerpt(text, item):
    if 'exact' in item:
        start = unique_pos(text, item['exact'])
        end = start + len(item['exact'])
    elif 'anchor' in item:
        start = unique_pos(text, item['anchor'])
        end = start + item['chars']
    else:
        start = 0 if item['start'] == 'BOF' else unique_pos(text, item['start'])
        end = len(text) if item['end'] == 'EOF' else unique_pos(text, item['end'])
    if not 0 <= start < end <= len(text):
        raise ValueError('Guidance boundaries are out of order')
    result = text[start:end]
    if digest(result) != item['sha256']:
        raise ValueError('Reviewed excerpt changed; recheck its boundary and update the section index')
    return result, start, end


def section(root, config, items):
    path = root / config['source']
    text = path.read_text(encoding='utf-8')
    chunks = [excerpt(text, item) for item in items]
    ranges = ', '.join(f'{text.count(chr(10), 0, a)+1}–{text.count(chr(10), 0, b-1)+1}'
                       for _, a, b in chunks)
    header = f'来源：{path}\n源 SHA256：{digest(text)}\n已选原文行：{ranges}\n'
    return header + '\n\n'.join(chunk for chunk, _, _ in chunks)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--topic', choices=['logic', 'layouts', 'style', 'all'])
    mode.add_argument('--case', help='Exact optional case ID from --list-cases')
    mode.add_argument('--list-cases', action='store_true')
    parser.add_argument('--query', default='', help='Filter optional case titles; does not load case bodies')
    args = parser.parse_args(argv)
    if args.query and not args.list_cases:
        parser.error('--query requires --list-cases')
    spec = json.loads((ROOT / 'references/guidance_sections.json').read_text(encoding='utf-8'))
    if args.list_cases:
        q = args.query.casefold()
        found = [x for x in spec['cases'] if q in (x['id'] + ' ' + x['topic']).casefold()]
        print('按需条件补例（仅索引；来源限定，不能据此判定医学正确或技能性能）：')
        for item in found:
            print(f"{item['id']}\t{item['topic']}")
        print(f'匹配 {len(found)} 条；用 --case 精确ID 读取完整原段及其限制。')
        return 0
    try:
        if args.case:
            matches = [x for x in spec['cases'] if x['id'] == args.case]
            if len(matches) != 1:
                raise ValueError('Unknown or ambiguous case ID; use --list-cases')
            item = matches[0]
            output = section(ROOT, item, [item])
            note = '按需案例原段；其中验证经过属于历史记录，不能自动作为当前能力证明。'
        else:
            topics = list(spec['defaults']) if args.topic in (None, 'all') else [args.topic]
            output = '\n\n'.join(section(ROOT, spec['defaults'][t], spec['defaults'][t]['segments'])
                                   for t in topics)
            note = ('这是通用指南选段，不是完整规则库。任务涉及特殊条件时，先用 --list-cases '
                    '[--query 关键词] 定位，再用 --case 精确ID 读取。其他期刊案例继续按案例ID或主题查询。'
                    '需要核查科学来源或历史验证时，定向打开对应完整记录。')
        # Assemble before printing, so a failed boundary never leaks a partial/full fallback.
        print(note + '\n\n' + output)
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f'Guidance read stopped: {exc}. No full-document fallback was emitted.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
