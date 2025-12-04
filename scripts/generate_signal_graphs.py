
import svgwrite
import math

def get_hexagon_points(x, y, size=80):
    """Calculates the points for a hexagon centered at (x, y)."""
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        points.append((x + size * math.cos(angle_rad), y + size * math.sin(angle_rad)))
    return points

def create_visualization_1_anatomy():
    """Generates the Signal Ecosystem visualization with AtroZ aesthetics."""
    dwg = svgwrite.Drawing('1_signal_ecosystem_anatomy.html', size=('1600px', '1200px'), profile='full')
    dwg.attribs['style'] = 'background-color: #0A0A0A;'
    colors = {
        'core_fill': '#04101A', 'core_stroke': '#00D4FF',
        'intel_fill': '#102F56', 'intel_stroke': '#B2642E',
        'elim_fill': '#3A0E0E', 'elim_stroke': '#7A0F0F',
        'text_color': '#E5E7EB', 'glow_color': '#39FF14'
    }
    font_family = "JetBrains Mono, monospace"
    dwg.defs.add(dwg.style("@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;400&display=swap');"))
    bg_gradient = dwg.defs.add(dwg.radialGradient())
    bg_gradient.add_stop_color(0, '#04101A', opacity=0.9)
    bg_gradient.add_stop_color(1, '#0A0A0A', opacity=0)
    dwg.add(dwg.rect(size=('100%', '100%'), fill=bg_gradient.get_paint_server()))
    decay_pattern = dwg.defs.add(dwg.pattern(size=(10, 10), patternUnits="userSpaceOnUse"))
    decay_pattern.add(dwg.rect(size=('100%', '100%'), fill=colors['elim_fill']))
    decay_pattern.add(dwg.line((0, 10), (10, 0), stroke='#000', stroke_width=1))
    decay_pattern.add(dwg.line((0, 5), (10, 5), stroke=colors['elim_stroke'], stroke_width=0.5, opacity=0.5))
    modules = {
        'core': {
            'files': ["signals.py", "signal_registry.py", "signal_loader.py", "signal_consumption.py"],
            'positions': [(700, 450), (900, 450), (700, 650), (900, 650)]
        },
        'integrate': {
            'files': ["signal_intelligence_layer.py", "signal_semantic_expander.py", "signal_contract_validator.py", "signal_evidence_extractor.py", "signal_context_scoper.py"],
        },
        'consider': {
            'files': ["signal_calibration_gate.py", "signal_quality_metrics.py"]
        },
        'eliminate': {
            'files': ["signal_aliasing.py", "signal_cache_invalidation.py", "signal_fallback_fusion.py", "signal_evidence_extractor_v1_legacy.py", "signal_evidence_extractor.py.bak"]
        }
    }
    core_pos = modules['core']['positions']
    for i in range(len(core_pos)):
        for j in range(i + 1, len(core_pos)):
            dwg.add(dwg.line(core_pos[i], core_pos[j], stroke=colors['core_stroke'], stroke_width=2.5, opacity=0.8))
    for i, file in enumerate(modules['core']['files']):
        x, y = core_pos[i]
        is_deprecated = file == "signal_loader.py"
        stroke_color = '#C41E3A' if is_deprecated else colors['core_stroke']

        hexagon = dwg.polygon(get_hexagon_points(x, y), fill=colors['core_fill'], stroke=stroke_color, stroke_width=3)
        dwg.add(hexagon)
        dwg.add(dwg.text(file, insert=(x, y + 5), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="11px"))
        if is_deprecated:
             dwg.add(dwg.text("[DEPRECATED]", insert=(x, y + 20), text_anchor="middle", fill='#C41E3A', font_family=font_family, font_size="9px"))
    def draw_peripheral_group(files, angle_start, angle_end, radius, fill, stroke):
        num_files = len(files)
        for i, file in enumerate(files):
            angle = angle_start + (i / (num_files -1 if num_files > 1 else 1)) * (angle_end - angle_start)
            x = 800 + radius * math.cos(angle)
            y = 550 + radius * math.sin(angle)
            hexagon = dwg.polygon(get_hexagon_points(x, y, size=70), fill=fill, stroke=stroke, stroke_width=1.5, opacity=0.6)
            dwg.add(hexagon)
            dwg.add(dwg.text(file, insert=(x, y + 5), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="10px", opacity=0.8))
            core_connection_point = min(core_pos, key=lambda p: math.hypot(p[0]-x, p[1]-y))
            dwg.add(dwg.line(core_connection_point, (x,y), stroke=colors['intel_stroke'], stroke_width=0.5, stroke_dasharray="4 4"))
    draw_peripheral_group(modules['integrate']['files'], -0.8, 0.8, 450, colors['intel_fill'], colors['intel_stroke'])
    draw_peripheral_group(modules['consider']['files'], 2.5, 3.0, 400, colors['intel_fill'], colors['intel_stroke'])
    draw_peripheral_group(modules['eliminate']['files'], 3.5, 5.0, 500, decay_pattern.get_paint_server(), colors['elim_stroke'])
    dwg.add(dwg.text("SIGNAL ECOSYSTEM: COMPLETE ANATOMY", insert=(800, 50), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="24px", style="letter-spacing: 8px; text-transform: uppercase;"))
    dwg.add(dwg.text("CORE OPERATIONAL", insert=(800, 750), text_anchor="middle", fill=colors['core_stroke'], font_family=font_family, font_size="14px", style="letter-spacing: 4px;"))
    dwg.add(dwg.text("PERIPHERAL INTELLIGENCE (DORMANT)", insert=(800, 100), text_anchor="middle", fill=colors['intel_stroke'], font_family=font_family, font_size="14px", style="letter-spacing: 4px;"))
    dwg.save()

def create_visualization_2_core():
    """Generates the CORE visualization with AtroZ aesthetics."""
    dwg = svgwrite.Drawing('2_signal_core_mechanisms.html', size=('1600px', '1200px'), profile='full')
    dwg.attribs['style'] = 'background-color: #0A0A0A;'
    colors = {
        'core_fill': '#04101A', 'core_stroke': '#00D4FF', 'deprecated_stroke': '#C41E3A',
        'text_color': '#E5E7EB', 'glow_color': '#39FF14', 'data_flow_color': '#BFEFCB'
    }
    font_family = "JetBrains Mono, monospace"
    dwg.defs.add(dwg.style("""
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;400&display=swap');
        .module-text { font-family: 'JetBrains Mono', monospace; font-size: 14px; fill: #E5E7EB; text-anchor: middle; }
        .sub-text { font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: #B2642E; text-anchor: middle; }
        .tooltip { font-family: 'JetBrains Mono', monospace; font-size: 12px; fill: #39FF14; visibility: hidden; }
        .hexagon:hover .tooltip { visibility: visible; }
    """))
    bg_gradient = dwg.defs.add(dwg.radialGradient())
    bg_gradient.add_stop_color(0, '#102F56', opacity=0.8)
    bg_gradient.add_stop_color(1, '#0A0A0A', opacity=0.1)
    dwg.add(dwg.rect(size=('100%', '100%'), fill=bg_gradient.get_paint_server()))
    data_flow_animation = dwg.defs.add(svgwrite.animate.Animate('stroke-dashoffset', dur='3s', repeatCount='indefinite', from_='20', to='0'))
    core_modules = {
        "signals.py": {'pos': (400, 600), 'desc': "Defines base types: SignalPack, SignalClient.", 'size': 120},
        "signal_registry.py": {'pos': (800, 300), 'desc': "Modern, Phase-2 registry for specialized signal packs.", 'size': 120},
        "signal_consumption.py": {'pos': (800, 900), 'desc': "Cryptographic tracking of signal usage via Merkle Trees.", 'size': 120},
        "signal_loader.py": {'pos': (1200, 600), 'desc': "LEGACY: Phase-1 loader, superficial data extraction.", 'size': 120}
    }
    connections = [
        ("signals.py", "signal_registry.py"),
        ("signals.py", "signal_consumption.py"),
        ("signal_registry.py", "signal_loader.py"),
        ("signal_consumption.py", "signal_loader.py")
    ]
    for start_mod, end_mod in connections:
        start_pos = core_modules[start_mod]['pos']
        end_pos = core_modules[end_mod]['pos']
        line = dwg.line(start_pos, end_pos, stroke=colors['core_stroke'], stroke_width=1.5, stroke_dasharray="10 5")
        line.add(data_flow_animation)
        dwg.add(line)
    for name, data in core_modules.items():
        x, y, size = data['pos'][0], data['pos'][1], data['size']
        is_deprecated = name == "signal_loader.py"
        stroke_color = colors['deprecated_stroke'] if is_deprecated else colors['core_stroke']
        g = dwg.g(class_='hexagon')
        g.add(dwg.polygon(get_hexagon_points(x, y, size=size), fill=colors['core_fill'], stroke=stroke_color, stroke_width=4))
        g.add(dwg.text(name, insert=(x, y - 10), class_='module-text'))
        if name == 'signal_consumption.py':
            g.add(dwg.circle((x-30, y+20), r=10, fill='#17A589'))
            g.add(dwg.text("Merkle Tree", insert=(x-30, y+45), class_='sub-text'))
        tooltip = dwg.text(data['desc'], insert=(x, y + size + 20), class_='tooltip')
        g.add(tooltip)
        dwg.add(g)
    dwg.add(dwg.text("THE CORE: THE BEATING HEART", insert=(800, 50), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="24px", style="letter-spacing: 8px; text-transform: uppercase;"))
    dwg.add(dwg.text("Forensic view of operational signal modules", insert=(800, 80), text_anchor="middle", fill=colors['core_stroke'], font_family=font_family, font_size="14px", style="letter-spacing: 4px;"))
    dwg.save()

def create_visualization_3_pathology():
    """Generates the INTELLIGENCE pathology visualization."""
    dwg = svgwrite.Drawing('3_signal_intelligence_pathology.html', size=('1600px', '1200px'), profile='full')
    dwg.attribs['style'] = 'background-color: #0A0A0A;'
    colors = {
        'intel_fill': '#102F56', 'intel_stroke': '#B2642E',
        'elim_fill': '#3A0E0E', 'elim_stroke': '#7A0F0F',
        'consider_fill': '#1D2A3A', 'consider_stroke': '#7B3F1D',
        'text_color': '#E5E7EB', 'spark_color': '#FFD700'
    }
    font_family = "JetBrains Mono, monospace"
    dwg.defs.add(dwg.style("@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;400&display=swap');"))
    bg_gradient = dwg.defs.add(dwg.radialGradient())
    bg_gradient.add_stop_color(0, '#3A0E0E', opacity=0.5)
    bg_gradient.add_stop_color(1, '#0A0A0A', opacity=0.1)
    dwg.add(dwg.rect(size=('100%', '100%'), fill=bg_gradient.get_paint_server()))
    decay_pattern = dwg.defs.add(dwg.pattern(size=(8, 8), patternUnits="userSpaceOnUse", id="decay"))
    decay_pattern.add(dwg.rect(size=('100%', '100%'), fill=colors['elim_fill']))
    decay_pattern.add(dwg.line((0, 8), (8, 0), stroke='#000', stroke_width=0.5))
    spark_animation = dwg.defs.add(svgwrite.animate.Animate('r', dur='0.1s', repeatCount='indefinite', values=['1', '3', '1']))
    modules = {
        'integrate': ["signal_semantic_expander.py", "signal_contract_validator.py", "signal_evidence_extractor.py", "signal_context_scoper.py"],
        'consider': ["signal_calibration_gate.py", "signal_quality_metrics.py"],
        'eliminate': ["signal_aliasing.py", "signal_cache_invalidation.py", "signal_fallback_fusion.py", "signal_evidence_extractor_v1_legacy.py", "signal_evidence_extractor.py.bak"]
    }
    intelligence_hub = "signal_intelligence_layer.py"
    hub_pos = (800, 250)
    hub_hex = dwg.polygon(get_hexagon_points(hub_pos[0], hub_pos[1], size=100), fill=colors['intel_fill'], stroke=colors['spark_color'], stroke_width=2)
    dwg.add(hub_hex)
    dwg.add(dwg.text(intelligence_hub, insert=hub_pos, text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="12px"))
    def draw_group(files, start_x, y, fill, stroke, title):
        dwg.add(dwg.text(title, insert=(start_x + 150, y - 80), text_anchor="middle", fill=stroke, font_family=font_family, font_size="14px", style="letter-spacing: 3px;"))
        for i, file in enumerate(files):
            x = start_x + (i % 2) * 200
            current_y = y + (i // 2) * 120
            if title == "ELIMINATE":
                 points = get_hexagon_points(x, current_y, size=60)
                 points[2] = (points[2][0] + 10, points[2][1] - 10)
                 hexagon = dwg.polygon(points, fill=decay_pattern.get_paint_server(), stroke=stroke, stroke_width=1)
            else:
                 hexagon = dwg.polygon(get_hexagon_points(x, current_y, size=60), fill=fill, stroke=stroke, stroke_width=1.5)
            dwg.add(hexagon)
            dwg.add(dwg.text(file, insert=(x, current_y), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="9px"))
            end_point = (x, current_y - 60)
            line = dwg.line(hub_pos, end_point, stroke=colors['intel_stroke'], stroke_width=1, stroke_dasharray="5 5")
            dwg.add(line)
            spark = dwg.circle(end_point, r=2, fill=colors['spark_color'])
            spark.add(spark_animation)
            dwg.add(spark)
    draw_group(modules['integrate'], 200, 600, colors['intel_fill'], colors['intel_stroke'], "INTEGRATE")
    draw_group(modules['consider'], 700, 600, colors['consider_fill'], colors['consider_stroke'], "CONSIDER")
    draw_group(modules['eliminate'], 1100, 500, 'url(#decay)', colors['elim_stroke'], "ELIMINATE")
    dwg.add(dwg.text("THE INTELLIGENCE LAYER: A GHOST IN THE MACHINE", insert=(800, 50), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="24px", style="letter-spacing: 8px; text-transform: uppercase;"))
    dwg.add(dwg.text("Pathology report of non-integrated modules", insert=(800, 80), text_anchor="middle", fill=colors['intel_stroke'], font_family=font_family, font_size="14px", style="letter-spacing: 4px;"))
    dwg.save()

def create_visualization_4_journey():
    """Generates the Signal's Journey visualization."""
    dwg = svgwrite.Drawing('4_signal_forensic_trace.html', size=('1600px', '1200px'), profile='full')
    dwg.attribs['style'] = 'background-color: #0A0A0A;'
    colors = {
        'path_stroke': '#B2642E', 'stage_fill': '#102F56', 'stage_stroke': '#00D4FF',
        'ghost_stroke': '#7B3F1D', 'text_color': '#E5E7EB', 'signal_particle': '#39FF14'
    }
    font_family = "JetBrains Mono, monospace"
    dwg.defs.add(dwg.style("@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;400&display=swap');"))
    bg_gradient = dwg.defs.add(dwg.radialGradient())
    bg_gradient.add_stop_color(0, '#04101A', opacity=0.9)
    bg_gradient.add_stop_color(1, '#0A0A0A', opacity=0.1)
    dwg.add(dwg.rect(size=('100%', '100%'), fill=bg_gradient.get_paint_server()))
    path_d = "M 200,600 C 400,600 400,300 600,300 S 800,0 1000,300 C 1200,600 1200,900 1400,900"
    journey_path = dwg.path(d=path_d, stroke=colors['path_stroke'], stroke_width=2, fill='none', stroke_dasharray="10 5")
    dwg.add(journey_path)
    stages = {
        "1. Monolith Extraction": {'pos': (200, 600), 'size': 70},
        "2. Registry & Caching": {'pos': (600, 300), 'size': 70},
        "3. Cryptographic Proof": {'pos': (1000, 300), 'size': 70},
        "4. Dormant Intelligence": {'pos': (1400, 900), 'size': 70}
    }
    for name, data in stages.items():
        x, y, size = data['pos'][0], data['pos'][1], data['size']
        dwg.add(dwg.polygon(get_hexagon_points(x, y, size=size), fill=colors['stage_fill'], stroke=colors['stage_stroke'], stroke_width=3))
        dwg.add(dwg.text(name, insert=(x, y - size - 10), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="12px"))
    ghost_pos = stages["4. Dormant Intelligence"]['pos']
    ghost_processes = ["Semantic Expansion", "Contract Validation", "Evidence Extraction"]
    for i, process in enumerate(ghost_processes):
        offset_x = ghost_pos[0] + 150
        offset_y = ghost_pos[1] - 50 + i * 50
        dwg.add(dwg.line((ghost_pos[0] + 70, ghost_pos[1]), (offset_x, offset_y), stroke=colors['ghost_stroke'], stroke_width=1, stroke_dasharray="2 2"))
        dwg.add(dwg.rect((offset_x, offset_y - 15), (150, 30), fill='none', stroke=colors['ghost_stroke'], stroke_width=0.5))
        dwg.add(dwg.text(process + " (Unrealized)", insert=(offset_x + 75, offset_y + 5), text_anchor="middle", fill=colors['ghost_stroke'], font_family=font_family, font_size="10px"))
    signal_particle = dwg.circle(r=8, fill=colors['signal_particle'])
    glow_filter = dwg.defs.add(dwg.filter())
    glow_filter.feGaussianBlur(in_='SourceGraphic', stdDeviation=3)
    signal_particle['filter'] = glow_filter.get_funciri()
    animation = svgwrite.animate.AnimateMotion(path=path_d, dur="10s", repeatCount="indefinite", rotate="auto")
    signal_particle.add(animation)
    dwg.add(signal_particle)
    dwg.add(dwg.text("THE SIGNAL'S JOURNEY: A FORENSIC TRACE", insert=(800, 50), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="24px", style="letter-spacing: 8px; text-transform: uppercase;"))
    dwg.add(dwg.text("Lifecycle of a single pattern from source to dormant potential", insert=(800, 80), text_anchor="middle", fill=colors['path_stroke'], font_family=font_family, font_size="14px", style="letter-spacing: 4px;"))
    dwg.save()

def create_visualization_5_blueprint():
    """Generates the Surgical Blueprint visualization."""
    dwg = svgwrite.Drawing('5_signal_integration_blueprint.html', size=('1600px', '1200px'), profile='full')
    dwg.attribs['style'] = 'background-color: #0A0A0A;'
    colors = {
        'ghost_fill': '#111', 'ghost_stroke': '#444',
        'intel_fill': '#0B231B', 'intel_stroke': '#39FF14',
        'laser_line': '#00D4FF', 'text_color': '#E5E7EB',
        'annotation_color': '#B2642E'
    }
    font_family = "JetBrains Mono, monospace"
    dwg.defs.add(dwg.style("@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@200;400&display=swap');"))
    bg_gradient = dwg.defs.add(dwg.radialGradient())
    bg_gradient.add_stop_color(0, '#04101A', opacity=0.9)
    bg_gradient.add_stop_color(1, '#0A0A0A', opacity=0.1)
    dwg.add(dwg.rect(size=('100%', '100%'), fill=bg_gradient.get_paint_server()))
    core_positions = [(800, 350), (1100, 550), (800, 750), (500, 550)]
    for pos in core_positions:
        dwg.add(dwg.polygon(get_hexagon_points(pos[0], pos[1], size=100), fill=colors['ghost_fill'], stroke=colors['ghost_stroke'], stroke_width=1))
    integration_hub = "signal_intelligence_layer.py"
    hub_pos = (800, 150)
    sub_modules = ["signal_semantic_expander.py", "signal_contract_validator.py", "signal_evidence_extractor.py", "signal_context_scoper.py"]
    dwg.add(dwg.polygon(get_hexagon_points(hub_pos[0], hub_pos[1], size=90), fill=colors['intel_fill'], stroke=colors['intel_stroke'], stroke_width=3))
    dwg.add(dwg.text(integration_hub, insert=hub_pos, text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="11px"))
    for i, module in enumerate(sub_modules):
        angle = (math.pi / 2) + (i - 1.5) * 0.8
        x = hub_pos[0] + 300 * math.cos(angle)
        y = hub_pos[1] + 300 * math.sin(angle)
        dwg.add(dwg.polygon(get_hexagon_points(x, y, size=70), fill=colors['intel_fill'], stroke=colors['intel_stroke'], stroke_width=1.5))
        dwg.add(dwg.text(module, insert=(x, y), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="9px"))
        dwg.add(dwg.line(hub_pos, (x, y), stroke=colors['intel_stroke'], stroke_width=0.5))
    target_core_node = core_positions[0]
    laser_line = dwg.line(hub_pos, target_core_node, stroke=colors['laser_line'], stroke_width=2, stroke_dasharray="2 6")
    laser_line.add(svgwrite.animate.Animate('stroke-dashoffset', dur='1s', repeatCount='indefinite', from_='0', to='16'))
    dwg.add(laser_line)
    annotations = [
        "1. Modify factory.py to inject EnrichedSignalPack",
        "2. Update BaseExecutor to use get_patterns_for_context()",
        "3. Replace direct SignalPack access with EnrichedSignalPack",
        "4. Deprecate signal_loader.py in core.py"
    ]
    for i, note in enumerate(annotations):
        y_pos = 200 + i * 30
        dwg.add(dwg.text(f"// {note}", insert=(1250, y_pos), text_anchor="start", fill=colors['annotation_color'], font_family=font_family, font_size="11px"))
    dwg.add(dwg.text("THE SURGICAL BLUEPRINT: INTEGRATION PROTOCOL", insert=(800, 50), text_anchor="middle", fill=colors['text_color'], font_family=font_family, font_size="24px", style="letter-spacing: 8px; text-transform: uppercase;"))
    dwg.add(dwg.text("Pre-operative plan for activating dormant intelligence", insert=(800, 80), text_anchor="middle", fill=colors['laser_line'], font_family=font_family, font_size="14px", style="letter-spacing: 4px;"))
    dwg.save()

if __name__ == "__main__":
    print("Generating visualization 1: Anatomy...")
    create_visualization_1_anatomy()
    print("Generating visualization 2: Core...")
    create_visualization_2_core()
    print("Generating visualization 3: Pathology...")
    create_visualization_3_pathology()
    print("Generating visualization 4: Journey...")
    create_visualization_4_journey()
    print("Generating visualization 5: Blueprint...")
    create_visualization_5_blueprint()
    print("All visualizations generated successfully.")
