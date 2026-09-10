const $ = id => document.getElementById(id);
const urlInput=$("url"), btn=$("generateBtn"), spinner=$("spinner"), btnText=$("btnText"), msg=$("message"), bar=$("bar"), result=$("result");

function historyData(){ try{return JSON.parse(localStorage.getItem("vortex_sfile_history")||"[]")}catch(_){return[]}}
function saveHistory(item){
  let h=historyData().filter(x=>x.source!==item.source);
  h.unshift(item); h=h.slice(0,12);
  localStorage.setItem("vortex_sfile_history",JSON.stringify(h)); renderHistory();
}
function renderHistory(){
  const list=$("historyList"), h=historyData();
  if(!h.length){list.innerHTML='<div class="empty">Belum ada riwayat.</div>';return}
  list.innerHTML=h.map(x=>`<div class="hist"><div class="hist-main"><b>${escapeHtml(x.title||"Sfile Download")}</b><small>${escapeHtml(x.source)}</small></div><a href="${encodeURI(x.direct)}" target="_blank" rel="noopener">OPEN</a></div>`).join("");
}
function escapeHtml(s){return String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
function loading(v){
  btn.disabled=v; spinner.style.display=v?"block":"none"; btnText.style.display=v?"none":"inline";
  bar.style.width=v?"68%":"0";
}
async function generate(){
  const url=urlInput.value.trim();
  if(!url){msg.textContent="Masukkan link Sfile dulu.";return}
  result.classList.add("hidden"); loading(true); msg.textContent="Menghubungi resolver Sfile…";
  try{
    const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});
    const j=await r.json();
    if(!r.ok||!j.ok) throw new Error(j.error||"Generate gagal");
    bar.style.width="100%";
    $("fileTitle").textContent=j.title||"Sfile Download";
    $("fileSize").textContent=j.size||"Tidak diketahui";
    const sid=(j.source_url||url).split("/").pop();
    const shareLink="https://sfile.co/"+sid;
    $("directUrl").value=shareLink;
    $("downloadBtn").href="/api/download?url="+encodeURIComponent(j.source_url||url);
    $("openBtn").href=shareLink;
    $("mode").textContent=j.cdn_url?"CDN DIRECT":"DIRECT";
    result.classList.remove("hidden");
    msg.textContent="Direct link berhasil dibuat.";
    saveHistory({title:j.title||"Sfile Download",source:j.source_url||url,direct:shareLink,date:Date.now()});
  }catch(e){
    msg.textContent="Gagal: "+e.message;
    bar.style.width="0";
  }finally{
    setTimeout(()=>{loading(false); if(!result.classList.contains("hidden"))bar.style.width="100%"},250)
  }
}
$("generateBtn").onclick=generate;
urlInput.addEventListener("keydown",e=>{if(e.key==="Enter")generate()});
$("copyBtn").onclick=async()=>{try{await navigator.clipboard.writeText($("directUrl").value);$("copyBtn").textContent="COPIED";setTimeout(()=>$("copyBtn").textContent="COPY",1200)}catch(_){}};
$("pasteBtn").onclick=async()=>{try{urlInput.value=await navigator.clipboard.readText()}catch(_){urlInput.focus()}};
$("clearBtn").onclick=()=>{localStorage.removeItem("vortex_sfile_history");renderHistory()};
renderHistory();
