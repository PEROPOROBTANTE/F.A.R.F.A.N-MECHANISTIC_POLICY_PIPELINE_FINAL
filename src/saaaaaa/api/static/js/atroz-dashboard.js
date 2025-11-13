        const pdetRegions = [
            { id: 'alto-patia', name: 'ALTO PATÍA', x: 25, y: 20, municipalities: 24, score: 72 },
            { id: 'arauca', name: 'ARAUCA', x: 75, y: 15, municipalities: 4, score: 68 },
            { id: 'bajo-cauca', name: 'BAJO CAUCA', x: 45, y: 25, municipalities: 13, score: 65 },
            { id: 'catatumbo', name: 'CATATUMBO', x: 65, y: 20, municipalities: 11, score: 61 },
            { id: 'choco', name: 'CHOCÓ', x: 15, y: 35, municipalities: 14, score: 58 },
            { id: 'caguan', name: 'CAGUÁN', x: 55, y: 40, municipalities: 17, score: 70 },
            { id: 'macarena', name: 'MACARENA', x: 60, y: 55, municipalities: 10, score: 66 },
            { id: 'montes-maria', name: 'MONTES MARÍA', x: 40, y: 10, municipalities: 15, score: 74 },
            { id: 'pacifico-medio', name: 'PACÍFICO MEDIO', x: 10, y: 50, municipalities: 4, score: 62 },
            { id: 'pacifico-narinense', name: 'PACÍFICO NARIÑO', x: 5, y: 65, municipalities: 11, score: 59 },
            { id: 'putumayo', name: 'PUTUMAYO', x: 35, y: 70, municipalities: 11, score: 67 },
            { id: 'sierra-nevada', name: 'SIERRA NEVADA', x: 70, y: 5, municipalities: 10, score: 63 },
            { id: 'sur-bolivar', name: 'SUR BOLÍVAR', x: 50, y: 15, municipalities: 7, score: 60 },
            { id: 'sur-cordoba', name: 'SUR CÓRDOBA', x: 35, y: 15, municipalities: 5, score: 69 },
            { id: 'sur-tolima', name: 'SUR TOLIMA', x: 45, y: 45, municipalities: 4, score: 71 },
            { id: 'uraba', name: 'URABÁ', x: 20, y: 10, municipalities: 10, score: 64 }
        ];

        const dashboardState = {
            currentView: 'constellation',
            focusMode: false,
            selectedRegions: [],
            timelineYear: 2024,
            dataVersion: 1
        };

        function initParticles() {
            const canvas = document.getElementById('particle-canvas');
            const ctx = canvas.getContext('2d');
            let particles = [];
            
            function resizeCanvas() {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
            
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();
            
            for (let i = 0; i < 100; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    size: Math.random() * 2 + 1,
                    speedX: Math.random() * 0.5 - 0.25,
                    speedY: Math.random() * 0.5 - 0.25,
                    color: `rgba(${Math.random() * 100 + 155}, ${Math.random() * 50 + 50}, ${Math.random() * 100 + 155}, ${Math.random() * 0.3 + 0.1})`
                });
            }
            
            let mouseX = null;
            let mouseY = null;
            
            canvas.addEventListener('mousemove', (event) => {
                mouseX = event.x;
                mouseY = event.y;
                
                if (Math.random() > 0.7) {
                    particles.push({
                        x: mouseX,
                        y: mouseY,
                        size: Math.random() * 3 + 1,
                        speedX: Math.random() * 2 - 1,
                        speedY: Math.random() * 2 - 1,
                        color: `rgba(0, 212, 255, ${Math.random() * 0.5 + 0.2})`
                    });
                }
            });
            
            canvas.addEventListener('mouseleave', () => {
                mouseX = null;
                mouseY = null;
            });
            
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                for (let i = 0; i < particles.length; i++) {
                    let p = particles[i];
                    
                    p.x += p.speedX;
                    p.y += p.speedY;
                    
                    if (mouseX !== null && mouseY !== null) {
                        let dx = mouseX - p.x;
                        let dy = mouseY - p.y;
                        let distance = Math.sqrt(dx * dx + dy * dy);
                        
                        if (distance < 100) {
                            p.x += dx * 0.02;
                            p.y += dy * 0.02;
                        }
                    }
                    
                    if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
                    if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;
                    
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                    ctx.fillStyle = p.color;
                    ctx.fill();
                    
                    for (let j = i; j < particles.length; j++) {
                        let p2 = particles[j];
                        let dx = p.x - p2.x;
                        let dy = p.y - p2.y;
                        let distance = Math.sqrt(dx * dx + dy * dy);
                        
                        if (distance < 100) {
                            ctx.beginPath();
                            ctx.strokeStyle = `rgba(0, 212, 255, ${0.1 * (1 - distance/100)})`;
                            ctx.lineWidth = 0.5;
                            ctx.moveTo(p.x, p.y);
                            ctx.lineTo(p2.x, p2.y);
                            ctx.stroke();
                        }
                    }
                }
                
                if (particles.length > 150) {
                    particles = particles.filter(p => p.size > 0.5);
                }
                
                requestAnimationFrame(animate);
            }
            
            animate();
        }

        function initConstellation() {
            const container = document.getElementById('pdetNodes');
            const canvas = document.getElementById('neuralCanvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = container.parentElement.offsetWidth;
            canvas.height = container.parentElement.offsetHeight;
            
            drawNeuralConnections(ctx, canvas.width, canvas.height);
            
            pdetRegions.forEach((region, index) => {
                const node = createPDETNode(region, canvas.width, canvas.height);
                container.appendChild(node);
                
                setTimeout(() => {
                    node.style.opacity = '1';
                    node.style.transform = 'scale(1)';
                }, index * 100);
            });
        }

        function createPDETNode(region, containerWidth, containerHeight) {
            const node = document.createElement('div');
            node.className = 'pdet-node';
            node.style.left = `${region.x}%`;
            node.style.top = `${region.y}%`;
            node.style.opacity = '0';
            node.style.transform = 'scale(0)';
            node.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            node.setAttribute('data-region-id', region.id);
            
            const scoreColor = region.score > 70 ? 'var(--atroz-green-toxic)' : 
                              region.score > 60 ? 'var(--atroz-copper-oxide)' : 'var(--atroz-red-500)';
            
            node.innerHTML = `
                <div class="pdet-core">
                    <div class="pdet-hexagon"></div>
                    <div class="pdet-pulse"></div>
                    <div class="pdet-inner">
                        <div class="pdet-score" style="color: ${scoreColor}">${region.score}</div>
                        <div class="pdet-name">${region.name}</div>
                    </div>
                </div>
            `;
            
            node.addEventListener('click', () => openMunicipalityDetail(region));
            
            node.addEventListener('mousemove', (e) => {
                showTooltip(e, `${region.name}: ${region.score}% de alineación`);
            });
            
            node.addEventListener('mouseleave', () => {
                hideTooltip();
            });
            
            node.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                toggleRegionSelection(region.id);
                showRadialMenu(e);
            });
            
            return node;
        }

        function drawNeuralConnections(ctx, width, height) {
            ctx.strokeStyle = 'rgba(0, 212, 255, 0.1)';
            ctx.lineWidth = 0.5;
            
            pdetRegions.forEach((region1, i) => {
                pdetRegions.forEach((region2, j) => {
                    if (i < j && Math.random() > 0.7) {
                        ctx.beginPath();
                        ctx.moveTo(region1.x * width / 100, region1.y * height / 100);
                        ctx.lineTo(region2.x * width / 100, region2.y * height / 100);
                        ctx.stroke();
                    }
                });
            });
            
            animateNeuralFlow(ctx, width, height);
        }

        function animateNeuralFlow(ctx, width, height) {
            let particles = [];
            
            for (let i = 0; i < 20; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    size: Math.random() * 2
                });
            }
            
            function animate() {
                ctx.fillStyle = 'rgba(10, 10, 10, 0.05)';
                ctx.fillRect(0, 0, width, height);
                
                ctx.fillStyle = 'rgba(0, 212, 255, 0.5)';
                particles.forEach(p => {
                    p.x += p.vx;
                    p.y += p.vy;
                    
                    if (p.x < 0 || p.x > width) p.vx *= -1;
                    if (p.y < 0 || p.y > height) p.vy *= -1;
                    
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                    ctx.fill();
                });
                
                requestAnimationFrame(animate);
            }
            
            animate();
        }

        function createDNAHelix() {
            const helix = document.querySelector('.helix-strand');
            const numPoints = 44;
            
            for (let i = 0; i < numPoints; i++) {
                const angle = (i / numPoints) * Math.PI * 4;
                const y = (i / numPoints) * 100;
                const x1 = 50 + Math.cos(angle) * 40;
                const x2 = 50 - Math.cos(angle) * 40;
                
                const point1 = document.createElement('div');
                point1.className = 'helix-point';
                point1.style.left = `${x1}%`;
                point1.style.top = `${y}%`;
                helix.appendChild(point1);
                
                const point2 = document.createElement('div');
                point2.className = 'helix-point';
                point2.style.left = `${x2}%`;
                point2.style.top = `${y}%`;
                helix.appendChild(point2);
                
                if (i % 3 === 0) {
                    const connector = document.createElement('div');
                    connector.className = 'helix-connector';
                    connector.style.top = `${y}%`;
                    helix.appendChild(connector);
                }
                
                if (i % 5 === 0) {
                    const card = document.createElement('div');
                    card.className = 'question-card';
                    card.style.left = `${x1 + 5}%`;
                    card.style.top = `${y}%`;
                    card.innerHTML = `Q${i+1} <span class="q-score">${Math.floor(Math.random() * 40) + 60}</span>`;
                    card.addEventListener('click', () => {
                        highlightElement(card);
                    });
                    helix.appendChild(card);
                }
            }
        }

        function openMunicipalityDetail(region) {
            const overlay = document.getElementById('muniOverlay');
            const title = document.getElementById('overlayTitle');
            
            title.textContent = `${region.name} · ${region.municipalities} MUNICIPIOS`;
            
            const matrix = document.getElementById('questionMatrix');
            matrix.innerHTML = '';
            for (let i = 1; i <= 44; i++) {
                const cell = document.createElement('div');
                const score = Math.random();
                const color = score > 0.7 ? 'var(--atroz-green-toxic)' : 
                             score > 0.4 ? 'var(--atroz-copper-oxide)' : 'var(--atroz-red-500)';
                
                cell.style.cssText = `
                    width: 100%;
                    aspect-ratio: 1;
                    background: ${color};
                    opacity: ${score};
                    cursor: pointer;
                    transition: all 0.2s;
                `;
                
                cell.addEventListener('mouseenter', (e) => {
                    cell.style.transform = 'scale(1.5)';
                    cell.style.zIndex = '10';
                    showTooltip({clientX: e.clientX, clientY: e.clientY}, `Pregunta ${i}: ${Math.round(score * 100)}%`);
                });
                
                cell.addEventListener('mouseleave', () => {
                    cell.style.transform = 'scale(1)';
                    cell.style.zIndex = '1';
                    hideTooltip();
                });
                
                matrix.appendChild(cell);
            }
            
            const clusters = ['GOBERNANZA', 'SOCIAL', 'ECONÓMICO', 'AMBIENTAL'];
            const clusterBars = document.getElementById('clusterBars');
            clusterBars.innerHTML = '';
            
            clusters.forEach((cluster, i) => {
                const value = Math.floor(Math.random() * 40) + 60;
                const bar = document.createElement('div');
                bar.style.cssText = `
                    position: absolute;
                    bottom: 0;
                    left: ${i * 25}%;
                    width: 20%;
                    height: ${value}%;
                    background: linear-gradient(180deg, var(--atroz-blue-electric), transparent);
                    border: 1px solid var(--atroz-blue-electric);
                    transition: all 0.3s;
                `;
                
                const label = document.createElement('div');
                label.style.cssText = `
                    position: absolute;
                    bottom: -20px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 8px;
                    white-space: nowrap;
                `;
                label.textContent = cluster;
                
                bar.appendChild(label);
                clusterBars.appendChild(bar);
            });
            
            overlay.classList.add('active');
        }

        function closeMuniOverlay() {
            document.getElementById('muniOverlay').classList.remove('active');
        }

        function toggleComparison() {
            const matrix = document.getElementById('comparisonMatrix');
            matrix.classList.toggle('active');
            
            if (matrix.classList.contains('active')) {
                const grid = document.getElementById('matrixGrid');
                grid.innerHTML = '';
                
                for (let i = 0; i < 9; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'matrix-cell';
                    cell.textContent = Math.floor(Math.random() * 100);
                    grid.appendChild(cell);
                }
            }
        }

        function toggleTimeline() {
            const timeline = document.getElementById('timeline');
            timeline.classList.toggle('active');
        }

        function toggleFocusMode() {
            dashboardState.focusMode = !dashboardState.focusMode;
            document.body.classList.toggle('focus-mode');
            
            showNotification(dashboardState.focusMode ? 
                'Modo enfoque activado' : 'Modo enfoque desactivado');
        }

        function showTooltip(event, text) {
            const tooltip = document.getElementById('tooltip');
            tooltip.textContent = text;
            tooltip.style.left = `${event.clientX + 10}px`;
            tooltip.style.top = `${event.clientY + 10}px`;
            tooltip.classList.add('active');
        }

        function hideTooltip() {
            const tooltip = document.getElementById('tooltip');
            tooltip.classList.remove('active');
        }

        function showNotification(message) {
            const notification = document.getElementById('notification');
            const messageEl = document.getElementById('notificationMessage');
            
            messageEl.textContent = message;
            notification.classList.add('active');
            
            setTimeout(() => {
                notification.classList.remove('active');
            }, 3000);
        }

        function highlightElement(element) {
            document.querySelectorAll('.focused').forEach(el => {
                el.classList.remove('focused');
            });
            
            element.classList.add('focused');
            
            document.body.classList.add('focus-mode');
            dashboardState.focusMode = true;
        }

        function toggleRegionSelection(regionId) {
            const index = dashboardState.selectedRegions.indexOf(regionId);
            
            if (index === -1) {
                dashboardState.selectedRegions.push(regionId);
                document.querySelector(`[data-region-id="${regionId}"]`).classList.add('focused');
            } else {
                dashboardState.selectedRegions.splice(index, 1);
                document.querySelector(`[data-region-id="${regionId}"]`).classList.remove('focused');
            }
            
            showNotification(`${dashboardState.selectedRegions.length} regiones seleccionadas`);
        }

        function showRadialMenu(event) {
            const radialMenu = document.getElementById('radialMenu');
            radialMenu.style.left = `${event.clientX - 100}px`;
            radialMenu.style.top = `${event.clientY - 100}px`;
            radialMenu.classList.add('active');
            
            setTimeout(() => {
                document.addEventListener('click', closeRadialMenu);
            }, 10);
        }

        function closeRadialMenu() {
            const radialMenu = document.getElementById('radialMenu');
            radialMenu.classList.remove('active');
            document.removeEventListener('click', closeRadialMenu);
        }

        document.querySelectorAll('.nav-pill').forEach(pill => {
            pill.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-pill').forEach(p => p.classList.remove('active'));
                e.currentTarget.classList.add('active');
                
                const view = e.currentTarget.dataset.view;
                dashboardState.currentView = view;
                
                const loading = document.getElementById('loadingDNA');
                loading.classList.add('active');
                
                setTimeout(() => {
                    loading.classList.remove('active');
                }, 1000);
            });
        });

        window.addEventListener('DOMContentLoaded', () => {
            initParticles();
            initConstellation();
            createDNAHelix();
            
            document.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showRadialMenu(e);
            });
            
            document.querySelectorAll('.radial-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const action = e.currentTarget.dataset.action;
                    handleRadialAction(action);
                    closeRadialMenu();
                });
            });
        });

        function handleRadialAction(action) {
            switch(action) {
                case 'drillDown':
                    if (dashboardState.selectedRegions.length > 0) {
                        showNotification(`Analizando ${dashboardState.selectedRegions.length} regiones`);
                    } else {
                        showNotification('Seleccione al menos una región primero');
                    }
                    break;
                case 'compare':
                    toggleComparison();
                    break;
                case 'analyze':
                    showNotification('Iniciando análisis profundo...');
                    break;
                case 'highlight':
                    toggleFocusMode();
                    break;
                case 'export':
                    exportData();
                    break;
            }
        }

        function exportData() {
            const loading = document.getElementById('loadingDNA');
            loading.classList.add('active');
            
            setTimeout(() => {
                loading.classList.remove('active');
                showNotification('Datos exportados con éxito');
            }, 1500);
        }

        function toggleFilter() {
            showNotification('Filtros aplicados');
        }
