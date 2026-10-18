import sys, json, time, numpy as np, model as m
from scipy.optimize import differential_evolution, minimize
S=sys.argv[1]; FR=sys.argv[2:] 
def down(a): return a.reshape(m.H//m.SC,m.SC,m.W//m.SC,m.SC).mean((1,3))>0.5
def load(f):
    M=down(np.load(f'{S}/mask_{f}.npy'))
    try: O=down(np.load(f'{S}/open_{f}.npy'))
    except FileNotFoundError: O=None
    if O is not None and O.sum()*m.SC*m.SC<6000: O=None
    return M,O
def iou(a,b): u=(a|b).sum(); return (a&b).sum()/u if u else 0
import json as _j, os as _o
SHP=_j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'shield_pts.json')))
def loss(cam,p,M,O,wo=0.5,f=None):
    try: s=m.sil(p,cam)
    except Exception: return 2.0
    if s is None: return 2.0
    l=1-iou(s,M)
    if O is not None and wo: l+=wo*(1-iou(m.open_poly(p,cam),O))
    if f in SHP:
        uv=m.shield_uv(p,cam); pts=np.array(SHP[f],float)
        if len(uv)==0: l+=1.0
        else:
            d=np.linalg.norm(pts[:,None,:]-uv[None],axis=2).min(1); l+=np.mean(np.minimum(d/80.0,1.5)**2)
    return l
B=[(-80,80),(0,60),(-80,80),(0,360),(3,75),(80,1600),(400,3200),(-15,15)]
if __name__=='__main__':
    p=dict(m.CUR); out={}
    try: out=json.load(open(f'{S}/cams.json'))
    except Exception: pass
    for f in FR:
        t=time.time(); M,O=load(f)
        r=differential_evolution(loss,B,args=(p,M,O,0.5,f),popsize=14,maxiter=120,tol=1e-4,seed=1,polish=False)
        r2=minimize(loss,r.x,args=(p,M,O,0.5,f),method='Nelder-Mead',options=dict(maxiter=1500,xatol=1e-3,fatol=1e-5))
        x=r2.x if r2.fun<r.fun else r.x
        out[f]=dict(cam=list(map(float,x)),loss=float(min(r.fun,r2.fun)),sil_iou=float(iou(m.sil(p,x),M)))
        json.dump(out,open(f'{S}/cams.json','w'),indent=1)
        print(f, round(out[f]['loss'],4), round(out[f]['sil_iou'],4), [round(v,1) for v in x], round(time.time()-t,1),'s',flush=True)
