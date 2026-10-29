#!/usr/bin/env python3
"""Validate figure-plan structure and semantic preservation; not a visual/medical judge."""
import argparse
import json
from pathlib import Path

RELATIONS = {'activation', 'inhibition', 'association', 'transport', 'contains',
             'adjacent', 'sequence', 'parallel', 'and', 'or', 'classification',
             'lineage', 'other'}
ALIGNMENT = {'match', 'partial', 'missing', 'conflict', 'uncertain'}


def validate(plan):
    errors, warnings = [], []
    semantic = plan.get('semantics', {})
    nodes, edges = semantic.get('entities', []), semantic.get('relations', [])
    if not nodes:
        errors.append('semantics.entities is empty')
    node_ids, edge_ids = set(), set()
    for kind, items, ids, required in (
        ('entity', nodes, node_ids, ('id', 'label', 'state', 'compartment', 'system')),
        ('relation', edges, edge_ids, ('id', 'source', 'target', 'type', 'condition',
                                      'system', 'evidence', 'source_location',
                                      'figure_location', 'alignment'))):
        for item in items:
            ident = item.get('id')
            if not isinstance(ident, str) or not ident or ident in ids:
                errors.append(f'{kind}: missing/duplicate id {ident!r}')
            ids.add(ident)
            for key in required:
                if key not in item:
                    errors.append(f'{kind} {ident}: missing {key}')
                elif item[key] is None or item[key] == 'unknown':
                    warnings.append(f'{kind} {ident}: unknown {key}; do not infer')
    for edge in edges:
        ident = edge.get('id')
        for key in ('source', 'target'):
            refs = edge.get(key)
            refs = refs if isinstance(refs, list) else [refs]
            if not refs or any(ref not in node_ids for ref in refs):
                errors.append(f'relation {ident}: unresolved {key} {refs!r}')
        if edge.get('type') not in RELATIONS:
            errors.append(f'relation {ident}: unsupported type')
        if edge.get('type') in {'and', 'or'}:
            inputs = edge.get('source')
            if not isinstance(inputs, list) or len(set(inputs)) < 2:
                errors.append(f'relation {ident}: AND/OR requires multiple source IDs')
        if edge.get('alignment') not in ALIGNMENT:
            errors.append(f'relation {ident}: unsupported alignment')
        if edge.get('type') == 'other' and not edge.get('meaning'):
            errors.append(f'relation {ident}: other requires meaning')
    visual = plan.get('visual', {})
    for key, ids in [('nodes', node_ids), ('edges', edge_ids)]:
        unknown = set(visual.get(key, {})) - ids
        if unknown:
            errors.append(f'visual.{key}: unknown semantic IDs {sorted(unknown)}')
    return errors, warnings


def semantic_delta(before, after):
    """Order-insensitive, ID-based comparison includes all semantic attributes."""
    changes = []
    for group in ('entities', 'relations'):
        old = {x['id']: x for x in before['semantics'].get(group, [])}
        new = {x['id']: x for x in after['semantics'].get(group, [])}
        for key in sorted(set(old) | set(new)):
            if old.get(key) != new.get(key):
                changes.append({'group': group, 'id': key,
                                'before': old.get(key), 'after': new.get(key)})
    old_rest = {k: v for k, v in before['semantics'].items()
                if k not in ('entities', 'relations')}
    new_rest = {k: v for k, v in after['semantics'].items()
                if k not in ('entities', 'relations')}
    if old_rest != new_rest:
        changes.append({'group': 'semantic_context', 'before': old_rest, 'after': new_rest})
    return changes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path)
    p.add_argument('--compare', type=Path, help='Previous semantic plan for a visual-only edit')
    args = p.parse_args()
    plan = json.loads(args.plan.read_text())
    errors, warnings = validate(plan)
    delta = None
    if args.compare:
        before = json.loads(args.compare.read_text())
        old_errors, _ = validate(before)
        if old_errors:
            errors.extend('before: ' + x for x in old_errors)
        if not errors:
            delta = semantic_delta(before, plan)
    result = {'structural_pass': not errors, 'errors': errors, 'warnings': warnings,
              'semantic_preserved': None if delta is None else not delta,
              'semantic_changes': delta,
              'boundary': 'No pixels inspected; no scientific validity claim.'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors or delta else 0)


if __name__ == '__main__':
    main()
