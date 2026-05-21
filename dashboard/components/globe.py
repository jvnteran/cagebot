"""Spinning wireframe globe component — Black Ops style.
Rendered as a self-contained HTML component via st.components.v1.html().
"""

import streamlit.components.v1 as components


def render_globe(points: list[dict], height: int = 520):
    """Render a spinning wireframe globe with city markers.

    Args:
        points: list of dicts with keys: city, country, lat, lon, accuracy_pct, events, decided_fights
        height: component height in pixels
    """
    # Serialize points to JS
    points_js = "[\n" + ",\n".join(
        f'{{city:"{p["city"]}",country:"{p["country"]}",lat:{p["lat"]},lon:{p["lon"]},'
        f'accuracy_pct:{p["accuracy_pct"]},events:{p["events"]},decided_fights:{p["decided_fights"]}}}'
        for p in points
    ) + "\n]"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #000; overflow: hidden; font-family: 'JetBrains Mono', 'SF Mono', monospace; }}
    .wrap {{ display: flex; justify-content: center; align-items: center; height: {height}px; position: relative; }}
    .tooltip {{
        position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
        background: rgba(0,0,0,0.92); border: 1px solid rgba(255,255,255,0.18);
        border-left: 2px solid #dc2626; padding: 8px 12px;
        font-size: 11px; color: rgba(255,255,255,0.85); letter-spacing: 0.05em;
        white-space: nowrap; pointer-events: none; display: none;
    }}
    .tooltip .city {{ font-family: 'Chakra Petch', sans-serif; color: #fff;
        letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; }}
    </style>
    </head>
    <body>
    <div class="wrap">
        <canvas id="globe" width="460" height="460"></canvas>
        <div class="tooltip" id="tt"></div>
    </div>
    <script>
    const POINTS = {points_js};
    const SIZE = 460, R = SIZE * 0.4, CX = SIZE/2, CY = SIZE/2, DEG = Math.PI/180;
    const canvas = document.getElementById('globe');
    const ctx = canvas.getContext('2d');
    const tt = document.getElementById('tt');
    let rot = 0, paused = false, hover = null;

    canvas.addEventListener('mouseenter', () => paused = true);
    canvas.addEventListener('mouseleave', () => {{ paused = false; hover = null; tt.style.display = 'none'; }});
    canvas.addEventListener('mousemove', (e) => {{
        const rect = canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left) * (SIZE / rect.width);
        const my = (e.clientY - rect.top) * (SIZE / rect.height);
        hover = null;
        for (const p of POINTS) {{
            const proj = project(p.lon, p.lat);
            if (!proj.visible) continue;
            const dx = proj.x - mx, dy = proj.y - my;
            if (dx*dx + dy*dy < 200) {{ hover = p; break; }}
        }}
        if (hover) {{
            tt.innerHTML = '<div class="city">' + hover.city + ' · ' + hover.country + '</div>'
                + 'ACC <span style="color:#dc2626">' + hover.accuracy_pct + '%</span>'
                + '  ·  EVT ' + hover.events + '  ·  FIGHTS ' + hover.decided_fights;
            tt.style.display = 'block';
        }} else {{
            tt.style.display = 'none';
        }}
    }});

    // Land bounding boxes
    const LAND = [
        [-168,24,-52,72],[-130,14,-82,32],[-55,60,-20,82],[-100,7,-77,20],
        [-80,-55,-34,12],[-12,36,40,72],[-18,-35,52,37],[25,12,62,42],
        [40,18,150,78],[95,-10,142,18],[127,30,146,46],
        [112,-40,155,-10],[165,-48,179,-34],[95,-10,142,8],[117,5,127,19]
    ];
    function isLand(lon, lat) {{
        for (const [w,s,e,n] of LAND) if (lon>=w && lon<=e && lat>=s && lat<=n) return true;
        return false;
    }}

    // Pre-compute land dots
    const landPts = [];
    for (let lat = 80; lat >= -60; lat -= 6)
        for (let lon = -180; lon <= 180; lon += 6)
            if (isLand(lon, lat)) landPts.push([lon, lat]);

    // Graticule
    const grats = [];
    for (let lat = -75; lat <= 75; lat += 15) {{
        const samples = [];
        for (let lon = -180; lon <= 180; lon += 10) samples.push([lon, lat]);
        grats.push({{ samples, major: lat === 0 }});
    }}
    for (let lon = -180; lon < 180; lon += 15) {{
        const samples = [];
        for (let lat = -90; lat <= 90; lat += 10) samples.push([lon, lat]);
        grats.push({{ samples, major: lon % 90 === 0 }});
    }}

    function project(lon, lat) {{
        const phi = (90 - lat) * DEG, theta = (lon + rot) * DEG;
        const sx = R * Math.sin(phi) * Math.sin(theta);
        const sz = R * Math.sin(phi) * Math.cos(theta);
        const sy = R * Math.cos(phi);
        return {{ x: CX + sx, y: CY - sy, z: sz, visible: sz > 0 }};
    }}

    function draw() {{
        ctx.clearRect(0, 0, SIZE, SIZE);

        // Atmosphere glow
        const grd = ctx.createRadialGradient(CX, CY, R*0.2, CX, CY, R+20);
        grd.addColorStop(0, 'rgba(220,38,38,0.08)');
        grd.addColorStop(0.6, 'rgba(220,38,38,0.03)');
        grd.addColorStop(1, 'transparent');
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, SIZE, SIZE);

        // Sphere fill
        ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI*2);
        ctx.fillStyle = '#000'; ctx.fill();

        // Clip to sphere
        ctx.save(); ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI*2); ctx.clip();

        // Graticule
        for (const g of grats) {{
            ctx.beginPath();
            let started = false;
            for (const [lon, lat] of g.samples) {{
                const p = project(lon, lat);
                if (p.visible) {{ if (!started) {{ ctx.moveTo(p.x, p.y); started = true; }} else ctx.lineTo(p.x, p.y); }}
                else started = false;
            }}
            ctx.strokeStyle = g.major ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)';
            ctx.lineWidth = g.major ? 0.8 : 0.5;
            ctx.stroke();
        }}

        // Land dots
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        for (const [lon, lat] of landPts) {{
            const p = project(lon, lat);
            if (p.visible) {{ ctx.beginPath(); ctx.arc(p.x, p.y, 1, 0, Math.PI*2); ctx.fill(); }}
        }}

        // City markers
        for (const c of POINTS) {{
            const p = project(c.lon, c.lat);
            if (!p.visible) continue;
            const r = 3 + Math.sqrt(c.events) * 1.4;
            // Glow
            ctx.beginPath(); ctx.arc(p.x, p.y, r+8, 0, Math.PI*2);
            ctx.fillStyle = 'rgba(220,38,38,0.12)'; ctx.fill();
            // Marker
            ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI*2);
            ctx.fillStyle = '#dc2626'; ctx.fill();
            ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 0.8; ctx.stroke();
            // White center
            ctx.beginPath(); ctx.arc(p.x, p.y, 1.2, 0, Math.PI*2);
            ctx.fillStyle = '#fff'; ctx.fill();
        }}

        ctx.restore();

        // Sphere border
        ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI*2);
        ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.lineWidth = 1.2; ctx.stroke();

        // Corner brackets
        ctx.strokeStyle = 'rgba(220,38,38,0.7)'; ctx.lineWidth = 1.2;
        const B = 18;
        ctx.beginPath(); ctx.moveTo(CX-R-B, CY-R+4); ctx.lineTo(CX-R-B, CY-R-14); ctx.lineTo(CX-R, CY-R-14); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(CX+R+B, CY-R+4); ctx.lineTo(CX+R+B, CY-R-14); ctx.lineTo(CX+R, CY-R-14); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(CX-R-B, CY+R-4); ctx.lineTo(CX-R-B, CY+R+14); ctx.lineTo(CX-R, CY+R+14); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(CX+R+B, CY+R-4); ctx.lineTo(CX+R+B, CY+R+14); ctx.lineTo(CX+R, CY+R+14); ctx.stroke();

        // HUD text
        ctx.font = '9px monospace'; ctx.letterSpacing = '2px';
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.fillText('LAT 00:00:00', CX-R-B, CY-R-22);
        ctx.textAlign = 'right';
        ctx.fillText('LON ' + String(Math.round(rot)).padStart(3,'0') + '°', CX+R+B, CY-R-22);
        ctx.textAlign = 'left';
        ctx.fillText('ORBIT // ' + (paused ? 'PAUSED' : 'TRACKING'), CX-R-B, CY+R+30);
        ctx.textAlign = 'right';
        ctx.fillText(POINTS.length + ' NODES', CX+R+B, CY+R+30);
        ctx.textAlign = 'left';

        // Crosshair
        ctx.strokeStyle = 'rgba(255,255,255,0.2)'; ctx.lineWidth = 0.6;
        ctx.beginPath(); ctx.moveTo(CX-6, CY); ctx.lineTo(CX+6, CY); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(CX, CY-6); ctx.lineTo(CX, CY+6); ctx.stroke();
    }}

    function animate() {{
        if (!document.hidden && !paused) rot = (rot + 0.15) % 360;
        draw();
        setTimeout(animate, 50);
    }}
    animate();
    </script>
    </body>
    </html>
    """
    components.html(html, height=height, scrolling=False)
