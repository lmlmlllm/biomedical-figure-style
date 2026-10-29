#!/usr/bin/env python3
"""Read selected style notes without loading the complete catalog into context."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from refresh_review_scope import assess


# Canonical CLI values plus explicitly supported historical strings, unchanged.
STATUS_VALUES = {
    'image_range': ('full_figure', 'panel', 'crop', 'unknown', 'partial_panel'),
    'clarity': ('original_or_high', 'clear', 'low_preview', 'unknown'),
    'access': ('viewed', 'caption_only', 'metadata_only', 'blocked', 'unknown'),
    'saved': ('archived', 'link_only', 'pending', 'missing'),
    'license': ('verified', 'verified_with_exceptions', 'restricted', 'unverified',
                'verified_CC_BY_4_0_with_credit_note', 'verified_open', 'unknown', 'pending'),
    'content': ('image_read', 'text_aligned', 'key_evidence_checked',
                'conflict_or_insufficient', 'unknown', 'insufficient'),
    'rule': ('candidate', 'integrated', 'tested', 'restricted_use', 'unknown'),
}


def first_recorded(*values):
    """Use explicit aliases only when the preferred value is absent or null."""
    return next((value for value in values if value is not None), None)


def category_text(value):
    """Search explicit category labels without changing the stored schema."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ' / '.join(label for label in value if isinstance(label, str))
    return None


def summary_metadata(entry, card, card_path, has_card, status):
    """Project bounded explicit metadata, never a card or its history."""
    truncated = []

    def short(value, maximum, field):
        if not isinstance(value, str):
            return None
        if len(value) > maximum:
            truncated.append(field)
            return value[:maximum - 1] + '…'
        return value

    source = entry.get('source') or {}
    task = (card or {}).get('task')
    task_field = 'design_card.task' if task is not None else None
    if isinstance(task, dict):
        task_field, task = next(((f'design_card.task.{key}', task[key]) for key in (
            'core_claim', 'one_sentence_claim', 'one_sentence_reading',
            'reading_claim', 'reading_takeaway', 'reusable_design_problem',
            'scientific_task', 'scientific_question', 'use_when')
            if task.get(key) is not None), (None, None))
    result = {
        'id': short(entry['id'], 120, 'id'),
        'title': short(entry.get('title'), 300, 'title'),
        'category': short(category_text(entry.get('category')), 120, 'category'),
        'layout_ids': [short(v, 64, 'layout_ids') for v in entry.get('layout_ids', [])[:12]
                       if isinstance(v, str)],
        'task': short(task, 200, 'task'), 'task_field': task_field,
        'design_note': short(entry.get('design_note'), 420, 'design_note'),
        'image_status': short(entry.get('image_status'), 80, 'image_status'),
        'reference_mode': short(entry.get('reference_mode'), 120, 'reference_mode'),
        'has_design_card': has_card,
        'design_card_ref': short(str(card_path) + '#' + entry['id'], 1600,
                                 'design_card_ref') if has_card else None,
        'learning_status': {
            key: short(status.get(key), 80, 'learning_status.' + key)
            for key in ('image_range', 'clarity', 'access', 'saved',
                        'license', 'content', 'rule')
        },
        'truncated_fields': truncated,
    }
    if len(entry.get('layout_ids', [])) > 12:
        truncated.append('layout_ids')
    if source.get('origin') == 'published_review':
        limits = {'article_title': 300, 'journal': 160, 'article_type': 80, 'doi': 160,
                  'first_online_date': 32, 'published_date': 32,
                  'article_url': 1200, 'figure_number': 64, 'figure_url': 1200}
        result['source'] = {
            field: short(first_recorded(source.get('article_title'), source.get('title'))
                         if field == 'article_title' else source.get(field),
                         maximum, 'source.' + field)
            for field, maximum in limits.items()
        }
        figure_number = source.get('figure_number')
        if isinstance(figure_number, int) and not isinstance(figure_number, bool):
            result['source']['figure_number'] = figure_number
    return result


def search(root, ids, layouts, query, limit, today, include_historical=False,
           status_filters=None, require_design_card=False, summary_only=False):
    catalog = json.loads((root / 'references/catalog.json').read_text())
    policy = json.loads((root / 'references/review_scope.json').read_text())
    card_path = root / 'references/design_cards.json'
    learning = json.loads(card_path.read_text()) if card_path.exists() else {'cards': {}}
    cards = learning.get('cards', {})
    tokens = [t.casefold() for t in re.split(r'\s+', query.strip()) if t]
    wanted_ids, wanted_layouts = set(ids), set(layouts)
    results = []
    for entry in catalog['entries']:
        if require_design_card and entry['id'] not in cards:
            continue
        source = entry.get('source') or {}
        article_title = first_recorded(source.get('article_title'), source.get('title'))
        card = cards.get(entry['id'])
        status = {'image_range': 'unknown', 'clarity': 'unknown', 'access': 'unknown',
                  'saved': entry.get('image_status', 'pending'), 'license': 'unverified',
                  'content': 'unknown', 'rule': 'unknown'}
        # Card status overrides catalog status; status overrides status_axes within each.
        for record in (entry, card):
            if isinstance(record, dict):
                for field in ('status_axes', 'status'):
                    recorded = record.get(field)
                    if isinstance(recorded, dict):
                        status.update({key: value for key, value in recorded.items()
                                       if key in status and isinstance(value, str)
                                       and value in STATUS_VALUES[key]})
        if any(status.get(k) != v for k, v in (status_filters or {}).items() if v):
            continue
        published = source.get('origin') == 'published_review'
        eligible, reason, cutoff = assess(source, policy, today) if published else (
            None, 'user_style_example', None)
        if published and not eligible and not include_historical:
            continue
        if wanted_ids and entry['id'] not in wanted_ids:
            continue
        if wanted_layouts and not wanted_layouts.issubset(entry.get('layout_ids', [])):
            continue
        if summary_only:
            result = summary_metadata(entry, card, card_path, entry['id'] in cards, status)
            title = (result['title'] or '').casefold()
            category = (result['category'] or '').casefold()
            note = (result['design_note'] or '').casefold()
            text = '\n'.join([title, category, note, (result['task'] or '').casefold(),
                              (result.get('source', {}).get('article_title') or '').casefold()])
        else:
            title = (entry.get('title') or '').casefold()
            category = (category_text(entry.get('category')) or '').casefold()
            note = (entry.get('design_note') or '').casefold()
            text = '\n'.join([title, category, note,
                              (article_title or '').casefold()])
            if card:
                text += '\n' + json.dumps(card, ensure_ascii=False).casefold()
        if tokens and not all(t in text for t in tokens):
            continue
        score = sum(4 * (t in title) + 2 * (t in category) + (t in note)
                    for t in tokens)
        if summary_only:
            result.update(scope_eligible_today=eligible, scope_reason_today=reason)
            if published:
                result['scope_window'] = [cutoff.isoformat(), today.isoformat()]
        else:
            result = {
                'id': entry['id'], 'title': entry.get('title'),
                'category': entry.get('category'), 'layout_ids': entry.get('layout_ids', []),
                'design_note': entry.get('design_note'),
                'observation_basis': entry.get('observation_basis'),
                'image_status': entry.get('image_status'),
                'image_path': entry.get('image_path'),
                'scientific_content_verified': entry.get('scientific_content_verified', False),
                'reference_mode': entry.get('reference_mode'),
                'scope_eligible_today': eligible, 'scope_reason_today': reason,
                'learning_status': status,
                'design_card': card,
                'design_card_ref': str(card_path) + '#' + entry['id'] if card else None,
            }
            if published:
                metric = source.get('journal_metric', {})
                result['source'] = {
                    k: source.get(k) for k in (
                        'article_title', 'journal', 'authors', 'article_type', 'doi',
                        'first_online_date', 'published_date', 'article_url',
                        'figure_number', 'figure_url', 'image_url', 'license_name',
                        'license_url', 'credit_note', 'attribution')
                }
                rights = source.get('rights')
                rights = rights if isinstance(rights, dict) else {}
                metadata_fallbacks = {
                    'article_title': article_title,
                    'authors': source.get('all_authors'),
                    'license_name': first_recorded(source.get('license'),
                                                   rights.get('license'),
                                                   rights.get('article_license')),
                    'license_url': rights.get('license_url'),
                    'credit_note': first_recorded(source.get('figure_specific_credit'),
                                                  source.get('caption_credit_verbatim')),
                    'attribution': source.get('article_attribution'),
                }
                for field, fallback in metadata_fallbacks.items():
                    if result['source'][field] is None:
                        result['source'][field] = fallback
                for field in ('rights', 'third_party_subpanel_boundary'):
                    if field in source:
                        result['source'][field] = source[field]
                result['source']['journal_metric'] = {
                    k: metric.get(k) for k in (
                        'journal_impact_factor', 'jif_year', 'verification_status',
                        'source_url')
                }
                result['scope_window'] = [cutoff.isoformat(), today.isoformat()]
        results.append((score, int(entry.get('batch', 0)),
                        int(entry.get('attachment_number', 0)), result))
    results.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    response = {
        'as_of': today.isoformat(), 'catalog_count': len(catalog['entries']),
        'matched_count': len(results), 'returned_count': min(len(results), limit),
        'historical_entries_requested': include_historical,
        'ranking': 'keyword relevance, then newest case batch; not journal or scientific ranking',
        'entries': [x[3] for x in results[:limit]],
    }
    if require_design_card:
        response['design_card_required'] = True
    if summary_only:
        response['summary_only'] = True
        response['summary_limits'] = {'title': 300, 'task': 200, 'design_note': 420,
                                      'source.article_title': 300}
        response['search_fields'] = ['title', 'category', 'design_note', 'task',
                                     'source.article_title']
        response['summary_boundary'] = ('Only displayed, length-limited metadata is searched; '
                                        'truncated_fields names shortened values. No full card or history; '
                                        "exact comparison-card freezing is the caller's responsibility.")
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', action='append', default=[], help='Exact case ID; repeatable')
    parser.add_argument('--layout', action='append', default=[], help='Required layout ID; repeatable')
    parser.add_argument('--query', default='', help='All whitespace-separated keywords must match')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--require-design-card', action='store_true',
                        help='Require an exact ID key in design_cards.json before ranking/limiting')
    parser.add_argument('--summary-only', action='store_true',
                        help='Search and return only bounded metadata; omit full cards and history')
    parser.add_argument('--as-of', type=date.fromisoformat)
    parser.add_argument('--include-historical', action='store_true',
                        help='Include expired/unverified published cases, explicitly labelled')
    for flag, axis in {
        'image-range': 'image_range', 'clarity': 'clarity',
        'access-status': 'access', 'saved-status': 'saved',
        'license-status': 'license', 'content-status': 'content', 'rule-status': 'rule',
    }.items():
        parser.add_argument('--' + flag, choices=STATUS_VALUES[axis])
    parser.add_argument('--skill-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error('--limit must be between 1 and 30')
    root = args.skill_root.resolve()
    policy = json.loads((root / 'references/review_scope.json').read_text())
    today = args.as_of or datetime.now(ZoneInfo(policy['timezone'])).date()
    filters = {'image_range': args.image_range, 'clarity': args.clarity,
               'access': args.access_status, 'saved': args.saved_status,
               'license': args.license_status, 'content': args.content_status,
               'rule': args.rule_status}
    print(json.dumps(search(root, args.id, args.layout, args.query, args.limit,
                            today, args.include_historical, filters,
                            require_design_card=args.require_design_card,
                            summary_only=args.summary_only), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
