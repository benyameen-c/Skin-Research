(function () {
  var root = document.documentElement;
  root.classList.add('js');
  var views = Array.prototype.slice.call(document.querySelectorAll('section.view'));
  var links = Array.prototype.slice.call(document.querySelectorAll('nav a'));
  function show() {
    var id = (location.hash || '').replace('#', '');
    var target = document.getElementById(id);
    var view = target && target.closest ? target.closest('section.view') : null;
    if (!view) { view = views[0]; target = null; }
    views.forEach(function (v) { v.classList.toggle('active', v === view); });
    links.forEach(function (a) {
      if (a.getAttribute('href') === '#' + view.id) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (target && target !== view) target.scrollIntoView(); else window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  show();

  // copy buttons: the CSV text is embedded in the page at build time
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('button.copy') : null;
    if (!b) return;
    var src = document.getElementById(b.getAttribute('data-src'));
    if (!src) return;
    var done = function (ok) { b.textContent = ok ? 'Copied' : 'Copy failed: open the file link'; };
    try { navigator.clipboard.writeText(src.value).then(function () { done(true); }, function () { done(false); }); }
    catch (err) { done(false); }
  });

  // alignment widget (same closed-form overlap as experiments/alignment.py)
  var w = document.getElementById('align-widget');
  if (!w) return;
  var d = document.getElementById('aw-d'), s = document.getElementById('aw-s');
  var sim = JSON.parse(w.getAttribute('data-sim') || '{}');
  var PX = 30, CX = 150, CY = 100;
  function retained(dm, sh) { var x = sh / dm; if (x >= 1) return 0; return 2 * (Math.acos(x) - x * Math.sqrt(1 - x * x)) / Math.PI; }
  function draw() {
    var dm = parseFloat(d.value), sh = parseFloat(s.value), r = dm * PX / 2;
    document.getElementById('aw-spot').setAttribute('r', r);
    var o = document.getElementById('aw-outline');
    o.setAttribute('r', r); o.setAttribute('cx', CX + sh * PX);
    var b = document.getElementById('aw-base');
    b.setAttribute('r', r);
    var loss = 100 * (1 - retained(dm, sh));
    document.getElementById('aw-d-out').textContent = dm.toFixed(1) + ' mm';
    document.getElementById('aw-s-out').textContent = sh.toFixed(2) + ' mm';
    document.getElementById('aw-loss').textContent = loss.toFixed(1) + '%';
    document.getElementById('aw-ratio').textContent = (100 * sh / dm).toFixed(0) + '%';
    var key = dm.toFixed(1) + '|' + sh.toFixed(2), px = document.getElementById('aw-px');
    px.textContent = (key in sim) ? Math.abs(sim[key]).toFixed(1) + '%' : 'not run';
  }
  d.addEventListener('input', draw); s.addEventListener('input', draw); draw();
})();
