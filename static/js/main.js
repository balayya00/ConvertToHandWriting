/* ============================================================
   PDF to Handwriting – main.js v4.0
   Live font previews via Google Fonts CSS classes
   ============================================================ */
'use strict';

/* ── State ───────────────────────────────────────────────────── */
const S = {
  file:null, pages:[], layoutData:null,
  font:'Kalam', paper:'ruled', color:'blue', format:'pdf',
  sessionId:null, jpgUrls:[], currentPage:0, converting:false,
  allFonts:[], activeCat:'all',
};

/* ── CSS font-family map (matches <style> block in HTML) ─────── */
const FONT_CSS = {
  HomemadeApple:        'Homemade Apple',
  DancingScript:        'Dancing Script',
  GreatVibes:           'Great Vibes',
  Allura:               'Allura',
  Sacramento:           'Sacramento',
  Parisienne:           'Parisienne',
  Pinyon_Script:        'Pinyon Script',
  Tangerine:            'Tangerine',
  AlexBrush:            'Alex Brush',
  Yellowtail:           'Yellowtail',
  Satisfy:              'Satisfy',
  Kalam:                'Kalam',
  Caveat:               'Caveat',
  Patrick_Hand:         'Patrick Hand',
  Indie_Flower:         'Indie Flower',
  Shadows_Into_Light:   'Shadows Into Light',
  Nothing_You_Could_Do: 'Nothing You Could Do',
  Covered_By_Your_Grace:'Covered By Your Grace',
  GloriaHallelujah:     'Gloria Hallelujah',
  Architects_Daughter:  'Architects Daughter',
  Permanent_Marker:     'Permanent Marker',
  Rock_Salt:            'Rock Salt',
  Pacifico:             'Pacifico',
  Damion:               'Damion',
  Marck_Script:         'Marck Script',
  Engagement:           'Engagement',
  Euphoria_Script:      'Euphoria Script',
  Italianno:            'Italianno',
  Norican:              'Norican',
  Rouge_Script:         'Rouge Script',
  Clicker_Script:       'Clicker Script',
  Kurale:               'Kurale',
  Amatic_SC:            'Amatic SC',
  Dr_Sugiyama:          'Dr Sugiyama',
  Qwitcher_Grypen:      'Qwitcher Grypen',
};

/* Category keywords to map style strings */
const CAT_MAP = {
  Calligraphy: ['calligraph','script','formal','copperplate','italic','victorian',
                'french','wedding','romantic','passionate','japanese','gothic',
                'fluid','artistic','flowing','fine','brush','retro'],
  Cursive:     ['cursive','cursive','elegant','smooth','dreamy','love letter'],
  Natural:     ['natural','casual','everyday','bubbly','light','comic','technical',
                'condensed','typewriter','decorative'],
  Bold:        ['bold','marker','rough','textured'],
  Print:       ['print','printing','draft'],
};

function getCategory(style) {
  const s = (style || '').toLowerCase();
  for (const [cat, keywords] of Object.entries(CAT_MAP)) {
    if (keywords.some(k => s.includes(k))) return cat;
  }
  return 'Natural';
}

/* Preview sample texts per style */
const PREVIEWS = {
  Calligraphy: 'Beautiful Writing',
  Cursive:     'Hello World',
  Natural:     'My Handwriting',
  Bold:        'Bold Notes',
  Print:       'Clear Print',
};

/* ── Boot ────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  loadFonts();
  initCharCounter();
  /* Default selections already set in HTML via class="selected/active" */
  S.format = 'pdf';
  S.color  = 'blue';
  S.paper  = 'ruled';
});

/* ── Font loading ─────────────────────────────────────────────── */
async function loadFonts() {
  try {
    const res = await fetch('/api/fonts');
    const raw = await res.text();
    let data;
    try { data = JSON.parse(raw); } catch(e) { throw new Error('Bad JSON from /api/fonts'); }

    if (data.fonts && data.fonts.length) {
      S.allFonts = data.fonts;
      renderFonts(data.fonts);
    } else {
      throw new Error('No fonts in response');
    }
  } catch(e) {
    console.warn('Font API error:', e);
    /* Build fallback list from FONT_CSS keys */
    S.allFonts = Object.keys(FONT_CSS).map(key => ({
      key, display: key.replace(/_/g,' '),
      emoji: '✍️', style: 'Natural', available: false,
    }));
    renderFonts(S.allFonts);
  }
}

function renderFonts(fonts, filter='') {
  const grid = $('font-grid');
  grid.innerHTML = '';

  const q   = filter.toLowerCase();
  const cat = S.activeCat;

  let shown = 0;
  fonts.forEach(f => {
    const fCat = getCategory(f.style || '');
    const matchCat  = (cat === 'all') || (fCat === cat);
    const matchText = !q ||
      f.display.toLowerCase().includes(q) ||
      (f.style||'').toLowerCase().includes(q);

    if (!matchCat || !matchText) return;

    shown++;
    const isSelected = f.key === S.font;
    const cssFamily  = FONT_CSS[f.key] || f.display;
    const previewTxt = PREVIEWS[fCat] || 'Handwriting';

    const card = document.createElement('div');
    card.className = `font-card${isSelected ? ' selected' : ''}`;
    card.dataset.key = f.key;
    card.dataset.cat = fCat;

    card.innerHTML = `
      <div class="fc-emoji">${esc(f.emoji || '✍️')}</div>
      <div class="fc-name">${esc(f.display)}</div>
      <div class="fc-preview ff-${esc(f.key)}"
           style="font-family:'${cssFamily}',cursive">${esc(previewTxt)}</div>
      <div class="fc-style">${esc(f.style || '')}</div>`;

    card.addEventListener('click', () => pickFont(card, f));
    grid.appendChild(card);
  });

  if (shown === 0) {
    grid.innerHTML = '<div class="loading-fonts">No fonts match your search.</div>';
  }
}

function pickFont(card, fontInfo) {
  document.querySelectorAll('.font-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  S.font = fontInfo.key;

  /* Update label */
  const lbl = $('selected-font-name');
  if (lbl) lbl.textContent = fontInfo.display;

  toast(`Font: ${fontInfo.display}`, 'info');
}

function filterFonts(q) {
  renderFonts(S.allFonts, q);
}

function filterCat(btn, cat) {
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  S.activeCat = cat;
  renderFonts(S.allFonts, $('font-search').value || '');
}

/* ── Tabs ────────────────────────────────────────────────────── */
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tabId));
  document.querySelectorAll('.tab-content').forEach(c =>
    c.classList.toggle('active', c.id === tabId));
}

/* ── Drag-and-drop ───────────────────────────────────────────── */
function onDragOver(e)  { e.preventDefault(); $('upload-zone').classList.add('drag-over'); }
function onDragLeave()  { $('upload-zone').classList.remove('drag-over'); }
function onDrop(e)      { e.preventDefault(); onDragLeave(); processFile(e.dataTransfer.files[0]); }
function onFileChange(i){ if(i.files[0]) processFile(i.files[0]); }

function processFile(file) {
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf','jpg','jpeg','png'].includes(ext))
    return toast('Only PDF, JPG, PNG supported', 'error');
  if (file.size > 50*1024*1024)
    return toast('Max file size is 50 MB', 'error');

  S.file = file;
  $('upload-zone').style.display  = 'none';
  $('file-preview').style.display = 'block';
  $('extract-btn').style.display  = 'block';

  const ico = $('file-type-icon');
  ico.className   = ext === 'pdf' ? 'fas fa-file-pdf' : 'fas fa-file-image';
  ico.style.color = ext === 'pdf' ? '#ef4444' : '#3b82f6';
  $('file-name').textContent = file.name;
  $('file-size').textContent = fmtSize(file.size);
  if (ext === 'pdf') $('layout-opt').style.display = 'block';
  toast(`File ready: ${file.name}`, 'success');
}

function removeFile() {
  S.file = null;
  $('upload-zone').style.display  = 'block';
  $('file-preview').style.display = 'none';
  $('extract-btn').style.display  = 'none';
  $('file-input').value           = '';
  $('layout-opt').style.display   = 'none';
}

/* ── Extract ─────────────────────────────────────────────────── */
async function extractText() {
  if (!S.file) return toast('Select a file first', 'warning');
  showOverlay('Extracting text…');
  try {
    const fd = new FormData();
    fd.append('file', S.file);
    fd.append('input_type', 'file');

    const res  = await fetch('/api/extract', { method:'POST', body:fd });
    const raw  = await res.text();
    let data;
    try { data = JSON.parse(raw); }
    catch(e) {
      console.error('Extract raw:', raw.slice(0,400));
      throw new Error('Server returned non-JSON during extraction');
    }
    if (!res.ok || data.error) throw new Error(data.error || 'Extraction failed');

    S.pages      = data.pages || [data.text || ''];
    S.layoutData = data.layout_data || null;

    $('extracted-text').value         = data.text || '';
    $('extracted-card').style.display = 'block';
    $('step-2').style.display         = 'block';
    $('page-count-badge').textContent =
      `${data.page_count||1} page${data.page_count!==1?'s':''}`;

    setStep(2);
    $('step-2').scrollIntoView({ behavior:'smooth', block:'nearest' });
    toast(`Extracted ${data.page_count||1} page(s)`, 'success');
  } catch(e) {
    console.error(e);
    toast(`Extraction error: ${e.message}`, 'error');
  } finally { hideOverlay(); }
}

function useDirectText() {
  const txt = ($('direct-text').value || '').trim();
  if (!txt) return toast('Enter some text first', 'warning');

  S.pages = [txt]; S.layoutData = null;
  $('extracted-text').value         = txt;
  $('extracted-card').style.display = 'block';
  $('step-2').style.display         = 'block';
  $('page-count-badge').textContent = '1 page';
  setStep(2);
  $('step-2').scrollIntoView({ behavior:'smooth', block:'nearest' });
  toast('Text ready!', 'success');
}

/* ── Settings ────────────────────────────────────────────────── */
function setPaper(el) {
  document.querySelectorAll('.paper-option').forEach(o=>o.classList.remove('active'));
  el.classList.add('active'); S.paper = el.dataset.value;
}
function setColor(el) {
  document.querySelectorAll('.color-option').forEach(o=>o.classList.remove('active'));
  el.classList.add('active'); S.color = el.dataset.value;
}
function setFormat(el) {
  document.querySelectorAll('.format-option').forEach(o=>o.classList.remove('selected'));
  el.classList.add('selected'); S.format = el.dataset.value;
  const r = el.querySelector('input[type=radio]');
  if (r) r.checked = true;
}
function updateSlider(id, vid) {
  const v = parseFloat($(id).value);
  $(vid).textContent = Number.isInteger(v) ? v : v.toFixed(1);
}

/* ── Convert ─────────────────────────────────────────────────── */
async function convertToHandwriting() {
  if (S.converting) return;
  const txt = ($('extracted-text').value || '').trim();
  if (!txt) return toast('No text to convert – extract or type some text first', 'warning');

  S.converting = true;
  $('convert-btn').disabled = true;

  showState('loading');
  $('download-card').style.display = 'none';
  startLoadingAnim();

  try {
    const pages = S.pages.length > 1 ? S.pages : [txt];

    const payload = {
      pages,
      text          : txt,
      font_name     : S.font,
      font_size     : parseInt($('font-size').value, 10),
      line_spacing  : parseFloat($('line-spacing').value),
      ink_color     : S.color,
      margin        : parseInt($('margin').value, 10),
      paper_style   : S.paper,
      output_format : S.format,
      page_width    : 794,
      page_height   : 1123,
      preserve_layout: !!(
        $('preserve-layout') && $('preserve-layout').checked && S.layoutData
      ),
      layout_data   : S.layoutData || null,
    };

    console.log('Sending convert request:',
      `font=${S.font} fmt=${S.format} pages=${pages.length}`);

    const res = await fetch('/api/convert', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify(payload),
    });

    const raw = await res.text();
    console.log('Convert response (first 300):', raw.slice(0,300));

    let data;
    try { data = JSON.parse(raw); }
    catch(e) {
      console.error('Full response:', raw);
      throw new Error(
        `Server returned invalid JSON (HTTP ${res.status}). ` +
        `Starts with: "${raw.slice(0,100)}"`
      );
    }

    if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`);

    S.sessionId   = data.session_id;
    S.jpgUrls     = data.jpg_urls || [];
    S.currentPage = 0;

    const pageCount = data.page_count || pages.length || 1;
    await showPreview(data);
    buildDownloadUI(data, pageCount);
    setStep(3);
    toast('✅ Handwriting generated!', 'success');

  } catch(e) {
    console.error('Conversion error:', e);
    toast(`Conversion failed: ${e.message}`, 'error');
    showState('empty');
  } finally {
    S.converting = false;
    $('convert-btn').disabled = false;
    stopLoadingAnim();
  }
}

/* ── Preview display ─────────────────────────────────────────── */
async function showPreview(data) {
  let url = data.preview_url || '';
  if (!url && data.pdf_url)                    url = `/api/preview/${data.session_id}`;
  if (!url && data.jpg_urls && data.jpg_urls.length) url = data.jpg_urls[0];
  if (!url) { showState('done-no-preview'); return; }

  return new Promise(resolve => {
    const img  = $('preview-image');
    img.onload = () => {
      showState('preview');
      if (S.jpgUrls.length > 1) {
        $('preview-controls').style.display = 'flex';
        refreshPageLabel();
      }
      resolve();
    };
    img.onerror = () => { showState('done-no-preview'); resolve(); };
    img.src = url + '?t=' + Date.now();
  });
}

function showState(state) {
  $('empty-preview').style.display   = (state==='empty'||state==='done-no-preview') ? 'block' : 'none';
  $('preview-loading').style.display = state==='loading'  ? 'flex'  : 'none';
  $('preview-container').style.display = state==='preview'? 'block' : 'none';

  if (state === 'done-no-preview') {
    $('empty-preview').innerHTML = `
      <div class="empty-icon">
        <i class="fas fa-check-circle" style="color:var(--ok)"></i>
      </div>
      <h3>Generated!</h3><p>Download your file below.</p>`;
  }
}

/* ── Page nav ────────────────────────────────────────────────── */
function prevPage() { if(S.currentPage>0){ S.currentPage--; flipPage(); } }
function nextPage() { if(S.currentPage<S.jpgUrls.length-1){ S.currentPage++; flipPage(); } }
function flipPage() {
  $('preview-image').src = S.jpgUrls[S.currentPage]+'?t='+Date.now();
  refreshPageLabel();
}
function refreshPageLabel() {
  $('page-indicator').textContent = `${S.currentPage+1} / ${S.jpgUrls.length}`;
  $('prev-page-btn').disabled = S.currentPage === 0;
  $('next-page-btn').disabled = S.currentPage === S.jpgUrls.length-1;
}

/* ── Download UI ─────────────────────────────────────────────── */
function buildDownloadUI(data, pageCount) {
  $('dl-pages').textContent  = pageCount;
  $('dl-format').textContent = (data.output_format||'pdf').toUpperCase();
  $('dl-font').textContent   = S.font.replace(/_/g,' ').slice(0,10);

  const btn = $('download-buttons');
  btn.innerHTML = '';

  if (data.pdf_url) {
    btn.appendChild(mkDlBtn(data.pdf_url,'handwritten_notes.pdf',
      'btn-dl-pdf','fas fa-file-pdf','⬇ Download PDF (All Pages)'));
  }
  if (data.jpg_urls && data.jpg_urls.length === 1) {
    btn.appendChild(mkDlBtn(data.jpg_urls[0],'handwritten_page_1.jpg',
      'btn-dl-jpg','fas fa-file-image','⬇ Download JPG Image'));
  } else if (data.jpg_urls && data.jpg_urls.length > 1) {
    data.jpg_urls.forEach((u,i) => {
      btn.appendChild(mkDlBtn(u,`handwritten_page_${i+1}.jpg`,
        'btn-dl-jpg','fas fa-file-image',`⬇ Page ${i+1} (JPG)`));
    });
    btn.appendChild(mkDlBtn(
      `/api/download/${data.session_id}/all`,
      'handwritten_notes.zip',
      'btn-dl-zip','fas fa-file-archive','⬇ All Pages (ZIP)'));
  }

  $('download-card').style.display = 'block';
  $('download-card').scrollIntoView({ behavior:'smooth', block:'nearest' });
}

function mkDlBtn(href, name, cls, icon, label) {
  const a = document.createElement('a');
  a.href = href; a.download = name;
  a.className = `btn ${cls} btn-full`;
  a.innerHTML = `<i class="${icon}"></i> ${label}`;
  return a;
}

/* ── Loading anim ────────────────────────────────────────────── */
let _lt = null;
const _lm = [
  'Loading handwriting fonts…','Sketching your text…',
  'Adding paper texture…','Applying ink effects…',
  'Assembling pages…','Almost done…',
];
function startLoadingAnim() {
  let i=0; $('loading-text').textContent=_lm[0];
  _lt = setInterval(()=>{ i=(i+1)%_lm.length; $('loading-text').textContent=_lm[i]; },1800);
}
function stopLoadingAnim() { clearInterval(_lt); _lt=null; }

/* ── Char counter ────────────────────────────────────────────── */
function initCharCounter() {
  const ta = $('direct-text');
  if (!ta) return;
  ta.addEventListener('input', ()=>{
    $('char-count').textContent = `${ta.value.length.toLocaleString()} characters`;
  });
}
function clearText() { $('direct-text').value=''; $('char-count').textContent='0 characters'; }

/* ── Step indicator ──────────────────────────────────────────── */
function setStep(n) {
  for(let i=1;i<=3;i++){
    const el=document.getElementById(`step-indicator-${i}`);
    if(!el) continue;
    const c=el.querySelector('.step-circle');
    el.classList.remove('active','completed');
    if(i<n){el.classList.add('completed');c.innerHTML='<i class="fas fa-check"></i>';}
    else if(i===n){el.classList.add('active');c.textContent=i;}
    else{c.textContent=i;}
  }
}

/* ── Reset ───────────────────────────────────────────────────── */
function resetAll() {
  Object.assign(S,{file:null,pages:[],layoutData:null,
    sessionId:null,jpgUrls:[],currentPage:0});
  $('upload-zone').style.display      = 'block';
  $('file-preview').style.display     = 'none';
  $('extract-btn').style.display      = 'none';
  $('file-input').value               = '';
  $('layout-opt').style.display       = 'none';
  $('extracted-card').style.display   = 'none';
  $('step-2').style.display           = 'none';
  $('download-card').style.display    = 'none';
  $('preview-controls').style.display = 'none';
  $('direct-text').value              = '';
  $('char-count').textContent         = '0 characters';
  showState('empty');
  setStep(1);
  window.scrollTo({top:0,behavior:'smooth'});
  toast('Ready for a new conversion!','success');
}

/* ── Toast ───────────────────────────────────────────────────── */
function toast(msg,type='info'){
  const icons={success:'fas fa-check-circle',error:'fas fa-exclamation-circle',
    warning:'fas fa-exclamation-triangle',info:'fas fa-info-circle'};
  const d=document.createElement('div');
  d.className=`toast ${type}`;
  d.innerHTML=`<i class="${icons[type]}"></i>
    <span class="toast-msg">${esc(msg)}</span>
    <button onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>`;
  $('toast-container').appendChild(d);
  setTimeout(()=>{
    d.style.opacity='0';d.style.transform='translateX(110%)';
    d.style.transition='all .3s';setTimeout(()=>d.remove(),320);
  },5000);
}

/* ── Overlay ─────────────────────────────────────────────────── */
function showOverlay(t='Processing…'){$('overlay-text').textContent=t;$('overlay').style.display='flex';}
function hideOverlay(){$('overlay').style.display='none';}

/* ── Utils ───────────────────────────────────────────────────── */
function $(x){return document.getElementById(x);}
function esc(s){const d=document.createElement('div');d.textContent=String(s);return d.innerHTML;}
function fmtSize(b){
  if(b<1024)return b+' B';
  if(b<1048576)return (b/1024).toFixed(1)+' KB';
  return (b/1048576).toFixed(1)+' MB';
}

/* ── Keyboard ────────────────────────────────────────────────── */
document.addEventListener('keydown',e=>{
  if(e.key==='Escape') hideOverlay();
  if($('preview-container').style.display!=='none'){
    if(e.key==='ArrowLeft')  prevPage();
    if(e.key==='ArrowRight') nextPage();
  }
});
