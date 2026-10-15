/* Read-only Chromium/CDP recording; no accounts or database writes. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
(async()=>{
 const base=process.env.SAFERIDE_MAP_BASE || 'http://127.0.0.1:8000';
 const out=path.resolve(process.env.SAFERIDE_MAP_ARTIFACTS || 'artifacts/map-recording');
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({executablePath:process.env.SAFERIDE_CHROMIUM_PATH || '/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.goto(base,{waitUntil:'domcontentloaded',timeout:65000});
  await page.waitForFunction(()=>document.querySelector('[data-route-hero]').dataset.mapState==='ready',null,{timeout:65000});
  await page.locator('[data-route-hero]').scrollIntoViewIfNeeded();
  const box=await page.locator('[data-route-hero]').boundingBox();
  const cdp=await page.context().newCDPSession(page),frames=[];
  cdp.on('Page.screencastFrame',frame=>{
   const file=path.join(out,`frame-${String(frames.length).padStart(4,'0')}.jpg`);
   fs.writeFileSync(file,Buffer.from(frame.data,'base64'));
   frames.push({file,time:frame.metadata.timestamp});
   cdp.send('Page.screencastFrameAck',{sessionId:frame.sessionId}).catch(()=>{});
  });
  await cdp.send('Page.startScreencast',{format:'jpeg',quality:85,maxWidth:1440,maxHeight:1000,everyNthFrame:1});
  await page.waitForTimeout(8000);
  await cdp.send('Page.stopScreencast');await cdp.detach();
  if(frames.length<30)throw new Error('Too few Chromium frames to assess motion');
  const list=frames.map((f,i)=>`file '${f.file}'\nduration ${Math.max(.001,(frames[i+1]?.time || f.time+.04)-f.time)}`).join('\n');
  const input=path.join(out,'frames.txt');fs.writeFileSync(input,list+'\n');
  const video=path.join(out,'danfo-motion.mp4');
  const crop=`crop=${Math.floor(box.width)}:${Math.floor(box.height)}:${Math.floor(box.x)}:${Math.floor(box.y)},pad=ceil(iw/2)*2:ceil(ih/2)*2`;
  const result=spawnSync('ffmpeg',['-y','-loglevel','error','-f','concat','-safe','0','-i',input,'-vf',crop,'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',video],{encoding:'utf8'});
  if(result.status)throw new Error(result.stderr);
  console.log(JSON.stringify({video,frames:frames.length,recordedSeconds:frames.at(-1).time-frames[0].time}));
 }finally{await browser.close()}
})().catch(error=>{console.error(error.message);process.exitCode=1});
