// Listings Manager Marine Proof Dashboard - Client-side JavaScript

let processingQueue = [];
let currentUploadMode = 'single';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    renderQueue();
    
    // Setup drag and drop for file input
    const uploadZone = document.querySelector('.upload-zone');
    if (uploadZone) {
        uploadZone.addEventListener('dragover', handleDragOver);
        uploadZone.addEventListener('dragleave', handleDragLeave);
        uploadZone.addEventListener('drop', handleDrop);
    }
});

// Update statistics display
function updateStats() {
    const total = processingQueue.length;
    const analyzed = processingQueue.filter(f => f.status === 'analyzed').length;
    const flagged = processingQueue.filter(f => f.needs_review).length;
    
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-analyzed').textContent = analyzed;
    document.getElementById('stat-flagged').textContent = flagged;
}

// Switch between upload modes
function showUploadMode(mode) {
    currentUploadMode = mode;
    
    const singleContainer = document.getElementById('upload-single');
    const folderContainer = document.getElementById('upload-folder');
    const btnSingle = document.getElementById('btn-single');
    const btnFolder = document.getElementById('btn-folder');
    
    if (mode === 'single') {
        singleContainer.style.display = 'block';
        folderContainer.style.display = 'none';
        btnSingle.classList.add('btn-success');
        btnSingle.classList.remove('btn-warning');
        btnFolder.classList.remove('btn-success');
        btnFolder.classList.add('btn-warning');
    } else {
        singleContainer.style.display = 'none';
        folderContainer.style.display = 'block';
        btnFolder.classList.add('btn-success');
        btnFolder.classList.remove('btn-warning');
        btnSingle.classList.remove('btn-success');
        btnSingle.classList.add('btn-warning');
    }
}

// Handle file selection via click
function handleFileSelect() {
    const input = document.getElementById('file-input');
    const files = Array.from(input.files);
    
    if (files.length === 0) return;
    
    for (const file of files) {
        uploadFile(file);
    }
    
    input.value = ''; // Clear selection so same file can be uploaded again
}

// Handle drag and drop events
function handleDragOver(e) {
    e.preventDefault();
    const uploadZone = document.querySelector('.upload-zone');
    if (uploadZone) uploadZone.classList.add('dragover');
}

function handleDragLeave(e) {
    const uploadZone = document.querySelector('.upload-zone');
    if (uploadZone) uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    const uploadZone = document.querySelector('.upload-zone');
    if (uploadZone) uploadZone.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
        if (file.type.startsWith('image/')) {
            uploadFile(file);
        }
    }
}

// Upload a single file to the API
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Show in queue immediately as pending
        const fileId = 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
        const newItem = {
            id: fileId,
            filename: file.name,
            status: 'pending',
            confidence: 0,
            analysis: null,
            needs_review: false,
            uploaded_at: new Date()
        };
        
        processingQueue.push(newItem);
        renderQueue();
        updateStats();
        
        // Upload to server
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        // Start analyzing immediately
        analyzeFile(fileId, file.name);
        
    } catch (error) {
        console.error('Upload error:', error);
        alert('Failed to upload ' + file.name + '. Please try again.');
    }
}

// Analyze a file using AI
async function analyzeFile(fileId, filename) {
    const item = processingQueue.find(i => i.id === fileId);
    if (!item) return;
    
    item.status = 'analyzing';
    renderQueue();
    
    try {
        const response = await fetch(`/api/analyze/${fileId}`);
        const data = await response.json();
        
        if (data.success) {
            item.analysis = data.result;
            item.confidence = data.confidence || 0.85;
            item.needs_review = data.needs_review || false;
            
            // Set status based on review flag
            item.status = item.needs_review ? 'flagged' : 'analyzed';
        } else {
            item.status = 'error';
            alert('Analysis failed for ' + filename);
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        item.status = 'error';
        alert('Analysis failed for ' + filename);
    }
    
    renderQueue();
    updateStats();
}

// Render the processing queue table
function renderQueue() {
    const tbody = document.getElementById('queue-body');
    
    if (processingQueue.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No files uploaded yet. Upload your first product above!</td></tr>';
        return;
    }
    
    // Show newest items first
    const reversedQueue = [...processingQueue].reverse();
    
    tbody.innerHTML = reversedQueue.map(item => {
        const statusClass = 'status-' + item.status;
        const statusLabel = getStatusLabel(item.status);
        
        let analysisHtml = '';
        if (item.analysis) {
            analysisHtml = `
                <div style="margin-bottom: 0.5rem;">
                    <strong>Title:</strong> ${item.analysis.title || 'N/A'}
                </div>
                <div style="font-size: 0.9rem; color: #16a34a;">
                    Price: $${typeof item.analysis.price === 'number' ? item.analysis.price.toFixed(2) : 'N/A'}
                </div>
            `;
        } else {
            analysisHtml = '<span class="status-badge status-pending">Waiting for AI...</span>';
        }
        
        let actionButtons = '';
        if (item.status === 'analyzed' || item.status === 'flagged') {
            actionButtons = `
                <button type="button" onclick="approveItem('${item.id}')" class="btn btn-success" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">✓ Post</button>
                <button type="button" onclick="rejectItem('${item.id}')" class="btn btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">✗ Skip</button>
            `;
        } else if (item.status === 'error') {
            actionButtons = '<button type="button" onclick="retryItem(${item.id})" class="btn btn-warning" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">↻ Retry</button>';
        }
        
        return `
            <tr>
                <td><div class="file-name">${item.filename}</div></td>
                <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                <td>${analysisHtml}</td>
                <td>${actionButtons}</td>
            </tr>
        `;
    }).join('');
}

// Get status label with emoji
function getStatusLabel(status) {
    const labels = {
        'pending': '📥 Pending',
        'analyzing': '🤖 Analyzing...',
        'analyzed': '✅ Done',
        'flagged': '⚠️ Needs Review',
        'error': '❌ Failed'
    };
    return labels[status] || status;
}

// Toggle settings panel visibility
function toggleSettings() {
    const panel = document.getElementById('settings-panel');
    const btn = document.getElementById('settings-toggle-btn');
    
    if (panel.classList.contains('show')) {
        panel.classList.remove('show');
        btn.textContent = '⚙️ Configure AI Settings';
    } else {
        panel.classList.add('show');
        btn.textContent = '❌ Close Settings';
    }
}

// Save settings to server
async function saveSettings() {
    const settings = {
        lmstudio_url: document.getElementById('setting-lmstudio-url').value,
        primary_model: document.getElementById('setting-primary-model').value,
        confidence_threshold: parseFloat(document.getElementById('setting-threshold').value) || 0.75
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            alert('✅ Settings saved!');
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('❌ Failed to save settings. Please try again.');
    }
}

// Approve item for posting
function approveItem(fileId) {
    const item = processingQueue.find(i => i.id === fileId);
    if (!item || !item.analysis) return;
    
    alert(`🚀 Posting ${item.filename} to marketplaces...\n\n(This will connect to real platforms in the full version)`);
}

// Reject/skip item
function rejectItem(fileId) {
    if (!confirm('Skip this item? It won\'t be posted.')) return;
    
    processingQueue = processingQueue.filter(i => i.id !== fileId);
    renderQueue();
    updateStats();
}

// Retry failed analysis
function retryItem(fileId) {
    const item = processingQueue.find(i => i.id === fileId);
    if (item) {
        item.status = 'pending';
        item.analysis = null;
        analyzeFile(fileId, item.filename);
    }
}

// Select folder to monitor
function selectFolder() {
    const path = prompt('Enter folder path to monitor (e.g., /home/user/products):');
    if (path) {
        document.getElementById('folder-path').value = path;
        alert(`📂 Monitoring started for: ${path}`);
    }
}

// Toggle auto-scan on/off
function toggleAutoScan() {
    const btn = document.getElementById('auto-scan-btn');
    
    if (btn.textContent.includes('Pause')) {
        btn.textContent = '▶️ Resume Auto-Scan';
        alert('⏸️ Auto-scan paused.');
    } else {
        btn.textContent = '⏸️ Pause Auto-Scan';
        alert('▶️ Auto-scan resumed!');
    }
}
