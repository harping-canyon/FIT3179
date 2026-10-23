let hideTimer;
let activeView;

export async function stabiliseTooltips(view, frame) {
  const display = view.tooltip();
  view.tooltip(function(handler, event, item, value) {
    clearTimeout(hideTimer);
    if (value !== null && value !== undefined) {
      activeView = view;
      display.call(this, handler, event, item, value);
    } else if (activeView === view) {
      hideTimer = setTimeout(() => {
        display.call(view, handler, event, item, null);
        activeView = null;
      }, 140);
    }
  });
  // Leaving a whole chart should not leave its last value floating on the page.
  frame.addEventListener('pointerleave', () => {
    if (activeView !== view) return;
    clearTimeout(hideTimer);
    display.call(view, null, null, null, null);
    activeView = null;
  });
  await view.runAsync();
}
