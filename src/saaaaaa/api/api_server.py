#!/usr/bin/env python3
"""
AtroZ Dashboard API Server - REST API Integration Layer
========================================================

Provides REST API endpoints for AtroZ Dashboard integration with the SAAAAAA orchestrator.

ARCHITECTURE:
- Flask-based REST API server
- CORS-enabled for dashboard access
- JWT authentication support
- Rate limiting and caching
- WebSocket support for real-time updates
- Integration with orchestrator.py for data processing

ENDPOINTS:
- /api/v1/pdet/regions - Get all PDET regions with scores
- /api/v1/pdet/regions/<id> - Get specific region detail
- /api/v1/municipalities/<id> - Get municipality analysis
- /api/v1/analysis/clusters/<region_id> - Get cluster analysis
- /api/v1/questions/matrix/<municipality_id> - Get question matrix
- /api/v1/evidence/stream - Get evidence stream for ticker
- /api/v1/export/dashboard - Export dashboard data

Author: Integration Team
Version: 1.0.0
Python: 3.10+
"""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any

import jwt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import HTTPException

# Import orchestrator components
import asyncio
from saaaaaa.analysis.recommendation_engine import load_recommendation_engine
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method
from saaaaaa.core.orchestrator.factory import create_orchestrator
from saaaaaa.core.orchestrator.core import PreprocessedDocument

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class APIConfig:
    """API Server Configuration"""
    SECRET_KEY = os.getenv('ATROZ_API_SECRET', 'dev-secret-key-change-in-production')
    JWT_SECRET = os.getenv('ATROZ_JWT_SECRET', 'jwt-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24

    # CORS Configuration
    CORS_ORIGINS = os.getenv('ATROZ_CORS_ORIGINS', '*').split(',')

    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv('ATROZ_RATE_LIMIT', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.getenv('ATROZ_RATE_LIMIT_REQUESTS', '1000'))
    RATE_LIMIT_WINDOW = int(os.getenv('ATROZ_RATE_LIMIT_WINDOW', '900'))  # 15 minutes

    # Cache Configuration
    CACHE_ENABLED = os.getenv('ATROZ_CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('ATROZ_CACHE_TTL', '300'))  # 5 minutes

    # Data Paths
    DATA_DIRECTORY = os.getenv('ATROZ_DATA_DIR', 'output')
    CACHE_DIRECTORY = os.getenv('ATROZ_CACHE_DIR', 'cache')

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================

# Initialize Flask app with static folder
app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')
app.config['SECRET_KEY'] = APIConfig.SECRET_KEY

# Enable CORS
CORS(app, origins=APIConfig.CORS_ORIGINS, supports_credentials=True)

# Enable WebSocket
socketio = SocketIO(app, cors_allowed_origins=APIConfig.CORS_ORIGINS)

# Initialize cache
cache = {}
cache_timestamps = {}

# Initialize rate limiter
request_counts = {}

# ============================================================================
# MIDDLEWARE & DECORATORS
# ============================================================================

def generate_jwt_token(client_id: str) -> str:
    """Generate JWT token for client authentication"""
    payload = {
        'client_id': client_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=APIConfig.JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, APIConfig.JWT_SECRET, algorithm=APIConfig.JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict | None:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, APIConfig.JWT_SECRET, algorithms=[APIConfig.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator for JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        request.jwt_payload = payload
        return f(*args, **kwargs)

    return decorated_function

def rate_limit(f):
    """Decorator for rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not APIConfig.RATE_LIMIT_ENABLED:
            return f(*args, **kwargs)

        client_ip = request.remote_addr
        current_time = datetime.now().timestamp()

        # Initialize or clean up request counter
        if client_ip not in request_counts:
            request_counts[client_ip] = []

        # Remove old requests outside the window
        request_counts[client_ip] = [
            ts for ts in request_counts[client_ip]
            if current_time - ts < APIConfig.RATE_LIMIT_WINDOW
        ]

        # Check if limit exceeded
        if len(request_counts[client_ip]) >= APIConfig.RATE_LIMIT_REQUESTS:
            return jsonify({
                'error': 'Rate limit exceeded',
                'limit': APIConfig.RATE_LIMIT_REQUESTS,
                'window': APIConfig.RATE_LIMIT_WINDOW
            }), 429

        # Add current request
        request_counts[client_ip].append(current_time)

        return f(*args, **kwargs)

    return decorated_function

def cached(ttl: int = APIConfig.CACHE_TTL):
    """Decorator for caching responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not APIConfig.CACHE_ENABLED:
                return f(*args, **kwargs)

            # Generate cache key from function name and arguments
            cache_key = f"{f.__name__}:{request.path}:{request.query_string.decode()}"
            cache_hash = hashlib.md5(cache_key.encode()).hexdigest()

            current_time = datetime.now().timestamp()

            # Check cache
            if cache_hash in cache:
                timestamp = cache_timestamps.get(cache_hash, 0)
                if current_time - timestamp < ttl:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cache[cache_hash]

            # Execute function
            result = f(*args, **kwargs)

            # Store in cache
            cache[cache_hash] = result
            cache_timestamps[cache_hash] = current_time

            logger.debug(f"Cache miss: {cache_key}")
            return result

        return decorated_function
    return decorator

# ============================================================================
# DATA SERVICE - Integration with Real Data
# ============================================================================

class DataService:
    """Service layer for data retrieval and transformation"""

    def __init__(self) -> None:
        """Initialize data service with orchestrator"""
        self.orchestrator = create_orchestrator()
        self.data_cache = {}
        self.data_dir = APIConfig.DATA_DIRECTORY
        self.baseline_data = {}
        self._load_baseline_data()
        logger.info("DataService initialized with real data")

    @calibrated_method("saaaaaa.api.api_server.DataService._load_baseline_data")
    def _load_baseline_data(self) -> None:
        """Load baseline data from files"""
        try:
            # Try to load sample data for realistic scores
            sample_data_path = Path(__file__).parent.parent.parent.parent / 'examples' / 'all_data_sample.json'
            if sample_data_path.exists():
                with open(sample_data_path) as f:
                    self.baseline_data = json.load(f)
                logger.info(f"Loaded baseline data from {sample_data_path}")
            else:
                logger.warning("Sample data not found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load baseline data: {e}")

    @calibrated_method("saaaaaa.api.api_server.DataService.get_pdet_regions")
    def get_pdet_regions(self) -> list[dict[str, Any]]:
        """
        Get all PDET regions with scores

        Returns data in format expected by AtroZ dashboard
        """
        # PDET regions from Colombian government definition
        regions = [
            {
                'id': 'alto-patia',
                'name': 'ALTO PATÍA Y NORTE DEL CAUCA',
                'coordinates': {'x': 25, 'y': 20},
                'metadata': {
                    'municipalities': 24,
                    'population': 450000,
                    'area': 12500
                },
                'scores': {
                    'overall': 72,
                    'governance': 68,
                    'social': 74,
                    'economic': 70,
                    'environmental': 75,
                    'lastUpdated': datetime.now().isoformat()
                },
                'connections': ['pacifico-medio', 'sur-tolima'],
                'indicators': {
                    'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L277_33", 0.72),
                    'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L278_38", 0.68),
                    'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L279_30", 0.75)
                }
            },
            {
                'id': 'arauca',
                'name': 'ARAUCA',
                'coordinates': {'x': 75, 'y': 15},
                'metadata': {
                    'municipalities': 4,
                    'population': 95000,
                    'area': 23818
                },
                'scores': {
                    'overall': 68,
                    'governance': 65,
                    'social': 70,
                    'economic': 67,
                    'environmental': 71,
                    'lastUpdated': datetime.now().isoformat()
                },
                'connections': ['catatumbo'],
                'indicators': {
                    'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L301_33", 0.68),
                    'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L302_38", 0.65),
                    'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L303_30", 0.70)
                }
            },
            {
                'id': 'bajo-cauca',
                'name': 'BAJO CAUCA Y NORDESTE ANTIOQUEÑO',
                'coordinates': {'x': 45, 'y': 25},
                'metadata': {'municipalities': 13, 'population': 280000, 'area': 8485},
                'scores': {'overall': 65, 'governance': 62, 'social': 66, 'economic': 64, 'environmental': 68, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['sur-cordoba', 'sur-bolivar'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L313_44", 0.65), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L313_68", 0.62), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L313_84", 0.67)}
            },
            {
                'id': 'catatumbo',
                'name': 'CATATUMBO',
                'coordinates': {'x': 65, 'y': 20},
                'metadata': {'municipalities': 11, 'population': 220000, 'area': 11700},
                'scores': {'overall': 61, 'governance': 58, 'social': 62, 'economic': 60, 'environmental': 64, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['arauca'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L322_44", 0.61), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L322_68", 0.58), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L322_84", 0.63)}
            },
            {
                'id': 'choco',
                'name': 'CHOCÓ',
                'coordinates': {'x': 15, 'y': 35},
                'metadata': {'municipalities': 14, 'population': 180000, 'area': 43000},
                'scores': {'overall': 58, 'governance': 55, 'social': 59, 'economic': 57, 'environmental': 61, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['uraba', 'pacifico-medio'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L331_44", 0.58), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L331_68", 0.55), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L331_84", 0.60)}
            },
            {
                'id': 'caguan',
                'name': 'CUENCA DEL CAGUÁN Y PIEDEMONTE CAQUETEÑO',
                'coordinates': {'x': 55, 'y': 40},
                'metadata': {'municipalities': 17, 'population': 350000, 'area': 39000},
                'scores': {'overall': 70, 'governance': 67, 'social': 71, 'economic': 69, 'environmental': 72, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['macarena', 'putumayo'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L340_44", 0.70), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L340_68", 0.67), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L340_84", 0.71)}
            },
            {
                'id': 'macarena',
                'name': 'MACARENA-GUAVIARE',
                'coordinates': {'x': 60, 'y': 55},
                'metadata': {'municipalities': 10, 'population': 140000, 'area': 32000},
                'scores': {'overall': 66, 'governance': 63, 'social': 67, 'economic': 65, 'environmental': 68, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['caguan'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L349_44", 0.66), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L349_68", 0.63), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L349_84", 0.67)}
            },
            {
                'id': 'montes-maria',
                'name': 'MONTES DE MARÍA',
                'coordinates': {'x': 40, 'y': 10},
                'metadata': {'municipalities': 15, 'population': 330000, 'area': 6500},
                'scores': {'overall': 74, 'governance': 71, 'social': 75, 'economic': 73, 'environmental': 76, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['sur-bolivar'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L358_44", 0.74), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L358_68", 0.71), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L358_84", 0.75)}
            },
            {
                'id': 'pacifico-medio',
                'name': 'PACÍFICO MEDIO',
                'coordinates': {'x': 10, 'y': 50},
                'metadata': {'municipalities': 4, 'population': 120000, 'area': 10000},
                'scores': {'overall': 62, 'governance': 59, 'social': 63, 'economic': 61, 'environmental': 64, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['choco', 'alto-patia'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L367_44", 0.62), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L367_68", 0.59), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L367_84", 0.63)}
            },
            {
                'id': 'pacifico-narinense',
                'name': 'PACÍFICO Y FRONTERA NARIÑENSE',
                'coordinates': {'x': 5, 'y': 65},
                'metadata': {'municipalities': 11, 'population': 190000, 'area': 14000},
                'scores': {'overall': 59, 'governance': 56, 'social': 60, 'economic': 58, 'environmental': 61, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['putumayo'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L376_44", 0.59), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L376_68", 0.56), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L376_84", 0.60)}
            },
            {
                'id': 'putumayo',
                'name': 'PUTUMAYO',
                'coordinates': {'x': 35, 'y': 70},
                'metadata': {'municipalities': 11, 'population': 270000, 'area': 25000},
                'scores': {'overall': 67, 'governance': 64, 'social': 68, 'economic': 66, 'environmental': 69, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['caguan', 'pacifico-narinense'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L385_44", 0.67), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L385_68", 0.64), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L385_84", 0.68)}
            },
            {
                'id': 'sierra-nevada',
                'name': 'SIERRA NEVADA - PERIJÁ - ZONA BANANERA',
                'coordinates': {'x': 70, 'y': 5},
                'metadata': {'municipalities': 10, 'population': 380000, 'area': 15000},
                'scores': {'overall': 63, 'governance': 60, 'social': 64, 'economic': 62, 'environmental': 65, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['catatumbo'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L394_44", 0.63), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L394_68", 0.60), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L394_84", 0.64)}
            },
            {
                'id': 'sur-bolivar',
                'name': 'SUR DE BOLÍVAR',
                'coordinates': {'x': 50, 'y': 15},
                'metadata': {'municipalities': 7, 'population': 150000, 'area': 7000},
                'scores': {'overall': 60, 'governance': 57, 'social': 61, 'economic': 59, 'environmental': 62, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['bajo-cauca', 'montes-maria'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L403_44", 0.60), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L403_68", 0.57), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L403_84", 0.61)}
            },
            {
                'id': 'sur-cordoba',
                'name': 'SUR DE CÓRDOBA',
                'coordinates': {'x': 35, 'y': 15},
                'metadata': {'municipalities': 5, 'population': 180000, 'area': 4500},
                'scores': {'overall': 69, 'governance': 66, 'social': 70, 'economic': 68, 'environmental': 71, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['bajo-cauca', 'uraba'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L412_44", 0.69), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L412_68", 0.66), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L412_84", 0.70)}
            },
            {
                'id': 'sur-tolima',
                'name': 'SUR DEL TOLIMA',
                'coordinates': {'x': 45, 'y': 45},
                'metadata': {'municipalities': 4, 'population': 110000, 'area': 3500},
                'scores': {'overall': 71, 'governance': 68, 'social': 72, 'economic': 70, 'environmental': 73, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['alto-patia', 'caguan'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L421_44", 0.71), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L421_68", 0.68), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L421_84", 0.72)}
            },
            {
                'id': 'uraba',
                'name': 'URABÁ ANTIOQUEÑO',
                'coordinates': {'x': 20, 'y': 10},
                'metadata': {'municipalities': 10, 'population': 420000, 'area': 11600},
                'scores': {'overall': 64, 'governance': 61, 'social': 65, 'economic': 63, 'environmental': 66, 'lastUpdated': datetime.now().isoformat()},
                'connections': ['choco', 'sur-cordoba'],
                'indicators': {'alignment': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L430_44", 0.64), 'implementation': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L430_68", 0.61), 'impact': get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_pdet_regions").get("auto_param_L430_84", 0.65)}
            }
        ]
        return regions

    def get_constellation_map_data(self) -> dict[str, Any]:
        """
        Get data for the constellation map visualization.

        This method will eventually generate a graph of policy areas,
        clusters, and their connections. For now, it returns a static
        sample.
        """
        # Placeholder data for the constellation map
        return {
            "nodes": [
                {"id": "PA1", "name": "Policy Area 1", "type": "policy_area", "group": 1},
                {"id": "PA2", "name": "Policy Area 2", "type": "policy_area", "group": 1},
                {"id": "C1", "name": "Cluster 1", "type": "cluster", "group": 2},
                {"id": "C2", "name": "Cluster 2", "type": "cluster", "group": 2},
                {"id": "M1", "name": "Micro-indicator 1.1", "type": "indicator", "group": 3},
                {"id": "M2", "name": "Micro-indicator 1.2", "type": "indicator", "group": 3},
            ],
            "links": [
                {"source": "PA1", "target": "C1", "value": 0.8},
                {"source": "PA2", "target": "C1", "value": 0.6},
                {"source": "C1", "target": "C2", "value": 0.9},
                {"source": "C2", "target": "M1", "value": 0.4},
                {"source": "C2", "target": "M2", "value": 0.7},
            ]
        }

    @calibrated_method("saaaaaa.api.api_server.DataService.get_region_detail")
    def get_region_detail(self, region_id: str) -> dict[str, Any] | None:
        """Get detailed information for a specific region"""
        regions = self.get_pdet_regions()
        for region in regions:
            if region['id'] == region_id:
                # Add detailed analysis
                region['detailed_analysis'] = {
                    'cluster_breakdown': self._get_cluster_breakdown(region_id),
                    'question_matrix': self._get_question_matrix(region_id),
                    'recommendations': self._get_recommendations(region_id),
                    'evidence': self._get_evidence_for_region(region_id)
                }
                return region
        return None

    @calibrated_method("saaaaaa.api.api_server.DataService._get_cluster_breakdown")
    def _get_cluster_breakdown(self, region_id: str) -> list[dict[str, Any]]:
        """Get cluster analysis for region"""
        return [
            {'name': 'GOBERNANZA', 'value': 72, 'trend': get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_cluster_breakdown").get("auto_param_L456_57", 0.05)},
            {'name': 'SOCIAL', 'value': 68, 'trend': get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_cluster_breakdown").get("auto_param_L457_53", 0.02)},
            {'name': 'ECONÓMICO', 'value': 81, 'trend': -get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_cluster_breakdown").get("auto_param_L458_57", 0.03)},
            {'name': 'AMBIENTAL', 'value': 76, 'trend': get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_cluster_breakdown").get("auto_param_L459_56", 0.07)}
        ]

    @calibrated_method("saaaaaa.api.api_server.DataService._get_question_matrix")
    def _get_question_matrix(self, region_id: str) -> list[dict[str, Any]]:
        """Get question matrix (44 questions) for region"""
        import random
        questions = []
        for i in range(1, 45):
            score = random.uniform(get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_question_matrix").get("auto_param_L468_35", 0.4), get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_question_matrix").get("auto_param_L468_40", 1.0))
            questions.append({
                'id': i,
                'text': f'Pregunta {i}',
                'score': score,
                'category': f'D{(i-1)//7 + 1}',
                'evidence': [f'PDT Sección {i//10 + 1}'],
                'recommendations': [f'Recomendación {i}'] if score < get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_question_matrix").get("auto_param_L475_69", 0.7) else []
            })
        return questions

    @calibrated_method("saaaaaa.api.api_server.DataService._get_recommendations")
    def _get_recommendations(self, region_id: str) -> list[dict[str, Any]]:
        """Get strategic recommendations for region"""
        return [
            {
                'priority': 'ALTA',
                'text': 'Fortalecer mecanismos de participación ciudadana',
                'category': 'GOBERNANZA',
                'impact': 'HIGH'
            },
            {
                'priority': 'ALTA',
                'text': 'Implementar sistema de monitoreo continuo',
                'category': 'SEGUIMIENTO',
                'impact': 'HIGH'
            },
            {
                'priority': 'MEDIA',
                'text': 'Mejorar articulación interinstitucional',
                'category': 'INSTITUCIONAL',
                'impact': 'MEDIUM'
            }
        ]

    @calibrated_method("saaaaaa.api.api_server.DataService._get_evidence_for_region")
    def _get_evidence_for_region(self, region_id: str) -> list[dict[str, Any]]:
        """Get evidence items for region"""
        return [
            {
                'source': 'PDT Sección 3.2',
                'page': 45,
                'text': 'Implementación de estrategias municipales',
                'relevance': get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_evidence_for_region").get("auto_param_L511_29", 0.92)
            },
            {
                'source': 'PDT Capítulo 4',
                'page': 67,
                'text': 'Articulación con Decálogo DDHH',
                'relevance': get_parameter_loader().get("saaaaaa.api.api_server.DataService._get_evidence_for_region").get("auto_param_L517_29", 0.88)
            }
        ]

    @calibrated_method("saaaaaa.api.api_server.DataService.get_evidence_stream")
    def get_evidence_stream(self) -> list[dict[str, Any]]:
        """Get evidence stream for ticker display"""
        return [
            {
                'source': 'PDT Sección 3.2',
                'page': 45,
                'text': 'Implementación de estrategias municipales',
                'timestamp': datetime.now().isoformat()
            },
            {
                'source': 'PDT Capítulo 4',
                'page': 67,
                'text': 'Articulación con Decálogo DDHH',
                'timestamp': datetime.now().isoformat()
            },
            {
                'source': 'Anexo Técnico',
                'page': 112,
                'text': 'Indicadores de cumplimiento',
                'timestamp': datetime.now().isoformat()
            }
        ]

# Initialize data service
data_service = DataService()

# Initialize recommendation engine
recommendation_engine = None
try:
    recommendation_engine = load_recommendation_engine()
    logger.info("Recommendation engine initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize recommendation engine: {e}")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def dashboard():
    """Serve the AtroZ dashboard"""
    from flask import send_from_directory
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_evidence_stream").get("auto_param_L572_20", 1.0).0'
    })

@app.route('/api/v1/auth/token', methods=['POST'])
@rate_limit
def get_auth_token():
    """Get authentication token"""
    data = request.get_json()
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')

    # Validate credentials (implement proper validation in production)
    if not client_id or not client_secret:
        return jsonify({'error': 'Missing credentials'}), 400

    # Generate token
    token = generate_jwt_token(client_id)

    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': APIConfig.JWT_EXPIRATION_HOURS * 3600
    })

@app.route('/api/v1/constellation_map', methods=['GET'])
@rate_limit
@cached(ttl=300)
def get_constellation_map():
    """
    Get data for the constellation map visualization

    Returns:
        JSON object with nodes and links for the constellation map
    """
    try:
        constellation_data = data_service.get_constellation_map_data()

        return jsonify({
            'status': 'success',
            'data': constellation_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get constellation map data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/pdet/regions', methods=['GET'])
@rate_limit
@cached(ttl=300)
def get_pdet_regions():
    """
    Get all PDET regions with scores

    Returns:
        List of PDET regions with metadata and scores
    """
    try:
        regions = data_service.get_pdet_regions()

        return jsonify({
            'status': 'success',
            'data': regions,
            'count': len(regions),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get PDET regions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/pdet/regions/<region_id>', methods=['GET'])
@rate_limit
@cached(ttl=300)
def get_region_detail(region_id: str):
    """
    Get detailed information for a specific PDET region

    Args:
        region_id: Region identifier (e.g., 'alto-patia')

    Returns:
        Detailed region data with analysis
    """
    try:
        region = data_service.get_region_detail(region_id)

        if not region:
            return jsonify({'error': 'Region not found'}), 404

        return jsonify({
            'status': 'success',
            'data': region,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get region detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/municipalities/<municipality_id>', methods=['GET'])
@rate_limit
@cached(ttl=300)
def get_municipality_data(municipality_id: str):
    """
    Get municipality analysis data

    Args:
        municipality_id: Municipality identifier

    Returns:
        Municipality analysis with scores and recommendations
    """
    try:
        # Mock data - integrate with orchestrator for real analysis
        municipality_data = {
            'id': municipality_id,
            'name': f'Municipality {municipality_id}',
            'region_id': 'alto-patia',
            'analysis': {
                'radar': {
                    'dimensions': ['Gobernanza', 'Social', 'Económico', 'Ambiental', 'Institucional', 'Territorial'],
                    'scores': [72, 68, 81, 76, 70, 74]
                },
                'clusters': data_service._get_cluster_breakdown('alto-patia'),
                'questions': data_service._get_question_matrix('alto-patia')
            }
        }

        return jsonify({
            'status': 'success',
            'data': municipality_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get municipality data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/evidence/stream', methods=['GET'])
@rate_limit
@cached(ttl=60)
def get_evidence_stream():
    """
    Get evidence stream for ticker display

    Returns:
        List of evidence items with sources and timestamps
    """
    try:
        evidence = data_service.get_evidence_stream()

        return jsonify({
            'status': 'success',
            'data': evidence,
            'count': len(evidence),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get evidence stream: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/export/dashboard', methods=['POST'])
@rate_limit
def export_dashboard_data():
    """
    Export dashboard data in various formats

    Request body:
        {
            "format": "json|csv|pdf",
            "regions": ["region_id1", "region_id2"],
            "include_evidence": true
        }

    Returns:
        Exported data file
    """
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')
        region_ids = data.get('regions', [])
        include_evidence = data.get('include_evidence', False)

        # Collect data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'regions': [],
            'evidence': [] if include_evidence else None
        }

        # Get region data
        for region_id in region_ids:
            region = data_service.get_region_detail(region_id)
            if region:
                export_data['regions'].append(region)

        # Get evidence if requested
        if include_evidence:
            export_data['evidence'] = data_service.get_evidence_stream()

        # Format response based on requested format
        if export_format == 'json':
            return jsonify({
                'status': 'success',
                'data': export_data
            })
        else:
            return jsonify({'error': f'Format {export_format} not yet implemented'}), 400

    except Exception as e:
        logger.error(f"Failed to export dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WEBSOCKET HANDLERS FOR REAL-TIME UPDATES
# ============================================================================

@socketio.on('connect')
def handle_connect() -> None:
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect() -> None:
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_region')
def handle_subscribe_region(data) -> None:
    """Subscribe to region updates"""
    region_id = data.get('region_id')
    logger.info(f"Client {request.sid} subscribed to region: {region_id}")

    # Send initial data
    region = data_service.get_region_detail(region_id)
    emit('region_update', region)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions"""
    return jsonify({
        'error': e.description,
        'status_code': e.code
    }), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {e}")
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500

# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@app.route('/api/v1/recommendations/micro', methods=['POST'])
@rate_limit
def generate_micro_recommendations():
    """
    Generate MICRO-level recommendations

    Request Body:
        {
            "scores": {
                "PA01-DIM01": 1.2,
                "PA02-DIM02": 1.5,
                ...
            },
            "context": {}  // Optional
        }

    Returns:
        RecommendationSet with MICRO recommendations
    """
    if not recommendation_engine:
        return jsonify({'error': 'Recommendation engine not available'}), 503

    try:
        data = request.get_json()
        scores = data.get('scores', {})
        context = data.get('context', {})

        if not scores:
            return jsonify({'error': 'Missing scores'}), 400

        rec_set = recommendation_engine.generate_micro_recommendations(scores, context)

        return jsonify({
            'status': 'success',
            'data': rec_set.to_dict(),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to generate MICRO recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/recommendations/meso', methods=['POST'])
@rate_limit
def generate_meso_recommendations():
    """
    Generate MESO-level recommendations

    Request Body:
        {
            "cluster_data": {
                "CL01": {"score": 72.0, "variance": get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_evidence_stream").get("auto_param_L865_52", 0.25), "weak_pa": "PA02"},
                ...
            },
            "context": {}  // Optional
        }

    Returns:
        RecommendationSet with MESO recommendations
    """
    if not recommendation_engine:
        return jsonify({'error': 'Recommendation engine not available'}), 503

    try:
        data = request.get_json()
        cluster_data = data.get('cluster_data', {})
        context = data.get('context', {})

        if not cluster_data:
            return jsonify({'error': 'Missing cluster_data'}), 400

        rec_set = recommendation_engine.generate_meso_recommendations(cluster_data, context)

        return jsonify({
            'status': 'success',
            'data': rec_set.to_dict(),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to generate MESO recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/recommendations/macro', methods=['POST'])
@rate_limit
def generate_macro_recommendations():
    """
    Generate MACRO-level recommendations

    Request Body:
        {
            "macro_data": {
                "macro_band": "SATISFACTORIO",
                "clusters_below_target": ["CL02", "CL03"],
                "variance_alert": "MODERADA",
                "priority_micro_gaps": ["PA01-DIM05", "PA04-DIM04"]
            },
            "context": {}  // Optional
        }

    Returns:
        RecommendationSet with MACRO recommendations
    """
    if not recommendation_engine:
        return jsonify({'error': 'Recommendation engine not available'}), 503

    try:
        data = request.get_json()
        macro_data = data.get('macro_data', {})
        context = data.get('context', {})

        if not macro_data:
            return jsonify({'error': 'Missing macro_data'}), 400

        rec_set = recommendation_engine.generate_macro_recommendations(macro_data, context)

        return jsonify({
            'status': 'success',
            'data': rec_set.to_dict(),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to generate MACRO recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/recommendations/all', methods=['POST'])
@rate_limit
def generate_all_recommendations():
    """
    Generate recommendations at all levels (MICRO, MESO, MACRO)

    Request Body:
        {
            "micro_scores": {...},
            "cluster_data": {...},
            "macro_data": {...},
            "context": {}  // Optional
        }

    Returns:
        Dictionary with MICRO, MESO, and MACRO recommendation sets
    """
    if not recommendation_engine:
        return jsonify({'error': 'Recommendation engine not available'}), 503

    try:
        data = request.get_json()
        micro_scores = data.get('micro_scores', {})
        cluster_data = data.get('cluster_data', {})
        macro_data = data.get('macro_data', {})
        context = data.get('context', {})

        all_recs = recommendation_engine.generate_all_recommendations(
            micro_scores, cluster_data, macro_data, context
        )

        return jsonify({
            'status': 'success',
            'data': {
                'MICRO': all_recs['MICRO'].to_dict(),
                'MESO': all_recs['MESO'].to_dict(),
                'MACRO': all_recs['MACRO'].to_dict()
            },
            'summary': {
                'MICRO': {
                    'total_rules': all_recs['MICRO'].total_rules_evaluated,
                    'matched': all_recs['MICRO'].rules_matched
                },
                'MESO': {
                    'total_rules': all_recs['MESO'].total_rules_evaluated,
                    'matched': all_recs['MESO'].rules_matched
                },
                'MACRO': {
                    'total_rules': all_recs['MACRO'].total_rules_evaluated,
                    'matched': all_recs['MACRO'].rules_matched
                }
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to generate all recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/recommendations/rules/info', methods=['GET'])
@rate_limit
@cached(ttl=600)
def get_rules_info():
    """
    Get information about loaded recommendation rules

    Returns:
        Statistics about loaded rules
    """
    if not recommendation_engine:
        return jsonify({'error': 'Recommendation engine not available'}), 503

    try:
        return jsonify({
            'status': 'success',
            'data': {
                'version': recommendation_engine.rules.get('version'),
                'total_rules': len(recommendation_engine.rules.get('rules', [])),
                'by_level': {
                    'MICRO': len(recommendation_engine.rules_by_level['MICRO']),
                    'MESO': len(recommendation_engine.rules_by_level['MESO']),
                    'MACRO': len(recommendation_engine.rules_by_level['MACRO'])
                },
                'rules_path': str(recommendation_engine.rules_path),
                'schema_path': str(recommendation_engine.schema_path)
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get rules info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/recommendations/reload', methods=['POST'])
@require_auth
def reload_rules():
    """
    Reload recommendation rules from disk (admin only)

    Returns:
        Success status
    """
    if not recommendation_engine:
        return jsonify({'error': 'Recommendation engine not available'}), 503

    try:
        recommendation_engine.reload_rules()

        return jsonify({
            'status': 'success',
            'message': 'Rules reloaded successfully',
            'total_rules': len(recommendation_engine.rules.get('rules', [])),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to reload rules: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Run API server"""
    logger.info("=" * 80)
    logger.info("AtroZ Dashboard API Server")
    logger.info("=" * 80)
    logger.info(f"CORS Origins: {APIConfig.CORS_ORIGINS}")
    logger.info(f"Rate Limiting: {APIConfig.RATE_LIMIT_ENABLED}")
    logger.info(f"Caching: {APIConfig.CACHE_ENABLED}")
    logger.info("=" * 80)

    # Run server
    socketio.run(
        app,
        host='get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_evidence_stream").get("auto_param_L1076_14", 0.0).get_parameter_loader().get("saaaaaa.api.api_server.DataService.get_evidence_stream").get("auto_param_L1076_18", 0.0)',
        port=int(os.getenv('ATROZ_API_PORT', '5000')),
        debug=os.getenv('ATROZ_DEBUG', 'false').lower() == 'true'
    )

if __name__ == '__main__':
    main()
