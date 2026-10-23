function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content) node.textContent = content;
  return node;
}

export function createChartCard(config) {
  const mount = document.querySelector(config.mount);
  if (!mount) throw new Error(`Missing chart mount: ${config.mount}`);

  const figure = element('figure', 'chart-card');
  if (config.layout === 'aside') figure.classList.add('chart-card--aside');
  figure.id = `chart-${config.id.toLowerCase()}`;
  const top = element('div', 'chart-card__top');
  const title = element('h3', 'chart-card__title', config.title);
  const description = element('p', 'chart-card__description', config.description);
  const views = element('div', 'chart-card__views');
  const frames = (config.views || [{title: config.title, spec: config.spec}]).map((view, index) => {
    const panel = element('section', 'chart-card__panel');
    const heading = element('h4', 'chart-card__panel-title', view.title);
    if (config.minWidth) {
      panel.classList.add('chart-card__panel--scroll');
      panel.tabIndex = 0;
      panel.setAttribute('aria-label', 'Chart; scroll horizontally on narrow screens');
    }
    const frame = element('div', 'chart-card__frame');
    if (config.minWidth) frame.style.minWidth = `${config.minWidth}px`;
    frame.id = `view-${config.id.toLowerCase()}-${index}`;
    frame.setAttribute('role', 'group');
    frame.setAttribute('aria-label', `${view.title}. ${config.insight}`);
    frame.textContent = 'Loading visualisation…';
    if (config.views) panel.append(heading);
    panel.append(frame);
    views.append(panel);
    return {frame, spec: view.spec, aspectRatio: view.aspectRatio};
  });
  if (frames.length === 1) views.classList.add('chart-card__views--single');
  const caption = element('figcaption', 'chart-card__caption');
  const finding = element('p', 'chart-card__finding', config.insight);
  const files = document.querySelector('#chart-files');
  const fileRow = element('li', '', config.fileLabel + ': ');
  frames.forEach(({spec}, index) => {
    const link = element('a', '', frames.length === 1 ? 'View' : (index === 0 ? 'World' : 'Europe detail'));
    link.href = spec;
    if (index) fileRow.append('; ');
    fileRow.append(link);
  });
  files.append(fileRow);
  top.append(title);
  if (config.description) top.append(description);
  figure.append(top, views);
  if (config.insight) {
    caption.append(finding);
    figure.append(caption);
  }
  mount.replaceChildren(figure);
  return frames;
}
