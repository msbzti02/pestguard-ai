/* PestGuard AI — Dasher Dashboard JS */
const API='';let curPage='dashboard',sid='s-'+Date.now(),chatH=[],lastPred=null;

// Toast
function toast(m,t='info'){const c=document.getElementById('toasts');const d=document.createElement('div');d.className=`alert alert-${t==='error'?'danger':t==='success'?'success':'info'} alert-dismissible fade show`;d.innerHTML=m+'<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';c.appendChild(d);setTimeout(()=>d.remove(),4000);}

// Nav
function nav(p){curPage=p;document.querySelectorAll('.page-section').forEach(s=>s.classList.remove('active'));document.getElementById('page-'+p)?.classList.add('active');document.querySelectorAll('#miniSidebar .nav-link').forEach(a=>{a.classList.toggle('active',a.dataset.page===p);});if(p==='heatmap')initMap();if(p==='weather')fetchWeather();if(p==='chat')initChat();if(p==='predict')initUpload();if(p==='analytics')loadAnalytics();if(p==='library')loadPestLibrary();if(p==='economics')initEconomics();if(p==='feedback')initFeedbackPage();}
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
    <div>${rows}</div>`;}catch(e){document.getElementById('sys-status').innerHTML='<span class="text-danger">Offline</span>';}}

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

// Inject premium visual CSS
(function(){const s=document.createElement('style');s.textContent=`
@keyframes ripple-expand{0%{transform:scale(0);opacity:1}100%{transform:scale(6);opacity:0}}
@keyframes weather-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes pulse-red{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,0.4)}50%{box-shadow:0 0 0 12px rgba(239,68,68,0)}}
@keyframes card-enter{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes skeleton-shimmer{0%{background-position:-200px 0}100%{background-position:calc(200px + 100%) 0}}
@keyframes typewriter-blink{0%,100%{opacity:1}50%{opacity:0}}
.card{animation:card-enter 0.4s ease;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);background:rgba(30,41,59,0.65)!important;border:1px solid rgba(255,255,255,0.06)!important;transition:transform 0.3s ease,box-shadow 0.3s ease,border-color 0.3s ease}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(16,185,129,0.1),0 4px 12px rgba(0,0,0,0.3);border-color:rgba(16,185,129,0.2)!important}
.typewriter-cursor{animation:typewriter-blink 0.8s step-end infinite;color:#10b981;font-weight:300}
.skeleton-line{height:14px;margin-bottom:10px;border-radius:6px;background:linear-gradient(90deg,rgba(255,255,255,0.04) 0px,rgba(255,255,255,0.08) 40px,rgba(255,255,255,0.04) 80px);background-size:200px 100%;animation:skeleton-shimmer 1.5s ease-in-out infinite}
.skeleton-line:nth-child(2){width:85%}.skeleton-line:nth-child(3){width:70%}
kbd{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.15);border-radius:4px;padding:1px 6px;font-size:11px}
`;document.head.appendChild(s);})();

// Upload — with drag/drop ripple animation
function initUpload(){const z=document.getElementById('upload-zone'),i=document.getElementById('file-input');if(!z||z._init)return;z._init=true;z.style.position='relative';z.style.overflow='hidden';
  ['dragover','dragenter'].forEach(e=>z.addEventListener(e,ev=>{ev.preventDefault();z.style.borderColor='var(--bs-primary)';z.style.background='rgba(16,185,129,0.05)';}));
  ['dragleave'].forEach(e=>z.addEventListener(e,ev=>{ev.preventDefault();z.style.borderColor='';z.style.background='';}));
  z.addEventListener('drop',ev=>{ev.preventDefault();z.style.borderColor='';z.style.background='';
    const rip=document.createElement('div');rip.style.cssText='position:absolute;border-radius:50%;background:rgba(16,185,129,0.3);animation:ripple-expand 0.6s ease-out forwards;pointer-events:none;width:50px;height:50px;';
    const rect=z.getBoundingClientRect();rip.style.left=(ev.clientX-rect.left-25)+'px';rip.style.top=(ev.clientY-rect.top-25)+'px';z.appendChild(rip);setTimeout(()=>rip.remove(),700);
    if(ev.dataTransfer.files[0])showPrev(ev.dataTransfer.files[0]);});
  i.addEventListener('change',ev=>{if(ev.target.files[0])showPrev(ev.target.files[0]);});}
function showPrev(f){if(f.size>10*1024*1024){toast('File too large','error');return;}const r=new FileReader();r.onload=e=>{document.getElementById('preview-img').src=e.target.result;document.getElementById('preview-area').style.display='block';document.getElementById('upload-zone').style.display='none';};r.readAsDataURL(f);window._file=f;toast('Image loaded','success');}
function resetUpload(){document.getElementById('preview-area').style.display='none';document.getElementById('upload-zone').style.display='';document.getElementById('pred-result').innerHTML='';window._file=null;}

// Confidence Gauge SVG
function confGauge(pct,color){const r=54,c=2*Math.PI*r,off=c-(pct/100)*c;return `<svg width="130" height="130" viewBox="0 0 120 120"><circle cx="60" cy="60" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/><circle cx="60" cy="60" r="${r}" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${off}" transform="rotate(-90 60 60)" style="transition:stroke-dashoffset 1s ease"/><text x="60" y="55" text-anchor="middle" fill="#fff" font-size="22" font-weight="bold">${pct.toFixed(1)}%</text><text x="60" y="72" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="10">confidence</text></svg>`;}

async function submitPrediction(){if(!window._file)return;const b=document.getElementById('pred-btn');b.disabled=true;b.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span>Checking quality...';
  // ── FEATURE 3: Image Quality Check first ──
  let qualityData=null;
  try{
    const qfd=new FormData();qfd.append('file',window._file);
    const qr=await fetch('/image-quality',{method:'POST',body:qfd});
    qualityData=await qr.json();
    if(!qualityData.ready_for_prediction){
      document.getElementById('pred-result').innerHTML=`<div class="card card-lg"><div class="card-body text-center">
        <div class="fs-1 mb-2">📸</div>
        <h5>Image Quality: <span style="color:${qualityData.grade_color}">${qualityData.grade} (${qualityData.quality_score}/100)</span></h5>
        <div class="mb-3">${qualityData.issues.map(i=>`<div class="text-warning small">⚠️ ${i}</div>`).join('')}</div>
        <div class="mb-3">${qualityData.suggestions.map(s=>`<div class="text-secondary small">💡 ${s}</div>`).join('')}</div>
        <button class="btn btn-outline-warning" onclick="forcePredict()">Analyze Anyway</button>
        <button class="btn btn-outline-secondary ms-2" onclick="resetUpload()">Upload Better Image</button>
      </div></div>`;
      b.disabled=false;b.innerHTML='<i class="ti ti-search me-1"></i>Analyze';return;
    }
  }catch(e){/* quality check failed, proceed anyway */}
  b.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span>Analyzing...';
  const fd=new FormData();fd.append('file',window._file);fd.append('simulate_low_confidence',document.getElementById('sim-low').checked);
  try{const r=await fetch('/predict',{method:'POST',body:fd});if(!r.ok)throw new Error((await r.json()).detail||r.statusText);const d=await r.json();lastPred=d;
    const cc=d.confidence>=0.7?'high':d.confidence>=0.5?'med':'low';
    const gColor=cc==='high'?'#10b981':cc==='med'?'#f59e0b':'#ef4444';
    // Quality badge
    const qBadge=qualityData?`<div class="mt-2"><span class="badge" style="background:${qualityData.grade_color}20;color:${qualityData.grade_color};font-size:10px">📸 Image: ${qualityData.grade} (${qualityData.quality_score}/100)</span></div>`:'';
    // Top-3 predictions
    let top3='';
    if(d.top_3&&d.top_3.length){const medals=['🥇','🥈','🥉'];top3='<h6 class="mt-4 mb-2"><i class="ti ti-chart-bar me-1"></i>Top Predictions</h6>'+d.top_3.map((p,i)=>{const w=Math.max(5,p.confidence*100);const bc=i===0?'#10b981':i===1?'#3b82f6':'#8b5cf6';return `<div class="d-flex align-items-center gap-2 mb-2"><span class="small" style="min-width:120px">${medals[i]} ${p.pest_name}</span><div style="flex:1;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden"><div style="width:0%;height:100%;background:${bc};border-radius:4px;transition:width 1s ease" data-bar="${w}"></div></div><span class="small fw-bold" style="min-width:45px;text-align:right">${(p.confidence*100).toFixed(1)}%</span></div>`;}).join('');}
    document.getElementById('pred-result').innerHTML=`<div class="row g-4">
      <div class="col-md-6"><div class="card card-lg"><div class="card-body text-center">
        <h5 class="mb-3"><i class="ti ti-bug me-2"></i>Identification</h5>
        ${confGauge(d.confidence*100,gColor)}
        <div class="fs-3 fw-bold mt-2">${d.pest_name}</div>
        <div class="mt-2 small text-secondary">Category: ${d.category_id} · Crop: ${d.crop||'Unknown'}</div>
        <div class="mt-2"><span class="badge ${d.confidence>=0.7?'bg-danger':'bg-warning'} bg-opacity-25" style="font-size:11px">${d.confidence>=0.7?'🔴 HIGH RISK PEST':'🟡 MODERATE RISK'}</span></div>
        ${qBadge}
        ${top3}
      </div></div></div>
      <div class="col-md-6"><div class="card card-lg"><div class="card-body">
        <h5 class="mb-3"><i class="ti ti-eye me-2"></i>Visual Analysis (VLM)</h5>
        <p class="text-secondary" style="line-height:1.7">${d.vlm_description}</p>
        ${d.confidence<0.7?'<div class="disclaimer-box mt-3">⚠️ Low confidence — upload a clearer image.</div>':''}
      </div></div></div>
    </div>
    <div class="d-flex gap-2 justify-content-center flex-wrap mt-3">
      <button class="btn btn-primary" onclick="nav('chat')"><i class="ti ti-message-dots me-1"></i>Get Treatment Advice</button>
      <button class="btn btn-outline-success" onclick="nav('economics')"><i class="ti ti-calculator me-1"></i>Economic Impact</button>
      <button class="btn btn-outline-info" onclick="shareResult()"><i class="ti ti-share me-1"></i>Share</button>
      <button class="btn btn-outline-success" onclick="downloadPdfReport()"><i class="ti ti-file-download me-1"></i>PDF Report</button>
      <button class="btn btn-outline-secondary" onclick="printReport()"><i class="ti ti-printer me-1"></i>Print</button>
    </div>
    <!-- FEATURE 5: Feedback buttons inline -->
    <div class="card card-lg mt-3"><div class="card-body">
      <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
        <span class="small"><i class="ti ti-message-check me-1"></i>Was this prediction correct?</span>
        <div class="d-flex gap-2" id="inline-feedback">
          <button class="btn btn-outline-success btn-sm" onclick="quickFeedback(true)"><i class="ti ti-check me-1"></i>Yes, Correct</button>
          <button class="btn btn-outline-danger btn-sm" onclick="quickFeedback(false)"><i class="ti ti-x me-1"></i>No, Wrong</button>
        </div>
      </div>
    </div></div>
    <div id="treatment-timeline" class="mt-4"></div>`;
    setTimeout(()=>{document.querySelectorAll('[data-bar]').forEach(el=>{el.style.width=el.dataset.bar+'%';});},100);
    toast('Prediction complete!','success');addToPredHistory(d);loadPestInfo(d.pest_name);loadTreatmentTimeline(d.pest_name);savePredToStorage();
  }catch(e){document.getElementById('pred-result').innerHTML=`<div class="alert alert-danger">${e.message}</div>`;toast(e.message,'error');}
  b.disabled=false;b.innerHTML='<i class="ti ti-search me-1"></i>Analyze';}

// Force predict even with low quality
async function forcePredict(){
  const b=document.getElementById('pred-btn');if(!window._file)return;
  b.disabled=true;b.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span>Analyzing...';
  const fd=new FormData();fd.append('file',window._file);fd.append('simulate_low_confidence',document.getElementById('sim-low').checked);
  try{const r=await fetch('/predict',{method:'POST',body:fd});if(!r.ok)throw new Error((await r.json()).detail||r.statusText);const d=await r.json();lastPred=d;
    // Simplified re-render
    document.getElementById('pred-result').innerHTML='<div class="alert alert-success">Prediction complete despite quality warning. Reload page to see full result.</div>';
    toast(`Detected: ${d.pest_name} (${(d.confidence*100).toFixed(1)}%)`,'success');
    addToPredHistory(d);loadPestInfo(d.pest_name);loadTreatmentTimeline(d.pest_name);
  }catch(e){document.getElementById('pred-result').innerHTML=`<div class="alert alert-danger">${e.message}</div>`;}
  b.disabled=false;b.innerHTML='<i class="ti ti-search me-1"></i>Analyze';
}

// FEATURE 5: Quick inline feedback after prediction
async function quickFeedback(isCorrect){
  if(!lastPred){toast('No prediction to give feedback on','error');return;}
  const el=document.getElementById('inline-feedback');
  if(isCorrect){
    try{
      await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        session_id:sid,prediction_pest:lastPred.pest_name,confidence:lastPred.confidence,is_correct:true
      })});
      el.innerHTML='<span class="text-success fw-bold"><i class="ti ti-check me-1"></i>Thanks! Feedback recorded ✅</span>';
      toast('Feedback submitted — thank you!','success');
    }catch(e){toast('Failed to submit feedback','error');}
  } else {
    // Show correction dropdown inline
    const pests=_libraryData.length?_libraryData.map(p=>p.pest_name):['Rice Leafhopper','Fall Armyworm','Green Peach Aphid','Corn Borer','Whitefly','Brown Planthopper'];
    el.innerHTML=`<select class="form-select form-select-sm" id="quick-fb-pest" style="width:180px"><option>Select actual pest...</option>${pests.map(p=>`<option>${p}</option>`).join('')}</select>
      <button class="btn btn-primary btn-sm" onclick="submitQuickCorrection()"><i class="ti ti-send me-1"></i>Submit</button>`;
  }
}
async function submitQuickCorrection(){
  const actual=document.getElementById('quick-fb-pest')?.value;
  if(!actual||actual.startsWith('Select')){toast('Please select the actual pest','error');return;}
  try{
    await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      session_id:sid,prediction_pest:lastPred.pest_name,confidence:lastPred.confidence,is_correct:false,actual_pest:actual
    })});
    document.getElementById('inline-feedback').innerHTML=`<span class="text-info fw-bold"><i class="ti ti-check me-1"></i>Correction recorded: ${actual} 📝</span>`;
    toast('Correction submitted — this helps improve the model!','success');
  }catch(e){toast('Failed to submit correction','error');}
}

// Chat — Enhanced with all 20 features
let _lastSuggestions = ['🌿 What is Integrated Pest Management according to FAO guidelines?','🐛 How do I treat Fall Armyworm on corn crops?','🌧️ Is it safe to spray pesticides in rainy weather and what precautions should I take?'];
let _voiceRecognition = null;
let _chatStartTime = 0;

function initChat(){
  const el=document.getElementById('chat-msgs');if(el)el.scrollTop=el.scrollHeight;
  document.getElementById('chat-input')?.focus();
  if(lastPred){
    document.getElementById('chat-ctx').innerHTML=`<div class="alert alert-info alert-dismissible fade show mb-3 small">🔗 Context: <strong>${lastPred.pest_name}</strong> (${(lastPred.confidence*100).toFixed(0)}%)<button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button></div>`;
    _lastSuggestions=[`🧪 How to treat ${lastPred.pest_name}?`,`🌿 Organic alternatives for ${lastPred.pest_name}?`,`⏰ When to treat ${lastPred.pest_name}?`];
  } else document.getElementById('chat-ctx').innerHTML='';
  showSuggestions(_lastSuggestions, 'chat-suggestions');
  if(chatH.length>0) showSuggestions(_lastSuggestions, 'chat-suggest-bar');
  // Request notification permission
  if('Notification' in window && Notification.permission==='default') Notification.requestPermission();
  loadAnalytics();
}

function showSuggestions(suggestions, targetId){
  const el=document.getElementById(targetId);if(!el)return;
  el.innerHTML='<div class="chat-suggest">'+suggestions.map(s=>`<button onclick="useSuggestion('${s.replace(/'/g,"\\'")}')">${s}</button>`).join('')+'</div>';
}

function useSuggestion(text){
  const clean=text.replace(/^[^\s]+ /,'');
  document.getElementById('chat-input').value=clean;
  sendChat();
}

function parseMarkdown(text){
  if(typeof marked!=='undefined'){
    marked.setOptions({breaks:true,gfm:true});
    try{return marked.parse(text);}catch(e){}
  }
  return text.replace(/## (.+)/g,'<h6 class="mt-2">$1</h6>').replace(/### (.+)/g,'<h6 class="mt-2 small">$1</h6>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\n- /g,'<br>• ');
}

async function sendChat(){
  const inp=document.getElementById('chat-input');const m=inp.value.trim();if(!m)return;inp.value='';
  _chatStartTime=performance.now();
  chatH.push({role:'user',content:m,time:new Date().toLocaleTimeString(),raw:m});
  renderChat();
  const msgs=document.getElementById('chat-msgs');
  msgs.innerHTML+='<div class="chat-bubble assistant typing-dots" id="typing"><span></span><span></span><span></span></div>';
  msgs.scrollTop=msgs.scrollHeight;
  const btn=document.getElementById('chat-btn');btn.disabled=true;
  try{
    const body={message:m,session_id:sid,language:document.getElementById('chat-lang')?.value||'English'};
    if(lastPred){body.pest_name=lastPred.pest_name;body.confidence=lastPred.confidence;body.crop=lastPred.crop;}
    try{const p=await new Promise((r,j)=>navigator.geolocation.getCurrentPosition(r,j,{timeout:2000}));body.lat=p.coords.latitude;body.lon=p.coords.longitude;}catch(e){}
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    const elapsed=((performance.now()-_chatStartTime)/1000).toFixed(1);
    let reply=d.reply||'No response.';
    if(d.weather_warning) reply='<div class="disclaimer-box mb-2" style="border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.08);color:#ef4444">'+d.weather_warning+'</div>'+reply;
    reply=parseMarkdown(reply);
    // Sources with relevance
    if(d.rag_sources?.length){
      reply+='<div class="mt-2">';
      d.rag_sources.forEach(s=>{
        const rel=s.relevance!=null?` · ${s.relevance}%`:'';
        reply+=`<span class="source-tag">📄 ${s.source}${s.page?' p.'+s.page:''}${rel}</span>`;
      });
      reply+='</div>';
    }
    // Quality + time meta
    const qc=d.rag_quality||'none';
    const qLabel={high:'🟢 RAG-Grounded',medium:'🟡 Partial Match',low:'🔴 Weak Match',none:'⚪ General'}[qc]||'';
    const meta=`${d.llm_provider||'AI'} · ${d.prompt_type||''} · ${elapsed}s · <span class="quality-badge quality-${qc}">${qLabel}</span>`;
    // Update suggestions
    if(d.suggestions?.length){_lastSuggestions=d.suggestions;showSuggestions(d.suggestions,'chat-suggest-bar');}
    chatH.push({role:'assistant',content:reply,time:meta,raw:d.reply||'',provider:d.llm_provider,elapsed});
    // Browser notification if tab not focused
    if(document.hidden&&'Notification' in window&&Notification.permission==='granted'){
      new Notification('PestGuard AI',{body:'Response ready!',icon:'🌾'});
    }
  }catch(e){
    chatH.push({role:'assistant',content:`<span class="text-danger">Error: ${e.message}</span>`,time:'error',raw:e.message});
    toast(e.message,'error');
  }
  btn.disabled=false;renderChat();loadAnalytics();
}

function renderChat(){
  const el=document.getElementById('chat-msgs');
  el.innerHTML=chatH.map((m,i)=>{
    if(m.role==='user') return `<div class="chat-bubble user">${m.raw||m.content}<div class="text-white-50 mt-1" style="font-size:0.7rem">${m.time||''}</div></div>`;
    // Assistant with action buttons
    return `<div class="chat-bubble assistant">${m.content}<div class="text-secondary mt-1" style="font-size:0.7rem">${m.time||''}</div><div class="chat-actions"><button onclick="copyMsg(${i})" title="Copy">📋 Copy</button><button onclick="rateMsg(${i},1)" title="Helpful">👍</button><button onclick="rateMsg(${i},0)" title="Not helpful">👎</button></div></div>`;
  }).join('');
  el.scrollTop=el.scrollHeight;
}

function copyMsg(i){
  const raw=chatH[i]?.raw||chatH[i]?.content||'';
  const clean=raw.replace(/<[^>]*>/g,'');
  navigator.clipboard?.writeText(clean).then(()=>toast('Copied to clipboard!','success')).catch(()=>{});
}

function rateMsg(i,good){
  toast(good?'Thanks for the feedback! 👍':'We\'ll improve! 👎','info');
}

// Voice Input
function toggleVoice(){
  const btn=document.getElementById('voice-btn');
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){toast('Voice not supported in this browser','error');return;}
  if(_voiceRecognition){_voiceRecognition.stop();_voiceRecognition=null;btn.classList.remove('recording');return;}
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  _voiceRecognition=new SR();_voiceRecognition.continuous=false;_voiceRecognition.interimResults=false;
  const lang=document.getElementById('chat-lang')?.value||'English';
  const langMap={English:'en-US',Turkish:'tr-TR',Arabic:'ar-SA',French:'fr-FR',Spanish:'es-ES',German:'de-DE'};
  _voiceRecognition.lang=langMap[lang]||'en-US';
  _voiceRecognition.onresult=e=>{document.getElementById('chat-input').value=e.results[0][0].transcript;btn.classList.remove('recording');_voiceRecognition=null;};
  _voiceRecognition.onerror=()=>{btn.classList.remove('recording');_voiceRecognition=null;toast('Voice error','error');};
  _voiceRecognition.onend=()=>{btn.classList.remove('recording');_voiceRecognition=null;};
  _voiceRecognition.start();btn.classList.add('recording');toast('Listening...','info');
}

// Export Chat
function exportChat(){
  if(!chatH.length){toast('No messages to export','error');return;}
  let text='=== PestGuard AI — Chat Export ===\nDate: '+new Date().toLocaleString()+'\n\n';
  chatH.forEach(m=>{
    const role=m.role==='user'?'👨‍🌾 You':'🤖 AI';
    const raw=(m.raw||m.content||'').replace(/<[^>]*>/g,'');
    text+=`${role}:\n${raw}\n\n`;
  });
  text+='=== End of Export ===\n';
  const blob=new Blob([text],{type:'text/plain'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download=`pestguard-chat-${Date.now()}.txt`;a.click();
  toast('Chat exported!','success');
}

// Analytics
async function loadAnalytics(){
  try{
    const r=await fetch('/chat/analytics');const d=await r.json();
    if(d.total_messages>0){
      const card=document.getElementById('chat-analytics-card');if(card)card.style.display='';
      const body=document.getElementById('chat-analytics-body');
      if(body)body.innerHTML=`<div class="row row-cols-2 row-cols-md-4 g-2 small"><div class="col"><div class="text-secondary">Messages</div><div class="fw-bold">${d.total_messages}</div></div><div class="col"><div class="text-secondary">Avg Time</div><div class="fw-bold">${d.avg_response_time}s</div></div><div class="col"><div class="text-secondary">Cache Hits</div><div class="fw-bold">${d.cache_hits}</div></div><div class="col"><div class="text-secondary">Providers</div><div class="fw-bold">${Object.keys(d.provider_usage||{}).join(', ')||'—'}</div></div></div>`;
    }
  }catch(e){}
}

// Weather
function weatherIcon(cond){const map={'Clear':'☀️','Sunny':'☀️','Partly Cloudy':'⛅','Cloudy':'☁️','Overcast':'🌫️','Light Rain':'🌦️','Rain':'🌧️','Heavy Rain':'⛈️','Storm':'🌩️','Snow':'🌨️','Fog':'🌫️','Windy':'💨','Haze':'🌫️'};return map[cond]||'🌤️';}
let _weatherTimer=null;
async function fetchWeather(){const lat=document.getElementById('w-lat').value,lon=document.getElementById('w-lon').value;const b=document.getElementById('w-btn');b.disabled=true;b.innerHTML='<span class="spinner-border spinner-border-sm"></span>';
  try{const r=await fetch(`/weather/${lat}/${lon}`);const w=await r.json();
    const wIcon=weatherIcon(w.condition);
    document.getElementById('weather-result').innerHTML=`
      <div class="text-center mb-4"><span class="safety-pill ${w.safe_to_spray?'safe':'unsafe'}" style="animation:${w.safe_to_spray?'':'pulse-red 2s infinite'}">${w.safe_to_spray?'✅ SAFE TO SPRAY':'🚫 DO NOT SPRAY'}</span></div>
      <div class="text-center mb-3"><span style="font-size:4rem;display:inline-block;animation:weather-float 3s ease-in-out infinite">${wIcon}</span></div>
      <div class="row row-cols-2 row-cols-md-5 g-3 mb-4">
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">🌡️</div><div class="fs-4 fw-bold">${w.temperature}°C</div><small class="text-secondary">TEMP</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">💧</div><div class="fs-4 fw-bold">${w.humidity}%</div><small class="text-secondary">HUMIDITY</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">💨</div><div class="fs-4 fw-bold">${w.wind_speed}</div><small class="text-secondary">WIND km/h</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">🌧️</div><div class="fs-4 fw-bold">${w.rain_probability}%</div><small class="text-secondary">RAIN</small></div></div></div>
        <div class="col"><div class="card card-lg text-center"><div class="card-body py-3"><div class="fs-1">☁️</div><div class="fw-bold">${w.condition}</div><small class="text-secondary">CONDITION</small></div></div></div>
      </div>
      ${w.alerts?.length?`<div class="alert alert-danger"><h6>⚠️ Warnings</h6><ul class="mb-0">${w.alerts.map(a=>`<li>${a}</li>`).join('')}</ul></div>`:''}
      <div class="disclaimer-box">${w.disclaimer}</div>`;
    // 5-day forecast
    if(w.forecast?.length){
      const fc=document.getElementById('forecast-card');if(fc)fc.style.display='';
      const best=w.forecast.find(d=>d.safe_to_spray);
      let html='<div class="table-responsive"><table class="table table-sm text-nowrap mb-0"><thead><tr><th>Date</th><th>Temp</th><th>Rain</th><th>Wind</th><th>Condition</th><th>Spray</th></tr></thead><tbody>';
      w.forecast.forEach(d=>{
        const isBest=best&&d.date===best.date;
        html+=`<tr ${isBest?'class="table-success"':''}><td>${d.date}</td><td>${d.temp_min}° / ${d.temp_max}°</td><td>${d.rain_probability}%</td><td>${d.wind_max} km/h</td><td>${d.condition}</td><td>${d.safe_to_spray?(isBest?'🌟 BEST':'✅ Safe'):'❌'}</td></tr>`;
      });
      html+='</tbody></table></div>';
      if(best)html+=`<div class="alert alert-success mt-2 small mb-0">🌟 Best spray window: <strong>${best.date}</strong> — ${best.condition}, ${best.temp_min}°-${best.temp_max}°C, Wind ${best.wind_max} km/h</div>`;
      else html+='<div class="alert alert-warning mt-2 small mb-0">⚠️ No safe spray window in the next 5 days.</div>';
      document.getElementById('forecast-body').innerHTML=html;
      // Forecast chart
      if(typeof ApexCharts!=='undefined'){
        document.getElementById('forecast-chart').innerHTML='';
        new ApexCharts(document.getElementById('forecast-chart'),{
          chart:{type:'line',height:200,toolbar:{show:false}},
          series:[{name:'Max °C',data:w.forecast.map(d=>d.temp_max)},{name:'Rain %',data:w.forecast.map(d=>d.rain_probability)}],
          xaxis:{categories:w.forecast.map(d=>d.date.slice(5))},
          colors:['#ef4444','#3b82f6'],theme:{mode:'dark'},grid:{borderColor:'rgba(255,255,255,0.05)'},
          stroke:{width:[3,2],dashArray:[0,5]},
          yaxis:[{title:{text:'°C'}},{opposite:true,title:{text:'%'}}]
        }).render();
      }
    }
    // 7-day spray calendar
    loadSprayCalendar(lat,lon);
    // Start auto-refresh countdown
    startWeatherCountdown();
    _sessionStats.weather++;updateSessionStats();
  }catch(e){document.getElementById('weather-result').innerHTML=`<div class="alert alert-danger">${e.message}</div>`;toast(e.message,'error');}
  b.disabled=false;b.innerHTML='<i class="ti ti-search me-1"></i>Check';}
function useMyLoc(){navigator.geolocation?.getCurrentPosition(p=>{document.getElementById('w-lat').value=p.coords.latitude.toFixed(2);document.getElementById('w-lon').value=p.coords.longitude.toFixed(2);fetchWeather();toast('Location detected','success');},()=>toast('Access denied','error'));}

// Save/Load favorite locations
function saveLocation(){
  const lat=document.getElementById('w-lat').value,lon=document.getElementById('w-lon').value;
  let saved=JSON.parse(localStorage.getItem('pestguard_locations')||'[]');
  if(!saved.find(l=>l.lat==lat&&l.lon==lon)){saved.push({lat,lon,name:`${lat}, ${lon}`});localStorage.setItem('pestguard_locations',JSON.stringify(saved));toast('Location saved!','success');}
  renderSavedLocations();
}
function renderSavedLocations(){
  const saved=JSON.parse(localStorage.getItem('pestguard_locations')||'[]');
  const el=document.getElementById('saved-locations');if(!el)return;
  el.innerHTML=saved.map((l,i)=>`<button class="btn btn-outline-secondary btn-sm me-1" onclick="loadLoc(${i})">📍 ${l.name}</button>`).join('');
}
function loadLoc(i){const saved=JSON.parse(localStorage.getItem('pestguard_locations')||'[]');if(saved[i]){document.getElementById('w-lat').value=saved[i].lat;document.getElementById('w-lon').value=saved[i].lon;fetchWeather();}}

// Auto-refresh weather countdown
function startWeatherCountdown(){
  if(_weatherTimer)clearInterval(_weatherTimer);
  let sec=300;
  _weatherTimer=setInterval(()=>{
    sec--;const el=document.getElementById('weather-countdown');
    if(el)el.textContent=`Auto-refresh in ${Math.floor(sec/60)}:${(sec%60).toString().padStart(2,'0')}`;
    if(sec<=0){sec=300;fetchWeather();}
  },1000);
}

// Heatmap
let hmap=null;
async function initMap(){if(hmap){hmap.remove();hmap=null;}hmap=L.map('heatmap-box').setView([39,35],6);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OSM © CARTO',maxZoom:18}).addTo(hmap);
  // Click to report
  hmap.on('click',e=>{document.getElementById('h-lat').value=e.latlng.lat.toFixed(2);document.getElementById('h-lon').value=e.latlng.lng.toFixed(2);toast('Location set from map click','info');});
  loadHeatmap();
  setTimeout(()=>hmap?.invalidateSize(),200);}

async function loadHeatmap(){
  if(!hmap)return;
  // Clear existing layers except tile
  hmap.eachLayer(l=>{if(!(l instanceof L.TileLayer))hmap.removeLayer(l);});
  try{const r=await fetch('/heatmap'),j=await r.json(),data=j.data||[];
    const cl={Aphid:'#10b981','Rice Leafhopper':'#3b82f6','Corn Borer':'#f59e0b','Fall Armyworm':'#ef4444',Locust:'#8b5cf6',Whitefly:'#ec4899'};
    // Stats
    const stats=document.getElementById('heatmap-stats');
    if(stats){
      const total=data.reduce((s,p)=>s+p.count,0);
      const pestCounts={};data.forEach(p=>{pestCounts[p.pest_type]=(pestCounts[p.pest_type]||0)+p.count;});
      const topPest=Object.entries(pestCounts).sort((a,b)=>b[1]-a[1])[0];
      stats.innerHTML=`
        <div class="col"><div class="card card-lg"><div class="card-body py-2 text-center"><div class="fw-bold">${data.length}</div><small class="text-secondary">Zones</small></div></div></div>
        <div class="col"><div class="card card-lg"><div class="card-body py-2 text-center"><div class="fw-bold">${total}</div><small class="text-secondary">Reports</small></div></div></div>
        <div class="col"><div class="card card-lg"><div class="card-body py-2 text-center"><div class="fw-bold">${topPest?topPest[0]:'—'}</div><small class="text-secondary">Top Pest</small></div></div></div>
        <div class="col"><div class="card card-lg"><div class="card-body py-2 text-center"><div class="fw-bold">${Object.keys(pestCounts).length}</div><small class="text-secondary">Species</small></div></div></div>`;
    }
    data.forEach(p=>{
      const c=cl[p.pest_type]||'#94a3b8';
      const isHot=p.count>=5;
      const circle=L.circle([p.grid_lat,p.grid_lon],{radius:Math.min(p.count*800,8000),color:c,fillColor:c,fillOpacity:isHot?0.5:0.35,weight:isHot?2:1}).bindPopup(`<b>${p.pest_type}</b><br>Reports: ${p.count}${isHot?'<br><span style="color:#ef4444">🚨 Alert Zone</span>':''}`).addTo(hmap);
      if(isHot){circle.setStyle({dashArray:'4',className:'pulse-circle'});}
    });
    const lg=L.control({position:'bottomright'});lg.onAdd=()=>{const d=L.DomUtil.create('div');d.style.cssText='background:rgba(10,14,26,0.9);padding:10px;border-radius:8px;font-size:12px;color:#fff;border:1px solid rgba(255,255,255,0.1)';d.innerHTML=Object.entries(cl).map(([k,v])=>`<div style="display:flex;align-items:center;gap:6px;margin:3px 0"><span style="width:10px;height:10px;border-radius:50%;background:${v};display:inline-block"></span>${k}</div>`).join('');return d;};lg.addTo(hmap);
  }catch(e){}}

async function submitReport(){const lat=+document.getElementById('h-lat').value,lon=+document.getElementById('h-lon').value,pest=document.getElementById('h-pest').value;
  try{const r=await fetch('/heatmap/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat,lon,pest_type:pest})});const d=await r.json();
    document.getElementById('report-msg').innerHTML=`<span class="text-success">✅ Submitted (grid: ${d.grid_lat||d.data?.grid_lat}, ${d.grid_lon||d.data?.grid_lon})</span>`;toast('Report submitted!','success');loadHeatmap();
  }catch(e){toast(e.message,'error');}}

// ============= CAMERA CAPTURE =============
let _cameraStream=null;
async function openCamera(){
  try{
    _cameraStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});
    document.getElementById('camera-video').srcObject=_cameraStream;
    document.getElementById('camera-area').style.display='block';
    document.getElementById('upload-zone').style.display='none';
  }catch(e){toast('Camera access denied','error');}
}
function capturePhoto(){
  const v=document.getElementById('camera-video'),c=document.getElementById('camera-canvas');
  c.width=v.videoWidth;c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  c.toBlob(blob=>{
    const f=new File([blob],'camera-capture.jpg',{type:'image/jpeg'});
    showPrev(f);closeCamera();
  },'image/jpeg',0.9);
}
function closeCamera(){
  if(_cameraStream){_cameraStream.getTracks().forEach(t=>t.stop());_cameraStream=null;}
  document.getElementById('camera-area').style.display='none';
  if(!window._file)document.getElementById('upload-zone').style.display='';
}

// ============= PREDICTION HISTORY =============
let _predHistory=[];
function addToPredHistory(d){
  _predHistory.push({name:d.pest_name,confidence:d.confidence,time:new Date().toLocaleTimeString(),crop:d.crop});
  if(_predHistory.length>8)_predHistory.shift();
  const card=document.getElementById('pred-history-card');if(card)card.style.display='';
  const el=document.getElementById('pred-history');
  if(el)el.innerHTML=_predHistory.map(p=>`<div class="col"><div class="card card-lg"><div class="card-body py-2 text-center small"><div class="fw-bold">${p.name}</div><div class="text-${p.confidence>=0.7?'success':'warning'}">${(p.confidence*100).toFixed(0)}%</div><div class="text-secondary">${p.time}</div></div></div></div>`).join('');
  _sessionStats.predictions++;updateSessionStats();
}

// ============= PEST INFO CARD =============
async function loadPestInfo(name){
  try{const r=await fetch(`/pest-info/${encodeURIComponent(name)}`);const d=await r.json();
    if(d.found){
      const el=document.getElementById('pest-info-card');if(!el)return;el.style.display='';
      const sc={Critical:'danger',High:'danger',Medium:'warning',Low:'info'};
      el.innerHTML=`<div class="card card-lg mt-3"><div class="card-body"><h6><i class="ti ti-info-circle me-2"></i>Pest Information</h6>
        <div class="row g-3"><div class="col-md-6"><table class="table table-sm small mb-0">
        <tr><td class="text-secondary">Scientific Name</td><td class="fst-italic">${d.scientific}</td></tr>
        <tr><td class="text-secondary">Family</td><td>${d.family}</td></tr>
        <tr><td class="text-secondary">Lifecycle</td><td>${d.lifecycle}</td></tr>
        <tr><td class="text-secondary">Severity</td><td><span class="badge bg-${sc[d.severity]||'secondary'}-subtle text-${sc[d.severity]||'secondary'}-emphasis">${d.severity}</span></td></tr>
        <tr><td class="text-secondary">Host Crops</td><td>${d.crops.join(', ')}</td></tr>
        </table></div><div class="col-md-6"><p class="small text-secondary">${d.description}</p></div></div></div></div>`;
    }
  }catch(e){}
}

// ============= SHARE RESULT =============
function shareResult(){
  if(!lastPred)return;
  const text=`PestGuard AI Detection:\n🐛 ${lastPred.pest_name}\n📊 Confidence: ${(lastPred.confidence*100).toFixed(1)}%\n🌱 Crop: ${lastPred.crop||'Unknown'}\n\nPowered by PestGuard AI`;
  navigator.clipboard?.writeText(text).then(()=>toast('Result copied to clipboard!','success')).catch(()=>{});
}

// ============= ANIMATED COUNTERS =============
function animateCounters(){
  document.querySelectorAll('[data-counter]').forEach(el=>{
    const target=parseInt(el.dataset.counter);let current=0;
    const step=Math.max(1,Math.floor(target/60));
    const timer=setInterval(()=>{current+=step;if(current>=target){current=target;clearInterval(timer);}el.textContent=current.toLocaleString();},20);
  });
}

// ============= PROVIDER STATUS GRID =============
async function loadProviderGrid(){
  const grid=document.getElementById('provider-grid');if(!grid)return;
  const providers=['Gemini','Groq','OpenRouter','Cohere','Mistral','Cerebras'];
  grid.innerHTML=providers.map(p=>`<div class="col"><div class="card" style="border:1px solid rgba(255,255,255,0.08)"><div class="card-body py-2 px-3 d-flex align-items-center gap-2"><span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;box-shadow:0 0 6px #10b981"></span><span class="small fw-bold">${p}</span></div></div></div>`).join('');
}

// ============= SESSION STATS =============
let _sessionStats={predictions:0,chats:0,weather:0};
function updateSessionStats(){
  const el=document.getElementById('session-stats');if(!el)return;
  el.innerHTML=`<div class="d-flex flex-column gap-2">
    <div class="d-flex justify-content-between"><span>🔬 Predictions</span><span class="fw-bold">${_sessionStats.predictions}</span></div>
    <div class="d-flex justify-content-between"><span>💬 Chats</span><span class="fw-bold">${_sessionStats.chats}</span></div>
    <div class="d-flex justify-content-between"><span>🌤️ Weather</span><span class="fw-bold">${_sessionStats.weather}</span></div>
    <div class="d-flex justify-content-between border-top pt-2 mt-1"><span>Total</span><span class="fw-bold">${_sessionStats.predictions+_sessionStats.chats+_sessionStats.weather}</span></div>
  </div>`;
}

// ============= LIVE ACTIVITY FEED =============
async function loadActivityFeed(){
  try{const r=await fetch('/activity');const d=await r.json();
    const el=document.getElementById('activity-feed');if(!el)return;
    if(!d.actions?.length){el.innerHTML='<span class="text-secondary">No activity yet...</span>';return;}
    el.innerHTML=d.actions.map(a=>{
      const ago=Math.floor((Date.now()-new Date(a.time).getTime())/1000);
      const agoStr=ago<60?ago+'s ago':ago<3600?Math.floor(ago/60)+'m ago':Math.floor(ago/3600)+'h ago';
      return `<div class="d-flex justify-content-between py-1" style="border-bottom:1px solid rgba(255,255,255,0.04)"><span>${a.action} ${a.detail}</span><span class="text-secondary">${agoStr}</span></div>`;
    }).join('');
  }catch(e){}
}

// ============= FEATURE 1: PDF REPORT DOWNLOAD =============
async function downloadPdfReport(){
  if(!lastPred){toast('No prediction to export','error');return;}
  const {jsPDF}=window.jspdf||{};
  if(!jsPDF){toast('PDF library not loaded','error');return;}
  const doc=new jsPDF();const d=lastPred;
  // Header
  doc.setFillColor(16,185,129);doc.rect(0,0,210,35,'F');
  doc.setTextColor(255);doc.setFontSize(20);doc.text('PestGuard AI — Pest Report',15,18);
  doc.setFontSize(10);doc.text('Generated: '+new Date().toLocaleString(),15,28);
  // Pest Info
  doc.setTextColor(0);doc.setFontSize(16);doc.text('Identification Result',15,50);
  doc.setFontSize(12);
  doc.text('Pest Name: '+d.pest_name,15,62);
  doc.text('Confidence: '+(d.confidence*100).toFixed(1)+'%',15,72);
  doc.text('Category ID: '+d.category_id,15,82);
  doc.text('Crop: '+(d.crop||'Unknown'),15,92);
  doc.text('Timestamp: '+d.timestamp,15,102);
  // VLM
  doc.setFontSize(14);doc.text('Visual Analysis',15,120);
  doc.setFontSize(10);const vlmLines=doc.splitTextToSize(d.vlm_description||'N/A',180);
  doc.text(vlmLines,15,130);
  // Top-3
  if(d.top_3?.length){
    let y=130+vlmLines.length*6+10;
    doc.setFontSize(14);doc.text('Top Predictions',15,y);y+=10;
    doc.setFontSize(10);
    d.top_3.forEach((p,i)=>{
      doc.text(`${i+1}. ${p.pest_name} — ${(p.confidence*100).toFixed(1)}% (${p.crop})`,15,y);y+=8;
    });
  }
  // Treatment
  const infoResp=await fetch('/pest-info/'+encodeURIComponent(d.pest_name)).catch(()=>null);
  if(infoResp){
    const info=await infoResp.json();
    if(info.found&&info.treatment){
      let y=200;doc.setFontSize(14);doc.text('Recommended Treatment Plan',15,y);y+=10;doc.setFontSize(9);
      info.treatment.forEach(t=>{
        doc.text(`Day ${t.day}: ${t.step} — ${t.desc} [${t.method}]`,15,y);y+=7;
      });
    }
  }
  // Footer
  doc.setFontSize(8);doc.setTextColor(150);
  doc.text('PestGuard AI — Department 2 Capstone · BAU 2026. This is a mock prediction.',15,285);
  doc.save(`pestguard-report-${d.pest_name.replace(/\s/g,'_')}-${Date.now()}.pdf`);
  toast('PDF report downloaded!','success');
}

// ============= FEATURE 2: ONBOARDING TOUR =============
const TOUR_STEPS=[
  {icon:'🌿',title:'Welcome to PestGuard AI!',text:'Your intelligent agricultural pest recognition system powered by Deep Learning and AI.'},
  {icon:'📷',title:'Pest Prediction',text:'Upload or photograph a pest image. Our CNN model identifies it with confidence scores and top-3 alternatives.'},
  {icon:'💬',title:'AI Advisor',text:'Chat with our RAG-powered advisor. Get treatment advice, pesticide recommendations, and safety guidelines.'},
  {icon:'🌤️',title:'Weather & Spray Safety',text:'Real-time weather data with 5-day forecasts. Automatic spray safety analysis based on wind, rain, and temperature.'},
  {icon:'🗺️',title:'Outbreak Heatmap',text:'Interactive map showing regional pest outbreaks. Report sightings and view temporal trends.'},
  {icon:'⌨️',title:'Pro Tips',text:'Use keyboard shortcuts (press ? anytime). Your chat history and predictions are auto-saved. Press Ctrl+D for PDF reports.'},
];
let _tourStep=0;
function showTour(){
  if(localStorage.getItem('pg_tour_done'))return;
  _tourStep=0;renderTourStep();
  document.getElementById('tour-overlay').style.display='';
}
function renderTourStep(){
  const s=TOUR_STEPS[_tourStep];
  document.getElementById('tour-content').innerHTML=`<div style="font-size:3rem;margin-bottom:12px">${s.icon}</div><h4>${s.title}</h4><p class="text-secondary mt-2">${s.text}</p>`;
  document.getElementById('tour-dots').innerHTML=TOUR_STEPS.map((_,i)=>`<span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin:0 3px;background:${i===_tourStep?'#10b981':'rgba(255,255,255,0.2)'}"></span>`).join('');
  document.getElementById('tour-next').textContent=_tourStep===TOUR_STEPS.length-1?'Get Started!':'Next →';
}
function nextTourStep(){
  _tourStep++;
  if(_tourStep>=TOUR_STEPS.length){skipTour();return;}
  renderTourStep();
}
function skipTour(){
  document.getElementById('tour-overlay').style.display='none';
  localStorage.setItem('pg_tour_done','1');
}

// ============= FEATURE 3: SESSION PERSISTENCE =============
function saveChatToStorage(){try{localStorage.setItem('pg_chatH',JSON.stringify(chatH.slice(-50)));}catch(e){}}
function loadChatFromStorage(){
  try{
    const saved=JSON.parse(localStorage.getItem('pg_chatH')||'[]');
    if(saved.length){
      chatH.push(...saved);
      const box=document.getElementById('chat-box');if(!box)return;
      saved.forEach(m=>{
        const div=document.createElement('div');div.className='chat-msg '+(m.role==='user'?'user':'bot');
        div.innerHTML=m.content||m.raw||'';box.appendChild(div);
      });
      box.scrollTop=box.scrollHeight;
    }
  }catch(e){}
}
function savePredToStorage(){try{localStorage.setItem('pg_predH',JSON.stringify(_predHistory.slice(-10)));}catch(e){}}
function loadPredFromStorage(){try{_predHistory=JSON.parse(localStorage.getItem('pg_predH')||'[]');renderPredHistory();}catch(e){}}
// Patch chat send to auto-save
const _origSendChat=typeof sendChat==='function'?sendChat:null;

// ============= FEATURE 4: KEYBOARD SHORTCUTS =============
document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
  if(e.key==='?'){e.preventDefault();new bootstrap.Modal(document.getElementById('shortcutsModal')).show();return;}
  if(e.ctrlKey){
    switch(e.key){
      case '1':e.preventDefault();nav('dashboard');break;
      case '2':e.preventDefault();nav('predict');break;
      case '3':e.preventDefault();nav('chat');break;
      case '4':e.preventDefault();nav('weather');break;
      case '5':e.preventDefault();nav('heatmap');break;
      case 'e':case 'E':e.preventDefault();if(typeof exportChat==='function')exportChat();break;
      case 'd':case 'D':e.preventDefault();downloadPdfReport();break;
    }
  }
});

// ============= FEATURE 5: SKELETON LOADING =============
function showSkeleton(id,rows=3){
  const el=document.getElementById(id);if(!el)return;
  el.innerHTML=Array(rows).fill(0).map(()=>'<div class="skeleton-line"></div>').join('');
}

// ============= FEATURE 6: OFFLINE DETECTION =============
function updateOnlineStatus(){
  const banner=document.getElementById('offline-banner');if(!banner)return;
  if(!navigator.onLine){banner.style.display='';document.body.style.paddingTop='50px';}
  else{banner.style.display='none';document.body.style.paddingTop='';}
}
window.addEventListener('online',()=>{updateOnlineStatus();toast('Back online!','success');});
window.addEventListener('offline',()=>{updateOnlineStatus();toast('You are offline','error');});

// ============= FEATURE 7: PRINT MODE =============
function printReport(){
  if(!lastPred){toast('No prediction to print','error');return;}
  window.print();
}

// ============= FEATURE 8: TREATMENT TIMELINE =============
async function loadTreatmentTimeline(pestName){
  const el=document.getElementById('treatment-timeline');if(!el)return;
  try{
    const r=await fetch('/pest-info/'+encodeURIComponent(pestName));const d=await r.json();
    if(!d.found||!d.treatment){el.innerHTML='<span class="text-secondary small">No treatment data available.</span>';return;}
    const methodColors={Inspection:'#3b82f6',Biological:'#10b981',Chemical:'#f59e0b',IPM:'#8b5cf6',Cultural:'#06b6d4',Organic:'#22c55e',Mechanical:'#ec4899',Regulatory:'#ef4444',Genetic:'#14b8a6','Resistance Mgmt':'#f97316'};
    el.innerHTML='<h6 class="mb-3"><i class="ti ti-timeline-event me-1"></i>Recommended Treatment Plan</h6>'+
      '<div class="position-relative" style="padding-left:30px">'+
      '<div style="position:absolute;left:12px;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.08)"></div>'+
      d.treatment.map((t,i)=>{
        const col=methodColors[t.method]||'#6b7280';
        return `<div class="mb-3 position-relative" style="animation:card-enter 0.4s ease ${i*0.15}s both">
          <div style="position:absolute;left:-24px;top:4px;width:12px;height:12px;border-radius:50%;background:${col};box-shadow:0 0 8px ${col}60"></div>
          <div class="card" style="border-left:3px solid ${col}"><div class="card-body py-2 px-3">
            <div class="d-flex justify-content-between align-items-center">
              <strong class="small">${t.step}</strong>
              <span class="badge" style="background:${col}20;color:${col};font-size:10px">Day ${t.day} · ${t.method}</span>
            </div>
            <div class="small text-secondary mt-1">${t.desc}</div>
          </div></div>
        </div>`;
      }).join('')+'</div>';
  }catch(e){el.innerHTML='<span class="text-secondary small">Failed to load treatment.</span>';}
}

// ============= FEATURE 9: SMART NOTIFICATIONS =============
let _lastWeatherSafe=null;
async function checkSmartNotifications(){
  try{
    // Weather change notification
    const wr=await fetch('/weather/41.0/29.0');const w=await wr.json();
    if(_lastWeatherSafe!==null&&_lastWeatherSafe!==w.safe_to_spray){
      if(!w.safe_to_spray)toast('⚠️ Weather changed — NOT safe to spray!','error');
      else toast('✅ Weather improved — Safe to spray now!','success');
    }
    _lastWeatherSafe=w.safe_to_spray;
    // Outbreak alert
    const hr=await fetch('/heatmap');const h=await hr.json();
    const highZones=h.filter(z=>(z.count||0)>=20);
    if(highZones.length>0){
      const zone=highZones[0];
      toast(`🚨 High outbreak: ${zone.pest_type} in ${zone.region} (${zone.count} reports)`,'error');
    }
  }catch(e){}
}

// ============= ENHANCED INIT =============
loadStatus();initCharts();animateCounters();loadProviderGrid();updateSessionStats();loadActivityFeed();renderSavedLocations();
loadChatFromStorage();loadPredFromStorage();updateOnlineStatus();
setInterval(loadStatus,30000);
setInterval(loadActivityFeed,10000);
setInterval(checkSmartNotifications,300000);
setTimeout(showTour,1500);

// ============= PARTICLE BACKGROUND =============
(function(){
  const c=document.getElementById('particle-canvas');if(!c)return;
  const ctx=c.getContext('2d');
  let particles=[];const N=35;
  function resize(){c.width=c.offsetWidth;c.height=c.offsetHeight;}
  resize();window.addEventListener('resize',resize);
  for(let i=0;i<N;i++)particles.push({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*2.5+0.5,dx:(Math.random()-0.5)*0.6,dy:(Math.random()-0.5)*0.4,o:Math.random()*0.5+0.2});
  function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    particles.forEach(p=>{
      p.x+=p.dx;p.y+=p.dy;
      if(p.x<0)p.x=c.width;if(p.x>c.width)p.x=0;
      if(p.y<0)p.y=c.height;if(p.y>c.height)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(16,185,129,${p.o})`;ctx.fill();
      // Glow
      ctx.beginPath();ctx.arc(p.x,p.y,p.r*3,0,Math.PI*2);
      ctx.fillStyle=`rgba(16,185,129,${p.o*0.15})`;ctx.fill();
    });
    // Connect nearby particles with lines
    for(let i=0;i<particles.length;i++){
      for(let j=i+1;j<particles.length;j++){
        const dx=particles[i].x-particles[j].x,dy=particles[i].y-particles[j].y;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<100){ctx.beginPath();ctx.moveTo(particles[i].x,particles[i].y);ctx.lineTo(particles[j].x,particles[j].y);
          ctx.strokeStyle=`rgba(16,185,129,${0.08*(1-dist/100)})`;ctx.stroke();}
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();

// ============= TYPEWRITER EFFECT =============
(function(){
  const el=document.getElementById('typewriter-text');if(!el)return;
  const text='PestGuard AI Dashboard';let i=0;
  function type(){
    if(i<=text.length){el.textContent=text.slice(0,i);i++;setTimeout(type,80);}
    else{const cursor=document.querySelector('.typewriter-cursor');if(cursor)setTimeout(()=>{cursor.style.display='none';},2000);}
  }
  setTimeout(type,500);
})();

// ============= FEATURE: LIVE ANALYTICS =============
let _analyticsCharts={};
async function loadAnalytics(){
  try{
    const r=await fetch('/analytics/system');const d=await r.json();
    // Metrics cards
    const m=document.getElementById('analytics-metrics');if(m){
      m.innerHTML=[
        {icon:'ti-clock',label:'Uptime',value:d.uptime_formatted,color:'#10b981'},
        {icon:'ti-activity',label:'Total Requests',value:d.total_requests.toLocaleString(),color:'#3b82f6'},
        {icon:'ti-gauge',label:'Avg Response',value:d.avg_response_ms+'ms',color:'#f59e0b'},
        {icon:'ti-server',label:'Providers',value:d.active_providers,color:'#8b5cf6'}
      ].map(c=>`<div class="col"><div class="card card-lg"><div class="card-body py-3">
        <div class="d-flex align-items-center gap-2 mb-1"><i class="ti ${c.icon}" style="color:${c.color}"></i><small class="text-secondary">${c.label}</small></div>
        <div class="fs-4 fw-bold">${c.value}</div>
      </div></div></div>`).join('');
    }
    // Response Time Chart
    if(!_analyticsCharts.rt){
      _analyticsCharts.rt=new ApexCharts(document.getElementById('chart-response-time'),{
        chart:{type:'area',height:250,background:'transparent',toolbar:{show:false},animations:{enabled:true}},
        series:[{name:'Response Time',data:[]}],
        xaxis:{categories:[],labels:{style:{colors:'#888'}}},
        yaxis:{labels:{style:{colors:'#888'},formatter:v=>v+'ms'}},
        stroke:{curve:'smooth',width:2},colors:['#10b981'],
        fill:{type:'gradient',gradient:{shadeIntensity:1,opacityFrom:0.4,opacityTo:0.05}},
        grid:{borderColor:'rgba(255,255,255,0.05)'},theme:{mode:'dark'},
        tooltip:{theme:'dark'}
      });_analyticsCharts.rt.render();
    }
    _analyticsCharts.rt.updateSeries([{name:'Response Time',data:d.response_times.map(r=>r.ms)}]);
    _analyticsCharts.rt.updateOptions({xaxis:{categories:d.response_times.map(r=>r.time.split('T')[1]?.slice(0,8)||'')}});

    // Provider Pie
    if(!_analyticsCharts.pie){
      _analyticsCharts.pie=new ApexCharts(document.getElementById('chart-provider-pie'),{
        chart:{type:'donut',height:250,background:'transparent'},
        series:[],labels:[],
        colors:['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ec4899','#06b6d4'],
        theme:{mode:'dark'},legend:{position:'bottom',labels:{colors:'#888'}},
        plotOptions:{pie:{donut:{size:'55%'}}}
      });_analyticsCharts.pie.render();
    }
    const pNames=Object.keys(d.provider_usage),pVals=Object.values(d.provider_usage);
    _analyticsCharts.pie.updateSeries(pVals);
    _analyticsCharts.pie.updateOptions({labels:pNames});

    // Endpoint Bar
    if(!_analyticsCharts.bar){
      _analyticsCharts.bar=new ApexCharts(document.getElementById('chart-endpoint-bar'),{
        chart:{type:'bar',height:220,background:'transparent',toolbar:{show:false}},
        series:[{name:'Requests',data:[]}],
        xaxis:{categories:[]},colors:['#3b82f6'],
        theme:{mode:'dark'},plotOptions:{bar:{borderRadius:4,horizontal:true}},
        grid:{borderColor:'rgba(255,255,255,0.05)'}
      });_analyticsCharts.bar.render();
    }
    _analyticsCharts.bar.updateSeries([{name:'Requests',data:Object.values(d.endpoint_counts)}]);
    _analyticsCharts.bar.updateOptions({xaxis:{categories:Object.keys(d.endpoint_counts).map(e=>'/'+e)}});

    // System Log
    const logEl=document.getElementById('analytics-log');if(logEl){
      logEl.innerHTML=d.response_times.slice(-15).reverse().map(r=>{
        const col=r.ms>500?'#ef4444':r.ms>200?'#f59e0b':'#10b981';
        return `<div class="py-1" style="border-bottom:1px solid rgba(255,255,255,0.04)"><span style="color:${col}">●</span> <span class="text-secondary">${r.time.split('T')[1]?.slice(0,8)||''}</span> <span>${r.path||'/'}</span> <span class="float-end" style="color:${col}">${r.ms}ms</span></div>`;
      }).join('');
    }
  }catch(e){console.error('Analytics error:',e);}
}

// ============= FEATURE: SIDE-BY-SIDE COMPARISON =============
let _cmpFiles={a:null,b:null};
function cmpPreview(side,input){
  const f=input.files[0];if(!f)return;
  _cmpFiles[side]=f;
  const r=new FileReader();r.onload=e=>{
    const img=document.getElementById('cmp-img-'+side);img.src=e.target.result;img.style.display='';
    document.getElementById('cmp-zone-'+side).style.display='none';
  };r.readAsDataURL(f);
  // Enable compare button if both loaded
  if(_cmpFiles.a&&_cmpFiles.b)document.getElementById('cmp-btn').disabled=false;
}
async function runComparison(){
  const btn=document.getElementById('cmp-btn');btn.disabled=true;btn.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span>Analyzing...';
  const results=[];
  for(const side of ['a','b']){
    const fd=new FormData();fd.append('file',_cmpFiles[side]);
    try{const r=await fetch('/predict',{method:'POST',body:fd});const d=await r.json();results.push(d);
      const cc=d.confidence>=0.7?'#10b981':d.confidence>=0.5?'#f59e0b':'#ef4444';
      document.getElementById('cmp-result-'+side).innerHTML=`
        <div class="mt-2">${confGauge(d.confidence*100,cc)}</div>
        <div class="fs-5 fw-bold">${d.pest_name}</div>
        <div class="small text-secondary">${d.crop||'Unknown'} · ${d.category_id}</div>`;
    }catch(e){document.getElementById('cmp-result-'+side).innerHTML=`<div class="text-danger small">${e.message}</div>`;}
  }
  // Comparison summary
  if(results.length===2){
    const same=results[0].pest_name===results[1].pest_name;
    const confDiff=Math.abs(results[0].confidence-results[1].confidence)*100;
    document.getElementById('cmp-comparison').innerHTML=`
      <div class="card card-lg"><div class="card-body">
        <h5 class="mb-3"><i class="ti ti-arrows-diff me-2"></i>Comparison Result</h5>
        <div class="text-center mb-3"><span class="badge fs-6 ${same?'bg-success':'bg-warning'} px-4 py-2">${same?'✅ SAME PEST':'⚠️ DIFFERENT PESTS'}</span></div>
        <table class="table table-sm small">
          <thead><tr><th></th><th>Image A</th><th>Image B</th></tr></thead>
          <tbody>
            <tr><td>Pest</td><td class="fw-bold">${results[0].pest_name}</td><td class="fw-bold">${results[1].pest_name}</td></tr>
            <tr><td>Confidence</td><td>${(results[0].confidence*100).toFixed(1)}%</td><td>${(results[1].confidence*100).toFixed(1)}%</td></tr>
            <tr><td>Crop</td><td>${results[0].crop||'—'}</td><td>${results[1].crop||'—'}</td></tr>
            <tr><td>Category</td><td>${results[0].category_id}</td><td>${results[1].category_id}</td></tr>
          </tbody>
        </table>
        <div class="small text-secondary text-center">Confidence difference: ${confDiff.toFixed(1)}%</div>
      </div></div>`;
  }
  btn.disabled=false;btn.innerHTML='<i class="ti ti-arrows-diff me-2"></i>Compare Both';
}

// Auto-refresh analytics when on that page
setInterval(()=>{if(document.getElementById('page-analytics')?.classList.contains('active'))loadAnalytics();},5000);

// ============= PEST LIBRARY =============
let _libraryData=[];
async function loadPestLibrary(){
  if(_libraryData.length){renderLibrary(_libraryData);return;}
  try{
    const r=await fetch('/pest-library');const d=await r.json();
    _libraryData=d.pests||[];
    renderLibrary(_libraryData);
  }catch(e){document.getElementById('lib-grid').innerHTML='<div class="text-danger">Failed to load library.</div>';}
}
function filterLibrary(){
  const q=(document.getElementById('lib-search')?.value||'').toLowerCase();
  const crop=document.getElementById('lib-crop')?.value||'all';
  const sev=document.getElementById('lib-severity')?.value||'all';
  const filtered=_libraryData.filter(p=>{
    if(q&&!p.pest_name.toLowerCase().includes(q)&&!p.scientific.toLowerCase().includes(q))return false;
    if(crop!=='all'&&!p.crops.some(c=>c.toLowerCase().includes(crop.toLowerCase())))return false;
    if(sev!=='all'&&p.severity!==sev)return false;
    return true;
  });
  renderLibrary(filtered);
}
function renderLibrary(pests){
  const grid=document.getElementById('lib-grid');if(!grid)return;
  if(!pests.length){grid.innerHTML='<div class="col-12 text-center text-secondary py-5"><i class="ti ti-search-off fs-1"></i><p class="mt-2">No pests match your filters.</p></div>';return;}
  const sevColors={High:'#ef4444',Medium:'#f59e0b',Critical:'#dc2626',Low:'#10b981'};
  grid.innerHTML=pests.map(p=>{
    const sc=sevColors[p.severity]||'#6b7280';
    const cropTags=p.crops.map(c=>`<span class="badge bg-dark bg-opacity-50 me-1" style="font-size:10px">${c}</span>`).join('');
    const steps=p.treatment?p.treatment.map(t=>`<div class="d-flex align-items-center gap-2 mb-1"><span class="badge bg-dark bg-opacity-50" style="font-size:9px;min-width:45px">Day ${t.day}</span><span class="small text-secondary">${t.step}</span></div>`).join(''):'<span class="small text-secondary">No treatment data</span>';
    return `<div class="col-md-6 col-lg-4">
      <div class="card card-lg h-100" style="border-left:3px solid ${sc}">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <h6 class="mb-0">${p.pest_name}</h6>
              <small class="text-secondary fst-italic">${p.scientific}</small>
            </div>
            <span class="badge" style="background:${sc}20;color:${sc};font-size:10px">${p.severity}</span>
          </div>
          <p class="small text-secondary mb-2" style="line-height:1.5">${p.description}</p>
          <div class="mb-2">${cropTags}</div>
          <div class="d-flex gap-3 small text-secondary mb-2">
            <span><i class="ti ti-dna me-1"></i>${p.family}</span>
            <span><i class="ti ti-clock me-1"></i>${p.lifecycle}</span>
          </div>
          <div class="mt-2 pt-2" style="border-top:1px solid rgba(255,255,255,0.06)">
            <div class="small fw-bold mb-1"><i class="ti ti-first-aid-kit me-1"></i>Treatment Steps</div>
            ${steps}
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
}

// ============= 7-DAY SPRAY CALENDAR =============
async function loadSprayCalendar(lat,lon){
  const card=document.getElementById('spray-calendar-card');if(!card)return;
  try{
    const r=await fetch(`/weather/forecast/${lat}/${lon}`);const d=await r.json();
    if(!d.forecast||!d.forecast.length){card.style.display='none';return;}
    card.style.display='block';
    const cal=document.getElementById('spray-calendar');
    const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    cal.innerHTML=d.forecast.map((day,i)=>{
      const dt=new Date(day.date);
      const dayName=i===0?'Today':i===1?'Tomorrow':days[dt.getDay()];
      const safe=day.safe_to_spray;
      const bg=safe?'rgba(16,185,129,0.15)':'rgba(239,68,68,0.15)';
      const border=safe?'#10b981':'#ef4444';
      const icon=safe?'✅':'❌';
      return `<div class="text-center p-3 rounded-3 flex-fill" style="background:${bg};border:1px solid ${border}30;min-width:110px;animation:card-enter 0.4s ease ${i*0.1}s both">
        <div class="small fw-bold mb-1">${dayName}</div>
        <div class="small text-secondary mb-2">${dt.toLocaleDateString('en',{month:'short',day:'numeric'})}</div>
        <div class="fs-4 mb-1">${icon}</div>
        <div class="small fw-bold" style="color:${border}">${safe?'SAFE':'UNSAFE'}</div>
        <div class="small text-secondary mt-1">${day.temp_max}°C · ${day.rain_prob}%🌧</div>
        <div class="small text-secondary">${day.wind_max} km/h 💨</div>
      </div>`;
    }).join('');
  }catch(e){card.style.display='none';}
}

// ============= FEATURE 1+2: ECONOMIC IMPACT CALCULATOR =============
let _econPestList=[];
async function initEconomics(){
  // Load pest library for dropdown
  if(!_econPestList.length){
    try{
      const r=await fetch('/pest-library');const d=await r.json();
      _econPestList=d.pests||[];
      const sel=document.getElementById('econ-pest');
      sel.innerHTML='<option>Select pest...</option>'+_econPestList.map(p=>`<option value="${p.pest_name}">${p.pest_name} (${p.severity})</option>`).join('');
    }catch(e){}
  }
  // Auto-fill from last prediction
  if(lastPred){
    document.getElementById('econ-pest').value=lastPred.pest_name;
    updateEconCrop();
    document.getElementById('econ-autofill').style.display='';
    document.getElementById('econ-autofill').innerHTML=`<span class="text-info"><i class="ti ti-link me-1"></i>Auto-filled from prediction: <strong>${lastPred.pest_name}</strong> (${(lastPred.confidence*100).toFixed(0)}%)</span>`;
  }
}

function updateEconCrop(){
  const pestName=document.getElementById('econ-pest').value;
  const pest=_econPestList.find(p=>p.pest_name===pestName);
  const cropSel=document.getElementById('econ-crop');
  const stageSel=document.getElementById('econ-stage');
  if(pest&&pest.crops){
    cropSel.innerHTML=pest.crops.map(c=>`<option>${c}</option>`).join('');
    // Load growth stages for selected crop
    const crop=pest.crops[0];
    loadCropStages(crop,stageSel);
  }
}

async function loadCropStages(crop,selectEl){
  try{
    const r=await fetch(`/crop-stages/${encodeURIComponent(crop)}`);const d=await r.json();
    selectEl.innerHTML='<option value="">Any stage</option>'+d.stages.map(s=>`<option value="${s.code}">${s.name} (${s.duration_days} days)</option>`).join('');
  }catch(e){selectEl.innerHTML='<option value="">Any stage</option>';}
}

// Listen for crop change to update stages
document.getElementById('econ-crop')?.addEventListener('change',function(){
  loadCropStages(this.value,document.getElementById('econ-stage'));
});

async function calcEconomicImpact(){
  const pest=document.getElementById('econ-pest').value;
  const crop=document.getElementById('econ-crop').value;
  const field=parseFloat(document.getElementById('econ-field').value)||1;
  const level=document.getElementById('econ-level').value;
  const stage=document.getElementById('econ-stage').value;
  if(!pest||pest.startsWith('Select')){toast('Please select a pest','error');return;}
  const btn=document.getElementById('econ-btn');btn.disabled=true;btn.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span>Calculating...';
  try{
    const r=await fetch('/economic-impact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      pest_name:pest,crop:crop,field_size_ha:field,infestation_level:level,growth_stage:stage||null
    })});
    const d=await r.json();
    renderEconomicResult(d);
  }catch(e){document.getElementById('econ-result').innerHTML=`<div class="alert alert-danger">${e.message}</div>`;toast(e.message,'error');}
  btn.disabled=false;btn.innerHTML='<i class="ti ti-calculator me-1"></i>Calculate';
}

function renderEconomicResult(d){
  const yi=d.yield_impact;
  const tc=d.treatment_costs;
  const roi=d.roi_analysis;
  const urgColors={EMERGENCY:'#dc2626',HIGH:'#ef4444',MODERATE:'#f59e0b',LOW:'#10b981'};
  const uc=urgColors[d.urgency]||'#6b7280';

  // ROI gauge
  function roiGauge(value,label,color){
    const capped=Math.min(value,30);const pct=Math.min(100,(capped/30)*100);
    const r=40,c=2*Math.PI*r,off=c-(pct/100)*c;
    return `<div class="text-center"><svg width="100" height="100" viewBox="0 0 100 100"><circle cx="50" cy="50" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/><circle cx="50" cy="50" r="${r}" fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${off}" transform="rotate(-90 50 50)" style="transition:all 1s"/><text x="50" y="48" text-anchor="middle" fill="#fff" font-size="16" font-weight="bold">${value}:1</text><text x="50" y="62" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="8">ROI</text></svg><div class="small mt-1">${label}</div></div>`;
  }

  let stageHtml='';
  if(d.stage_vulnerability){
    const sv=d.stage_vulnerability;
    const slColors={Critical:'#dc2626',High:'#ef4444',Medium:'#f59e0b',Low:'#10b981',Unknown:'#6b7280'};
    const sc=slColors[sv.level]||'#6b7280';
    stageHtml=`<div class="card card-lg mt-3"><div class="card-body">
      <h6><i class="ti ti-seedling me-2"></i>Growth Stage Vulnerability</h6>
      <div class="d-flex align-items-center gap-3 mb-2">
        <span class="badge fs-6 px-3 py-2" style="background:${sc}20;color:${sc}">${sv.level} Risk</span>
        <span class="small text-secondary">Stage modifier: ${sv.modifier}×</span>
      </div>
      <p class="small text-secondary mb-0">${sv.note}</p>
    </div></div>`;
  }

  document.getElementById('econ-result').innerHTML=`
    <!-- Urgency Banner -->
    <div class="text-center mb-4">
      <span class="safety-pill" style="background:${uc}20;color:${uc};border:1px solid ${uc}50;animation:${d.urgency==='EMERGENCY'?'pulse-red 2s infinite':'none'}">
        ${d.urgency==='EMERGENCY'?'🚨':''}${d.urgency==='HIGH'?'⚠️':''}${d.urgency==='MODERATE'?'🟡':''}${d.urgency==='LOW'?'✅':''}
        ${d.urgency} PRIORITY
      </span>
    </div>

    <!-- Key Metrics -->
    <div class="row row-cols-2 row-cols-md-4 g-3 mb-4">
      <div class="col"><div class="card card-lg text-center"><div class="card-body py-3">
        <div class="fs-1">💰</div>
        <div class="fs-4 fw-bold" style="color:#ef4444">$${yi.potential_loss_usd.toLocaleString()}</div>
        <small class="text-secondary">Potential Loss</small>
      </div></div></div>
      <div class="col"><div class="card card-lg text-center"><div class="card-body py-3">
        <div class="fs-1">📉</div>
        <div class="fs-4 fw-bold" style="color:#f59e0b">${yi.adjusted_loss_percent}%</div>
        <small class="text-secondary">Yield Loss</small>
      </div></div></div>
      <div class="col"><div class="card card-lg text-center"><div class="card-body py-3">
        <div class="fs-1">🌾</div>
        <div class="fs-4 fw-bold">${yi.estimated_loss_tons} t</div>
        <small class="text-secondary">Tonnage Lost</small>
      </div></div></div>
      <div class="col"><div class="card card-lg text-center"><div class="card-body py-3">
        <div class="fs-1">💵</div>
        <div class="fs-4 fw-bold" style="color:#10b981">$${d.crop_economics.total_field_value.toLocaleString()}</div>
        <small class="text-secondary">Field Value</small>
      </div></div></div>
    </div>

    <!-- ROI & Treatment Comparison -->
    <div class="row g-4 mb-4">
      <div class="col-md-4"><div class="card card-lg h-100"><div class="card-body text-center">
        <h6 class="mb-3"><i class="ti ti-chart-arrows me-1"></i>Treatment ROI</h6>
        <div class="d-flex justify-content-around">
          ${roiGauge(roi.ipm_roi,'IPM','#10b981')}
          ${roiGauge(roi.chemical_roi,'Chemical','#f59e0b')}
        </div>
        <div class="mt-3"><span class="badge bg-success-subtle text-success-emphasis">Best: ${roi.best_strategy}</span></div>
      </div></div></div>
      <div class="col-md-8"><div class="card card-lg h-100"><div class="card-body">
        <h6 class="mb-3"><i class="ti ti-receipt me-1"></i>Treatment Cost Comparison</h6>
        <table class="table table-sm small mb-0">
          <thead><tr><th>Strategy</th><th>Cost/ha</th><th>Total Cost</th><th>Net Saving</th><th>ROI</th></tr></thead>
          <tbody>
            <tr class="${roi.best_strategy==='IPM'?'table-success':''}"><td><span class="badge bg-success-subtle text-success-emphasis">🌿 IPM Integrated</span></td><td>$${tc.ipm_integrated.per_ha}</td><td>$${tc.ipm_integrated.total.toLocaleString()}</td><td class="text-success fw-bold">$${roi.ipm_net_saving.toLocaleString()}</td><td>${roi.ipm_roi}:1</td></tr>
            <tr class="${roi.best_strategy==='Chemical'?'table-warning':''}"><td><span class="badge bg-warning-subtle text-warning-emphasis">🧪 Chemical Only</span></td><td>$${tc.chemical_only.per_ha}</td><td>$${tc.chemical_only.total.toLocaleString()}</td><td class="text-success fw-bold">$${roi.chemical_net_saving.toLocaleString()}</td><td>${roi.chemical_roi}:1</td></tr>
            <tr><td><span class="badge bg-info-subtle text-info-emphasis">🍃 Organic</span></td><td>$${tc.organic.per_ha}</td><td>$${tc.organic.total.toLocaleString()}</td><td>—</td><td>—</td></tr>
          </tbody>
        </table>
      </div></div></div>
    </div>

    <!-- Recommendation -->
    <div class="card card-lg mb-3" style="border-left:4px solid ${uc}"><div class="card-body">
      <h6><i class="ti ti-bulb me-2" style="color:${uc}"></i>Recommendation</h6>
      <p class="mb-0">${d.recommendation}</p>
    </div></div>

    ${stageHtml}

    <!-- Crop Economics -->
    <div class="card card-lg mt-3"><div class="card-body">
      <h6><i class="ti ti-coins me-2"></i>Crop Economics (${d.crop})</h6>
      <div class="row row-cols-3 g-2 small">
        <div class="col"><span class="text-secondary">Market Price:</span> <strong>$${d.crop_economics.price_per_ton}/ton</strong></div>
        <div class="col"><span class="text-secondary">Avg Yield:</span> <strong>${d.crop_economics.yield_per_ha} t/ha</strong></div>
        <div class="col"><span class="text-secondary">Value/ha:</span> <strong>$${d.crop_economics.value_per_ha.toLocaleString()}</strong></div>
      </div>
    </div></div>
  `;
}

// ============= FEATURE 5: FEEDBACK HUB =============
async function initFeedbackPage(){
  // Show last prediction info
  const info=document.getElementById('feedback-pred-info');
  if(lastPred){
    info.innerHTML=`<div class="alert alert-info small mb-0"><i class="ti ti-bug me-1"></i>Latest prediction: <strong>${lastPred.pest_name}</strong> (${(lastPred.confidence*100).toFixed(1)}% confidence) · Crop: ${lastPred.crop||'Unknown'}</div>`;
  } else {
    info.innerHTML='<div class="alert alert-secondary small mb-0">No predictions yet. Run a prediction first to provide feedback.</div>';
  }
  // Populate pest dropdown for corrections
  if(_libraryData.length){
    document.getElementById('fb-actual-pest').innerHTML=_libraryData.map(p=>`<option>${p.pest_name}</option>`).join('');
  } else {
    try{
      const r=await fetch('/pest-library');const d=await r.json();
      _libraryData=d.pests||[];
      document.getElementById('fb-actual-pest').innerHTML=_libraryData.map(p=>`<option>${p.pest_name}</option>`).join('');
    }catch(e){}
  }
  loadFeedbackAnalytics();
}

function showCorrectionForm(){
  document.getElementById('feedback-correction').style.display='';
}

async function submitFeedback(isCorrect){
  if(!lastPred){toast('No prediction to give feedback on','error');return;}
  const body={
    session_id:sid,
    prediction_pest:lastPred.pest_name,
    confidence:lastPred.confidence,
    is_correct:isCorrect,
  };
  if(!isCorrect){
    body.actual_pest=document.getElementById('fb-actual-pest').value;
    body.comments=document.getElementById('fb-comments').value;
  }
  try{
    const r=await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    document.getElementById('feedback-msg').innerHTML=`<div class="alert alert-success small">${d.message} (Total feedback: ${d.total_feedback})</div>`;
    document.getElementById('feedback-correction').style.display='none';
    toast(isCorrect?'Thanks for confirming!':'Correction recorded — thank you!','success');
    loadFeedbackAnalytics();
  }catch(e){toast('Failed to submit','error');}
}

async function loadFeedbackAnalytics(){
  const el=document.getElementById('feedback-analytics');if(!el)return;
  try{
    const r=await fetch('/feedback/analytics');const d=await r.json();
    if(!d.total_feedback||d.total_feedback===0){
      el.innerHTML='<div class="card card-lg"><div class="card-body text-center text-secondary py-5"><i class="ti ti-chart-pie fs-1"></i><p class="mt-2">No feedback data yet. Start by verifying predictions!</p></div></div>';
      return;
    }

    // Accuracy donut
    const accColor=d.accuracy_rate>=80?'#10b981':d.accuracy_rate>=60?'#f59e0b':'#ef4444';
    const accR=40,accC=2*Math.PI*accR,accOff=accC-(d.accuracy_rate/100)*accC;
    const accGauge=`<svg width="120" height="120" viewBox="0 0 100 100"><circle cx="50" cy="50" r="${accR}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/><circle cx="50" cy="50" r="${accR}" fill="none" stroke="${accColor}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${accC}" stroke-dashoffset="${accOff}" transform="rotate(-90 50 50)" style="transition:all 1s"/><text x="50" y="48" text-anchor="middle" fill="#fff" font-size="18" font-weight="bold">${d.accuracy_rate}%</text><text x="50" y="62" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="9">accuracy</text></svg>`;

    // Misidentification table
    let misTable='';
    if(d.misidentifications&&d.misidentifications.length){
      misTable=`<div class="card card-lg mt-3"><div class="card-body">
        <h6><i class="ti ti-arrows-shuffle me-2"></i>Common Misidentifications</h6>
        <table class="table table-sm small mb-0">
          <thead><tr><th>Predicted</th><th></th><th>Actual</th><th>Count</th><th>%</th></tr></thead>
          <tbody>${d.misidentifications.map(m=>`<tr><td class="text-danger">${m.predicted}</td><td>→</td><td class="text-success">${m.actual}</td><td>${m.count}</td><td>${m.percentage}%</td></tr>`).join('')}</tbody>
        </table>
      </div></div>`;
    }

    // Per-pest accuracy bars
    let pestBars='';
    if(d.per_pest_accuracy&&d.per_pest_accuracy.length){
      pestBars=d.per_pest_accuracy.slice(0,8).map(p=>{
        const bc=p.accuracy>=80?'#10b981':p.accuracy>=60?'#f59e0b':'#ef4444';
        return `<div class="d-flex align-items-center gap-2 mb-2"><span class="small" style="min-width:140px">${p.pest}</span><div style="flex:1;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden"><div style="width:${p.accuracy}%;height:100%;background:${bc};border-radius:4px;transition:width 1s ease"></div></div><span class="small fw-bold" style="min-width:55px;text-align:right">${p.accuracy}% (${p.total})</span></div>`;
      }).join('');
    }

    // Timeline
    let timeline='';
    if(d.recent_timeline&&d.recent_timeline.length){
      timeline=d.recent_timeline.slice(0,10).map(t=>{
        const icon=t.correct?'✅':'❌';
        const time=new Date(t.timestamp).toLocaleTimeString();
        return `<div class="d-flex justify-content-between py-1 small" style="border-bottom:1px solid rgba(255,255,255,0.04)"><span>${icon} ${t.pest} ${!t.correct&&t.actual?`→ ${t.actual}`:''}</span><span class="text-secondary">${(t.confidence*100).toFixed(0)}% · ${time}</span></div>`;
      }).join('');
    }

    el.innerHTML=`
      <div class="row g-4 mb-4">
        <div class="col-md-4"><div class="card card-lg h-100"><div class="card-body text-center">
          <h6 class="mb-3">Model Accuracy</h6>
          ${accGauge}
          <div class="mt-2 small text-secondary">${d.correct} correct / ${d.total_feedback} total</div>
        </div></div></div>
        <div class="col-md-4"><div class="card card-lg h-100"><div class="card-body">
          <h6><i class="ti ti-chart-bar me-2"></i>Confidence Analysis</h6>
          <div class="mb-3">
            <div class="small text-secondary mb-1">Avg Confidence (Correct)</div>
            <div class="d-flex align-items-center gap-2"><div class="conf-bar flex-fill"><div class="conf-bar-fill conf-high" style="width:${d.confidence_analysis.avg_correct_confidence*100}%"></div></div><span class="small fw-bold">${(d.confidence_analysis.avg_correct_confidence*100).toFixed(1)}%</span></div>
          </div>
          <div class="mb-3">
            <div class="small text-secondary mb-1">Avg Confidence (Incorrect)</div>
            <div class="d-flex align-items-center gap-2"><div class="conf-bar flex-fill"><div class="conf-bar-fill conf-low" style="width:${d.confidence_analysis.avg_incorrect_confidence*100}%"></div></div><span class="small fw-bold">${(d.confidence_analysis.avg_incorrect_confidence*100).toFixed(1)}%</span></div>
          </div>
          <div class="small text-secondary">Gap: ${(d.confidence_analysis.confidence_gap*100).toFixed(1)} percentage points</div>
        </div></div></div>
        <div class="col-md-4"><div class="card card-lg h-100"><div class="card-body">
          <h6><i class="ti ti-bulb me-2"></i>Improvement Suggestions</h6>
          ${d.suggestions.map(s=>`<div class="small mb-2"><i class="ti ti-point-filled me-1 text-info"></i>${s}</div>`).join('')}
        </div></div></div>
      </div>
      ${pestBars?`<div class="card card-lg mb-4"><div class="card-body"><h6><i class="ti ti-chart-bar me-2"></i>Per-Pest Accuracy</h6>${pestBars}</div></div>`:''}
      ${misTable}
      ${timeline?`<div class="card card-lg mt-3"><div class="card-body"><h6><i class="ti ti-clock me-2"></i>Recent Feedback</h6>${timeline}</div></div>`:''}
    `;
  }catch(e){el.innerHTML='<div class="text-danger small">Failed to load analytics.</div>';}
}

