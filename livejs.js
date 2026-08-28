/* ============================================================
   Data layer. ONE code path: everything on the page is computed
   from the subscription records by compute(), whether those
   records came baked in or from a live Stripe sync. That is what
   keeps the chart, the lists and the KPIs on the same basis.
   ============================================================ */
const BAKE = JSON.parse(document.getElementById('bakedata').textContent);
const P = BAKE.P, FXB = BAKE.FX, RATE = +FXB.usd_to_cad;
let HIST  = BAKE.H.slice();
let NAMES = Object.assign({}, BAKE.N);
let OPENINV = BAKE.INV.slice();
let CTRY  = Object.assign({}, BAKE.C || {});   // customer id -> ISO-3166 alpha-2
let STAMP = BAKE.stamp * 1000;

const GROUPS = ['Coach','Athlete','Pro','Legacy'];
const LIVE_ST = new Set(['active','past_due','trialing','unpaid']);
const MONTHS = {month:1, year:12, week:0.25, day:1/30};

const tierOf  = s => P[s.p] || s.p;
const groupOf = t => { const h=String(t).split(' -')[0].trim();
                       return (h==='Coach'||h==='Athlete'||h==='Pro') ? h : 'Legacy'; };
const perMonth = s => (s.a * (s.q||1) / 100) / (MONTHS[s.iv] * (s.ic||1));
const toBase  = (v,cur) => cur==='usd' ? v*RATE : v;
const whoOf   = c => NAMES[c] || ['Unknown',''];
const ctryOf  = c => CTRY[c] || '';

const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function fmtDate(ts){                        // "Aug 24, '26" - UTC, matches the generator
  const d=new Date(ts*1000);
  return `${MON[d.getUTCMonth()]} ${d.getUTCDate()}, '${String(d.getUTCFullYear()).slice(2)}`;
}

function compute(){
  const now = Date.now()/1000;
  const real = HIST.filter(s=>s.s!=='incomplete_expired');

  /* ---- tiers ---- */
  const T={}, tsplit={}, tcount={};
  let usdM=0, cadM=0, usdN=0, cadN=0;
  for(const s of HIST){
    const t=tierOf(s);
    T[t] = T[t] || {active:0,past_due:0,leaving:0,canceled:0,mrr:0,usd:0,cad:0};
    if(LIVE_ST.has(s.s)){
      T[t][s.s==='past_due'?'past_due':'active']++;
      const v=perMonth(s);
      T[t].mrr += toBase(v,s.u);
      if(s.u==='usd'){ T[t].usd+=v; usdM+=v; usdN++; } else { T[t].cad+=v; cadM+=v; cadN++; }
      if(s.ce) T[t].leaving++;
    } else if(s.s==='canceled') T[t].canceled++;
  }
  const tiers = Object.keys(T).filter(t=>T[t].active+T[t].past_due>0).map(t=>({
      tier:t, group:groupOf(t), active:T[t].active, past_due:T[t].past_due,
      leaving:T[t].leaving, canceled:T[t].canceled,
      mrr:+T[t].mrr.toFixed(2), usd:+T[t].usd.toFixed(2), cad:+T[t].cad.toFixed(2)}));
  tiers.sort((a,b)=> GROUPS.indexOf(a.group)-GROUPS.indexOf(b.group) || b.mrr-a.mrr);

  const groups = GROUPS.map(g=>{
    const rows=tiers.filter(r=>r.group===g);
    const sum=k=>rows.reduce((a,r)=>a+r[k],0);
    return {group:g, active:sum('active'), past_due:sum('past_due'), leaving:sum('leaving'),
            canceled:sum('canceled'), mrr:+sum('mrr').toFixed(2),
            usd:+sum('usd').toFixed(2), cad:+sum('cad').toFixed(2)};
  });

  /* ---- people ----
     joined  = every subscription that STARTED in the window (even if it has since ended)
     churned = every subscription that ENDED in the window, keyed on ended_at
     Same basis on both sides, so joined - churned always equals the chart's change. */
  const row=(s,when)=>{ const [n,e]=whoOf(s.c); const t=tierOf(s);
    return {name:n, email:e, tier:t, group:groupOf(t), date:fmtDate(when), ts:when, cc:ctryOf(s.c),
            mrr:+toBase(perMonth(s),s.u).toFixed(2), amt:+perMonth(s).toFixed(2), cur:s.u}; };
  const joined = real.map(s=>{ const r=row(s,s.cr); if(s.en) r.gone=fmtDate(s.en); return r; })
                     .sort((a,b)=>b.ts-a.ts);
  const churned = real.filter(s=>s.en).map(s=>row(s,s.en)).sort((a,b)=>b.ts-a.ts);
  const leaving = HIST.filter(s=>LIVE_ST.has(s.s)&&s.ce)
                      .map(s=>{ const r=row(s,s.cr); r.ends=fmtDate(s.pe||now); return r; })
                      .sort((a,b)=>b.mrr-a.mrr);

  const past_due = HIST.filter(s=>s.s==='past_due').map(s=>{
    const [n,e]=whoOf(s.c); const t=tierOf(s);
    let mine = OPENINV.filter(i=>i.s===s.i);
    if(!mine.length) mine = OPENINV.filter(i=>i.c===s.c);
    const oldest = mine.length ? Math.min(...mine.map(i=>i.t)) : null;
    return {name:n, email:e, tier:t, group:groupOf(t), cc:ctryOf(s.c), amt:+perMonth(s).toFixed(2), cur:s.u,
            owed:+(mine.reduce((a,i)=>a+i.a,0)/100).toFixed(2),
            owed_cur:(mine[0]&&mine[0].u)||s.u,
            days: oldest ? Math.floor((now-oldest)/86400) : 0,
            url:(mine[0]&&mine[0].url)||''};
  }).sort((a,b)=>b.days-a.days);

  /* ---- roster: one row per subscription ever, for the search box ----
     Deliberately built from HIST, not from the live lists, so a member who
     left two years ago is just as findable as one who joined this morning. */
  const roster = HIST.map(s=>{
    const [n,e]=whoOf(s.c); const t=tierOf(s);
    let state, label;
    if(s.s==='past_due')                 { state='past_due'; label='Past due'; }
    else if(s.s==='incomplete_expired')  { state='never';    label='Never started'; }
    else if(LIVE_ST.has(s.s) && s.ce)    { state='leaving';  label='Leaving '+fmtDate(s.pe||now); }
    else if(LIVE_ST.has(s.s))            { state='active';   label='Active'; }
    else                                 { state='gone';     label='Cancelled'+(s.en?' '+fmtDate(s.en):''); }
    return {name:n, email:e, cid:s.c, tier:t, group:groupOf(t), cc:ctryOf(s.c),
            state, label, since:fmtDate(s.cr), ts:s.cr,
            amt:+perMonth(s).toFixed(2), cur:s.u};
  }).sort((a,b)=>{
    const rank={past_due:0, leaving:1, active:2, gone:3, never:4};
    return rank[a.state]-rank[b.state] || b.ts-a.ts;
  });

  /* ---- members by country ----
     Counts PEOPLE, not subscriptions: one member holding two plans is one
     person in one country. That is why this total can sit below the
     subscription counts on the money tiles. Country comes from the customer's
     card, so a member with no charge on file has none. */
  const CC = {}, seenCust = new Set();
  let ccKnown = 0, ccUnknown = 0;
  for(const s of HIST){
    if(!LIVE_ST.has(s.s) || seenCust.has(s.c)) continue;
    seenCust.add(s.c);
    const cc = ctryOf(s.c);
    if(cc){ CC[cc] = (CC[cc]||0)+1; ccKnown++; } else ccUnknown++;
  }
  const countries = Object.keys(CC).map(cc=>({cc, n:CC[cc]}))
                          .sort((a,b)=> b.n-a.n || a.cc.localeCompare(b.cc));

  /* ---- trends ---- */
  const first = Math.min(...HIST.map(s=>s.cr));
  const jan1  = Date.UTC(new Date().getUTCFullYear(),0,1)/1000;
  const WIN = [
    {key:'7',   label:'7 days',   start:now-7*86400},
    {key:'30',  label:'30 days',  start:now-30*86400},
    {key:'90',  label:'90 days',  start:now-90*86400},
    {key:'ytd', label:'This year',start:jan1},
    {key:'all', label:'All time', start:first-86400},
  ];
  const series=(pred,start,n=120)=>{
    const step=Math.max(now-start,86400)/(n-1), out=[];
    for(let i=0;i<n;i++){
      const ts=start+step*i, d=new Date(ts*1000);
      const pt={d:`${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,'0')}-${String(d.getUTCDate()).padStart(2,'0')}`};
      let tot=0;
      for(const g of GROUPS) pt[g]=0;
      for(const s of HIST){
        if(s.s==='incomplete_expired') continue;
        if(s.cr>ts) continue;
        if(s.en && s.en<=ts) continue;
        if(!pred(s)) continue;
        pt[groupOf(tierOf(s))]++; tot++;
      }
      pt.Total=tot; out.push(pt);
    }
    return out;
  };
  const trends={};
  for(const w of WIN) trends[w.key]={label:w.label, start:w.start,
      usd:series(s=>s.u==='usd', w.start), cad:series(s=>s.u!=='usd', w.start)};

  const deadOwed = OPENINV.filter(i=>{ const s=HIST.find(x=>x.i===i.s); return !s || s.s!=='past_due'; });

  return {
    fx:FXB,
    generated: new Date(STAMP).toLocaleString('en-US',{weekday:'long',month:'long',day:'numeric',
                 hour:'numeric',minute:'2-digit',timeZone:'America/Toronto'}).replace(' at ',' · ')+' ET',
    groups_order:GROUPS, windows:WIN.map(w=>({key:w.key,label:w.label,start:w.start})),
    totals:{
      active:  tiers.reduce((a,t)=>a+t.active,0),
      past_due:tiers.reduce((a,t)=>a+t.past_due,0),
      leaving: tiers.reduce((a,t)=>a+t.leaving,0),
      mrr:+tiers.reduce((a,t)=>a+t.mrr,0).toFixed(2),
      usd_mrr:+usdM.toFixed(2), cad_mrr:+cadM.toFixed(2), usd_n:usdN, cad_n:cadN,
      mrr_usd_view:+(usdM+cadM/RATE).toFixed(2),
      new30: joined.filter(j=>j.ts>=now-30*86400).length,
      churn30: churned.filter(c=>c.ts>=now-30*86400).length,
      owed:+past_due.reduce((a,p)=>a+p.owed,0).toFixed(2),
      owed_usd:+past_due.filter(p=>p.owed_cur==='usd').reduce((a,p)=>a+p.owed,0).toFixed(2),
      owed_cad:+past_due.filter(p=>p.owed_cur!=='usd').reduce((a,p)=>a+p.owed,0).toFixed(2),
      dead_owed:+(deadOwed.reduce((a,i)=>a+i.a,0)/100).toFixed(2), dead_n:deadOwed.length,
      stalled: HIST.filter(s=>s.s==='incomplete_expired').length,
      manual_n:0, manual_mrr:0, manual_usd:0, manual_cad:0, now_ts:now
    },
    countries, cc_known:ccKnown, cc_unknown:ccUnknown,
    groups, tiers, trends, joined, churned, leaving, past_due, roster, manual:[]
  };
}
