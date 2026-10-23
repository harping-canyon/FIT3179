"""Build a disjoint player-support hierarchy from game records."""
import json
from collections import Counter
from pathlib import Path


def build_player_tree(games):
    counts = Counter()
    for game in games:
        assert 1 <= game['min_players'] <= game['max_players']
        parent = 'solo' if game['min_players'] == 1 else 'company'
        maximum = game['max_players']
        label = ('Solo only' if maximum == 1 else '2 players' if maximum == 2
                 else '3–4 players' if maximum <= 4 else '5+ players')
        counts[parent, label] += 1
    rows = [{'id': 'root', 'parent': None, 'label': 'All games'}]
    for parent, label in [('solo', 'Solo option'), ('company', 'Needs company')]:
        rows.append({'id': parent, 'parent': 'root', 'label': label,
                     'total': sum(n for (p, _), n in counts.items() if p == parent)})
    for i, ((parent, label), n) in enumerate(counts.items()):
        rows.append({'id': str(i), 'parent': parent, 'label': label, 'n': n})
    assert sum(row.get('n', 0) for row in rows) == len(games)
    return rows


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    games = json.loads((root / 'data/games.json').read_text(encoding='utf-8'))
    print(json.dumps(build_player_tree(games), ensure_ascii=False, indent=2))
