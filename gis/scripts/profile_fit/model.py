import csv, math, numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull
import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))+'/'
N=120
def outline(fn): return np.array([(float(r['x_east']),float(r['z_south'])) for r in csv.DictReader(open(ROOT+'gis/measurements/normalized/'+fn))])
def ray_radius(ring,ux,uz):
    a=ring; b=np.roll(ring,-1,0); e=b-a
    den=ux*e[:,1]-uz*e[:,0]; ok=np.abs(den)>1e-12
    t=(a[:,0]*e[:,1]-a[:,1]*e[:,0])/np.where(ok,den,1); s=(a[:,0]*uz-a[:,1]*ux)/np.where(ok,den,1)
    v=ok&(t>0)&(s>=-1e-9)&(s<=1+1e-9); return t[v].max() if v.any() else 0
def smooth(r,k=2): return np.mean([np.roll(r,j) for j in range(-k,k+1)],0)
ang=2*np.pi*np.arange(N)/N; DX,DZ=np.cos(ang),np.sin(ang)
rPl=smooth(np.array([ray_radius(outline('bowl_plinth_design_2026-10-17.csv'),x,z) for x,z in zip(DX,DZ)]))
rRo0=smooth(np.array([ray_radius(outline('bowl_roof_outer_design_2026-10-17.csv'),x,z) for x,z in zip(DX,DZ)]))
rRo=smooth(np.maximum(rRo0,rPl-4.0),6)
rRi=smooth(np.array([ray_radius(outline('bowl_roof_inner_design_2026-10-17.csv'),x,z) for x,z in zip(DX,DZ)]))
# profile params: yW wall top, Rh, Rv shoulder radii, openY, sag, dF foot inset (rRo - r0), bulge, yFoot
CUR=dict(yW=51.0,Rh=3.0,Rv=3.0,openY=50.0,sag=1.5,dF=None,bulge=0.0,yFoot=6.0)
def shell(p, nw=10, ns=10, nr=8):
    """Outer shell points (N x K x 3) in app frame (x east, y up, z south), y above pad."""
    yW,Rh,Rv,openY,sag,bulge,yF=p['yW'],p['Rh'],p['Rv'],p['openY'],p['sag'],p['bulge'],p['yFoot']
    r0=rRo-p['dF'] if p['dF'] is not None else np.minimum(rPl+1.0,rRo)
    rows=[]
    for k in range(nw+1):
        f=k/nw; rows.append((r0+(rRo-r0)*f+bulge*math.sin(math.pi*f), np.full(N,yF+(yW-yF)*f)))
    for k in range(1,ns+1):
        a=k/ns*math.pi/2; rows.append((rRo-Rh*(1-math.cos(a)), np.full(N,yW+Rv*math.sin(a))))
    rc=rRo-Rh; top=yW+Rv
    for k in range(1,nr+1):
        t=k/nr; rows.append((rc+(rRi-rc)*t, np.full(N,top+(openY-top)*t-sag*math.sin(t*math.pi))))
    R=np.stack([r for r,_ in rows],1); Y=np.stack([y for _,y in rows],1)
    return np.stack([DX[:,None]*R, Y, DZ[:,None]*R],-1)
def opening(p):
    return np.stack([DX*rRi, np.full(N,p['openY']), DZ*rRi],-1)
def cam_matrix(c):
    """c: tx,ty,tz, az(deg, from +x toward +z), el(deg), dist, f(px), roll(deg) -> (R, C, f)."""
    tx,ty,tz,az,el,d,f,roll=c
    az,el,roll=map(math.radians,(az,el,roll))
    fwd=-np.array([math.cos(el)*math.cos(az), math.sin(el), math.cos(el)*math.sin(az)])  # camera looks toward target
    C=np.array([tx,ty,tz])-fwd*d
    right=np.cross(fwd,[0,1,0]); right/=np.linalg.norm(right); up=np.cross(right,fwd)
    cr,sr=math.cos(roll),math.sin(roll); right,up=cr*right+sr*up, -sr*right+cr*up
    return np.stack([right,-up,fwd]),C,f
W,H=1280,720; SC=4  # raster at 1/4
def project(P,cam):
    R,C,f=cam_matrix(cam); q=(P.reshape(-1,3)-C)@R.T
    z=np.maximum(q[:,2],1e-3); return np.stack([f*q[:,0]/z+W/2, f*q[:,1]/z+H/2],1), q[:,2]
def raster(poly):
    im=Image.new('1',(W//SC,H//SC)); ImageDraw.Draw(im).polygon([tuple(x) for x in (poly/SC)],fill=1); return np.asarray(im)
def sil(p,cam):
    uv,z=project(shell(p),cam)
    if (z<1).any(): return None
    h=ConvexHull(uv); return raster(uv[h.vertices])
def open_poly(p,cam):
    uv,z=project(opening(p),cam); return raster(uv)

SH_TH=np.radians(-1.76-90+45*np.arange(8))
def wall_r(p,th,y):
    i=(np.round(th/(2*np.pi)*N).astype(int))%N
    r0=rRo[i]-p['dF'] if p['dF'] is not None else np.minimum(rPl[i]+1.0,rRo[i])
    f=np.clip((y-p['yFoot'])/(p['yW']-p['yFoot']),0,1)
    return r0+(rRo[i]-r0)*f+p['bulge']*np.sin(np.pi*f)
def shield_centres(p):
    y=p.get('hs',28.75); r=wall_r(p,SH_TH,y)+2.6
    return np.stack([np.cos(SH_TH)*r,np.full(8,y),np.sin(SH_TH)*r],-1)
def shield_uv(p,cam):
    P=shield_centres(p); uv,z=project(P,cam)
    R,C,f=cam_matrix(cam); nrm=np.stack([np.cos(SH_TH),np.zeros(8),np.sin(SH_TH)],-1)
    vis=((C-P)*nrm).sum(1)/np.linalg.norm(C-P,axis=1)>0.25
    return uv[vis]
