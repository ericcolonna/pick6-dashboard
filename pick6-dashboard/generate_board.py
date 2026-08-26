#!/usr/bin/env python3
"""
Pick 6 Member Dashboard - daily generator.

Inputs, all in DIR:
  all.json       every subscription: GetSubscriptions {limit:100, status:"all"},
                 paginated with starting_after, merged into ONE flat JSON array
  cmap.json      {customer_id: {name, email}} from GetCustomers. The .name field is
                 usually null - take .name // .description // .metadata.name.
                 Build with jq straight to JSON; a TSV breaks on names with tabs.
  open_slim.json open invoices: GetInvoices {limit:100, status:"open"} mapped to
                 [{id,cust,email,amt,cur_code,created,sub,desc,url,attempts,next}]
                 - cur_code is .currency and IS REQUIRED
  prodmap.json   {stripe_product_id: "Tier Name"}   (ships with this script)
  fx.json        {"usd_to_cad": 1.3834, "as_of": "...", "source": "...", "base": "CAD"}
                 refresh the rate whenever you refresh the board
  manual_members.csv   OPTIONAL - cash/manual members Eric maintains by hand

Run:  python3 generate_board.py [DIR]   ->  writes dash.json + roster-board.html
      (the output file keeps its original name; the page itself is "Member Dashboard")

Stripe account: acct_1QAluWL1hlk0mE2U (Pick6athletics), livemode true, READ scope only.
Artifact URL:   https://claude.ai/code/artifact/48d53f4b-ae90-4b3b-908e-ba6fd9825dc2

--- DESIGN RULES ERIC SET, do not undo them ---
CURRENCY: he bills in BOTH. Never add USD and CAD into one MONEY figure. Money gets
  separate KPI tiles and separate table columns; one converted figure lives in the
  footnote only, with rate and date. HEADCOUNT is different - the members-by-tier chart
  is a single combined chart, because a member is a member regardless of what currency
  they are billed in. Eric asked for this explicitly.
COLOUR: no orange anywhere. Tier hues set by Eric:
    Coach        = light green  (#4fbf6a light / #3fae63 dark)
    Athlete      = violet       (#8a5cd6 light / #9478de dark)
    Lockdown Pro = black        (#111111 light / #f2f6fc dark - black is invisible on
                                 the navy ground, so dark mode uses near-white)
    Legacy       = #003594      (his brand blue, exact in light mode; dark mode
                                 brightens to #2b62c9 because #003594 on the navy
                                 surface is only 1.58:1 contrast)
  The "decreasing" red is a deep blue-shifted crimson - #c8102e light / #e81f3d dark.
  Eric rejected both #e0736f (salmon) and #ff1f1f (bright) as reading orange; the fix
  was shifting the hue toward magenta and darkening, not more saturation.
  It applies to EVERY part of a losing row, not just the number: past-due meta lines,
  the leaving amounts and their "ends <date>", churned amounts and dates, and the panel
  subtitles. Watch the cascade - .who .mt and .when set their own muted colour, so the
  .down overrides live in a rule block at the very END of the stylesheet.
  Green and red stay RESERVED for direction - green = increasing, red = decreasing -
  on KPI deltas, joined/churned amounts, and the arrow on each line's end label. Coach
  being green is Eric's call; the direction arrows sit apart from the lines so it reads
  fine. Never introduce a red category.
TIER FILTER: sits BETWEEN the By Tier table and the Past Due / Leaving pair, not at the
  top - Eric moved it there so it sits with the lists it actually affects. All / Coach /
  Athlete / Pro / Legacy ("Lockdown Pro" is shortened to "Pro" in this control only),
  filtering the four people lists (past due, leaving,
  joined, churned). It does not touch the chart or the KPI tiles. Persists in
  localStorage.
DATES: every date in the people lists carries an apostrophe-prefixed 2-digit year
  ("Jul 6, '25") - the all-time view spans 2024-2026, bare "Jul 6" was ambiguous, and
  the apostrophe makes it unmistakably a year rather than a second day number.
NAMING: plan labels say "Legacy - Monthly", never "Lockdown Academy"; and "Pro -
  Monthly", never "Lockdown Pro" - Eric asked for both. Lives in prodmap.json, and the
  group name in build's GROUPS list is "Pro".
TOTAL LINE: the chart carries a fifth series - the sum of all tiers - as a solid black
  2.5px line (--total: #111 light / #f2f6fc dark), no area fill. Eric asked for solid
  black specifically. NOTE it shares its colour with the Pro tier; Pro is a flat line at
  1 so they do not currently overlap, but if Pro ever grows, change one of them.
  Total sets the y-scale and appears in the legend, end labels, and hover dots.
LEGEND TOGGLES: every legend entry is a button - click to show/hide that series,
  Total included. Hidden series drop out of the drawing, the end labels, the hover dots
  and the tooltip, and crucially out of the y-scale, so hiding Legacy and Total lets the
  small tiers fill the chart. The last visible series cannot be switched off. Choices
  persist in localStorage; toggling resets zoom and pan so the new scale is honest.
ZOOM: the chart takes a trackpad pinch (wheel + ctrlKey) or a two-finger touch pinch to
  scale the Y axis 1x-20x, so the small tiers can be read against the big Legacy line.
  Zooming holds the centre of the current view. Once zoomed, the chart PANS vertically:
  a plain scroll over it moves the view through the data and only hands scrolling back
  to the page at the top or bottom edge, and click-drag pans too. Double-click or the
  Reset chip returns to 1x and PAN 0; changing the range resets both. Bind
  the gesture listeners ONCE to #chart, never inside drawChart - drawChart runs on every
  redraw and duplicate listeners break the reset. Note .zoomnote needs an explicit
  [hidden]{display:none} rule because display:inline-flex otherwise wins.
RANGE: one centred, unlabelled toggle at the top drives everything - 7 days / 30 days /
  90 days / this year / all time. No "History" caption, Eric removed it. Charts, joined+churned lists, and the KPI deltas all follow it. Point-in-time
  figures (past due, leaving, cash members) do not.
NO revenue/expenses panel, and NO "cancelled all-time" column in the By Tier table -
  both removed at Eric's request. The canceled counts are still computed in dash.json,
  just not shown.
RECONCILIATION INVARIANT: for every range, joined - churned MUST equal the change in the
  chart total. That means "joined" counts every subscription that STARTED in the window
  (whether or not it has since ended) and "churned" counts every subscription that ENDED
  in the window, keyed on ended_at. Do NOT key churn on canceled_at (that is when someone
  clicked cancel, not when access stopped) and do NOT filter joiners to survivors - either
  mistake produces a net figure that contradicts the chart.

--- BUSINESS MEANINGS, confirmed by Eric ---
Reconciliation (Aug 25 2026): Stripe matched Mighty plan counts exactly - Coach 19,
  Athlete 22, Lockdown Pro 1, Platinum 0, Legacy 70, total 112.
Mighty "Cancelled"       == Stripe cancel_at_period_end == the "Leaving" column.
Mighty "Pending Payment" == Stripe incomplete_expired - abandoned signups, ignore.
"Legacy"                 == closed plans no longer sold. NOT a migration target.
"Erictest test"          == Eric's own $0 promo account. Leave it in.
"""
import sys, os
DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

import json, datetime, collections, csv, os, io
PRODMAP=json.load(open(os.path.join(DIR,'prodmap.json')))
FX=json.load(open('fx.json')) if os.path.exists('fx.json') else {"usd_to_cad":1.0,"as_of":"n/a","source":"none","base":"CAD"}
RATE=float(FX['usd_to_cad'])
def to_base(amount, cur):
    """Everything is reported in CAD. USD amounts convert at the stored rate."""
    return amount*RATE if cur=='usd' else amount
subs=json.load(open('all.json'))
cmap=json.load(open('cmap.json'))
openinv=json.load(open('open_slim.json'))
subix={s['id']:s for s in subs}
now=datetime.datetime.now(datetime.timezone.utc); nowts=now.timestamp()
LIVE=('active','past_due','trialing','unpaid')

def tier(s): return PRODMAP.get(s['items']['data'][0]['price']['product'], s['items']['data'][0]['price']['product'])
GROUPS=['Coach','Athlete','Pro','Legacy']
def group(t):
    h=t.split(' -')[0].strip()
    if h=='Coach': return 'Coach'
    if h=='Athlete': return 'Athlete'
    if h=='Pro': return 'Pro'
    return 'Legacy'
def who(cid):
    c=cmap.get(cid,{}); return c.get('name','Unknown'), c.get('email','')
def _per_month(s):
    it=s['items']['data'][0]; pr=it['price']
    amt=(pr.get('unit_amount') or 0)*it.get('quantity',1)/100
    r=pr['recurring']; m={'month':1,'year':12,'week':0.25,'day':1/30}[r['interval']]*r.get('interval_count',1)
    return amt/m, pr['currency']
def mrr_of(s):
    """Monthly value in CAD, the reporting currency."""
    v,cur=_per_month(s); return to_base(v,cur)
def native_of(s):
    v,cur=_per_month(s); return round(v,2), cur

split=collections.Counter(); splitn=collections.Counter()
tiers=collections.defaultdict(lambda: collections.Counter()); tmrr=collections.Counter()
tsplit=collections.defaultdict(lambda: collections.Counter()); tcount=collections.defaultdict(lambda: collections.Counter())
for s in subs:
    t=tier(s)
    if s['status'] in LIVE:
        tiers[t]['active' if s['status']!='past_due' else 'past_due']+=1
        tmrr[t]+=mrr_of(s)
        _v,_c=_per_month(s); split[_c]+=_v; splitn[_c]+=1
        tsplit[t][_c]+=_v; tcount[t][_c]+=1
        if s.get('cancel_at_period_end'): tiers[t]['leaving']+=1
    elif s['status']=='canceled': tiers[t]['canceled']+=1
tierlist=[{'tier':t,'group':group(t),'active':v['active'],'past_due':v['past_due'],'leaving':v['leaving'],
           'canceled':v['canceled'],'mrr':round(tmrr[t],2),
           'usd':round(tsplit[t]['usd'],2),'cad':round(tsplit[t]['cad'],2),
           'usd_n':tcount[t]['usd'],'cad_n':tcount[t]['cad']} for t,v in tiers.items() if v['active']+v['past_due']]
tierlist.sort(key=lambda x:(GROUPS.index(x['group']),-x['mrr']))

def fmt(ts):
    # year included - the all-time view spans 2024-2026 and bare "Jul 6" is ambiguous
    return datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).strftime("%b %-d, '%y")
def row(s,when):
    n,e=who(s['customer']); t=tier(s)
    nv,nc=native_of(s)
    return {'name':n,'email':e,'tier':t,'group':group(t),'date':fmt(when),'ts':when,
            'mrr':round(mrr_of(s),2),'amt':nv,'cur':nc}
# Joined  = every subscription that STARTED in the window (abandoned checkouts excluded),
#           whether or not it has since ended.
# Churned = every subscription that ENDED in the window (ended_at, i.e. access actually
#           stopped) - NOT canceled_at, which is merely when they clicked cancel.
# Using the same basis on both sides is what makes joined - churned equal the change
# in the chart. Mixing "still-alive joiners" with "all cancellers" does not reconcile.
real=[s for s in subs if s['status']!='incomplete_expired']
def jrow(s):
    r=row(s,s['created'])
    if s.get('ended_at'):
        r['gone']=fmt(s['ended_at'])
    return r
joined=sorted([jrow(s) for s in real],key=lambda x:-x['ts'])
churned=sorted([row(s,s['ended_at']) for s in real if s.get('ended_at')],key=lambda x:-x['ts'])
leaving=[]
for s in subs:
    if s['status'] in LIVE and s.get('cancel_at_period_end'):
        r=row(s,s.get('canceled_at') or s['created'])
        r['ends']=fmt(s['items']['data'][0].get('current_period_end') or s.get('cancel_at') or nowts)
        leaving.append(r)
leaving.sort(key=lambda x:-x['mrr'])
pastdue=[]
for s in subs:
    if s['status']=='past_due':
        n,e=who(s['customer']); t=tier(s)
        mine=[i for i in openinv if i['sub']==s['id']] or [i for i in openinv if i['cust']==s['customer']]
        oldest=min([i['created'] for i in mine], default=None)
        nv,nc=native_of(s)
        pastdue.append({'name':n,'email':e,'tier':t,'group':group(t),'mrr':round(mrr_of(s),2),'amt':nv,'cur':nc,
            'owed':round(sum(i['amt'] for i in mine)/100,2),'owed_cur':(mine[0]['cur_code'] if mine and mine[0].get('cur_code') else nc),'days':int((nowts-oldest)/86400) if oldest else 0,
            'url':mine[0]['url'] if mine else ''})
pastdue.sort(key=lambda x:-x['days'])
dead=[i for i in openinv if (subix.get(i['sub']) or {}).get('status')!='past_due']
stalled=sum(1 for s in subs if s['status']=='incomplete_expired')

# ---- manual / cash members ----
manual=[]; mpath='manual_members.csv'
if os.path.exists(mpath):
    lines=[l for l in open(mpath) if l.strip() and not l.lstrip().startswith('#')]
    for r in csv.DictReader(io.StringIO(''.join(lines))):
        nm=(r.get('name') or '').strip()
        if not nm or nm.lower().startswith('example'): continue
        try: amt=float(r.get('amount') or 0)
        except ValueError: amt=0.0
        iv=(r.get('interval') or 'month').strip().lower()
        m = amt/12 if iv.startswith('year') else (0.0 if iv.startswith('one') else amt)
        cur=(r.get('currency') or 'cad').strip().lower()
        manual.append({'name':nm,'tier':(r.get('tier') or 'Other').strip(),'amount':amt,'cur':cur,
                       'interval':iv,'mrr':round(to_base(m,cur),2),'note':(r.get('note') or '').strip()})
manual.sort(key=lambda x:-x['mrr'])
manual_mrr=round(sum(m['mrr'] for m in manual),2)
manual_usd=round(sum(m['amount']/(12 if m['interval'].startswith('year') else 1) for m in manual if m['cur']=='usd' and not m['interval'].startswith('one')),2)
manual_cad=round(sum(m['amount']/(12 if m['interval'].startswith('year') else 1) for m in manual if m['cur']!='usd' and not m['interval'].startswith('one')),2)

# ---- trend by the four groups, split by billing currency ----
def subcur(s): return s['items']['data'][0]['price']['currency']
first_ts=min(s['created'] for s in subs)
jan1=datetime.datetime(now.year,1,1,tzinfo=datetime.timezone.utc).timestamp()
WINDOWS={
 '7':   {'label':'7 days',   'start': nowts-7*86400},
 '30':  {'label':'30 days',  'start': nowts-30*86400},
 '90':  {'label':'90 days',  'start': nowts-90*86400},
 'ytd': {'label':'This year','start': jan1},
 # start a day before the very first signup so the chart truly begins at zero
 'all': {'label':'All time', 'start': first_ts-86400},
}
def build_trend(pred, start_ts, npoints=120):
    span=max(nowts-start_ts, 86400)
    step=span/(npoints-1)
    out=[]
    for i in range(npoints):
        ts=start_ts+step*i
        d=datetime.datetime.fromtimestamp(ts,datetime.timezone.utc)
        pt={'d':d.strftime('%Y-%m-%d')}
        for g in GROUPS:
            pt[g]=sum(1 for s in subs if s['status']!='incomplete_expired' and s['created']<=ts
                      and not (s.get('ended_at') and s['ended_at']<=ts)
                      and group(tier(s))==g and pred(s))
        pt['Total']=sum(pt[g] for g in GROUPS); out.append(pt)
    return out
trends={}
for k,w in WINDOWS.items():
    trends[k]={'label':w['label'],'start':w['start'],
               'usd':build_trend(lambda s: subcur(s)=='usd', w['start']),
               'cad':build_trend(lambda s: subcur(s)=='cad', w['start'])}

grp=collections.defaultdict(lambda: collections.Counter()); gmrr=collections.Counter()
gusd=collections.Counter(); gcad=collections.Counter()
for t in tierlist:
    g=t['group']
    for k in ('active','past_due','leaving','canceled','usd_n','cad_n'): grp[g][k]+=t[k]
    gusd[g]+=t['usd']; gcad[g]+=t['cad']
    gmrr[g]+=t['mrr']
groups=[{'group':g,'active':grp[g]['active'],'past_due':grp[g]['past_due'],'leaving':grp[g]['leaving'],
         'canceled':grp[g]['canceled'],'mrr':round(gmrr[g],2),
         'usd':round(gusd[g],2),'cad':round(gcad[g],2),
         'usd_n':grp[g]['usd_n'],'cad_n':grp[g]['cad_n']} for g in GROUPS]

out={'fx':FX,'generated': now.astimezone(datetime.timezone(datetime.timedelta(hours=-4))).strftime('%A, %B %-d · %-I:%M %p ET'),
 'groups_order':GROUPS,
 'totals':{'active':sum(t['active'] for t in tierlist),'past_due':sum(t['past_due'] for t in tierlist),
   'leaving':sum(t['leaving'] for t in tierlist),'mrr':round(sum(t['mrr'] for t in tierlist),2),
   'new30':sum(1 for j in joined if j['ts']>=nowts-30*86400),
   'churn30':sum(1 for c in churned if c['ts']>=nowts-30*86400),
   'now_ts':nowts,'owed':round(sum(i['owed'] for i in pastdue),2),
   'owed_usd':round(sum(i['owed'] for i in pastdue if i.get('owed_cur')=='usd'),2),
   'owed_cad':round(sum(i['owed'] for i in pastdue if i.get('owed_cur')!='usd'),2),
   'dead_owed':round(sum(i['amt'] for i in dead)/100,2),'dead_n':len(dead),'stalled':stalled,
   'usd_mrr':round(split['usd'],2),'cad_mrr':round(split['cad'],2),
   'usd_n':splitn['usd'],'cad_n':splitn['cad'],
   'mrr_usd_view':round(split['usd']+split['cad']/RATE,2),
   'manual_n':len(manual),'manual_mrr':manual_mrr,'manual_usd':manual_usd,'manual_cad':manual_cad},
 'groups':groups,'tiers':tierlist,'trends':trends,'windows':[{'key':k,'label':WINDOWS[k]['label'],'start':WINDOWS[k]['start']} for k in ('7','30','90','ytd','all')],'joined':joined,'churned':churned,
 'leaving':leaving,'past_due':pastdue,'manual':manual}
json.dump(out,open('dash.json','w'),indent=1)
t=out['totals']
print(json.dumps(t,indent=1))
print('CHECK: CAD-native %.2f + USD-native %.2f @ %.4f = %.2f CAD  (= %.2f USD)'%(
  t['cad_mrr'],t['usd_mrr'],RATE,t['mrr'],t['mrr_usd_view']))


import json as _j
d=json.load(open('dash.json'))
DATA=_j.dumps(d,separators=(',',':'))
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
.dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 3px color-mix(in srgb,var(--good) 22%,transparent)}

/* range toggle */
.rangebar{display:flex;align-items:center;gap:26px;flex-wrap:wrap;margin-top:-4px}
.rangebar--centre{justify-content:center;margin-top:-2px}
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
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <header>
    <div>
      <div class="eyebrow">Pick 6 Athletics &nbsp;·&nbsp; Lockdown Academy</div>
      <h1>Member Dashboard</h1>
    </div>
    <div class="stamp">
      <div class="live"><span class="dot"></span><span id="gen"></span></div>
      <div class="eyebrow" style="margin-top:4px">Live from Stripe · reconciled to Mighty</div>
    </div>
  </header>

  <div class="rangebar rangebar--centre" role="group" aria-label="History range">
    <div class="seg" id="range"></div>
  </div>

  <section class="kpis" id="kpis"></section>

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
    <div class="phead"><h2>By tier</h2><div class="note">Matches your Mighty plan counts · USD and CAD kept apart</div></div>
    <div class="scroll">
      <table>
        <thead><tr>
          <th>Tier</th><th class="n">Active</th><th class="n">Past due</th>
          <th class="n">Leaving</th><th class="n">Monthly USD</th><th class="n">Monthly CAD</th>
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

  <section class="panel">
    <div class="phead"><h2>Cash &amp; manual members</h2><div class="note" id="manualnote">From manual_members.csv</div></div>
    <ul class="people" id="manual"></ul>
  </section>

  <footer>
    <span id="footnote">Source: Stripe (Pick6athletics), read-only. "Leaving" = cancelled but still inside their paid term — what Mighty labels "Cancelled". <span id="fxnote"></span></span>
    <span class="mono" id="foot"></span>
  </footer>
</div>

<script>
const D = __DATA__;
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
const GROUPS = D.groups_order;

const T0_usd_n = D.totals.usd_n, T0_cad_n = D.totals.cad_n;
let RANGE = '90';                       // default view
let TIER  = 'all';                      // tier filter for the people lists
let ZOOM  = 1;                          // vertical zoom on the chart (pinch to change)
let PAN   = 0;                          // value at the bottom of the visible y range
let VIS   = {};                         // which series are drawn - click the legend
let VIEW  = {fullMax:1, yMax:1};        // last drawn scale, so pan can be clamped
const WIN = Object.fromEntries(D.windows.map(w=>[w.key,w]));
const winStart = () => WIN[RANGE].start;
const winLabel = () => WIN[RANGE].label;
const inWin = ts => ts >= winStart();
$('#gen').textContent = D.generated;
$('#foot').textContent = D.generated;
$('#fxnote').innerHTML = `USD and CAD are kept <b>separate</b> and never added together — ${T0_usd_n} subscriptions bill in USD, ${T0_cad_n} in CAD. If you want one combined figure, CA$${plain(D.totals.mrr)} / US$${plain(D.totals.mrr_usd_view)} at ${FX.usd_to_cad} CAD per USD (${FX.as_of}, ${FX.source}).`;

/* ---------- KPIs (recomputed per range) ---------- */
const T = D.totals;
function renderKPIs(){
  const pts = D.trends[RANGE].usd.map((p,i)=>p.Total + D.trends[RANGE].cad[i].Total);
  const delta = pts[pts.length-1] - pts[0];
  const nJoined  = D.joined.filter(p=>inWin(p.ts)).length;
  const nChurned = D.churned.filter(p=>inWin(p.ts)).length;
  const net = nJoined - nChurned;
  const arrow = n => n>0?'▲':n<0?'▼':'—';
  const cls   = n => n>0?'up':n<0?'down':'flat';
  const kpis = [
    {k:'Active members', v:T.active + T.manual_n,
     sub:`<span class="${cls(delta)}">${arrow(delta)} ${Math.abs(delta)} over ${winLabel().toLowerCase()}</span>${T.manual_n?`<span style="color:var(--ink-3)"> · incl. ${T.manual_n} cash</span>`:''}`},
    {k:'Monthly · USD', v:'US$'+plain(T.usd_mrr + T.manual_usd),
     sub:`<span class="money">${T.usd_n} subscriptions</span>`, small:true},
    {k:'Monthly · CAD', v:'CA$'+plain(T.cad_mrr + T.manual_cad),
     sub:`<span class="money">${T.cad_n} subscriptions</span>`, small:true},
    {k:'Joined · churned', small:(String(nJoined).length+String(nChurned).length)>4,
     v:`<span class="up">${nJoined}</span><span style="color:var(--ink-3)"> / </span><span class="down">${nChurned}</span>`,
     sub:`<span class="${cls(net)}">${net>0?'+':''}${net} net over ${winLabel().toLowerCase()}</span>`},
    {k:'Leaving at period end', v:T.leaving, sub:`<span class="money">Already cancelled, term not up</span>`},
    {k:'Past due', v:T.past_due, hot:T.past_due>0,
     sub:`<span class="${T.owed>0?'down':'flat'}">${[T.owed_usd?'US$'+T.owed_usd.toFixed(2):null, T.owed_cad?'CA$'+T.owed_cad.toFixed(2):null].filter(Boolean).join(' + ')||'nothing'} outstanding</span>`},
    {k:'Cash / manual', v:T.manual_n,
     sub:`<span class="money">${T.manual_n?[T.manual_usd?'US$'+plain(T.manual_usd):null,T.manual_cad?'CA$'+plain(T.manual_cad):null].filter(Boolean).join(' + ')+' a month':'Add them in manual_members.csv'}</span>`}
  ];
  $('#kpis').innerHTML = kpis.map(o=>`
    <div class="kpi">
      ${o.accent?`<span class="curstripe" style="background:${o.accent}"></span>`:''}
      <div class="eyebrow">${o.k}</div>
      <div class="num v"${o.small?' style="font-size:29px"':''}>${o.v}</div>
      <div class="sub">${o.sub}</div>
    </div>`).join('');
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
const maxOne=Math.max(...D.tiers.flatMap(t=>[t.usd,t.cad]));
const byGroup={}; D.tiers.forEach(t=>{(byGroup[t.group]=byGroup[t.group]||[]).push(t)});
$('#tbody').innerHTML = GROUPS.filter(g=>byGroup[g]).map(g=>{
 const G=D.groups.find(x=>x.group===g);
 const head=`<tr class="grouprow"><td><span class="tierName"><span class="rail" style="background:${BR[g]}"></span><b>${g}</b></span></td>
   <td class="n"><b>${G.active}</b></td><td class="n">${G.past_due?`<span class="pill bad">${G.past_due}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
   <td class="n">${G.leaving?`<span class="pill warn">${G.leaving}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
   <td class="n"><b>${G.usd?'US$'+plain(G.usd):'<span style="color:var(--ink-3);font-weight:400">—</span>'}</b></td>
   <td class="n"><b>${G.cad?'CA$'+plain(G.cad):'<span style="color:var(--ink-3);font-weight:400">—</span>'}</b></td></tr>`;
 return head + byGroup[g].map(t=>`
 <tr class="subrow">
  <td><span class="tierName" style="padding-left:16px;font-weight:400;color:var(--ink-2)">${esc(t.tier)}</span></td>
  <td class="n">${t.active}</td>
  <td class="n">${t.past_due? `<span class="pill bad">${t.past_due}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n">${t.leaving? `<span class="pill warn">${t.leaving}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n">${t.usd?`<span class="barwrap"><span class="bar" style="width:${Math.max(4,t.usd/maxOne*54)}px;background:var(--ink-3);opacity:.4"></span>US$${plain(t.usd)}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
  <td class="n">${t.cad?`<span class="barwrap"><span class="bar" style="width:${Math.max(4,t.cad/maxOne*54)}px;background:var(--ink-3);opacity:.4"></span>CA$${plain(t.cad)}</span>`:'<span style="color:var(--ink-3)">—</span>'}</td>
 </tr>`).join('');}).join('');
$('#tfoot').innerHTML = `<tr><td>All tiers</td><td class="n">${T.active}</td><td class="n">${T.past_due}</td>
  <td class="n">${T.leaving}</td>
  <td class="n">US$${plain(T.usd_mrr)}</td><td class="n">CA$${plain(T.cad_mrr)}</td></tr>`;

/* ---------- People lists ---------- */
function person(p, right){
  return `<li><span class="rail" style="background:${BR[p.group]}"></span>
    <span class="who"><span class="nm">${esc(p.name)}</span><br><span class="mt">${esc(p.tier)}</span></span>
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
   <span class="who"><span class="nm">${esc(p.name)}</span><br>
     <span class="mt down">${esc(p.tier)} · ${p.days} day${p.days===1?'':'s'} overdue${p.url?` · <a class="inv" href="${p.url}" target="_blank" rel="noopener">invoice</a>`:''}</span></span>
   <span class="amt down">${nat(p.owed,p.owed_cur||p.cur)}</span></li>`).join('')
  : `<div class="empty">${TIER==='all'?'Everyone is paid up.':'No '+TIER+' members are past due.'}</div>`;
$('#pdpanel').querySelector('.note').textContent = P.length ? 'Chase these' : 'All clear';
}

$('#manual').innerHTML = D.manual.length ? D.manual.map(p=>`
  <li><span class="rail" style="background:${BR[p.tier]||'var(--ink-3)'}"></span>
   <span class="who"><span class="nm">${esc(p.name)}</span><br>
     <span class="mt">${esc(p.tier)}${p.note?' · '+esc(p.note):''}</span></span>
   <span class="amt">${p.amount?nat(p.amount,p.cur||'cad')+'/'+p.interval.slice(0,2):'comped'}</span></li>`).join('')
  : `<div class="empty">No manual members yet. Add rows to <b>manual_members.csv</b> in your Brainstorming folder — name, tier, amount, interval, note — and they'll appear here on the next refresh. Mighty shows 7 in <i>Pick 6 Elite group</i> and 3 <i>Manual member - free</i>; those are the ones to list.</div>`;
if(D.manual.length) $('#manualnote').textContent = `${D.manual.length} people`;

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
  try{ localStorage.setItem('p6range', RANGE); }catch(_){}
  redraw();
});
try{ const saved=localStorage.getItem('p6range'); if(saved && WIN[saved]) RANGE=saved; }catch(_){}
redraw();
</script>'''
open(os.path.join(DIR,'roster-board.html'),'w').write(HTML.replace('__DATA__', DATA))
print('wrote roster-board.html')
