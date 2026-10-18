import sys, json, time, numpy as np, model as m
from scipy.optimize import differential_evolution, minimize
from solve_cams import load, loss, iou, SHP
from PIL import Image, ImageDraw
S=sys.argv[1]; ROUNDS=int(sys.argv[2]) if len(sys.argv)>2 else 3
KEYS=['yW','Rh','Rv','openY','sag','dF','bulge','hs']
PB=[(30,56),(1,40),(1,20),(35,60),(-3,6),(-4,15),(-4,6),(18,36)]
def P(x): p=dict(m.CUR); p.update(dict(zip(KEYS,map(float,x)))); return p
def total(x,cams,data,pen=True):
    p=P(x); l=sum(loss(np.array(cams[f]),p,*data[f],0.5,f) for f in cams)/len(cams)
    if pen and p['yW']+p['Rv']>58: l+=0.05*(p['yW']+p['Rv']-58)  # press: max height 56 m (+-2)
    return l
def overlay(p,cams,tag):
    tiles=[]
    for f,c in cams.items():
        im=Image.open(m.ROOT+f'research/frames/JWNowpO44rw/JWNowpO44rw_{f}.jpg').convert('RGB'); d=ImageDraw.Draw(im)
        P3=m.shell(p); uv,_=m.project(P3,c)
        from scipy.spatial import ConvexHull
        h=ConvexHull(uv); d.line([tuple(uv[i]) for i in list(h.vertices)+[h.vertices[0]]],fill=(0,255,255),width=3)
        nw=10; ns=10
        for j,col in ((nw,(255,0,255)),(nw+ns,(255,255,0))):  # wall top / crest rings
            u,_=m.project(P3[:,j,:],c); d.line([tuple(x) for x in np.vstack([u,u[:1]])],fill=col,width=2)
        u,_=m.project(m.opening(p),c); d.line([tuple(x) for x in np.vstack([u,u[:1]])],fill=(0,255,0),width=2)
        for u in m.shield_uv(p,c): d.ellipse((u[0]-10,u[1]-10,u[0]+10,u[1]+10),outline=(255,0,0),width=4)
        for u in SHP.get(f,[]): d.ellipse((u[0]-6,u[1]-6,u[0]+6,u[1]+6),fill=(0,255,0))
        im=im.resize((640,360)); ImageDraw.Draw(im).text((5,5),f,fill='yellow'); tiles.append(im)
    sh=Image.new('RGB',(1920,360*((len(tiles)+2)//3)))
    for k,t in enumerate(tiles): sh.paste(t,((k%3)*640,(k//3)*360))
    sh.save(f'{S}/overlay_{tag}.jpg',quality=82)
if __name__=='__main__':
    cams={f:np.array(v['cam']) for f,v in json.load(open(f'{S}/cams.json')).items()}
    data={f:load(f) for f in cams}
    x=np.array([m.CUR.get(k,28.75) if m.CUR.get(k,28.75) is not None else 1.0 for k in KEYS])
    x[KEYS.index('dF')]=float(np.mean(m.rRo-np.minimum(m.rPl+1,m.rRo)))
    print('start', round(total(x,cams,data),4), flush=True); overlay(P(x),cams,'before')
    for rd in range(ROUNDS):
        t=time.time()
        r=differential_evolution(total,PB,args=(cams,data),x0=x,popsize=10,maxiter=50,tol=1e-5,seed=rd,polish=False)
        x=r.x
        for f in cams:
            r2=minimize(loss,cams[f],args=(P(x),*data[f],0.5,f),method='Nelder-Mead',options=dict(maxiter=800,xatol=1e-3,fatol=1e-6)); cams[f]=r2.x
        print('round',rd,round(total(x,cams,data),4),{k:round(v,2) for k,v in zip(KEYS,x)},round(time.time()-t),'s',flush=True)
    json.dump(dict(profile=dict(zip(KEYS,map(float,x))),cams={f:list(map(float,c)) for f,c in cams.items()},
                   per_frame={f:dict(sil_iou=float(iou(m.sil(P(x),cams[f]),data[f][0]))) for f in cams}),open(f'{S}/fit.json','w'),indent=1)
    overlay(P(x),cams,'after')
