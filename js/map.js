function catalog() {
  return window.CATALOG || { places: [], poems: [], authors: [] };
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function padIndex(i) {
  return String(i + 1).padStart(2, '0');
}

/* 外侧卡片：上方水墨小图 + 下方编号标签（参考引线标注图） */
var CARD = { art: 108, gap: 5, tagH: 26, padX: 12, radius: 6 };

function tagWidth(name) {
  return Math.max(78, 34 + name.length * 15);
}

function cardSize(name) {
  var tw = tagWidth(name);
  var w = Math.max(CARD.art, tw);
  var h = CARD.art + CARD.gap + CARD.tagH;
  return { w: w, h: h, tw: tw };
}

function labelAnchor(place, size) {
  var lab = place.map.label || {};
  var side = lab.side || (place.map.x >= 600 ? 'right' : 'bottom');
  var cx = lab.x, cy = lab.y;
  var x, y;
  if (side === 'right') {
    x = cx - size.w * 0.15;
    y = cy - size.h / 2;
  } else if (side === 'left') {
    x = cx - size.w * 0.85;
    y = cy - size.h / 2;
  } else if (side === 'top') {
    x = cx - size.w / 2;
    y = cy - size.h * 0.85;
  } else {
    x = cx - size.w / 2;
    y = cy - size.h * 0.2;
  }
  return { x: x, y: y, side: side };
}

function leaderAttach(px, py, cardX, cardY, size, side) {
  var cx = cardX + size.w / 2;
  var cy = cardY + size.h / 2;
  if (side === 'right') return { x: cardX, y: cardY + CARD.art * 0.55 };
  if (side === 'left') return { x: cardX + size.w, y: cardY + CARD.art * 0.55 };
  if (side === 'top') return { x: cx, y: cardY + size.h };
  return { x: cx, y: cardY };
}

function pinMarkup(place, index) {
  var n = padIndex(index);
  var name = escapeHtml(place.name);
  var x = place.map.x, y = place.map.y;
  var size = cardSize(place.name);
  var anchor = labelAnchor(place, size);
  var end = leaderAttach(x, y, anchor.x, anchor.y, size, anchor.side);
  var tagX = (size.w - size.tw) / 2;
  var tagY = CARD.art + CARD.gap;
  var artHref = place.map.card || '';
  var maskId = 'card-mask-' + place.id;
  var artOffsetX = (size.w - CARD.art) / 2;
  var artNode = artHref
    ? '<image class="card-art" href="' + artHref + '" xlink:href="' + artHref + '"' +
      ' x="0" y="0" width="' + CARD.art + '" height="' + CARD.art + '"' +
      ' preserveAspectRatio="xMidYMid slice" mask="url(#' + maskId + ')"/>'
    : '';

  return [
    '<g class="place-pin" data-place="' + place.id + '"',
    ' font-family="\'SimSun\',\'宋体\',\'Songti SC\',serif">',
    '<defs>',
    '<mask id="' + maskId + '" maskUnits="userSpaceOnUse">',
    '<rect x="2" y="2" width="' + (CARD.art - 4) + '" height="' + (CARD.art - 4) + '" rx="40" fill="#fff"/>',
    '</mask>',
    '</defs>',
    '<g class="place-spot" transform="translate(' + x + ' ' + y + ')">',
    '<circle class="hit" r="18" fill="transparent"/>',
    '<circle class="pin-ring" r="7" fill="none" stroke="#9c3b2e" stroke-width="1" opacity=".35"/>',
    '<circle class="pin-dot" r="3.4" fill="#9c3b2e"/>',
    '</g>',
    '<line class="leader" x1="' + x + '" y1="' + y + '" x2="' + end.x.toFixed(1) + '" y2="' + end.y.toFixed(1) + '"/>',
    '<g class="place-label" transform="translate(' + anchor.x.toFixed(1) + ' ' + anchor.y.toFixed(1) + ')">',
    '<rect class="hit" x="-4" y="-4" width="' + (size.w + 8) + '" height="' + (size.h + 8) + '" fill="transparent"/>',
    '<g transform="translate(' + artOffsetX + ' 0)">',
    artNode,
    '</g>',
    '<rect class="pin-tag" x="' + tagX + '" y="' + tagY + '" width="' + size.tw + '" height="' + CARD.tagH + '" rx="' + (CARD.tagH / 2) + '"/>',
    '<text x="' + (tagX + 12) + '" y="' + (tagY + CARD.tagH / 2 + 1) + '" font-size="12" fill="#9c3b2e" dominant-baseline="middle">' + n + '</text>',
    '<text class="pin-name" x="' + (tagX + 34) + '" y="' + (tagY + CARD.tagH / 2 + 1) + '" font-size="13.5" fill="#2b2118" dominant-baseline="middle">' + name + '</text>',
    '</g>',
    '</g>'
  ].join('');
}

function renderPins() {
  var layer = document.getElementById('placeLayer');
  if (!layer) return;
  var html = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' +
    catalog().places.map(pinMarkup).join('') + '</svg>';
  var parsed = new DOMParser().parseFromString(html, 'image/svg+xml');
  if (parsed.querySelector('parsererror')) {
    layer.textContent = '';
    return;
  }
  while (layer.firstChild) layer.removeChild(layer.firstChild);
  [...parsed.documentElement.childNodes].forEach(function (n) {
    layer.appendChild(document.importNode(n, true));
  });
  layer.querySelectorAll('.place-pin').forEach(function (g) {
    g.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      openPlace(g.getAttribute('data-place'), true);
    });
  });
}

function renderIndex() {
  var nav = document.getElementById('placeIndex');
  if (!nav) return;
  nav.innerHTML = '<h2>地点索引</h2>' + catalog().places.map(function (place, i) {
    return '<a href="#place-' + place.id + '" data-place="' + place.id + '">' +
      '<em>' + padIndex(i) + '</em>' +
      '<span class="place">' + escapeHtml(place.name) +
      '<small>' + escapeHtml(place.region) + '</small></span></a>';
  }).join('');
  nav.querySelectorAll('a[data-place]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      openPlace(a.getAttribute('data-place'), true);
    });
  });
}

function renderToolbarPlaces() {
  var toolbar = document.getElementById('toolbar');
  var hideBtn = document.getElementById('btnHide');
  catalog().places.forEach(function (place) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = place.name;
    btn.setAttribute('data-place', place.id);
    btn.addEventListener('click', function () { openPlace(place.id, true); });
    toolbar.insertBefore(btn, hideBtn);
  });
}

function fillPanel(place) {
  document.getElementById('panelKicker').textContent = '风土人情';
  document.getElementById('panelTitle').textContent = place.name;
  document.getElementById('panelRegion').textContent = place.region;
  document.getElementById('panelLead').textContent = (place.culture && place.culture.lead) || '';
  var sections = (place.culture && place.culture.sections) || [];
  document.getElementById('panelSections').innerHTML = sections.map(function (s) {
    return '<div class="place-section"><h3>' + escapeHtml(s.title) + '</h3><p>' + escapeHtml(s.body) + '</p></div>';
  }).join('');

  var poems = catalog().poemsAt(place.id);
  document.getElementById('panelPoems').innerHTML = poems.map(function (poem) {
    var author = catalog().authorById(poem.authorId);
    var meta = [poem.dynasty, author && author.name, poem.form].filter(Boolean).join(' · ');
    return '<a href="poem.html?id=' + encodeURIComponent(poem.id) + '">' +
      '<strong>' + escapeHtml(poem.title) + '</strong>' +
      '<small>' + escapeHtml(meta) + '</small></a>';
  }).join('');
}

var activePlaceId = null;

function setActivePin(id) {
  document.querySelectorAll('.place-pin').forEach(function (g) {
    g.classList.toggle('is-active', g.getAttribute('data-place') === id);
  });
  document.querySelectorAll('#placeIndex a').forEach(function (a) {
    a.classList.toggle('is-active', a.getAttribute('data-place') === id);
  });
}

function openPlace(id, pushHash) {
  var place = catalog().placeById(id);
  if (!place) return;
  activePlaceId = id;
  fillPanel(place);
  var panel = document.getElementById('placePanel');
  panel.classList.add('open');
  panel.setAttribute('aria-hidden', 'false');
  document.getElementById('panelScrim').classList.add('show');
  document.body.classList.add('panel-open');
  setActivePin(id);
  if (pushHash) {
    var next = '#place-' + id;
    if (location.hash !== next) history.replaceState(null, '', next);
  }
}

function closePlace() {
  activePlaceId = null;
  var panel = document.getElementById('placePanel');
  panel.classList.remove('open');
  panel.setAttribute('aria-hidden', 'true');
  document.getElementById('panelScrim').classList.remove('show');
  document.body.classList.remove('panel-open');
  setActivePin(null);
  if (location.hash.indexOf('#place-') === 0) history.replaceState(null, '', location.pathname + location.search);
}

function placeIdFromHash() {
  var h = location.hash || '';
  var m = h.match(/^#place-([a-z0-9-]+)/i);
  if (m) return m[1];
  if (h.length > 1) {
    var raw = decodeURIComponent(h.slice(1));
    if (catalog().placeById(raw)) return raw;
  }
  return null;
}

function bindChrome() {
  var toolbar = document.getElementById('toolbar');
  var isMobile = function () { return window.matchMedia('(max-width: 900px)').matches; };

  document.getElementById('btnHide').addEventListener('click', function () {
    if (isMobile()) toolbar.classList.toggle('open');
    else toolbar.classList.add('hide');
  });
  document.getElementById('panelClose').addEventListener('click', closePlace);
  document.getElementById('panelScrim').addEventListener('click', closePlace);

  document.addEventListener('keydown', function (e) {
    var k = e.key.toLowerCase();
    if (k === 'h') toolbar.classList.toggle('hide');
    if (k === 'escape') {
      closePlace();
      toolbar.classList.remove('open');
    }
  });
  document.addEventListener('pointerdown', function (e) {
    if (!isMobile() || !toolbar.classList.contains('open')) return;
    if (!toolbar.contains(e.target)) toolbar.classList.remove('open');
  });
  window.addEventListener('resize', function () {
    toolbar.classList.toggle('hide', false);
    toolbar.classList.toggle('open', false);
  });
  window.addEventListener('hashchange', function () {
    var id = placeIdFromHash();
    if (id) openPlace(id, false);
    else closePlace();
  });
}

(function boot() {
  renderPins();
  renderIndex();
  renderToolbarPlaces();
  bindChrome();
  var art = document.querySelector('.art');
  var probe = new Image();
  probe.onload = function () { art.style.opacity = '.62'; };
  probe.src = 'assets/map.jpeg';

  var fromHash = placeIdFromHash();
  if (fromHash) openPlace(fromHash, false);
})();
