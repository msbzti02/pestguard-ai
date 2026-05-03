/* PestGuard AI — Enhanced Frontend v2 */
const API = '';
let currentPage = 'home', sessionId = 'sess-' + Date.now(), chatHistory = [], lastPrediction = null;

// ── Toast System ──
function toast(msg, type='info') {
    let c = document.getElementById('toast-container');
    if (!c) { c = document.createElement('div'); c.id='toast-container'; c.className='toast-container'; document.body.appendChild(c); }
    const t = document.createElement('div');
    t.className = 'toast ' + type;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

// ── Router ──
function navigate(page) {
    currentPage = page;
    document.querySelectorAll('#nav-links a').forEach(a => a.classList.toggle('active', a.dataset.page === page));
    render();
}
document.getElementById('nav-links').addEventListener('click', e => {
    const link = e.target.closest('a[data-page]');
    if (link) { e.preventDefault(); navigate(link.dataset.page); }
});

function render() {
    const app = document.getElementById('app');
    const pages = { home: renderHome, predict: renderPredict, chat: renderChat, weather: renderWeather, heatmap: renderHeatmap };
    app.innerHTML = (pages[currentPage] || renderHome)();
    app.innerHTML += '<div class="footer">© 2026 PestGuard AI — Department 2 Capstone · BAU</div>';
    if (currentPage === 'heatmap') initHeatmap();
    if (currentPage === 'predict') initUpload();
    if (currentPage === 'chat') initChat();
    if (currentPage === 'weather') initWeather();
    if (currentPage === 'home') loadStatus();
}

// ── HOME ──
function renderHome() {
    return `<div class="fade-in-up">
    <div class="page-header" style="text-align:center;padding:3rem 0 1rem">
        <h1 style="font-size:2.75rem;margin-bottom:0.5rem">🔬 PestGuard AI</h1>
        <p style="max-width:700px;margin:0 auto;font-size:1.05rem">Intelligent insect pest recognition powered by RAG, multi-provider LLMs, computer vision, and real-time weather analysis.</p>
    </div>
    <div class="hero-stats">
        <div class="hero-stat"><div class="number count-animate">4,766</div><div class="label">Knowledge Chunks</div></div>
        <div class="hero-stat"><div class="number count-animate">20</div><div class="label">Source Documents</div></div>
        <div class="hero-stat"><div class="number count-animate">3</div><div class="label">AI Providers</div></div>
        <div class="hero-stat"><div class="number count-animate">102</div><div class="label">Pest Species</div></div>
    </div>
    <div class="grid-3 stagger" style="margin-top:1.5rem">
        <div class="glow-card" onclick="navigate('predict')">
            <div class="card-header"><div class="card-icon green">📸</div><h3>Pest Prediction</h3></div>
            <p style="color:var(--text-secondary);font-size:0.9rem">Upload a pest photo for AI identification with VLM visual analysis and confidence scoring.</p>
        </div>
        <div class="glow-card" onclick="navigate('chat')">
            <div class="card-header"><div class="card-icon blue">💬</div><h3>AI Advisor</h3></div>
            <p style="color:var(--text-secondary);font-size:0.9rem">Chat with our RAG-powered expert for treatment plans, pesticide recommendations, and IPM strategies.</p>
        </div>
        <div class="glow-card" onclick="navigate('weather')">
            <div class="card-header"><div class="card-icon amber">🌤️</div><h3>Spray Safety</h3></div>
            <p style="color:var(--text-secondary);font-size:0.9rem">Real-time weather with FAO/WHO pesticide safety thresholds. Know when it's safe to apply.</p>
        </div>
    </div>
    <div class="grid-2 stagger" style="margin-top:1.5rem">
        <div class="glow-card" onclick="navigate('heatmap')">
            <div class="card-header"><div class="card-icon red">🗺️</div><h3>Outbreak Heatmap</h3></div>
            <p style="color:var(--text-secondary);font-size:0.9rem">Regional pest outbreak visualization with anonymized privacy-safe reporting.</p>
        </div>
        <div class="card" id="status-card">
            <div class="card-header"><div class="card-icon green">⚡</div><h3>System Status</h3></div>
            <div id="sys-status"><div class="spinner"></div></div>
        </div>
    </div></div>`;
}

function formatUptime(sec) {
    if (sec < 60) return sec + 's';
    if (sec < 3600) return Math.floor(sec/60) + 'm ' + (sec%60) + 's';
    const h = Math.floor(sec/3600), m = Math.floor((sec%3600)/60);
    return h + 'h ' + m + 'm';
}

async function loadStatus() {
    try {
        const r = await fetch(API + '/'); const d = await r.json();
        const el = document.getElementById('sys-status');
        const dp = d.display || {};
        const components = [
            { name: 'AI Engine', status: dp.ai_engine || (d.vlm === 'active' ? 'Operational' : 'Offline'), icon: '🧠' },
            { name: 'Vision (VLM)', status: dp.vision || 'Offline', icon: '👁️' },
            { name: 'Weather API', status: dp.weather_service || (d.weather === 'real' ? 'Operational' : 'Offline'), icon: '🌤️' },
            { name: 'Knowledge Base', status: dp.knowledge_base || 'Offline', icon: '📚' },
        ];
        const rows = components.map(c => {
            const ok = c.status === 'Operational';
            return `<div style="display:flex;align-items:center;justify-content:space-between;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                <span style="display:flex;align-items:center;gap:0.5rem;font-size:0.85rem">${c.icon} ${c.name}</span>
                <span style="display:flex;align-items:center;gap:0.35rem;font-size:0.8rem;font-weight:600;color:${ok?'var(--accent-green)':'var(--accent-red)'}">
                    <span style="width:7px;height:7px;border-radius:50%;background:${ok?'var(--accent-green)':'var(--accent-red)'};display:inline-block;box-shadow:0 0 6px ${ok?'var(--accent-green)':'var(--accent-red)'}"></span>
                    ${c.status}
                </span>
            </div>`;
        }).join('');
        const uptime = d.uptime_seconds ? formatUptime(d.uptime_seconds) : '';
        if (el) el.innerHTML = `<div style="display:grid;gap:0.15rem">${rows}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.6rem;padding-top:0.5rem;border-top:1px solid rgba(255,255,255,0.06)">
                <span style="font-size:0.7rem;color:var(--text-muted)">v${d.version || '0.5.0'}</span>
                ${uptime ? `<span style="font-size:0.7rem;color:var(--text-muted)">⏱ Uptime: ${uptime}</span>` : ''}
            </div>`;
        document.getElementById('status-dot').className = 'status-dot online';
    } catch(e) { document.getElementById('status-dot').className = 'status-dot offline'; }
}

// ── PREDICT ──
function renderPredict() {
    return `<div class="fade-in-up">
    <div class="page-header"><h1>📸 Pest Prediction</h1><p>Upload a photo for AI-powered insect identification</p></div>
    <div class="step-indicator">
        <div class="step active" id="step1">📷 Upload</div><div class="step-connector" id="sc1"></div>
        <div class="step" id="step2">🔍 Analyze</div><div class="step-connector" id="sc2"></div>
        <div class="step" id="step3">📋 Results</div>
    </div>
    <div class="card" id="upload-card" style="position:relative">
        <div class="upload-zone" id="upload-zone">
            <input type="file" id="file-input" accept="image/*">
            <div class="upload-icon">📷</div>
            <div class="upload-text"><strong>Click or drag</strong> an image here<br><span style="font-size:0.8rem;color:var(--text-muted)">JPEG, PNG, WebP · Max 10MB</span></div>
        </div>
        <div id="preview-area" style="display:none;margin-top:1.5rem">
            <img id="preview-img" class="image-preview" alt="Uploaded pest image">
            <div style="display:flex;gap:0.75rem;margin-top:1rem;flex-wrap:wrap;align-items:center">
                <button class="btn btn-primary btn-lg" id="predict-btn" onclick="submitPrediction()">🔍 Analyze Pest</button>
                <button class="btn btn-secondary" onclick="resetUpload()">✕ Clear</button>
                <label style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:var(--text-muted)"><input type="checkbox" id="sim-low"> Simulate low confidence</label>
            </div>
        </div>
    </div>
    <div id="prediction-result" style="margin-top:1.5rem"></div></div>`;
}

function initUpload() {
    const zone = document.getElementById('upload-zone'), input = document.getElementById('file-input');
    if (!zone) return;
    ['dragover','dragenter'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.add('dragover'); }));
    ['dragleave','drop'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.remove('dragover'); }));
    zone.addEventListener('drop', ev => { if (ev.dataTransfer.files[0]) showPreview(ev.dataTransfer.files[0]); });
    input.addEventListener('change', ev => { if (ev.target.files[0]) showPreview(ev.target.files[0]); });
}

function showPreview(file) {
    if (file.size > 10*1024*1024) { toast('File too large (max 10MB)', 'error'); return; }
    const reader = new FileReader();
    reader.onload = e => { document.getElementById('preview-img').src = e.target.result; document.getElementById('preview-area').style.display = 'block'; document.getElementById('upload-zone').style.display = 'none'; };
    reader.readAsDataURL(file);
    window._selectedFile = file;
    setStep(1);
    toast('Image loaded — ready to analyze', 'success');
}

function resetUpload() {
    document.getElementById('preview-area').style.display = 'none';
    document.getElementById('upload-zone').style.display = '';
    document.getElementById('prediction-result').innerHTML = '';
    window._selectedFile = null;
    setStep(0);
}

function setStep(n) {
    ['step1','step2','step3'].forEach((id,i) => { const el=document.getElementById(id); if(el) el.className = i<n?'step done':i===n?'step active':'step'; });
    ['sc1','sc2'].forEach((id,i) => { const el=document.getElementById(id); if(el) el.className = i<n?'step-connector active':'step-connector'; });
}

async function submitPrediction() {
    if (!window._selectedFile) return;
    const btn = document.getElementById('predict-btn');
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Analyzing...';
    setStep(1);
    const form = new FormData();
    form.append('file', window._selectedFile);
    form.append('simulate_low_confidence', document.getElementById('sim-low').checked);
    try {
        const res = await fetch(API + '/predict', { method: 'POST', body: form });
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || res.statusText); }
        const data = await res.json();
        lastPrediction = data;
        setStep(2);
        showPredictionResult(data);
        toast('Prediction complete!', 'success');
    } catch (err) {
        document.getElementById('prediction-result').innerHTML = `<div class="card" style="border-color:var(--accent-red)"><p style="color:var(--accent-red)">❌ ${err.message}</p></div>`;
        toast(err.message, 'error');
    }
    btn.disabled = false; btn.innerHTML = '🔍 Analyze Pest';
}

function showPredictionResult(d) {
    const cc = d.confidence >= 0.7 ? 'high' : d.confidence >= 0.5 ? 'medium' : 'low';
    const cv = cc==='high'?'var(--accent-green)':cc==='medium'?'var(--accent-amber)':'var(--accent-red)';
    document.getElementById('prediction-result').innerHTML = `
    <div class="result-section fade-in-up">
        <div class="card">
            <div class="card-header"><div class="card-icon green">🐛</div><h3>Identification</h3></div>
            <div style="font-size:1.5rem;font-weight:700;margin:0.5rem 0">${d.pest_name}</div>
            <div style="display:flex;align-items:center;gap:0.75rem;margin:0.5rem 0">
                <span style="color:${cv};font-weight:700;font-size:1.25rem">${(d.confidence*100).toFixed(1)}%</span>
                <span style="color:var(--text-muted);font-size:0.8rem">confidence</span>
            </div>
            <div class="confidence-bar"><div class="confidence-bar-fill confidence-${cc}" style="width:${d.confidence*100}%"></div></div>
            <div style="margin-top:1rem;font-size:0.85rem;color:var(--text-secondary)">
                <div>Category: ${d.category_id} · Crop: ${d.crop||'Unknown'}</div>
                ${d.is_mock?'<div style="color:var(--accent-amber);margin-top:0.5rem">⚠️ Mock prediction (D3 model pending)</div>':''}
            </div>
        </div>
        <div class="card">
            <div class="card-header"><div class="card-icon blue">👁️</div><h3>Visual Analysis (VLM)</h3></div>
            <p style="color:var(--text-secondary);font-size:0.9rem;line-height:1.7">${d.vlm_description}</p>
            ${d.confidence<0.7?'<div class="disclaimer">⚠️ Low confidence — upload a clearer image for better results.</div>':''}
        </div>
    </div>
    <div style="margin-top:1rem;text-align:center">
        <button class="btn btn-primary" onclick="navigate('chat')">💬 Get Treatment Advice</button>
    </div>`;
}

// ── CHAT ──
function renderChat() {
    const msgs = chatHistory.map(m => {
        const time = m.time || '';
        return `<div class="chat-message ${m.role}">${m.content}<div class="chat-meta">${time}</div></div>`;
    }).join('');
    const ctx = lastPrediction ? `<div class="disclaimer" style="border-color:var(--accent-blue-glow);background:rgba(59,130,246,0.08);color:var(--accent-blue);margin-bottom:1rem">🔗 Context: <strong>${lastPrediction.pest_name}</strong> (${(lastPrediction.confidence*100).toFixed(0)}%)</div>` : '';
    return `<div class="fade-in-up">
    <div class="page-header"><h1>💬 AI Agricultural Advisor</h1><p>RAG-powered pest management expert with 4,766 knowledge chunks</p></div>
    ${ctx}
    <div class="card chat-container">
        <div class="chat-messages" id="chat-messages">
            ${msgs || '<div style="text-align:center;color:var(--text-muted);padding:3rem"><div style="font-size:2rem;margin-bottom:0.5rem">🌾</div>Ask about pest management, treatment timing, or safety precautions...</div>'}
        </div>
        <div class="chat-input-row">
            <input type="text" id="chat-input" placeholder="How do I treat aphids on my rice field?" onkeydown="if(event.key==='Enter')sendChat()">
            <button class="btn btn-primary" id="chat-send-btn" onclick="sendChat()">Send</button>
        </div>
    </div></div>`;
}

function initChat() {
    const el = document.getElementById('chat-messages');
    if (el) el.scrollTop = el.scrollHeight;
    document.getElementById('chat-input')?.focus();
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    chatHistory.push({ role: 'user', content: msg, time: new Date().toLocaleTimeString() });
    render();
    // Show typing indicator
    const msgs = document.getElementById('chat-messages');
    if (msgs) { msgs.innerHTML += '<div class="typing-indicator" id="typing"><span></span><span></span><span></span></div>'; msgs.scrollTop = msgs.scrollHeight; }
    const btn = document.getElementById('chat-send-btn');
    btn.disabled = true;
    try {
        const body = { message: msg, session_id: sessionId };
        if (lastPrediction) { body.pest_name = lastPrediction.pest_name; body.confidence = lastPrediction.confidence; body.crop = lastPrediction.crop; }
        try { const pos = await new Promise((r,j)=>navigator.geolocation.getCurrentPosition(r,j,{timeout:2000})); body.lat=pos.coords.latitude; body.lon=pos.coords.longitude; } catch(e){}
        const res = await fetch(API+'/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
        const data = await res.json();
        let reply = data.reply||'No response.';
        // Weather warning
        if (data.weather_warning) reply = `<div class="disclaimer" style="border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.08);color:var(--accent-red);margin-bottom:0.75rem">${data.weather_warning}</div>` + reply;
        // Markdown
        reply = reply.replace(/## (.+)/g,'<h2>$1</h2>').replace(/### (.+)/g,'<h3>$1</h3>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\n- /g,'<br>• ');
        // Sources
        if (data.rag_sources?.length) {
            reply += '<div style="margin-top:0.75rem">';
            data.rag_sources.forEach(s => { reply += `<span class="source-tag">📄 ${s.source}</span>`; });
            reply += '</div>';
        }
        const meta = `${data.llm_provider||'AI'} · ${data.prompt_type||''}`;
        chatHistory.push({ role:'assistant', content: reply, time: meta });
    } catch(err) {
        chatHistory.push({ role:'assistant', content:`<span style="color:var(--accent-red)">Error: ${err.message}</span>`, time:'error' });
        toast(err.message, 'error');
    }
    btn.disabled = false;
    render();
}

// ── WEATHER ──
function renderWeather() {
    return `<div class="fade-in-up">
    <div class="page-header"><h1>🌤️ Weather & Spray Safety</h1><p>Real-time weather with FAO/WHO pesticide application safety checks</p></div>
    <div class="card" style="margin-bottom:1.5rem">
        <div style="display:flex;gap:0.75rem;flex-wrap:wrap;align-items:end">
            <div><label style="font-size:0.8rem;color:var(--text-muted)">Latitude</label><br>
                <input type="number" step="0.01" id="w-lat" value="41.0" style="padding:0.5rem;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:var(--radius-sm);color:var(--text-primary);width:120px;font-family:inherit"></div>
            <div><label style="font-size:0.8rem;color:var(--text-muted)">Longitude</label><br>
                <input type="number" step="0.01" id="w-lon" value="29.0" style="padding:0.5rem;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:var(--radius-sm);color:var(--text-primary);width:120px;font-family:inherit"></div>
            <button class="btn btn-primary" id="w-btn" onclick="fetchWeather()">🔍 Check Weather</button>
            <button class="btn btn-secondary btn-sm" onclick="useMyLocation()">📍 My Location</button>
        </div>
    </div>
    <div id="weather-result"></div></div>`;
}

function initWeather() { fetchWeather(); }

function useMyLocation() {
    navigator.geolocation?.getCurrentPosition(p => {
        document.getElementById('w-lat').value = p.coords.latitude.toFixed(2);
        document.getElementById('w-lon').value = p.coords.longitude.toFixed(2);
        fetchWeather();
        toast('Location detected', 'success');
    }, () => toast('Location access denied', 'error'));
}

async function fetchWeather() {
    const lat = document.getElementById('w-lat').value, lon = document.getElementById('w-lon').value;
    const btn = document.getElementById('w-btn');
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
    try {
        const res = await fetch(API+`/weather/${lat}/${lon}`);
        const w = await res.json();
        document.getElementById('weather-result').innerHTML = `<div class="fade-in-up">
            <div style="text-align:center;margin-bottom:1.5rem">
                <div class="safety-badge ${w.safe_to_spray?'safe':'unsafe'}">${w.safe_to_spray?'✅ SAFE TO SPRAY':'🚫 DO NOT SPRAY'}</div>
            </div>
            <div class="weather-grid stagger">
                <div class="weather-stat"><div class="stat-icon">🌡️</div><div class="stat-value">${w.temperature}°C</div><div class="stat-label">Temperature</div></div>
                <div class="weather-stat"><div class="stat-icon">💧</div><div class="stat-value">${w.humidity}%</div><div class="stat-label">Humidity</div></div>
                <div class="weather-stat"><div class="stat-icon">💨</div><div class="stat-value">${w.wind_speed} km/h</div><div class="stat-label">Wind Speed</div></div>
                <div class="weather-stat"><div class="stat-icon">🌧️</div><div class="stat-value">${w.rain_probability}%</div><div class="stat-label">Rain Probability</div></div>
                <div class="weather-stat"><div class="stat-icon">☁️</div><div class="stat-value" style="font-size:1rem">${w.condition}</div><div class="stat-label">Condition</div></div>
            </div>
            ${w.alerts?.length?`<div class="card" style="margin-top:1rem;border-color:rgba(239,68,68,0.3)"><h3 style="color:var(--accent-red)">⚠️ Warnings</h3><ul style="margin-top:0.5rem;padding-left:1.2rem">${w.alerts.map(a=>`<li style="color:var(--text-secondary)">${a}</li>`).join('')}</ul></div>`:''}
            <div class="disclaimer">${w.disclaimer}</div>
            ${w.is_mock?'<div class="disclaimer" style="border-color:rgba(139,92,246,0.3);background:rgba(139,92,246,0.08);color:var(--accent-purple)">ℹ️ Mock weather data</div>':''}
        </div>`;
    } catch(err) { document.getElementById('weather-result').innerHTML = `<div class="card"><p style="color:var(--accent-red)">❌ ${err.message}</p></div>`; toast(err.message,'error'); }
    btn.disabled = false; btn.innerHTML = '🔍 Check Weather';
}

// ── HEATMAP ──
function renderHeatmap() {
    return `<div class="fade-in-up">
    <div class="page-header"><h1>🗺️ Regional Pest Outbreak Map</h1><p>Anonymized sighting reports (0.1° grid, ~11km privacy zones)</p></div>
    <div class="card" style="padding:0;overflow:hidden"><div id="heatmap-container"></div></div>
    <div class="card" style="margin-top:1rem">
        <h3 style="margin-bottom:0.75rem">📍 Report a Pest Sighting</h3>
        <div style="display:flex;gap:0.75rem;flex-wrap:wrap;align-items:end">
            <div><label style="font-size:0.75rem;color:var(--text-muted)">Latitude</label><br><input type="number" step="0.01" id="h-lat" value="39.9" style="padding:0.5rem;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:var(--radius-sm);color:var(--text-primary);width:100px;font-family:inherit"></div>
            <div><label style="font-size:0.75rem;color:var(--text-muted)">Longitude</label><br><input type="number" step="0.01" id="h-lon" value="32.8" style="padding:0.5rem;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:var(--radius-sm);color:var(--text-primary);width:100px;font-family:inherit"></div>
            <div><label style="font-size:0.75rem;color:var(--text-muted)">Pest Type</label><br><select id="h-pest" style="padding:0.5rem;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:var(--radius-sm);color:var(--text-primary);font-family:inherit"><option>Aphid</option><option>Rice Leafhopper</option><option>Corn Borer</option><option>Fall Armyworm</option><option>Locust</option><option>Whitefly</option></select></div>
            <button class="btn btn-primary btn-sm" onclick="submitReport()">Submit Report</button>
        </div>
        <div id="report-msg" style="margin-top:0.5rem;font-size:0.85rem"></div>
        <div class="disclaimer">Privacy: Coordinates rounded to 0.1° (~11km). No personal data stored.</div>
    </div></div>`;
}

let hmap = null;
async function initHeatmap() {
    if (hmap) { hmap.remove(); hmap = null; }
    hmap = L.map('heatmap-container').setView([39.0,35.0],6);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OSM © CARTO',maxZoom:18}).addTo(hmap);
    try {
        const r = await fetch(API+'/heatmap'), j = await r.json(), data = j.data||[];
        const colors = {Aphid:'#10b981','Rice Leafhopper':'#3b82f6','Corn Borer':'#f59e0b','Fall Armyworm':'#ef4444',Locust:'#8b5cf6',Whitefly:'#ec4899'};
        data.forEach(pt => {
            const c = colors[pt.pest_type]||'#94a3b8';
            L.circle([pt.grid_lat,pt.grid_lon],{radius:Math.min(pt.count*800,8000),color:c,fillColor:c,fillOpacity:0.35,weight:1})
                .bindPopup(`<b>${pt.pest_type}</b><br>Reports: ${pt.count}<br>Grid: ${pt.grid_lat}, ${pt.grid_lon}`).addTo(hmap);
        });
        const legend = L.control({position:'bottomright'});
        legend.onAdd = () => { const d=L.DomUtil.create('div',''); d.style.cssText='background:rgba(10,14,26,0.9);padding:10px 14px;border-radius:8px;border:1px solid rgba(255,255,255,0.1);color:#f1f5f9;font-size:12px;font-family:Inter,sans-serif'; d.innerHTML=Object.entries(colors).map(([k,v])=>`<div style="display:flex;align-items:center;gap:6px;margin:3px 0"><span style="width:10px;height:10px;border-radius:50%;background:${v};display:inline-block"></span>${k}</div>`).join(''); return d; };
        legend.addTo(hmap);
    } catch(e) { console.error(e); }
    setTimeout(()=>hmap.invalidateSize(),200);
}

async function submitReport() {
    const lat=parseFloat(document.getElementById('h-lat').value), lon=parseFloat(document.getElementById('h-lon').value), pest=document.getElementById('h-pest').value;
    try {
        const r = await fetch(API+'/heatmap/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat,lon,pest_type:pest})});
        const d = await r.json();
        document.getElementById('report-msg').innerHTML = `<span style="color:var(--accent-green)">✅ Submitted (grid: ${d.grid_lat||d.data?.grid_lat}, ${d.grid_lon||d.data?.grid_lon})</span>`;
        toast('Pest sighting reported!','success');
        initHeatmap();
    } catch(e) { toast(e.message,'error'); }
}

// ── Init ──
render();
setInterval(loadStatus, 30000);
