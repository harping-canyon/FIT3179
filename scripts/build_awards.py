"""Join an independent, frozen Spiel des Jahres extract to the BGG cohort.

Run on a fresh clone with `python scripts/build_awards.py`. No raw BGG inputs
or network access are needed. Award facts and reviewed title aliases are kept
in data/sources/sdj-awards.json, with a source URL for every record.
"""
import hashlib
import json
from pathlib import Path
from build_player_tree import build_player_tree

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def enrich_awards(games):
    source_path = DATA / 'sources/sdj-awards.json'
    source = json.loads(source_path.read_text(encoding='utf-8'))
    records = source['winners']
    assert sorted(r['year'] for r in records) == list(range(1979, 2025))
    by_id = {g['id']: g for g in games}
    winners = []
    for row in records:
        if row['bgg_id'] is None:
            continue
        game = by_id[row['bgg_id']]
        assert game['title'] == row['bgg_title']
        assert game['year'] <= row['year']
        winners.append({'id': game['id'], 'award_year': row['year'],
                        'award': 'Spiel des Jahres', 'source_url': row['source_url']})
    assert len(winners) == len({w['id'] for w in winners}) == 14
    winner_ids = {w['id'] for w in winners}
    tree = []
    for scope, cohort in [('all', games), ('winners', [g for g in games if g['id'] in winner_ids])]:
        rows = build_player_tree(cohort)
        # Omit empty branches so stratify/treemap never allocates an empty box.
        rows = [r for r in rows if r.get('total', 1) > 0]
        for row in rows:
            row.update(scope=scope, cohort_n=len(cohort))
        tree.extend(rows)
    output = {'award_winners.json': winners, 'player_tree_awards.json': tree}
    sizes = {'sources/sdj-awards.json': source_path.stat().st_size}
    for name, value in output.items():
        path = DATA / name
        path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
        sizes[name] = path.stat().st_size
    provenance = {
        'organisation': source['organisation'], 'catalogue': source['catalogue'],
        'extract': './sources/sdj-awards.json', 'retrieved': source['retrieved'],
        'scope': source['scope'], 'matching': source['matching'],
        'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
        'source_winners': len(records), 'matched_story_games': len(winners),
        'charts': ['ratings.json', 'player-counts.json'],
    }
    return sizes, provenance

def main():
    games = json.loads((DATA/'games.json').read_text(encoding='utf-8'))
    sizes, provenance = enrich_awards(games)
    path = DATA/'metadata.json'
    meta = json.loads(path.read_text(encoding='utf-8'))
    meta['updated'] = '2026-10-27'
    meta['pipeline_version'] = 5
    meta['sources']['awards'] = provenance
    meta['files'].update(sizes)
    # A clone may omit final newlines present in the original build outputs.
    meta['files'] = {name: (DATA/name).stat().st_size for name in meta['files']}
    meta['output_bytes_excluding_metadata'] = sum(meta['files'].values())
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"Joined {provenance['matched_story_games']} of {provenance['source_winners']} award winners to {len(games)} story games")

if __name__ == '__main__':
    main()
