/* wheelkend multi-city shell
   讀 data/cities/index.json 與 data/cities/<id>.json，驅動轉盤、圖文卡、名單與 Leaflet 地圖
   轉盤引擎：spin-wheel v5.0.2（MIT，於 index.html 內嵌） */
(function () {
  'use strict';

  // ---------- palette（與 CSS token 對齊）----------
  var INK = '#29211a', CREAM = '#faf2df', VERM = '#c2402c', TEAL = '#20565a', OCHRE = '#d6992f', GOLD = '#e4b84c';
  var COLORED = [VERM, TEAL, OCHRE];
  function wedgeBg(i) { return (i % 2 === 0) ? COLORED[(i / 2) % 3] : CREAM; }
  function wedgeFg(i) {
    if (i % 2 === 1) return INK;
    return wedgeBg(i) === OCHRE ? INK : '#fbf4e2';
  }

  var LABEL_FONT = "'Noto Serif TC', 'Songti TC', serif";
  var FONT_PROBE = '週末目的地轉盤蘇杭無錫南京嘉興烏鎮紹寧波常通揚莫干山千島湖黃天津戴河關承德崇禮大同正定古北慕田峪白洋淀蔚縣野三坡延慶薊州轉';
  var RM = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- dom ----------
  var rim = document.getElementById('rim');
  var wheelWindow = document.getElementById('wheelWindow');
  var hubBtn = document.getElementById('hubBtn');
  var ctaBtn = document.getElementById('ctaBtn');
  var pointerEl = document.getElementById('pointer');
  var stampEl = document.getElementById('stamp');
  var resultBody = document.getElementById('resultBody');
  var destList = document.getElementById('destList');
  var citySel = document.getElementById('citySel');

  // ---------- state ----------
  var CITY = null, DESTS = [], wheel = null, spinning = false;
  var map = null, mapMarkers = [];

  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  // ---------- gold studs on the rim（一次性）----------
  var STUD_COUNT = 14;
  var studs = [];
  for (var s = 0; s < STUD_COUNT; s++) {
    var el = document.createElement('i');
    el.className = 'stud';
    rim.appendChild(el);
    studs.push(el);
  }
  function layoutStuds() {
    var w = rim.clientWidth;
    if (!w) return;
    var pad = parseFloat(getComputedStyle(rim).paddingTop) || 13;
    var r = (w / 2) - (pad / 2);
    var rPct = (r / w) * 100;
    studs.forEach(function (el, i) {
      var a = (-90 + i * (360 / STUD_COUNT)) * Math.PI / 180;
      el.style.left = (50 + Math.cos(a) * rPct) + '%';
      el.style.top = (50 + Math.sin(a) * rPct) + '%';
    });
  }
  layoutStuds();
  if (window.ResizeObserver) new ResizeObserver(layoutStuds).observe(rim);
  else window.addEventListener('resize', layoutStuds);

  // ---------- result card states ----------
  function renderIdle() {
    stampEl.classList.remove('on');
    resultBody.innerHTML =
      '<span class="chip">尚未開獎</span>' +
      '<p class="verdict">這週末，去哪裡？</p>' +
      '<p class="whisper">十四選一——點轉盤中央，或按上面的紅按鈕</p>';
  }

  function renderSpinning() {
    stampEl.classList.remove('on');
    resultBody.innerHTML =
      '<span class="chip hot">命運運轉中</span>' +
      '<p class="verdict">⋯⋯</p>' +
      '<p class="live">指針正掠過 <b id="liveName">—</b></p>';
  }

  function renderResult(i) {
    var d = DESTS[i];
    var src = 'img/' + CITY.id + '/' + d.key + '.jpg';
    resultBody.innerHTML =
      '<span class="chip hot">本週判決</span>' +
      '<p class="verdict">這週末就去 <span class="win">' + esc(d.name) + '</span>！</p>' +
      '<div class="timepill"><span class="tp-label">交通</span>' + esc(d.time) + '</div>' +
      '<div class="card-cols">' +
        '<div class="photo-wrap"><img src="' + src + '" alt="' + esc(d.cap) + '">' +
          '<span class="photo-cap">' + esc(d.cap) + '</span></div>' +
        '<p class="intro">' + esc(d.intro) + '</p>' +
      '</div>' +
      '<div class="kw-row">' + d.kw.map(function (k) {
        return '<span class="kw">' + esc(k) + '</span>';
      }).join('') + '</div>' +
      '<p class="whisper">不滿意的話，再轉一次，命運不介意</p>';
    var im = resultBody.querySelector('.photo-wrap img');
    if (im) im.onerror = function () {
      this.outerHTML = '<div class="photo-fallback">' + esc(d.cap) + '</div>';
    };
    stampEl.classList.remove('on');
    void stampEl.offsetWidth; // restart slam animation
    stampEl.classList.add('on');
  }

  function highlight(i) {
    for (var k = 0; k < DESTS.length; k++) {
      var li = document.getElementById('dest-' + k);
      if (li) li.classList.toggle('is-hit', k === i);
    }
  }

  function showFatal(err) {
    resultBody.innerHTML =
      '<span class="chip hot">載入失敗</span>' +
      '<p class="verdict">資料載入不了</p>' +
      '<p class="whisper">' + esc(err && err.message || err) + '——請重新整理再試</p>';
  }

  // ---------- confetti ----------
  function confetti() {
    if (RM || !document.body.animate) return;
    var box = pointerEl.getBoundingClientRect();
    var ox = box.left + box.width / 2;
    var oy = box.top + box.height / 2;
    var colors = [VERM, TEAL, OCHRE, GOLD, INK];
    for (var i = 0; i < 46; i++) {
      var p = document.createElement('i');
      var c = colors[i % colors.length];
      var sz = 5 + Math.random() * 6;
      p.style.cssText = 'position:fixed;left:' + ox + 'px;top:' + oy + 'px;width:' + sz * 0.7 +
        'px;height:' + sz + 'px;background:' + c + ';z-index:99;pointer-events:none;border-radius:1.5px;';
      document.body.appendChild(p);
      var dx = (Math.random() - 0.5) * 340;
      var rot = (Math.random() - 0.5) * 1080;
      var anim = p.animate([
        { transform: 'translate(0,0) rotate(0deg)', opacity: 1 },
        { transform: 'translate(' + dx * 0.55 + 'px,' + (-70 - Math.random() * 110) + 'px) rotate(' + rot * 0.4 + 'deg)', opacity: 1, offset: 0.32 },
        { transform: 'translate(' + dx + 'px,' + (190 + Math.random() * 200) + 'px) rotate(' + rot + 'deg)', opacity: 0 }
      ], { duration: 950 + Math.random() * 650, easing: 'cubic-bezier(.16,.6,.4,1)' });
      anim.onfinish = (function (node) { return function () { node.remove(); }; })(p);
    }
  }

  // ---------- wheel ----------
  function easeOutQuart(n) { return 1 - Math.pow(1 - n, 4); }

  function tickPointer() {
    pointerEl.classList.remove('tick');
    void pointerEl.offsetWidth;
    pointerEl.classList.add('tick');
  }

  function onRest(e) {
    spinning = false;
    hubBtn.disabled = false;
    ctaBtn.disabled = false;
    ctaBtn.textContent = '再轉一次';
    renderResult(e.currentIndex);
    highlight(e.currentIndex);
    confetti();
    focusDest(e.currentIndex);
  }

  function initWheel() {
    if (wheel) { wheel.remove(); wheel = null; }
    wheel = new spinWheel.Wheel(wheelWindow, {
      items: DESTS.map(function (d, i) {
        return { label: d.name, backgroundColor: wedgeBg(i), labelColor: wedgeFg(i) };
      }),
      isInteractive: false,
      radius: 1,
      borderColor: INK,
      borderWidth: 4,
      lineColor: INK,
      lineWidth: 2.5,
      itemLabelFont: LABEL_FONT,
      itemLabelAlign: 'right',
      itemLabelRadius: 0.93,
      itemLabelRadiusMax: 0.44,
      itemLabelFontSizeMax: 30,
      itemLabelBaselineOffset: -0.07,
      pointerAngle: 0,
      onRest: onRest,
      onCurrentIndexChange: function (e) {
        tickPointer();
        var live = document.getElementById('liveName');
        if (live && spinning) live.textContent = DESTS[e.currentIndex].name;
      }
    });
    window.__wk = { wheel: wheel }; // test hook: lets automation drive the animation clock
  }

  function spin() {
    if (spinning || !wheel) return;
    spinning = true;
    hubBtn.disabled = true;
    ctaBtn.disabled = true;
    ctaBtn.textContent = '命運運轉中⋯';
    renderSpinning();
    var target = Math.floor(Math.random() * DESTS.length);
    var duration = RM ? 900 : 4300 + Math.random() * 900;
    var revs = RM ? 1 : 4 + Math.floor(Math.random() * 3);
    wheel.spinToItem(target, duration, false, revs, 1, easeOutQuart);
  }

  rim.addEventListener('click', spin);
  ctaBtn.addEventListener('click', spin);

  // ---------- map（Leaflet，vendor 內建）----------
  function initMap() {
    var mapSec = document.getElementById('mapSec');
    if (!window.L) { if (mapSec) mapSec.style.display = 'none'; return; }
    if (map) { map.remove(); map = null; mapMarkers = []; }
    map = L.map('bigmap', { scrollWheelZoom: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 12,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    var bounds = [[CITY.center.lat, CITY.center.lon]];
    L.circleMarker([CITY.center.lat, CITY.center.lon],
      { radius: 8, color: '#fbf4e2', weight: 2, fillColor: INK, fillOpacity: 1 })
      .addTo(map)
      .bindTooltip(CITY.name, { permanent: true, direction: 'right', offset: [10, 0], className: 'map-tip' });
    DESTS.forEach(function (d, i) {
      var m = L.circleMarker([d.lat, d.lon],
        { radius: 7, color: INK, weight: 1.5, fillColor: wedgeBg(i), fillOpacity: 0.95 })
        .addTo(map)
        .bindPopup('<b>' + esc(d.name) + '</b><br>' + esc(d.time));
      mapMarkers.push(m);
      bounds.push([d.lat, d.lon]);
    });
    map.fitBounds(bounds, { padding: [30, 30] });
  }

  function focusDest(i) {
    if (!map || !mapMarkers[i]) return;
    var d = DESTS[i];
    map.flyTo([d.lat, d.lon], 9, { duration: RM ? 0 : 1.4 });
    mapMarkers[i].openPopup();
  }

  // ---------- city loading ----------
  function fetchJson(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error(url + ' → HTTP ' + r.status);
      return r.json();
    });
  }

  function currentCityId() {
    var m = location.search.match(/[?&]city=([a-z-]+)/);
    return m ? m[1] : null;
  }

  function buildCityOptions(manifest, current) {
    citySel.innerHTML = manifest.cities.map(function (c) {
      return '<option value="' + esc(c.id) + '"' + (c.id === current ? ' selected' : '') + '>' +
        esc(c.name) + '</option>';
    }).join('');
    citySel.addEventListener('change', function () {
      location.search = '?city=' + this.value;
    });
  }

  function initCity(cfg) {
    CITY = cfg;
    DESTS = cfg.dests;
    document.title = '週末目的地轉盤・' + cfg.name;
    document.getElementById('eyebrow').textContent = cfg.eyebrow;
    document.getElementById('lede').innerHTML = cfg.lede; // 本地資料，非用戶輸入
    var sl = document.getElementById('sideL'), sr = document.getElementById('sideR');
    if (sl) sl.textContent = cfg.sideTags[0];
    if (sr) sr.textContent = cfg.sideTags[1];
    destList.innerHTML = DESTS.map(function (d, i) {
      return '<li id="dest-' + i + '"><i class="dot" style="background:' + wedgeBg(i) + '"></i>' +
        '<span class="d-name">' + esc(d.name) + '</span>' +
        '<span class="leader"></span>' +
        '<span class="d-time">' + esc(d.time) + '</span></li>';
    }).join('');
    var cw = document.getElementById('creditsWrap');
    var cb = document.getElementById('creditsBody');
    if (cfg.credits && cfg.credits.length) {
      cb.innerHTML = cfg.credits.map(esc).join('<br>');
      cw.style.display = '';
    } else {
      cw.style.display = 'none';
    }
    renderIdle();
    initWheel();
    initMap();
  }

  // ---------- boot ----------
  function whenFonts() {
    if (!document.fonts || !document.fonts.load) return Promise.resolve();
    return Promise.race([
      Promise.all([
        document.fonts.load('900 30px "Noto Serif TC"', FONT_PROBE),
        document.fonts.load('700 16px "Noto Sans TC"', FONT_PROBE)
      ]),
      new Promise(function (r) { setTimeout(r, 2400); })
    ]);
  }

  Promise.all([fetchJson('data/cities/index.json'), whenFonts().catch(function () {})])
    .then(function (res) {
      var manifest = res[0];
      var id = currentCityId() || manifest.default;
      var known = manifest.cities.some(function (c) { return c.id === id; });
      if (!known) id = manifest.default;
      buildCityOptions(manifest, id);
      return fetchJson('data/cities/' + id + '.json').then(initCity);
    })
    .catch(showFatal);

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      if (wheel) wheel.itemLabelFont = LABEL_FONT; // setter triggers a redraw once fonts land
    });
  }
})();
