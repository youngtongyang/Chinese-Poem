const stage = document.getElementById('stage');
const notesPanel = document.getElementById('notesPanel');

function catalog() {
  return window.CATALOG || { places: [], poems: [], authors: [] };
}

function poemIdFromQuery() {
  const id = new URLSearchParams(location.search).get('id');
  return id && id.trim() ? id.trim() : 'wang-lushan-pubu';
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderMissing(id) {
  document.title = '未找到该诗';
  stage.innerHTML =
    '<div class="content" style="padding:8%;flex-direction:column;gap:1em">' +
    '<div class="title-main">未找到这首诗</div>' +
    '<p class="author-desc">目录里没有「' + escapeHtml(id) + '」。请从地图重新进入。</p>' +
    '<a class="map-back" href="map.html" style="writing-mode:horizontal-tb;letter-spacing:.2em">返回地图</a>' +
    '</div>';
  const toolbar = document.getElementById('toolbar');
  if (toolbar) toolbar.style.display = 'none';
}

function fitStage(poem) {
  const titleLen = poem.title.length;
  const lineCount = poem.lines.length;
  const lineChars = poem.lines.reduce(function (m, l) { return Math.max(m, l.length); }, 0);
  stage.classList.remove('title-tight', 'title-xlong', 'title-xxlong', 'is-wuyan', 'is-qiyan');
  if (titleLen >= 6) stage.classList.add('title-tight');
  if (titleLen >= 8) stage.classList.add('title-xlong');
  if (titleLen >= 9) stage.classList.add('title-xxlong');
  if (lineChars <= 5) stage.classList.add('is-wuyan');
  else stage.classList.add('is-qiyan');
  stage.setAttribute('data-title-len', String(titleLen));
  stage.setAttribute('data-lines', String(lineCount));
  stage.setAttribute('data-line-chars', String(lineChars));
}

function renderPoem(poem, author, place) {
  const isLushi = poem.lines.length >= 8;
  document.title = poem.title + ' · ' + poem.dynasty + '·' + author.name;
  fitStage(poem);

  const art = document.getElementById('art');
  if (poem.art && poem.art.src) {
    stage.classList.remove('no-art');
    art.style.backgroundImage = 'url("' + poem.art.src + '")';
    var mobile = window.matchMedia('(max-width: 900px)').matches;
    if (mobile) {
      art.style.backgroundSize = poem.art.sizeMobile || 'cover';
      art.style.backgroundPosition = poem.art.positionMobile || poem.art.position || 'center 42%';
    } else {
      if (poem.art.size) art.style.backgroundSize = poem.art.size;
      if (poem.art.position) art.style.backgroundPosition = poem.art.position;
    }
  } else {
    stage.classList.add('no-art');
    art.style.backgroundImage = 'none';
  }

  const titleMain = document.getElementById('titleMain');
  titleMain.textContent = poem.title;
  titleMain.classList.toggle('is-long', poem.title.length > 5);
  document.getElementById('titleSub').textContent = poem.dynasty + ' · ' + poem.form;
  var gradeEl = document.getElementById('titleGrade');
  var grade = catalog().gradeLabel(poem);
  if (gradeEl) {
    gradeEl.textContent = grade;
    gradeEl.hidden = !grade;
  }
  document.getElementById('authorLine').textContent = author.name;

  const seal = document.getElementById('seal');
  const chars = (author.seal && author.seal.length === 4) ? author.seal : ['诗', '笺', '之', '作'];
  seal.innerHTML = chars.map(function (c) { return '<span>' + escapeHtml(c) + '</span>'; }).join('');

  const poemEl = document.getElementById('poem');
  poemEl.classList.toggle('is-jueju', !isLushi);
  poemEl.classList.toggle('is-lushi', isLushi);
  poemEl.innerHTML = poem.lines.map(function (line) {
    return '<div class="col"><div class="line">' + escapeHtml(line) + '</div></div>';
  }).join('');

  const gloss = document.getElementById('gloss');
  const bits = poem.gloss || [];
  gloss.innerHTML = bits.map(function (g, i) {
    const sep = i < bits.length - 1 ? '<span class="gloss-sep">｜</span>' : '';
    return '<span>' + escapeHtml(g) + '</span>' + sep;
  }).join('');

  const card = document.getElementById('authorCard');
  const portrait = document.getElementById('authorPortrait');
  if (author.portrait) {
    card.classList.remove('no-portrait');
    portrait.hidden = false;
    portrait.src = author.portrait;
    portrait.alt = author.name + '画像';
  } else {
    card.classList.add('no-portrait');
    portrait.hidden = true;
    portrait.removeAttribute('src');
  }
  document.getElementById('authorName').textContent = author.name;
  document.getElementById('authorDates').textContent = author.dates || '';
  document.getElementById('authorDesc').innerHTML = author.desc || '';
  document.getElementById('authorWorks').innerHTML =
    '<span class="works-label">代表作</span>' + escapeHtml(author.works || '');

  document.getElementById('notesTitle').textContent = poem.title + ' · 讲解';
  document.getElementById('notesGrid').innerHTML = (poem.notes || []).map(function (n) {
    return '<div class="note-item"><h4>' + escapeHtml(n.title) + '</h4><p>' + n.body + '</p></div>';
  }).join('');

  const backHash = place ? '#' + place.id : '';
  document.getElementById('mapBack').href = 'map.html' + backHash;
  const toolbarMap = document.getElementById('toolbarMap');
  if (toolbarMap) toolbarMap.href = 'map.html' + backHash;
}

/* ══════════════════════════════════════════════════════════
   诗句「春风拂柳」物理引擎
   关键设计：柳枝模型 —— 常驻微风 + 每列独立相位。
   ══════════════════════════════════════════════════════════ */

class PoemPhysics {
  constructor(el, index = 0, total = 4) {
    this.el = el;
    this.x = 0; this.y = 0; this.rot = 0;
    this.vx = 0; this.vy = 0; this.vrot = 0;
    this.dragging = false;
    this.ptrId = null;
    this.lastX = 0; this.lastY = 0; this.lastT = 0;
    this.t = 0;

    this.STIFF = 0.045;
    this.DAMP  = 0.955;
    this.ROT_K = 0.020;
    this.ROT_D = 0.965;
    this.MAX_ROT = 9;
    this.MAX_OFF = 150;

    this.BEND_GAIN = 38;
    this.BEND_MAX  = 14;
    this.bend = 0;

    this.BREEZE_AMP_X   = 5.2;
    this.BREEZE_AMP_Y   = 2.6;
    this.BREEZE_AMP_ROT = 1.6;
    this.BREEZE_T = 7.5;
    this.phase = (index / total) * Math.PI * 1.5;
    this.phase2 = index * 1.7;

    this.pointer = { x: -9999, y: -9999, active: false };

    el.addEventListener('pointerdown', e => this.down(e));
  }

  breeze() {
    const w = (Math.PI * 2) / this.BREEZE_T;
    return {
      x: Math.sin(this.t * w + this.phase) * this.BREEZE_AMP_X
       + Math.sin(this.t * w * 0.43 + this.phase2) * this.BREEZE_AMP_X * 0.35,
      y: Math.sin(this.t * w * 1.31 + this.phase + 1.1) * this.BREEZE_AMP_Y,
      rot: Math.sin(this.t * w * 0.83 + this.phase) * this.BREEZE_AMP_ROT
    };
  }

  down(e) {
    e.preventDefault();
    this.dragging = true;
    this.ptrId = e.pointerId;
    this.el.setPointerCapture(e.pointerId);
    this.el.classList.add('dragging');
    this.lastX = e.clientX; this.lastY = e.clientY; this.lastT = performance.now();
    this.vx = 0; this.vy = 0; this.vrot = 0;
    this._move = ev => this.move(ev);
    this._up   = ev => this.up(ev);
    window.addEventListener('pointermove', this._move);
    window.addEventListener('pointerup', this._up);
    window.addEventListener('pointercancel', this._up);
  }

  move(e) {
    if (!this.dragging || e.pointerId !== this.ptrId) return;
    const dx = e.clientX - this.lastX;
    const dy = e.clientY - this.lastY;
    const dt = Math.max(1, performance.now() - this.lastT);

    this.x += dx; this.y += dy;

    this.vx = this.vx * 0.6 + (dx / dt * 16) * 0.4;
    this.vy = this.vy * 0.6 + (dy / dt * 16) * 0.4;

    const targetBend = Math.max(-this.BEND_MAX,
                        Math.min(this.BEND_MAX, this.vx / 16 * this.BEND_GAIN * 0.5));
    this.bend += (targetBend - this.bend) * 0.14;

    this.rot += (this.bend * 0.5 - this.rot) * 0.10;

    this.x = Math.max(-this.MAX_OFF, Math.min(this.MAX_OFF, this.x));
    this.y = Math.max(-this.MAX_OFF, Math.min(this.MAX_OFF, this.y));

    this.lastX = e.clientX; this.lastY = e.clientY; this.lastT = performance.now();
  }

  up(e) {
    if (e.pointerId !== this.ptrId) return;
    this.dragging = false;
    this.el.classList.remove('dragging');
    window.removeEventListener('pointermove', this._move);
    window.removeEventListener('pointerup', this._up);
    window.removeEventListener('pointercancel', this._up);
  }

  step(dtScale = 1) {
    this.t += (1 / 60) * dtScale;

    if (!this.dragging) {
      const b = this.breeze();
      const anchorX = b.x, anchorY = b.y, anchorRot = b.rot;

      this.vx += (anchorX - this.x) * this.STIFF;
      this.vy += (anchorY - this.y) * this.STIFF;
      this.vrot += (anchorRot + this.bend - this.rot) * this.ROT_K;

      this.vx *= this.DAMP; this.vy *= this.DAMP; this.vrot *= this.ROT_D;

      this.x += this.vx; this.y += this.vy; this.rot += this.vrot;

      this.bend *= 0.97;
      if (Math.abs(this.bend) < 0.01) this.bend = 0;
    } else {
      this.x += Math.sin(this.t * 2.2 + this.phase) * 0.06 * dtScale;
      this.y += Math.cos(this.t * 1.9 + this.phase) * 0.04 * dtScale;
    }

    this.el.style.transform =
      `translate3d(${this.x.toFixed(2)}px, ${this.y.toFixed(2)}px, 0) rotate(${this.rot.toFixed(3)}deg)`;
  }
}

let colPhys = [];
let currentPoem = null;

function bindPhysics() {
  const colEls = [...document.querySelectorAll('.poem .col')];
  colPhys = colEls.map((el, i) => new PoemPhysics(el, i, colEls.length));
}

let _lastT = performance.now();
(function loop(now) {
  const dt = Math.min(50, now - _lastT) / 16.67;
  _lastT = now;
  for (const p of colPhys) p.step(dt);
  requestAnimationFrame(loop);
})(_lastT);

function bindPointerWind() {
  const poemEl = document.querySelector('.poem');
  if (!poemEl || !window.matchMedia('(hover: hover)').matches) return;
  poemEl.addEventListener('pointermove', e => {
    for (const p of colPhys) {
      if (p.dragging) continue;
      const r = p.el.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const dist = Math.hypot(e.clientX - cx, e.clientY - cy);
      if (dist < 260) {
        const f = (1 - dist / 260) ** 2 * 0.30;
        p.vx += (e.clientX < cx ? 1 : -1) * f * 0.9;
        p.vy += (e.clientY < cy ? 1 : -1) * f * 0.45;
        p.vrot += (e.clientX < cx ? 1 : -1) * f * 0.22;
      }
    }
  });
}

function openNotes()  { notesPanel.classList.add('show'); }
function closeNotes() { notesPanel.classList.remove('show'); }

function replayInk() {
  const lines = document.querySelectorAll('.line');
  lines.forEach(el => el.classList.remove('ink-in'));
  void document.body.offsetWidth;
  lines.forEach(el => el.classList.add('ink-in'));
  for (const p of colPhys) { p.x = p.y = p.rot = 0; p.vx = p.vy = p.vrot = 0; }
}

function startInk() {
  document.querySelectorAll('.line').forEach(el => el.classList.add('ink-in'));
}

function revealSequence(poem) {
  const art = document.getElementById('art');
  const src = poem.art && poem.art.src;
  let started = false;
  function go() {
    if (started) return;
    started = true;
    requestAnimationFrame(function () {
      if (src && art) art.classList.add('is-ready');
      window.setTimeout(startInk, src ? 380 : 60);
    });
  }
  if (!src) {
    go();
    return;
  }
  const im = new Image();
  im.onload = go;
  im.onerror = go;
  im.src = src;
  if (im.complete) go();
}

function bindChrome() {
  document.getElementById('notesToggle').onclick = openNotes;
  document.getElementById('notesClose').onclick  = closeNotes;
  document.getElementById('btnNotes').onclick    = () => notesPanel.classList.contains('show') ? closeNotes() : openNotes();
  document.getElementById('btnReplay').onclick = replayInk;

  const toolbar = document.getElementById('toolbar');
  const isMobile = () => window.matchMedia('(max-width: 900px)').matches;

  document.getElementById('btnHide').onclick = () => {
    if (isMobile()) {
      toolbar.classList.toggle('open');
      return;
    }
    toolbar.classList.add('hide');
  };

  document.addEventListener('keydown', e => {
    const k = e.key.toLowerCase();
    if (k === 'h') toolbar.classList.toggle('hide');
    if (k === 'escape') { closeNotes(); toolbar.classList.remove('open'); }
    if (k === 'r') replayInk();
  });

  document.addEventListener('pointerdown', e => {
    if (!isMobile() || !toolbar.classList.contains('open')) return;
    if (!toolbar.contains(e.target)) toolbar.classList.remove('open');
  });

  window.addEventListener('resize', () => {
    toolbar.classList.toggle('hide', false);
    toolbar.classList.toggle('open', false);
  });

  document.getElementById('btnShot').onclick = async () => {
    const btn = document.getElementById('btnShot');
    const old = btn.textContent;
    btn.textContent = '⏳ 导出中…';
    const artSrc = (currentPoem && currentPoem.art && currentPoem.art.src) ? currentPoem.art.src : '';
    const fileName = (currentPoem ? currentPoem.title : '古诗') + '.png';
    try {
      const w = stage.offsetWidth, h = stage.offsetHeight, dpr = 2;
      const canvas = document.createElement('canvas');
      canvas.width = w * dpr; canvas.height = h * dpr;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ece2cd'; ctx.fillRect(0, 0, canvas.width, canvas.height);
      if (artSrc) {
        await new Promise((res, rej) => {
          const im = new Image();
          im.crossOrigin = 'anonymous';
          im.onload = () => { ctx.drawImage(im, 0, 0, canvas.width, canvas.height); res(); };
          im.onerror = rej;
          im.src = artSrc;
        });
        ctx.save();
        ctx.globalAlpha = .30; ctx.fillStyle = '#ece2cd';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.restore();
      }
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
        <foreignObject width="100%" height="100%">
          ${new XMLSerializer().serializeToString(stage.cloneNode(true))}
        </foreignObject></svg>`;
      const blob = new Blob([svg], {type: 'image/svg+xml'});
      const url = URL.createObjectURL(blob);
      const img2 = new Image();
      await new Promise((res, rej) => { img2.onload = res; img2.onerror = rej; img2.src = url; });
      ctx.drawImage(img2, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      const a = document.createElement('a');
      a.download = fileName;
      a.href = canvas.toDataURL('image/png');
      a.click();
      btn.textContent = '✓ 已导出';
    } catch (err) {
      console.warn(err);
      btn.textContent = '⚠ 请直接截图';
    }
    setTimeout(() => btn.textContent = old, 2200);
  };
}

(function boot() {
  const id = poemIdFromQuery();
  const poem = catalog().poemById ? catalog().poemById(id) : null;
  if (!poem) {
    renderMissing(id);
    return;
  }
  const author = catalog().authorById(poem.authorId) || { name: '佚名', seal: ['诗', '笺', '之', '作'] };
  const place = catalog().placeById(poem.placeId);
  currentPoem = poem;
  renderPoem(poem, author, place);
  bindPhysics();
  bindPointerWind();
  bindChrome();
  revealSequence(poem);
  console.log('%c《' + poem.title + '》古诗页面已就绪', 'color:#9c3b2e;font-size:15px;font-weight:bold');
  console.log('按 H 隐藏工具列 ｜ 按 Esc 关闭讲解');
})();
