const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createRoute,angleDelta,screenTangent,createAnimator}=require('../../static/js/danfo_motion.js');
const path=[{lng:3.3,lat:6.5},{lng:3.301,lat:6.5},{lng:3.301,lat:6.501}];
const project=p=>({x:p.lng*100000,y:-p.lat*100000});
test('distance interpolation traverses uneven segments without cutting corners',()=>{
 const route=createRoute([path[0],path[0],path[1],path[2]]);
 assert.deepEqual(route.at(0),path[0]);assert.deepEqual(route.at(route.length),path[2]);
 const p=route.at(route.length*.25);assert.equal(p.lat,6.5);assert.ok(p.lng>3.3&&p.lng<3.301);
 assert.throws(()=>createRoute([path[0],path[0]]));
});
test('screen tangent follows the projection, including rotated and pitched maps',()=>{
 const route=createRoute(path);
 assert.ok(Math.abs(screenTangent(route,10,project).angle)<1);
 const rotated=p=>({x:p.lat*50000,y:p.lng*100000});
 assert.ok(Math.abs(screenTangent(route,10,rotated).angle-90)<1);
 assert.ok(Math.abs(screenTangent(route,route.length-10,project).angle+90)<1);
});
test('heading interpolation takes the short turn across the 360-degree boundary',()=>{
 assert.equal(angleDelta(179,-179),2);assert.equal(angleDelta(-179,179),-2);
 assert.equal(angleDelta(10,350),-20);assert.equal(angleDelta(720,10),10);
});
test('animation pause, resume, hidden tabs and destruction preserve progress',()=>{
 let queue=new Map(),next=0,listener;global.document={hidden:false,addEventListener:(_,f)=>{listener=f},removeEventListener:()=>{}};
 global.requestAnimationFrame=f=>{queue.set(++next,f);return next};global.cancelAnimationFrame=id=>queue.delete(id);
 const frames=[],states=[];let removed=false;
 const animator=createAnimator({path,project,marker:{update:(p,h)=>frames.push({p,h}),remove:()=>{removed=true}},onState:s=>states.push(s)});
 const tick=t=>{const callbacks=[...queue.values()];queue.clear();callbacks.forEach(f=>f(t))};
 animator.play();tick(0);tick(16);const p=frames.at(-1).p;animator.pause();tick(1000);assert.deepEqual(frames.at(-1).p,p);
 animator.play();tick(1016);assert.deepEqual(frames.at(-1).p,p);tick(1032);assert.ok(frames.at(-1).p.lng>p.lng);
 document.hidden=true;listener();tick(60000);const hidden=frames.at(-1).p;document.hidden=false;listener();tick(120000);assert.deepEqual(frames.at(-1).p,hidden);
 animator.destroy();tick(120016);assert.equal(queue.size,0);assert.equal(removed,true);assert.ok(states.includes('paused'));
});
test('arrival stops instead of teleporting; replay is explicit',()=>{
 let callbacks=new Map(),id=0;global.document={hidden:false,addEventListener:()=>{},removeEventListener:()=>{}};
 global.requestAnimationFrame=f=>{callbacks.set(++id,f);return id};global.cancelAnimationFrame=n=>callbacks.delete(n);
 const short=[{lng:3.3,lat:6.5},{lng:3.300001,lat:6.5}],positions=[],states=[];
 const animator=createAnimator({path:short,project,marker:{update:p=>positions.push(p),remove:()=>{}},onState:s=>states.push(s)});
 const tick=t=>{const pending=[...callbacks.values()];callbacks.clear();pending.forEach(f=>f(t))};
 animator.play();tick(0);tick(64);assert.deepEqual(positions.at(-1),short[1]);assert.equal(states.at(-1),'arrived');assert.equal(callbacks.size,0);
 animator.play();assert.deepEqual(positions.at(-1),short[0]);assert.equal(states.at(-1),'playing');animator.destroy();
});
