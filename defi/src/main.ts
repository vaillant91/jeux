import Phaser from 'phaser';
import { registerSW } from 'virtual:pwa-register';
import './style.css';
import { campaignLevel, demoLevel, clone, paint, validateLevel } from './game/levels';
import type { Level, Theme } from './game/levels';
import { encodeLevel, decodeLevel } from './game/codec';
import { newCode, dailyCode } from './game/random';
import { PlatformRun } from './game/platform';
import { ArcadeRun } from './game/arcade';
import { Saves } from './storage';
const $ = <T extends HTMLElement = HTMLElement>(id: string) => { const el = document.getElementById(id); if (!el)
    throw Error(`Élément absent : ${id}`); return el as T; };
const button = (text: string, action: () => void | Promise<void>, primary = false) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.className = primary ? 'primary' : ''; b.onclick = () => { Promise.resolve().then(action).catch(report); }; return b; };
const report = (e: unknown) => { $('message').textContent = e instanceof Error ? e.message : String(e); };
let storage: Pick<Storage, 'getItem' | 'setItem'>;
try {
    storage = localStorage;
}
catch {
    storage = { getItem: () => null, setItem: () => { throw Error(); } };
}
const saves = new Saves(storage);
let mode: 'menu' | 'play' | 'editor' | 'result' = 'menu', paused = false, run: PlatformRun | ArcadeRun | null = null, campaign = 0, fromEditor = false;
let draft = demoLevel(), draftId: string = crypto.randomUUID(), draftName = 'Mon parcours', tool = 1, editorCamera = 0, history: Level[] = [], redo: Level[] = [];
let currentLevel = demoLevel(), currentCode = '', resultShown = false, accumulator = 0;
const held = new Set<string>(), pointers = new Map<number, string>();
let pressed = false;
const palette = ['Gomme', 'Sol', 'Plateforme', 'Pics', 'Checkpoint', 'Ressort', 'Gemme', 'Cœur', 'Départ', 'Arrivée', 'Monstre'];
const colors: Record<Theme, number[]> = { prairie: [0x142e35, 0x76dca1, 0x325e51], volcan: [0x301c2d, 0xff945e, 0x644044], glace: [0x203e63, 0xb2efff, 0x4a7e9c], desert: [0x583c49, 0xffd48b, 0xaa7955] };
function release() { held.clear(); pointers.clear(); pressed = false; }
function setMode(next: typeof mode) { mode = next; paused = false; release(); $('panel').hidden = next === 'play'; $('editor').hidden = next !== 'editor'; $('touch').hidden = next !== 'play'; $('pause').hidden = next !== 'play'; $('pause').textContent = 'Pause'; $('pause-note').hidden = true; $('back-editor').hidden = !(next === 'play' && fromEditor); $('message').textContent = saves.warning; accumulator = 0; requestAnimationFrame(() => { game.scale.getParentBounds(); game.scale.refresh(); }); }
function panel(title: string, copy: string, actions: HTMLButtonElement[]) { $('panel-title').textContent = title; $('panel-copy').textContent = copy; $('actions').replaceChildren(...actions); $('extras').replaceChildren(); $('panel').hidden = false; }
function menu() {
    setMode('menu');
    run = null;
    panel('Un code. Un défi. À toi de jouer.', 'Crée un parcours, partage son code et défie tes amis. Ou tiens 45 secondes dans l’arène.', [
        button('Jouer la campagne →', () => startLevel(campaignLevel(1), 1), true), button('Défi du jour', async () => startArcade(await dailyCode())), button('Arcade aléatoire', () => startArcade(newCode())), button('Créer un parcours', () => openEditor()), button('Mes parcours', library), button('Parcours démo', () => startLevel(demoLevel()))
    ]);
    const form = document.createElement('form'), input = document.createElement('textarea');
    input.placeholder = 'Code arcade ou parcours P1–P4…';
    input.maxLength = 2000;
    input.rows = 2;
    input.setAttribute('aria-label', 'Code du défi');
    form.append(input, button('Jouer ce code', async () => { if (/^P[1-4]-/i.test(input.value.trim()))
        await startLevel(await decodeLevel(input.value));
    else
        startArcade(input.value); }));
    form.onsubmit = e => e.preventDefault();
    $('extras').append(form);
}
function library() { setMode('menu'); panel('Mes parcours', 'Les cartes restent dans ce navigateur. Exporte un code pour les partager ou les sauvegarder ailleurs.', [button('Nouveau parcours', () => openEditor(), true), button('Retour', menu)]); for (const item of saves.data.levels)
    $('extras').append(button(item.name, () => openEditor(item.level, item.id, item.name))); }
function openEditor(level = demoLevel(), id: string = crypto.randomUUID(), name = 'Mon parcours') { draft = clone(level); draftId = id; draftName = name; history = []; redo = []; editorCamera = 0; $<HTMLInputElement>('editor-scroll').value = '0'; setMode('editor'); $('panel').hidden = true; $<HTMLInputElement>('level-name').value = name; $<HTMLSelectElement>('theme').value = draft.theme; saveDraft(); }
function saveDraft() { const ok = saves.save({ id: draftId, name: draftName, level: draft }); $('message').textContent = ok ? 'Brouillon enregistré dans ce navigateur.' : saves.warning; }
function remember() { history.push(clone(draft)); if (history.length > 40)
    history.shift(); redo = []; }
function edit(c: number, r: number, erase = false) { const next = paint(draft, c, r, erase ? 0 : tool); if (JSON.stringify(next) !== JSON.stringify(draft)) {
    remember();
    draft = next;
    saveDraft();
} }
function undo() { if (history.length) {
    redo.push(clone(draft));
    draft = history.pop()!;
    $<HTMLSelectElement>('theme').value = draft.theme;
    saveDraft();
} }
function redoEdit() { if (redo.length) {
    history.push(clone(draft));
    draft = redo.pop()!;
    $<HTMLSelectElement>('theme').value = draft.theme;
    saveDraft();
} }
async function startLevel(level: Level, n = 0, editor = false) { validateLevel(level); const code = await encodeLevel(level); currentLevel = clone(level); currentCode = code; campaign = n; fromEditor = editor; run = new PlatformRun(level); resultShown = false; setMode('play'); $('instructions').textContent = '← → / Q D : avancer · Espace / ↑ : sauter · Maj : courir · P : pause'; $('mode-label').textContent = n ? `CAMPAGNE · ${String(n).padStart(2, '0')} / 12` : 'PARCOURS LIBRE'; }
function startArcade(code: string) { run = new ArcadeRun(code); currentCode = run.code; campaign = 0; fromEditor = false; resultShown = false; setMode('play'); $('instructions').textContent = 'Flèches / ZQSD / WASD : bouger · Espace : esquive · P : pause'; $('mode-label').textContent = `ARCADE · ${run.code}`; }
function togglePause() { if (mode !== 'play')
    return; paused = !paused; release(); $('pause').textContent = paused ? 'Reprendre' : 'Pause'; $('pause-note').hidden = !paused; }
function restart() { if (run instanceof ArcadeRun)
    startArcade(currentCode);
else
    void startLevel(currentLevel, campaign, fromEditor); }
function showResult() {
    if (!run || resultShown)
        return;
    resultShown = true;
    const won = run.status === 'won', platform = run instanceof PlatformRun;
    let record = '';
    if (platform && won) {
        const best = saves.record('level:' + JSON.stringify(currentLevel), Math.round(run.time * 1000), true);
        record = `Meilleur temps : ${(best / 1000).toFixed(2)} s.`;
    }
    else if (!platform) {
        record = `Record local : ${saves.record('arcade:' + currentCode, run.score)} points.`;
    }
    setMode('result');
    panel(won ? 'Défi relevé !' : 'Encore une tentative ?', `${run.score} points · ${run.time.toFixed(2)} s. ${record}`, [button(won && campaign ? 'Niveau suivant →' : 'Rejouer', () => won && campaign ? startLevel(campaignLevel(campaign === 12 ? 1 : campaign + 1), campaign === 12 ? 1 : campaign + 1) : restart(), true), ...(won && campaign ? [button('Rejouer ce niveau', restart)] : []), button('Partager le code', () => share(currentCode)), ...(fromEditor ? [button('Retour à l’éditeur', returnEditor)] : []), button('Accueil', menu)]);
}
function returnEditor() { setMode('editor'); $('panel').hidden = true; }
function share(code: string) { $<HTMLTextAreaElement>('share-code').value = code; $<HTMLDialogElement>('share-dialog').showModal(); }
class DefiScene extends Phaser.Scene {
    private g!: Phaser.GameObjects.Graphics;
    private cameraX = 0;
    create() { this.g = this.add.graphics(); this.input.mouse?.disableContextMenu(); this.input.on('pointerdown', (p: Phaser.Input.Pointer) => this.paintPointer(p)); this.input.on('pointermove', (p: Phaser.Input.Pointer) => { if (p.isDown)
        this.paintPointer(p); }); menu(); }
    private paintPointer(p: Phaser.Input.Pointer) { if (mode === 'editor')
        edit(Math.floor((p.x - 24 + editorCamera) / 48), Math.floor((p.y - 112) / 48), p.rightButtonDown()); }
    update(_time: number, delta: number) {
        if (mode === 'play' && run && !paused) {
            accumulator += Math.min(delta / 1000, .05);
            while (accumulator >= 1 / 120) {
                const active = (...keys: string[]) => keys.some(k => held.has(k) || [...pointers.values()].includes(k));
                run.step({ x: Number(active('ArrowRight', 'd')) - Number(active('ArrowLeft', 'a', 'q')), y: Number(active('ArrowDown', 's')) - Number(active('ArrowUp', 'w', 'z')), jump: active(' ', 'ArrowUp', 'w', 'z'), pressed, run: active('Shift') }, 1 / 120);
                pressed = false;
                accumulator -= 1 / 120;
                if (run.status !== 'playing') {
                    showResult();
                    break;
                }
            }
        }
        this.draw();
        if (run && (mode === 'play' || mode === 'result')) {
            $('hud').textContent = `${'♥'.repeat(run.lives)}  ·  ${run.score} pts  ·  ${run instanceof ArcadeRun ? (45 - run.time).toFixed(1) : run.time.toFixed(1)} s${run instanceof ArcadeRun ? `  ·  Esquive ${run.cooldown <= 0 ? 'prête' : run.cooldown.toFixed(1) + ' s'}` : `  ·  ${run.gems} gemmes`}`;
        }
        else
            $('hud').textContent = mode === 'editor' ? '40 × 11 cases · Peins ton défi' : '3 vies · Des défis à partager';
    }
    private block(c: number, r: number, t: number, x: number, y: number, theme: Theme) {
        const g = this.g, p = colors[theme];
        if (t === 1) {
            g.fillStyle(p[2]).fillRoundedRect(x, y, 48, 48, 3);
            g.fillStyle(p[1]).fillRect(x, y, 48, 7);
            g.lineStyle(1, 0xffffff, .07).lineBetween(x + 8, y + 24, x + 29, y + 24);
        }
        if (t === 2) {
            g.fillStyle(p[1]).fillRoundedRect(x, y, 48, 10, 4);
            g.fillStyle(p[2]).fillRect(x + 5, y + 10, 38, 6);
        }
        if (t === 3) {
            g.fillStyle(0xff7586);
            for (let i = 0; i < 3; i++)
                g.fillTriangle(x + 4 + i * 14, y + 47, x + 11 + i * 14, y + 14, x + 18 + i * 14, y + 47);
        }
        if (t === 4) {
            g.lineStyle(3, 0xe3fff4).lineBetween(x + 14, y + 47, x + 14, y + 8);
            g.fillStyle(run instanceof PlatformRun && run.checkpoints.has(`${c},${r}`) ? 0xf8d87a : 0x75e9b9).fillTriangle(x + 15, y + 8, x + 39, y + 18, x + 15, y + 28);
        }
        if (t === 5) {
            g.lineStyle(4, 0xffd375);
            for (let i = 0; i < 3; i++)
                g.strokeRect(x + 10, y + 20 + i * 8, 28, 7);
            g.fillStyle(0xffd375).fillRoundedRect(x + 5, y + 13, 38, 8, 3);
        }
        if (t === 6) {
            g.fillStyle(0x75eee4).fillTriangle(x + 24, y + 8, x + 10, y + 23, x + 38, y + 23).fillTriangle(x + 10, y + 23, x + 38, y + 23, x + 24, y + 40);
            g.lineStyle(1, 0xdffffb).lineBetween(x + 24, y + 8, x + 24, y + 39);
        }
        if (t === 7) {
            g.fillStyle(0xff7b9c).fillCircle(x + 17, y + 20, 9).fillCircle(x + 31, y + 20, 9).fillTriangle(x + 9, y + 23, x + 39, y + 23, x + 24, y + 40);
        }
    }
    private monster(x: number, y: number) { const g = this.g; g.fillStyle(0xb198ec).fillRoundedRect(x, y, 34, 34, 10); g.fillStyle(0xffffff).fillCircle(x + 10, y + 12, 5).fillCircle(x + 24, y + 12, 5); g.fillStyle(0x25263f).fillCircle(x + 11, y + 13, 2).fillCircle(x + 25, y + 13, 2); g.lineStyle(2, 0x25263f).lineBetween(x + 11, y + 25, x + 24, y + 25); }
    private hero(x: number, y: number, invulnerable: number) { const g = this.g, alpha = invulnerable > 0 ? .55 : 1; g.fillStyle(0xf6db80, alpha).fillRoundedRect(x, y, 28, 38, 9); g.fillStyle(0x183e4b, alpha).fillRoundedRect(x + 4, y + 8, 22, 12, 4); g.fillStyle(0xb4fff2).fillRect(x + 16, y + 10, 6, 5); g.fillStyle(0xfef3c9, alpha).fillRect(x + 3, y + 31, 7, 7).fillRect(x + 18, y + 31, 7, 7); }
    private draw() {
        const g = this.g;
        g.clear();
        const isArcade = run instanceof ArcadeRun && (mode === 'play' || mode === 'result'), level = mode === 'editor' ? draft : mode === 'menu' ? demo : currentLevel, p = colors[level.theme];
        g.fillStyle(isArcade ? 0x101c32 : p[0]).fillRect(0, 0, 1000, 700);
        for (let i = 0; i < 65; i++) {
            g.fillStyle(0xd4f3ee, .15 + (i % 3) * .1).fillCircle((i * 137 + 53) % 1000, (i * 71 + 23) % 470, 1 + i % 2);
        }
        if (isArcade && run instanceof ArcadeRun) {
            g.lineStyle(2, 0x47677b, .5).strokeRoundedRect(24, 104, 952, 574, 20);
            for (const gem of run.gems)
                this.block(0, 0, 6, gem.x - 24, gem.y - 24, 'prairie');
            for (const bullet of run.projectiles) {
                const color = [0xff8392, 0xffc878, 0xc6a4ff][bullet.kind];
                g.fillStyle(color, bullet.delay > 0 ? .25 : 1).fillCircle(bullet.x, bullet.y, bullet.r);
                g.lineStyle(2, color, .4).strokeCircle(bullet.x, bullet.y, bullet.r + 5);
            }
            this.hero(run.x - 14, run.y - 19, run.invulnerable);
            if (run.dash > 0)
                g.lineStyle(3, 0x7fffe1).strokeCircle(run.x, run.y, 30);
        }
        else {
            const platform = run instanceof PlatformRun && (mode === 'play' || mode === 'result') ? run : null;
            if (mode === 'editor')
                this.cameraX = editorCamera;
            else if (platform)
                this.cameraX += (Math.max(0, Math.min(968, platform.player.x + 14 - 420 + Math.max(-42, Math.min(42, platform.vx * .12)))) - this.cameraX) * .12;
            else
                this.cameraX = 0;
            for (let i = 0; i < 6; i++) {
                const x = i * 260 - this.cameraX * .22;
                g.fillStyle(p[2], .35).fillTriangle(x - 100, 590, x + 140, 230 + (i % 3) * 40, x + 350, 590);
            }
            g.fillStyle(p[1], .1).fillCircle(800 - this.cameraX * .08, 180, 58);
            for (let r = 0; r < 11; r++)
                for (let c = 0; c < 40; c++) {
                    const x = 24 + c * 48 - this.cameraX, y = 112 + r * 48;
                    if (x < -48 || x > 1000)
                        continue;
                    if (!platform?.collected.has(`${c},${r}`))
                        this.block(c, r, level.tiles[r][c], x, y, level.theme);
                    if (mode === 'editor')
                        g.lineStyle(1, 0xffffff, .13).strokeRect(x, y, 48, 48);
                }
            const gx = 24 + level.goal[0] * 48 - this.cameraX, gy = 112 + level.goal[1] * 48;
            g.fillStyle(0x9cf3d2, .15).fillRoundedRect(gx, gy - 22, 48, 70, 20);
            g.lineStyle(4, 0x9cf3d2).strokeRoundedRect(gx + 5, gy - 18, 38, 64, 18);
            if (platform) {
                for (const m of platform.monsters)
                    this.monster(24 + m.x - this.cameraX, 112 + m.y);
                this.hero(24 + platform.player.x - this.cameraX, 112 + platform.player.y, platform.invulnerable);
            }
            else {
                for (const [c, r] of level.monstres)
                    this.monster(31 + c * 48 - this.cameraX, 120 + r * 48);
                this.hero(34 + level.start[0] * 48 - this.cameraX, 117 + level.start[1] * 48, 0);
            }
        }
    }
}
const demo = demoLevel();
const game = new Phaser.Game({ type: Phaser.AUTO, parent: 'game', width: 1000, height: 700, backgroundColor: '#142e35', scene: DefiScene, scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH }, render: { antialias: true }, input: { activePointers: 4 } });
$('home').onclick = menu;
$('pause').onclick = togglePause;
$('back-editor').onclick = returnEditor;
$('undo').onclick = undo;
$('redo').onclick = redoEdit;
$('test-level').onclick = () => void startLevel(draft, 0, true).catch(report);
$('export-level').onclick = () => void encodeLevel(draft).then(share).catch(report);
$<HTMLInputElement>('level-name').oninput = e => { draftName = (e.target as HTMLInputElement).value.slice(0, 28) || 'Mon parcours'; saveDraft(); };
$<HTMLSelectElement>('theme').onchange = e => { remember(); draft.theme = (e.target as HTMLSelectElement).value as Theme; saveDraft(); };
$<HTMLInputElement>('editor-scroll').oninput = e => { editorCamera = Number((e.target as HTMLInputElement).value); };
palette.forEach((name, i) => { const b = button(`${i === 10 ? 'M' : i} · ${name}`, () => { tool = i; for (const el of $('palette').children)
    el.setAttribute('aria-pressed', String(el === b)); }); b.setAttribute('aria-pressed', String(i === tool)); $('palette').append(b); });
$('close-share').onclick = () => $<HTMLDialogElement>('share-dialog').close();
$('copy-code').onclick = () => void navigator.clipboard.writeText($<HTMLTextAreaElement>('share-code').value).then(() => { $('copy-code').textContent = 'Code copié !'; }).catch(() => { $<HTMLTextAreaElement>('share-code').select(); $('copy-code').textContent = 'Sélectionné : copie manuellement'; });
const onKey = (e: KeyboardEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement || $<HTMLDialogElement>('share-dialog').open)
        return;
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (mode === 'editor' && e.type === 'keydown' && e.ctrlKey && (k === 'z' || k === 'y')) {
        e.preventDefault();
        if (k === 'z')
            undo();
        else
            redoEdit();
        return;
    }
    if (mode !== 'play')
        return;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(k))
        e.preventDefault();
    if (e.type === 'keydown') {
        if (!e.repeat && (k === 'p' || k === 'Escape')) {
            togglePause();
            return;
        }
        if (!paused && !held.has(k) && (k === ' ' || (run instanceof PlatformRun && ['ArrowUp', 'w', 'z'].includes(k))))
            pressed = true;
        if (!paused)
            held.add(k);
    }
    else
        held.delete(k);
};
window.addEventListener('keydown', onKey);
window.addEventListener('keyup', onKey);
const blur = () => { release(); if (mode === 'play' && !paused)
    togglePause(); };
window.addEventListener('blur', blur);
const visibility = () => { if (document.hidden)
    blur(); };
document.addEventListener('visibilitychange', visibility);
document.querySelectorAll<HTMLButtonElement>('[data-control]').forEach(b => {
    b.onpointerdown = e => { e.preventDefault(); b.setPointerCapture(e.pointerId); const key = b.dataset.control!; pointers.set(e.pointerId, key); if (key === ' ' && !paused)
        pressed = true; };
    const up = (e: PointerEvent) => pointers.delete(e.pointerId);
    b.onpointerup = up;
    b.onpointercancel = up;
    b.onlostpointercapture = up;
});
let waiting = false;
const updateSW = registerSW({ onNeedRefresh() { waiting = true; $('update').hidden = false; }, onOfflineReady() { $('pwa-status').textContent = 'Disponible hors ligne'; }, onRegisterError() { $('pwa-status').textContent = 'Hors ligne indisponible · jeu en ligne prêt'; } });
$('update').onclick = () => { if (!waiting)
    return; if (mode === 'play') {
    $('message').textContent = 'Termine la partie ou retourne à l’accueil pour appliquer la mise à jour.';
    return;
} if (mode === 'editor')
    saveDraft(); void updateSW(true); };
if (import.meta.hot)
    import.meta.hot.dispose(() => { game.destroy(true); window.removeEventListener('keydown', onKey); window.removeEventListener('keyup', onKey); window.removeEventListener('blur', blur); document.removeEventListener('visibilitychange', visibility); });
