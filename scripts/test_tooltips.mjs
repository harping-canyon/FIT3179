import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const source = await readFile(new URL('../src/tooltips.js', import.meta.url), 'utf8');
const {stabiliseTooltips} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function fixture() {
  const calls = []; let callback = (...args) => calls.push(args[3]);
  const listeners = {};
  const view = {tooltip(fn) {if (!fn) return callback; callback=fn; return this;}, runAsync: async()=>{}};
  return {view, frame:{addEventListener:(name,fn)=>listeners[name]=fn}, calls, send:value=>callback(null,{},null,value), leave:()=>listeners.pointerleave()};
}
const a=fixture(), b=fixture();
await stabiliseTooltips(a.view,a.frame); await stabiliseTooltips(b.view,b.frame);
a.send('Italy'); a.send(null); await sleep(30); a.send('Germany'); await sleep(170);
assert.deepEqual(a.calls,['Italy','Germany'], 'Crossing a short gap must not hide the tooltip');
a.send(null); await sleep(170); assert.equal(a.calls.at(-1),null,'Empty plot must eventually hide');
a.send('Italy'); a.leave(); assert.equal(a.calls.at(-1),null,'Leaving chart must hide immediately');
a.send('Italy'); a.send(null); b.send('New chart'); await sleep(170);
assert.equal(a.calls.at(-1),'Italy','Old timer must not hide a newer chart tooltip');
assert.equal(b.calls.at(-1),'New chart'); b.leave();
console.log('PASS: gap grace, empty-plot dismissal, chart exit, cross-chart timer cancellation');
