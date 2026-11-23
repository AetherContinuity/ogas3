import json, time, urllib.request, sys
from datetime import datetime, timedelta, timezone
BASE="https://aci-entsoe-proxy.ruotsalainen-marko.workers.dev/day-ahead-price"
months=[]
d=datetime(2025,11,1,tzinfo=timezone.utc)
while d<datetime(2026,11,1,tzinfo=timezone.utc):
    n=(d.replace(day=28)+timedelta(days=4)).replace(day=1)
    months.append((d,n)); d=n
out={}
for a,b in months:
    url=f"{BASE}?bzn=FI&periodStart={a:%Y-%m-%dT%H:%MZ}&periodEnd={b:%Y-%m-%dT%H:%MZ}"
    for att in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl/8.0"}),timeout=120)
            j=json.load(r); break
        except Exception as e:
            print("retry",a,e,file=sys.stderr); time.sleep(6*(att+1))
    else: raise SystemExit("fail")
    if "error" in j: raise SystemExit(f"{a}: {j}")
    for s in j["series"]:
        pts=sorted(s["points"],key=lambda p:p["position"])
        res=pts[0]["resolution"]; step=15 if res=="PT15M" else 60
        ps=datetime.fromisoformat(pts[0]["periodStart"].replace("Z","+00:00"))
        # fill A03 compressed positions
        maxpos=None
        bypos={p["position"]:p["quantity"] for p in pts}
        # determine period length: assume day (96 or 24)
        n = 96 if step==15 else 24
        last=None
        for pos in range(1,n+1):
            if pos in bypos: last=bypos[pos]
            t=ps+timedelta(minutes=step*(pos-1))
            out[t.isoformat()]=last
    print(a.date(),len(out),file=sys.stderr)
    time.sleep(3)
json.dump(out,open("data/fi_dayahead.json","w"))
