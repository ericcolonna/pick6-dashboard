import json, os
DIR=os.path.dirname(os.path.abspath(__file__))
BAKE=open(os.path.join(DIR,'bake.json')).read()
ENGINE=open(os.path.join(DIR,'livejs.js')).read()
SYNC=open(os.path.join(DIR,'syncjs.js')).read()
HTML = r'''<title>Pick 6 Member Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  color-scheme:light;
  --ground:#eef1f6; --panel:#ffffff; --panel-2:#f7f9fc; --line:#d3dae6; --line-soft:#e4e9f1;
  --ink:#0e1826; --ink-2:#4a5768; --ink-3:#7a869a;
  --s1:#4fbf6a; --s2:#8a5cd6; --s3:#111111; --s4:#003594; --total:#111111;
  --la:#2a78d6; --p6:#eb6834;
  --good:#3fae7c; --warn:#a86f00; --bad:#c8102e;
  --good-bg:#e2f3ec; --warn-bg:#faf0da; --bad-bg:#fbe3e7;
  --chalk:#c2ccdb;
  --shadow:0 1px 2px rgba(14,24,38,.05),0 8px 24px -12px rgba(14,24,38,.18);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  color-scheme:dark;
  --ground:#080e18; --panel:#101c2e; --panel-2:#15243a; --line:#243550; --line-soft:#1b2a41;
  --ink:#f2f6fc; --ink-2:#a9b8cd; --ink-3:#6d7f99;
  --s1:#3fae63; --s2:#9478de; --s3:#f2f6fc; --s4:#2b62c9; --total:#f2f6fc;
  --la:#3987e5; --p6:#e0672f;
  --good:#5fd3a3; --warn:#e0a323; --bad:#e81f3d;
  --good-bg:#0f2c25; --warn-bg:#2d2413; --bad-bg:#361219;
  --chalk:#2b3d59;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -14px rgba(0,0,0,.7);
}}
:root[data-theme="dark"]{
  color-scheme:dark;
  --ground:#080e18; --panel:#101c2e; --panel-2:#15243a; --line:#243550; --line-soft:#1b2a41;
  --ink:#f2f6fc; --ink-2:#a9b8cd; --ink-3:#6d7f99;
  --s1:#3fae63; --s2:#9478de; --s3:#f2f6fc; --s4:#2b62c9; --total:#f2f6fc;
  --la:#3987e5; --p6:#e0672f;
  --good:#5fd3a3; --warn:#e0a323; --bad:#e81f3d;
  --good-bg:#0f2c25; --warn-bg:#2d2413; --bad-bg:#361219;
  --chalk:#2b3d59;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -14px rgba(0,0,0,.7);
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
 font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 64px;display:flex;flex-direction:column;gap:22px}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
.num{font-family:"Barlow Condensed","IBM Plex Sans",sans-serif;font-variant-numeric:tabular-nums;font-weight:600;line-height:.92}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);font-weight:500}

/* header */
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px;
 padding-bottom:18px;border-bottom:2px solid var(--line)}
h1{font-family:"Barlow Condensed",sans-serif;font-weight:700;font-size:40px;letter-spacing:.005em;
 margin:2px 0 0;text-transform:uppercase;text-wrap:balance}
.stamp{text-align:right}
.live{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--ink-2)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 3px color-mix(in srgb,var(--good) 22%,transparent);flex:none}
.dot-ok{background:var(--good);box-shadow:0 0 0 3px color-mix(in srgb,var(--good) 22%,transparent)}
.dot-bad{background:var(--bad);box-shadow:0 0 0 3px color-mix(in srgb,var(--bad) 22%,transparent)}
.dot-wait{background:var(--ink-3);box-shadow:0 0 0 3px color-mix(in srgb,var(--ink-3) 22%,transparent);animation:pulse 1.1s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
#syncsub{margin-top:4px}

/* range toggle */
.rangebar{display:flex;align-items:center;gap:26px;flex-wrap:wrap;margin-top:-4px}
/* the toggle and the one tile it actually drives, side by side */
/* One strip: the range toggle and the only figure it changes. Reads as a pair
   rather than a control floating beside a stray card. */
.windowrow{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;
 background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);
 padding:11px 16px 11px 12px}
.winmetric{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.winmetric .lbl{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--ink-3);font-weight:500}
.winmetric .fig{font-family:"Barlow Condensed",sans-serif;font-variant-numeric:tabular-nums;
 font-weight:600;font-size:30px;line-height:1;white-space:nowrap}
.winmetric .note{font-size:12.5px}
@media (max-width:700px){.windowrow{justify-content:center;gap:12px}}
.tierbar{margin-top:2px;padding-top:20px;border-top:1px solid var(--line)}
.seg button .swd{width:8px;height:8px;border-radius:2px;display:inline-block;margin-right:6px;vertical-align:-1px}
.seg{display:inline-flex;background:var(--panel-2);border:1px solid var(--line);border-radius:9px;padding:3px;gap:2px}
.seg button{appearance:none;border:0;background:transparent;cursor:pointer;
 font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;
 color:var(--ink-3);padding:6px 13px;border-radius:6px;transition:background .12s,color .12s;white-space:nowrap}
.seg button:hover{color:var(--ink-2)}
.seg button[aria-pressed="true"]{background:var(--panel);color:var(--ink);
 box-shadow:0 1px 2px rgba(0,0,0,.12);font-weight:600}

/* kpi */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(146px,1fr));gap:10px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 14px 13px;
 box-shadow:var(--shadow);display:flex;flex-direction:column;gap:9px;position:relative;overflow:hidden}
.kpi .v{font-size:40px;white-space:nowrap}
.curstripe{position:absolute;left:0;top:0;bottom:0;width:3px}
.kpi .sub{font-size:12.5px;color:var(--ink-2);display:flex;align-items:center;gap:6px;min-height:19px}
.kpi .money{font-size:13px;color:var(--ink-3)}
.up{color:var(--good)} .flat{color:var(--ink-3)}
.down{color:var(--bad)}

/* panels */
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);overflow:hidden}
.phead{display:flex;align-items:baseline;justify-content:space-between;gap:12px;
 padding:14px 18px;border-bottom:1px solid var(--line-soft)}
.phead h2{font-family:"Barlow Condensed",sans-serif;text-transform:uppercase;letter-spacing:.03em;
 font-size:20px;font-weight:600;margin:0}
.phead .note{font-size:12px;color:var(--ink-3)}
.pbody{padding:16px 18px}

/* chart */
.legend{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
#legend{display:inline-flex;gap:16px;align-items:center;flex-wrap:wrap}
.zoomnote{display:inline-flex;align-items:center;gap:8px;font-family:"IBM Plex Mono",monospace;
 font-size:11px;color:var(--ink-2);background:var(--panel-2);border:1px solid var(--line);
 border-radius:999px;padding:3px 5px 3px 10px}
.zoomnote button{appearance:none;border:0;background:var(--line-soft);color:var(--ink-2);cursor:pointer;
 font-family:inherit;font-size:10px;letter-spacing:.06em;text-transform:uppercase;
 padding:3px 8px;border-radius:999px}
.zoomnote button:hover{background:var(--line);color:var(--ink)}
.zoomnote[hidden]{display:none}
.chartbox{touch-action:none}
button.lg{appearance:none;background:transparent;border:0;padding:3px 6px;border-radius:6px;cursor:pointer;
 font-family:inherit;transition:opacity .12s,background .12s}
button.lg:hover{background:var(--panel-2)}
button.lg[aria-pressed="false"]{opacity:.38}
button.lg[aria-pressed="false"] .sw{background:var(--ink-3)!important}
.lg{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;color:var(--ink-2)}
.sw{width:14px;height:3px;border-radius:2px}
.chartbox{position:relative}
svg{display:block;width:100%;height:auto}
.tip{position:absolute;pointer-events:none;opacity:0;transition:opacity .12s;
 background:var(--panel-2);border:1px solid var(--line);border-radius:8px;padding:9px 11px;
 font-size:12.5px;box-shadow:var(--shadow);white-space:nowrap;z-index:5}
.tip .td{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin-bottom:5px}
.tip .tr{display:flex;align-items:center;gap:8px;justify-content:space-between}
.tip .tr b{font-family:"IBM Plex Mono",monospace;font-weight:600}

/* table */
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.12em;
 text-transform:uppercase;color:var(--ink-3);font-weight:500;padding:0 12px 9px;white-space:nowrap}
td{padding:11px 12px;border-top:1px solid var(--line-soft);vertical-align:middle}
th:first-child,td:first-child{padding-left:18px} th:last-child,td:last-child{padding-right:18px}
td.n,th.n{text-align:right;font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
tbody tr:hover{background:var(--panel-2)}
tr.grouprow td{background:var(--panel-2);border-top:2px solid var(--line)}
tr.subrow td{border-top:1px solid var(--line-soft)}
tfoot td{border-top:2px solid var(--line);font-weight:600;background:var(--panel-2)}
.tierName{display:flex;align-items:center;gap:9px;font-weight:500}
.rail{width:3px;height:20px;border-radius:2px;flex:none}
.bar{height:7px;border-radius:4px;min-width:3px}
.barwrap{display:flex;align-items:center;gap:9px;justify-content:flex-end}
.pill{display:inline-flex;align-items:center;gap:5px;font-family:"IBM Plex Mono",monospace;
 font-size:11px;padding:2.5px 8px;border-radius:999px;font-weight:500;white-space:nowrap}
.pill.ok{background:var(--good-bg);color:var(--good)}
.pill.warn{background:var(--warn-bg);color:var(--warn)}
.pill.bad{background:var(--bad-bg);color:var(--bad)}
.pill.mute{background:var(--panel-2);color:var(--ink-3);border:1px solid var(--line-soft)}

/* two-up */
.duo{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
@media (max-width:860px){.duo{grid-template-columns:1fr}}
.people{list-style:none;margin:0;padding:0}
.people li{display:flex;align-items:center;gap:11px;padding:10px 18px;border-top:1px solid var(--line-soft)}
.people li:first-child{border-top:none}
.who{flex:1;min-width:0}
.who .nm{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.who .mt{font-size:12px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.when{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-3);white-space:nowrap}
.amt{font-family:"IBM Plex Mono",monospace;font-size:13px;white-space:nowrap;font-variant-numeric:tabular-nums}
.empty{padding:22px 18px;color:var(--ink-3);font-size:13.5px}
a.inv{color:var(--bad);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--bad) 40%,transparent);font-size:12.5px}
a.inv:hover{border-bottom-color:var(--bad)}
a:focus-visible,button:focus-visible{outline:2px solid var(--la);outline-offset:2px;border-radius:4px}

.next{border-style:dashed;background:transparent;box-shadow:none}
.next .pbody{color:var(--ink-2);font-size:13.5px;display:flex;flex-direction:column;gap:8px}
footer{font-size:12px;color:var(--ink-3);border-top:1px solid var(--line);padding-top:16px;
 display:flex;flex-wrap:wrap;gap:6px 18px;justify-content:space-between}
/* "decreasing" red must beat the muted defaults on .when / .mt - these rules sit last
   on purpose, because .who .mt and .when set their own colour further up */
.people .when.down, .people .mt.down, .people .amt.down, .phead .note .down{color:var(--bad)}

/* flag beside every name */
.flag{font-size:14px;line-height:1;cursor:default;font-family:"Apple Color Emoji","Segoe UI Emoji",
 "Noto Color Emoji",sans-serif}
.flag.none{font-size:11px;color:var(--ink-3);font-family:"IBM Plex Mono",monospace}

/* member search */
.searchbar{padding:14px 18px;border-bottom:1px solid var(--line-soft)}
.searchbar input{width:100%;box-sizing:border-box;appearance:none;font:inherit;font-size:14px;
 padding:10px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel-2);
 color:var(--ink)}
.searchbar input::placeholder{color:var(--ink-3)}
.searchbar input:focus{outline:2px solid var(--la);outline-offset:1px;border-color:transparent}
.people li.hit{cursor:pointer}
.people li.hit:hover{background:var(--panel-2)}
.st{font-size:11px;letter-spacing:.04em;text-transform:uppercase;padding:2px 7px;border-radius:99px;
 white-space:nowrap;font-weight:500}
.st.active{background:var(--good-bg);color:var(--good)}
.st.leaving,.st.past_due{background:var(--bad-bg);color:var(--bad)}
.st.gone,.st.never{background:var(--panel-2);color:var(--ink-3);border:1px solid var(--line-soft)}
.mailrow{padding:0 18px 12px 47px;font-family:"IBM Plex Mono",monospace;font-size:12.5px;
 color:var(--ink-2);word-break:break-all}
.mailrow a{color:var(--la);text-decoration:none}
.mailrow a:hover{text-decoration:underline}

/* members by country — single series, so no legend and no palette;
   the country name carries identity, the bar carries magnitude only */
.ctot{display:flex;align-items:baseline;gap:10px;padding:16px 18px 4px}
.ctot .big{font-family:"IBM Plex Mono",monospace;font-size:30px;font-weight:500;
 letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.ctot .cap{font-size:13px;color:var(--ink-3)}
.clist{list-style:none;margin:0;padding:8px 18px 18px}
.clist li{border-radius:6px}
.crow{display:grid;grid-template-columns:22px minmax(96px,1fr) 2.6fr 34px 44px 16px;
 align-items:center;gap:10px;padding:5px 0;border-radius:6px;cursor:pointer}
.crow:hover{background:var(--panel-2)}
.clist li.open>.crow{background:var(--panel-2)}
.chev{font-size:10px;color:var(--ink-3);transition:transform .12s ease;text-align:center}
.clist li.open .chev{transform:rotate(90deg)}
.clist .cn{font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.clist .track{display:block;height:9px;background:var(--line-soft);border-radius:99px;overflow:hidden}
.clist .fill{display:block;height:9px;background:var(--la);border-radius:0 4px 4px 0;min-width:3px}
.clist .cnum{font-family:"IBM Plex Mono",monospace;font-size:13px;text-align:right;
 font-variant-numeric:tabular-nums}
.clist .cpct{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--ink-3);
 text-align:right;font-variant-numeric:tabular-nums}
@media (max-width:600px){.crow{grid-template-columns:22px minmax(84px,1fr) 1.4fr 30px 40px 16px}}

/* the members inside an expanded country */
.cmem{list-style:none;margin:2px 0 10px;padding:0 0 0 32px;
 border-left:2px solid var(--line-soft);margin-left:9px}
.cmem li{display:flex;align-items:center;gap:11px;padding:7px 0;cursor:pointer;
 border-top:1px solid var(--line-soft)}
.cmem li:first-child{border-top:none}
.cmem li:hover{background:var(--panel-2)}
.cmem .who{flex:1;min-width:0}
.cmem .nm{font-size:13.5px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cmem .mt{font-size:11.5px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cmem .amt{font-size:12.5px}
.cmem .mailrow{padding:0 0 10px 0;margin:0}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <header>
    <div>
      <div class="eyebrow">Pick 6 Athletics &nbsp;·&nbsp; Lockdown Academy</div>
      <h1>Member Dashboard</h1>
    </div>
    <div class="stamp">
      <div class="live"><span class="dot dot-ok" id="syncdot"></span><span id="synctext"></span></div>
      <div class="eyebrow" style="margin-top:4px" id="syncsub"></div>
    </div>
  </header>

  <section class="kpis" id="kpis"></section>

  <div class="windowrow">
    <div class="seg" id="range" role="group" aria-label="History range"></div>
    <div class="winmetric" id="wintile"></div>
  </div>

  <section class="panel">
    <div class="phead">
      <h2>Members by tier</h2>
      <div class="legend"><span id="zoomnote" class="zoomnote" hidden></span><span id="legend"></span></div>
    </div>
    <div class="pbody">
      <div class="chartbox" id="chart"><div class="tip" id="tip"></div></div>
    </div>
  </section>

  <section class="panel">
    <div class="phead"><h2>By tier</h2><div class="note" id="tablenote"></div></div>
    <div class="scroll">
      <table>
        <thead><tr>
          <th>Tier</th><th class="n">Active</th><th class="n">Past due</th>
          <th class="n">Leaving</th><th class="n">Monthly USD</th><th class="n">Monthly CAD</th><th class="n">Total CAD</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
        <tfoot id="tfoot"></tfoot>
      </table>
    </div>
  </section>

  <div class="rangebar tierbar" role="group" aria-label="Tier filter">
    <span class="eyebrow">Filter the lists below by tier</span>
    <div class="seg" id="tierfilter"></div>
  </div>

  <div class="duo">
    <section class="panel" id="pdpanel">
      <div class="phead"><h2>Past due</h2><div class="note">Chase these</div></div>
      <ul class="people" id="pastdue"></ul>
    </section>
    <section class="panel">
      <div class="phead"><h2>Leaving at period end</h2><div class="note" id="leavingNote"></div></div>
      <ul class="people" id="leaving"></ul>
    </section>
  </div>

  <div class="duo">
    <section class="panel">
      <div class="phead"><h2>Joined</h2><div class="note" id="joinedNote"></div></div>
      <ul class="people" id="joined"></ul>
    </section>
    <section class="panel">
      <div class="phead"><h2>Churned</h2><div class="note" id="churnedNote"></div></div>
      <ul class="people" id="churned"></ul>
    </section>
  </div>

  <section class="panel" style="margin-top:22px">
    <div class="phead"><h2>Find a member</h2><div class="note" id="searchnote"></div></div>
    <div class="searchbar">
      <input id="q" type="search" autocomplete="off" spellcheck="false"
             placeholder="Search every member, past or present — name, email or country">
    </div>
    <ul class="people" id="results"></ul>
  </section>

  <section class="panel" style="margin-top:22px">
    <div class="phead"><h2>Members by country</h2><div class="note" id="ctrynote"></div></div>
    <div class="ctot"><span class="big" id="ctrytotal"></span><span class="cap" id="ctrycap"></span></div>
    <ul class="clist" id="ctrylist"></ul>
  </section>

  <footer>
    <span id="footnote">Source: Stripe (Pick6athletics), read-only. "Leaving" = cancelled but still inside their paid term — what Mighty labels "Cancelled". <span id="fxnote"></span></span>
    <span class="mono" id="foot"></span>
  </footer>
</div>

__BAKETAG__
<script>
__ENGINE__
let D = compute();
const $ = s => document.querySelector(s);
const FX = D.fx || {usd_to_cad:1,as_of:'n/a'};
const money  = n => 'CA$' + n.toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:0});
const money2 = n => 'CA$' + n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const plain  = n => n.toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:0});
// native = what the member is actually charged, in their own currency
const nat = (amt,cur) => (cur==='usd'?'US$':'CA$') + amt.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const esc = s => String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const BR = {'Coach':'var(--s1)','Athlete':'var(--s2)','Pro':'var(--s3)','Legacy':'var(--s4)','Other':'var(--ink-3)','Free':'var(--ink-3)','Elite':'var(--s3)'};

let RANGE = '7';                        // always opens on 7 days
let TIER  = 'all';                      // tier filter for the people lists
let ZOOM  = 1;                          // vertical zoom on the chart (pinch to change)
let PAN   = 0;                          // value at the bottom of the visible y range
let VIS   = {};                         // which series are drawn - click the legend
let VIEW  = {fullMax:1, yMax:1};        // last drawn scale, so pan can be clamped
const WIN = Object.fromEntries(D.windows.map(w=>[w.key,w]));
const winStart = () => WIN[RANGE].start;
const winLabel = () => WIN[RANGE].label;
const inWin = ts => ts >= winStart();
$('#foot').textContent = D.generated;
function renderFoot(){ $('#foot').textContent = D.generated; $('#fxnote').innerHTML = `USD and CAD are kept <b>separate</b> and never added together — ${D.totals.usd_n} subscriptions bill in USD, ${D.totals.cad_n} in CAD. If you want one combined figure, CA$${plain(D.totals.mrr)} / US$${plain(D.totals.mrr_usd_view)} at ${FX.usd_to_cad} CAD per USD (${FX.as_of}, ${FX.source}).`; }

/* ---------- KPIs (recomputed per range) ---------- */
function renderKPIs(){
  const T = D.totals;
  const pts = D.trends[RANGE].usd.map((p,i)=>p.Total + D.trends[RANGE].cad[i].Total);
  const delta = pts[pts.length-1] - pts[0];
  const nJoined  = D.joined.filter(p=>inWin(p.ts)).length;
  const nChurned = D.churned.filter(p=>inWin(p.ts)).length;
  const net = nJoined - nChurned;
  const arrow = n => n>0?'▲':n<0?'▼':'—';
  const cls   = n => n>0?'up':n<0?'down':'flat';
  const kpis = [
    {k:'Active members', v:T.active, sub:''},
    {k:'Monthly · USD', v:'US$'+plain(T.usd_mrr),
     sub:`<span class="money">${T.usd_n} subscriptions</span>`, small:true},
    {k:'Monthly · CAD', v:'CA$'+plain(T.cad_mrr),
     sub:`<span class="money">${T.cad_n} subscriptions</span>`, small:true},
    {k:'Total · CAD', v:'CA$'+plain(T.mrr), small:true,
     sub:`<span class="money">USD converted at ${FX.usd_to_cad}</span>`},

    {k:'Leaving at period end', v:T.leaving, sub:`<span class="money">Already cancelled, term not up</span>`},
    {k:'Past due', v:T.past_due, hot:T.past_due>0,
     sub:`<span class="${T.owed>0?'down':'flat'}">${[T.owed_usd?'US$'+T.owed_usd.toFixed(2):null, T.owed_cad?'CA$'+T.owed_cad.toFixed(2):null].filter(Boolean).join(' + ')||'nothing'} outstanding</span>`},
    {k:'Joined · churned', windowed:true, small:(String(nJoined).length+String(nChurned).length)>4,
     v:`<span class="up">${nJoined}</span><span style="color:var(--ink-3)"> / </span><span class="down">${nChurned}</span>`,
     sub:`<span class="${cls(net)}">${net>0?'+':''}${net} net over ${winLabel().toLowerCase()}</span>`}
  ];
  const card = o=>`
    <div class="kpi">
      ${o.accent?`<span class="curstripe" style="background:${o.accent}"></span>`:''}
      <div class="eyebrow">${o.k}</div>
      <div class="num v"${o.small?' style="font-size:29px"':''}>${o.v}</div>
      <div class="sub">${o.sub}</div>
    </div>`;
  $('#kpis').innerHTML = kpis.filter(o=>!o.windowed).map(card).join('');
  const w = kpis.find(o=>o.windowed);
  $('#wintile').innerHTML = `<span class="lbl">${w.k}</span><span class="fig">${w.v}</span><span class="note">${w.sub}</span>`;
}

/* ---------- Trend charts: one per billing currency, redrawn on range change ---------- */
const SER = GROUPS.map(g=>({n:g,c:BR[g]}));
const SLOT=['s1','s2','s3','s4'];
const SERIES = [...SER, {n:'Total', c:'var(--total)'}];
SERIES.forEach(s=>{ if(!(s.n in VIS)) VIS[s.n]=true; });
try{ const saved=JSON.parse(localStorage.getItem('p6vis')||'null');
     if(saved) SERIES.forEach(s=>{ if(s.n in saved) VIS[s.n]=!!saved[s.n]; }); }catch(_){}
function renderLegend(){
  $('#legend').innerHTML = SERIES.map(s=>
    `<button type="button" class="lg" data-s="${s.n}" aria-pressed="${VIS[s.n]}"
       title="${VIS[s.n]?'Hide':'Show'} ${s.n}"><span class="sw" style="background:${s.c}"></span>${s.n}</button>`
  ).join('');
}
renderLegend();

const W=1100, H=300, M={t:18,r:64,b:30,l:38};
const pw=W-M.l-M.r, ph=H-M.t-M.b;

// USD and CAD books added together - headcount is headcount, currency is irrelevant here
function combined(k){
  const u=D.trends[k].usd, c=D.trends[k].cad;
  return u.map((p,i)=>{
    const o={d:p.d, Total:p.Total + c[i].Total};
    GROUPS.forEach(g=>o[g]=p[g]+c[i][g]);
    return o;
  });
}
function drawChart(boxSel, tipSel, pts){
  const box=$(boxSel); box.querySelector('svg')?.remove();
  const N=pts.length;
  const X = i => M.l + (i/(N-1))*pw;
  const shown = [...GROUPS, 'Total'].filter(k=>VIS[k]);
  const maxV = shown.length ? Math.max(1, ...pts.flatMap(p=>shown.map(k=>p[k]))) : 1;
  const baseStep = maxV>60?20:maxV>30?10:maxV>12?5:2;
  const fullMax = Math.ceil(maxV/baseStep)*baseStep + baseStep;
  const yMax = fullMax / ZOOM;                       // pinch shrinks the visible range
  PAN = Math.min(Math.max(PAN, 0), Math.max(0, fullMax - yMax));   // keep the view inside the data
  VIEW = {fullMax, yMax};
  const yStep = yMax>60?20:yMax>30?10:yMax>12?5:yMax>6?2:1;
  const Y = v => M.t + ph - ((v - PAN)/yMax)*ph;
  const path = k => pts.map((p,i)=>`${i?'L':'M'}${X(i).toFixed(1)},${Y(p[k]).toFixed(1)}`).join(' ');
  const floorY = (M.t+ph).toFixed(1);   // bottom of the plot, whatever value that is now
  const area = k => `${path(k)} L${X(N-1).toFixed(1)},${floorY} L${X(0).toFixed(1)},${floorY} Z`;
  const ticks=[];
  for(let v=Math.ceil(PAN/yStep)*yStep; v<=PAN+yMax+0.001; v+=yStep) ticks.push(v);
  const dfmt = s => new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:(RANGE==='all'||RANGE==='ytd')?'2-digit':undefined,timeZone:'UTC'});
  const xlabels=[0, Math.floor(N/3), Math.floor(2*N/3), N-1].map(i=>({i,l:dfmt(pts[i].d)}));
  const uid = boxSel.replace(/\W/g,'');
  // direction over the visible window decides the endpoint colour
  const dirOf = g => { const d = pts[N-1][g]-pts[0][g]; return d>0?'var(--good)':d<0?'var(--bad)':'var(--ink-3)'; };
  const dirArrow = g => { const d = pts[N-1][g]-pts[0][g]; return d>0?'▲':d<0?'▼':''; };
  // nudge end-of-line labels apart so they never sit on top of each other
  const clampY = y => Math.min(Math.max(y, M.t+4), M.t+ph-4);
  const LABELS = [...GROUPS, 'Total'].filter(k=>VIS[k]);
  const labelYs = LABELS.map(g=>({g, y:clampY(Y(pts[N-1][g]))})).sort((a,b)=>a.y-b.y);
  const GAP=15;
  for(let i=1;i<labelYs.length;i++)
    if(labelYs[i].y - labelYs[i-1].y < GAP) labelYs[i].y = labelYs[i-1].y + GAP;
  const overflow = labelYs[labelYs.length-1].y - (M.t+ph);
  if(overflow>0) labelYs.forEach(o=>o.y -= overflow);
  box.insertAdjacentHTML('afterbegin', `
<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Active members per tier over ${winLabel()}">
  <defs>
    <clipPath id="${uid}clip"><rect x="${M.l}" y="${M.t}" width="${pw}" height="${ph}"/></clipPath>
    ${GROUPS.map((g,i)=>`<linearGradient id="${uid}g${i}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--${SLOT[i]})" stop-opacity=".15"/><stop offset="100%" stop-color="var(--${SLOT[i]})" stop-opacity="0"/>
    </linearGradient>`).join('')}</defs>
  ${ticks.map(v=>`<line x1="${M.l}" x2="${M.l+pw}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--chalk)" stroke-width="1" opacity="${v===0?'.9':'.4'}"/>
     <text x="${M.l-9}" y="${Y(v)+4}" text-anchor="end" font-family="IBM Plex Mono" font-size="11" fill="var(--ink-3)">${v}</text>`).join('')}
  ${xlabels.map(o=>`<text x="${X(o.i)}" y="${M.t+ph+20}" text-anchor="${o.i===0?'start':o.i===N-1?'end':'middle'}" font-family="IBM Plex Mono" font-size="11" fill="var(--ink-3)">${o.l}</text>`).join('')}
  <g clip-path="url(#${uid}clip)">
  ${GROUPS.map((g,i)=>VIS[g]?`<path d="${area(g)}" fill="url(#${uid}g${i})"/>`:'').join('')}
  ${GROUPS.map((g,i)=>VIS[g]?`<path d="${path(g)}" fill="none" stroke="var(--${SLOT[i]})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`:'').join('')}
  ${VIS.Total?`<path d="${path('Total')}" fill="none" stroke="var(--total)" stroke-width="2.5"
        stroke-linejoin="round" stroke-linecap="round"/>`:''}
  ${GROUPS.map((g,i)=>VIS[g]?`<circle cx="${X(N-1)}" cy="${Y(pts[N-1][g])}" r="4.5" fill="var(--${SLOT[i]})" stroke="var(--panel)" stroke-width="2"/>`:'').join('')}
  ${VIS.Total?`<circle cx="${X(N-1)}" cy="${Y(pts[N-1].Total)}" r="4.5" fill="var(--total)" stroke="var(--panel)" stroke-width="2"/>`:''}
  </g>
  ${labelYs.map(o=>`<text x="${X(N-1)+10}" y="${o.y+4}" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="${dirOf(o.g)}">${dirArrow(o.g)}${pts[N-1][o.g]}</text>`).join('')}
  <line class="cross" x1="0" x2="0" y1="${M.t}" y2="${M.t+ph}" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3" opacity="0"/>
  <g clip-path="url(#${uid}clip)">${LABELS.map(k=>`<circle class="hd" r="5" fill="${k==='Total'?'var(--total)':`var(--${SLOT[GROUPS.indexOf(k)]})`}" stroke="var(--panel)" stroke-width="2" opacity="0"/>`).join('')}</g>
  <rect x="${M.l}" y="${M.t}" width="${pw}" height="${ph}" fill="transparent"/>
</svg>`);
  const svg=box.querySelector('svg'), tip=$(tipSel);
  const cross=svg.querySelector('.cross'), hds=[...svg.querySelectorAll('.hd')];
  svg.addEventListener('mousemove', e=>{
    const r=svg.getBoundingClientRect(); const sx=(e.clientX-r.left)/r.width*W;
    let i=Math.round((sx-M.l)/pw*(N-1)); i=Math.max(0,Math.min(N-1,i));
    const p=pts[i], px=X(i);
    cross.setAttribute('opacity','1'); cross.setAttribute('x1',px); cross.setAttribute('x2',px);
    hds.forEach((c,k)=>{c.setAttribute('opacity','1');c.setAttribute('cx',px);c.setAttribute('cy',Y(p[LABELS[k]]));});
    tip.innerHTML=`<div class="td">${dfmt(p.d)}</div>`+
      SER.filter(s=>VIS[s.n]).map(s=>`<div class="tr"><span><span class="sw" style="display:inline-block;background:${s.c};margin-right:6px;vertical-align:middle"></span>${s.n}</span><b>${p[s.n]}</b></div>`).join('')+
      `<div class="tr" style="margin-top:5px;padding-top:5px;border-top:1px solid var(--line-soft)"><span style="color:var(--ink-3)">Total</span><b>${p.Total}</b></div>`;
    tip.style.opacity='1';
    const left=px/W*r.width;
    tip.style.left=Math.min(Math.max(left+14,0), r.width-tip.offsetWidth-4)+'px';
    tip.style.top='8px';
  });
  svg.addEventListener('mouseleave',()=>{tip.style.opacity='0';cross.setAttribute('opacity','0');hds.forEach(c=>c.setAttribute('opacity','0'));});

}

function touchDist(e){
  const [a,b]=e.touches;
  return Math.hypot(a.clientX-b.clientX, a.clientY-b.clientY);
}
let zoomQueued=false;
function scheduleRedraw(){
  if(zoomQueued) return;
  zoomQueued=true;
  requestAnimationFrame(()=>{ zoomQueued=false; drawChart('#chart','#tip', combined(RANGE)); renderZoomNote(); });
}
function setZoom(z){
  const next = Math.min(20, Math.max(1, z));
  if(Math.abs(next-ZOOM) < 0.001) return;
  const centre = PAN + VIEW.yMax/2;              // hold the middle of the view steady
  ZOOM = next;
  const newMax = VIEW.fullMax / ZOOM;
  PAN = Math.min(Math.max(centre - newMax/2, 0), Math.max(0, VIEW.fullMax - newMax));
  if(ZOOM<=1.001) PAN = 0;
  scheduleRedraw();
}
// dyPx > 0 moves the view UP through the data (content follows the pointer)
function panBy(dyPx){
  if(ZOOM<=1.001) return false;
  const perPx = VIEW.yMax / (H - M.t - M.b);
  const limit = Math.max(0, VIEW.fullMax - VIEW.yMax);
  const next = Math.min(Math.max(PAN + dyPx*perPx, 0), limit);
  if(Math.abs(next-PAN) < 0.0001) return false;   // at the edge - let the page scroll
  PAN = next; scheduleRedraw(); return true;
}
function renderZoomNote(){
  const n=$('#zoomnote');
  if(ZOOM<=1.01){ n.hidden=true; n.innerHTML=''; PAN=0; return; }
  n.hidden=false;
  n.innerHTML = `${ZOOM.toFixed(1)}× vertical · drag to pan <button type="button" id="zoomreset">Reset</button>`;
  $('#zoomreset').onclick = ()=>setZoom(1);
}

// Pinch to zoom the vertical scale. A trackpad pinch arrives as a wheel event with
// ctrlKey set; two-finger touch is handled separately. Bound ONCE to the container,
// which survives every redraw - binding inside drawChart stacked duplicate listeners
// and broke double-click-to-reset.
$('#legend').addEventListener('click', e=>{
  const b=e.target.closest('button.lg'); if(!b) return;
  VIS[b.dataset.s] = !VIS[b.dataset.s];
  if(!Object.values(VIS).some(Boolean)) VIS[b.dataset.s] = true;   // never hide everything
  try{ localStorage.setItem('p6vis', JSON.stringify(VIS)); }catch(_){}
  ZOOM=1; PAN=0;                                                   // rescale to what is showing
  renderLegend(); scheduleRedraw();
});

(function bindZoom(){
  const box=$('#chart');
  box.addEventListener('wheel', e=>{
    if(e.ctrlKey){                      // pinch
      e.preventDefault();
      setZoom(ZOOM * Math.exp(-e.deltaY * 0.005));
      return;
    }
    // once zoomed, a plain scroll over the chart pans it vertically - until it hits
    // an edge, at which point the page takes over again
    if(panBy(-e.deltaY)) e.preventDefault();
  }, {passive:false});

  let drag=null;
  box.addEventListener('pointerdown', e=>{
    if(ZOOM<=1.001 || e.button!==0) return;
    drag={y:e.clientY}; box.setPointerCapture(e.pointerId); box.style.cursor='grabbing';
  });
  box.addEventListener('pointermove', e=>{
    if(!drag) return;
    panBy(e.clientY - drag.y); drag.y=e.clientY;
  });
  const endDrag = e=>{ if(!drag) return; drag=null; box.style.cursor=''; try{box.releasePointerCapture(e.pointerId);}catch(_){} };
  box.addEventListener('pointerup', endDrag);
  box.addEventListener('pointercancel', endDrag);
  let pinchStart=null;
  box.addEventListener('touchstart', e=>{ if(e.touches.length===2) pinchStart={d:touchDist(e), z:ZOOM}; }, {passive:true});
  box.addEventListener('touchmove', e=>{
    if(e.touches.length===2 && pinchStart){ e.preventDefault(); setZoom(pinchStart.z * (touchDist(e)/pinchStart.d)); }
  }, {passive:false});
  box.addEventListener('touchend', ()=>{ pinchStart=null; }, {passive:true});
  box.addEventListener('dblclick', e=>{ e.preventDefault(); PAN=0; setZoom(1); scheduleRedraw(); });
})();

/* ---------- Tier table ---------- */
function renderTable(){
const T = D.totals;
$('#tablenote').innerHTML = `Total CAD converts USD at <b>${FX.usd_to_cad}</b> · rate as of ${FX.as_of}`;
const maxOne=Math.max(...D.tiers.flatMap(t=>[t.usd,t.cad]));
const byGroup={}; D.tiers.forEach(t=>{(byGroup[t.group]=byGroup[t.group]||[]).push(t)});
$('#tbody').innerHTML = GROUPS.filter(g=>byGroup[g]).map(g=>{
 const G=D.groups.find(x=>x.group===g);
 const head=`<tr class="grouprow"><td><span class="tierName"><span class="rail" style="background:${BR[g]}"></span><b>${g}</b></span></td>
   <td class="n"><b>${G.active}</b></td><td class="n">${G.past_due?`<span class="pill bad">${G.past_due}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
   <td class="n">${G.leaving?`<span class="pill warn">${G.leaving}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
   <td class="n"><b>${G.usd?'US$'+plain(G.usd):'<span style="color:var(--ink-3);font-weight:400">—</span>'}</b></td>
   <td class="n"><b>${G.cad?'CA$'+plain(G.cad):'<span style="color:var(--ink-3);font-weight:400">—</span>'}</b></td>
   <td class="n" style="color:var(--ink)"><b>CA$${plain(G.mrr)}</b></td></tr>`;
 return head + byGroup[g].map(t=>`
 <tr class="subrow">
  <td><span class="tierName" style="padding-left:16px;font-weight:400;color:var(--ink-2)">${esc(t.tier)}</span></td>
  <td class="n">${t.active}</td>
  <td class="n">${t.past_due? `<span class="pill bad">${t.past_due}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n">${t.leaving? `<span class="pill warn">${t.leaving}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n">${t.usd?`<span class="barwrap"><span class="bar" style="width:${Math.max(4,t.usd/maxOne*54)}px;background:var(--ink-3);opacity:.4"></span>US$${plain(t.usd)}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n">${t.cad?`<span class="barwrap"><span class="bar" style="width:${Math.max(4,t.cad/maxOne*54)}px;background:var(--ink-3);opacity:.4"></span>CA$${plain(t.cad)}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n" style="color:var(--ink-2)">CA$${plain(t.mrr)}</td>
 </tr>`).join('');}).join('');
$('#tfoot').innerHTML = `<tr><td>All tiers</td><td class="n">${T.active}</td><td class="n">${T.past_due}</td>
  <td class="n">${T.leaving}</td>
  <td class="n">US$${plain(T.usd_mrr)}</td><td class="n">CA$${plain(T.cad_mrr)}</td>
  <td class="n">CA$${plain(T.mrr)}</td></tr>`;
}   /* end renderTable */

/* ---------- People lists ---------- */
/* ---------- Country flags ----------
   A 2-letter ISO code maps to its flag by offsetting each letter into the
   regional-indicator block. Intl gives us the full name for the tooltip. */
let RNAME=null;
try{ RNAME = new Intl.DisplayNames(['en'],{type:'region'}); }catch(_){ RNAME=null; }
const ctryName = cc => { try{ return (RNAME && RNAME.of(cc)) || cc; }catch(_){ return cc; } };
function flag(cc){
  if(!cc || cc.length!==2) return `<span class="flag none" title="Country unknown — no card on file">—</span>`;
  const c = cc.toUpperCase();
  const em = String.fromCodePoint(...[...c].map(ch=>127397+ch.charCodeAt(0)));
  return `<span class="flag" title="${esc(ctryName(c))}" aria-label="${esc(ctryName(c))}">${em}</span>`;
}

function person(p, right){
  return `<li><span class="rail" style="background:${BR[p.group]}"></span>
    <span class="who"><span class="nm">${flag(p.cc)} ${esc(p.name)}</span><br><span class="mt">${esc(p.tier)}</span></span>
    ${right}</li>`;
}
const tierOK = p => TIER==='all' || p.group===TIER;
function renderPeople(){
  const J = D.joined.filter(p=>inWin(p.ts) && tierOK(p)), C = D.churned.filter(p=>inWin(p.ts) && tierOK(p));
  $('#joined').innerHTML = J.length ? J.map(p=>person(p,
    `<span class="amt ${p.gone?'flat':'up'}">${p.gone?'':'+'}${nat(p.amt,p.cur)}</span><span class="when">${p.date}${p.gone?` <span style="color:var(--bad)">→ left ${p.gone}</span>`:''}</span>`)).join('')
    : `<div class="empty">Nobody new in the last ${winLabel().toLowerCase()}.</div>`;
  $('#churned').innerHTML = C.length ? C.map(p=>person(p,
    `<span class="amt down">−${nat(p.amt,p.cur)}</span><span class="when down">${p.date}</span>`)).join('')
    : `<div class="empty">Nobody left in the last ${winLabel().toLowerCase()}.</div>`;
  const stayed = J.filter(p=>!p.gone).length;
  $('#joinedNote').innerHTML  = `${J.length} started${J.length-stayed?` · <span style="color:var(--bad)">${J.length-stayed} already gone</span>`:''}`;
  $('#churnedNote').innerHTML = `<span class="down">${C.length} ended</span>`;
}
function renderLeaving(){
const L = D.leaving.filter(tierOK);
$('#leaving').innerHTML = L.length ? L.map(p=>person(p,
  `<span class="amt down">${nat(p.amt,p.cur)}</span><span class="when down">ends ${p.ends}</span>`)).join('')
  : `<div class="empty">${TIER==='all'?'Nobody has cancelled ahead.':'No '+TIER+' members have cancelled ahead.'}</div>`;
$('#leavingNote').innerHTML = `<span class="down">${L.length} cancelled, still training</span>`;
}
function renderPastDue(){
const P = D.past_due.filter(tierOK);
$('#pastdue').innerHTML = P.length ? P.map(p=>`
  <li><span class="rail" style="background:var(--bad)"></span>
   <span class="who"><span class="nm">${flag(p.cc)} ${esc(p.name)}</span><br>
     <span class="mt down">${esc(p.tier)} · ${p.days} day${p.days===1?'':'s'} overdue${p.url?` · <a class="inv" href="${p.url}" target="_blank" rel="noopener">invoice</a>`:''}</span></span>
   <span class="amt down">${nat(p.owed,p.owed_cur||p.cur)}</span></li>`).join('')
  : `<div class="empty">${TIER==='all'?'Everyone is paid up.':'No '+TIER+' members are past due.'}</div>`;
$('#pdpanel').querySelector('.note').textContent = P.length ? 'Chase these' : 'All clear';
}

/* ---------- Member search ----------
   Searches the whole roster - every subscription that has ever existed, not
   just current members - so "was this guy ever a member?" is answerable.
   Email is matchable but stays hidden until the row is clicked. */
const CAP = 60;
let OPEN = new Set();      // revealed emails, in search and country lists alike
let OPENCC = new Set();    // expanded country rows
const norm = s => String(s||'').toLowerCase();
const RANK = {past_due:0, leaving:1, active:2, gone:3};

/* One row per PERSON, not per subscription. Grouped on customer id — never on
   name, because members missing from the name map are all "Unknown" and would
   collapse together. Someone who has held three plans is one row listing three. */
function groupPeople(rows){
  const m = new Map();
  for(const r of rows){
    if(!m.has(r.cid)) m.set(r.cid, {cid:r.cid, name:r.name, email:r.email, cc:r.cc, subs:[]});
    m.get(r.cid).subs.push(r);
  }
  for(const p of m.values()){
    p.subs.sort((a,b)=> RANK[a.state]-RANK[b.state] || b.ts-a.ts);
    p.lead  = p.subs[0];                                   // most pressing status
    p.plans = [...new Set(p.subs.map(s=>s.tier))].join(' + ');
    p.money = p.subs.filter(s=>s.state!=='gone').map(s=>nat(s.amt,s.cur)).join(' + ')
              || nat(p.subs[0].amt, p.subs[0].cur);
    p.since = p.subs.map(s=>s.ts).sort((a,b)=>a-b)[0];
    p.sinceLabel = p.subs.find(s=>s.ts===p.since).since;
  }
  return [...m.values()];
}

function searchHits(q){
  const terms = norm(q).split(/\s+/).filter(Boolean);
  if(!terms.length) return null;
  return groupPeople(D.roster).filter(p=>{
    const hay = [norm(p.name), norm(p.email), norm(p.cc), norm(p.cc && ctryName(p.cc)),
                 ...p.subs.map(s=>norm(s.tier))].join(' ');
    return terms.every(t=>hay.includes(t));
  }).sort((a,b)=> RANK[a.lead.state]-RANK[b.lead.state] || b.lead.ts-a.lead.ts);
}

function renderSearch(){
  const q = $('#q').value.trim();
  const hits = searchHits(q);
  const note = $('#searchnote'), out = $('#results');

  if(hits===null){
    note.textContent = `${groupPeople(D.roster).length} people, all time`;
    out.innerHTML = `<div class="empty">Type a name, an email, or a country — "canada", "athlete", "gmail". Everyone who has ever been a member is in here.</div>`;
    return;
  }
  if(!hits.length){
    note.textContent = 'No match';
    out.innerHTML = `<div class="empty">Nobody matches “${esc(q)}”.</div>`;
    return;
  }
  const shown = hits.slice(0, CAP);
  note.innerHTML = hits.length>CAP
    ? `${hits.length} matches · showing first ${CAP}`
    : `${hits.length} match${hits.length===1?'':'es'}`;

  out.innerHTML = shown.map(p=>{
    const key = 'q:'+p.cid;
    const open = OPEN.has(key);
    const mail = p.email
      ? `<div class="mailrow"><a href="mailto:${esc(p.email)}">${esc(p.email)}</a></div>`
      : `<div class="mailrow" style="color:var(--ink-3)">No email on file</div>`;
    return `<li class="hit" data-k="${esc(key)}" title="Click to ${open?'hide':'show'} email">
        <span class="rail" style="background:${BR[p.lead.group]}"></span>
        <span class="who"><span class="nm">${flag(p.cc)} ${esc(p.name)}</span><br>
          <span class="mt">${esc(p.plans)} · joined ${p.sinceLabel}</span></span>
        <span class="st ${p.lead.state}">${esc(p.lead.label)}</span>
        <span class="amt ${p.lead.state==='active'?'':'flat'}">${p.money}</span>
      </li>${open?mail:''}`;
  }).join('');
}

$('#results').addEventListener('click', e=>{
  const li = e.target.closest('li.hit'); if(!li) return;
  const k = li.dataset.k;
  OPEN.has(k) ? OPEN.delete(k) : OPEN.add(k);
  renderSearch();
});
$('#q').addEventListener('input', ()=>{ OPEN.clear(); renderSearch(); });

/* ---------- Members by country ----------
   One series (a count), so: no legend, no categorical palette, every bar the
   same hue. The country name carries identity; the bar carries magnitude. */
function renderCountries(){
  const L = D.countries, total = D.cc_known + D.cc_unknown;
  $('#ctrytotal').textContent = total;
  $('#ctrycap').innerHTML = `${total===1?'person':'people'} paying you, across
    <strong style="color:var(--ink-2)">${L.length}</strong> countr${L.length===1?'y':'ies'}`;
  $('#ctrynote').textContent = D.cc_unknown
    ? `${D.cc_unknown} without a country on file`
    : 'Every member mapped';

  if(!L.length){ $('#ctrylist').innerHTML =
    `<div class="empty">No country data yet.</div>`; return; }

  const max = L[0].n;
  $('#ctrylist').innerHTML = L.map(r=>{
    const pct  = total ? (r.n/total*100) : 0;
    const nm   = ctryName(r.cc);
    const open = OPENCC.has(r.cc);
    return `<li class="${open?'open':''}">
      <div class="crow" data-cc="${esc(r.cc)}" role="button" tabindex="0"
           aria-expanded="${open}"
           title="${esc(nm)} — ${r.n} of ${total} members (${pct.toFixed(1)}%) · click for the list">
        ${flag(r.cc)}
        <span class="cn">${esc(nm)}</span>
        <span class="track"><span class="fill" style="width:${(r.n/max*100).toFixed(1)}%"></span></span>
        <span class="cnum">${r.n}</span>
        <span class="cpct">${pct.toFixed(1)}%</span>
        <span class="chev">▶</span>
      </div>
      ${open ? memberList(r.cc) : ''}
    </li>`;
  }).join('');
}

/* The people behind one country bar. Current members only — the bar counts
   people, so this list must too: one row per person, their plans listed
   together rather than as separate rows. */
function memberList(cc){
  const live = new Set(['active','past_due','leaving']);
  const people = groupPeople(D.roster.filter(r=>r.cc===cc && live.has(r.state)))
    .sort((a,b)=>a.name.localeCompare(b.name,'en',{sensitivity:'base'}));

  return `<ul class="cmem">` + people.map(p=>{
    const key  = 'cc:'+p.cid;
    const open = OPEN.has(key);
    const mail = p.email
      ? `<div class="mailrow"><a href="mailto:${esc(p.email)}">${esc(p.email)}</a></div>`
      : `<div class="mailrow" style="color:var(--ink-3)">No email on file</div>`;
    return `<li data-k="${esc(key)}" title="Click to ${open?'hide':'show'} email">
        <span class="who"><span class="nm">${esc(p.name)}</span><br>
          <span class="mt">${esc(p.plans)} · joined ${p.sinceLabel}</span></span>
        <span class="st ${p.lead.state}">${esc(p.lead.label)}</span>
        <span class="amt ${p.lead.state==='active'?'':'flat'}">${p.money}</span>
      </li>${open?mail:''}`;
  }).join('') + `</ul>`;
}

$('#ctrylist').addEventListener('click', e=>{
  const mem = e.target.closest('.cmem li');
  if(mem){                                   // a person inside a country
    const k = mem.dataset.k;
    OPEN.has(k) ? OPEN.delete(k) : OPEN.add(k);
    renderCountries(); return;
  }
  const row = e.target.closest('.crow');
  if(!row) return;                           // a country bar
  const cc = row.dataset.cc;
  OPENCC.has(cc) ? OPENCC.delete(cc) : OPENCC.add(cc);
  renderCountries();
});
$('#ctrylist').addEventListener('keydown', e=>{
  if(e.key!=='Enter' && e.key!==' ') return;
  const row = e.target.closest('.crow'); if(!row) return;
  e.preventDefault();
  const cc = row.dataset.cc;
  OPENCC.has(cc) ? OPENCC.delete(cc) : OPENCC.add(cc);
  renderCountries();
  const again = $('#ctrylist').querySelector(`.crow[data-cc="${cc}"]`);
  if(again) again.focus();
});

/* ---------- Range toggle ---------- */
$('#range').innerHTML = D.windows.map(w=>
  `<button type="button" data-k="${w.key}" aria-pressed="${w.key===RANGE}">${w.label}</button>`).join('');
$('#tierfilter').innerHTML = ['all',...GROUPS].map(g=>
  `<button type="button" data-t="${g}" aria-pressed="${g===TIER}">${
    g==='all'?'All':`<span class="swd" style="background:${BR[g]}"></span>${g}`}</button>`).join('');
function redraw(){
  $('#range').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed', b.dataset.k===RANGE));
  $('#tierfilter').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed', b.dataset.t===TIER));
  renderKPIs();
  drawChart('#chart','#tip', combined(RANGE));
  renderZoomNote();
  renderPeople(); renderLeaving(); renderPastDue();
  renderTable(); renderFoot(); renderSearch(); renderCountries();
}
$('#tierfilter').addEventListener('click', e=>{
  const b=e.target.closest('button'); if(!b) return;
  TIER=b.dataset.t;
  try{ localStorage.setItem('p6tier', TIER); }catch(_){}
  redraw();
});
try{ const st=localStorage.getItem('p6tier'); if(st && (st==='all'||GROUPS.includes(st))) TIER=st; }catch(_){}
$('#range').addEventListener('click', e=>{
  const b=e.target.closest('button'); if(!b) return;
  RANGE=b.dataset.k; ZOOM=1; PAN=0;
  redraw();
});
redraw();
</script>
<script>
__SYNC__
</script>'''
# escape < so a name containing "</script" can never break out of the tag
BAKE_SAFE = BAKE.replace('<', '\\u003c')
BAKE_TAG = '<script id="bakedata" type="application/json">' + BAKE_SAFE + '</script>'
out=HTML.replace('__ENGINE__', ENGINE).replace('__SYNC__', SYNC).replace('__BAKETAG__', BAKE_TAG)
open(os.path.join(DIR,'live-board.html'),'w').write(out)
print('wrote live-board.html', round(len(out)/1024), 'KB')
