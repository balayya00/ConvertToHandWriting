/**
 * PDF to Handwriting Converter - Main JavaScript
 */

// ===== STATE =====
const state = {
    currentTab: 'upload-tab',
    selectedFile: null,
    extractedPages: [],
    layoutData: null,
    isLayoutPreserved: false,
    selectedFont: 'Kalam',
    selectedPaper: 'ruled',
    selectedColor: 'blue',
    selectedFormat: 'pdf',
    sessionId: null,
    currentPage: 0,
    totalPages: 0,
    jpgUrls: [],
    isConverting: false,
    fontsLoaded: false
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    loadFonts();
    setupCharCounter();
    setupFormatOptions();
    
    // Select default format
    document.querySelector('.format-option[data-value="pdf"]').classList.add('selected');
});

// ===== FONT LOADING =====
async function loadFonts() {
    try {
        const response = await fetch('/api/fonts');
        const data = await response.json();
        
        if (data.fonts) {
            renderFontGrid(data.fonts);
            state.fontsLoaded = true;
        }
    } catch (error) {
        console.error('Failed to load fonts:', error);
        renderFontGridFallback();
    }
}

function renderFontGrid(fonts) {
    const grid = document.getElementById('font-grid');
    grid.innerHTML = '';
    
    // Font preview texts
    const previews = {
        'cursive': 'Hello World',
        'casual': 'Quick notes',
        'natural': 'My writing',
        'elegant': 'Beautiful script',
        'bold': 'Strong words',
        'calligraphy': 'Fine writing',
        'smooth': 'Smooth flow',
        'comic': 'Fun style',
        'light': 'Light touch',
        'bubbly': 'So cute!',
        'marker': 'Bold idea',
        'print': 'Clean print',
        'romantic': 'With love',
        'rough': 'Rough draft',
        'retro': 'Old style',
        'technical': 'Technical',
        'dreamy': 'Dreams...'
    };
    
    fonts.forEach(font => {
        const card = document.createElement('div');
        card.className = `font-card ${font.key === state.selectedFont ? 'selected' : ''}`;
        card.onclick = () => selectFont(card, font.key);
        
        const preview = previews[font.style] || 'Handwriting';
        const name = font.display_name.split(' ').slice(1).join(' ').replace(/\(.*?\)/, '').trim();
        
        card.innerHTML = `
            <div class="font-card-name">${font.display_name.split('(')[0].trim()}</div>
            <div class="font-card-preview">${preview}</div>
            <div class="font-card-style">${font.description}</div>
            ${!font.available ? '<div class="font-downloading"><i class="fas fa-download"></i> Downloading...</div>' : ''}
        `;
        
        grid.appendChild(card);
    });
}

function renderFontGridFallback() {
    const grid = document.getElementById('font-grid');
    const defaultFonts = [
        { key: 'HomemadeApple', name: '✍️ Homemade Apple', preview: 'Classic cursive' },
        { key: 'Kalam', name: '🖊️ Kalam', preview: 'Natural pen' },
        { key: 'Caveat', name: '📝 Caveat', preview: 'Casual writing' },
        { key: 'DancingScript', name: '💫 Dancing Script', preview: 'Elegant script' },
        { key: 'Pacifico', name: '🌊 Pacifico', preview: 'Bold casual' },
        { key: 'GloriaHallelujah', name: '✨ Gloria', preview: 'Comic style' },
        { key: 'Patrick_Hand', name: '📋 Patrick Hand', preview: 'Neat print' },
        { key: 'Indie_Flower', name: '🌸 Indie Flower', preview: 'Bubbly cute' },
    ];
    
    grid.innerHTML = defaultFonts.map(f => `
        <div class="font-card ${f.key === state.selectedFont ? 'selected' : ''}" 
             onclick="selectFont(this, '${f.key}')">
            <div class="font-card-name">${f.name}</div>
            <div class="font-card-preview">${f.preview}</div>
        </div>
    `).join('');
}

function selectFont(card, fontKey) {
    document.querySelectorAll('.font-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    state.selectedFont = fontKey;
    showToast(`Font selected: ${fontKey.replace(/_/g, ' ')}`, 'success');
}

// ===== TAB SWITCHING =====
function switchTab(tabId) {
    state.currentTab = tabId;
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabId);
    });
}

// ===== FILE HANDLING =====
function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('upload-zone').classList.add('drag-over');
}

function handleDragLeave(e) {
    document.getElementById('upload-zone').classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('upload-zone').classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(input) {
    if (input.files && input.files[0]) {
        processFile(input.files[0]);
    }
}

function processFile(file) {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    const allowedExts = ['.pdf', '.jpg', '.jpeg', '.png'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExts.includes(ext)) {
        showToast('Unsupported file type. Please upload PDF, JPG, or PNG', 'error');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
        showToast('File too large. Maximum size is 50MB', 'error');
        return;
    }
    
    state.selectedFile = file;
    
    // Update UI
    document.getElementById('file-preview').style.display = 'block';
    document.getElementById('extract-btn').style.display = 'block';
    document.getElementById('upload-zone').style.display = 'none';
    
    const icon = document.getElementById('file-type-icon');
    icon.className = ext === '.pdf' ? 'fas fa-file-pdf' : 'fas fa-file-image';
    icon.style.color = ext === '.pdf' ? '#ef4444' : '#3b82f6';
    
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    
    // Show layout option for PDFs
    if (ext === '.pdf') {
        document.getElementById('layout-option').style.display = 'block';
    }
    
    showToast(`File ready: ${file.name}`, 'success');
}

function removeFile() {
    state.selectedFile = null;
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('extract-btn').style.display = 'none';
    document.getElementById('upload-zone').style.display = 'block';
    document.getElementById('file-input').value = '';
    document.getElementById('layout-option').style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ===== TEXT EXTRACTION =====
async function extractText() {
    if (!state.selectedFile) {
        showToast('Please select a file first', 'warning');
        return;
    }
    
    showOverlay('Extracting text from file...');
    
    try {
        const formData = new FormData();
        formData.append('file', state.selectedFile);
        formData.append('input_type', 'file');
        
        const response = await fetch('/api/extract', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Extraction failed');
        }
        
        // Store extracted data
        state.extractedPages = data.pages || [data.text];
        state.layoutData = data.layout_data || null;
        
        // Show extracted text
        document.getElementById('extracted-text').value = data.text;
        document.getElementById('extracted-card').style.display = 'block';
        document.getElementById('step-2').style.display = 'block';
        document.getElementById('page-count-badge').textContent = `${data.page_count} page${data.page_count > 1 ? 's' : ''}`;
        
        // Update step indicator
        updateStepIndicator(2);
        
        // Scroll to settings
        document.getElementById('step-2').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        showToast(`Successfully extracted ${data.page_count} page(s)`, 'success');
        
    } catch (error) {
        console.error('Extraction error:', error);
        showToast(`Extraction failed: ${error.message}`, 'error');
    } finally {
        hideOverlay();
    }
}

function useDirectText() {
    const text = document.getElementById('direct-text').value.trim();
    
    if (!text) {
        showToast('Please enter some text first', 'warning');
        return;
    }
    
    state.extractedPages = [text];
    state.layoutData = null;
    
    document.getElementById('extracted-text').value = text;
    document.getElementById('extracted-card').style.display = 'block';
    document.getElementById('step-2').style.display = 'block';
    document.getElementById('page-count-badge').textContent = '1 page';
    
    updateStepIndicator(2);
    document.getElementById('step-2').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    showToast('Text ready for conversion!', 'success');
}

// ===== SETTINGS =====
function selectPaper(el) {
    document.querySelectorAll('.paper-option').forEach(opt => opt.classList.remove('active'));
    el.classList.add('active');
    state.selectedPaper = el.dataset.value;
}

function selectColor(el) {
    document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('active'));
    el.classList.add('active');
    state.selectedColor = el.dataset.value;
}

function selectFormat(el) {
    document.querySelectorAll('.format-option').forEach(opt => opt.classList.remove('selected'));
    el.classList.add('selected');
    state.selectedFormat = el.dataset.value;
    const radio = el.querySelector('input[type="radio"]');
    if (radio) radio.checked = true;
}

function setupFormatOptions() {
    document.querySelectorAll('.format-option').forEach(option => {
        option.addEventListener('click', function() {
            selectFormat(this);
        });
    });
}

function updateSlider(sliderId, displayId, unit) {
    const slider = document.getElementById(sliderId);
    const display = document.getElementById(displayId);
    display.textContent = parseFloat(slider.value).toFixed(slider.step.includes('.') ? 1 : 0);
}

// ===== CONVERSION =====
async function convertToHandwriting() {
    const extractedText = document.getElementById('extracted-text').value.trim();
    
    if (!extractedText) {
        showToast('No text to convert. Please extract or enter text first.', 'warning');
        return;
    }
    
    if (state.isConverting) return;
    state.isConverting = true;
    
    // Show loading in preview
    document.getElementById('empty-preview').style.display = 'none';
    document.getElementById('preview-container').style.display = 'none';
    document.getElementById('preview-loading').style.display = 'flex';
    document.getElementById('download-card').style.display = 'none';
    
    // Animate loading
    animateLoading();
    
    try {
        // Prepare pages
        let pages = state.extractedPages.length > 0 ? [...state.extractedPages] : [extractedText];
        
        // Update with any edits made to extracted text
        if (pages.length === 1 || state.extractedPages.length <= 1) {
            pages = [extractedText];
        }
        
        // Build settings
        const settings = {
            pages: pages,
            text: extractedText,
            font_name: state.selectedFont,
            font_size: parseInt(document.getElementById('font-size').value),
            line_spacing: parseFloat(document.getElementById('line-spacing').value),
            ink_color: state.selectedColor,
            margin: parseInt(document.getElementById('margin').value),
            paper_style: state.selectedPaper,
            output_format: state.selectedFormat,
            page_width: 794,
            page_height: 1123,
        };
        
        // Add layout data if available and requested
        const preserveLayout = document.getElementById('preserve-layout');
        if (preserveLayout && preserveLayout.checked && state.layoutData) {
            settings.layout_data = state.layoutData;
            settings.preserve_layout = true;
        }
        
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Conversion failed');
        }
        
        // Store session info
        state.sessionId = data.session_id;
        state.totalPages = data.page_count || 1;
        state.currentPage = 0;
        state.jpgUrls = data.jpg_urls || [];
        
        // Show preview
        await showPreview(data);
        
        // Show download options
        showDownloadOptions(data);
        
        // Update step indicator
        updateStepIndicator(3);
        
        showToast('✅ Handwriting generated successfully!', 'success');
        
    } catch (error) {
        console.error('Conversion error:', error);
        showToast(`Conversion failed: ${error.message}`, 'error');
        
        // Reset preview
        document.getElementById('preview-loading').style.display = 'none';
        document.getElementById('empty-preview').style.display = 'block';
    } finally {
        state.isConverting = false;
        stopLoadingAnimation();
    }
}

let loadingInterval = null;

function animateLoading() {
    const texts = [
        'Loading handwriting fonts...',
        'Drawing your text...',
        'Adding paper texture...',
        'Applying ink effects...',
        'Generating PDF...',
        'Almost done...'
    ];
    let i = 0;
    document.getElementById('loading-text').textContent = texts[0];
    document.getElementById('loading-detail').textContent = 'Please wait...';
    
    loadingInterval = setInterval(() => {
        i = (i + 1) % texts.length;
        document.getElementById('loading-text').textContent = texts[i];
    }, 1500);
}

function stopLoadingAnimation() {
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
    document.getElementById('preview-loading').style.display = 'none';
}

async function showPreview(data) {
    const previewImg = document.getElementById('preview-image');
    const previewContainer = document.getElementById('preview-container');
    
    let previewUrl = data.preview_url;
    if (!previewUrl && data.pdf_url) {
        previewUrl = `/api/preview/${data.session_id}`;
    }
    
    if (previewUrl) {
        return new Promise((resolve, reject) => {
            previewImg.onload = () => {
                previewContainer.style.display = 'block';
                document.getElementById('preview-loading').style.display = 'none';
                
                // Setup pagination if multiple pages
                if (state.jpgUrls.length > 1) {
                    document.getElementById('preview-controls').style.display = 'flex';
                    updatePageIndicator();
                }
                
                resolve();
            };
            previewImg.onerror = () => {
                previewContainer.style.display = 'none';
                document.getElementById('preview-loading').style.display = 'none';
                document.getElementById('empty-preview').style.display = 'block';
                document.getElementById('empty-preview').innerHTML = `
                    <div class="empty-icon"><i class="fas fa-check-circle" style="color: var(--success)"></i></div>
                    <h3>Handwriting generated!</h3>
                    <p>Preview not available, but your download is ready below.</p>
                `;
                resolve();
            };
            previewImg.src = previewUrl + '?t=' + Date.now();
        });
    } else {
        document.getElementById('preview-loading').style.display = 'none';
        previewContainer.style.display = 'none';
    }
}

function showDownloadOptions(data) {
    const downloadCard = document.getElementById('download-card');
    const downloadButtons = document.getElementById('download-buttons');
    
    downloadCard.style.display = 'block';
    downloadButtons.innerHTML = '';
    
    // Update stats
    document.getElementById('dl-pages').textContent = state.totalPages;
    document.getElementById('dl-format').textContent = data.output_format.toUpperCase();
    
    // PDF Download Button
    if (data.pdf_url) {
        const pdfBtn = document.createElement('a');
        pdfBtn.href = data.pdf_url;
        pdfBtn.download = 'handwritten_notes.pdf';
        pdfBtn.className = 'btn btn-download-pdf btn-full';
        pdfBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Download PDF (All Pages)';
        downloadButtons.appendChild(pdfBtn);
    }
    
    // JPG Download Buttons
    if (data.jpg_urls && data.jpg_urls.length > 0) {
        if (data.jpg_urls.length === 1) {
            const jpgBtn = document.createElement('a');
            jpgBtn.href = data.jpg_urls[0];
            jpgBtn.download = 'handwritten_page_1.jpg';
            jpgBtn.className = 'btn btn-download-jpg btn-full';
            jpgBtn.innerHTML = '<i class="fas fa-file-image"></i> Download JPG Image';
            downloadButtons.appendChild(jpgBtn);
        } else {
            // Individual page downloads + ZIP
            data.jpg_urls.forEach((url, i) => {
                const btn = document.createElement('a');
                btn.href = url;
                btn.download = `handwritten_page_${i + 1}.jpg`;
                btn.className = 'btn btn-download-jpg btn-full';
                btn.innerHTML = `<i class="fas fa-file-image"></i> Download Page ${i + 1} (JPG)`;
                downloadButtons.appendChild(btn);
            });
            
            // ZIP download
            const zipBtn = document.createElement('a');
            zipBtn.href = `/api/download/${data.session_id}/all`;
            zipBtn.download = 'handwritten_notes.zip';
            zipBtn.className = 'btn btn-download-zip btn-full';
            zipBtn.innerHTML = '<i class="fas fa-file-archive"></i> Download All Pages (ZIP)';
            downloadButtons.appendChild(zipBtn);
        }
    }
    
    // Scroll to download
    downloadCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ===== PAGE NAVIGATION =====
function prevPage() {
    if (state.currentPage > 0) {
        state.currentPage--;
        updatePagePreview();
    }
}

function nextPage() {
    if (state.currentPage < state.jpgUrls.length - 1) {
        state.currentPage++;
        updatePagePreview();
    }
}

function updatePagePreview() {
    if (state.jpgUrls.length > 0) {
        const url = state.jpgUrls[state.currentPage];
        document.getElementById('preview-image').src = url + '?t=' + Date.now();
        updatePageIndicator();
    }
}

function updatePageIndicator() {
    document.getElementById('page-indicator').textContent = 
        `Page ${state.currentPage + 1} / ${state.jpgUrls.length}`;
    document.getElementById('prev-page-btn').disabled = state.currentPage === 0;
    document.getElementById('next-page-btn').disabled = 
        state.currentPage === state.jpgUrls.length - 1;
}

// ===== STEP INDICATOR =====
function updateStepIndicator(step) {
    for (let i = 1; i <= 3; i++) {
        const el = document.getElementById(`step-indicator-${i}`);
        if (!el) continue;
        
        el.classList.remove('active', 'completed');
        if (i < step) {
            el.classList.add('completed');
            el.querySelector('.step-circle').innerHTML = '<i class="fas fa-check"></i>';
        } else if (i === step) {
            el.classList.add('active');
        }
    }
}

// ===== CHAR COUNTER =====
function setupCharCounter() {
    const textarea = document.getElementById('direct-text');
    if (textarea) {
        textarea.addEventListener('input', () => {
            const count = textarea.value.length;
            document.getElementById('char-count').textContent = 
                `${count.toLocaleString()} character${count !== 1 ? 's' : ''}`;
        });
    }
}

function clearText() {
    document.getElementById('direct-text').value = '';
    document.getElementById('char-count').textContent = '0 characters';
}

// ===== RESET =====
function resetAll() {
    state.selectedFile = null;
    state.extractedPages = [];
    state.layoutData = null;
    state.sessionId = null;
    state.currentPage = 0;
    state.totalPages = 0;
    state.jpgUrls = [];
    
    // Reset UI
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('extract-btn').style.display = 'none';
    document.getElementById('upload-zone').style.display = 'block';
    document.getElementById('file-input').value = '';
    document.getElementById('extracted-card').style.display = 'none';
    document.getElementById('step-2').style.display = 'none';
    document.getElementById('download-card').style.display = 'none';
    document.getElementById('preview-container').style.display = 'none';
    document.getElementById('empty-preview').style.display = 'block';
    document.getElementById('preview-controls').style.display = 'none';
    document.getElementById('direct-text').value = '';
    document.getElementById('char-count').textContent = '0 characters';
    document.getElementById('layout-option').style.display = 'none';
    
    // Reset step indicator
    for (let i = 1; i <= 3; i++) {
        const el = document.getElementById(`step-indicator-${i}`);
        if (!el) continue;
        el.classList.remove('active', 'completed');
        if (i === 1) el.classList.add('active');
        el.querySelector('.step-circle').innerHTML = i;
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    showToast('Ready for a new conversion!', 'success');
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ===== OVERLAY =====
function showOverlay(text = 'Processing...') {
    document.getElementById('overlay-text').textContent = text;
    document.getElementById('overlay').style.display = 'flex';
}

function hideOverlay() {
    document.getElementById('overlay').style.display = 'none';
}

// ===== INFO =====
function showInfo() {
    showToast('PDF to Handwriting Converter - Built with Python Flask, PIL, PyMuPDF & ReportLab', 'info');
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') hideOverlay();
    
    // Arrow keys for page navigation when preview is visible
    if (document.getElementById('preview-container').style.display !== 'none') {
        if (e.key === 'ArrowLeft') prevPage();
        if (e.key === 'ArrowRight') nextPage();
    }
});
