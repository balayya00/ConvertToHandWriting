/* ============================================================
   PDF to Handwriting Converter – main.js v6.0
   ============================================================ */
'use strict';

const S = {
  file: null, pages: [], layoutData: null,
  font: 'Kalam', paper: 'ruled', color: 'blue', format: 'pdf',
  sessionId: null, jpgUrls: [], currentPage: 0, converting: false,
  allFonts: [], activeCat: 'all',
};

/* CSS font-family names for live preview in cards */
const FONT_CSS = {
  Kalam:                  'Kalam',
  Caveat:                 'Caveat',
  Indie_Flower:           'Indie Flower',
  Gloria_Hallelujah:      'Gloria Hallelujah',
  Shadows_Into_Light:     'Shadows Into Light',
  Nothing_You_Could_Do:   'Nothing You Could Do',
  Covered_By_Your_Grace:  'Covered By Your Grace',
  Gochi_Hand:             'Gochi Hand',
  Handlee:                'Handlee',
  Patrick_Hand:           'Patrick Hand',
  Architects_Daughter:    'Architects Daughter',
  Amatic_SC:              'Amatic SC',
  Reenie_Beanie:          'Reenie Beanie',
  Dancing_Script:         'Dancing Script',
  Satisfy:                'Satisfy',
  Yellowtail:             'Yellowtail',
  Damion:                 'Damion',
  Norican:                'Norican',
  Marck_Script:           'Marck Script',
  Homemade_Apple:         'Homemade Apple',
  Great_Vibes:            'Great Vibes',
  Allura:                 'Allura',
  Sacramento:             'Sacramento',
  Parisienne:             'Parisienne',
  Pinyon_Script:          'Pinyon Script',
  Tangerine:              'Tangerine',
  Alex_Brush:             'Alex Brush',
  Engagement:             'Engagement',
  Euphoria_Script:        'Euphoria Script',
  Permanent_Marker:       'Permanent Marker',
  Rock_Salt:              'Rock Salt',
  Pacifico:               'Pacifico',
};

/* Sample preview text per category */
const PREVIEW = {
  Natural:     'My handwriting',
  Print:       'Neat and clear',
  Cursive:     'Hello World',
  Calligraphy: 'Beautiful script',
  Bold:        'Bold strokes',
};

document.addEventListener('DOMContentLoaded', () => {
  injectGoogleFonts();
  loadFonts();
  initCharCounter();
});

/* ── Inject Google Fonts link for live previews ─────────────── */
function injectGoogleFonts() {
  const families = [
    'Kalam', 'Caveat', 'Indie+Flower', 'Gloria+Hallelujah',
    'Shadows+Into+Light', 'Nothing+You+Could+Do', 'Covered+By+Your+Grace',
    'Gochi+Hand', 'Handlee', 'Patrick+Hand', 'Architects+Daughter',
    'Amatic+SC', 'Reenie+Beanie', 'Dancing+Script', 'Satisfy',
    'Yellowtail', 'Damion', 'Norican', 'Marck+Script', 'Homemade+Apple',
    'Great+Vibes', 'Allura', 'Sacramento', 'Parisienne', 'Pinyon+Script',
    'Tangerine', 'Alex+Brush', 'Engagement', 'Euphoria+Script',
    'Permanent+Marker', 'Rock+Salt', 'Pacifico', 'Inter:wght@400;500;600;700',
  ].join('&family=');

  const link = document.createElement('link');
  link.rel  = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?family=${families}&display=swap`;
  document.head.appendChild(link);
}

/* ── Font loading ─────────────────────────────────────────────── */
async function loadFonts() {
  const grid = g('font-grid');
  grid.innerHTML = '<div class="loading-fonts"><i class="fas fa-spinner fa-spin"></i> Loading fonts…</div>';
  try {
    const res = await fetch('/api/fonts');
    const txt = await res.text();
    let data;
    try { data = JSON.parse(txt); }
    catch(e) { throw new Error('Bad JSON from /api/fonts: ' + txt.slice(0, 100)); }
    if (!data.fonts || !data.fonts.length) throw new Error('No fonts returned');
    S.allFonts = data.fonts;
    renderFontGrid(S.allFonts, '');
  } catch(e) {
    console.warn('Font API error:', e);
    /* Build fallback from FONT_CSS keys */
    S.allFonts = Object.keys(FONT_CSS).map(key => ({
      key, display: key.replace(/_/g, ' '),
      emoji: '✍️', style: 'Handwriting', category: 'Natural',
      available: false,
    }));
    renderFontGrid(S.allFonts, '');
  }
}

function renderFontGrid(fonts, searchQ) {
  const grid = g('font-grid');
  const q    = (searchQ || '').toLowerCase().trim();
  const cat  = S.activeCat;

  const filtered = fonts.filter(f => {
    const matchCat  = cat === 'all' || f.category === cat;
    const matchQ    = !q ||
      f.display.toLowerCase().includes(q) ||
      (f.style || '').toLowerCase().includes(q);
    return matchCat && matchQ;
  });

  if (!filtered.length) {
    grid.innerHTML = '<div class="loading-fonts">No fonts match.</div>';
    return;
  }

  grid.innerHTML = filtered.map(f => {
    const css   = FONT_CSS[f.key] || f.display;
    const prev  = PREVIEW[f.category] || 'Handwriting';
    const sel   = f.key === S.font ? ' selected' : '';
    return `
      <div class="font-card${sel}" data-key="${xss(f.key)}"
           onclick="pickFont(this,'${xss(f.key)}','${xss(f.display)}')">
        <div class="fc-top">
          <span class="fc-emoji">${xss(f.emoji || '✍️')}</span>
          <span class="fc-name">${xss(f.display)}</span>
        </div>
        <div class="fc-preview" style="font-family:'${css}',cursive">${xss(prev)}</div>
        <div class="fc-meta">
          <span class="fc-style">${xss(f.style || '')}</span>
          ${f.available
            ? '<span class="fc-badge ok">✓ Ready</span>'
            : '<span class="fc-badge dl">↓ Queued</span>'}
        </div>
      </div>`;
  }).join('');
}

function pickFont(card, key, display) {
  document.querySelectorAll('.font-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  S.font = key;
  const lbl = g('selected-font-name');
  if (lbl) lbl.textContent = display;
  toast(`Font: ${display}`, 'info');
}

function filterFonts(q) {
  renderFontGrid(S.allFonts, q);
}

function filterCat(btn, cat) {
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  S.activeCat = cat;
  renderFontGrid(S.allFonts, g('font-search') ? g('font-search').value : '');
}

/* ── Tabs ─────────────────────────────────────────────────────── */
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tabId));
  document.querySelectorAll('.tab-content').forEach(c =>
    c.classList.toggle('active', c.id === tabId));
}

/* ── Upload ───────────────────────────────────────────────────── */
function onDragOver(e)  { e.preventDefault(); g('upload-zone').classList.add('drag-over'); }
function onDragLeave()  { g('upload-zone').classList.remove('drag-over'); }
function onDrop(e)      { e.preventDefault(); onDragLeave(); processFile(e.dataTransfer.files[0]); }
function onFileChange(i){ if (i.files[0]) processFile(i.files[0]); }

function processFile(file) {
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf','jpg','jpeg','png'].includes(ext))
    return toast('Only PDF, JPG, PNG files supported', 'error');
  if (file.size > 50 * 1024 * 1024)
    return toast('File too large (max 50 MB)', 'error');
  S.file = file;
  g('upload-zone').style.display  = 'none';
  g('file-preview').style.display = 'block';
  g('extract-btn').style.display  = 'block';
  const ico = g('file-type-icon');
  ico.className   = ext === 'pdf' ? 'fas fa-file-pdf' : 'fas fa-file-image';
  ico.style.color = ext === 'pdf' ? '#ef4444' : '#3b82f6';
  g('file-name').textContent = file.name;
  g('file-size').textContent = fmtSize(file.size);
  if (ext === 'pdf') g('layout-opt').style.display = 'block';
  toast(`File selected: ${file.name}`, 'success');
}

function removeFile() {
  S.file = null;
  g('upload-zone').style.display  = 'block';
  g('file-preview').style.display = 'none';
  g('extract-btn').style.display  = 'none';
  g('file-input').value           = '';
  g('layout-opt').style.display   = 'none';
}

/* ── Extract ──────────────────────────────────────────────────── */
async function extractText() {
  if (!S.file) return toast('Select a file first', 'warning');
  showOverlay('Extracting text…');
  try {
    const fd = new FormData();
    fd.append('file', S.file);
    fd.append('input_type', 'file');
    const res = await fetch('/api/extract', { method: 'POST', body: fd });
    const raw = await res.text();
    let data;
    try { data = JSON.parse(raw); }
    catch (e) {
      console.error('Extract raw:', raw.slice(0, 300));
      throw new Error('Server returned invalid response during extraction');
    }
    if (!res.ok || data.error) throw new Error(data.error || 'Extraction failed');
    S.pages      = data.pages  || [data.text || ''];
    S.layoutData = data.layout_data || null;
    g('extracted-text').value         = data.text || '';
    g('extracted-card').style.display = 'block';
    g('step-2').style.display         = 'block';
    g('page-count-badge').textContent =
      `${data.page_count || 1} page${data.page_count !== 1 ? 's' : ''}`;
    setStep(2);
    g('step-2').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    toast(`Extracted ${data.page_count || 1} page(s) successfully`, 'success');
  } catch (e) {
    console.error(e);
    toast(`Extraction failed: ${e.message}`, 'error');
  } finally { hideOverlay(); }
}

function useDirectText() {
  const txt = (g('direct-text').value || '').trim();
  if (!txt) return toast('Enter some text first', 'warning');
  S.pages = [txt]; S.layoutData = null;
  g('extracted-text').value         = txt;
  g('extracted-card').style.display = 'block';
  g('step-2').style.display         = 'block';
  g('page-count-badge').textContent = '1 page';
  setStep(2);
  g('step-2').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  toast('Text ready for conversion!', 'success');
}

/* ── Settings ─────────────────────────────────────────────────── */
function setPaper(el) {
  document.querySelectorAll('.paper-option').forEach(o => o.classList.remove('active'));
  el.classList.add('active'); S.paper = el.dataset.value;
}
function setColor(el) {
  document.querySelectorAll('.color-option').forEach(o => o.classList.remove('active'));
  el.classList.add('active'); S.color = el.dataset.value;
}
function setFormat(el) {
  document.querySelectorAll('.format-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected'); S.format = el.dataset.value;
  const r = el.querySelector('input[type=radio]');
  if (r) r.checked = true;
}
function updateSlider(id, vid) {
  const v = parseFloat(g(id).value);
  g(vid).textContent = Number.isInteger(v) ? v : v.toFixed(1);
}

/* ── Convert ──────────────────────────────────────────────────── */
async function convertToHandwriting() {
  if (S.converting) return;
  const txt = (g('extracted-text').value || '').trim();
  if (!txt) return toast('No text to convert', 'warning');
  S.converting = true;
  g('convert-btn').disabled = true;
  showState('loading');
  g('download-card').style.display = 'none';
  startLoadingAnim();
  try {
    const pages = S.pages.length > 1 ? S.pages : [txt];
    const payload = {
      pages,
      text:           txt,
      font_name:      S.font,
      font_size:      parseInt(g('font-size').value, 10),
      line_spacing:   parseFloat(g('line-spacing').value),
      ink_color:      S.color,
      margin:         parseInt(g('margin').value, 10),
      paper_style:    S.paper,
      output_format:  S.format,
      page_width:     794,
      page_height:    1123,
      preserve_layout: !!(g('preserve-layout') && g('preserve-layout').checked && S.layoutData),
      layout_data:    S.layoutData || null,
    };
    console.log('Convert:', `font=${S.font} fmt=${S.format} pages=${pages.length}`);
    const res = await fetch('/api/convert', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const raw = await res.text();
    console.log('Response:', raw.slice(0, 200));
    let data;
    try { data = JSON.parse(raw); }
    catch (e) {
      console.error('Full response:', raw);
      throw new Error(`Invalid JSON (HTTP ${res.status}): ${raw.slice(0, 120)}`);
    }
    if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`);
    S.sessionId   = data.session_id;
    S.jpgUrls     = data.jpg_urls || [];
    S.currentPage = 0;
    await showPreview(data);
    buildDownloadUI(data, data.page_count || pages.length);
    setStep(3);
    toast('✅ Handwriting generated!', 'success');
  } catch (e) {
    console.error('Convert error:', e);
    toast(`Conversion failed: ${e.message}`, 'error');
    showState('empty');
  } finally {
    S.converting = false;
    g('convert-btn').disabled = false;
    stopLoadingAnim();
  }
}

/* ── Preview ──────────────────────────────────────────────────── */
async function showPreview(data) {
  let url = data.preview_url || '';
  if (!url && data.pdf_url) url = `/api/preview/${data.session_id}`;
  if (!url && data.jpg_urls && data.jpg_urls.length) url = data.jpg_urls[0];
  if (!url) { showState('done-no-preview'); return; }
  return new Promise(resolve => {
    const img = g('preview-image');
    img.onload  = () => {
      showState('preview');
      if (S.jpgUrls.length > 1) {
        g('preview-controls').style.display = 'flex';
        refreshPageLabel();
      }
      resolve();
    };
    img.onerror = () => { showState('done-no-preview'); resolve(); };
    img.src = url + '?t=' + Date.now();
  });
}

function showState(state) {
  g('empty-preview').style.display    = (state === 'empty' || state === 'done-no-preview') ? 'block' : 'none';
  g('preview-loading').style.display  = state === 'loading'  ? 'flex'  : 'none';
  g('preview-container').style.display= state === 'preview'  ? 'block' : 'none';
  if (state === 'done-no-preview') {
    g('empty-preview').innerHTML = `
      <div class="empty-icon">
        <i class="fas fa-check-circle" style="color:var(--ok)"></i>
      </div>
      <h3>Handwriting generated!</h3>
      <p>Download your file below.</p>`;
  }
}

/* ── Page nav ─────────────────────────────────────────────────── */
function prevPage() { if (S.currentPage > 0) { S.currentPage--; flipPage(); } }
function nextPage() { if (S.currentPage < S.jpgUrls.length - 1) { S.currentPage++; flipPage(); } }
function flipPage() {
  g('preview-image').src = S.jpgUrls[S.currentPage] + '?t=' + Date.now();
  refreshPageLabel();
}
function refreshPageLabel() {
  g('page-indicator').textContent = `${S.currentPage + 1} / ${S.jpgUrls.length}`;
  g('prev-page-btn').disabled = S.currentPage === 0;
  g('next-page-btn').disabled = S.currentPage === S.jpgUrls.length - 1;
}

/* ── Download UI ──────────────────────────────────────────────── */
function buildDownloadUI(data, pageCount) {
  g('dl-pages').textContent  = pageCount;
  g('dl-format').textContent = (data.output_format || 'pdf').toUpperCase();
  g('dl-font').textContent   = S.font.replace(/_/g, ' ').slice(0, 12);
  const btn = g('download-buttons');
  btn.innerHTML = '';
  if (data.pdf_url) {
    btn.appendChild(mkBtn(data.pdf_url, 'handwritten_notes.pdf',
      'btn-dl-pdf', 'fas fa-file-pdf', '⬇ Download PDF (All Pages)'));
  }
  if (data.jpg_urls && data.jpg_urls.length === 1) {
    btn.appendChild(mkBtn(data.jpg_urls[0], 'handwritten_page_1.jpg',
      'btn-dl-jpg', 'fas fa-file-image', '⬇ Download JPG'));
  } else if (data.jpg_urls && data.jpg_urls.length > 1) {
    data.jpg_urls.forEach((u, i) => {
      btn.appendChild(mkBtn(u, `handwritten_page_${i+1}.jpg`,
        'btn-dl-jpg', 'fas fa-file-image', `⬇ Page ${i+1} (JPG)`));
    });
    btn.appendChild(mkBtn(
      `/api/download/${data.session_id}/all`, 'handwritten_notes.zip',
      'btn-dl-zip', 'fas fa-file-archive', '⬇ All Pages (ZIP)'));
  }
  g('download-card').style.display = 'block';
  g('download-card').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function mkBtn(href, name, cls, icon, label) {
  const a = document.createElement('a');
  a.href = href; a.download = name;
  a.className = `btn ${cls} btn-full`;
  a.innerHTML = `<i class="${icon}"></i> ${label}`;
  return a;
}

/* ── Loading animation ────────────────────────────────────────── */
let _lt = null;
const _lm = [
  'Loading handwriting fonts…', 'Sketching your text…',
  'Adding paper texture…',      'Applying ink effects…',
  'Assembling pages…',          'Almost done…',
];
function startLoadingAnim() {
  let i = 0;
  g('loading-text').textContent = _lm[0];
  _lt = setInterval(() => { i=(i+1)%_lm.length; g('loading-text').textContent = _lm[i]; }, 1800);
}
function stopLoadingAnim() { clearInterval(_lt); _lt = null; }

/* ── Char counter ─────────────────────────────────────────────── */
function initCharCounter() {
  const ta = g('direct-text');
  if (!ta) return;
  ta.addEventListener('input', () => {
    g('char-count').textContent = `${ta.value.length.toLocaleString()} characters`;
  });
}
function clearText() {
  g('direct-text').value = '';
  g('char-count').textContent = '0 characters';
}

/* ── Step indicator ───────────────────────────────────────────── */
function setStep(n) {
  for (let i = 1; i <= 3; i++) {
    const el = document.getElementById(`step-indicator-${i}`);
    if (!el) continue;
    const c = el.querySelector('.step-circle');
    el.classList.remove('active', 'completed');
    if (i < n)      { el.classList.add('completed'); c.innerHTML = '<i class="fas fa-check"></i>'; }
    else if (i === n){ el.classList.add('active');   c.textContent = i; }
    else             { c.textContent = i; }
  }
}

/* ── Reset ────────────────────────────────────────────────────── */
function resetAll() {
  Object.assign(S, { file:null, pages:[], layoutData:null,
    sessionId:null, jpgUrls:[], currentPage:0 });
  ['upload-zone','extracted-card','step-2','download-card'].forEach(id => {
    g(id).style.display = id === 'upload-zone' ? 'block' : 'none';
  });
  g('file-preview').style.display     = 'none';
  g('extract-btn').style.display      = 'none';
  g('file-input').value               = '';
  g('layout-opt').style.display       = 'none';
  g('preview-controls').style.display = 'none';
  g('direct-text').value              = '';
  g('char-count').textContent         = '0 characters';
  showState('empty');
  setStep(1);
  window.scrollTo({ top: 0, behavior: 'smooth' });
  toast('Ready for a new conversion!', 'success');
}

/* ── Toast ────────────────────────────────────────────────────── */
function toast(msg, type='info') {
  const icons = {
    success:'fas fa-check-circle', error:'fas fa-exclamation-circle',
    warning:'fas fa-exclamation-triangle', info:'fas fa-info-circle',
  };
  const d = document.createElement('div');
  d.className = `toast ${type}`;
  d.innerHTML = `
    <i class="${icons[type]||icons.info}"></i>
    <span class="toast-msg">${xss(msg)}</span>
    <button onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>`;
  g('toast-container').appendChild(d);
  setTimeout(() => {
    d.style.opacity = '0'; d.style.transform = 'translateX(110%)';
    d.style.transition = 'all .3s'; setTimeout(() => d.remove(), 320);
  }, 5000);
}

/* ── Overlay ──────────────────────────────────────────────────── */
function showOverlay(t='Processing…') { g('overlay-text').textContent = t; g('overlay').style.display = 'flex'; }
function hideOverlay() { g('overlay').style.display = 'none'; }

/* ── Utilities ────────────────────────────────────────────────── */
function g(id) { return document.getElementById(id); }
function xss(s) {
  const d = document.createElement('div');
  d.textContent = String(s == null ? '' : s);
  return d.innerHTML;
}
function fmtSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(1) + ' MB';
}

/* ── Keyboard shortcuts ───────────────────────────────────────── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') hideOverlay();
  if (g('preview-container') && g('preview-container').style.display !== 'none') {
    if (e.key === 'ArrowLeft')  prevPage();
    if (e.key === 'ArrowRight') nextPage();
  }
});
