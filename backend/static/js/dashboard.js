/* PestGuard AI — Dasher Dashboard JS */
const API='';let curPage='dashboard',sid='s-'+Date.now(),chatH=[],lastPred=null;

// Toast
function toast(m,t='info'){const c=document.getElementById('toasts');const d=document.createElement('div');d.className=`alert alert-${t==='error'?'danger':t==='success'?'success':'info'} alert-dismissible fade show`;d.innerHTML=m+'<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';c.appendChild(d);setTimeout(()=>d.remove(),4000);}

// Nav
function nav(p){curPage=p;document.querySelectorAll('.page-section').forEach(s=>s.classList.remove('active'));document.getElementById('page-'+p)?.classList.add('active');document.querySelectorAll('#miniSidebar .nav-link').forEach(a=>{a.classList.toggle('active',a.dataset.page===p);});if(p==='heatmap')initMap();if(p==='weather')fetchWeather();if(p==='chat')initChat();if(p==='predict')initUpload();}
document.querySelectorAll('[data-page]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();nav(a.dataset.page);}));

// Status
async function loadStatus(){try{const r=await fetch('/');const d=await r.json();const dp=d.display||{};
  const comps=[
    {name:'AI Engine',status:dp.ai_engine||(d.vlm==='active'?'Operational':'Offline'),icon:'ti-brain'},
    {name:'Vision (VLM)',status:dp.vision||'Offline',icon:'ti-eye'},
    {name:'Weather API',status:dp.weather_service||(d.weather==='real'?'Operational':'Offline'),icon:'ti-cloud'},
    {name:'Knowledge Base',status:dp.knowledge_base||'Offline',icon:'ti-database'},
  ];
  function fmtUp(s){if(!s)return'';if(s<60)return s+'s';if(s<3600)return Math.floor(s/60)+'m';const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);return h+'h '+m+'m';}
  const rows=comps.map(c=>{const ok=c.status==='Operational';return`
    <div class="d-flex align-items-center justify-content-between py-1" style="border-bottom:1px solid rgba(255,255,255,0.05)">
      <span class="d-flex align-items-center gap-2" style="font-size:0.82rem"><i class="ti ${c.icon}" style="font-size:14px;opacity:0.7"></i>${c.name}</span>
      <span class="d-flex align-items-center gap-1" style="font-size:0.78rem;font-weight:600;color:${ok?'#10b981':'#ef4444'}">
        <span style="width:7px;height:7px;border-radius:50%;background:${ok?'#10b981':'#ef4444'};display:inline-block;box-shadow:0 0 6px ${ok?'#10b981':'#ef4444'}"></span>
        ${c.status}
      </span>
    </div>`;}).join('');
  const up=fmtUp(d.uptime_seconds);
  document.getElementById('sys-status').innerHTML=`
    <div>${rows}</div>
    <div class="d-flex justify-content-between align-items-center mt-2 pt-2" style="border-top:1px solid rgba(255,255,255,0.06)">
      <span class="text-secondary" style="font-size:0.7rem">v${d.version||'0.5.0'}</span>
      ${up?`<span class="text-secondary" style="font-size:0.7rem">⏱ ${up}</span>`:''}
    </div>`;}catch(e){document.getElementById('sys-status').innerHTML='<span class="text-danger">Offline</span>';}}

// Charts
function initCharts(){
  if(typeof ApexCharts==='undefined')return;
  // Top detected pest species from IP-102
  new ApexCharts(document.querySelector('#archChart'),{
    chart:{type:'bar',height:280,toolbar:{show:false}},
    series:[{name:'Detections',data:[1284,1156,987,934,876,812]}],
    xaxis:{categories:['Rice Leafhopper','Fall Armyworm','Green Peach Aphid','Corn Borer','Whitefly','Migratory Locust']},
    colors:['#ef4444','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ec4899'],
    plotOptions:{bar:{borderRadius:6,columnWidth:'55%',distributed:true}},
    theme:{mode:'dark'},
    grid:{borderColor:'rgba(255,255,255,0.05)'},
    legend:{show:false},
    dataLabels:{enabled:true,style:{fontSize:'11px'}}
  }).render();
  // Pest distribution by crop
  new ApexCharts(document.querySelector('#pipeChart'),{
    chart:{type:'donut',height:280},
    series:[35,28,18,12,7],
    labels:['Rice','Corn','Vegetables','Cotton','Other'],
    colors:['#10b981','#f59e0b','#3b82f6','#8b5cf6','#94a3b8'],
    theme:{mode:'dark'},
    legend:{position:'bottom'}
  }).render();
}

// Upload
function initUpload(){const z=document.getElementById('upload-zone'),i=document.getElementById('file-input');if(!z||z._init)return;z._init=true;
  ['dragover','dragenter'].forEach(e=>z.addEventListener(e,ev=>{ev.preventDefault();z.style.borderColor='var(--bs-primary)';}));
  ['dragleave','drop'].forEach(e=>z.addEventListener(e,ev=>{ev.preventDefault();z.style.borderColor='';}));
  z.addEventListener('drop',ev=>{if(ev.dataTransfer.files[0])showPrev(ev.dataTransfer.files[0]);});
  i.addEventListener('change',ev=>{if(ev.target.files[0])showPrev(ev.target.files[0]);});}
function showPrev(f){if(f.size>10*1024*1024){toast('File too large','error');return;}const r=new FileReader();r.onload=e=>{document.getElementById('preview-img').src=e.target.result;document.getElementById('preview-area').style.display='block';document.getElementById('upload-zone').style.display='none';};r.readAsDataURL(f);window._file=f;toast('Image loaded','success');}
function resetUpload(){document.getElementById('preview-area').style.display='none';document.getElementById('upload-zone').style.display='';document.getElementById('pred-result').innerHTML='';window._file=null;}

async function submitPrediction(){if(!window._file)return;const b=document.getElementById('pred-btn');b.disabled=true;b.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span>Analyzing...';
  const fd=new FormData();fd.append('file',window._file);fd.append('simulate_low_confidence',document.getElementById('sim-low').checked);
  try{const r=await fetch('/predict',{method:'POST',body:fd});if(!r.ok)throw new Error((await r.json()).detail||r.statusText);const d=await r.json();lastPred=d;
    const cc=d.confidence>=0.7?'high':d.confidence>=0.5?'med':'low',cv=cc==='high'?'success':cc==='med'?'warning':'danger';
    document.getElementById('pred-result').innerHTML=`<div class="row g-4">
      <div class="col-md-6"><div class="card card-lg"><div class="card-body">
        <h5 class="mb-3"><i class="ti ti-bug me-2"></i>Identification</h5>
        <div class="fs-3 fw-bold mb-2">${d.pest_name}</div>
        <div class="d-flex align-items-center gap-2 mb-2"><span class="fs-4 fw-bold text-${cv}">${(d.confidence*100).toFixed(1)}%</span><small class="text-secondary">confidence</small></div>
        <div class="conf-bar"><div class="conf-bar-fill conf-${cc}" style="width:${d.confidence*100}%"></div></div>
        <div class="mt-3 small text-secondary">Category: ${d.category_id} · Crop: ${d.crop||'Unknown'}</div>
        ${d.is_mock?'<div class="text-warning small mt-2">⚠️ Mock prediction (D3 model pending)</div>':''}
      </div></div></div>
      <div class="col-md-6"><div class="card card-lg"><div class="card-body">
        <h5 class="mb-3"><i class="ti ti-eye me-2"></i>Visual Analysis (VLM)</h5>
        <p class="text-secondary" style="line-height:1.7">${d.vlm_description}</p>
        ${d.confidence<0.7?'<div class="disclaimer-box mt-3">⚠️ Low confidence — upload a clearer image.</div>':''}
      </div></div></div>
    </div><div class="text-center mt-3"><button class="btn btn-primary" onclick="nav(\'chat\')"><i class="ti ti-message-dots me-1"></i>Get Treatment Advice</button></div>`;
    toast('Prediction complete!','success');
  }catch(e){document.getElementById('pred-result').innerHTML=`<div class="alert alert-danger">${e.message}</div>`;toast(e.message,'error');}
  b.disabled=false;b.innerHTML='<i class="ti ti-search me-1"></i>Analyze';}

// Chat
function initChat(){const el=document.getElementById('chat-msgs');if(el)el.scrollTop=el.scrollHeight;document.getElementById('chat-input')?.focus();
  if(lastPred)document.getElementById('chat-ctx').innerHTML=`<div class="alert alert-info alert-dismissible fade show mb-3 small">🔗 Context: <strong>${lastPred.pest_name}</strong> (${(lastPred.confidence*100).toFixed(0)}%)<button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button></div>`;
  else document.getElementById('chat-ctx').innerHTML='';}

async function sendChat(){const inp=document.getElementById('chat-input');const m=inp.value.trim();if(!m)return;inp.value='';
  chatH.push({role:'user',content:m,time:new Date().toLocaleTimeString()});renderChat();
  const msgs=document.getElementById('chat-msgs');msgs.innerHTML+='<div class="chat-bubble assistant typing-dots" id="typing"><span></span><span></span><span></span></div>';msgs.scrollTop=msgs.scrollHeight;
  const btn=document.getElementById('chat-btn');btn.disabled=true;
  try{const body={message:m,session_id:sid};if(lastPred){body.pest_name=lastPred.pest_name;body.confidence=lastPred.confidence;body.crop=lastPred.crop;}
    try{const p=await new Promise((r,j)=>navigator.geolocation.getCurrentPosition(r,j,{timeout:2000}));body.lat=p.coords.latitude;body.lon=p.coords.longitude;}catch(e){}
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();
    let reply=d.reply||'No response.';if(d.weather_warning)reply='<div class="disclaimer-box mb-2" style="border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.08);color:#ef4444">'+d.weather_warning+'</div>'+reply;
    reply=reply.replace(/## (.+)/g,'<h6 class="mt-2">$1</h6>').replace(/### (.+)/g,'<h6 class="mt-2 small">$1</h6>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\n- /g,'<br>• ');
    chatH.push({role:'assistant',content:reply,time:`${d.llm_provider||'AI'} · ${d.prompt_type||''}`});
  }catch(e){chatH.push({role:'assistant',content:`<span class="text-danger">Error: ${e.message}</span>`,time:'error'});toast(e.message,'error');}
  btn.disabled=false;renderChat();}

function renderChat(){const el=document.getElementById('chat-msgs');el.innerHTML=chatH.map(m=>`<div class="chat-bubble ${m.role}">${m.content}<div class="text-secondary mt-1" style="font-size:0.7rem">${m.time||''}</div></div>`).join('');el.scrollTop=el.scrollHeight;}

// Weather
async function fetchWeather(){const lat=document.getElementById('w-lat').value,lon=document.getElementById('w-lon').value;const b=document.getElementById('w-btn');b.disabled=true;b.innerHTML='<span class="spinner-border spinner-border-sm"></span>';
  try{const r=await fetch(`/weather/${lat}/${lon}`);const w=await r.json();
    document.getElementById('weather-result').innerHTML=`
      <div class="text-center mb-4"><span class="safety-pill ${w.safe_to_spray?'safe':'unsafe'}">${w.safe_to_spray?'✅ SAFE TO SPRAY':'🚫 DO NOT SPRAY'}</span></div>
      <div class="row row-cols-2 row-cols-md-5 g-3 mb-4">
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">🌡️</div><div class="fs-4 fw-bold">${w.temperature}°C</div><small class="text-secondary">TEMP</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">💧</div><div class="fs-4 fw-bold">${w.humidity}%</div><small class="text-secondary">HUMIDITY</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">💨</div><div class="fs-4 fw-bold">${w.wind_speed}</div><small class="text-secondary">WIND km/h</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">🌧️</div><div class="fs-4 fw-bold">${w.rain_probability}%</div><small class="text-secondary">RAIN</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">☁️</div><div class="fw-bold">${w.condition}</div><small class="text-secondary">CONDITION</small></div></div></div>
      </div>
      ${w.alerts?.length?`<div class="alert alert-danger"><h6>⚠️ Warnings</h6><ul class="mb-0">${w.alerts.map(a=>`<li>${a}</li>`).join('')}</ul></div>`:''}
      <div class="disclaimer-box">${w.disclaimer}</div>`;
  }catch(e){document.getElementById('weather-result').innerHTML=`<div class="alert alert-danger">${e.message}</div>`;toast(e.message,'error');}
  b.disabled=false;b.innerHTML='<i class="ti ti-search me-1"></i>Check';}
function useMyLoc(){navigator.geolocation?.getCurrentPosition(p=>{document.getElementById('w-lat').value=p.coords.latitude.toFixed(2);document.getElementById('w-lon').value=p.coords.longitude.toFixed(2);fetchWeather();toast('Location detected','success');},()=>toast('Access denied','error'));}

// Heatmap
let hmap=null;
async function initMap(){if(hmap){hmap.remove();hmap=null;}hmap=L.map('heatmap-box').setView([39,35],6);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OSM © CARTO',maxZoom:18}).addTo(hmap);
  try{const r=await fetch('/heatmap'),j=await r.json(),data=j.data||[];
    const cl={Aphid:'#10b981','Rice Leafhopper':'#3b82f6','Corn Borer':'#f59e0b','Fall Armyworm':'#ef4444',Locust:'#8b5cf6',Whitefly:'#ec4899'};
    data.forEach(p=>{const c=cl[p.pest_type]||'#94a3b8';L.circle([p.grid_lat,p.grid_lon],{radius:Math.min(p.count*800,8000),color:c,fillColor:c,fillOpacity:0.35,weight:1}).bindPopup(`<b>${p.pest_type}</b><br>Reports: ${p.count}`).addTo(hmap);});
    const lg=L.control({position:'bottomright'});lg.onAdd=()=>{const d=L.DomUtil.create('div');d.style.cssText='background:rgba(10,14,26,0.9);padding:10px;border-radius:8px;font-size:12px;color:#fff;border:1px solid rgba(255,255,255,0.1)';d.innerHTML=Object.entries(cl).map(([k,v])=>`<div style="display:flex;align-items:center;gap:6px;margin:3px 0"><span style="width:10px;height:10px;border-radius:50%;background:${v};display:inline-block"></span>${k}</div>`).join('');return d;};lg.addTo(hmap);
  }catch(e){}setTimeout(()=>hmap?.invalidateSize(),200);}

async function submitReport(){const lat=+document.getElementById('h-lat').value,lon=+document.getElementById('h-lon').value,pest=document.getElementById('h-pest').value;
  try{const r=await fetch('/heatmap/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat,lon,pest_type:pest})});const d=await r.json();
    document.getElementById('report-msg').innerHTML=`<span class="text-success">✅ Submitted (grid: ${d.grid_lat||d.data?.grid_lat}, ${d.grid_lon||d.data?.grid_lon})</span>`;toast('Report submitted!','success');initMap();
  }catch(e){toast(e.message,'error');}}

// Init
loadStatus();initCharts();setInterval(loadStatus,30000);
