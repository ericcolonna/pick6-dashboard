/* ============================================================
   Live sync. Pulls only what can still change: the ~111 live
   subscriptions (2 pages) and the open invoices. The ~293
   cancelled subscriptions are frozen records - they ship baked
   into the page and are never re-fetched. When someone drops off
   the live list we fetch that one subscription to learn its end
   date, then recompute the WHOLE page from the merged records,
   so no section is ever fresher than another.
   ============================================================ */
const SRV='Stripe', TOOL='stripe_api_read', CTX='acct_1QAluWL1hlk0mE2U';
const req=(op,params)=>({stripe_api_operation_id:op,parameters:params,stripe_context:CTX,livemode:true});
const FRESH={cache:{refresh:true}};
let MCP=null, syncing=false, lastErr=null, watchOff=null;

function listOf(res){
  let p=res&&res.payload;
  if(typeof p==='string'){ try{p=JSON.parse(p);}catch(_){return null;} }
  return (p&&typeof p==='object'&&Array.isArray(p.data))?p:null;
}
function objOf(res){
  let p=res&&res.payload;
  if(typeof p==='string'){ try{p=JSON.parse(p);}catch(_){return null;} }
  return (p&&typeof p==='object'&&!Array.isArray(p))?p:null;
}
function compactSub(s){
  const it=s.items&&s.items.data&&s.items.data[0]; if(!it) return null;
  const pr=it.price||it.plan, r=(pr&&pr.recurring)||pr;
  if(!pr||!r||!r.interval) return null;
  return {i:s.id,c:s.customer,p:pr.product,u:pr.currency,a:pr.unit_amount||pr.amount||0,
          iv:r.interval,ic:r.interval_count||1,q:it.quantity||1,cr:s.created,
          en:s.ended_at||0,ce:s.cancel_at_period_end?1:0,
          pe:it.current_period_end||s.cancel_at||0,s:s.status};
}

async function runSync(firstPage){
  if(syncing) return; syncing=true; setSync('syncing');
  try{
    let live=firstPage.data.slice(), more=firstPage.has_more, guard=0;
    while(more && guard++<8){
      const r=await MCP.callTool(SRV,TOOL,req('GetSubscriptions',{limit:100,starting_after:live[live.length-1].id}),FRESH);
      const pg=listOf(r);
      if(!pg) throw {code:'upstream_error',message:'Could not read a subscription page'};
      live=live.concat(pg.data); more=pg.has_more;
    }

    const ir=await MCP.callTool(SRV,TOOL,req('GetInvoices',{limit:100,status:'open'}),FRESH);
    const ip=listOf(ir);
    if(ip) OPENINV=ip.data.map(i=>({
      s:(i.parent&&i.parent.subscription_details&&i.parent.subscription_details.subscription)||null,
      c:i.customer, a:i.amount_remaining, u:i.currency, t:i.created, url:i.hosted_invoice_url}));

    const byId=new Map(HIST.map(h=>[h.i,h]));
    const freshIds=new Set(), newCust=new Set();
    for(const s of live){
      const cs=compactSub(s); if(!cs) continue;
      freshIds.add(cs.i); byId.set(cs.i,cs);
      if(!NAMES[cs.c]) newCust.add(cs.c);
    }
    // previously live, absent from the live list => it ended; fetch its end date.
    // Throttled per sync, not a ceiling: whatever is left over is picked up by the
    // next 30-minute sync, so a stale roster self-heals. 50 covers weeks of the daily
    // re-bake failing, against a real-world worst case of ~4 departures in a day.
    const dropped=[...byId.values()].filter(h=>!freshIds.has(h.i)&&h.en===0&&LIVE_ST.has(h.s));
    for(const h of dropped.slice(0,50)){
      // Stripe renamed these path params to `id` (spec 2026-08-26). Both keys are
      // sent so the call works either way - the unused one is ignored.
      const r=await MCP.callTool(SRV,TOOL,req('GetSubscriptionsSubscriptionExposedId',
                                              {id:h.i, subscription_exposed_id:h.i}),FRESH);
      const full=objOf(r); const cs=full&&compactSub(full);
      if(cs) byId.set(cs.i,cs);
    }
    // New member => fetch their name, and their country off their first charge.
    // Country lives on the charge, not the customer, so it is a second call -
    // but only ever for people we have not seen before, so usually zero.
    for(const c of [...newCust].slice(0,50)){
      const r=await MCP.callTool(SRV,TOOL,req('GetCustomersCustomer',{id:c, customer:c}),FRESH);
      const cu=objOf(r);
      if(cu) NAMES[c]=[cu.name||cu.description||(cu.metadata&&cu.metadata.name)||'Unknown', cu.email||''];
      if(!CTRY[c]){
        try{
          const cr=await MCP.callTool(SRV,TOOL,req('GetCharges',{customer:c,limit:1}),FRESH);
          const cp=listOf(cr), ch=cp&&cp.data&&cp.data[0];
          const cc = ch && ((ch.billing_details&&ch.billing_details.address&&ch.billing_details.address.country)
                     || (ch.payment_method_details&&ch.payment_method_details.card&&ch.payment_method_details.card.country));
          if(cc) CTRY[c]=cc;
        }catch(_){ /* no charge yet (trial or $0 promo) - stays unknown */ }
      }
    }

    HIST=[...byId.values()];
    STAMP=Date.now(); lastErr=null;
    D=compute(); redraw(); setSync('ok');
  }catch(e){
    lastErr=e||{code:'upstream_error',message:'Sync failed'};
    setSync('err');
    if(lastErr.retryable && !runSync._retried){
      runSync._retried=true;
      setTimeout(()=>{ runSync._retried=false; kick(); }, Math.min(lastErr.retryAfterMs||4000,60000)+Math.random()*2000);
    }
  } finally { syncing=false; }
}

function kick(){
  if(!MCP) return;
  MCP.callTool(SRV,TOOL,req('GetSubscriptions',{limit:100}),FRESH)
     .then(r=>{ const pg=listOf(r); if(pg) return runSync(pg);
                lastErr={code:'upstream_error',message:'Could not read subscriptions'}; setSync('err'); })
     .catch(e=>{ lastErr=e; setSync('err'); });
}

/* Each error code has a different fix - never collapse them into one banner. */
function errCopy(e){
  switch(e&&e.code){
    case 'needs_reauth':        return ['Stripe needs reconnecting','Settings → Connectors on claude.ai'];
    case 'server_not_connected':return ['Stripe not connected','Add it in Settings → Connectors on claude.ai'];
    case 'selection_required':  return ['Choose a Stripe account','Pick one when claude.ai asks'];
    case 'blocked_by_policy':   return ['Stripe access blocked','Your organisation policy blocks this tool'];
    case 'approval_required':   return ['Stripe access needs approval',''];
    case 'not_in_manifest':     return ['Stripe call not permitted',''];
    case 'not_granted':
    case 'capability_disabled':
    case 'capability_removed':  return ['Live sync unavailable here','Open the artifact on claude.ai'];
    case 'server_unavailable':  return ['Stripe unreachable','Retrying shortly'];
    case 'tool_error':          return ['Stripe returned an error', (e.message||'').slice(0,90)];
    default:                    return ['Could not sync', (e&&e.message||'').slice(0,90)];
  }
}
function ago(ms){
  const s=Math.max(0,Math.round((Date.now()-ms)/1000));
  if(s<45) return 'just now';
  const m=Math.round(s/60); if(m<60) return m+(m===1?' min ago':' mins ago');
  const h=Math.round(m/60); if(h<24) return h+(h===1?' hour ago':' hours ago');
  const d=Math.round(h/24); return d+(d===1?' day ago':' days ago');
}
function setSync(state){
  const dot=$('#syncdot'), txt=$('#synctext'), sub=$('#syncsub');
  if(!dot) return;
  dot.className='dot '+(state==='err'?'dot-bad':state==='syncing'?'dot-wait':'dot-ok');
  if(state==='syncing'){ txt.textContent='Syncing with Stripe…'; sub.textContent=''; return; }
  if(state==='err'){
    const [a,b]=errCopy(lastErr);
    txt.textContent=a; sub.textContent=(b?b+' · ':'')+'showing data from '+ago(STAMP);
    return;
  }
  txt.textContent='Synced '+ago(STAMP);
  sub.textContent = MCP ? 'Live from Stripe · rechecks every 30 minutes' : 'Live from Stripe';
}

(async function startLive(){
  setSync('ok');
  setInterval(()=>{ if(!syncing) setSync(lastErr?'err':'ok'); }, 30000);   // keep "x mins ago" honest
  let mcp=null;
  try{ mcp = await (window.claude && window.claude.use ? window.claude.use('mcp') : Promise.resolve(null)); }catch(_){ mcp=null; }
  if(!mcp){ return; }                       // no live sync here - the baked page stands on its own
  MCP=mcp;
  setSync('ok');
  watchOff = MCP.watchTool(SRV, TOOL, req('GetSubscriptions',{limit:100}), ev=>{
    if(ev.type==='data'){
      const pg=listOf(ev.result);
      if(pg) runSync(pg);
      else { lastErr={code:'upstream_error',message:'Could not read subscriptions'}; setSync('err'); }
    } else {
      lastErr=ev.error; setSync('err');
    }
  }, {refetchInterval:1800000});
})();
