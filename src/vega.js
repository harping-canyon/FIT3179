import {stabiliseTooltips} from './tooltips.js';

export async function renderChart(frame, specUrl, {aspectRatio} = {}) {
  if (typeof window.vegaEmbed !== 'function') {
    throw new Error('The chart library did not load. Check your connection and try again.');
  }
  const response = await fetch(specUrl, {cache: 'no-store'});
  if (!response.ok) throw new Error(`Cannot load chart specification (${response.status}).`);
  const spec = await response.json();
  const nativeVega = spec.$schema.includes('/vega/');
  if (nativeVega) spec.width = frame.clientWidth;
  const facetLayout = spec.usermeta?.responsiveFacet;
  const fitFacet = (width) => {
    const {columns, reservedWidth, spacing} = facetLayout;
    spec.spec.width = Math.max(160, Math.floor((width - reservedWidth - spacing * (columns - 1)) / columns));
  };
  if (facetLayout) fitFacet(frame.clientWidth);
  const heightFor = (width) => Math.max(210, Math.min(350, Math.round(width / aspectRatio)));
  if (aspectRatio) spec.height = heightFor(frame.clientWidth);
  frame.replaceChildren();
  const embedOptions = {
    actions: false, renderer: 'svg',
    tooltip: {theme: 'custom', offsetX: 18, offsetY: 18},
  };
  let result = await window.vegaEmbed(frame, spec, embedOptions);
  const {view} = result;
  await stabiliseTooltips(view, frame);
  // Facets cannot use Vega-Lite's container width. Recalculate the two plot
  // widths from their component rather than stretching the resulting SVG.
  if (facetLayout) {
    let currentWidth = Math.floor(frame.clientWidth);
    let pendingWidth = null;
    let rendering = false;
    let timer;
    const refresh = async () => {
      if (rendering) return;
      rendering = true;
      try {
        while (pendingWidth !== null) {
          const width = pendingWidth;
          pendingWidth = null;
          if (width === currentWidth) continue;
          currentWidth = width;
          fitFacet(width);
          result.finalize();
          result = await window.vegaEmbed(frame, spec, embedOptions);
          await stabiliseTooltips(result.view, frame);
        }
      } catch (error) {
        console.error(error);
        frame.classList.add('chart-card__frame--error');
        frame.textContent = 'The chart could not resize. Reload the page to try again.';
      } finally { rendering = false; }
    };
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.floor(entry.contentRect.width);
      if (!width || width === currentWidth) return;
      pendingWidth = width;
      clearTimeout(timer);
      timer = setTimeout(refresh, 120);
    });
    observer.observe(frame);
  }
  // Respond to the component's width, including stacking at the CSS breakpoint.
  // Symbol areas stay constant: only the geographic view dimensions change.
  if (aspectRatio || nativeVega) {
    let previousWidth = 0;
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.floor(entry.contentRect.width);
      if (!width || width === previousWidth) return;
      previousWidth = width;
      view.width(width);
      if (aspectRatio) view.height(heightFor(width));
      view.runAsync().catch(console.error);
    });
    observer.observe(frame);
  }
}
