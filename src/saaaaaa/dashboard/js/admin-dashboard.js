/**
 * AtroZ Admin Dashboard Control System
 * Complete implementation with PDF upload, pipeline integration, and real-time metrics
 */

class AtroZAdminDashboard {
    constructor() {
        this.apiUrl = window.ATROZ_API_URL || window.location.origin;
        this.socket = null;
        this.uploadedFile = null;
        this.analysisRunning = false;
        this.metrics = {
            processed: 0,
            questions: 0,
            evidence: 0,
            recommendations: 0,
            macroScore: null,
            uptime: 0
        };
        this.systemHealth = {
            cpu: 0,
            memory: 0,
            cache: 0,
            latency: 0
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.startMetricsRefresh();
        this.loadSystemMetrics();
        this.addLog('Sistema de administración inicializado correctamente', 'success');
    }

    setupEventListeners() {
        // Upload zone events
        const uploadZone = document.getElementById('uploadZone');
        const pdfInput = document.getElementById('pdfInput');

        uploadZone.addEventListener('click', () => pdfInput.click());

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        pdfInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        // Run analysis button
        document.getElementById('runAnalysisBtn').addEventListener('click', () => {
            this.runPipelineAnalysis();
        });
    }

    handleFileSelect(file) {
        if (!file.type.includes('pdf')) {
            this.showNotification('Error: Solo se permiten archivos PDF', 'error');
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            this.showNotification('Error: El archivo excede el tamaño máximo de 50MB', 'error');
            return;
        }

        this.uploadedFile = file;
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = this.formatBytes(file.size);
        document.getElementById('fileInfo').style.display = 'block';
        document.getElementById('runAnalysisBtn').disabled = false;

        this.addLog(`Archivo seleccionado: ${file.name} (${this.formatBytes(file.size)})`, 'success');
        this.showNotification(`Archivo cargado: ${file.name}`, 'success');
    }

    async runPipelineAnalysis() {
        if (!this.uploadedFile) {
            this.showNotification('Error: No hay archivo seleccionado', 'error');
            return;
        }

        if (this.analysisRunning) {
            this.showNotification('Ya hay un análisis en ejecución', 'warning');
            return;
        }

        this.analysisRunning = true;
        document.getElementById('runAnalysisBtn').disabled = true;
        document.getElementById('loadingDNA').classList.add('active');
        document.getElementById('uploadProgress').style.display = 'block';
        document.getElementById('currentStatus').textContent = 'SUBIENDO DOCUMENTO...';

        this.addLog(`Iniciando análisis del documento: ${this.uploadedFile.name}`, 'success');

        try {
            // Step 1: Upload PDF
            const uploadResponse = await this.uploadPDF();
            if (!uploadResponse.ok) {
                throw new Error('Error al subir el documento');
            }

            const uploadData = await uploadResponse.json();
            this.addLog(`Documento subido exitosamente. ID: ${uploadData.document_id}`, 'success');

            // Step 2: Trigger pipeline analysis
            document.getElementById('currentStatus').textContent = 'EJECUTANDO PIPELINE...';
            this.updateProgress(20);

            const analysisResponse = await fetch(`${this.apiUrl}/api/admin/run-analysis`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_id: uploadData.document_id,
                    settings: {
                        phase_timeout: parseInt(document.getElementById('phaseTimeout').value),
                        enable_cache: document.getElementById('enableCache').checked,
                        enable_parallel: document.getElementById('enableParallel').checked,
                        log_level: document.getElementById('logLevel').value
                    }
                })
            });

            if (!analysisResponse.ok) {
                const errorData = await analysisResponse.json();
                throw new Error(errorData.error || 'Error en el análisis');
            }

            const analysisData = await analysisResponse.json();
            this.addLog(`Pipeline iniciado. Job ID: ${analysisData.job_id}`, 'success');

            // Step 3: Monitor analysis progress via WebSocket
            this.monitorAnalysisProgress(analysisData.job_id);

        } catch (error) {
            this.addLog(`Error: ${error.message}`, 'error');
            this.showNotification(`Error: ${error.message}`, 'error');
            this.resetAnalysisState();
        }
    }

    async uploadPDF() {
        const formData = new FormData();
        formData.append('file', this.uploadedFile);
        formData.append('municipality', 'general');
        formData.append('analysis_type', 'complete');

        return fetch(`${this.apiUrl}/api/admin/upload-pdf`, {
            method: 'POST',
            body: formData
        });
    }

    monitorAnalysisProgress(jobId) {
        // WebSocket will handle real-time updates
        this.currentJobId = jobId;
        document.getElementById('currentStatus').textContent = 'PROCESANDO...';

        // Also poll for status as backup
        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiUrl}/api/admin/analysis-status/${jobId}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    this.handleAnalysisComplete(data);
                } else if (data.status === 'failed') {
                    this.handleAnalysisError(data);
                } else {
                    this.updateProgress(data.progress || 0);
                    document.getElementById('currentStatus').textContent = data.current_phase || 'PROCESANDO...';
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 2000);
    }

    handleAnalysisComplete(data) {
        clearInterval(this.progressInterval);
        this.updateProgress(100);
        document.getElementById('currentStatus').textContent = 'ANÁLISIS COMPLETADO';
        document.getElementById('loadingDNA').classList.remove('active');

        this.addLog(`Análisis completado exitosamente en ${data.duration}s`, 'success');
        this.addLog(`Preguntas analizadas: ${data.metrics.questions_analyzed}`, 'success');
        this.addLog(`Evidencias extraídas: ${data.metrics.evidence_count}`, 'success');
        this.addLog(`Score macro: ${data.metrics.macro_score}`, 'success');

        this.updateMetricsFromAnalysis(data.metrics);
        this.showNotification('¡Análisis completado exitosamente!', 'success');

        setTimeout(() => {
            this.resetAnalysisState();
        }, 3000);
    }

    handleAnalysisError(data) {
        clearInterval(this.progressInterval);
        document.getElementById('currentStatus').textContent = 'ERROR EN ANÁLISIS';
        document.getElementById('loadingDNA').classList.remove('active');

        this.addLog(`Error en análisis: ${data.error}`, 'error');
        this.showNotification(`Error: ${data.error}`, 'error');

        this.resetAnalysisState();
    }

    updateProgress(percent) {
        document.getElementById('uploadProgressFill').style.width = `${percent}%`;
    }

    resetAnalysisState() {
        this.analysisRunning = false;
        document.getElementById('runAnalysisBtn').disabled = false;
        document.getElementById('currentStatus').textContent = 'ESPERANDO DOCUMENTO';
        document.getElementById('uploadProgress').style.display = 'none';
        this.updateProgress(0);
    }

    connectWebSocket() {
        if (typeof io === 'undefined') {
            console.warn('Socket.IO not available, using polling only');
            return;
        }

        this.socket = io(this.apiUrl);

        this.socket.on('connect', () => {
            this.addLog('Conexión WebSocket establecida', 'success');
        });

        this.socket.on('disconnect', () => {
            this.addLog('Conexión WebSocket perdida', 'warning');
        });

        this.socket.on('analysis_progress', (data) => {
            if (data.job_id === this.currentJobId) {
                this.updateProgress(data.progress);
                document.getElementById('currentStatus').textContent = data.phase;
                this.addLog(`Fase ${data.phase_num}/11: ${data.phase}`, 'info');
            }
        });

        this.socket.on('analysis_complete', (data) => {
            if (data.job_id === this.currentJobId) {
                this.handleAnalysisComplete(data);
            }
        });

        this.socket.on('analysis_error', (data) => {
            if (data.job_id === this.currentJobId) {
                this.handleAnalysisError(data);
            }
        });

        this.socket.on('system_metrics', (data) => {
            this.updateSystemHealth(data);
        });
    }

    async loadSystemMetrics() {
        try {
            const response = await fetch(`${this.apiUrl}/api/admin/metrics`);
            if (!response.ok) return;

            const data = await response.json();
            this.updateMetrics(data);
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    updateMetrics(data) {
        document.getElementById('metricProcessed').textContent = data.documents_processed || 0;
        document.getElementById('metricQuestions').textContent = data.total_questions || 0;
        document.getElementById('metricEvidence').textContent = data.total_evidence || 0;
        document.getElementById('metricRecommendations').textContent = data.total_recommendations || 0;
        document.getElementById('metricScore').textContent = data.avg_macro_score ? data.avg_macro_score.toFixed(1) : '--';
        document.getElementById('metricUptime').textContent = this.formatUptime(data.uptime_seconds || 0);

        // Orchestrator metrics
        document.getElementById('calibrationVersion').textContent = data.calibration_version || '--';
        document.getElementById('methodCount').textContent = data.method_count || '--';
        document.getElementById('questionCount').textContent = data.question_count || '--';
        document.getElementById('lastVerification').textContent = data.last_verification || '--';

        // Performance metrics
        document.getElementById('perfMacro').textContent = data.perf_macro?.toFixed(2) || '--';
        document.getElementById('perfMeso').textContent = data.perf_meso?.toFixed(2) || '--';
        document.getElementById('perfMicro').textContent = data.perf_micro?.toFixed(2) || '--';
        document.getElementById('perfReport').textContent = data.perf_report?.toFixed(2) || '--';

        // Last run info
        if (data.last_run) {
            document.getElementById('lastRun').textContent = new Date(data.last_run).toLocaleString('es-CO');
        }

        if (data.estimated_time) {
            document.getElementById('estimatedTime').textContent = `${data.estimated_time}s`;
        }
    }

    updateMetricsFromAnalysis(metrics) {
        this.metrics.processed++;
        this.metrics.questions += metrics.questions_analyzed || 0;
        this.metrics.evidence += metrics.evidence_count || 0;
        this.metrics.recommendations += metrics.recommendations_count || 0;
        this.metrics.macroScore = metrics.macro_score;

        document.getElementById('metricProcessed').textContent = this.metrics.processed;
        document.getElementById('metricQuestions').textContent = this.metrics.questions;
        document.getElementById('metricEvidence').textContent = this.metrics.evidence;
        document.getElementById('metricRecommendations').textContent = this.metrics.recommendations;
        document.getElementById('metricScore').textContent = this.metrics.macroScore?.toFixed(1) || '--';
    }

    updateSystemHealth(data) {
        this.systemHealth = {
            cpu: data.cpu || 0,
            memory: data.memory || 0,
            cache: data.cache_hit_rate || 0,
            latency: data.api_latency || 0
        };

        document.getElementById('cpuValue').textContent = `${this.systemHealth.cpu.toFixed(1)}%`;
        document.getElementById('cpuBar').style.width = `${this.systemHealth.cpu}%`;

        document.getElementById('memValue').textContent = `${this.systemHealth.memory.toFixed(1)}%`;
        document.getElementById('memBar').style.width = `${this.systemHealth.memory}%`;

        document.getElementById('cacheValue').textContent = `${this.systemHealth.cache.toFixed(1)}%`;
        document.getElementById('cacheBar').style.width = `${this.systemHealth.cache}%`;

        const latencyPercent = Math.min((this.systemHealth.latency / 1000) * 100, 100);
        document.getElementById('latencyValue').textContent = `${this.systemHealth.latency.toFixed(0)}ms`;
        document.getElementById('latencyBar').style.width = `${latencyPercent}%`;
    }

    startMetricsRefresh() {
        // Refresh metrics every 5 seconds
        setInterval(() => {
            this.loadSystemMetrics();
        }, 5000);

        // Update uptime every second
        setInterval(() => {
            this.metrics.uptime++;
            document.getElementById('metricUptime').textContent = this.formatUptime(this.metrics.uptime);
        }, 1000);
    }

    addLog(message, type = 'info') {
        const logConsole = document.getElementById('logConsole');
        const timestamp = new Date().toLocaleTimeString('es-CO', { hour12: false });

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span> <span>${message}</span>`;

        logConsole.appendChild(logEntry);
        logConsole.scrollTop = logConsole.scrollHeight;

        // Keep only last 100 entries
        while (logConsole.children.length > 100) {
            logConsole.removeChild(logConsole.firstChild);
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const messageEl = document.getElementById('notificationMessage');

        let icon = '📢';
        if (type === 'success') icon = '✓';
        if (type === 'error') icon = '✗';
        if (type === 'warning') icon = '⚠';

        messageEl.textContent = `${icon} ${message}`;
        notification.classList.add('active');

        setTimeout(() => {
            notification.classList.remove('active');
        }, 4000);
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}

// Global functions for UI controls
function clearLogs() {
    const logConsole = document.getElementById('logConsole');
    logConsole.innerHTML = '<div class="log-entry"><span class="timestamp">[--:--:--]</span> <span>Logs limpiados</span></div>';
}

function exportLogs() {
    const logConsole = document.getElementById('logConsole');
    const logs = Array.from(logConsole.children).map(entry => entry.textContent).join('\n');
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `atroz-logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

function refreshMetrics() {
    if (window.adminDashboard) {
        window.adminDashboard.loadSystemMetrics();
        window.adminDashboard.showNotification('Métricas actualizadas', 'success');
    }
}

function saveSettings() {
    const settings = {
        logLevel: document.getElementById('logLevel').value,
        phaseTimeout: document.getElementById('phaseTimeout').value,
        enableCache: document.getElementById('enableCache').checked,
        enableParallel: document.getElementById('enableParallel').checked
    };

    localStorage.setItem('atrozAdminSettings', JSON.stringify(settings));

    if (window.adminDashboard) {
        window.adminDashboard.addLog('Configuración guardada', 'success');
        window.adminDashboard.showNotification('Configuración guardada correctamente', 'success');
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AtroZAdminDashboard();

    // Load saved settings
    const savedSettings = localStorage.getItem('atrozAdminSettings');
    if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        document.getElementById('logLevel').value = settings.logLevel || 'INFO';
        document.getElementById('phaseTimeout').value = settings.phaseTimeout || 300;
        document.getElementById('enableCache').checked = settings.enableCache !== false;
        document.getElementById('enableParallel').checked = settings.enableParallel !== false;
    }
});
