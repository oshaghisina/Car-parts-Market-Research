// Custom JavaScript for Torob Scraper Web Interface

// Global variables
let currentTaskId = null;
let progressInterval = null;
let logInterval = null;
let autoScroll = true;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Torob Scraper Web Interface initialized');
    
    // Initialize parts inputs
    updatePartInputs();
    
    // Add event listeners
    setupEventListeners();
    
    // Load initial configuration
    loadConfiguration();
});

// Setup event listeners
function setupEventListeners() {
    // File input change
    document.getElementById('fileInput').addEventListener('change', function() {
        const fileName = this.files[0]?.name;
        if (fileName) {
            showAlert(`File selected: ${fileName}`, 'info');
        }
    });
    
    // Form validation
    document.getElementById('excelFilename').addEventListener('input', validateForm);
    document.getElementById('partCount').addEventListener('change', function() {
        updatePartInputs();
        validateForm();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            startScraping();
        }
    });
}

// Load configuration
function loadConfiguration() {
    fetch('/api/config')
    .then(response => response.json())
    .then(data => {
        console.log('Configuration loaded:', data);
        // Store configuration for later use
        window.appConfig = data;
    })
    .catch(error => {
        console.error('Error loading configuration:', error);
    });
}

// Update parts inputs based on count
function updatePartInputs() {
    const count = parseInt(document.getElementById('partCount').value);
    const container = document.getElementById('partsInput');
    
    container.innerHTML = '';
    
    for (let i = 1; i <= count; i++) {
        const partDiv = document.createElement('div');
        partDiv.className = 'card mb-3 fade-in';
        partDiv.innerHTML = `
            <div class="card-header">
                <h6 class="mb-0">
                    <i class="fas fa-car"></i> Part ${i}
                </h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Part Name *</label>
                        <input type="text" class="form-control" id="partName${i}" 
                               placeholder="e.g., چراغ سمت راست تیگو ۸ پرو" required
                               oninput="validateForm()">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Part Code</label>
                        <input type="text" class="form-control" id="partCode${i}" 
                               placeholder="e.g., TIGGO8-HEADLIGHT-RH">
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <label class="form-label">Keywords</label>
                        <input type="text" class="form-control" id="keywords${i}" 
                               placeholder="Auto-generated if empty">
                    </div>
                </div>
            </div>
        `;
        container.appendChild(partDiv);
    }
    
    validateForm();
}

// Validate form
function validateForm() {
    const partsData = getPartsData();
    const isValid = partsData.length > 0;
    
    const startButton = document.querySelector('button[onclick="startScraping()"]');
    if (startButton) {
        startButton.disabled = !isValid;
        if (isValid) {
            startButton.classList.remove('btn-secondary');
            startButton.classList.add('btn-primary');
        } else {
            startButton.classList.remove('btn-primary');
            startButton.classList.add('btn-secondary');
        }
    }
    
    return isValid;
}

// Upload file
function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a file', 'warning');
        return;
    }
    
    // Show loading state
    const uploadButton = document.querySelector('button[onclick="uploadFile()"]');
    const originalText = uploadButton.innerHTML;
    uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
    uploadButton.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(`File uploaded successfully! Found ${data.parts_count} parts.`, 'success');
            loadPartsFromFile(data.parts_data);
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error uploading file: ' + error.message, 'danger');
    })
    .finally(() => {
        // Reset button state
        uploadButton.innerHTML = originalText;
        uploadButton.disabled = false;
    });
}

// Load parts from uploaded file
function loadPartsFromFile(partsData) {
    const count = partsData.length;
    document.getElementById('partCount').value = count;
    updatePartInputs();
    
    partsData.forEach((part, index) => {
        const i = index + 1;
        document.getElementById(`partName${i}`).value = part.part_name || '';
        document.getElementById(`partCode${i}`).value = part.part_code || '';
        document.getElementById(`keywords${i}`).value = part.keywords || '';
    });
    
    validateForm();
}

// Start scraping
function startScraping() {
    if (!validateForm()) {
        showAlert('Please enter at least one part', 'warning');
        return;
    }
    
    const partsData = getPartsData();
    const excelFilename = document.getElementById('excelFilename').value || 'torob_prices.xlsx';
    
    // Show confirmation
    const confirmed = confirm(`Start scraping ${partsData.length} part(s)?\n\nThis may take several minutes.`);
    if (!confirmed) {
        return;
    }
    
    const data = {
        parts_data: partsData,
        excel_filename: excelFilename
    };
    
    // Show loading state
    const startButton = document.querySelector('button[onclick="startScraping()"]');
    const originalText = startButton.innerHTML;
    startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
    startButton.disabled = true;
    
    fetch('/api/start_scraping', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentTaskId = data.task_id;
            showProgress();
            startProgressTracking();
        } else {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error starting scraping: ' + error.message, 'danger');
    })
    .finally(() => {
        // Reset button state
        startButton.innerHTML = originalText;
        startButton.disabled = false;
    });
}

// Get parts data from form
function getPartsData() {
    const count = parseInt(document.getElementById('partCount').value);
    const partsData = [];
    
    for (let i = 1; i <= count; i++) {
        const partName = document.getElementById(`partName${i}`).value.trim();
        const partCode = document.getElementById(`partCode${i}`).value.trim();
        const keywords = document.getElementById(`keywords${i}`).value.trim();
        
        if (partName) {
            partsData.push({
                part_id: `part_${i}_${Date.now()}`,
                part_name: partName,
                part_code: partCode,
                keywords: keywords || `${partName} automotive part`
            });
        }
    }
    
    return partsData;
}

// Show progress section
function showProgress() {
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('logSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Clear previous log
    clearLog();
    
    // Scroll to progress section
    document.getElementById('progressSection').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

// Start progress tracking
function startProgressTracking() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    // Start log tracking
    startLogTracking();
    
    progressInterval = setInterval(() => {
        if (currentTaskId) {
            fetch(`/api/task_status/${currentTaskId}`)
            .then(response => response.json())
            .then(data => {
                updateProgress(data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(progressInterval);
                    clearInterval(logInterval);
                    showResults(data);
                }
            })
            .catch(error => {
                console.error('Error fetching progress:', error);
            });
        }
    }, 1000);
}

// Start log tracking
function startLogTracking() {
    if (logInterval) {
        clearInterval(logInterval);
    }
    
    // Add initial log message
    addLogMessage('🚀 Starting scraping process...', 'info');
    
    logInterval = setInterval(() => {
        if (currentTaskId) {
            fetch(`/api/task_logs/${currentTaskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.logs && data.logs.length > 0) {
                    data.logs.forEach(log => {
                        addLogMessage(log.message, log.level);
                    });
                }
            })
            .catch(error => {
                // Log endpoint might not exist yet, that's okay
                console.log('Log endpoint not available yet');
            });
        }
    }, 2000); // Check for logs every 2 seconds
}

// Update progress display
function updateProgress(data) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressMessage = document.getElementById('progressMessage');
    
    if (data.progress !== undefined) {
        progressBar.style.width = data.progress + '%';
        progressText.textContent = data.progress + '%';
    }
    
    if (data.message) {
        progressMessage.textContent = data.message;
    }
    
    // Update progress details
    const details = [];
    if (data.completed_tasks !== undefined) {
        details.push(`Completed: ${data.completed_tasks}`);
    }
    if (data.failed_tasks !== undefined) {
        details.push(`Failed: ${data.failed_tasks}`);
    }
    if (data.total_tasks !== undefined) {
        details.push(`Total: ${data.total_tasks}`);
    }
    
    document.getElementById('progressDetails').textContent = details.join(' | ');
}

// Add log message
function addLogMessage(message, level = 'info') {
    const logContainer = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry mb-1 log-${level}`;
    
    const levelIcon = getLevelIcon(level);
    const levelColor = getLevelColor(level);
    
    logEntry.innerHTML = `
        <span class="text-muted">[${timestamp}]</span>
        <span class="${levelColor}">${levelIcon}</span>
        <span>${message}</span>
    `;
    
    logContainer.appendChild(logEntry);
    
    // Auto-scroll if enabled
    if (autoScroll) {
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// Get level icon
function getLevelIcon(level) {
    const icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'search': '🔍',
        'drill': '📄',
        'found': '📊',
        'processing': '🔄'
    };
    return icons[level] || 'ℹ️';
}

// Get level color
function getLevelColor(level) {
    const colors = {
        'info': 'text-info',
        'success': 'text-success',
        'warning': 'text-warning',
        'error': 'text-danger',
        'search': 'text-primary',
        'drill': 'text-info',
        'found': 'text-success',
        'processing': 'text-warning'
    };
    return colors[level] || 'text-light';
}

// Clear log
function clearLog() {
    const logContainer = document.getElementById('logContainer');
    logContainer.innerHTML = '<div class="text-muted">Waiting for scraping to start...</div>';
}

// Toggle auto-scroll
function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const icon = document.getElementById('autoScrollIcon');
    
    if (autoScroll) {
        icon.className = 'fas fa-arrow-down';
        // Scroll to bottom
        const logContainer = document.getElementById('logContainer');
        logContainer.scrollTop = logContainer.scrollHeight;
    } else {
        icon.className = 'fas fa-pause';
    }
}

// Show results
function showResults(data) {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('logSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    const resultsContent = document.getElementById('resultsContent');
    
    if (data.status === 'completed') {
        resultsContent.innerHTML = `
            <div class="alert alert-success">
                <h5><i class="fas fa-check-circle"></i> Scraping Completed Successfully!</h5>
                <p>Your results are ready for download.</p>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-chart-bar"></i> Statistics</h6>
                    <ul class="list-unstyled">
                        <li><strong>Parts Processed:</strong> ${data.stats?.parts_processed || 'N/A'}</li>
                        <li><strong>Search Results:</strong> ${data.stats?.search_results || 'N/A'}</li>
                        <li><strong>Final Offers:</strong> ${data.stats?.final_offers || 'N/A'}</li>
                        <li><strong>Unique Sellers:</strong> ${data.stats?.unique_sellers || 'N/A'}</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-file-excel"></i> File Information</h6>
                    <ul class="list-unstyled">
                        <li><strong>Excel File:</strong> ${data.excel_file || 'N/A'}</li>
                        <li><strong>Status:</strong> <span class="badge bg-success">Ready</span></li>
                        <li><strong>Completion Time:</strong> ${new Date().toLocaleString()}</li>
                    </ul>
                </div>
            </div>
        `;
    } else {
        resultsContent.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="fas fa-exclamation-triangle"></i> Scraping Failed</h5>
                <p>${data.error || 'An unknown error occurred'}</p>
            </div>
        `;
    }
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

// Download results
function downloadResults() {
    if (currentTaskId) {
        window.open(`/api/download/${currentTaskId}`, '_blank');
    }
}

// Start new scraping
function startNewScraping() {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('logSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    clearForm();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Clear form
function clearForm() {
    document.getElementById('excelFilename').value = 'torob_prices.xlsx';
    document.getElementById('partCount').value = '1';
    updatePartInputs();
    document.getElementById('fileInput').value = '';
    currentTaskId = null;
    
    if (progressInterval) {
        clearInterval(progressInterval);
    }
}

// Show alert
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.getElementById('uploadStatus').innerHTML = '';
    document.getElementById('uploadStatus').appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Show configuration
function showConfig() {
    fetch('/api/config')
    .then(response => response.json())
    .then(data => {
        document.getElementById('configContent').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-search"></i> Scraping Settings</h6>
                    <div class="config-item">
                        <div class="config-label">Base URL</div>
                        <div class="config-value">${data.scraping?.base_url || 'N/A'}</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">Delay Range</div>
                        <div class="config-value">${data.scraping?.delay_range?.min || 'N/A'}-${data.scraping?.delay_range?.max || 'N/A'}s</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">Max Scroll Attempts</div>
                        <div class="config-value">${data.scraping?.scroll?.max_attempts || 'N/A'}</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-bolt"></i> Performance Settings</h6>
                    <div class="config-item">
                        <div class="config-label">Caching</div>
                        <div class="config-value">
                            <span class="badge bg-${data.caching?.enabled ? 'success' : 'secondary'}">
                                ${data.caching?.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">Cache TTL</div>
                        <div class="config-value">${data.caching?.ttl_hours || 'N/A'} hours</div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">Parallel Processing</div>
                        <div class="config-value">
                            <span class="badge bg-${data.performance?.parallel?.enabled ? 'success' : 'secondary'}">
                                ${data.performance?.parallel?.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                    </div>
                    <div class="config-item">
                        <div class="config-label">Max Workers</div>
                        <div class="config-value">${data.performance?.parallel?.max_workers || 'N/A'}</div>
                    </div>
                </div>
            </div>
        `;
        
        new bootstrap.Modal(document.getElementById('configModal')).show();
    })
    .catch(error => {
        showAlert('Error loading configuration: ' + error.message, 'danger');
    });
}

// Show tasks
function showTasks() {
    fetch('/api/tasks')
    .then(response => response.json())
    .then(data => {
        const tasksHtml = Object.keys(data).length > 0 ? 
            Object.entries(data).map(([id, task]) => `
                <div class="card mb-3 task-card">
                    <div class="card-body">
                        <h6><i class="fas fa-tasks"></i> Task ${id.substring(0, 8)}...</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <p class="mb-1"><strong>Status:</strong> 
                                    <span class="badge bg-${task.status === 'completed' ? 'success' : task.status === 'failed' ? 'danger' : 'warning'}">
                                        ${task.status}
                                    </span>
                                </p>
                                <p class="mb-1"><strong>Message:</strong> ${task.message || 'N/A'}</p>
                            </div>
                            <div class="col-md-6">
                                <p class="mb-1"><strong>Start Time:</strong> ${task.start_time || 'N/A'}</p>
                                <p class="mb-0"><strong>End Time:</strong> ${task.end_time || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('') : 
            '<p class="text-muted text-center">No tasks found.</p>';
        
        document.getElementById('tasksContent').innerHTML = tasksHtml;
        new bootstrap.Modal(document.getElementById('tasksModal')).show();
    })
    .catch(error => {
        showAlert('Error loading tasks: ' + error.message, 'danger');
    });
}

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Export functions for global access
window.updatePartInputs = updatePartInputs;
window.uploadFile = uploadFile;
window.startScraping = startScraping;
window.downloadResults = downloadResults;
window.startNewScraping = startNewScraping;
window.clearForm = clearForm;
window.showConfig = showConfig;
window.showTasks = showTasks;
