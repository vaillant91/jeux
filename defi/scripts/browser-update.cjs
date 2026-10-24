/* A -> B at the same origin/profile. Restores the source and production build. */
const {chromium}=require('playwright');const fs=require('node:fs');const assert=require('node:assert/strict');const {execSync}=require('node:child_process');
(async()=>{
 const source=fs.readFileSync('index.html','utf8');let browser;
 const build=()=>execSync('npm run build',{env:{...process.env,PAGES_BASE_PATH:'/jeux/'},stdio:'pipe'});
 try{
  build();browser=await chromium.launch({channel:'chrome',headless:true});const context=await browser.newContext();const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:4174/jeux/');await page.getByRole('button',{name:'Créer un parcours',exact:true}).click();await page.locator('#level-name').fill('Conservé après mise à jour');await page.locator('#home').click();
  await page.evaluate(async()=>{await navigator.serviceWorker.ready});await page.reload();await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
  await page.getByRole('button',{name:'Arcade aléatoire',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).waitFor();
  const code=await page.locator('#mode-label').textContent();
  fs.writeFileSync('index.html',source.replace('</title>',' — version B</title>'));build();
  await page.evaluate(async()=>{const reg=await navigator.serviceWorker.getRegistration();await reg.update()});
  await page.locator('#update').waitFor({state:'visible'});assert(!((await page.title()).includes('version B')));
  await page.locator('#update').click();assert.match(await page.locator('#message').textContent(),/Termine la partie/);assert.equal(await page.locator('#mode-label').textContent(),code);
  await page.locator('#home').click();await page.locator('#update').click();await page.waitForFunction(()=>document.title.includes('version B'));
  await page.getByRole('button',{name:'Mes parcours',exact:true}).click();await page.getByRole('button',{name:'Conservé après mise à jour',exact:true}).waitFor();assert.deepEqual(errors,[]);
  console.log('PASS: A -> B waiting worker, update deferred during play, explicit safe activation, saved draft preserved.');
 }finally{if(browser)await browser.close();fs.writeFileSync('index.html',source);build()}
})().catch(e=>{console.error(e);process.exit(1)});
