"""Deterministic chart datasets derived from the frozen relational source.

All joins use IDs; multi-valued categories and place links stay separate.
Only the Python standard library is required. Called by build_data.py.
"""
from advanced_data import build_advanced
import csv
import io
import math
import re
import zipfile
from collections import Counter, defaultdict

EXAMPLES = [9209, 822, 183394, 2651, 193738, 12333]
THEMES = ['Economic', 'City Building', 'Transportation', 'Trains']
MECHANIC_LABELS = {
    'Hand Management': ('Managing a hand', 'Choosing how and when to use items in your hand.'),
    'Dice Rolling': ('Rolling dice', 'Using dice as part of play.'),
    'Set Collection': ('Collecting sets', 'Collecting combinations of items for a benefit.'),
    'Area Majority / Influence': ('Competing for influence', 'Comparing influence or presence within areas.'),
    'Open Drafting': ('Choosing from a shared pool', 'Taking turns choosing openly available items.'),
}


def read_rows(raw, name):
    with (raw / name).open(encoding='utf-8-sig', newline='') as source:
        yield from csv.DictReader(source)


def quantile(values, p):
    """Linear interpolation at (n-1)*p; the pandas default convention."""
    values = sorted(values)
    index = (len(values) - 1) * p
    low, high = math.floor(index), math.ceil(index)
    return values[low] + (values[high] - values[low]) * (index - low)


def build_story(base, country_links, countries, raw, codes, normalise):
    families = {int(r['id_family']): r['family'] for r in read_rows(raw, 'family.csv')}
    place_links = defaultdict(set)
    for row in read_rows(raw, 'b_game_family.csv'):
        game_id = int(row['id_bgg'])
        label = families[int(row['id_family'])]
        if game_id in base and label.startswith(('Country: ', 'Cities: ')):
            place_links[label].add(game_id)
    ids = set().union(*place_links.values())
    assert len(ids) == 871, 'Frozen cohort changed'

    def memberships(entity):
        names = {int(r['id_' + entity]): r[entity] for r in read_rows(raw, entity + '.csv')}
        result = defaultdict(set)
        for row in read_rows(raw, 'b_game_' + entity + '.csv'):
            game_id = int(row['id_bgg'])
            if game_id in ids:
                result[names[int(row['id_' + entity])]].add(game_id)
        return result

    categories, mechanics = memberships('category'), memberships('mechanic')
    war_ids = categories['Wargame']
    games = [{**base[i], 'is_wargame': i in war_ids,
              'group': 'Wargame' if i in war_ids else 'Other games'} for i in sorted(ids)]
    assert len(war_ids) == 145
    assert all(g['minutes'] is None or g['minutes'] > 0 for g in games)
    assert all(g['min_players'] is not None and g['max_players'] is not None
               and 1 <= g['min_players'] <= g['max_players']
               and g['min_players'].is_integer() and g['max_players'].is_integer() for g in games)
    for g in games:
        g['min_players'], g['max_players'] = int(g['min_players']), int(g['max_players'])

    for country in countries:
        linked = country_links[country['iso']]
        country['wargame_count'] = len(linked & war_ids)
        country['other_count'] = len(linked - war_ids)
        country['eligible_ratio'] = len(linked) >= 20
        country['wargame_share'] = country['wargame_count'] / len(linked)
    eligible = [c for c in countries if c['eligible_ratio']]
    assert len(eligible) == 12
    matrix = []
    for country in eligible:
        for theme in THEMES:
            n = len(country_links[country['iso']] & categories[theme])
            matrix.append({'iso': country['iso'], 'country': country['country'], 'category': theme,
                           'numerator': n, 'denominator': country['game_count'], 'share': n / country['game_count']})
    ranks = []
    for group, field in [('Wargame', 'wargame_count'), ('Other games', 'other_count')]:
        for country in eligible:
            # Competition rank: equal counts share a rank, subsequent ranks skip.
            rank = 1 + sum(c[field] > country[field] for c in eligible)
            ranks.append({'iso': country['iso'], 'country': country['country'], 'group': group,
                          'game_count': country[field], 'rank': rank, 'country_sample': country['game_count']})

    # Independent, reproducible city matching from the original gazetteer.
    with (raw / 'countryInfo.txt').open(encoding='utf-8') as source:
        country_info = {r[0]: {'name': r[4], 'continent': r[8]} for r in csv.reader((line for line in source if not line.startswith('#')), delimiter='\t') if len(r) > 8}
    lookup, gazetteer = defaultdict(set), {}
    with zipfile.ZipFile(raw / 'cities15000.zip') as archive:
        with io.TextIOWrapper(archive.open('cities15000.txt'), encoding='utf-8') as stream:
            for row in csv.reader(stream, delimiter='\t'):
                gid = int(row[0])
                gazetteer[gid] = {'id': gid, 'city': row[1], 'country_iso': row[8],
                                  'latitude': float(row[4]), 'longitude': float(row[5]), 'country': country_info[row[8]]['name'], 'continent': country_info[row[8]]['continent']}
                for name in set([row[1], row[2], *row[3].split(',')]):
                    if name:
                        lookup[(row[8], normalise(name))].add(gid)
    city_links, city_audit = defaultdict(set), []
    for label, linked in sorted(place_links.items()):
        if not label.startswith('Cities: '):
            continue
        parsed = re.fullmatch(r'(.+?) \((.+)\)', label.removeprefix('Cities: '))
        candidates = set()
        if parsed:
            city, context = parsed.groups()
            code = codes.get(normalise(context.split(',')[-1].strip()))
            candidates = lookup.get((code, normalise(city)), set())
        status = 'matched' if len(candidates) == 1 else 'ambiguous' if candidates else 'unmatched'
        record = {'tag': label, 'status': status, 'candidate_ids': sorted(candidates), 'game_ids': sorted(linked)}
        city_audit.append(record)
        if status == 'matched':
            city_links[next(iter(candidates))].update(linked)
    cities = []
    for gid, linked in sorted(city_links.items()):
        examples = sorted(linked, key=lambda i: (-base[i]['rating_votes'], base[i]['title']))[:3]
        cities.append({**gazetteer[gid], 'game_count': len(linked),
                       'example_titles': ', '.join(base[i]['title'] for i in examples)})
    assert len(cities) == 121 and len(set().union(*city_links.values())) == 283

    boxes = []
    for group in ['Wargame', 'Other games']:
        values = [g['complexity'] for g in games if g['group'] == group]
        q1, median, q3 = [quantile(values, p) for p in [.25, .5, .75]]
        iqr = q3 - q1
        inside = [v for v in values if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]
        boxes.append({'group': group, 'n': len(values), 'q1': q1, 'median': median, 'q3': q3,
                      'whisker_low': min(inside), 'whisker_high': max(inside),
                      'outliers': sorted(v for v in values if v < min(inside) or v > max(inside))})
    duration_counts = Counter(g['minutes'] for g in games if g['minutes'] is not None)
    duration_n = sum(duration_counts.values())
    ecdf = [{'minutes': 0, 'cumulative_n': 0, 'denominator': duration_n, 'share': 0}]
    total = 0
    for minutes, n in sorted(duration_counts.items()):
        total += n
        ecdf.append({'minutes': minutes, 'cumulative_n': total, 'denominator': duration_n, 'share': total / duration_n})
    player_counts = Counter('Solo option' if g['min_players'] == 1 else
                            'Exactly two only' if g['min_players'] == g['max_players'] == 2 else
                            'Group options, no solo' for g in games)
    players = [{'category': name, 'n': player_counts[name], 'denominator': len(games),
                'share': player_counts[name] / len(games), 'order': i}
               for i, name in enumerate(['Solo option', 'Exactly two only', 'Group options, no solo'])]
    top_mechanics = sorted(mechanics, key=lambda name: (-len(mechanics[name]), name))[:5]
    mechanic_rows = [{'original_label': name, 'display_label': MECHANIC_LABELS[name][0],
                     'definition': MECHANIC_LABELS[name][1], 'game_count': len(mechanics[name]),
                     'denominator': len(games)} for name in top_mechanics]
    by_id = {g['id']: g for g in games}
    examples = [{**by_id[i], 'order': order, 'source_url': f'https://boardgamegeek.com/boardgame/{i}',
                 'official_edition_check': 'pending'} for order, i in enumerate(EXAMPLES)]
    evidence = {
        'story_games': len(games), 'wargames': len(war_ids), 'other_games': len(ids - war_ids),
        'time_valid': duration_n, 'time_missing': len(games) - duration_n,
        'missing_time_wargames': sum(g['minutes'] is None and g['is_wargame'] for g in games),
        'at_most_60_minutes': sum(n for t, n in duration_counts.items() if t <= 60),
        'city_tag_count': len(city_audit),
        'city_locations_by_continent': dict(sorted(Counter(c['continent'] for c in cities).items())), 'matched_city_locations': len(cities),
        'matched_city_games': len(set().union(*city_links.values())),
        'city_tagged_games': len(set().union(*(v for k, v in place_links.items() if k.startswith('Cities: ')))),
        'quantile_method': 'Linear interpolation at (n-1)*p; whiskers are outermost observations within 1.5 times the middle-half range.',
        'rank_method': 'Descending competition rank within the same 12 countries with >=20 associated games; ties share rank.',
        'scope_note': 'Place associations are catalogue tags, not verified literal game settings, origin, sales or player geography.',
    }
    assert duration_n == 854 and evidence['at_most_60_minutes'] == 428
    return {**build_advanced(games, examples, mechanics, top_mechanics, MECHANIC_LABELS), 'games.json': games, 'cities.json': cities, 'country_categories.json': matrix,
            'country_ranks.json': ranks, 'complexity_summary.json': boxes,
            'mechanics.json': mechanic_rows, 'time_ecdf.json': ecdf, 'players.json': players,
            'examples.json': examples, 'story_evidence.json': evidence,
            'geography_audit.json': {'cities': city_audit, 'country_game_ids': {k: sorted(v) for k, v in sorted(country_links.items())}}}
