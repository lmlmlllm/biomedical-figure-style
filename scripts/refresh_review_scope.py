#!/usr/bin/env python3
"""Refresh the rolling review window and generate the eligible web index."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo


def assess(source, policy, today):
    try:
        cutoff = today.replace(year=today.year - policy['window_years'])
    except ValueError:
        cutoff = today.replace(year=today.year - policy['window_years'], day=28)
    if source.get('published_date_basis') != 'first_online':
        return False, 'first_online_date_basis_unverified', cutoff
    if source.get('first_online_date') and source['first_online_date'] != source.get('published_date'):
        return False, 'first_online_date_fields_conflict', cutoff
    try:
        published = date.fromisoformat(source.get('published_date', ''))
    except (ValueError, TypeError):
        return False, 'first_online_date_unverified', cutoff
    if not cutoff <= published <= today:
        return False, 'outside_rolling_three_year_window', cutoff
    if source.get('article_type') not in policy['article_types']:
        return False, 'formal_review_type_unverified', cutoff
    journal = source.get('journal', '')
    if journal not in policy['priority_journals'] and not any(
        journal.startswith(prefix) for prefix in policy['priority_journal_prefixes']
    ):
        return False, 'journal_needs_quality_verification', cutoff
    metric = source.get('journal_metric', {})
    if policy.get('require_verified_journal_metric') and (
        metric.get('verification_status') not in {'verified_official_publisher', 'verified_official_society', 'verified_clarivate'}
        or not isinstance(metric.get('journal_impact_factor'), (int, float))
        or not isinstance(metric.get('jif_year'), int)
        or not metric.get('source_url', '').startswith('https://')
    ):
        return False, 'journal_metric_unverified', cutoff
    return True, 'verified_date_type_and_priority_venue', cutoff


def refresh(root, today=None):
    policy = json.loads((root / 'references/review_scope.json').read_text())
    today = today or datetime.now(ZoneInfo(policy['timezone'])).date()
    path = root / 'references/catalog.json'
    catalog = json.loads(path.read_text())
    active, historical = [], []
    _, _, cutoff = assess({}, policy, today)
    for entry in catalog['entries']:
        source = entry.get('source', {})
        if source.get('origin') != 'published_review':
            continue
        eligible, reason, cutoff = assess(source, policy, today)
        source.update(scope_eligible=eligible, scope_reason=reason,
                      scope_checked_at=today.isoformat(),
                      scope_window_start=cutoff.isoformat(),
                      scope_window_end=today.isoformat(),
                      scope_date_basis='first_online_publication_date')
        (active if eligible else historical).append(entry)
    catalog['active_review_count'] = len(active)
    catalog['historical_review_count'] = len(historical)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    lines = [
        '# 近三年高水平期刊综述配图', '',
        f'筛选日期：{today}；首次在线发表窗口：{cutoff}–{today}。', '',
        f'当前符合条件的参考图 **{len(active)} 张**，来自 **{len({e["source"]["doi"] for e in active})} 篇**正式综述。', '',
        '按当前期刊白名单筛选，不把白名单表述为影响因子排名。未核实的分数不予填写。旧期刊案例保留历史记录，但不进入此索引；用户提供的个人风格案例单独保留。', '',
        '| 案例 / 配图出处 | 期刊 | 官方JIF（统计年） | 首次在线发表 | 模板 | 保存状态 |',
        '|---|---|---|---|---|---|'
    ]
    for e in active:
        s = e['source']
        metric = s.get('journal_metric', {})
        metric_label = f'[{metric["journal_impact_factor"]}（{metric["jif_year"]}）]({metric["source_url"]})' if metric else '未核实'
        lines.append(f'| [{e["id"]} · {e["title"]}]({s["figure_url"]}) | {s["journal"]} | {metric_label} | {s["published_date"]} | {"/".join(e["layout_ids"])} | {e["image_status"]} |')
    lines += ['', '调用已分析样式时按案例ID读取 [catalog.json](catalog.json) 的设计笔记；本索引每轮刷新。新图仍需核实自身科学内容。', '',
              f'历史或待核实网络案例：{len(historical)} 张。详细资格见各条目 source.scope_eligible 与 source.scope_reason。', '']
    (root / 'references/active_web_index_CN.md').write_text('\n'.join(lines))
    state_path = root / 'references/search_cycle_state.json'
    if state_path.exists():
        state = json.loads(state_path.read_text())
        state.update(scope_window_start=cutoff.isoformat(),
                     scope_window_end=today.isoformat(),
                     scope_checked_at=today.isoformat(),
                     active_review_count=len(active),
                     active_review_article_count=len({e['source']['doi'] for e in active}),
                     historical_review_count=len(historical))
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    return {'active_review_count': len(active), 'historical_review_count': len(historical),
            'scope_window': [cutoff.isoformat(), today.isoformat()]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--as-of', type=date.fromisoformat, help='Explicit review date for reproducible audit')
    args = parser.parse_args()
    print(json.dumps(refresh(args.skill_root, args.as_of), ensure_ascii=False))
