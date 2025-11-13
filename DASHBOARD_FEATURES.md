# AtroZ Dashboard Features & User Guide

## Overview

The AtroZ Dashboard is a visceral, data-rich visualization system for analyzing Colombian PDET (Programas de Desarrollo con Enfoque Territorial) municipal development plans. It provides multi-level analysis with real-time updates and comprehensive data exploration.

## Visual Design

### Color Scheme

The dashboard uses the AtroZ "visceral analysis" aesthetic:

- **Blood Red** (`#8B0000`): Critical alerts, low scores
- **Copper/Bronze** (`#B2642E`, `#17A589`): Medium scores, transitions
- **Electric Blue** (`#00D4FF`): Neural connections, data flows
- **Toxic Green** (`#39FF14`): High scores, positive indicators
- **Dark Background** (`#0A0A0A`): Canvas for visibility

### Animations

- **Organic Pulsing**: Background gradients that breathe
- **Particle Canvas**: Interactive floating particles respond to mouse
- **Neural Connections**: Animated lines connecting related regions
- **Glitch Effects**: Subtle cyberpunk-style text distortions
- **Floating Nodes**: PDET regions with 3D-like hover effects

## Main Interface

### 1. Header Bar

```
┌─────────────────────────────────────────────────┐
│ ATROZ  [CONSTELACIÓN] [MACRO] [MESO] [MICRO]  │
└─────────────────────────────────────────────────┘
```

**Navigation Pills**:
- **CONSTELACIÓN**: Overview of all 16 PDET regions
- **MACRO**: High-level strategic analysis
- **MESO**: Cluster-based analysis
- **MICRO**: Detailed 44-question breakdown

### 2. Constellation Map (Main View)

The primary visualization showing all PDET regions:

```
        🔷 ARAUCA (68)
                            🔷 CATATUMBO (61)
                                          🔷 SIERRA NEVADA (63)
    🔷 URABÁ (64)
           🔷 SUR CÓRDOBA (69)
    🔷 CHOCÓ (58)    🔷 BAJO CAUCA (65)
                            🔷 SUR BOLÍVAR (60)
                    🔷 MONTES DE MARÍA (74)
    
    🔷 PACÍFICO MEDIO (62)
           🔷 ALTO PATÍA (72)
                    🔷 SUR DEL TOLIMA (71)
                            🔷 CAGUÁN (70)
                                    🔷 MACARENA (66)
    
    🔷 PACÍFICO NARIÑO (59)
           🔷 PUTUMAYO (67)
```

**Features**:
- Each hexagonal node shows:
  - Region name (uppercase)
  - Overall score (0-100)
  - Color indicating performance (green >70, copper 60-70, red <60)
- Neural connections between related regions
- Hover for quick info
- Click for detailed analysis

### 3. Data Panel (Right Sidebar)

```
┌────────────────────────────┐
│ NIVEL MACRO                │
│ ┌────────────────────┐     │
│ │  Phylogram   87%   │     │
│ └────────────────────┘     │
│                            │
│ NIVEL MESO · CLUSTERS      │
│ ┌────────────────────┐     │
│ │ GOBERNANZA     72  │     │
│ │ SOCIAL         68  │     │
│ │ ECONÓMICO      81  │     │
│ │ AMBIENTAL      76  │     │
│ └────────────────────┘     │
│                            │
│ NIVEL MICRO · 44 PREGUNTAS│
│ ┌────────────────────┐     │
│ │   DNA Helix View   │     │
│ └────────────────────┘     │
│                            │
│ RECOMENDACIONES CRÍTICAS   │
│ ┌────────────────────┐     │
│ │ ⚠ ALTA: Fortalecer │     │
│ │   participación    │     │
│ └────────────────────┘     │
└────────────────────────────┘
```

**Sections**:
1. **Macro**: Overall system health score
2. **Meso**: 4 cluster scores with trends
3. **Micro**: 44-question DNA helix visualization
4. **Recommendations**: Critical action items

### 4. Evidence Stream (Bottom Ticker)

```
┌────────────────────────────────────────────────────┐
│ 🔴 PDT Sección 3.2 · Página 45 · "Implementación..."  │
│ 🔴 PDT Capítulo 4 · Página 67 · "Articulación..."     │
└────────────────────────────────────────────────────┘
```

Scrolling ticker showing:
- Document source (PDT sections)
- Page numbers
- Relevant quotes
- Updates in real-time

## Interactions

### Click on Region Node

Opens detailed modal with:

```
┌─────────────────────────────────────────────────┐
│ ALTO PATÍA · 24 MUNICIPIOS              [X]    │
├─────────────────────────────────────────────────┤
│                                                 │
│  ALINEACIÓN MACRO     CLUSTERS      44 PREGUNTAS│
│  ┌──────────────┐    ┌────────┐    ┌─────────┐ │
│  │ Radar Chart  │    │ Bars   │    │ Matrix  │ │
│  │              │    │ Gov 72 │    │ Q1  Q2  │ │
│  │   Hexagon    │    │ Soc 68 │    │ Q3  Q4  │ │
│  │   6 axes     │    │ Eco 81 │    │ ... ... │ │
│  │              │    │ Env 76 │    │ Q43 Q44 │ │
│  └──────────────┘    └────────┘    └─────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Content**:
1. **Radar Chart**: 6-dimension alignment analysis
2. **Cluster Bars**: Visual comparison of 4 clusters
3. **Question Matrix**: 44 questions in 7x7 grid, color-coded by score

### Hover Effects

- **Region nodes**: Glow effect, tooltip appears
- **Questions**: Score popup with category
- **Clusters**: Trend information
- **Evidence items**: Full text preview

### Right-Click (Radial Menu)

Context menu with options:
- 🔍 Drill Down
- ⇄ Compare
- 📊 Analyze
- 🌟 Highlight
- 📥 Export

## Control Panel (Left Side)

```
┌───┐
│ ⊕ │  Compare regions
├───┤
│ ↓ │  Export data
├───┤
│ ◈ │  Apply filters
├───┤
│ ⏱ │  Timeline view
├───┤
│ 🔍 │  Focus mode
└───┘
```

### Compare Mode

Select multiple regions to see side-by-side comparison:

```
┌────────────────────────┐
│ MATRIZ COMPARATIVA     │
├────────────────────────┤
│ Region A  |  Region B  │
│   72     vs    65      │
│                        │
│ Gov  68  |  Gov  62    │
│ Soc  74  |  Soc  66    │
│ Eco  70  |  Eco  64    │
│ Env  75  |  Env  68    │
└────────────────────────┘
```

### Export Options

Download data in multiple formats:
- **JSON**: Raw data for processing
- **CSV**: Spreadsheet-compatible
- **PDF**: Report format (future)

### Filter Panel

Apply filters to focus analysis:
- Score range: 0-100 slider
- Categories: Select specific clusters
- Time range: Historical view (if data available)

### Timeline View

```
┌────────────────────────────────┐
│ 2018 ─────●────── 2020 ─────●── 2022 ─────●── 2024 │
└────────────────────────────────┘
```

Scrub through time to see changes (future feature).

### Focus Mode

Dims all elements except selected region/cluster for concentrated analysis.

## Data Visualization Details

### Score Color Coding

```
90-100: Toxic Green (#39FF14)  🟢 Excelente
70-89:  Green-Blue  (#17A589)  🟢 Satisfactorio  
60-69:  Copper      (#B2642E)  🟡 Aceptable
40-59:  Orange-Red  (#C41E3A)  🟠 Deficiente
0-39:   Blood Red   (#8B0000)  🔴 Crítico
```

### PDET Regions

**16 Colombian PDET Territories**:

1. **Alto Patía y Norte del Cauca** (24 municipios) - 72 pts
2. **Arauca** (4 municipios) - 68 pts
3. **Bajo Cauca y Nordeste Antioqueño** (13 municipios) - 65 pts
4. **Catatumbo** (11 municipios) - 61 pts
5. **Chocó** (14 municipios) - 58 pts
6. **Cuenca del Caguán** (17 municipios) - 70 pts
7. **Macarena-Guaviare** (10 municipios) - 66 pts
8. **Montes de María** (15 municipios) - 74 pts
9. **Pacífico Medio** (4 municipios) - 62 pts
10. **Pacífico y Frontera Nariñense** (11 municipios) - 59 pts
11. **Putumayo** (11 municipios) - 67 pts
12. **Sierra Nevada** (10 municipios) - 63 pts
13. **Sur de Bolívar** (7 municipios) - 60 pts
14. **Sur de Córdoba** (5 municipios) - 69 pts
15. **Sur del Tolima** (4 municipios) - 71 pts
16. **Urabá Antioqueño** (10 municipios) - 64 pts

### Cluster Analysis (Meso Level)

Four main clusters:

1. **GOBERNANZA**: Democratic participation, institutional capacity
2. **SOCIAL**: Education, health, community development
3. **ECONÓMICO**: Infrastructure, employment, economic growth
4. **AMBIENTAL**: Environmental protection, sustainability

### 44-Question Breakdown (Micro Level)

Questions organized into 7 dimensions:
- **D1**: Participation (Questions 1-7)
- **D2**: Transparency (Questions 8-14)
- **D3**: Capacity (Questions 15-21)
- **D4**: Resources (Questions 22-28)
- **D5**: Impact (Questions 29-35)
- **D6**: Sustainability (Questions 36-42)
- **D7**: Innovation (Questions 43-44)

## Real-Time Features

### WebSocket Updates

When enabled, the dashboard receives live updates:
- Region score changes
- New evidence items
- Recommendation updates
- System alerts

**Indicator**: Green pulse in top-right corner when connected

### Auto-Refresh

Configurable automatic data refresh:
- Default: Every 60 seconds
- Cached data: 5-minute TTL
- Manual refresh: Click refresh button

### Notifications

Toast notifications appear for:
- ✅ Data loaded successfully
- ⚠️ Connection issues
- 🔄 Refresh completed
- 📊 Export ready

## Accessibility

### Keyboard Navigation

- `Tab`: Navigate between elements
- `Enter`: Activate selected element
- `Esc`: Close modals
- `Arrow keys`: Navigate in matrix views
- `Space`: Toggle selections
- `Ctrl+Z`: Undo last action

### Screen Reader Support

- All interactive elements have ARIA labels
- Status updates announced
- Data tables properly structured
- Alternative text for visualizations

### Color Blindness

- Not solely relying on color
- Patterns and icons used
- High contrast mode available
- Configurable color schemes

## Performance

### Optimizations

- **Canvas rendering**: 60 FPS animations
- **Lazy loading**: Detail modals load on demand
- **Debouncing**: Reduced API calls
- **Caching**: Local storage for recent data
- **Compression**: Gzip on static assets

### Browser Requirements

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

Older browsers may have degraded experience.

## Mobile Support

While optimized for desktop, mobile features include:

- Responsive layout (tablets 768px+)
- Touch gestures
- Simplified visualizations
- Bottom sheet modals
- Burger menu navigation

## Advanced Features

### State Management

- Undo/redo capability
- Session persistence
- Bookmark states
- Share links with state

### Custom Views

- Save favorite regions
- Custom dashboards
- Preset filters
- Scheduled reports

### Integration

- REST API for data access
- WebSocket for live updates
- Export to external tools
- Embed in other applications

## Getting Started

### First Time Users

1. **Explore**: Click around the constellation
2. **Learn**: Hover over elements for tooltips
3. **Analyze**: Click a region for details
4. **Compare**: Select multiple regions
5. **Export**: Download data for reports

### Power Users

1. **Keyboard shortcuts**: Speed up navigation
2. **Filters**: Create custom views
3. **API access**: Programmatic data retrieval
4. **Automation**: Schedule exports
5. **Integrations**: Connect to other tools

## Support & Documentation

- **Main guide**: `ATROZ_DASHBOARD_DEPLOYMENT.md`
- **API docs**: `/api/v1/` endpoints
- **GitHub**: Submit issues and feature requests
- **Community**: Join discussion forums

## Future Enhancements

Planned features:
- [ ] Historical data tracking
- [ ] Predictive analytics
- [ ] Custom report builder
- [ ] Multi-user collaboration
- [ ] Mobile app
- [ ] API rate limiting controls
- [ ] Advanced filtering
- [ ] Data export to Excel/PDF
- [ ] Email notifications
- [ ] Integration with GIS systems

---

**Ready to explore?** 🚀

Start your local server:
```bash
bash scripts/start_dashboard.sh
```

Or visit the deployed dashboard:
```
https://kkkkknhh.github.io/SAAAAAA/
```
