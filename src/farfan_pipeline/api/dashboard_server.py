import os
import time
import json
import logging
from typing import Dict, Any, List
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from farfan_pipeline.core.orchestrator import Orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atroz_dashboard")

# Initialize Flask App
PROJECT_ROOT = '/home/recovered/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL-3'
app = Flask(__name__, static_folder=PROJECT_ROOT, static_url_path='')
app.config['SECRET_KEY'] = os.getenv('MANIFEST_SECRET_KEY', 'atroz-secret-key')
app.config['UPLOAD_FOLDER'] = os.path.abspath('data/uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Enable CORS for development
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global state
pipeline_status = {
    "active_jobs": [],
    "completed_jobs": [],
    "system_metrics": {
        "cpu_usage": 0,
        "memory_usage": 0,
        "uptime": 0
    }
}

# Mock PDET Data (will be replaced by real data adapter)
PDET_REGIONS = [
    {"id": "arauca", "name": "Arauca", "score": 85, "x": 15, "y": 20, "municipalities": 7},
    {"id": "catatumbo", "name": "Catatumbo", "score": 72, "x": 25, "y": 15, "municipalities": 8},
    {"id": "montes_maria", "name": "Montes de María", "score": 91, "x": 35, "y": 10, "municipalities": 15},
    {"id": "pacifico_medio", "name": "Pacífico Medio", "score": 64, "x": 10, "y": 40, "municipalities": 4},
    {"id": "putumayo", "name": "Putumayo", "score": 78, "x": 20, "y": 80, "municipalities": 9},
    {"id": "sierra_nevada", "name": "Sierra Nevada", "score": 88, "x": 40, "y": 5, "municipalities": 8},
    {"id": "uraba", "name": "Urabá Antioqueño", "score": 69, "x": 20, "y": 25, "municipalities": 8},
    {"id": "choco", "name": "Chocó", "score": 55, "x": 8, "y": 30, "municipalities": 12},
    {"id": "macarena", "name": "Macarena - Guaviare", "score": 82, "x": 45, "y": 50, "municipalities": 12},
    {"id": "pacifico_nariñense", "name": "Pacífico Nariñense", "score": 60, "x": 5, "y": 70, "municipalities": 11},
    {"id": "cuenca_caguan", "name": "Cuenca del Caguán", "score": 75, "x": 30, "y": 60, "municipalities": 6},
    {"id": "sur_tolima", "name": "Sur del Tolima", "score": 89, "x": 25, "y": 45, "municipalities": 4},
    {"id": "sur_bolivar", "name": "Sur de Bolívar", "score": 67, "x": 30, "y": 20, "municipalities": 7},
    {"id": "bajo_cauca", "name": "Bajo Cauca", "score": 71, "x": 28, "y": 22, "municipalities": 13},
    {"id": "sur_cordoba", "name": "Sur de Córdoba", "score": 63, "x": 22, "y": 18, "municipalities": 5},
    {"id": "alto_patia", "name": "Alto Patía", "score": 80, "x": 15, "y": 65, "municipalities": 24}
]

# Evidence stream - will be populated by pipeline analysis
EVIDENCE_STREAM = [
    {"source": "PDT Sección 3.2", "page": 45, "text": "Implementación de estrategias municipales", "region": "arauca"},
    {"source": "PDT Capítulo 4", "page": 67, "text": "Articulación con Decálogo DDHH", "region": "catatumbo"},
    {"source": "Anexo Técnico", "page": 112, "text": "Indicadores de cumplimiento territorial", "region": "montes_maria"},
    {"source": "PDT Sección 5.1", "page": 89, "text": "Proyección territorial 2030", "region": "putumayo"},
    {"source": "PATR Capítulo 2", "page": 34, "text": "Cadenas de valor agropecuarias", "region": "bajo_cauca"},
    {"source": "PDT Sección 6.3", "page": 156, "text": "Mecanismos de participación ciudadana", "region": "choco"},
]

from flask import Flask, jsonify, request, Response

@app.route('/')
def index():
    dashboard_path = os.path.join(PROJECT_ROOT, 'dashboard.html')
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        return Response(f.read(), mimetype='text/html')

@app.route('/api/pdet-regions', methods=['GET'])
def get_pdet_regions():
    """Return PDET regions with current scores"""
    return jsonify(PDET_REGIONS)

@app.route('/api/evidence', methods=['GET'])
def get_evidence():
    """Return current evidence stream"""
    return jsonify(EVIDENCE_STREAM)

@app.route('/api/upload/plan', methods=['POST'])
def upload_plan():
    """Handle PDF plan upload"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        job_id = f"job_{int(time.time())}"
        pipeline_status['active_jobs'].append({
            "id": job_id,
            "filename": filename,
            "status": "queued",
            "progress": 0,
            "phase": 0
        })
        
        # Emit update via WebSocket
        socketio.emit('job_created', {"job_id": job_id, "filename": filename})
        
        # Trigger pipeline (mock for now, will connect to real orchestrator)
        socketio.start_background_task(run_pipeline_mock, job_id, filename)
        
        return jsonify({"message": "File uploaded successfully", "job_id": job_id}), 202
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Return system metrics"""
    import psutil
    metrics = {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "active_jobs": len(pipeline_status['active_jobs']),
        "uptime": time.time() - start_time
    }
    return jsonify(metrics)

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('system_status', {"status": "online", "version": "1.0.0"})

def run_pipeline_mock(job_id, filename):
    """Mock pipeline execution to demonstrate UI updates"""
    logger.info(f"Starting pipeline for {job_id}")
    
    phases = [
        "Acquisition & Integrity",
        "Format Decomposition",
        "Text Extraction",
        "Structure Normalization",
        "Semantic Segmentation",
        "Entity Recognition",
        "Relation Extraction",
        "Policy Analysis",
        "Report Generation"
    ]
    
    for i, phase in enumerate(phases):
        time.sleep(2)  # Simulate work
        progress = int((i + 1) / len(phases) * 100)
        
        socketio.emit('pipeline_progress', {
            "job_id": job_id,
            "phase": i + 1,
            "phase_name": phase,
            "progress": progress,
            "status": "processing"
        })
        
    socketio.emit('pipeline_completed', {
        "job_id": job_id,
        "status": "completed",
        "result_url": f"/artifacts/{job_id}/report.json"
    })

start_time = time.time()

if __name__ == '__main__':
    logger.info("Starting AtroZ Dashboard Server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
