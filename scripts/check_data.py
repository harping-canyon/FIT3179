"""Audit exported data against source-derived evidence and chart contracts."""
import json
import math
from collections import Counter
from pathlib import Path
from statistics import quantiles

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def main():
    countries, games, cities = load('countries.json'), load('games.json'), load('cities.json')
    meta, evidence, audit = load('metadata.json'), load('story_evidence.json'), load('geography_audit.json')
    assert len(games) == len({g['id'] for g in games}) == meta['story_games'] == 871
    by_id = {g['id']: g for g in games}
    assert all(1900 <= g['year'] <= 2024 and g['rating_votes'] >= 1000 and g['complexity_votes'] >= 30
               and 1 <= g['rating'] <= 10 and 1 <= g['complexity'] <= 5 for g in games)
    assert len(countries) == len({c['iso'] for c in countries}) == 98
    assert countries == sorted(countries, key=lambda c: (-c['game_count'], c['country']))
    for c in countries:
        linked = audit['country_game_ids'][c['iso']]
        assert len(linked) == len(set(linked)) == c['game_count']
        assert set(linked) <= by_id.keys()
        assert sum(by_id[i]['is_wargame'] for i in linked) == c['wargame_count']
        assert c['other_count'] + c['wargame_count'] == c['game_count']
        assert c['wargame_share'] == c['wargame_count'] / c['game_count']
        assert c['eligible_ratio'] == (c['game_count'] >= 20)
    assert [(c['iso'], c['game_count']) for c in countries[:5]] == [('US',128),('GB',113),('FR',104),('JP',101),('DE',93)]
    polygons = {f['properties']['iso'] for f in load('world.geojson')['features']}
    mapped = [c for c in countries if c['longitude'] is not None]
    assert len(mapped) == meta['countries_with_shape_point'] == 89
    assert all(c['iso'] in polygons and -180 <= c['longitude'] <= 180 and -90 <= c['latitude'] <= 90 for c in mapped)
    assert all(c['latitude'] is None for c in countries if c['longitude'] is None)
    assert len(cities) == len({c['id'] for c in cities}) == 121
    assert all(-180 <= c['longitude'] <= 180 and -90 <= c['latitude'] <= 90 for c in cities)
    city_ids = {}
    for row in audit['cities']:
        if row['status'] == 'matched':
            assert len(row['candidate_ids']) == 1
            city_ids.setdefault(row['candidate_ids'][0], set()).update(row['game_ids'])
    assert all(len(city_ids[c['id']]) == c['game_count'] for c in cities)
    assert len(set().union(*city_ids.values())) == evidence['matched_city_games'] == 283
    assert Counter(c['continent'] for c in cities) == evidence['city_locations_by_continent']
    for row in load('country_categories.json'):
        assert 0 <= row['numerator'] <= row['denominator'] and row['denominator'] >= 20
        assert row['share'] == row['numerator'] / row['denominator']
    assert len(load('country_categories.json')) == 48
    heatmap = load('../charts/themes.json')
    low, high = heatmap['layer'][0]['encoding']['color']['scale']['domain']
    assert all(low <= row['share'] <= high for row in load('country_categories.json'))

    for summary in load('complexity_summary.json'):
        values = [g['complexity'] for g in games if g['group'] == summary['group']]
        quartiles = quantiles(values, n=4, method='inclusive')
        assert summary['n'] == len(values)
        assert all(math.isclose(summary[key], value) for key, value in zip(['q1','median','q3'], quartiles))
    valid = [g['minutes'] for g in games if g['minutes'] is not None]
    assert len(valid) == 854
    assert sum(g['minutes'] is None and g['is_wargame'] for g in games) == 17
    for row in load('time_ecdf.json'):
        assert row['denominator'] == len(valid)
        assert row['cumulative_n'] == sum(t <= row['minutes'] for t in valid)
        assert row['share'] == row['cumulative_n'] / len(valid)
    assert load('time_ecdf.json')[-1]['share'] == 1
    assert sum(p['n'] for p in load('players.json')) == 871
    assert [p['n'] for p in load('players.json')] == [240,100,531]
    # Independently derive each treemap leaf from game fields, not the builder.
    tree = load('player_tree.json')
    tree_ids = {row['id'] for row in tree}
    assert len(tree_ids) == len(tree)
    leaves = [row for row in tree if 'n' in row]
    assert len(leaves) == 7 and sum(row['n'] for row in leaves) == len(games)
    bounds = {'Solo only': (1, 1), '2 players': (2, 2),
              '3–4 players': (3, 4), '5+ players': (5, float('inf'))}
    assigned = set()
    for leaf in leaves:
        assert leaf['parent'] in tree_ids
        low, high = bounds[leaf['label']]
        members = {g['id'] for g in games
                   if (g['min_players'] == 1) == (leaf['parent'] == 'solo')
                   and low <= g['max_players'] <= high}
        assert len(members) == leaf['n'] and not (members & assigned)
        assigned.update(members)
    assert assigned == set(by_id)
    for parent in [row for row in tree if 'total' in row]:
        assert parent['total'] == sum(row['n'] for row in leaves if row['parent'] == parent['id'])
    rank_rows = load('country_ranks.json')
    for row in rank_rows:
        group = [r for r in rank_rows if r['group'] == row['group']]
        assert row['rank'] == 1 + sum(r['game_count'] > row['game_count'] for r in group)
    specs = [load('../charts/' + name) for name in ['country-counts.json','country-counts-europe.json']]
    scales = [next(layer['encoding']['size']['scale'] for layer in spec['layer'] if layer['mark']['type'] == 'circle') for spec in specs]
    assert scales[0] == scales[1] and scales[0]['type'] == 'linear' and scales[0]['domain'] == [0,128]
    # Check new comparisons against source membership and native game fields.
    from statistics import median
    from story_data import read_rows
    from build_data import RAW
    names = {int(r['id_mechanic']): r['mechanic'] for r in read_rows(RAW, 'mechanic.csv')}
    memberships = {}
    cohort = {g['id'] for g in games}
    for r in read_rows(RAW, 'b_game_mechanic.csv'):
        if int(r['id_bgg']) in cohort:
            memberships.setdefault(names[int(r['id_mechanic'])], set()).add(int(r['id_bgg']))
    nodes = load('mechanic_nodes.json')
    lookup = {n['label']: memberships[n['name']] for n in nodes}
    assert len(nodes) == 5 and len(load('mechanic_edges.json')) == 10
    assert all(n['n'] == len(lookup[n['label']]) for n in nodes)
    for edge in load('mechanic_edges.json'):
        shared = lookup[edge['source']] & lookup[edge['target']]
        assert set(edge['game_ids']) == shared and edge['n'] == len(shared)
    for row in load('duration_summary.json'):
        values = [g['minutes'] for g in games if g['group']==row['group'] and g['minutes'] is not None]
        assert row['n'] == len(values) and row['median'] == median(values)
    examples = {g['id']: g for g in load('examples.json')}
    axes = {'Complexity': ('complexity',1,5), 'Minutes': ('minutes',0,180), 'Maximum players': ('max_players',1,6)}
    assert len(load('game_profiles.json')) == 18
    for row in load('game_profiles.json'):
        field, low, high = axes[row['axis']]
        assert row['value'] == examples[row['id']][field]
        assert math.isclose(row['position'], (row['value']-low)/(high-low))
        assert 0 <= row['position'] <= 1
    for name, size in meta['files'].items():
        assert (DATA / name).stat().st_size == size, f'Stale metadata for {name}'
    assert sum(meta['files'].values()) == meta['output_bytes_excluding_metadata']
    payload = sum(p.stat().st_size for p in DATA.iterdir() if p.is_file())
    assert payload < 2_000_000
    print(f'PASS: {len(games)} games, {len(cities)} cities, {len(countries)} country groups; all public data {payload:,} bytes')


if __name__ == '__main__':
    main()
