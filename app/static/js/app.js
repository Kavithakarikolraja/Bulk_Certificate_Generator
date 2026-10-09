const API_BASE = '/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    initAppTheme();
    initTabs();
    initThemePicker();
    initDropzone();
    initForms();
    loadJobHistory();
});

// App Light/Dark Theme Switcher
function initAppTheme() {
    const savedTheme = localStorage.getItem('app-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggleBtnText(savedTheme);
}

function toggleAppTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('app-theme', newTheme);
    updateThemeToggleBtnText(newTheme);
}

function updateThemeToggleBtnText(theme) {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        btn.innerHTML = theme === 'dark' ? '🌙 Dark Mode' : '☀️ Light Mode';
    }
}

// Tab Navigation
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            document.getElementById(targetId).classList.add('active');

            if (targetId === 'tab-history') {
                loadJobHistory();
            }
        });
    });
}

// Theme Picker in Form
let selectedTheme = 'gold';
function initThemePicker() {
    const cards = document.querySelectorAll('.theme-card');
    cards.forEach(card => {
        card.addEventListener('click', () => {
            cards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedTheme = card.getAttribute('data-theme');
            document.getElementById('template_theme_input').value = selectedTheme;
        });
    });
}

// Drag and Drop Zone
let selectedCsvFile = null;
function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    const csvInput = document.getElementById('csv_file_input');
    const dropzoneText = document.getElementById('dropzone-filename');

    if (!dropzone) return;

    dropzone.addEventListener('click', () => csvInput.click());

    csvInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedCsvFile = e.target.files[0];
            dropzoneText.textContent = `Selected: ${selectedCsvFile.name} (${(selectedCsvFile.size / 1024).toFixed(1)} KB)`;
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files.length > 0) {
            selectedCsvFile = dt.files[0];
            dropzoneText.textContent = `Selected: ${selectedCsvFile.name} (${(selectedCsvFile.size / 1024).toFixed(1)} KB)`;
        }
    });
}

// Forms Initialization
function initForms() {
    const generateForm = document.getElementById('generate-form');
    if (generateForm) {
        generateForm.addEventListener('submit', handleGenerateSubmit);
    }

    const verifyForm = document.getElementById('verify-form');
    if (verifyForm) {
        verifyForm.addEventListener('submit', handleVerifySubmit);
    }
}

// Toggle Input Mode (CSV vs JSON)
let inputMode = 'json';
function setInputMode(mode) {
    inputMode = mode;
    document.querySelectorAll('.toggle-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(`toggle-${mode}`).classList.add('active');

    if (mode === 'json') {
        document.getElementById('json-input-group').style.display = 'block';
        document.getElementById('csv-input-group').style.display = 'none';
    } else {
        document.getElementById('json-input-group').style.display = 'none';
        document.getElementById('csv-input-group').style.display = 'block';
    }
}

// Handle Bulk Generation Submission
async function handleGenerateSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('title').value;
    const issuer_name = document.getElementById('issuer_name').value;
    const issue_date = document.getElementById('issue_date').value;
    const theme = selectedTheme;

    let res;
    if (inputMode === 'json') {
        const jsonText = document.getElementById('json_recipients').value;
        let recipients = [];
        try {
            recipients = JSON.parse(jsonText);
        } catch (err) {
            alert('Invalid JSON format for recipients list.');
            return;
        }

        res = await fetch(`${API_BASE}/jobs/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                issuer_name,
                issue_date,
                template_theme: theme,
                recipients
            })
        });
    } else {
        if (!selectedCsvFile) {
            alert('Please select or drop a CSV file.');
            return;
        }
        const formData = new FormData();
        formData.append('file', selectedCsvFile);
        formData.append('title', title);
        formData.append('issuer_name', issuer_name);
        formData.append('issue_date', issue_date);
        formData.append('template_theme', theme);

        res = await fetch(`${API_BASE}/jobs/upload-csv`, {
            method: 'POST',
            body: formData
        });
    }

    const data = await res.json();
    if (res.ok) {
        showProgressModal(data.id);
    } else {
        alert(`Error creating job: ${data.detail || 'Unknown error'}`);
    }
}

// Poll Progress Modal
let pollInterval = null;
function showProgressModal(jobId) {
    const modal = document.getElementById('progress-modal');
    modal.classList.add('active');

    document.getElementById('modal-job-id').textContent = jobId.substring(0, 13) + '...';
    
    pollInterval = setInterval(async () => {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`);
        if (!res.ok) return;

        const job = await res.json();
        const p = job.progress;

        document.getElementById('progress-percent-text').textContent = `${p.percentage}%`;
        document.getElementById('progress-bar-inner').style.width = `${p.percentage}%`;
        document.getElementById('stat-total').textContent = p.total;
        document.getElementById('stat-processed').textContent = p.processed;
        document.getElementById('stat-success').textContent = p.successful;
        document.getElementById('stat-failed').textContent = p.failed;
        document.getElementById('modal-status-badge').textContent = job.status;

        if (job.status === 'COMPLETED' || job.status === 'PARTIALLY_FAILED' || job.status === 'FAILED') {
            clearInterval(pollInterval);
            document.getElementById('modal-actions').style.display = 'block';
            if (job.download_zip_url) {
                document.getElementById('btn-download-zip').href = job.download_zip_url;
                document.getElementById('btn-download-zip').style.display = 'inline-flex';
            }
        }
    }, 800);
}

function closeModal() {
    if (pollInterval) clearInterval(pollInterval);
    document.getElementById('progress-modal').classList.remove('active');
    loadJobHistory();
}

// Load Job History & Update Banner Stats
async function loadJobHistory() {
    const tbody = document.getElementById('job-history-tbody');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/jobs?limit=50`);
        const data = await res.json();
        
        // Update Banner Metrics
        document.getElementById('banner-total-jobs').textContent = data.total_count || 0;
        const totalCertsGenerated = data.jobs.reduce((sum, j) => sum + (j.progress.successful || 0), 0);
        document.getElementById('banner-total-certs').textContent = totalCertsGenerated;

        tbody.innerHTML = '';
        if (data.jobs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding:30px;">No generation jobs submitted yet. Use the "New Batch Job" tab to create one!</td></tr>`;
            return;
        }

        data.jobs.forEach(job => {
            const tr = document.createElement('tr');
            const created = new Date(job.created_at).toLocaleString();
            const statusClass = `status-${job.status.toLowerCase().replace('_', '-')}`;
            
            tr.innerHTML = `
                <td><code>${job.id.substring(0, 8)}...</code></td>
                <td><strong>${job.title}</strong><br/><small style="color:var(--text-muted)">${job.issuer_name}</small></td>
                <td><span class="status-pill ${statusClass}">${job.status}</span></td>
                <td>${job.progress.processed} / ${job.progress.total} (${job.progress.percentage}%)</td>
                <td><span style="color:var(--accent-emerald)">✓ ${job.progress.successful}</span> | <span style="color:var(--accent-crimson)">✗ ${job.progress.failed}</span></td>
                <td><small style="color:var(--text-muted)">${created}</small></td>
                <td>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="viewJobDetails('${job.id}')">Details</button>
                        ${job.download_zip_url ? `<a href="${job.download_zip_url}" class="btn btn-emerald" style="padding: 6px 12px; font-size: 12px;">ZIP</a>` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

// View Job Recipients Details
async function viewJobDetails(jobId) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) return;
    const job = await res.json();

    const detailModal = document.getElementById('details-modal');
    document.getElementById('details-job-title').textContent = `${job.title} (Job ID: ${job.id.substring(0, 8)})`;
    
    const tbody = document.getElementById('details-recipients-tbody');
    tbody.innerHTML = '';

    job.recipients.forEach(r => {
        const tr = document.createElement('tr');
        const statusClass = `status-${r.status.toLowerCase()}`;
        
        tr.innerHTML = `
            <td><strong>${r.name || '<em style="color:var(--accent-crimson)">[Blank Name]</em>'}</strong></td>
            <td>${r.email || '-'}</td>
            <td><span class="status-pill ${statusClass}">${r.status}</span></td>
            <td>${r.error_message ? `<span style="color:var(--accent-crimson); font-size:13px;">⚠️ ${r.error_message}</span>` : '<span style="color:var(--accent-emerald)">✓ Validated</span>'}</td>
            <td>
                ${r.certificate_id ? `<a href="${API_BASE}/certificates/${r.certificate_id}/download" target="_blank" class="btn btn-primary" style="padding:5px 12px; font-size:12px;">Download PDF</a>` : '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });

    detailModal.classList.add('active');
}

function closeDetailsModal() {
    document.getElementById('details-modal').classList.remove('active');
}

// Certificate Verification Handler
async function handleVerifySubmit(e) {
    e.preventDefault();
    const code = document.getElementById('verify_code_input').value.trim();
    if (!code) return;

    const res = await fetch(`${API_BASE}/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();

    const resultBox = document.getElementById('verify-result-box');
    resultBox.style.display = 'block';

    if (data.is_valid) {
        resultBox.className = 'glass-panel';
        resultBox.style.borderColor = 'var(--accent-emerald)';
        resultBox.innerHTML = `
            <div style="display:flex; align-items:center; gap:18px; margin-bottom:20px;">
                <div style="width:54px; height:54px; background:rgba(16, 185, 129, 0.2); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px; color:var(--accent-emerald); border:1px solid rgba(16, 185, 129, 0.4);">✓</div>
                <div>
                    <h3 style="color:var(--accent-emerald); font-size:20px;">AUTHENTIC CERTIFICATE VERIFIED</h3>
                    <p style="color:var(--text-secondary)">Official Record ID: <code>${data.certificate_code}</code></p>
                </div>
            </div>
            <div class="form-grid" style="margin-bottom:20px;">
                <div><label>Recipient Name</label><p style="font-size:16px; font-weight:700;">${data.recipient_name}</p></div>
                <div><label>Course / Program</label><p style="font-size:16px; font-weight:700;">${data.course_title}</p></div>
                <div><label>Issuing Institution</label><p style="font-size:16px; font-weight:700;">${data.issuer_name}</p></div>
                <div><label>Date of Issuance</label><p style="font-size:16px; font-weight:700;">${data.issue_date}</p></div>
            </div>
            <a href="${data.download_url}" target="_blank" class="btn btn-emerald">Download Verified PDF Certificate</a>
        `;
    } else {
        resultBox.className = 'glass-panel';
        resultBox.style.borderColor = 'var(--accent-crimson)';
        resultBox.innerHTML = `
            <div style="display:flex; align-items:center; gap:18px;">
                <div style="width:54px; height:54px; background:rgba(239, 68, 68, 0.2); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px; color:var(--accent-crimson); border:1px solid rgba(239, 68, 68, 0.4);">✕</div>
                <div>
                    <h3 style="color:var(--accent-crimson); font-size:20px;">VERIFICATION FAILED</h3>
                    <p style="color:var(--text-secondary)">${data.message}</p>
                </div>
            </div>
        `;
    }
}

// Canva Studio Theme Selection
let studioTheme = 'gold';
function selectStudioTheme(theme, element) {
    studioTheme = theme;
    const parentGrid = element.parentElement;
    parentGrid.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('studio_theme_input').value = theme;
}

// Render Studio Preview Inline Image (ONLY on 'See Certificate Design' button click!)
function renderStudioPreview() {
    const placeholder = document.getElementById('studio-placeholder-text');
    const imgEl = document.getElementById('studio-preview-img');
    if (!imgEl) return;

    const theme = studioTheme;
    const heading = encodeURIComponent(document.getElementById('studio_heading')?.value || 'CERTIFICATE OF ACHIEVEMENT');
    const recipient = encodeURIComponent(document.getElementById('studio_name')?.value || 'Jane Doe');
    const course = encodeURIComponent(document.getElementById('studio_course')?.value || 'Executive AI & Cloud Architecture');
    const issuer = encodeURIComponent(document.getElementById('studio_issuer')?.value || 'Global Tech Institute');

    // High resolution PNG preview image URL
    const previewUrl = `${API_BASE}/templates/preview-image?theme=${theme}&recipient_name=${recipient}&course_title=${course}&issuer_name=${issuer}&cert_heading=${heading}&t=${Date.now()}`;

    placeholder.style.display = 'none';
    imgEl.style.display = 'block';
    imgEl.src = previewUrl;
}


// Download Sample CSV helper
function downloadSampleCsv() {
    const csvContent = "data:text/csv;charset=utf-8,name,email\nJohn Doe,john@example.com\nAlice Smith,alice@domain.org\nBob Johnson,bob@company.com\nInvalid Test Recipient,\n";
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "sample_recipients.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
