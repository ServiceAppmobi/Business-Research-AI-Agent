CUSTOMER_PORTAL_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>Business Research — Customer Portal</title>
<style>
:root{color-scheme:dark;--bg:#071426;--panel:#10243d;--line:#24415f;--blue:#2684ff;--muted:#a9bbd0;--white:#f4f8ff}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(145deg,#061225,#0b1d34 55%,#102a49);color:var(--white);font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,sans-serif;min-height:100vh;padding:36px 16px}
main{max-width:760px;margin:0 auto}.brand{display:flex;align-items:center;gap:12px;margin-bottom:28px}.mark{width:38px;height:38px;border:3px solid #55a1ff;border-radius:10px;display:grid;place-items:center;color:#fff;font-weight:800}.brand strong{letter-spacing:.2px}.brand small{display:block;color:var(--muted)}.panel{background:rgba(16,36,61,.94);border:1px solid var(--line);border-radius:18px;padding:26px;box-shadow:0 18px 60px #0005}h1{font-size:clamp(25px,5vw,34px);line-height:1.15;margin:0 0 8px}p{color:var(--muted);margin:0 0 22px}.grid{display:grid;gap:14px}label{font-size:13px;color:#c5d5e7;font-weight:650}input{width:100%;margin-top:6px;background:#08182b;border:1px solid #355371;border-radius:10px;padding:13px;color:white;font:inherit;outline:none}input:focus{border-color:#69aaff;box-shadow:0 0 0 3px #2684ff30}button{border:0;border-radius:10px;padding:13px 18px;background:var(--blue);color:white;font:inherit;font-weight:700;cursor:pointer}button:disabled{opacity:.55;cursor:wait}.secondary{background:#1b3552;border:1px solid #3a5877}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.notice{margin-top:16px;padding:12px 14px;border-radius:10px;background:#0a1b30;color:#c7d7e9;border:1px solid #29435f;white-space:pre-wrap}.notice.error{border-color:#a44b59;color:#ffd5d9}.result{display:none;margin-top:24px;border-top:1px solid var(--line);padding-top:20px}.status{display:inline-block;border-radius:99px;background:#183c61;color:#a9d2ff;padding:5px 11px;font-size:13px;font-weight:700;text-transform:capitalize}.summary{margin-top:15px;white-space:pre-wrap;color:#e1ebf7}.foot{font-size:12px;margin-top:18px;color:#8fa6bf}.hidden{display:none!important}
</style>
</head>
<body><main>
<div class="brand"><div class="mark">B</div><div><strong>BUSINESS RESEARCH AI</strong><small>Secure customer portal</small></div></div>
<section class="panel">
<h1>Your research, in one place.</h1>
<p>Enter the order reference and secure access token you received when starting checkout. Your token is never saved in this browser.</p>
<form id="lookup" class="grid">
<label>Order reference<input id="order" autocomplete="off" required placeholder="Paste your order ID"></label>
<label>Secure access token<input id="token" type="password" autocomplete="off" required placeholder="Paste your access token"></label>
<button id="open" type="submit">Open my report</button>
</form>
<div id="message" class="notice" role="status" aria-live="polite">Your order details are private. Do not share your access token with anyone.</div>
<section id="result" class="result">
<div><span class="status" id="status"></span></div>
<div class="summary" id="summary"></div>
<div class="actions"><button id="download" type="button" class="hidden">Download PDF report</button><button id="clear" type="button" class="secondary">Close secure session</button></div>
</section>
<div class="foot">Access is protected by a unique order token. This portal does not offer email-based recovery yet.</div>
</section></main>
<script>
(function(){
const form=document.getElementById('lookup'),orderInput=document.getElementById('order'),tokenInput=document.getElementById('token'),message=document.getElementById('message'),result=document.getElementById('result'),statusEl=document.getElementById('status'),summary=document.getElementById('summary'),openBtn=document.getElementById('open'),downloadBtn=document.getElementById('download');
let activeOrder='',activeToken='';
function say(text,error){message.textContent=text;message.classList.toggle('error',!!error)}
function clearSession(){activeOrder='';activeToken='';tokenInput.value='';orderInput.value='';result.style.display='none';downloadBtn.classList.add('hidden');summary.textContent='';say('Secure session closed. Your access token has been cleared.')}
form.addEventListener('submit',async function(event){
event.preventDefault();activeOrder=orderInput.value.trim();activeToken=tokenInput.value.trim();result.style.display='none';downloadBtn.classList.add('hidden');openBtn.disabled=true;say('Checking your order…');
try{
const response=await fetch('/api/v1/orders/'+encodeURIComponent(activeOrder),{headers:{Authorization:'Bearer '+activeToken}});
const data=await response.json();if(!response.ok)throw new Error(data.detail||'Could not open this order.');
statusEl.textContent=(data.status||'unknown').replaceAll('_',' ');summary.textContent='';
if(data.status==='completed'&&data.report){
const report=data.report;const fields=[['Executive summary',report.executive_summary],['Market overview',report.market_overview],['Target customers',report.target_customers],['Opportunities',report.opportunities],['Risks',report.risks],['Competitor landscape',report.competitor_landscape],['Recommended next steps',report.recommended_next_steps],['Assumptions and limitations',report.assumptions_and_limitations]];
for(const [heading,value] of fields){if(value===undefined||value===null||value==='')continue;const block=document.createElement('div');const title=document.createElement('strong');title.textContent=heading;const body=document.createElement('p');body.textContent=Array.isArray(value)?value.map(x=>'• '+String(x)).join('\\n'):String(value);body.style.whiteSpace='pre-wrap';block.append(title,body);summary.append(block)}
downloadBtn.classList.remove('hidden');say('Your report is ready. You can review it below or download the PDF.');
}else{summary.textContent='Your report is not ready yet. Refresh this page later to check again.';say('Order found. Current status: '+statusEl.textContent+'.')}
result.style.display='block';
}catch(error){activeOrder='';activeToken='';say(error.message||'Something went wrong.',true)}finally{openBtn.disabled=false}
});
downloadBtn.addEventListener('click',async function(){
downloadBtn.disabled=true;say('Preparing your PDF…');
try{const response=await fetch('/api/v1/orders/'+encodeURIComponent(activeOrder)+'/report.pdf',{headers:{Authorization:'Bearer '+activeToken}});if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||'PDF download failed.')}const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='business-research-'+activeOrder+'.pdf';document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);say('PDF download started.')}catch(error){say(error.message,true)}finally{downloadBtn.disabled=false}
});
document.getElementById('clear').addEventListener('click',clearSession);
})();
</script></body></html>"""
