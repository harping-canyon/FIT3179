// Section links land at the chapter boundary, including its label and top rule.
// Keep the URL and keyboard focus useful without letting native anchor scrolling
// compete with the animation. Wheel, touch and key input cancel the movement.
export function setupNavigation() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let frame;
  const stop = () => cancelAnimationFrame(frame);
  ['wheel', 'touchstart', 'pointerdown', 'keydown'].forEach(type => {
    window.addEventListener(type, stop, {passive: true});
  });
  const resolve = hash => {
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    return target?.closest('.story-section') || target;
  };
  const align = (target, animate) => {
    stop();
    const start = window.scrollY;
    const end = Math.max(0, Math.min(
      start + target.getBoundingClientRect().top - 20,
      document.documentElement.scrollHeight - window.innerHeight
    ));
    const focus = () => {
      const heading = target.querySelector('h2') || target;
      heading.setAttribute('tabindex', '-1');
      heading.focus({preventScroll: true});
    };
    if (!animate || reduceMotion.matches) {
      window.scrollTo({top: end, behavior: 'instant'});
      focus();
      return;
    }
    const duration = Math.min(850, 450 + Math.abs(end - start) * 0.035);
    const began = performance.now();
    const step = now => {
      const t = Math.min(1, (now - began) / duration);
      const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      window.scrollTo({top: start + (end - start) * eased, behavior: 'instant'});
      if (t < 1) frame = requestAnimationFrame(step);
      else focus();
    };
    frame = requestAnimationFrame(step);
  };
  document.querySelectorAll('.story-nav a').forEach(link => {
    link.addEventListener('click', event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const hash = link.getAttribute('href');
      const target = resolve(hash);
      if (!target) return;
      event.preventDefault();
      if (location.hash !== hash) history.pushState(null, '', hash);
      align(target, true);
    });
  });
  window.addEventListener('hashchange', () => {
    if (location.hash && resolve(location.hash)) align(resolve(location.hash), false);
  });
  // Chart rendering changes chapter heights; align deep links once it finishes.
  if (location.hash && resolve(location.hash)) align(resolve(location.hash), false);
}
