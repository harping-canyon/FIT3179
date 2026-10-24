import {setupNavigation} from './navigation.js?v=13';
import {charts} from './charts.js?v=33';
import {createChartCard} from './chart-card.js?v=31';
import {renderChart} from './vega.js?v=12';

async function loadCoverage() {
  const response = await fetch('./data/metadata.json');
  if (!response.ok) throw new Error(`Cannot load data notes (${response.status}).`);
  const metadata = await response.json();
  const note = document.querySelector('#coverage-note');
  note.textContent = `${metadata.country_geocoded_games} games link to ${metadata.country_associations} countries and territories. The maps show ${metadata.countries_with_shape_point}; the remaining ${metadata.country_associations - metadata.countries_with_shape_point} appear in the table. The dashed box marks the area enlarged in the detail map.`;
}

async function main() {
  await document.fonts.ready;
  const chartJobs = charts.map(async (config) => {
    const views = createChartCard(config);
    await Promise.all(views.map(async ({frame, spec, aspectRatio}) => {
      try { await renderChart(frame, spec, {aspectRatio}); }
      catch (error) {
        frame.textContent = error.message;
        frame.classList.add('chart-card__frame--error');
        console.error(`Chart ${config.id} failed:`, error);
      }
    }));
  });
  const coverageJob = loadCoverage().catch((error) => {
    document.querySelector('#coverage-note').textContent = error.message;
    console.error('Metadata failed:', error);
  });
  await Promise.all([...chartJobs, coverageJob, loadCountryTable(), loadCityTable()]);
  setupNavigation();
}

async function loadCountryTable() {
  const body = document.querySelector('#country-table tbody');
  try {
    const response = await fetch('./data/countries.json');
    if (!response.ok) throw new Error(`Cannot load country table (${response.status}).`);
    const rows = await response.json();
    rows.forEach((row) => {
      const tr = document.createElement('tr');
      [row.country, row.game_count, row.longitude === null ? 'Table only' : 'Mapped', row.example_titles].forEach((value) => {
        const cell = document.createElement('td');
        cell.textContent = value;
        tr.append(cell);
      });
      body.append(tr);
    });
  } catch (error) { document.querySelector('#table-status').textContent = error.message; }
}

main();

async function loadCityTable() {
  const status = document.querySelector('#city-status');
  try {
    const response = await fetch('./data/cities.json');
    if (!response.ok) throw new Error('City details could not be loaded.');
    const rows = (await response.json()).sort((a, b) => a.city.localeCompare(b.city));
    const input = document.querySelector('#city-search');
    const body = document.querySelector('#city-table tbody');
    function update() {
      const query = input.value.trim().toLocaleLowerCase();
      const matches = rows.filter(row => `${row.city} ${row.country}`.toLocaleLowerCase().includes(query));
      body.replaceChildren(...matches.map(row => {
        const tr = document.createElement('tr');
        [row.city, row.game_count, row.country, row.example_titles].forEach(value => {
          const td = document.createElement('td'); td.textContent = value; tr.append(td);
        });
        return tr;
      }));
      status.textContent = `${matches.length} of ${rows.length} cities. A game can appear under more than one city.`;
    }
    input.addEventListener('input', update);
    update();
  } catch (error) { status.textContent = error.message; }
}
