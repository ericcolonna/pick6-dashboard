import json, datetime
subs=json.load(open('all.json')); cmap=json.load(open('cmap.json'))
inv=json.load(open('open_slim.json')); prod=json.load(open('prodmap.json')); fx=json.load(open('fx.json'))
try:    ctry=json.load(open('countries.json'))     # customer id -> ISO alpha-2
except FileNotFoundError: ctry={}

def compact(s):
    it=s['items']['data'][0]; pr=it['price']; r=pr['recurring']
    return {'i':s['id'],'c':s['customer'],'p':pr['product'],'u':pr['currency'],
            'a':pr.get('unit_amount') or 0,'iv':r['interval'],'ic':r.get('interval_count',1),
            'q':it.get('quantity',1),'cr':s['created'],'en':s.get('ended_at') or 0,
            'ce':1 if s.get('cancel_at_period_end') else 0,
            'pe':it.get('current_period_end') or s.get('cancel_at') or 0,'s':s['status']}
H=[compact(s) for s in subs]
# names only for customers we could ever show
N={k:[v['name'],v['email']] for k,v in cmap.items()}
INV=[{'s':i['sub'],'c':i['cust'],'a':i['amt'],'u':i['cur_code'],'t':i['created'],'url':i['url']} for i in inv]
C={k:v for k,v in ctry.items() if k in cmap}      # only customers we can show
bake={'H':H,'N':N,'P':prod,'FX':fx,'INV':INV,'C':C,
      'stamp':datetime.datetime.now(datetime.timezone.utc).timestamp()}
json.dump(bake,open('bake.json','w'),separators=(',',':'))
import os
print('subs',len(H),'names',len(N),'invoices',len(INV),'countries',len(C),
      'size KB',round(os.path.getsize('bake.json')/1024))
