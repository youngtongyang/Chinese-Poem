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

function tagWidth(name) {
  return Math.max(72, 38 + name.length * 15);
}

function pinMarkup(place, index) {
  var n = padIndex(index);
  var name = escapeHtml(place.name);
  var x = place.map.x, y = place.map.y;
  var tw = tagWidth(place.name);
  var th = 22;
  var side = x > 720 ? 'left' : 'right';
  var lx = side === 'right' ? 12 : -12 - tw;
  var ly = y < 70 ? 14 : -30;

  return [
    '<g class="place-pin" data-place="' + place.id + '"',
    ' transform="translate(' + x + ' ' + y + ')"',
    ' font-family="\'SimSun\',\'宋体\',\'Songti SC\',serif">',
    '<circle class="hit" r="22" fill="transparent"/>',
    '<circle class="pin-ring" r="8" fill="none" stroke="#9c3b2e" stroke-width="1.1"/>',
    '<circle class="pin-dot" r="3.6" fill="#9c3b2e"/>',
    '<g class="pin-label" transform="translate(' + lx + ' ' + ly + ')">',
    '<rect class="pin-tag" x="0" y="0" width="' + tw + '" height="' + th + '" rx="' + (th / 2) + '"/>',
    '<text class="pin-index" x="11" y="' + (th / 2 + 1) + '" font-size="11" fill="#9c3b2e" dominant-baseline="middle">' + n + '</text>',
    '<text class="pin-name" x="32" y="' + (th / 2 + 1) + '" font-size="13" fill="#2b2118" dominant-baseline="middle">' + name + '</text>',
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
  var cat = catalog();
  var zones = {};
  cat.places.forEach(function (place) {
    var z = place.zone || '其他';
    if (!zones[z]) zones[z] = [];
    zones[z].push(place);
  });
  var order = (cat.ZONE_ORDER || []).concat(['其他']);
  var html = '<h2>地点索引</h2>';
  order.forEach(function (zone) {
    var list = zones[zone];
    if (!list || !list.length) return;
    html += '<div class="index-zone" data-zone="' + escapeHtml(zone) + '">' +
      '<button class="index-zone-toggle" type="button" aria-expanded="false">' +
      '<span class="zone-name">' + escapeHtml(zone) + '</span>' +
      '<span class="zone-count">' + countLabel(list.length) + '</span>' +
      '</button><div class="index-zone-list"><div class="index-zone-inner">';
    list.forEach(function (place) {
      var i = cat.places.indexOf(place);
      html += '<a href="#place-' + place.id + '" data-place="' + place.id + '">' +
        '<em>' + padIndex(i) + '</em>' +
        '<span>' + escapeHtml(place.name) + '</span></a>';
    });
    html += '</div></div></div>';
  });
  nav.innerHTML = html;
  nav.querySelectorAll('.index-zone-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      toggleZone(btn.closest('.index-zone').getAttribute('data-zone'));
    });
  });
  nav.querySelectorAll('a[data-place]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      openPlace(a.getAttribute('data-place'), true);
    });
  });
}

function countLabel(n) {
  var cn = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
  return (cn[n] || String(n)) + '处';
}

function toggleZone(zone) {
  var current = document.querySelector('.index-zone.is-open');
  if (current && current.getAttribute('data-zone') === zone) {
    setOpenZone(null);
    return;
  }
  setOpenZone(zone);
}

function setOpenZone(zone) {
  document.querySelectorAll('.index-zone').forEach(function (el) {
    var on = zone && el.getAttribute('data-zone') === zone;
    el.classList.toggle('is-open', on);
    var btn = el.querySelector('.index-zone-toggle');
    if (btn) btn.setAttribute('aria-expanded', on ? 'true' : 'false');
  });
  var ids = {};
  if (zone) {
    catalog().places.forEach(function (place) {
      if (place.zone === zone) ids[place.id] = true;
    });
  }
  document.querySelectorAll('.place-pin').forEach(function (g) {
    var dim = zone && !ids[g.getAttribute('data-place')];
    g.classList.toggle('is-dim', dim);
  });
}

function expandZoneForPlace(id) {
  var place = catalog().placeById(id);
  if (place && place.zone) setOpenZone(place.zone);
  else setOpenZone(null);
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
    var grade = catalog().gradeLabel(poem);
    var meta = [grade, poem.dynasty, author && author.name, poem.form].filter(Boolean).join(' · ');
    return '<a href="poem.html?id=' + encodeURIComponent(poem.id) + '">' +
      '<strong>' + escapeHtml(poem.title) + '</strong>' +
      '<small>' + escapeHtml(meta) + '</small></a>';
  }).join('');

  var scroll = document.getElementById('panelScroll');
  var art = document.getElementById('panelArt');
  var src = place.map && place.map.card;
  if (src) {
    art.src = src;
    art.alt = place.name;
    scroll.hidden = false;
  } else {
    art.removeAttribute('src');
    art.alt = '';
    scroll.hidden = true;
  }
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
  expandZoneForPlace(id);
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
  setOpenZone(null);
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
  document.getElementById('panelClose').addEventListener('click', closePlace);
  document.getElementById('panelScrim').addEventListener('click', closePlace);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closePlace();
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
  bindChrome();

  var stageEl = document.getElementById('stage');
  var art = document.querySelector('.art');
  var sources = [
    'assets/map.jpeg',
    'assets/map-land-west.jpeg',
    'assets/map-land-north.jpeg',
    'assets/map-land-south.jpeg'
  ];
  var left = sources.length;
  var painted = false;
  function paint() {
    if (painted) return;
    painted = true;
    stageEl.classList.add('is-painted');
    if (art) art.classList.add('is-ready');
  }
  sources.forEach(function (src) {
    var img = new Image();
    img.onload = img.onerror = function () {
      if (--left <= 0) paint();
    };
    img.src = src;
  });
  setTimeout(paint, 2800);

  var fromHash = placeIdFromHash();
  if (fromHash) openPlace(fromHash, false);
})();
