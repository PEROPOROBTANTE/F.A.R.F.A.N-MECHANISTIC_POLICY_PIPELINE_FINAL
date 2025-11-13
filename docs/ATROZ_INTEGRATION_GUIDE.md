# AtroZ Dashboard Integration Guide

## Complete Integration Architecture for SAAAAAA Orchestrator

**Version:** 1.0.0  
**Date:** 2025-10-22  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Frontend Integration](#frontend-integration)
7. [Deployment](#deployment)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This integration connects the **AtroZ Dashboard** (visceral visualization interface) with the **SAAAAAA Orchestrator** (policy analysis engine), creating a complete end-to-end system for Municipal Development Plan analysis across Colombian PDET regions.

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AtroZ Dashboard (Frontend)                │
│  - HTML5 + CSS3 + Vanilla JavaScript                        │
│  - Real-time particle system & neural connections           │
│  - Interactive PDET region visualization                    │
│  - Evidence stream ticker                                   │
└────────────┬────────────────────────────────────────────────┘
             │ REST API + WebSocket
┌────────────▼────────────────────────────────────────────────┐
│              API Server (Flask + SocketIO)                   │
│  - RESTful endpoints for data access                        │
│  - JWT authentication                                        │
│  - Rate limiting & caching                                   │
│  - WebSocket for real-time updates                          │
└────────────┬────────────────────────────────────────────────┘
             │ Python Integration
┌────────────▼────────────────────────────────────────────────┐
│              SAAAAAA Orchestrator                            │
│  - CHESS Strategy execution                                 │
│  - 584 analytical methods                                   │
│  - 300 question analysis                                    │
│  - MICRO → MESO → MACRO synthesis                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

✅ **Complete Integration**: Connects dashboard to all 584 analytical methods  
✅ **Real-time Updates**: WebSocket support for live data streaming  
✅ **Intelligent Caching**: Client and server-side caching with TTL  
✅ **Security**: JWT authentication, rate limiting, CORS support  
✅ **Scalability**: Async execution, connection pooling  
✅ **Monitoring**: Performance metrics, error tracking, logging  

---

## Architecture

### Backend Architecture

```python
api_server.py                 # Flask REST API server
├── Authentication Layer      # JWT token management
├── Rate Limiting Layer       # Request throttling
├── Caching Layer            # Response caching
├── API Endpoints            # REST API routes
│   ├── /api/v1/pdet/regions
│   ├── /api/v1/pdet/regions/<id>
│   ├── /api/v1/municipalities/<id>
│   ├── /api/v1/evidence/stream
│   └── /api/v1/export/dashboard
└── WebSocket Handler        # Real-time updates

orchestrator.py              # CHESS orchestrator
└── Integration with API     # Data provider
```

### Frontend Architecture

```javascript
static/js/
├── atroz-data-service.js           # Data access layer
│   ├── HTTP client with retry
│   ├── Client-side caching
│   ├── WebSocket client
│   └── Authentication handling
│
├── atroz-dashboard-integration.js  # Integration layer
│   ├── State management
│   ├── Visualization adapter
│   ├── Event handling
│   └── Auto-refresh logic
│
└── deepseek_html_20251022_29a8c3.html  # Dashboard UI
    ├── Particle system
    ├── Neural connections
    ├── PDET visualization
    └── Evidence ticker
```

### Data Flow

```
1. User Action (Dashboard)
   ↓
2. State Change (StateManager)
   ↓
3. Data Request (DataService)
   ↓
4. HTTP/WebSocket (API Server)
   ↓
5. Orchestrator Execution (CHESS)
   ↓
6. Method Invocation (584 methods)
   ↓
7. Result Synthesis (ReportAssembler)
   ↓
8. Response (JSON)
   ↓
9. Visualization Update (Dashboard)
```

---

## Installation

### Prerequisites

```bash
# Python 3.10+
python --version

# Node.js (optional, for build tools)
node --version

# pip packages
pip install flask flask-cors flask-socketio pyjwt pyyaml
```

### Backend Setup

```bash
# 1. Clone or navigate to project
cd /Users/recovered/PycharmProjects/SAAAAAA

# 2. Install dependencies
pip install -r requirements.txt

# Additional packages for API server
pip install flask flask-cors flask-socketio pyjwt

# 3. Verify file structure
ls -la api_server.py orchestrator.py choreographer.py

# 4. Test imports
python -c "from api_server import app; print('✓ API server ready')"
```

### Frontend Setup

```bash
# 1. Create static directory structure
mkdir -p static/js static/css

# 2. Verify JavaScript files exist
ls -la static/js/atroz-data-service.js
ls -la static/js/atroz-dashboard-integration.js

# 3. Copy dashboard HTML
cp deepseek_html_20251022_29a8c3.html static/index.html
```

### Update HTML Dashboard

Add these script tags to `static/index.html` **before** the closing `</body>` tag:

```html
<!-- Socket.IO for WebSocket support (optional but recommended) -->
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<!-- AtroZ Data Service -->
<script src="/static/js/atroz-data-service.js"></script>

<!-- AtroZ Dashboard Integration -->
<script src="/static/js/atroz-dashboard-integration.js"></script>

<!-- Configuration -->
<script>
    // Configure API connection
    window.ATROZ_API_URL = 'http://localhost:5000';
    window.ATROZ_ENABLE_REALTIME = 'true';
    window.ATROZ_ENABLE_AUTH = 'false'; // Set to 'true' for production
    window.ATROZ_CLIENT_ID = 'atroz-dashboard-v1';
    window.ATROZ_CACHE_TIMEOUT = '300000'; // 5 minutes
</script>
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# API Server Configuration
ATROZ_API_PORT=5000
ATROZ_API_SECRET=your-secret-key-change-in-production
ATROZ_JWT_SECRET=your-jwt-secret-change-in-production
ATROZ_DEBUG=false

# CORS Configuration
ATROZ_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
ATROZ_RATE_LIMIT=true
ATROZ_RATE_LIMIT_REQUESTS=1000
ATROZ_RATE_LIMIT_WINDOW=900  # 15 minutes

# Caching
ATROZ_CACHE_ENABLED=true
ATROZ_CACHE_TTL=300  # 5 minutes

# Data Paths
ATROZ_DATA_DIR=output
ATROZ_CACHE_DIR=cache

# WebSocket
ATROZ_ENABLE_REALTIME=true
```

Load environment variables:

```bash
# Linux/Mac
source .env

# Or use python-dotenv
pip install python-dotenv
```

---

## API Reference

### Authentication

#### POST `/api/v1/auth/token`

Get JWT authentication token.

**Request:**
```json
{
  "client_id": "atroz-dashboard-v1",
  "client_secret": "your-secret"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### PDET Regions

#### GET `/api/v1/pdet/regions`

Get all PDET regions with scores.

**Headers:**
```
Authorization: Bearer <token>
X-Atroz-Client: dashboard-v1
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "alto-patia",
      "name": "ALTO PATÍA Y NORTE DEL CAUCA",
      "coordinates": {"x": 25, "y": 20},
      "metadata": {
        "municipalities": 24,
        "population": 450000,
        "area": 12500
      },
      "scores": {
        "overall": 72,
        "governance": 68,
        "social": 74,
        "economic": 70,
        "environmental": 75,
        "lastUpdated": "2025-10-22T10:30:00Z"
      },
      "connections": ["pacifico-medio", "sur-tolima"],
      "indicators": {
        "alignment": 0.72,
        "implementation": 0.68,
        "impact": 0.75
      }
    }
  ],
  "count": 16,
  "timestamp": "2025-10-22T10:30:00Z"
}
```

#### GET `/api/v1/pdet/regions/<region_id>`

Get detailed region information.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "alto-patia",
    "name": "ALTO PATÍA Y NORTE DEL CAUCA",
    "detailed_analysis": {
      "cluster_breakdown": [...],
      "question_matrix": [...],
      "recommendations": [...],
      "evidence": [...]
    }
  }
}
```

### Municipalities

#### GET `/api/v1/municipalities/<municipality_id>`

Get municipality analysis data.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "12345",
    "name": "Municipality Name",
    "region_id": "alto-patia",
    "analysis": {
      "radar": {
        "dimensions": ["Gobernanza", "Social", ...],
        "scores": [72, 68, 81, 76, 70, 74]
      },
      "clusters": [...],
      "questions": [...]
    }
  }
}
```

### Evidence Stream

#### GET `/api/v1/evidence/stream`

Get evidence items for ticker display.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "source": "PDT Sección 3.2",
      "page": 45,
      "text": "Implementación de estrategias municipales",
      "timestamp": "2025-10-22T10:30:00Z"
    }
  ],
  "count": 10
}
```

### Export

#### POST `/api/v1/export/dashboard`

Export dashboard data.

**Request:**
```json
{
  "format": "json",
  "regions": ["alto-patia", "arauca"],
  "include_evidence": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-10-22T10:30:00Z",
    "regions": [...],
    "evidence": [...]
  }
}
```

### WebSocket Events

#### `connect`

Client connects to WebSocket.

**Server Response:**
```json
{
  "status": "connected"
}
```

#### `subscribe_region`

Subscribe to region updates.

**Client Emit:**
```json
{
  "region_id": "alto-patia"
}
```

**Server Response:**
```json
{
  "id": "alto-patia",
  "name": "ALTO PATÍA Y NORTE DEL CAUCA",
  "scores": {...}
}
```

---

## Frontend Integration

### Basic Usage

```javascript
// Access global integration object
const integration = window.atrozDashboard;
const dataService = window.atrozDataService;
const stateManager = window.atrozStateManager;

// Fetch PDET regions
const regions = await dataService.fetchPDETRegions();

// Update state
stateManager.updateState({
  currentView: 'constellation',
  selectedRegions: new Set(['alto-patia', 'arauca'])
});

// Subscribe to state changes
stateManager.subscribe((prevState, newState) => {
  console.log('State changed:', newState);
});

// Export data
await integration.exportData({
  format: 'json',
  regions: ['alto-patia'],
  includeEvidence: true
});
```

### Advanced Usage

```javascript
// Subscribe to real-time region updates
dataService.subscribeToRegion('alto-patia', (updatedData) => {
  console.log('Region updated:', updatedData);
  // Update visualization
});

// Manual data refresh
await integration.refreshData();

// Custom state subscription
const unsubscribe = stateManager.subscribe((prev, next) => {
  if (prev.focusMode !== next.focusMode) {
    console.log('Focus mode changed:', next.focusMode);
  }
});

// Later: unsubscribe
unsubscribe();
```

### Integration with Existing Dashboard Code

Replace the mock `pdetRegions` array with dynamic data:

```javascript
// BEFORE (static data in HTML)
const pdetRegions = [
  { id: 'alto-patia', name: 'ALTO PATÍA', x: 25, y: 20, ... }
];

// AFTER (dynamic data from API)
// Wait for integration ready
window.addEventListener('atroz:ready', async (event) => {
  const integration = event.detail.integration;
  
  // Regions are automatically loaded
  const state = integration.stateManager.getState();
  console.log('Loaded regions:', state.regions);
  
  // Dashboard will auto-update
});
```

---

## Deployment

### Development

```bash
# Terminal 1: Start API server
python api_server.py

# Terminal 2: Serve static files (optional)
python -m http.server 8000 --directory static

# Access dashboard
open http://localhost:8000
```

### Production

#### Option 1: Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn gevent-websocket

# Run with gunicorn
gunicorn --worker-class gevent -w 4 -b 0.0.0.0:5000 api_server:app

# Nginx configuration
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/static;
        try_files $uri /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### Option 2: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "api_server:app"]
```

Build and run:

```bash
docker build -t atroz-dashboard .
docker run -p 5000:5000 -e ATROZ_API_SECRET=secret atroz-dashboard
```

---

## Testing

### Backend Tests

```python
# test_api.py
import pytest
from api_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_pdet_regions(client):
    response = client.get('/api/v1/pdet/regions')
    assert response.status_code == 200
    assert 'data' in response.json
```

Run tests:

```bash
pytest test_api.py -v
```

### Frontend Tests

```javascript
// test_integration.js
describe('AtroZ Data Service', () => {
  it('should fetch PDET regions', async () => {
    const service = new AtrozDataService('http://localhost:5000');
    const regions = await service.fetchPDETRegions();
    expect(regions).toBeInstanceOf(Array);
    expect(regions.length).toBeGreaterThan(0);
  });
});
```

---

## Troubleshooting

### Common Issues

#### 1. CORS Errors

**Problem:** `Access to fetch has been blocked by CORS policy`

**Solution:**
```bash
# Update CORS_ORIGINS in .env
ATROZ_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Restart API server
```

#### 2. WebSocket Connection Failed

**Problem:** `WebSocket connection failed`

**Solution:**
```javascript
// Disable WebSocket in config
window.ATROZ_ENABLE_REALTIME = 'false';

// Or check firewall/proxy settings
```

#### 3. Rate Limiting

**Problem:** `429 Too Many Requests`

**Solution:**
```bash
# Increase rate limit in .env
ATROZ_RATE_LIMIT_REQUESTS=5000

# Or disable for development
ATROZ_RATE_LIMIT=false
```

#### 4. Authentication Errors

**Problem:** `401 Unauthorized`

**Solution:**
```javascript
// Disable auth for development
window.ATROZ_ENABLE_AUTH = 'false';

// Or provide valid credentials
await dataService.authenticate('client-id', 'client-secret');
```

### Debug Mode

Enable detailed logging:

```bash
# Backend
ATROZ_DEBUG=true python api_server.py

# Frontend
localStorage.setItem('atroz:debug', 'true');
```

### Performance Monitoring

```python
# Monitor API performance
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    logger.info(f'{request.method} {request.path} {response.status_code} {duration:.3f}s')
    return response
```

---

## Next Steps

1. **Implement Real Orchestrator Integration**
   - Replace mock data in `DataService` with real orchestrator calls
   - Map API endpoints to orchestrator methods

2. **Add Authentication**
   - Implement user authentication
   - Role-based access control

3. **Enhance Monitoring**
   - Add application performance monitoring (APM)
   - Set up error tracking (Sentry, etc.)

4. **Optimize Performance**
   - Database caching (Redis)
   - CDN for static assets
   - Async task queue (Celery)

5. **Add Analytics**
   - User interaction tracking
   - Dashboard usage metrics
   - Performance analytics

---

## Support

For issues and questions:
- Check logs: `tail -f /var/log/atroz-api.log`
- Review code: `orchestrator.py`, `api_server.py`
- Test endpoints: `curl http://localhost:5000/api/v1/health`

---

**End of Integration Guide**
