const API = '';  // same origin — Flask serves both frontend and API

let selectedTemplate = null;
let selectedStyle = null;
let uploadedFile = null;

// ── Init ────────────────────────────────────────────────────────────────────

async function init() {
  await Promise.all([loadStyles(), loadTemplates()]);
  setupUpload();
}

// ── Data loading ─────────────────────────────────────────────────────────────

async function loadStyles() {
  const res = await fetch(`${API}/styles`);
  const styles = await res.json();
  const container = document.getElementById('styleSelector');

  Object.entries(styles).forEach(([key, s], i) => {
    const el = document.createElement('div');
    el.className = 'style-option' + (i === 0 ? ' selected' : '');
    el.dataset.key = key;
    el.innerHTML = `
      <div class="style-dot"></div>
      <span class="style-name">${s.name}</span>
      <span class="style-trigger">${s.trigger_word}</span>
    `;
    el.addEventListener('click', () => selectStyle(key));
    container.appendChild(el);

    if (i === 0) selectedStyle = key;
  });
}

async function loadTemplates() {
  const res = await fetch(`${API}/templates`);
  const templates = await res.json();
  const grid = document.getElementById('templateGrid');

  const ICONS = ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'];
  let iconIndex = 0;

  Object.entries(templates).forEach(([key, t]) => {
    const card = document.createElement('div');
    card.className = 'template-card';
    card.dataset.key = key;

    const thumbHTML = t.preview_url
      ? `<img class="template-thumb" src="${t.preview_url}" alt="${t.name}">`
      : `<div class="template-thumb-placeholder">${ICONS[iconIndex % ICONS.length]}</div>`;

    card.innerHTML = `
      ${thumbHTML}
      <div class="template-info">
        <div class="template-name">${t.name}</div>
        <div class="template-mood">${t.mood || t.environment}</div>
      </div>
    `;
    card.addEventListener('click', () => selectTemplate(key, card));
    grid.appendChild(card);
    iconIndex++;
  });
}

function makePlaceholder(icon) {
  const div = document.createElement('div');
  div.className = 'template-thumb-placeholder';
  div.textContent = icon;
  return div;
}

// ── Selection ─────────────────────────────────────────────────────────────────

function selectStyle(key) {
  selectedStyle = key;
  document.querySelectorAll('.style-option').forEach(el => {
    el.classList.toggle('selected', el.dataset.key === key);
  });
  updateGenerateBtn();
}

function selectTemplate(key, card) {
  selectedTemplate = key;
  document.querySelectorAll('.template-card').forEach(el => el.classList.remove('selected'));
  card.classList.add('selected');
  updateGenerateBtn();
}

function updateGenerateBtn() {
  const btn = document.getElementById('generateBtn');
  btn.disabled = !(uploadedFile && selectedTemplate && selectedStyle);
}

// ── Upload ────────────────────────────────────────────────────────────────────

function setupUpload() {
  const area = document.getElementById('uploadArea');
  const input = document.getElementById('imageInput');
  const preview = document.getElementById('imagePreview');
  const placeholder = document.getElementById('uploadPlaceholder');

  area.addEventListener('click', () => input.click());

  area.addEventListener('dragover', e => {
    e.preventDefault();
    area.classList.add('drag-over');
  });
  area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
  area.addEventListener('drop', e => {
    e.preventDefault();
    area.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) setUploadedFile(file, preview, placeholder);
  });

  input.addEventListener('change', () => {
    if (input.files[0]) setUploadedFile(input.files[0], preview, placeholder);
  });
}

function setUploadedFile(file, preview, placeholder) {
  uploadedFile = file;
  const url = URL.createObjectURL(file);
  preview.src = url;
  preview.classList.remove('hidden');
  placeholder.classList.add('hidden');
  updateGenerateBtn();
}

// ── Generate ──────────────────────────────────────────────────────────────────

document.getElementById('generateBtn').addEventListener('click', async () => {
  const btn = document.getElementById('generateBtn');
  const label = document.getElementById('generateLabel');
  const spinner = document.getElementById('generateSpinner');
  const errorMsg = document.getElementById('errorMsg');
  const resultSection = document.getElementById('resultSection');

  // Reset
  errorMsg.classList.add('hidden');
  errorMsg.textContent = '';
  resultSection.classList.add('hidden');

  // Loading state
  btn.disabled = true;
  label.textContent = 'Generating…';
  spinner.classList.remove('hidden');

  try {
    const form = new FormData();
    form.append('image', uploadedFile);
    form.append('template_key', selectedTemplate);
    form.append('style_key', selectedStyle);

    const res = await fetch(`${API}/generate`, { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || `Server error ${res.status}`);
    }

    showResult(data);

  } catch (err) {
    errorMsg.textContent = err.message;
    errorMsg.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    label.textContent = 'Generate Portrait';
    spinner.classList.add('hidden');
    updateGenerateBtn();
  }
});

// ── Result display ────────────────────────────────────────────────────────────

function showResult(data) {
  const section = document.getElementById('resultSection');
  const img = document.getElementById('resultImage');

  const images = data.images || [];
  if (images.length === 0 || !images[0].key) {
    document.getElementById('errorMsg').textContent = 'No image URL in response.';
    document.getElementById('errorMsg').classList.remove('hidden');
    return;
  }

  img.src = `/r2-image?key=${encodeURIComponent(images[0].key)}`;
  document.getElementById('metaTemplate').textContent = data.template || selectedTemplate;
  document.getElementById('metaStyle').textContent = data.style || selectedStyle;
  document.getElementById('metaSeed').textContent = data.seed ?? '—';
  document.getElementById('metaPrompt').textContent = data.positive_prompt || '';

  section.classList.remove('hidden');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Start ─────────────────────────────────────────────────────────────────────
init();
