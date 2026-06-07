/* ============================================================
   PDF to Handwriting Converter  –  main.js  v3.0
   ============================================================ */
'use strict';

/* ── State ─────────────────────────────────────────────────── */
const S = {
  file          : null,
  pages         : [],
  layoutData    : null,
  font          : 'Kalam',
  paper         : 'ruled',
  color         : 'blue',
  format        : 'pdf',
  sessionId     : null,
  jpgUrls       : [],
  currentPage   : 0,
  converting    : false,
};

/* ── Boot ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  loadFonts();
  initCharCounter();
  setFormat(document.querySelector('.format-option[data-value="pdf"]'));
  setColor(document.querySelector('.color-option[data-value="blue"]'));
  setPaper(document.querySelector('.paper-option[data-value="ruled"]'));
});

/* ── Font loading ───────────────────────────────────────────── */
async function loadFonts() {
  const grid = id('font-grid');
  try {
    const res  = await fetchJSON('/api/fonts');
    const fonts = (res && res.fonts) ? res.fonts : [];
    if (!fonts.length) throw new Error('empty');
    renderFonts(fonts);
  } catch (e) {
    grid.innerHTML = fallbackFontHTML();
    bindFontCards();
  }
}

function renderFonts(fonts) {
  const grid = id('font-grid');
  grid.innerHTML = fonts.map(f => `
    <div class="font-card ${f.key === S.font ? 'selected' : ''}"
         data-key="${esc(f.key)}"
         onclick="pickFont(this)">
      <div class="fc-name">${esc(f.display_name)}</div>
      <div class="fc-desc">${esc(f.description)}</div>
      ${!f.available ? '<div class="fc-dl"><i class="fas fa-download"></i> Queued</div>' : ''}
    </div>`).join('');
}

function fallbackFontHTML() {
  const list = [
    ['HomemadeApple','✍️ Homemade Apple','Classic cursive'],
    ['Kalam',        '🖊️ Kalam',         'Natural pen'],
    ['Caveat',       '📝 Caveat',         'Casual writing'],
    ['DancingScript','💫 Dancing Script', 'Elegant script'],
    ['Pacifico',     '🌊 Pacifico',       'Bold casual'],
    ['IndieFlower',  '🌸 Indie Flower',   'Bubbly cute'],
    ['PatrickHand',  '📋 Patrick Hand',   'Neat print'],
    ['GloriaHallelujah','✨ Gloria',      'Comic style'],
  ];
  return list.map(([k,n,d]) => `
    <div class="font-card ${k===S.font?'selected':''}"
         data-key="${k}" onclick="pickFont(this)">
      <div class="fc-name">${n}</div>
      <div class="fc-desc">${d}</div>
    </div>`).join('');
}

function bindFontCards() {
  id('font-grid').querySelectorAll('.font-card')
    .forEach(c => { c.onclick = () => pickFont(c); });
}

function pickFont(card) {
  document.querySelectorAll('.font-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  S.font = card.dataset.key;
  toast(`Font: ${card.dataset.key.replace(/_/g,' ')}`, 'info');
}

/* ── Tabs ───────────────────────────────────────────────────── */
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tabId));
  document.querySelectorAll('.tab-content').forEach(c =>
    c.classList.toggle('active', c.id === tabId));
}

/* ── Drag-and-drop / file select ────────────────────────────── */
function onDragOver(e)  { e.preventDefault(); id('upload-zone').classList.add('drag-over'); }
function onDragLeave()  { id('upload-zone').classList.remove('drag-over'); }
function onDrop(e)      { e.preventDefault(); onDragLeave(); processFile(e.dataTransfer.files[0]); }
function onFileChange(i){ if (i.files[0]) processFile(i.files[0]); }

function processFile(file) {
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf','jpg','jpeg','png'].includes(ext)) {
    return toast('Only PDF, JPG, PNG supported', 'error');
  }
  if (file.size > 50*1024*1024) {
    return toast('Max file size is 50 MB', 'error');
  }
  S.file = file;

  id('upload-zone').style.display = 'none';
  id('file-preview').style.display = 'block';
  id('extract-btn').style.display  = 'block';

  const icon = id('file-type-icon');
  icon.className = ext === 'pdf' ? 'fas fa-file-pdf' : 'fas fa-file-image';
  icon.style.color = ext === 'pdf' ? '#ef4444' : '#3b82f6';
  id('file-name').textContent = file.name;
  id('file-size').textContent = fmtSize(file.size);

  if (ext === 'pdf') id('layout-opt').style.display = 'block';
  toast(`File ready: ${file.name}`, 'success');
}

function removeFile() {
  S.file = null;
  id('upload-zone').style.display = 'block';
  id('file-preview').style.display = 'none';
  id('extract-btn').style.display  = 'none';
  id('file-input').value = '';
  id('layout-opt').style.display = 'none';
}

/* ── Extract ────────────────────────────────────────────────── */
async function extractText() {
  if (!S.file) return toast('Select a file first', 'warning');
  showOverlay('Extracting text…');
  try {
    const fd = new FormData();
    fd.append('file', S.file);
    fd.append('input_type', 'file');

    const res  = await fetch('/api/extract', { method:'POST', body:fd });
    const text = await res.text();          // raw text first

    let data;
    try { data = JSON.parse(text); }
    catch(e) {
      console.error('Extract raw response:', text.slice(0,500));
      throw new Error('Server returned invalid JSON during extraction');
    }

    if (!res.ok || data.error) throw new Error(data.error || 'Extraction failed');

    S.pages      = data.pages || [data.text || ''];
    S.layoutData = data.layout_data || null;

    id('extracted-text').value = data.text || '';
    id('extracted-card').style.display = 'block';
    id('step-2').style.display         = 'block';
    id('page-count-badge').textContent =
      `${data.page_count || 1} page${data.page_count !== 1 ? 's' : ''}`;

    setStep(2);
    id('step-2').scrollIntoView({ behavior:'smooth', block:'nearest' });
    toast(`Extracted ${data.page_count || 1} page(s)`, 'success');
  } catch(e) {
    console.error(e);
    toast(`Extraction error: ${e.message}`, 'error');
  } finally {
    hideOverlay();
  }
}

function useDirectText() {
  const txt = id('direct-text').value.trim();
  if (!txt) return toast('Enter some text first', 'warning');

  S.pages      = [txt];
  S.layoutData = null;

  id('extracted-text').value         = txt;
  id('extracted-card').style.display = 'block';
  id('step-2').style.display         = 'block';
  id('page-count-badge').textContent = '1 page';

  setStep(2);
  id('step-2').scrollIntoView({ behavior:'smooth', block:'nearest' });
  toast('Text ready!', 'success');
}

/* ── Settings helpers ───────────────────────────────────────── */
function setPaper(el) {
  document.querySelectorAll('.paper-option').forEach(o => o.classList.remove('active'));
  el.classList.add('active');
  S.paper = el.dataset.value;
}
function setColor(el) {
  document.querySelectorAll('.color-option').forEach(o => o.classList.remove('active'));
  el.classList.add('active');
  S.color = el.dataset.value;
}
function setFormat(el) {
  document.querySelectorAll('.format-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  S.format = el.dataset.value;
  const r = el.querySelector('input[type=radio]');
  if (r) r.checked = true;
}

function updateSlider(sliderId, valId) {
  const v = parseFloat(id(sliderId).value);
  id(valId).textContent = Number.isInteger(v) ? v : v.toFixed(1);
}

/* ── Convert ────────────────────────────────────────────────── */
async function convertToHandwriting() {
  if (S.converting) return;

  const txt = (id('extracted-text').value || '').trim();
  if (!txt) return toast('No text to convert – extract or type some text first', 'warning');

  S.converting = true;
  id('convert-btn').disabled = true;

  showState('loading');
  id('download-card').style.display = 'none';

  startLoadingAnim();

  try {
    // Rebuild pages from edited textarea
    const pages = S.pages.length > 1
      ? S.pages
      : [txt];

    const payload = {
      pages,
      text         : txt,
      font_name    : S.font,
      font_size    : parseInt(id('font-size').value, 10),
      line_spacing : parseFloat(id('line-spacing').value),
      ink_color    : S.color,
      margin       : parseInt(id('margin').value, 10),
      paper_style  : S.paper,
      output_format: S.format,
      page_width   : 794,
      page_height  : 1123,
      preserve_layout: !!(id('preserve-layout') &&
                          id('preserve-layout').checked &&
                          S.layoutData),
      layout_data  : S.layoutData || null,
    };

    console.log('Convert payload pages count:', pages.length,
                'font:', S.font, 'format:', S.format);

    const res  = await fetch('/api/convert', {
      method  : 'POST',
      headers : { 'Content-Type': 'application/json' },
      body    : JSON.stringify(payload),
    });

    // Read raw body first so we can log it on failure
    const rawBody = await res.text();
    console.log('Convert raw response (first 300):', rawBody.slice(0, 300));

    let data;
    try {
      data = JSON.parse(rawBody);
    } catch (parseErr) {
      console.error('Full raw response:', rawBody);
      throw new Error(
        `Server response is not valid JSON. ` +
        `Status ${res.status}. ` +
        `Body starts with: "${rawBody.slice(0, 120)}"`
      );
    }

    if (!res.ok || data.error) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }

    // ── Success ──────────────────────────────────────────────
    S.sessionId   = data.session_id;
    S.jpgUrls     = data.jpg_urls || [];
    S.currentPage = 0;

    const pageCount = data.page_count || pages.length || 1;

    await showPreview(data);
    buildDownloadUI(data, pageCount);
    setStep(3);
    toast('✅ Handwriting generated!', 'success');

  } catch (err) {
    console.error('Conversion error:', err);
    toast(`Conversion failed: ${err.message}`, 'error');
    showState('empty');
  } finally {
    S.converting = false;
    id('convert-btn').disabled = false;
    stopLoadingAnim();
  }
}

/* ── Preview ────────────────────────────────────────────────── */
async function showPreview(data) {
  let url = data.preview_url || '';
  if (!url && data.pdf_url) url = `/api/preview/${data.session_id}`;
  if (!url && data.jpg_urls && data.jpg_urls.length)
    url = data.jpg_urls[0];

  if (!url) { showState('empty'); return; }

  return new Promise(resolve => {
    const img = id('preview-image');
    const bust = `?t=${Date.now()}`;

    img.onload = () => {
      showState('preview');
      if (S.jpgUrls.length > 1) {
        id('preview-controls').style.display = 'flex';
        refreshPageLabel();
      }
      resolve();
    };
    img.onerror = () => {
      showState('done-no-preview');
      resolve();
    };
    img.src = url + bust;
  });
}

function showState(state) {
  id('empty-preview').style.display   = state === 'empty'   ? 'block' : 'none';
  id('preview-loading').style.display = state === 'loading' ? 'flex'  : 'none';
  id('preview-container').style.display =
    state === 'preview' ? 'block' : 'none';

  if (state === 'done-no-preview') {
    id('empty-preview').style.display = 'block';
    id('empty-preview').innerHTML = `
      <div class="empty-icon">
        <i class="fas fa-check-circle" style="color:var(--success)"></i>
      </div>
      <h3>Handwriting generated!</h3>
      <p>Download your file below.</p>`;
  }
}

/* ── Page navigation ────────────────────────────────────────── */
function prevPage() {
  if (S.currentPage > 0) { S.currentPage--; flipPage(); }
}
function nextPage() {
  if (S.currentPage < S.jpgUrls.length - 1) { S.currentPage++; flipPage(); }
}
function flipPage() {
  const img = id('preview-image');
  img.src   = S.jpgUrls[S.currentPage] + `?t=${Date.now()}`;
  refreshPageLabel();
}
function refreshPageLabel() {
  id('page-indicator').textContent =
    `Page ${S.currentPage + 1} / ${S.jpgUrls.length}`;
  id('prev-page-btn').disabled = S.currentPage === 0;
  id('next-page-btn').disabled = S.currentPage === S.jpgUrls.length - 1;
}

/* ── Download UI ────────────────────────────────────────────── */
function buildDownloadUI(data, pageCount) {
  const card    = id('download-card');
  const buttons = id('download-buttons');

  id('dl-pages').textContent  = pageCount;
  id('dl-format').textContent = (data.output_format || 'pdf').toUpperCase();

  buttons.innerHTML = '';

  if (data.pdf_url) {
    buttons.appendChild(mkDownloadBtn(
      data.pdf_url,
      'handwritten_notes.pdf',
      'btn-dl-pdf',
      'fas fa-file-pdf',
      'Download PDF  (all pages)'
    ));
  }

  if (data.jpg_urls && data.jpg_urls.length === 1) {
    buttons.appendChild(mkDownloadBtn(
      data.jpg_urls[0],
      'handwritten_page_1.jpg',
      'btn-dl-jpg',
      'fas fa-file-image',
      'Download JPG Image'
    ));
  } else if (data.jpg_urls && data.jpg_urls.length > 1) {
    data.jpg_urls.forEach((u, i) => {
      buttons.appendChild(mkDownloadBtn(
        u,
        `handwritten_page_${i+1}.jpg`,
        'btn-dl-jpg',
        'fas fa-file-image',
        `Download Page ${i+1} (JPG)`
      ));
    });
    buttons.appendChild(mkDownloadBtn(
      `/api/download/${data.session_id}/all`,
      'handwritten_notes.zip',
      'btn-dl-zip',
      'fas fa-file-archive',
      'Download All Pages (ZIP)'
    ));
  }

  card.style.display = 'block';
  card.scrollIntoView({ behavior:'smooth', block:'nearest' });
}

function mkDownloadBtn(href, name, cls, icon, label) {
  const a = document.createElement('a');
  a.href         = href;
  a.download     = name;
  a.className    = `btn ${cls} btn-full`;
  a.innerHTML    = `<i class="${icon}"></i> ${label}`;
  return a;
}

/* ── Loading animation ──────────────────────────────────────── */
let _loadTmr = null;
const _loadMsgs = [
  'Loading handwriting fonts…',
  'Sketching your text…',
  'Adding paper texture…',
  'Applying ink effects…',
  'Assembling pages…',
  'Almost done…',
];
function startLoadingAnim() {
  let i = 0;
  id('loading-text').textContent = _loadMsgs[0];
  _loadTmr = setInterval(() => {
    i = (i + 1) % _loadMsgs.length;
    id('loading-text').textContent = _loadMsgs[i];
  }, 1800);
}
function stopLoadingAnim() {
  clearInterval(_loadTmr);
  _loadTmr = null;
}

/* ── Char counter ───────────────────────────────────────────── */
function initCharCounter() {
  const ta = id('direct-text');
  if (!ta) return;
  ta.addEventListener('input', () => {
    id('char-count').textContent =
      `${ta.value.length.toLocaleString()} characters`;
  });
}
function clearText() {
  id('direct-text').value = '';
  id('char-count').textContent = '0 characters';
}

/* ── Step indicator ─────────────────────────────────────────── */
function setStep(n) {
  for (let i = 1; i <= 3; i++) {
    const el = id(`step-indicator-${i}`);
    if (!el) continue;
    const circle = el.querySelector('.step-circle');
    el.classList.remove('active','completed');
    if (i < n)      { el.classList.add('completed'); circle.innerHTML = '<i class="fas fa-check"></i>'; }
    else if (i===n) { el.classList.add('active');    circle.textContent = i; }
    else            { circle.textContent = i; }
  }
}

/* ── Reset ──────────────────────────────────────────────────── */
function resetAll() {
  Object.assign(S, {
    file:null, pages:[], layoutData:null,
    sessionId:null, jpgUrls:[], currentPage:0,
  });

  id('upload-zone').style.display     = 'block';
  id('file-preview').style.display    = 'none';
  id('extract-btn').style.display     = 'none';
  id('file-input').value              = '';
  id('layout-opt').style.display      = 'none';
  id('extracted-card').style.display  = 'none';
  id('step-2').style.display          = 'none';
  id('download-card').style.display   = 'none';
  id('preview-controls').style.display= 'none';
  id('direct-text').value             = '';
  id('char-count').textContent        = '0 characters';

  showState('empty');
  setStep(1);
  window.scrollTo({ top:0, behavior:'smooth' });
  toast('Ready for a new conversion!', 'success');
}

/* ── Toast ──────────────────────────────────────────────────── */
function toast(msg, type='info') {
  const icons = {
    success:'fas fa-check-circle',
    error:'fas fa-exclamation-circle',
    warning:'fas fa-exclamation-triangle',
    info:'fas fa-info-circle',
  };
  const div = document.createElement('div');
  div.className = `toast ${type}`;
  div.innerHTML = `
    <i class="${icons[type]||icons.info}"></i>
    <span class="toast-msg">${esc(msg)}</span>
    <button onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>`;
  id('toast-container').appendChild(div);
  setTimeout(() => {
    div.style.opacity   = '0';
    div.style.transform = 'translateX(110%)';
    div.style.transition= 'all .3s';
    setTimeout(()=>div.remove(), 320);
  }, 5000);
}

/* ── Overlay ────────────────────────────────────────────────── */
function showOverlay(txt='Processing…') {
  id('overlay-text').textContent = txt;
  id('overlay').style.display    = 'flex';
}
function hideOverlay() {
  id('overlay').style.display = 'none';
}

/* ── Utilities ──────────────────────────────────────────────── */
function id(x)       { return document.getElementById(x); }
function esc(s)      { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
function fmtSize(b)  {
  if (b < 1024)         return `${b} B`;
  if (b < 1024**2)      return `${(b/1024).toFixed(1)} KB`;
  return `${(b/1024**2).toFixed(1)} MB`;
}
async function fetchJSON(url, opts={}) {
  const r = await fetch(url, opts);
  const t = await r.text();
  try { return JSON.parse(t); }
  catch(e) { throw new Error(`Invalid JSON from ${url}: ${t.slice(0,200)}`); }
}

/* ── Keyboard shortcuts ─────────────────────────────────────── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') hideOverlay();
  if (id('preview-container').style.display !== 'none') {
    if (e.key === 'ArrowLeft')  prevPage();
    if (e.key === 'ArrowRight') nextPage();
  }
});
