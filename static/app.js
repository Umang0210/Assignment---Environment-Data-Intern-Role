document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const dropzoneContent = document.getElementById('dropzone-content');
  const filePreview = document.getElementById('file-preview');
  const selectedFilename = document.getElementById('selected-filename');
  const selectedFilesize = document.getElementById('selected-filesize');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const startRedactBtn = document.getElementById('start-redact-btn');
  
  const confidenceRange = document.getElementById('confidence-range');
  const confidenceDisplay = document.getElementById('confidence-display');
  const resetCacheCheck = document.getElementById('reset-cache-check');

  const progressSection = document.getElementById('progress-section');
  const progressStatusText = document.getElementById('progress-status-text');
  const progressSubText = document.getElementById('progress-sub-text');
  
  const resultsSection = document.getElementById('results-section');
  
  // Downloads
  const downloadRedactedBtn = document.getElementById('download-redacted-btn');
  const downloadOriginalBtn = document.getElementById('download-original-btn');
  const downloadMappingBtn = document.getElementById('download-mapping-btn');
  const downloadReportBtn = document.getElementById('download-report-btn');

  // Metrics
  const metricTotalPii = document.getElementById('metric-total-pii');
  const metricUniquePii = document.getElementById('metric-unique-pii');
  const metricHighConf = document.getElementById('metric-high-conf');
  const metricDuration = document.getElementById('metric-duration');
  const typeBarsContainer = document.getElementById('type-bars-container');
  const methodBarsContainer = document.getElementById('method-bars-container');
  const confHighVal = document.getElementById('conf-high-val');
  const confMedVal = document.getElementById('conf-med-val');
  const confLowVal = document.getElementById('conf-low-val');

  // Comparison & Tables
  const comparisonViewContainer = document.getElementById('comparison-view-container');
  const originalTextDisplay = document.getElementById('original-text-display');
  const redactedTextDisplay = document.getElementById('redacted-text-display');
  const origCharCount = document.getElementById('orig-char-count');
  const redactedCharCount = document.getElementById('redacted-char-count');
  const tabSplitBtn = document.getElementById('tab-split-btn');
  const tabRedactedBtn = document.getElementById('tab-redacted-btn');
  const tabOriginalBtn = document.getElementById('tab-original-btn');

  const mappingTableBody = document.getElementById('mapping-table-body');
  const tableSearchInput = document.getElementById('table-search-input');

  let selectedFile = null;
  let currentMappingData = {};

  // Event Listeners for Dropzone & File Input
  dropzone.addEventListener('click', (e) => {
    if (!filePreview.classList.contains('hidden') && e.target.closest('#remove-file-btn')) {
      return;
    }
    if (filePreview.classList.contains('hidden')) {
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-over');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-over');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files[0]) {
      if (files[0].name.toLowerCase().endsWith('.docx')) {
        handleFileSelected(files[0]);
      } else {
        alert('Please select a valid Word document (.docx file).');
      }
    }
  });

  removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    filePreview.classList.add('hidden');
    dropzoneContent.classList.remove('hidden');
    startRedactBtn.disabled = true;
  });

  function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith('.docx')) {
      alert('Only .docx files are supported.');
      return;
    }
    selectedFile = file;
    selectedFilename.textContent = file.name;
    selectedFilesize.textContent = formatBytes(file.size);
    
    dropzoneContent.classList.add('hidden');
    filePreview.classList.remove('hidden');
    startRedactBtn.disabled = false;
  }

  // Confidence Slider Sync
  confidenceRange.addEventListener('input', (e) => {
    confidenceDisplay.textContent = parseFloat(e.target.value).toFixed(2);
  });

  // Start Redaction Process
  startRedactBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Show Loader
    progressSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    startRedactBtn.disabled = true;

    progressStatusText.textContent = "Analyzing Document & Extracting Text...";
    progressSubText.textContent = "Parsing document elements and initializing PII detectors";

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('confidence', confidenceRange.value);
    formData.append('reset_cache', resetCacheCheck.checked ? 'true' : 'false');

    try {
      setTimeout(() => {
        progressStatusText.textContent = "Executing spaCy NER & Regex Engine...";
        progressSubText.textContent = "Detecting names, emails, phones, SSNs, credit cards, and addresses";
      }, 800);

      const response = await fetch('/api/redact', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to redact document.');
      }

      progressStatusText.textContent = "Generating Redacted Copy & Metrics...";
      progressSubText.textContent = "Replacing PII with synthetic data and creating evaluation reports";

      const data = await response.json();

      setTimeout(() => {
        progressSection.classList.add('hidden');
        renderResults(data);
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        startRedactBtn.disabled = false;
      }, 500);

    } catch (error) {
      alert(`Error: ${error.message}`);
      progressSection.classList.add('hidden');
      startRedactBtn.disabled = false;
    }
  });

  // Render Results Dashboard
  function renderResults(data) {
    currentMappingData = data.mapping || {};

    // Setup Download Links
    downloadRedactedBtn.href = data.downloads.redacted;
    downloadOriginalBtn.href = data.downloads.original;
    downloadMappingBtn.href = data.downloads.mapping;
    downloadReportBtn.href = data.downloads.report;

    // Overview Stats
    const stats = data.stats || {};
    metricTotalPii.textContent = stats.total_pii_detected || 0;
    metricUniquePii.textContent = stats.total_unique_pii || 0;
    metricHighConf.textContent = (stats.by_confidence && stats.by_confidence.high) || 0;
    metricDuration.textContent = `${data.file_info.processing_time_seconds}s`;

    // Render Entity Type Bars
    renderTypeBars(stats.by_type || {}, stats.total_pii_detected || 1);

    // Render Method Bars
    renderMethodBars(stats.by_method || {}, stats.total_pii_detected || 1);

    // Confidence Counts
    const byConf = stats.by_confidence || { high: 0, medium: 0, low: 0 };
    confHighVal.textContent = byConf.high;
    confMedVal.textContent = byConf.medium;
    confLowVal.textContent = byConf.low;

    // Render Text Comparison
    renderTextComparison(data.original_text, data.redacted_text, currentMappingData);

    // Render Mapping Table
    renderMappingTable(currentMappingData);
  }

  // Bar Charts Rendering Helpers
  function renderTypeBars(byType, total) {
    typeBarsContainer.innerHTML = '';
    const entries = Object.entries(byType).sort((a, b) => b[1] - a[1]);
    
    if (entries.length === 0) {
      typeBarsContainer.innerHTML = '<p class="text-dim">No PII entities detected.</p>';
      return;
    }

    entries.forEach(([type, count]) => {
      const pct = Math.round((count / total) * 100);
      const barRow = document.createElement('div');
      barRow.className = 'bar-row';
      barRow.innerHTML = `
        <div class="bar-label-group">
          <span style="text-transform: capitalize;">${type.replace('_', ' ')}</span>
          <span>${count} (${pct}%)</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%; background: var(--primary);"></div>
        </div>
      `;
      typeBarsContainer.appendChild(barRow);
    });
  }

  function renderMethodBars(byMethod, total) {
    methodBarsContainer.innerHTML = '';
    const entries = Object.entries(byMethod);

    if (entries.length === 0) {
      methodBarsContainer.innerHTML = '<p class="text-dim">No methods recorded.</p>';
      return;
    }

    entries.forEach(([method, count]) => {
      const pct = Math.round((count / total) * 100);
      const isNer = method.toLowerCase().includes('ner');
      const barColor = isNer ? 'var(--accent-purple)' : 'var(--accent-emerald)';
      
      const barRow = document.createElement('div');
      barRow.className = 'bar-row';
      barRow.innerHTML = `
        <div class="bar-label-group">
          <span>${method}</span>
          <span>${count} (${pct}%)</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%; background: ${barColor};"></div>
        </div>
      `;
      methodBarsContainer.appendChild(barRow);
    });
  }

  // Text Comparison Highlight Logic
  function renderTextComparison(originalText, redactedText, mapping) {
    origCharCount.textContent = `${originalText.length} chars`;
    redactedCharCount.textContent = `${redactedText.length} chars`;

    // Highlight Original Text
    let highlightedOrig = escapeHtml(originalText);
    // Highlight Redacted Text
    let highlightedRedacted = escapeHtml(redactedText);

    // Sort terms by length descending to prevent partial match overwrites
    const originalTerms = Object.keys(mapping).sort((a, b) => b.length - a.length);

    originalTerms.forEach(orig => {
      const fake = mapping[orig].fake_value;
      const origEsc = escapeHtml(orig);
      const fakeEsc = escapeHtml(fake);

      if (origEsc.trim().length > 0) {
        const origReg = new RegExp(escapeRegExp(origEsc), 'g');
        highlightedOrig = highlightedOrig.replace(origReg, `<mark class="original-mark" title="Original PII">${origEsc}</mark>`);
      }

      if (fakeEsc.trim().length > 0) {
        const fakeReg = new RegExp(escapeRegExp(fakeEsc), 'g');
        highlightedRedacted = highlightedRedacted.replace(fakeReg, `<mark class="redacted-mark" title="Redacted Fake Data">${fakeEsc}</mark>`);
      }
    });

    originalTextDisplay.innerHTML = highlightedOrig;
    redactedTextDisplay.innerHTML = highlightedRedacted;
  }

  // Tab View Switcher
  tabSplitBtn.addEventListener('click', () => {
    setActiveTab(tabSplitBtn, 'split-mode');
  });

  tabRedactedBtn.addEventListener('click', () => {
    setActiveTab(tabRedactedBtn, 'redacted-only-mode');
  });

  tabOriginalBtn.addEventListener('click', () => {
    setActiveTab(tabOriginalBtn, 'original-only-mode');
  });

  function setActiveTab(btn, modeClass) {
    [tabSplitBtn, tabRedactedBtn, tabOriginalBtn].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    comparisonViewContainer.className = `comparison-view ${modeClass}`;
  }

  // Render Mapping Table
  function renderMappingTable(mapping, filterQuery = '') {
    mappingTableBody.innerHTML = '';

    const entries = Object.entries(mapping);
    if (entries.length === 0) {
      mappingTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No PII mappings available</td></tr>';
      return;
    }

    let count = 0;
    entries.forEach(([orig, info]) => {
      const q = filterQuery.toLowerCase();
      if (q && !orig.toLowerCase().includes(q) && !info.fake_value.toLowerCase().includes(q) && !info.type.toLowerCase().includes(q)) {
        return;
      }

      count++;
      const tr = document.createElement('tr');

      const confLevel = info.confidence >= 0.85 ? 'high' : (info.confidence >= 0.70 ? 'medium' : 'low');
      const pillClass = getPillClass(info.type);

      tr.innerHTML = `
        <td style="color: var(--text-dim); font-family: var(--font-mono);">${count}</td>
        <td style="font-weight: 600; color: #fca5a5;">${escapeHtml(orig)}</td>
        <td style="font-weight: 600; color: #6ee7b7;">${escapeHtml(info.fake_value)}</td>
        <td><span class="type-pill ${pillClass}">${info.type}</span></td>
        <td><span class="method-tag">${info.method}</span></td>
        <td><span class="conf-badge ${confLevel}">${(info.confidence * 100).toFixed(0)}%</span></td>
      `;

      mappingTableBody.appendChild(tr);
    });

    if (count === 0) {
      mappingTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No matching PII entities found</td></tr>';
    }
  }

  tableSearchInput.addEventListener('input', (e) => {
    renderMappingTable(currentMappingData, e.target.value);
  });

  function getPillClass(type) {
    const known = ['name', 'email', 'phone', 'ssn', 'credit_card'];
    return known.includes(type) ? type : 'default-pill';
  }

  function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
});
