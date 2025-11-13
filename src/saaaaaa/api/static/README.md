# AtroZ Dashboard - Static Files

This directory contains the static files for the AtroZ Municipal Analysis Dashboard.

## Structure

```
static/
├── index.html              # Main dashboard HTML
├── css/
│   └── atroz-dashboard.css # Dashboard styles
├── js/
│   ├── atroz-dashboard.js        # Main dashboard JavaScript
│   ├── atroz-data-service.js     # Data fetching and caching
│   └── atroz-dashboard-integration.js  # API integration
├── assets/                 # Images, icons, etc.
└── README.md              # This file
```

## Features

### Visual Design
- **Color Scheme**: Based on AtroZ visceral aesthetic
  - Blood red (#8B0000), copper tones, electric blue (#00D4FF)
  - Toxic green (#39FF14) for positive indicators
- **Animations**: Organic pulsing, neural connections, particle effects
- **Layout**: Constellation view, macro/meso/micro levels
- **Interactive**: Hover effects, click-to-drill-down, radial menus

### Data Visualization
- **PDET Regions**: 16 Colombian PDET regions displayed as hexagonal nodes
- **Score Display**: Color-coded scoring (green >70, copper 60-70, red <60)
- **Neural Connections**: Dynamic connection lines between related regions
- **Evidence Stream**: Scrolling ticker with document references
- **Detail Modal**: Radar charts, cluster analysis, 44-question matrix

### Real-Time Features
- **WebSocket Support**: Live data updates from backend
- **Auto-Refresh**: Configurable refresh intervals
- **Cache Management**: Client-side caching with TTL
- **State Management**: Undo/redo capability

## Configuration

The dashboard can be configured via window variables in `index.html`:

```javascript
window.ATROZ_API_URL = 'http://localhost:5000';  // Backend API URL
window.ATROZ_ENABLE_REALTIME = true;             // Enable WebSocket
window.ATROZ_ENABLE_AUTH = false;                // Enable authentication
window.ATROZ_CACHE_TIMEOUT = 300000;             // Cache TTL (5 minutes)
window.ATROZ_REFRESH_INTERVAL = 60000;           // Auto-refresh (1 minute)
```

## Development

### Local Testing

1. Start the API server:
```bash
python src/saaaaaa/api/api_server.py
```

2. Open browser to `http://localhost:5000/`

### Standalone Mode

The dashboard can run standalone (without backend) using mock data:

```bash
cd src/saaaaaa/api/static
python -m http.server 8000
```

Open `http://localhost:8000/` in browser.

## Deployment

### GitHub Pages

The dashboard is automatically deployed to GitHub Pages via GitHub Actions:

1. Push changes to `main` branch
2. GitHub Actions workflow builds and deploys
3. Access at: `https://<username>.github.io/<repository>/`

### Backend API

For full functionality, deploy the backend API server:

```bash
# Install dependencies
pip install flask flask-cors flask-socketio pyjwt

# Run server
python src/saaaaaa/api/api_server.py
```

Environment variables:
- `ATROZ_API_PORT`: Port for API server (default: 5000)
- `ATROZ_API_SECRET`: Secret key for sessions
- `ATROZ_JWT_SECRET`: Secret for JWT tokens
- `ATROZ_CORS_ORIGINS`: Allowed CORS origins
- `ATROZ_DEBUG`: Enable debug mode (true/false)

## API Integration

The dashboard integrates with the backend API via REST and WebSocket:

### REST Endpoints
- `GET /api/v1/pdet/regions` - Get all PDET regions
- `GET /api/v1/pdet/regions/<id>` - Get region detail
- `GET /api/v1/municipalities/<id>` - Get municipality data
- `GET /api/v1/evidence/stream` - Get evidence stream
- `POST /api/v1/export/dashboard` - Export data

### WebSocket Events
- `connect` - Connection established
- `subscribe_region` - Subscribe to region updates
- `region_update` - Receive region data updates

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Particle canvas uses requestAnimationFrame
- SVG animations use CSS transforms
- Lazy loading for detail modals
- Debounced resize handlers
- Client-side caching reduces API calls

## Accessibility

- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Color contrast meets WCAG AA standards
- Screen reader compatible

## Credits

- Design: AtroZ Visceral Analysis System
- Data: Colombian PDET (Programas de Desarrollo con Enfoque Territorial)
- Framework: Vanilla JavaScript (no framework dependencies)
- Icons: Unicode symbols
- Fonts: JetBrains Mono

## License

See main repository LICENSE file.
