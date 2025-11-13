# 🎯 AtroZ Dashboard Integration - Complete Setup

**Visceral Analysis Interface for SAAAAAA Orchestrator**

---

## 🚀 Quick Start (60 seconds)

```bash
# 1. Run quick start script
./atroz_quickstart.sh dev

# 2. Open browser to http://localhost:8000

# 3. Start analyzing!
```

**That's it!** The script handles everything automatically.

---

## 📋 What You Get

### ✅ Complete Integration Stack

```
┌─────────────────────────────────────────┐
│  AtroZ Dashboard (Visceral UI)          │
│  • Neural particle system               │
│  • 16 PDET region hexagons              │
│  • Real-time evidence ticker            │
│  • Interactive radar/cluster charts     │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│  REST API Server (Flask)                │
│  • /api/v1/pdet/regions                 │
│  • /api/v1/municipalities/<id>          │
│  • /api/v1/evidence/stream              │
│  • WebSocket real-time updates          │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│  SAAAAAA Orchestrator                   │
│  • 584 analytical methods               │
│  • 300 question analysis (MICRO)        │
│  • Cluster synthesis (MESO)             │
│  • Overall convergence (MACRO)          │
└─────────────────────────────────────────┘
```

### 🎨 Dashboard Features

- **Constellation View**: Interactive map of 16 PDET regions
- **MACRO Level**: Executive summary with overall scores
- **MESO Level**: Cluster analysis (Gobernanza, Social, Económico, Ambiental)
- **MICRO Level**: Detailed 44-question matrix
- **Evidence Stream**: Live ticker showing document citations
- **Real-time Updates**: WebSocket-powered live data
- **Export Functionality**: Download analysis results

### 🔧 Backend Features

- **RESTful API**: Clean, documented endpoints
- **JWT Authentication**: Secure access control
- **Rate Limiting**: Protection against abuse
- **Intelligent Caching**: Fast response times
- **WebSocket Support**: Real-time push updates
- **Error Handling**: Robust error management

---

## 📁 File Structure

```
SAAAAAA/
├── api_server.py                           # Flask REST API server (NEW)
├── static/
│   ├── js/
│   │   ├── atroz-data-service.js          # Data access layer (NEW)
│   │   └── atroz-dashboard-integration.js  # Integration glue (NEW)
│   ├── css/
│   └── index.html                          # Dashboard UI (updated)
├── atroz_quickstart.sh                     # Quick start script (NEW)
├── requirements_atroz.txt                  # Python dependencies (NEW)
├── ATROZ_INTEGRATION_GUIDE.md             # Detailed guide (NEW)
├── README_ATROZ_INTEGRATION.md            # This file (NEW)
├── orchestrator.py                         # Existing orchestrator
├── choreographer.py                        # Existing choreographer
└── [existing SAAAAAA files...]
```

---

## 🛠️ Manual Setup (if needed)

### Prerequisites

```bash
# Python 3.10 or higher
python3 --version

# pip
pip --version
```

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements_atroz.txt

# Or install individually:
pip install flask flask-cors flask-socketio pyjwt pyyaml python-dotenv
```

### Step 2: Configure Environment

Create `.env` file:

```bash
cat > .env << EOF
ATROZ_API_PORT=5000
ATROZ_API_SECRET=your-secret-key
ATROZ_JWT_SECRET=your-jwt-secret
ATROZ_DEBUG=true
ATROZ_CORS_ORIGINS=http://localhost:8000
ATROZ_RATE_LIMIT=false
ATROZ_CACHE_ENABLED=true
ATROZ_ENABLE_REALTIME=true
EOF
```

### Step 3: Update Dashboard HTML

Add these lines to `static/index.html` before `</body>`:

```html
<!-- Socket.IO for WebSocket -->
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<!-- AtroZ Integration -->
<script src="/static/js/atroz-data-service.js"></script>
<script src="/static/js/atroz-dashboard-integration.js"></script>

<!-- Configuration -->
<script>
    window.ATROZ_API_URL = 'http://localhost:5000';
    window.ATROZ_ENABLE_REALTIME = 'true';
</script>
```

### Step 4: Start Servers

```bash
# Terminal 1: API Server
python api_server.py

# Terminal 2: Static File Server
python -m http.server 8000 --directory static
```

### Step 5: Access Dashboard

Open browser to: http://localhost:8000

---

## 🔌 API Endpoints

### Health Check

```bash
curl http://localhost:5000/api/v1/health
```

### Get PDET Regions

```bash
curl http://localhost:5000/api/v1/pdet/regions
```

### Get Region Detail

```bash
curl http://localhost:5000/api/v1/pdet/regions/alto-patia
```

### Get Municipality Data

```bash
curl http://localhost:5000/api/v1/municipalities/12345
```

### Get Evidence Stream

```bash
curl http://localhost:5000/api/v1/evidence/stream
```

### Export Data

```bash
curl -X POST http://localhost:5000/api/v1/export/dashboard \
  -H "Content-Type: application/json" \
  -d '{"format": "json", "regions": ["alto-patia"]}'
```

---

## 💻 Frontend API Usage

### Access Global Objects

```javascript
// Integration manager
const integration = window.atrozDashboard;

// Data service
const dataService = window.atrozDataService;

// State manager
const stateManager = window.atrozStateManager;
```

### Fetch Data

```javascript
// Get all PDET regions
const regions = await dataService.fetchPDETRegions();

// Get region detail
const detail = await dataService.fetchRegionDetail('alto-patia');

// Get municipality data
const municipality = await dataService.fetchMunicipalityData('12345');

// Get evidence stream
const evidence = await dataService.fetchEvidenceStream();
```

### Manage State

```javascript
// Update state
stateManager.updateState({
  currentView: 'constellation',
  selectedRegions: new Set(['alto-patia', 'arauca'])
});

// Subscribe to changes
stateManager.subscribe((prevState, newState) => {
  console.log('State changed:', newState);
});

// Get current state
const state = stateManager.getState();
```

### Real-time Updates

```javascript
// Subscribe to region updates
dataService.subscribeToRegion('alto-patia', (updatedData) => {
  console.log('Region updated:', updatedData);
});
```

### Export Data

```javascript
// Export selected regions
await integration.exportData({
  format: 'json',
  regions: ['alto-patia', 'arauca'],
  includeEvidence: true
});
```

---

## 🎮 Dashboard Controls

### Navigation Pills

- **CONSTELACIÓN**: Overview of all 16 PDET regions
- **MACRO**: Executive-level aggregation
- **MESO**: Cluster-level analysis
- **MICRO**: Detailed 44-question breakdown

### Control Interface (Left Side)

- **⊕ Compare**: Compare multiple regions
- **↓ Export**: Download analysis data
- **◈ Filter**: Apply filters to data
- **⏱ Timeline**: View historical data
- **🔍 Focus**: Enter focus mode

### Interaction

- **Click region**: Open detailed modal
- **Right-click region**: Radial context menu
- **Hover**: View tooltips
- **Drag timeline**: Scrub through time

---

## 🔍 Customization

### Configure API URL

```javascript
// In static/index.html
window.ATROZ_API_URL = 'https://your-api-server.com';
```

### Disable Real-time Updates

```javascript
window.ATROZ_ENABLE_REALTIME = 'false';
```

### Enable Authentication

```javascript
window.ATROZ_ENABLE_AUTH = 'true';
window.ATROZ_CLIENT_ID = 'your-client-id';
window.ATROZ_CLIENT_SECRET = 'your-secret';
```

### Adjust Cache Timeout

```javascript
window.ATROZ_CACHE_TIMEOUT = '600000'; // 10 minutes
```

---

## 🚦 Production Deployment

### Option 1: Gunicorn + Nginx

```bash
# Install production server
pip install gunicorn gevent-websocket

# Run with gunicorn
gunicorn --worker-class gevent -w 4 -b 0.0.0.0:5000 api_server:app

# Configure nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/static;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Option 2: Docker

```bash
# Build image
docker build -t atroz-dashboard .

# Run container
docker run -p 5000:5000 \
  -e ATROZ_API_SECRET=production-secret \
  atroz-dashboard
```

### Option 3: Cloud Platform

Deploy to:
- **Heroku**: `heroku create && git push heroku main`
- **AWS**: Use Elastic Beanstalk or ECS
- **Google Cloud**: Use Cloud Run or App Engine
- **Azure**: Use App Service

---

## 🐛 Troubleshooting

### API Server Won't Start

```bash
# Check if port is in use
lsof -i :5000

# Kill existing process
kill $(lsof -t -i:5000)

# Try different port
ATROZ_API_PORT=5001 python api_server.py
```

### CORS Errors in Browser

```bash
# Update CORS origins
export ATROZ_CORS_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"

# Restart API server
```

### WebSocket Connection Failed

```javascript
// Disable WebSocket in browser console
window.ATROZ_ENABLE_REALTIME = 'false';
location.reload();
```

### Data Not Loading

```bash
# Check API server logs
tail -f logs/api_server.log

# Test API endpoints
curl http://localhost:5000/api/v1/health

# Check browser console for errors
# Open DevTools > Console
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements_atroz.txt --force-reinstall

# Verify imports
python -c "from api_server import app; print('OK')"
```

---

## 📊 Monitoring

### View Logs

```bash
# API server
tail -f logs/api_server.log

# Static server
tail -f logs/static_server.log

# Both
tail -f logs/*.log
```

### Check Server Status

```bash
# API server
curl http://localhost:5000/api/v1/health

# Static server
curl http://localhost:8000/
```

### Monitor Performance

```javascript
// In browser console
console.log('Cache stats:', atrozDataService.cache.size);
console.log('State version:', atrozStateManager.getState().dataVersion);
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run API tests
pytest tests/test_api.py -v

# Test specific endpoint
curl -v http://localhost:5000/api/v1/pdet/regions
```

### Frontend Tests

```javascript
// In browser console

// Test data service
const regions = await atrozDataService.fetchPDETRegions();
console.log('Regions:', regions);

// Test state manager
atrozStateManager.updateState({ currentView: 'macro' });
console.log('State:', atrozStateManager.getState());
```

---

## 📚 Documentation

- **Detailed Guide**: [`ATROZ_INTEGRATION_GUIDE.md`](ATROZ_INTEGRATION_GUIDE.md)
- **API Reference**: See guide for complete endpoint documentation
- **Frontend API**: See guide for JavaScript API reference
- **Architecture**: See guide for system architecture details

---

## 🤝 Support

### Common Tasks

**Stop servers:**
```bash
./stop_atroz.sh
# OR
kill $(cat logs/*.pid)
```

**Restart servers:**
```bash
./stop_atroz.sh
./atroz_quickstart.sh dev
```

**Clear cache:**
```bash
rm -rf cache/*
```

**View running processes:**
```bash
ps aux | grep python
```

---

## ✨ Features Roadmap

- [ ] Database integration for persistent storage
- [ ] User authentication and authorization
- [ ] Multi-language support (EN/ES)
- [ ] Advanced filtering and search
- [ ] PDF report generation
- [ ] Email notifications
- [ ] Scheduled analysis runs
- [ ] Mobile responsive design
- [ ] PWA (Progressive Web App) support

---

## 🎉 Success!

If you see this, you're ready to go:

```
===============================================
  AtroZ Dashboard is RUNNING!
===============================================

  Dashboard:    http://localhost:8000
  API:          http://localhost:5000/api/v1/health

  To stop:
    ./stop_atroz.sh
===============================================
```

**Enjoy analyzing Colombian Municipal Development Plans with visceral precision! 🎯**

---

**Last Updated:** 2025-10-22  
**Version:** 1.0.0  
**Maintainer:** Integration Team
