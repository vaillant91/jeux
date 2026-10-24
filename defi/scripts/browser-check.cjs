/* Real Chromium smoke test. Requires playwright on NODE_PATH or installed locally. */
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');const zlib=require('node:zlib');
(async()=>{
 const browser=await chromium.launch({channel:process.env.BROWSER_CHANNEL||'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:1100}});const page=await context.newPage();const errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 fs.mkdirSync('test-results',{recursive:true});
 await page.goto('http://127.0.0.1:4174/jeux/');await page.getByRole('button',{name:'Jouer la campagne →',exact:true}).waitFor();
 await page.screenshot({path:'test-results/home.png',fullPage:true});
 await page.evaluate(async()=>{await navigator.serviceWorker.ready});await page.reload();await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
 const manifest=await page.evaluate(async()=>await(await fetch('./manifest.webmanifest')).json());assert.equal(manifest.scope,'/jeux/');
 await page.getByRole('button',{name:'Jouer la campagne →',exact:true}).click();await page.locator('#mode-label').filter({hasText:'CAMPAGNE'}).waitFor();
 await page.keyboard.down('ArrowRight');await page.waitForFunction(()=>document.querySelector('#hud').textContent.includes('500 pts'));await page.keyboard.up('ArrowRight');
 await page.getByRole('button',{name:'Pause',exact:true}).click();const hud=await page.locator('#hud').textContent();await page.waitForTimeout(250);assert.equal(await page.locator('#hud').textContent(),hud);await page.getByRole('button',{name:'Reprendre',exact:true}).click();
 await page.locator('#home').click();await page.getByRole('button',{name:'Créer un parcours',exact:true}).click();
 await page.locator('#level-name').fill('Recette navigateur');await page.locator('#theme').selectOption('volcan');
 await page.getByRole('button',{name:'6 · Gemme',exact:true}).click();let box=await page.locator('canvas').boundingBox();await page.mouse.click(box.x+box.width*(24+7*48+24)/1000,box.y+box.height*(112+4*48+24)/700);
 await page.getByRole('button',{name:'Partager',exact:true}).click();await page.locator('#share-dialog').waitFor({state:'visible'});let code=await page.locator('#share-code').inputValue();assert.equal(zlib.inflateSync(Buffer.from(code.slice(3),'base64url'))[4*40+7],6);await page.getByRole('button',{name:'Fermer',exact:true}).click();
 await page.getByRole('button',{name:'Annuler',exact:true}).click();await page.getByRole('button',{name:'Rétablir',exact:true}).click();
 await page.getByRole('button',{name:'Tester →',exact:true}).click();await page.getByRole('button',{name:'Éditeur',exact:true}).waitFor();await page.getByRole('button',{name:'Éditeur',exact:true}).click();assert.equal(await page.locator('#level-name').inputValue(),'Recette navigateur');
 await page.screenshot({path:'test-results/editor.png',fullPage:true});
 await page.locator('#home').click();await page.getByRole('button',{name:'Mes parcours',exact:true}).click();await page.getByRole('button',{name:'Recette navigateur',exact:true}).click();assert.equal(await page.locator('#theme').inputValue(),'volcan');
 // An independent P4 fixture verifies full input -> victory -> replay in Phaser.
 const tiles=Array.from({length:11},()=>Array(40).fill(0));tiles[10].fill(1);
 const bytes=Buffer.from([...tiles.flat(),1,9,5,9,0,0,0]);const shortCode='P4-'+zlib.deflateSync(bytes).toString('base64url');
 await page.locator('#home').click();await page.getByRole('textbox',{name:'Code du défi'}).fill(shortCode);await page.getByRole('button',{name:'Jouer ce code',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).waitFor();
 await page.keyboard.down('ArrowRight');await page.getByRole('heading',{name:'Défi relevé !',exact:true}).waitFor();await page.keyboard.up('ArrowRight');await page.getByRole('button',{name:'Rejouer',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).waitFor();assert.match(await page.locator('#hud').textContent(),/0 pts/);
 // Deterministic loss from a custom map with no landing beyond the start.
 for(let c=2;c<40;c++)tiles[10][c]=0;
 const fallCode='P4-'+zlib.deflateSync(Buffer.from([...tiles.flat(),1,9,38,9,0,0,0])).toString('base64url');
 await page.locator('#home').click();await page.getByRole('textbox',{name:'Code du défi'}).fill(fallCode);await page.getByRole('button',{name:'Jouer ce code',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).waitFor();await page.keyboard.down('ArrowRight');await page.getByRole('heading',{name:'Encore une tentative ?',exact:true}).waitFor();await page.keyboard.up('ArrowRight');
 // Offline reload and a complete playable level with no server resources.
 await context.setOffline(true);await page.reload();await page.getByRole('button',{name:'Jouer la campagne →',exact:true}).waitFor();await page.getByRole('textbox',{name:'Code du défi'}).fill(shortCode);await page.getByRole('button',{name:'Jouer ce code',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).waitFor();await page.keyboard.down('ArrowRight');await page.getByRole('heading',{name:'Défi relevé !',exact:true}).waitFor();await page.keyboard.up('ArrowRight');
 await context.setOffline(false);await page.locator('#home').click();await page.getByRole('button',{name:'Défi du jour',exact:true}).click();await page.locator('#mode-label').filter({hasText:'ARCADE'}).waitFor();await page.keyboard.press(' ');await page.waitForFunction(()=>!document.querySelector('#hud').textContent.includes('Esquive prête'));await page.screenshot({path:'test-results/arcade.png',fullPage:true});
 await page.locator('#home').click();await page.setViewportSize({width:390,height:844});await page.screenshot({path:'test-results/mobile-menu.png',fullPage:true});
 await page.getByRole('button',{name:'Jouer la campagne →',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).waitFor();await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await page.screenshot({path:'test-results/mobile-game.png',fullPage:true});
 const right=page.getByRole('button',{name:'Droite',exact:true});await right.scrollIntoViewIfNeeded();const rb=await right.boundingBox();const cdp=await context.newCDPSession(page);await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:rb.x+rb.width/2,y:rb.y+rb.height/2}]});await page.waitForFunction(()=>document.querySelector('#hud').textContent.includes('500 pts'));await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 assert.equal(await page.locator('canvas').count(),1);assert.deepEqual(errors,[]);console.log('PASS: real Chromium, campaign movement, pause, editor, undo/redo, library, P4 import, win/loss/replay, offline full level, arcade dash, mobile layout and pointer control.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});




