"""Additional comparisons; every count derives from the frozen cohort."""
from itertools import combinations
from statistics import median
import math

def build_advanced(games, examples, mechanics, top, labels):
    nodes = []
    for i, name in enumerate(top):
        # Place the strongest overlaps on the perimeter; coordinates carry no data.
        order = ['Hand Management', 'Set Collection', 'Open Drafting', 'Area Majority / Influence', 'Dice Rolling']
        angle = -math.pi / 2 + order.index(name) * 2 * math.pi / len(top)
        nodes.append({'name': name, 'label': labels[name][0], 'n': len(mechanics[name]),
                      'x': math.cos(angle), 'y': math.sin(angle)})
    edges = []
    for a, b in combinations(nodes, 2):
        shared = mechanics[a['name']] & mechanics[b['name']]
        edges.append({'source': a['label'], 'target': b['label'], 'n': len(shared),
                      'x': a['x'], 'y': a['y'], 'x2': b['x'], 'y2': b['y'],
                      'game_ids': sorted(shared)})
    axes = [('complexity', 'Complexity', 1, 5), ('minutes', 'Minutes', 0, 180), ('max_players', 'Maximum players', 1, 6)]
    profiles = [{'id': g['id'], 'title': g['title'], 'axis': label, 'order': i, 'value': g[field],
                 'position': (g[field]-low)/(high-low), 'minimum_players': g['min_players']}
                for g in examples for i, (field, label, low, high) in enumerate(axes)]
    times = [{'group': group, 'n': len(vals), 'median': median(vals)}
             for group in ['Wargame', 'Other games']
             for vals in [[g['minutes'] for g in games if g['group']==group and g['minutes'] is not None]]]
    return {'mechanic_nodes.json': nodes, 'mechanic_edges.json': edges, 'game_profiles.json': profiles,
            'duration_summary.json': times}
