/* Original procedural concept geometry, not surveyed stadium geometry. */
const canvas = document.querySelector('#stadium');
const ctx = canvas.getContext('2d');
let width=0,height=0,angle=-0.38,mode='night',dragging=false,lastX=0;
const TAU=Math.PI*2;
function point(x,y,z){const c=Math.cos(angle),s=Math.sin(angle),a=x*c-y*s,b=x*s+y*c,scale=Math.min(width/800,height/520);return [width*.51+a*scale,height*.53+(b*.49-z*.96)*scale];}
function line(points,color,w=1,closed=false){ctx.beginPath();points.forEach((p,i)=>{const q=point(...p);i?ctx.lineTo(...q):ctx.moveTo(...q)});if(closed)ctx.closePath();ctx.strokeStyle=color;ctx.lineWidth=w;ctx.stroke();}
function poly(points,fill,stroke){ctx.beginPath();points.forEach((p,i)=>{const q=point(...p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.closePath();ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=.6;ctx.stroke();}}
function ring(rx,ry,z,color,w=1){const p=[];for(let i=0;i<=120;i++){let a=i/120*TAU;p.push([Math.cos(a)*rx,Math.sin(a)*ry,z])}line(p,color,w)}
function at(a,rx,ry,z){return [Math.cos(a)*rx,Math.sin(a)*ry,z]}
function render(){ctx.clearRect(0,0,width,height);const day=mode==='day',event=mode==='event';
// Architectural ground grid.
for(let i=-600;i<=600;i+=45){line([[i,-500,-7],[i,500,-7]],'#36516a22',.6);line([[-600,i,-7],[600,i,-7]],'#36516a22',.6)}
ring(370,265,-4,'#4b759244',.7);ring(350,250,-4,'#618fab33',.7);
// Site perimeter, intentionally abstract and without route or gate information.
for(let r=0;r<3;r++)ring(310+r*9,216+r*7,-2,'#63849c29',.8);
// Building walls sorted back-to-front for correct occlusion.
const facets=[];for(let i=0;i<96;i++){let a=i/96*TAU,b=(i+1)/96*TAU;facets.push({a,b,depth:Math.sin((a+b)/2+angle)})}facets.sort((a,b)=>a.depth-b.depth);
facets.forEach(({a,b,depth})=>{poly([at(a,275,185,0),at(b,275,185,0),at(b,287,195,65),at(a,287,195,65)],day?'#506a7a':'#162e42','#496a7e');for(let z=8;z<60;z+=9)line([at(a,277+z*.16,187+z*.13,z),at(b,277+z*.16,187+z*.13,z)],day?'#819aa5':'#426379',.5);line([at(a,275,185,0),at(b,287,195,65)],'#a0bbc878',.7);if(depth>.1&&Math.floor(a*15)%8<2)poly([at(a,279,188,10),at(b,279,188,10),at(b,285,193,54),at(a,285,193,54)],Math.floor(a*15)%16<8?'#843e4e':'#214d4b')});
// Bowl and colored seating tiers.
poly(Array.from({length:120},(_,i)=>at(i/120*TAU,246,161,64)),day?'#283d4b':'#06131f');
for(let tier=0;tier<15;tier++){let t=tier/14,rx=153+t*92,ry=92+t*67,z=7+t*55;ring(rx,ry,z,tier<6?(day?'#477c6e':'#286957'):tier<11?(day?'#9f595c':'#914454'):'#4b5664',2.5);}
for(let i=0;i<64;i++){let a=i/64*TAU;line([at(a,153,92,7),at(a,245,159,62)],'#b0c8d13b',.7)}
// Playing field.
poly([[-130,-77,5],[130,-77,5],[130,77,5],[-130,77,5]],day?'#436e60':'#1d5149','#8ac9b3');
for(let i=0;i<12;i++)if(i%2===0)poly([[-130+i*260/12,-77,5],[-130+(i+1)*260/12,-77,5],[-130+(i+1)*260/12,77,5],[-130+i*260/12,77,5]],'#b3e9c909');
const field='#b6e9d9a0';line([[-124,-71,5],[124,-71,5],[124,71,5],[-124,71,5]],field,.8,true);line([[0,-71,5],[0,71,5]],field,.8);ring(21,21,5,field,.8);for(const sign of [-1,1]){line([[sign*124,-32,5],[sign*88,-32,5],[sign*88,32,5],[sign*124,32,5]],field,.8);line([[sign*124,-15,5],[sign*112,-15,5],[sign*112,15,5],[sign*124,15,5]],field,.8);line([[sign*127,-8,5],[sign*127,-8,12],[sign*127,8,12],[sign*127,8,5]],'#daedf0',1)}
// Roof radial canopy: original, stylized structure.
for(let i=0;i<96;i++){const a=i/96*TAU,b=(i+1)/96*TAU;poly([at(a,295,202,78),at(b,295,202,78),at(b,220,140,84),at(a,220,140,84)],day?(i%2?'#9baeb9':'#bcc8cf'):(i%2?'#355268':'#47667c'),'#a4c5d360');line([at(a,295,202,78),at(a,220,140,84)],day?'#dde8edaa':'#8cb6cb99',.7);if(i%4===0)line([at(a,295,202,78),at(b,220,140,84)],'#8ab0c26b',.6)}
ring(295,202,78,day?'#d2e4ec':'#a3c8da',1.4);ring(220,140,84,'#badceb',1.4);ring(299,205,74,'#75abc270',1);
// Perimeter lighting, without a real infrastructure layout.
if(!day){ctx.save();ctx.shadowBlur=event?15:9;ctx.shadowColor=event?'#d5a1ff':'#b3e5ff';ring(222,142,82,event?'#c5a5f4':'#c8f1ff',1.9);ring(295,202,76,event?'#9e83df':'#84c8ef',1.3);ctx.restore();}
if(event){poly([[-85,-52,8],[-36,-52,8],[-36,52,8],[-85,52,8]],'#242a49','#9c9ed5');poly([[-85,-52,8],[-85,-52,43],[-85,52,43],[-85,52,8]],'#7277b1','#d6d9ff');for(let i=-2;i<=2;i++){line([[-82,i*20,43],[-30+i*13,i*29,140]],'#c1bbf350',1.5)}for(let x=-8;x<90;x+=7)for(let y=-48;y<50;y+=7){let p=point(x,y,7);ctx.fillStyle=(x+y)%3?'#87bcdb':'#d0a3c6';ctx.fillRect(p[0],p[1],1.2,1.2)}}
// Coordinate-style corner marks.
ctx.strokeStyle='#5a849650';ctx.lineWidth=1;const marks=[[width*.19,height*.26],[width*.84,height*.72]];for(const [x,y]of marks){ctx.beginPath();ctx.moveTo(x-8,y);ctx.lineTo(x+8,y);ctx.moveTo(x,y-8);ctx.lineTo(x,y+8);ctx.stroke();}
}
function resize(){let r=canvas.getBoundingClientRect();width=r.width;height=r.height;const dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);render()}
new ResizeObserver(resize).observe(canvas);
canvas.addEventListener('pointerdown',e=>{if(e.pointerType==='touch')return;dragging=true;lastX=e.clientX;canvas.setPointerCapture(e.pointerId)});
canvas.addEventListener('pointermove',e=>{if(dragging){angle+=(e.clientX-lastX)*.005;lastX=e.clientX;render()}});
for(const type of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(type,()=>dragging=false);
canvas.tabIndex=0;canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Concept stadium illustration. Use left and right arrow keys to rotate. Geometry is illustrative.');canvas.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();angle+=e.key==='ArrowLeft'?-.1:.1;render()}});
window.setSceneMode=value=>{mode=value;render()};
