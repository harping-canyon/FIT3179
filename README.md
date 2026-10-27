# The world on the table

An interactive visual story about 871 board games, their geographic associations and playing demands.

[View the visualisation](https://harping-canyon.github.io/FIT3179/)

## Run locally

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/. No build step is required.

Chart definitions are in `charts/`, prepared data and provenance in `data/`, and page components in `src/`.

## Independent awards data

The ratings scatterplot outlines Spiel des Jahres winners, and the player-count
treemap can show just those winners. Both join the BGG cohort to an independent
source: the [Spiel des Jahres e.V. catalogue](https://www.spiel-des-jahres.de/spiele/).

`data/sources/sdj-awards.json` records all 46 main-award winners from 1979–2024,
with a source URL per winner. Fourteen match the 871-game geographic cohort.
Eleven use normalised exact titles; three use reviewed German-to-English aliases
(Sherlock Holmes, Alhambra and Ticket to Ride). Awards attach only to the matched
game identity, not its expansions or other editions. The other 32 winners are
outside this story cohort, not additional plotted games. This is an award-based
subset, not a representative sample of all winners or a causal comparison.

Rebuild the small joined files on a fresh clone with:

```sh
python scripts/build_awards.py
python scripts/check_awards.py
python scripts/check_site.py
```

The complete `build_data.py` pipeline also applies this join, but requires the
original frozen BGG and geographic research inputs, which are excluded from Git.
The source extract was retrieved on 27 October 2026 from the organiser's public
WordPress API (`/wp-json/wp/v2/spiele`, all 10 pages). Winner status comes from
`preiskat-spiel-des-jahres`, and award years from the catalogue's `oferjahr`
selector. Only factual titles, years, URLs and match decisions are retained;
no review prose or artwork is redistributed.
