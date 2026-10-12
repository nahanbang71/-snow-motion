const W=1920,H=1080,LEN=16,FADE=.9;
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)|0;let t=Math.imul(a^(a>>>15),1|a);t=(t+Math.imul(t^(t>>>7),61|t))^t;return((t^(t>>>14))>>>0)/4294967296}}
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),lerp=(a,b,t)=>a+(b-a)*t,sm=t=>{t=clamp(t,0,1);return t*t*(3-2*t)};
const mix=(c1,c2,t)=>c1.map((v,i)=>Math.round(lerp(v,c2[i],t)));const rgb=c=>`rgb(${c[0]},${c[1]},${c[2]})`;
const sprites={};
function sprite(col){if(sprites[col])return sprites[col];const c=document.createElement('canvas');c.width=c.height=128;const g=c.getContext('2d');
 const gr=g.createRadialGradient(64,64,0,64,64,64);gr.addColorStop(0,`rgba(${col},1)`);gr.addColorStop(.16,`rgba(${col},.6)`);gr.addColorStop(.45,`rgba(${col},.14)`);gr.addColorStop(1,`rgba(${col},0)`);
 g.fillStyle=gr;g.fillRect(0,0,128,128);return sprites[col]=c}
function glow(x,y,r,col,a){ctx.globalAlpha=a;ctx.drawImage(sprite(col),x-r,y-r,2*r,2*r);ctx.globalAlpha=1}
// ---------------------------------------------------------------- sky projection (gnomonic)
const D2R=Math.PI/180;
function project(c,k,roll){const ra0=c.ra*D2R,d0=c.dec*D2R,s0=Math.sin(d0),c0=Math.cos(d0),cr=Math.cos(roll),sr=Math.sin(roll);
 return(ra,dec)=>{const r=ra*D2R,d=dec*D2R,cd=Math.cos(d),sd=Math.sin(d),dr=r-ra0,cosc=s0*sd+c0*cd*Math.cos(dr);if(cosc<=-.2)return null;
  const f=2/(1+cosc);let x=-cd*Math.sin(dr)*f,y=(c0*sd-s0*cd*Math.cos(dr))*f;const rx=x*cr-y*sr,ry=x*sr+y*cr;return[W/2+rx*k,H*.40-ry*k]}}
function bvColor(bv){return bv<.0?'175,200,255':bv<.35?'215,228,255':bv<.8?'255,250,240':bv<1.2?'255,225,180':'255,190,150'}
function prepScene(ci,roll){const c=SKY.cons[ci];let k=(H*.17)/(2*Math.tan(Math.max(c.rad,.05)/2));k=clamp(k,430,1150);const P=project(c,k,roll);
 const stars=[];const r=rng(500+ci);for(const[ra,dec,mag,bv]of SKY.stars){const p=P(ra,dec);if(!p)continue;if(p[0]<-60||p[0]>W+60||p[1]<-60||p[1]>H+60)continue;stars.push({x:p[0],y:p[1],m:mag,c:bvColor(bv),f:.6+2.2*r(),ph:r()*6.28})}
 const nf=Math.round(2600);for(let i=0;i<nf;i++)stars.push({x:r()*(W+600)-300,y:r()*(H+600)-300,m:7.2+r()*1.4,c:'255,250,240',f:.6+2*r(),ph:r()*6.28});
 const verts=c.verts.map(v=>{const p=P(v.ra,v.dec)||[W/2,H/2];return{x:p[0],y:p[1],mag:v.mag,name:v.en,en:v.en,named:!!v.en}});
 const cx=verts.reduce((a,v)=>a+v.x,0)/verts.length,cy=verts.reduce((a,v)=>a+v.y,0)/verts.length;const edges=[];c.polys.forEach(p=>{for(let i=0;i<p.length-1;i++)edges.push([p[i],p[i+1]])});
 {let mn=1e9,mx=-1e9;for(const v of verts){mn=Math.min(mn,v.y);mx=Math.max(mx,v.y)}let sh=Math.max(0,210-mn);if(mx+sh>H*.7)sh=Math.min(sh,Math.max(0,H*.7-mx));if(mx>H*.7&&sh===0)sh=-Math.min(mx-H*.7,Math.max(0,mn-210));for(const v of verts)v.y+=sh;for(const st of stars)st.y+=sh}
 const cx2=verts.reduce((a,v)=>a+v.x,0)/verts.length,cy2=verts.reduce((a,v)=>a+v.y,0)/verts.length;
 const labels=[],rects=[];const named=verts.map((v,j)=>({v,j})).filter(o=>o.v.named&&o.v.en).sort((a,b)=>a.v.mag-b.v.mag);
 const wid=(t,sz)=>[...t].reduce((a,ch)=>a+(ch.charCodeAt(0)>255?sz*.98:sz*.58),0);
 for(const o of named){const v=o.v,dx=v.x-cx,dy=v.y-cy,L=Math.hypot(dx,dy)||1,base=Math.atan2(dy,dx);let best=null;
  loop:for(const rad of[28,46,66])for(const da of[0,.6,-.6,1.2,-1.2,1.9,-1.9,3.14]){const a=base+da,ux=Math.cos(a),uy=Math.sin(a),lx=v.x+ux*rad,ly=v.y+uy*rad,al=ux>=0?'left':'right',w=wid(v.en,22),x0=al==='left'?lx:lx-w-8,r={x0:x0,x1:x0+w+8,y0:ly-16,y1:ly+16};
   if(r.x0<50||r.x1>W-50||r.y0<170||r.y1>H*.78)continue;let bad=false;for(const q of rects)if(!(r.x1<q.x0||r.x0>q.x1||r.y1<q.y0||r.y0>q.y1)){bad=true;break}
   if(!bad)for(const u of verts)if(u.x>r.x0-14&&u.x<r.x1+14&&u.y>r.y0-14&&u.y<r.y1+14&&u!==v){bad=true;break}
   if(!bad){best={lx,ly,al,ux,uy,r};break loop}}
  if(!best){const a=base,ux=Math.cos(a),uy=Math.sin(a);best={lx:v.x+ux*34,ly:v.y+uy*34,al:ux>=0?'left':'right',ux,uy,r:null}}
  if(best.r)rects.push(best.r);labels.push({j:o.j,...best})}
 return{c,stars,verts,edges,cx:cx2,cy:cy2,k,labels}}
// ---------------------------------------------------------------- places
function ridge(baseY,amp,seed,fr,col,off,rim,bottom=H+10,sharp=0){ctx.beginPath();ctx.moveTo(-10,bottom);
 const fn=x=>amp*(.5*Math.sin((x+off)*fr+seed)+.3*Math.sin((x+off)*fr*2.3+seed*1.7)+.18*Math.sin((x+off)*fr*5.1+seed*.6)+.1*Math.sin((x+off)*fr*11+seed*2.2));
 for(let x=-10;x<=W+10;x+=8){let y=fn(x);if(sharp)y=Math.abs(y)*1.25+.25*y;ctx.lineTo(x,baseY-y)}ctx.lineTo(W+10,bottom);ctx.closePath();ctx.fillStyle=col;ctx.fill();
 if(rim){ctx.beginPath();for(let x=-10;x<=W+10;x+=8){let y=fn(x);if(sharp)y=Math.abs(y)*1.25+.25*y;x===-10?ctx.moveTo(x,baseY-y):ctx.lineTo(x,baseY-y)}ctx.strokeStyle=rim;ctx.lineWidth=1.8;ctx.stroke()}}
function skyGrad(stops){const g=ctx.createLinearGradient(0,0,0,H);stops.forEach(([p,c])=>g.addColorStop(p,rgb(c)));ctx.fillStyle=g;ctx.fillRect(0,0,W,H)}
function fireflies(t,n,seed,y0,y1,col='200,255,120'){const r=rng(seed);ctx.globalCompositeOperation='lighter';for(let i=0;i<n;i++){const x=r()*W,y=y0+r()*(y1-y0),s=.4+r()*.9,p=r()*6.28,a=20+r()*30,b=10+r()*18,f=1+2*r();
 const px=x+a*Math.sin(t*s+p),py=y+b*Math.sin(t*s*1.3+p*2),pu=Math.pow(.5+.5*Math.sin(t*f+p),2);glow(px,py,8+12*pu,col,.2+.6*pu);glow(px,py,2.2,'255,255,220',.9*pu)}ctx.globalCompositeOperation='source-over'}
const PLACES=[
 {name:'사막',sky:[[0,[3,5,20]],[.55,[24,18,56]],[.82,[110,60,76]],[1,[40,24,40]]],faint:1,hz:H*.8,
  fg(t,cam){ridge(H*.86,70,3,.0032,'#14091a',cam,'rgba(255,170,120,.45)');ridge(H*.92,50,9,.005,'#0c0610',cam*1.4,'rgba(255,150,110,.3)');ridge(H*1.0,45,14,.007,'#06030a',cam*2,null);
   const r=rng(7);ctx.fillStyle='rgba(255,200,150,.5)';for(let i=0;i<70;i++){const y=H*(.82+.16*r()),x=((r()*W*1.4+t*(60+80*r()))%(W*1.4))-W*.2;ctx.fillRect(x,y,2+r()*5,1)}
   ctx.fillStyle='#04020a';const cx=W*.12-cam*2;ctx.beginPath();ctx.roundRect(cx-14,H*.74,28,H*.3,14);ctx.fill();ctx.beginPath();ctx.roundRect(cx-52,H*.8,24,70,12);ctx.fill();ctx.fillRect(cx-52,H*.86,52,18);ctx.beginPath();ctx.roundRect(cx+26,H*.77,22,80,11);ctx.fill();ctx.fillRect(cx+14,H*.85,26,16)}},
 {name:'설산',sky:[[0,[2,7,28]],[.6,[16,36,78]],[.85,[84,116,168]],[1,[30,50,90]]],faint:1,hz:H*.8,
  fg(t,cam){ridge(H*.84,200,5,.0028,'#0b1630',cam,'rgba(200,225,255,.7)',H+10,1);ridge(H*.9,130,11,.0045,'#060d20',cam*1.6,'rgba(190,215,255,.45)',H+10,1);ridge(H*1.0,60,2,.007,'#03060f',cam*2.4,null);
   ctx.globalCompositeOperation='lighter';const r=rng(9);for(let l=0;l<3;l++){for(let i=0;i<8;i++){const x=((r()*W*1.5+t*(10+l*8))%(W*1.5))-W*.25,y=H*(.74+l*.06)+r()*40,w=240+r()*320;ctx.save();ctx.translate(x,y);ctx.scale(1,.28);const g=ctx.createRadialGradient(0,0,0,0,0,w);g.addColorStop(0,'rgba(170,200,255,.09)');g.addColorStop(1,'rgba(170,200,255,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(0,0,w,0,6.283);ctx.fill();ctx.restore()}}ctx.globalCompositeOperation='source-over'}},
 {name:'해변',sky:[[0,[2,8,30]],[.6,[12,40,84]],[.78,[40,92,124]],[.78,[8,30,56]],[1,[2,10,24]]],faint:1,hz:H*.78,
  fg(t,cam){const hz=H*.78,r=rng(12);ctx.globalCompositeOperation='lighter';for(let i=0;i<260;i++){const y=hz+4+Math.pow(r(),1.5)*(H*.2),x=r()*W,w=20+r()*140,a=.05+.14*r(),sh=.5+.5*Math.sin(t*(.6+r())+r()*6);ctx.fillStyle=`rgba(170,215,255,${a*sh})`;ctx.fillRect(x-w/2+8*Math.sin(t*.8+i),y,w,1.5)}ctx.globalCompositeOperation='source-over';
   for(let k=0;k<5;k++){ctx.strokeStyle=`rgba(220,240,255,${.25+.1*k})`;ctx.lineWidth=2+k*.6;ctx.beginPath();const y0=H*(.9+k*.022);for(let x=0;x<=W;x+=12)ctx.lineTo(x,y0+6*Math.sin(x*.01+t*(1+k*.2)+k));ctx.stroke()}
   ctx.fillStyle='#02060e';ctx.fillRect(0,H*.97,W,H*.03);const px=W*.88,py=H*.99;ctx.strokeStyle='#02060e';ctx.lineWidth=14;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(px,py);ctx.quadraticCurveTo(px-30,py-200,px-80,py-340);ctx.stroke();
   for(let i=0;i<8;i++){const a=-Math.PI/2+i*.55-1.8+.06*Math.sin(t*1.2+i);ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(px-80,py-340);ctx.quadraticCurveTo(px-80+Math.cos(a)*90,py-340+Math.sin(a)*60-30,px-80+Math.cos(a)*170,py-340+Math.sin(a)*120+40+8*Math.sin(t*1.5+i));ctx.stroke()}}},
 {name:'숲',sky:[[0,[1,5,16]],[.65,[8,26,40]],[1,[16,44,56]]],faint:1,hz:H*.85,
  fg(t,cam){function pine(x,b,h,w){ctx.beginPath();for(let k=0;k<6;k++){const yy=b-h*(k/6),ww=w*(1-k/7);ctx.moveTo(x-ww,yy);ctx.lineTo(x,yy-h/5.2);ctx.lineTo(x+ww,yy)}ctx.closePath();ctx.fill();ctx.fillRect(x-w*.07,b,w*.14,h*.12)}
   const r=rng(21);ctx.fillStyle='#04100f';for(let i=0;i<26;i++){const x=r()*W*1.3-W*.15-cam*.6,h=140+r()*140;pine(x,H*.99,h,34+h*.18)}
   ctx.fillStyle='#02080a';for(const[x,h]of[[W*.05,640],[W*.14,520],[W*.93,660],[W*.84,500],[W*.99,540]])pine(x-cam*1.4,H*1.02,h,h*.28);
   ctx.globalCompositeOperation='lighter';const g=ctx.createLinearGradient(0,H*.8,0,H);g.addColorStop(0,'rgba(120,180,190,0)');g.addColorStop(1,'rgba(120,180,190,.1)');ctx.fillStyle=g;ctx.fillRect(0,H*.8,W,H*.2);ctx.globalCompositeOperation='source-over';fireflies(t,40,22,H*.5,H*.95)}},
 {name:'도시',sky:[[0,[3,5,18]],[.5,[22,22,50]],[.78,[110,60,44]],[1,[60,30,28]]],faint:.35,hz:H*.82,
  fg(t,cam){const r=rng(31);ctx.globalCompositeOperation='lighter';glow(W*.5,H*.86,900,'255,150,80',.28);ctx.globalCompositeOperation='source-over';ctx.fillStyle='#07060c';
   for(let l=0;l<2;l++){let x=-40;const rr=rng(40+l);while(x<W+40){const w=60+rr()*90,h=(l?60:100)+rr()*(l?110:170);ctx.fillStyle=l?'#0b0912':'#050409';ctx.fillRect(x-cam*(.8+l),H*.9-h,w,h+H*.2);
     for(let wy=H*.9-h+14;wy<H*.88;wy+=16)for(let wx=x+8;wx<x+w-8;wx+=14){const on=rr()<.5;if(on){const fl=.6+.4*Math.sin(t*(.3+rr())+rr()*9);ctx.fillStyle=`rgba(255,${190+rr()*50|0},120,${.55*fl})`;ctx.fillRect(wx-cam*(.8+l),wy,6,8)}}
     x+=w+4+rr()*10}}
   ctx.fillStyle='#030207';ctx.fillRect(0,H*.94,W,H*.06);ctx.globalCompositeOperation='lighter';for(let i=0;i<9;i++){const dir=i%2?1:-1,x=(((t*(90+i*14)*dir+i*400)%(W+300))+W+300)%(W+300)-150,y=H*(.955+.012*(i%3));glow(x,y,16,dir>0?'255,235,200':'255,70,60',.9)}ctx.globalCompositeOperation='source-over'}},
 {name:'초원',sky:[[0,[2,7,26]],[.6,[20,34,66]],[.85,[44,70,100]],[1,[10,24,34]]],faint:1,hz:H*.8,
  fg(t,cam){ridge(H*.84,60,2,.0035,'#07131a',cam,'rgba(120,200,200,.3)');ridge(H*.92,45,8,.0055,'#040c11',cam*1.4,null);
   ctx.fillStyle='#02070a';ctx.beginPath();ctx.ellipse(W*.78-cam,H*.7,6,60,0,0,6.283);ctx.fill();ctx.strokeStyle='#02070a';ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(W*.78-cam,H*.82);ctx.lineTo(W*.78-cam,H*.66);ctx.stroke();for(const[dx,dy,rad]of[[0,-90,70],[-46,-60,52],[46,-62,56],[0,-40,60]]){ctx.beginPath();ctx.arc(W*.78-cam+dx,H*.66+dy*.3,rad,0,6.283);ctx.fill()}
   const r=rng(61);ctx.strokeStyle='#020608';ctx.lineWidth=2.2;for(let i=0;i<340;i++){const x=r()*W,h=40+r()*100,y=H*(.92+r()*.1),sw=Math.sin(t*1.2+x*.01+r()*3)*(10+h*.12);ctx.beginPath();ctx.moveTo(x,y);ctx.quadraticCurveTo(x+sw*.4,y-h*.6,x+sw,y-h);ctx.stroke()}fireflies(t,28,62,H*.7,H*.98)}},
 {name:'호수',sky:[[0,[2,5,22]],[.7,[18,30,70]],[1,[6,10,30]]],faint:1,hz:H*.72,mirror:true,
  fg(t,cam){const hz=H*.72;ridge(hz+2,130,16,.0042,'#02040a',cam*.6,'rgba(150,180,255,.35)',hz+2);ridge(hz+2,60,18,.007,'#010208',cam,null,hz+2);
   const g=ctx.createLinearGradient(0,hz,0,H);g.addColorStop(0,'rgba(60,80,140,.3)');g.addColorStop(1,'rgba(0,0,10,.75)');ctx.fillStyle=g;ctx.fillRect(0,hz,W,H-hz);
   const r=rng(71);ctx.globalCompositeOperation='lighter';for(let i=0;i<200;i++){const y=hz+8+Math.pow(r(),1.6)*(H-hz),x=r()*W,w=30+r()*160,a=.04+.1*r(),sh=.5+.5*Math.sin(t*(.5+r())+r()*6);ctx.fillStyle=`rgba(170,200,255,${a*sh})`;ctx.fillRect(x-w/2,y,w,1.4)}ctx.globalCompositeOperation='source-over';fireflies(t,34,72,H*.55,H*.9)}},
 {name:'한옥마을',sky:[[0,[2,5,22]],[.62,[18,22,58]],[.86,[44,40,84]],[1,[14,12,30]]],faint:.9,hz:H*.9,
  fg(t,cam){function hanok(x,b,s,lit){ctx.fillStyle='#05040c';ctx.fillRect(x-170*s,b-150*s,340*s,150*s);
    ctx.beginPath();ctx.moveTo(x-260*s,b-150*s);ctx.bezierCurveTo(x-210*s,b-160*s,x-170*s,b-190*s,x-120*s,b-230*s);ctx.bezierCurveTo(x-60*s,b-262*s,x+60*s,b-262*s,x+120*s,b-230*s);ctx.bezierCurveTo(x+170*s,b-190*s,x+210*s,b-160*s,x+260*s,b-150*s);ctx.bezierCurveTo(x+200*s,b-136*s,x+160*s,b-130*s,x+120*s,b-134*s);ctx.lineTo(x-120*s,b-134*s);ctx.bezierCurveTo(x-160*s,b-130*s,x-200*s,b-136*s,x-260*s,b-150*s);ctx.closePath();ctx.fillStyle='#030208';ctx.fill();ctx.strokeStyle='rgba(180,170,255,.22)';ctx.lineWidth=1.6;ctx.stroke();
    for(let i=0;i<3;i++){const wx=x-120*s+i*86*s,fl=.75+.25*Math.sin(t*.7+i+x);ctx.fillStyle=`rgba(255,200,120,${.8*fl*lit})`;ctx.fillRect(wx,b-120*s,70*s,88*s);ctx.strokeStyle='rgba(30,14,6,.9)';ctx.lineWidth=Math.max(1,2.2*s);for(let k=0;k<=3;k++){ctx.beginPath();ctx.moveTo(wx+k*70*s/3,b-120*s);ctx.lineTo(wx+k*70*s/3,b-32*s);ctx.stroke()}
     ctx.globalCompositeOperation='lighter';glow(wx+35*s,b-76*s,70*s,'255,190,110',.18*fl*lit);ctx.globalCompositeOperation='source-over'}
    ctx.fillStyle='#030208';ctx.fillRect(x-185*s,b-12*s,370*s,14*s)}
   ridge(H*.915,26,4,.003,'#0a0818',cam*.5,'rgba(160,150,230,.25)');ridge(H*.945,16,9,.005,'#06050f',cam*.8,null);
   hanok(W*.30-cam,H*.975,.26,1);hanok(W*.50-cam*1.1,H*.985,.34,.85);hanok(W*.66-cam*.8,H*.972,.2,.9);
   ctx.fillStyle='#030208';ctx.fillRect(0,H*.975,W,H*.025);ctx.globalCompositeOperation='lighter';for(const lx of[W*.2,W*.42,W*.58,W*.8]){const fl=.7+.3*Math.sin(t*2+lx);glow(lx,H*.965,16,'255,160,80',.7*fl);glow(lx,H*.965,3,'255,230,170',1)}ctx.globalCompositeOperation='source-over'}},
 {name:'화산',sky:[[0,[8,3,12]],[.55,[34,10,24]],[.85,[120,34,20]],[1,[50,14,10]]],faint:.8,hz:H*.82,
  fg(t,cam){ctx.globalCompositeOperation='lighter';glow(W*.42-cam,H*.5,560,'255,90,30',.28+.06*Math.sin(t*1.7));ctx.globalCompositeOperation='source-over';
   ctx.fillStyle='#060204';ctx.beginPath();ctx.moveTo(W*.1-cam,H+10);ctx.lineTo(W*.36-cam,H*.5);ctx.lineTo(W*.48-cam,H*.5);ctx.lineTo(W*.76-cam,H+10);ctx.closePath();ctx.fill();ridge(H*.95,40,3,.006,'#030102',cam*1.6,null);
   ctx.globalCompositeOperation='lighter';const r=rng(81);for(let i=0;i<7;i++){const sx=W*.4-cam+(r()-.5)*40;const g=ctx.createLinearGradient(sx,H*.5,sx+(r()-.5)*260,H*.95);const fl=.6+.4*Math.sin(t*1.5+i);g.addColorStop(0,`rgba(255,160,60,${.9*fl})`);g.addColorStop(1,'rgba(255,60,20,0)');ctx.strokeStyle=g;ctx.lineWidth=3+r()*3;ctx.beginPath();ctx.moveTo(sx,H*.5);ctx.quadraticCurveTo(sx+(r()-.5)*160,H*.7,sx+(r()-.5)*260,H*.95);ctx.stroke()}
   for(let i=0;i<60;i++){const ph=((t*(.25+r()*.4)+r())%1),x=W*.42-cam+(r()-.5)*120+Math.sin(t+i)*40*ph,y=H*.5-ph*H*.45;glow(x,y,5+4*r(),'255,150,60',(1-ph)*.9)}
   for(let i=0;i<14;i++){const ph=((t*.08+i/14)%1),x=W*.42-cam+Math.sin(i*3+t*.4)*60*ph,y=H*.5-ph*H*.5,rad=60+ph*120;glow(x,y,rad,'120,60,60',.07*(1-ph))}ctx.globalCompositeOperation='source-over'}},
 {name:'극지',sky:[[0,[1,4,18]],[.6,[8,22,44]],[.82,[24,50,80]],[1,[10,20,36]]],faint:1,hz:H*.82,aur:true,
  fg(t,cam){ridge(H*.88,36,6,.004,'#0a1426',cam,'rgba(190,230,255,.45)');ridge(H*.95,26,12,.006,'#060c1a',cam*1.5,'rgba(190,230,255,.3)');const r=rng(91);ctx.globalCompositeOperation='lighter';for(let i=0;i<70;i++){const x=r()*W,y=H*(.9+r()*.1),tw=Math.pow(.5+.5*Math.sin(t*(1+r()*2)+r()*6),3);glow(x,y,6,'200,235,255',.7*tw)}ctx.globalCompositeOperation='source-over';
   const tx=W*.72-cam*1.5,ty=H*.93;ctx.fillStyle='#050912';ctx.beginPath();ctx.moveTo(tx-90,ty);ctx.lineTo(tx,ty-120);ctx.lineTo(tx+90,ty);ctx.closePath();ctx.fill();ctx.globalCompositeOperation='lighter';const fl=.8+.2*Math.sin(t*3);glow(tx,ty-34,70,'255,170,90',.55*fl);ctx.fillStyle='rgba(255,200,120,.55)';ctx.beginPath();ctx.moveTo(tx-14,ty);ctx.lineTo(tx,ty-50);ctx.lineTo(tx+14,ty);ctx.fill();ctx.globalCompositeOperation='source-over'}}
];
function aurora(t,amp){ctx.globalCompositeOperation='lighter';const cols=[[60,255,150],[40,230,210],[165,110,255]];
 for(let k=0;k<3;k++){const c=cols[k],yb=H*(.4+k*.05),ph=k*1.3;for(let x=-20;x<W+20;x+=6){const y0=yb+60*Math.sin(x*.0035+t*.45+ph)+32*Math.sin(x*.0105-t*.8+ph*2),h=(220+120*Math.sin(x*.0048+t*.3+ph)+60*Math.sin(x*.0125+t*.9));
  const inten=amp*(.45+.55*Math.pow(.5+.5*Math.sin(x*.0062+t*.35+ph*1.7),1.6))*(.55+.45*Math.sin(x*.07+t*.9+k*2)*Math.sin(x*.021-t*.5));const g=ctx.createLinearGradient(0,y0-h,0,y0);g.addColorStop(0,`rgba(${c},0)`);g.addColorStop(.62,`rgba(${c},${.3*inten})`);g.addColorStop(.93,`rgba(${c},${.85*inten})`);g.addColorStop(1,`rgba(255,255,255,${.3*inten})`);ctx.fillStyle=g;ctx.fillRect(x,y0-h,6.5,h+4)}}ctx.globalCompositeOperation='source-over'}
// ---------------------------------------------------------------- the scene: place + sky + constellation drawing + names
const SEQ=[],PLACE_OF=[['Sco','Leo','Cru','Cnc'],['UMa','UMi','Cas','Cep'],['Del','Psc','Aqr','PsA'],['Lyr','Cyg','Aql','Sge'],['Ori','Gem','CMa','CMi'],['Boo','Vir','Lib','CrB'],['Peg','And','Per','Ari'],['Tau','Aur','Lep','Cet'],['Sgr','Cap','Oph','Crv'],['Dra','Her','Cen','Lac']];
PLACE_OF.forEach((codes,pi)=>codes.forEach(code=>SEQ.push({place:pi,code})));
window.customScene=(pi,code)=>{SEQ[999]={place:pi,code};delete cache[999]};window.SEQ=SEQ;window.PLACES=PLACES;
const cache={};
function scene(i){if(cache[i])return cache[i];const s=SEQ[i],ci=SKY.cons.findIndex(c=>c.code===s.code);const roll=(i%5-2)*.05;return cache[i]=prepScene(ci,roll)}
function starsDraw(S,place,t,cam,a){ctx.globalCompositeOperation='lighter';const z=cam.z;for(const s of S.stars){const x=W/2+(s.x-W/2)*z+cam.x,y=H*.40+(s.y-H*.40)*z+cam.y;if(x<-10||x>W+10||y<-10||y>H+10)continue;if(y>place.hz+30)continue;
  const tw=.7+.3*Math.sin(t*s.f+s.ph);let vis=clamp((8.4-s.m)/5.4,.1,1);if(place.faint<1&&s.m>3.2)vis*=place.faint;const al=a*tw*vis;if(al<.03)continue;const sz=clamp(.5+(6.4-s.m)*.3,.5,2.4);
  if(s.m<2.6){glow(x,y,sz*5,s.c,al*.6);ctx.globalAlpha=al;ctx.fillStyle='#fff';ctx.fillRect(x-sz*.5,y-sz*.5,sz,sz);if(s.m<1.2){ctx.fillRect(x-sz*3,y-.35,sz*6,.7);ctx.fillRect(x-.35,y-sz*3,.7,sz*6)}}else{ctx.globalAlpha=al;ctx.fillStyle='rgb('+s.c+')';ctx.fillRect(x-sz*.5,y-sz*.5,sz,sz)}}
 ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over'}
function label(txt,x,y,size,col,a,align='left'){if(a<=.01)return;ctx.save();ctx.globalAlpha=a;ctx.font=`500 ${size}px "Helvetica Neue",Arial,sans-serif`;ctx.letterSpacing='1.5px';ctx.textAlign=align;ctx.textBaseline='middle';ctx.shadowColor=col;ctx.shadowBlur=14;ctx.fillStyle='#fff';ctx.fillText(txt,x,y);ctx.shadowBlur=0;ctx.restore()}
const T_DRAW=1.5,D_DRAW=7.2,T_FLASH=T_DRAW+D_DRAW+.1,T_NAME=T_FLASH+1.0;
function drawFrame(i,t){ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';const S=scene(i),place=PLACES[SEQ[i].place],p=t/LEN;
 const cam={x:lerp(-20,20,p)*(i%2?-1:1),y:lerp(6,-6,p),z:lerp(1,1.025,p)};const toS=(x,y)=>[W/2+(x-W/2)*cam.z+cam.x,H*.40+(y-H*.40)*cam.z+cam.y];
 skyGrad(place.sky);starsDraw(S,place,t,cam,1);if(place.aur)aurora(t,clamp(t/3,0,1));
 // reflection for lake
 if(place.mirror){ctx.save();ctx.beginPath();ctx.rect(0,place.hz,W,H-place.hz);ctx.clip();ctx.translate(0,place.hz*2);ctx.scale(1,-1);ctx.globalAlpha=.4;starsDraw(S,{hz:place.hz,faint:1},t+.3,cam,.7);ctx.restore()}
 // constellation lines (laser draw)
 const V=S.verts.map(v=>toS(v.x,v.y)),n=S.edges.length,dt=D_DRAW/n;ctx.globalCompositeOperation='lighter';
 const done=t>T_FLASH,fl=clamp((t-T_FLASH)/1.3,0,1),pulse=done?Math.sin(Math.PI*fl):0;
 S.edges.forEach(([a,b],k)=>{const e=clamp((t-T_DRAW-k*dt)/dt,0,1);if(e<=0)return;const[x1,y1]=V[a],[x2,y2]=V[b],ex=lerp(x1,x2,e),ey=lerp(y1,y2,e);
  const la=done?(.55+.45*pulse):.9;ctx.lineCap='round';ctx.strokeStyle=`rgba(80,225,255,${la*.5})`;ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(ex,ey);ctx.stroke();ctx.strokeStyle=`rgba(210,250,255,${la})`;ctx.lineWidth=1.8;ctx.stroke();if(e<1)glow(ex,ey,26,'130,240,255',1)});
 S.verts.forEach((v,j)=>{const[x,y]=V[j];let reach=-1;S.edges.forEach(([a,b],k)=>{if(a===j||b===j){const tt=T_DRAW+k*dt+(b===j?dt:0);if(reach<0||tt<reach)reach=tt}});if(reach<0||t<reach)return;
  const age=t-reach,sparkle=clamp(1-age/.8,0,1),base=clamp(1.3+(5-v.mag)*.5,1.6,4.2);glow(x,y,(16+base*5)*(1+sparkle*.8),'255,255,255',.55+.4*sparkle);
  if(done){const big=Math.sin(Math.PI*fl)*1.0;glow(x,y,(30+base*14)*(1+big*2.4),'210,245,255',.4+.6*big);if(big>.05){ctx.fillStyle=`rgba(255,255,255,${.9*big})`;const L=(34+base*18)*big;ctx.fillRect(x-L,y-.8,2*L,1.6);ctx.fillRect(x-.8,y-L,1.6,2*L)}}else glow(x,y,10+base*3,'255,255,255',.7)});
 if(done&&fl<1){ctx.fillStyle=`rgba(180,235,255,${.1*pulse})`;ctx.fillRect(0,0,W,H)}ctx.globalCompositeOperation='source-over';
 place.fg(t,cam.x*.6);
 // names
 const c=S.c,tn=(t-T_NAME);if(tn>0){const a=sm(tn/1.2),ty=H*.1;ctx.save();ctx.globalAlpha=a;ctx.font='500 54px "Helvetica Neue",Arial,sans-serif';ctx.letterSpacing='16px';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#e8fbff';ctx.shadowColor='rgba(110,230,255,1)';ctx.shadowBlur=18;ctx.fillText(c.la.toUpperCase(),W/2+8,ty);ctx.shadowBlur=8;if(c.en&&c.en.toLowerCase()!==c.la.toLowerCase()){ctx.globalAlpha=a*.75;ctx.font='400 22px "Helvetica Neue",Arial,sans-serif';ctx.letterSpacing='8px';ctx.fillStyle='#bfefff';ctx.fillText(c.en.toUpperCase(),W/2+4,ty+46)}ctx.restore();
  const u=sm(tn/1.4);ctx.strokeStyle=`rgba(120,235,255,${.8*a})`;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(W/2-200*u,ty+84);ctx.lineTo(W/2+200*u,ty+84);ctx.stroke();
  S.labels.forEach((o,k)=>{const aa=sm((tn-.8-k*.3)/.8);if(aa<=0)return;const v=S.verts[o.j],[x,y]=V[o.j],lx=o.lx+(x-v.x),ly=o.ly+(y-v.y),tx=lx+(o.ux>=0?8:-8);
   ctx.strokeStyle=`rgba(255,255,255,${.5*aa})`;ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(x+o.ux*14,y+o.uy*14);ctx.lineTo(lx,ly);ctx.stroke();label(v.en,tx,ly,22,'rgba(255,230,160,1)',aa,o.al)})}
 // vignette + fades
 const g=ctx.createRadialGradient(W/2,H/2,H*.5,W/2,H/2,H*1.0);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'rgba(0,0,0,.5)');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
 const af=Math.min(clamp(t/FADE,0,1),clamp((LEN-t)/FADE,0,1));if(af<1){ctx.fillStyle=`rgba(0,0,0,${1-af})`;ctx.fillRect(0,0,W,H)}}
window.drawFrame=drawFrame;window.meta=i=>({placeIdx:SEQ[i].place,place:PLACES[SEQ[i].place].name,code:SEQ[i].code,ko:SKY.cons.find(c=>c.code===SEQ[i].code).ko,nth:PLACE_OF[SEQ[i].place].indexOf(SEQ[i].code)+1});
