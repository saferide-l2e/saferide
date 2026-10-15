/* Real Chromium motion QA. --fixture-basemap is an explicitly isolated test,
   using the actual MapLibre engine and live OSRM geometry, without street tiles. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const base = process.env.SAFERIDE_MAP_BASE || 'http://127.0.0.1:8000';
const fixture = process.argv.includes('--fixture-basemap');
const keyless = fixture || process.argv.includes('--keyless');
if (fixture && !/^http:\/\/(127\.0\.0\.1|localhost):/.test(base)) throw new Error('Fixtures are local-only');
const out = path.resolve(process.env.SAFERIDE_MAP_ARTIFACTS || 'artifacts/map');
fs.mkdirSync(out, {recursive:true});
const evidence = {base, fixtureBasemap:fixture, keyless, screenshots:[], routes:[], errors:[], consoleErrors:[]};
const waitReady = page => page.waitForFunction(()=>document.querySelector('[data-route-hero]').dataset.mapState==='ready',null,{timeout:65000});
const sample = page => page.evaluate(()=>{
 const element=document.querySelector('.danfo-marker'), image=element.querySelector('img'), r=element.getBoundingClientRect();
 return {x:r.x+r.width/2,y:r.y+r.height/2,heading:Number(image.dataset.heading),width:parseFloat(getComputedStyle(element).width)};
});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.SAFERIDE_CHROMIUM_PATH || '/usr/bin/chromium',headless:true,
  args:['--no-sandbox','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 if(keyless){
  await context.route(base+'/',async route=>{const response=await route.fetch();const body=(await response.text()).replace(/data-google-key="[^"]*"/,'data-google-key=""');await route.fulfill({response,body})});
 }
 if(fixture){
  await context.route('https://tiles.openfreemap.org/styles/liberty',route=>route.fulfill({json:{version:8,sources:{fixture:{type:'geojson',data:{type:'FeatureCollection',features:[]},attribution:'Offline test canvas · Road geometry: OSRM / OpenStreetMap'}},layers:[{id:'background',type:'background',paint:{'background-color':'#dae6de'}}]}}));
 }
 await context.addInitScript(()=>{
  let motion;
  Object.defineProperty(window,'SafeRideMotion',{configurable:true,get:()=>motion,set:api=>{
   const original=api.createAnimator;
   api.createAnimator=options=>{window.__mapQA=options;const update=options.marker.update;options.marker.update=(p,h)=>{options.lastPosition=p;update(p,h)};return original(options)};motion=api;
  }});
 });
 const page=await context.newPage();
 let inducedFailure=false;
 page.on('console',entry=>{if(entry.type()==='error'&&!inducedFailure)evidence.consoleErrors.push(entry.text().replace(/key=[^&\s]+/g,'key=[redacted]'))});
 page.on('pageerror',error=>evidence.errors.push(error.message));
 const shot=async name=>{const file=path.join(out,name+'.png');await page.screenshot({path:file,fullPage:false});evidence.screenshots.push(file)};
 try{
  await page.goto(base+'/',{waitUntil:'domcontentloaded',timeout:65000});
  await waitReady(page);
  evidence.renderer=await page.locator('.maplibregl-canvas').count() ? 'MapLibre' : 'Google Maps';
  assert.equal(await page.locator('[data-map-provider]').count(),0);
  if(!fixture)await page.waitForFunction(()=>/OpenStreetMap|Terms|Map data/.test(Array.from(document.querySelectorAll('.maplibregl-ctrl-attrib,.gm-style-cc')).map(e=>e.textContent).join(' ')),null,{timeout:20000});
  evidence.attribution=(await page.locator('.maplibregl-ctrl-attrib, .gm-style-cc').allTextContents()).join(' ');
  if(!fixture)assert.match(evidence.attribution,/OpenStreetMap|Terms|Map data/);
  assert.equal((await page.locator('[data-map-directions]').innerText()).trim(),'View directions');
  for(const [width,height] of [[320,900],[390,1000],[768,1100],[1024,1000],[1440,1000]]){
   await page.setViewportSize({width,height});await page.locator('[data-route-hero]').scrollIntoViewIfNeeded();await page.waitForTimeout(250);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow at ${width}`);
   const p=await sample(page);assert.ok(p.width>=(width<=600?38:width<1024?42:45)&&p.width<=(width<=600?42:width<1024?46:50));
   await shot('map-'+width);
  }
  await page.setViewportSize({width:1440,height:1000});await page.locator('[data-route-hero]').scrollIntoViewIfNeeded();
  await page.locator('[data-map-origin]').selectOption('Yaba');await page.locator('[data-map-origin]').selectOption('Jibowu');await waitReady(page);await page.waitForTimeout(400);
  const frames=await page.evaluate(()=>new Promise(resolve=>{
   const result=[],begin=performance.now(),qa=window.__mapQA,points=qa.path.map(qa.project);
   const first=document.querySelector('.danfo-marker').getBoundingClientRect(),p=qa.project(qa.lastPosition),ox=first.x+first.width/2-p.x,oy=first.y+first.height/2-p.y;
   const roadError=(x,y)=>{let min=Infinity;for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i],dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1)));min=Math.min(min,Math.hypot(x-a.x-t*dx,y-a.y-t*dy))}return min};
   function record(now){const element=document.querySelector('.danfo-marker'),r=element.getBoundingClientRect();result.push({t:now,x:r.x+r.width/2,y:r.y+r.height/2,heading:Number(element.querySelector('img').dataset.heading),roadError:roadError(r.x+r.width/2-ox,r.y+r.height/2-oy)});if(now-begin<10000)requestAnimationFrame(record);else resolve(result)}requestAnimationFrame(record);
  }));
  const errors=[];
  for(let i=3;i<frames.length;i++){
   const a=frames[i-3],b=frames[i],dx=b.x-a.x,dy=b.y-a.y;
   if(Math.hypot(dx,dy)>.35){const target=Math.atan2(dy,dx)*180/Math.PI;errors.push(Math.abs(((b.heading-target+540)%360)-180))}
  }
  assert.ok(errors.length>5,'Not enough moving frames');
  evidence.motion={frames:frames.length,maxHeadingError:Math.max(...errors),meanHeadingError:errors.reduce((a,b)=>a+b,0)/errors.length,maxRouteDrift:Math.max(...frames.map(f=>f.roadError))};
  assert.ok(evidence.motion.maxRouteDrift<1.5,'Marker drifted off the projected road');
  assert.ok(evidence.motion.meanHeadingError<25,JSON.stringify(evidence.motion));
  fs.writeFileSync(path.join(out,'motion-frames.json'),JSON.stringify(frames,null,2));
  if(await page.locator('[data-route-hero]').getAttribute('data-motion')!=='playing'){await page.locator('[data-map-motion]').click();await page.waitForTimeout(100)}
  await page.locator('[data-map-motion]').click();assert.equal(await page.locator('[data-route-hero]').getAttribute('data-motion'),'paused');const paused=await sample(page);await page.waitForTimeout(400);const still=await sample(page);
  assert.ok(Math.hypot(paused.x-still.x,paused.y-still.y)<.1,'Pause moved the bus');
  await page.locator('[data-map-motion]').click();await page.waitForTimeout(400);const resumed=await sample(page);
  assert.ok(Math.hypot(resumed.x-still.x,resumed.y-still.y)>2,'Resume did not move');
  evidence.pauseResume='passed';
  // Capture successive actual Chromium frames, then encode their measured durations.
  await page.locator('[data-map-origin]').selectOption('Yaba');await page.locator('[data-map-origin]').selectOption('Jibowu');await waitReady(page);
  const videoFrames=[];
  for(let i=0;i<30;i++){
   const file=path.join(out,`motion-${String(i).padStart(3,'0')}.png`);const time=Date.now();await page.locator('[data-route-hero]').screenshot({path:file});videoFrames.push({file,time});await page.waitForTimeout(70);
  }
  const concat=videoFrames.map((frame,i)=>`file '${frame.file}'\nduration ${((videoFrames[i+1]?.time || frame.time+100)-frame.time)/1000}`).join('\n');
  const input=path.join(out,'motion-concat.txt');fs.writeFileSync(input,concat+'\n');
  const encoded=spawnSync('ffmpeg',['-y','-loglevel','error','-f','concat','-safe','0','-i',input,'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-pix_fmt','yuv420p','-movflags','+faststart',path.join(out,'danfo-motion.mp4')],{encoding:'utf8'});
  assert.equal(encoded.status,0,encoded.stderr);evidence.video=path.join(out,'danfo-motion.mp4');
  for(const [origin,destination] of [['Lekki Phase 1','Jibowu'],['Yaba','Ikeja'],['Agege','Oshodi'],['Surulere','CMS'],['Maryland','Victoria Island']]){
   await page.locator('[data-map-origin]').selectOption(origin);await page.locator('[data-map-destination]').selectOption(destination);await waitReady(page);
   assert.equal(await page.locator('[data-origin-label]').innerText(),origin);assert.equal(await page.locator('#site-to').inputValue(),destination);
   assert.ok((await page.locator('[data-map-directions]').getAttribute('href')).includes(encodeURIComponent(destination+', Lagos, Nigeria')));
   evidence.routes.push({origin,destination,distance:await page.locator('[data-map-distance]').innerText()});
  }
  await page.locator('[data-map-destination]').selectOption('Agege');await page.locator('[data-map-origin]').selectOption('Yaba');await page.locator('[data-map-destination]').selectOption('Ikeja');await waitReady(page);await page.waitForTimeout(1000);
  assert.equal(await page.locator('[data-destination-label]').innerText(),'Ikeja');assert.equal(await page.locator('.danfo-marker').count(),1);evidence.staleResponses='passed';
  await page.locator('[data-theme-toggle]').click();await shot('map-dark');assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.emulateMedia({reducedMotion:'reduce'});await page.locator('[data-map-origin]').selectOption('Jibowu');await waitReady(page);
  assert.equal(await page.locator('[data-route-hero]').getAttribute('data-motion'),'paused');const a=await sample(page);await page.waitForTimeout(300);const b=await sample(page);assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<.1);evidence.reducedMotion='passed';
  // Error scenarios are explicitly induced and never counted as provider success.
  inducedFailure=true;
  await context.route('**/route/v1/driving/**',route=>route.fulfill({status:503,body:'unavailable'}));
  await context.route('**/ComputeRoutes',route=>route.abort());
  await page.locator('[data-map-destination]').selectOption('Mile 2');await page.waitForFunction(()=>document.querySelector('[data-route-hero]').dataset.mapState==='unavailable',null,{timeout:45000});
  assert.equal(await page.locator('.danfo-marker').count(),0);assert.equal(await page.locator('[data-map-motion]').isDisabled(),true);assert.ok(await page.locator('[data-map-directions]').getAttribute('href'));evidence.failureFallback='passed';await shot('map-routing-unavailable');
  assert.deepEqual(evidence.errors,[]);assert.deepEqual(evidence.consoleErrors,[]);
 }catch(error){evidence.failure=error.message;await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});process.exitCode=1}
 finally{fs.writeFileSync(path.join(out,'qa-result.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify(evidence));await browser.close()}
})();
