"""Audit independent award joins and both treemap cohorts without raw BGG files."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
def load(path):
    return json.loads((DATA/path).read_text(encoding='utf-8'))

def main():
    games = load('games.json')
    by_id = {g['id']: g for g in games}
    source = load('sources/sdj-awards.json')
    records = source['winners']
    assert [r['year'] for r in records] == list(range(1979, 2025))
    matches = {r['bgg_id']: r for r in records if r['bgg_id'] is not None}
    assert len(matches) == 14
    assert sum(r['match_method'] == 'reviewed translated title' for r in matches.values()) == 3
    winners = load('award_winners.json')
    assert len(winners) == len({r['id'] for r in winners}) == len(matches)
    for row in winners:
        ref = matches[row['id']]
        assert row['award_year'] == ref['year']
        assert row['source_url'] == ref['source_url']
        assert row['source_url'].startswith('https://www.spiel-des-jahres.de/spiele/')
        assert ref['bgg_title'] == by_id[row['id']]['title']
        assert by_id[row['id']]['year'] <= row['award_year']
    assert matches[9209]['year'] == 2004 and matches[822]['year'] == 2001
    # No automatic inheritance by expansions or separate editions.
    assert not {14996, 160069, 45358, 431} & matches.keys()
    tree = load('player_tree_awards.json')
    for scope, selected in [('all', games), ('winners', [by_id[i] for i in matches])]:
        rows = [r for r in tree if r['scope'] == scope]
        assert len(rows) == len({r['id'] for r in rows})
        expected = Counter()
        for game in selected:
            parent = 'solo' if game['min_players'] == 1 else 'company'
            n = game['max_players']
            label = 'Solo only' if n == 1 else '2 players' if n == 2 else '3–4 players' if n <= 4 else '5+ players'
            expected[parent, label] += 1
        actual = {(r['parent'], r['label']): r['n'] for r in rows if 'n' in r}
        assert actual == dict(expected)
        assert sum(actual.values()) == len(selected)
        assert all(r['cohort_n'] == len(selected) for r in rows)
        for parent in [r for r in rows if 'total' in r]:
            assert parent['total'] == sum(n for (p, _), n in expected.items() if p == parent['id'])
        if scope == 'all':
            assert [{k:v for k,v in r.items() if k not in ('scope','cohort_n')} for r in rows] == load('player_tree.json')
    meta = load('metadata.json')
    provenance = meta['sources']['awards']
    assert provenance['sha256'] == hashlib.sha256((DATA/'sources/sdj-awards.json').read_bytes()).hexdigest()
    assert provenance['source_winners'] == 46 and provenance['matched_story_games'] == 14
    for name, size in meta['files'].items():
        assert (DATA/name).stat().st_size == size, name
    assert sum(meta['files'].values()) == meta['output_bytes_excluding_metadata']
    assert sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file()) < 2_000_000
    print('PASS: 46 sourced winners, 14 unique matches, no edition inheritance, both treemap partitions and denominators, provenance hashes and payload')

if __name__ == '__main__':
    main()
