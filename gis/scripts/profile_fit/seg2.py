import sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
import os
FR=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))+'/research/frames/JWNowpO44rw/JWNowpO44rw_%s.jpg'
ROI={'000641.633':(420,150,1000,390),'000659.633':(150,0,1030,330),'001221.500':(100,40,1280,700),'001224.500':(90,40,1280,690),
     '001232.600':(40,200,1160,720),'001235.934':(140,210,1080,670),'001239.267':(120,150,1110,630),'001244.833':(180,240,850,550),'001247.833':(20,140,1070,540)}
VT={'001244.833':0.34}
# Base leaks (light murram and site ground joined to the wall): areas outside the visible wall edge, read by hand
# on the frames (1280 x 720 px), removed from the mask before the largest-component step.
EXCLUDE={'001221.500':[[(0,200),(117,227),(115,347),(133,453),(180,547),(220,613),(280,693),(0,720)],
                       [(1280,520),(1233,587),(1173,640),(1133,673),(1280,720)]],
         '001224.500':[[(0,213),(120,240),(117,347),(144,440),(197,533),(247,607),(313,667),(0,720)],
                       [(1280,560),(1247,600),(1200,640),(1280,720)]]}
def segment(name):
    im=np.asarray(Image.open(FR%name).convert('RGB')).astype(float)/255
    mx=im.max(2); mn=im.min(2); s=(mx-mn)/np.maximum(mx,1e-6); r,g,b=im[...,0],im[...,1],im[...,2]
    x0,y0,x1,y1=ROI[name]; roi=np.zeros(mx.shape,bool); roi[y0:y1,x0:x1]=True
    white=(mx>VT.get(name,0.40))&(s<0.22)&((r-b)<0.045)
    red=(r>0.30)&(r>1.5*g)&(r>1.3*b)&(s>0.4)
    m=(white|red)&roi
    if name in EXCLUDE:
        ex=Image.new('1',(mx.shape[1],mx.shape[0]))
        for poly in EXCLUDE[name]: ImageDraw.Draw(ex).polygon(poly,fill=1)
        roi&=~np.asarray(ex); m&=roi
    m=nd.binary_opening(m,iterations=1)
    lab,n=nd.label(m); sizes=nd.sum(m,lab,range(1,n+1)); m=lab==(1+int(np.argmax(sizes)))
    m=nd.binary_closing(m,iterations=8); m=nd.binary_fill_holes(m); m&=roi
    m=nd.binary_opening(m,iterations=5)
    lab,n=nd.label(m); sizes=nd.sum(m,lab,range(1,n+1)); m=lab==(1+int(np.argmax(sizes)))
    # opening: dark region enclosed by the stadium
    dark=(mx<0.42)&m
    dark=nd.binary_opening(dark,iterations=3)
    lab,n=nd.label(dark); op=None
    if n:
        sizes=nd.sum(dark,lab,range(1,n+1)); k=1+int(np.argmax(sizes))
        if sizes[k-1]>800: op=nd.binary_fill_holes(nd.binary_closing(lab==k,iterations=4))
    return (im*255).astype(np.uint8), m, op
if __name__=='__main__':
    tiles=[]; info={}
    for f in ROI:
        im,m,op=segment(f); np.save(f'{sys.argv[1]}/mask_{f}.npy',m); 
        if op is not None: np.save(f'{sys.argv[1]}/open_{f}.npy',op)
        info[f]={'mask_px':int(m.sum()),'open_px':int(op.sum()) if op is not None else 0}
        o=im.copy(); e=m^nd.binary_erosion(m,iterations=2); o[e]=[0,255,255]
        if op is not None: e2=op^nd.binary_erosion(op,iterations=2); o[e2]=[255,255,0]
        t=Image.fromarray(o).resize((640,360)); ImageDraw.Draw(t).text((5,5),f,fill='yellow'); tiles.append(t)
    sh=Image.new('RGB',(1920,1080))
    for k,t in enumerate(tiles): sh.paste(t,((k%3)*640,(k//3)*360))
    sh.save(sys.argv[1]+'/seg.jpg',quality=80); print(json.dumps(info))
