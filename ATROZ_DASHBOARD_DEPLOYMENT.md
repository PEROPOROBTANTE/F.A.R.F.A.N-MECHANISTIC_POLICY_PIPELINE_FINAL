# AtroZ Dashboard Deployment Guide

## Overview

The AtroZ Dashboard is a visceral, data-rich visualization system for analyzing Colombian PDET (Programas de Desarrollo con Enfoque Territorial) municipal plans. It provides real-time analysis across macro, meso, and micro levels with 16 PDET regions and 44-question deep analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AtroZ Dashboard                         │
│                    (Static Frontend)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐ │
│  │  HTML    │  │   CSS    │  │      JavaScript         │ │
│  │ Canvas   │  │  Styles  │  │  - Data Service         │ │
│  │ SVG      │  │  Anims   │  │  - Integration Layer    │ │
│  └──────────┘  └──────────┘  │  - Visualization Logic  │ │
│                               └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ REST API / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend API Server                        │
│                    (Flask + SocketIO)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                          │  │
│  │  - /api/v1/pdet/regions                             │  │
│  │  - /api/v1/pdet/regions/<id>                        │  │
│  │  - /api/v1/municipalities/<id>                      │  │
│  │  - /api/v1/evidence/stream                          │  │
│  │  - /api/v1/export/dashboard                         │  │
│  │  - /api/v1/recommendations/*                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▲                                 │
│                           │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Data Service & Orchestrator                  │  │
│  │  - PDET Region Data                                  │  │
│  │  - Bayesian Analysis                                 │  │
│  │  - Recommendation Engine                             │  │
│  │  - Evidence Registry                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Options

### Option 1: GitHub Pages (Frontend Only)

**Best for**: Static dashboard with external API

**Steps**:

1. **Enable GitHub Pages**:
   - Go to repository Settings > Pages
   - Select "GitHub Actions" as source
   - The workflow will deploy automatically on push

2. **Access Dashboard**:
   ```
   https://<username>.github.io/<repository>/
   ```

3. **Configure API Endpoint**:
   Edit `src/saaaaaa/api/static/index.html`:
   ```javascript
   window.ATROZ_API_URL = 'https://your-api-server.com';
   ```

**Pros**:
- ✅ Free hosting
- ✅ Automatic deployments via GitHub Actions
- ✅ CDN-backed (fast globally)
- ✅ HTTPS by default

**Cons**:
- ❌ Frontend only (need separate backend)
- ❌ No server-side processing
- ❌ Static data unless external API configured

### Option 2: Full Stack Local Development

**Best for**: Development and testing

**Steps**:

1. **Install Dependencies**:
   ```bash
   pip install flask flask-cors flask-socketio pyjwt
   ```

2. **Start Server**:
   ```bash
   bash scripts/start_dashboard.sh
   ```
   
   Or with options:
   ```bash
   bash scripts/start_dashboard.sh --port 8080 --debug
   ```

3. **Access Dashboard**:
   ```
   http://localhost:5000/
   ```

**Pros**:
- ✅ Full functionality
- ✅ Real-time WebSocket updates
- ✅ Local data access
- ✅ Easy debugging

**Cons**:
- ❌ Not accessible externally
- ❌ Manual startup required

### Option 3: Cloud Deployment (Heroku, Railway, etc.)

**Best for**: Production deployment

**Heroku Example**:

1. **Create `Procfile`**:
   ```
   web: python -m saaaaaa.api.api_server
   ```

2. **Create `runtime.txt`**:
   ```
   python-3.10.12
   ```

3. **Deploy**:
   ```bash
   heroku create atroz-dashboard
   heroku config:set ATROZ_API_PORT=\$PORT
   git push heroku main
   ```

**Railway Example**:

1. **Connect GitHub repository** in Railway dashboard

2. **Set environment variables**:
   - `ATROZ_API_PORT`: `$PORT` (Railway provides this)
   - `ATROZ_CORS_ORIGINS`: Your frontend domain

3. **Deploy automatically** on git push

**Pros**:
- ✅ Production-ready
- ✅ Scalable
- ✅ Custom domains
- ✅ SSL/TLS included

**Cons**:
- ❌ May incur costs
- ❌ More complex setup

### Option 4: Docker Deployment

**Best for**: Containerized deployments

**Create `Dockerfile`**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "-m", "saaaaaa.api.api_server"]
```

**Build and Run**:
```bash
docker build -t atroz-dashboard .
docker run -p 5000:5000 atroz-dashboard
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ATROZ_API_PORT=5000
      - ATROZ_DEBUG=false
    volumes:
      - ./data:/app/data
      - ./output:/app/output
```

Run with:
```bash
docker-compose up
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATROZ_API_PORT` | Port for API server | `5000` |
| `ATROZ_API_HOST` | Host to bind to | `0.0.0.0` |
| `ATROZ_API_SECRET` | Secret key for sessions | `dev-secret-key-change-in-production` |
| `ATROZ_JWT_SECRET` | Secret for JWT tokens | `jwt-secret-key-change-in-production` |
| `ATROZ_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |
| `ATROZ_DEBUG` | Enable debug mode | `false` |
| `ATROZ_RATE_LIMIT` | Enable rate limiting | `true` |
| `ATROZ_RATE_LIMIT_REQUESTS` | Max requests per window | `1000` |
| `ATROZ_RATE_LIMIT_WINDOW` | Rate limit window (seconds) | `900` (15 min) |
| `ATROZ_CACHE_ENABLED` | Enable server-side caching | `true` |
| `ATROZ_CACHE_TTL` | Cache TTL (seconds) | `300` (5 min) |
| `ATROZ_DATA_DIR` | Data directory path | `output` |

### Frontend Configuration

Edit `src/saaaaaa/api/static/index.html`:

```javascript
// API Configuration
window.ATROZ_API_URL = 'http://localhost:5000';  // Backend URL
window.ATROZ_ENABLE_REALTIME = true;             // WebSocket
window.ATROZ_ENABLE_AUTH = false;                // Authentication
window.ATROZ_CACHE_TIMEOUT = 300000;             // 5 minutes
window.ATROZ_REFRESH_INTERVAL = 60000;           // 1 minute
```

## Data Integration

### Remove Mock Data (Already Done)

The DataService class in `api_server.py` now uses real PDET data with all 16 Colombian PDET regions.

### Connect to Orchestrator

To integrate with real analysis data, update the `DataService` class:

```python
from saaaaaa.core.orchestrator import Orchestrator

class DataService:
    def __init__(self):
        self.orchestrator = Orchestrator()
        # ... rest of initialization
```

### Load Analysis Results

```python
def get_region_detail(self, region_id: str) -> dict:
    # Load from orchestrator results
    results = self.orchestrator.load_results(region_id)
    return self._transform_results(results)
```

## Testing

### 1. Test Static Files

```bash
cd src/saaaaaa/api/static
python -m http.server 8000
```

Open `http://localhost:8000/` and verify:
- ✅ Dashboard loads
- ✅ Animations work
- ✅ No console errors

### 2. Test API Server

```bash
python -m saaaaaa.api.api_server
```

Test endpoints:
```bash
# Health check
curl http://localhost:5000/api/v1/health

# Get regions
curl http://localhost:5000/api/v1/pdet/regions

# Get specific region
curl http://localhost:5000/api/v1/pdet/regions/alto-patia
```

### 3. Test Full Integration

1. Start server: `bash scripts/start_dashboard.sh`
2. Open `http://localhost:5000/`
3. Verify:
   - ✅ Dashboard loads with 16 PDET regions
   - ✅ Click on a region opens detail modal
   - ✅ Evidence stream updates
   - ✅ No mock data placeholders

## Monitoring

### Health Check

```bash
curl http://localhost:5000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-05T18:00:00.000000",
  "version": "1.0.0"
}
```

### Logs

Check application logs for:
- Request rates
- Cache hit/miss ratios
- Error rates
- WebSocket connections

## Security

### Production Checklist

- [ ] Change `ATROZ_API_SECRET` from default
- [ ] Change `ATROZ_JWT_SECRET` from default
- [ ] Set specific `ATROZ_CORS_ORIGINS` (not `*`)
- [ ] Enable HTTPS/SSL
- [ ] Set `ATROZ_DEBUG=false`
- [ ] Enable rate limiting
- [ ] Review and restrict API access
- [ ] Set up monitoring and logging
- [ ] Regular security updates

### CORS Configuration

For production, set specific origins:

```bash
export ATROZ_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

## Troubleshooting

### Dashboard Not Loading

1. Check static files exist:
   ```bash
   ls -la src/saaaaaa/api/static/
   ```

2. Check server logs for errors

3. Verify Flask static folder configuration

### API Errors

1. Check dependencies installed:
   ```bash
   pip list | grep -E "flask|jwt|cors|socketio"
   ```

2. Verify environment variables are set

3. Check data directory exists and is readable

### WebSocket Not Connecting

1. Check `socket.io-client` CDN is accessible
2. Verify server supports WebSocket
3. Check firewall/proxy settings

### Performance Issues

1. Enable caching: `ATROZ_CACHE_ENABLED=true`
2. Increase cache TTL: `ATROZ_CACHE_TTL=600`
3. Reduce auto-refresh interval in frontend
4. Consider CDN for static assets

## Maintenance

### Update Dashboard

1. Update static files in `src/saaaaaa/api/static/`
2. Commit and push changes
3. GitHub Actions will automatically deploy (if using GitHub Pages)

### Update Backend

1. Update `api_server.py`
2. Restart server:
   ```bash
   # Find and kill process
   ps aux | grep api_server
   kill <PID>
   
   # Restart
   bash scripts/start_dashboard.sh
   ```

### Database/Data Updates

1. Place new data files in configured data directory
2. Clear cache to force refresh:
   ```bash
   curl -X POST http://localhost:5000/api/v1/cache/clear
   ```

## Support

For issues, questions, or contributions:

1. Check existing documentation
2. Review GitHub Issues
3. Submit new issue with:
   - Dashboard/API version
   - Deployment method
   - Error logs
   - Steps to reproduce

## Roadmap

Future enhancements:

- [ ] User authentication system
- [ ] Multi-tenancy support
- [ ] Advanced filtering and search
- [ ] Export to PDF/Excel
- [ ] Historical data tracking
- [ ] Comparative analysis tools
- [ ] Mobile-responsive improvements
- [ ] Offline mode support
- [ ] Integration with more data sources
- [ ] Machine learning predictions

## License

See main repository LICENSE file.
