"""e-metanolisolmun tuotantokustannus (LCOM) FI day-ahead -hinnoilla.

Elektrolyysi ajaa vain vartteina, joina hinta <= kynnys P*. Oletukset [A]
alla; hintadata: tools/frg_hinnat.py -> data/fi_dayahead.json (ei committata).
Claude Opus 5.5, 23.11.2026. Katselmoitava (katselmoinnit/frg-irr-ketju-pyynto.txt).
"""
import json, statistics as st
from datetime import datetime
P=json.load(open("data/fi_dayahead.json"))
ts=sorted(P); prices=[P[t] for t in ts if P[t] is not None]
N=len(prices); hours_total=N/4
# --- assumptions [A] ---
EL_MW=50; KWH_PER_KG=55.0
H2_T_PER_T=0.199; CO2_T_PER_T=1.46; AUX_MWH_PER_T=0.35
GRID_TAX=8.0          # €/MWh grid fee + electricity tax class II
CO2_COST=80.0         # €/t captured biogenic CO2
CAPEX_EL=1900*EL_MW*1000
CAPEX_SYN=45e6; CAPEX_BUF=5e6
CAPEX=CAPEX_EL+CAPEX_SYN+CAPEX_BUF
WACC=0.07; LIFE=20
CRF=WACC*(1+WACC)**LIFE/((1+WACC)**LIFE-1)
FOM=0.03*CAPEX
HEAT_FRAC=0.22; HEAT_PRICE=20.0
def run(th):
    sel=[p for p in prices if p<=th]
    mwh=len(sel)*EL_MW/4
    if mwh==0: return None
    avgp=sum(sel)/len(sel)
    h2_t=mwh*1000/KWH_PER_KG/1000
    meoh=h2_t/H2_T_PER_T
    elec=mwh*(avgp+GRID_TAX)+meoh*AUX_MWH_PER_T*(avgp+GRID_TAX)
    co2=meoh*CO2_T_PER_T*CO2_COST
    heat=-mwh*HEAT_FRAC*HEAT_PRICE
    ann=CAPEX*CRF+FOM
    tot=ann+elec+co2+heat
    return dict(th=th,h=len(sel)/4,cf=len(sel)/N,avgp=avgp,meoh_kt=meoh/1000,
        capex_t=ann/meoh,elec_t=elec/meoh,co2_t=co2/meoh,heat_t=heat/meoh,lcom=tot/meoh)
print(f"data: {ts[0]} .. {ts[-1]}  n={N} ({hours_total:.0f} h)  mean {st.mean(prices):.1f} median {st.median(prices):.1f} min {min(prices)} max {max(prices)}")
print(f"CAPEX {CAPEX/1e6:.0f} M€, annuity {CAPEX*CRF/1e6:.1f} + FOM {FOM/1e6:.1f} M€/a")
rows=[run(t) for t in [0,10,20,25,27,30,40,50,60,80,100,150,1e9]]
print(f"{'P*':>6} {'h':>6} {'CF':>5} {'avgP':>6} {'kt':>5} {'capex':>6} {'elec':>6} {'co2':>5} {'heat':>5} {'LCOM':>6}")
for r in rows:
    if r: print(f"{r['th'] if r['th']<1e8 else 'all':>6} {r['h']:6.0f} {r['cf']:5.2f} {r['avgp']:6.1f} {r['meoh_kt']:5.1f} {r['capex_t']:6.0f} {r['elec_t']:6.0f} {r['co2_t']:5.0f} {r['heat_t']:5.0f} {r['lcom']:6.0f}")
best=min((run(t) for t in range(1,300)), key=lambda r:r['lcom'])
print("optimum:",{k:round(v,2) for k,v in best.items()})
json.dump([r for r in rows if r],open("data/results.json","w"),indent=1)
