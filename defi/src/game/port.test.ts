import { describe, expect, it } from 'vitest';
import { campaignLevel, demoLevel, paint, validateLevel, emptyLevel } from './levels';
import { encodeLevel, decodeLevel } from './codec';
import { PythonRandom, normalizeCode, codeSeed, dailyCode } from './random';
import { PlatformRun } from './platform';
import { ArcadeRun } from './arcade';
import { Saves } from '../storage';
import fixture from './fixtures/python.json';
const idle = { x: 0, y: 0, jump: false, pressed: false, run: false };
const flat = () => { const l = emptyLevel(); l.tiles[10].fill(1); return l; };
describe('Parité du Python', () => {
    it('reproduit exactement la démo et les 12 cartes de campagne', () => {
        expect(demoLevel()).toEqual(fixture.levels[0]);
        for (let n = 1; n <= 12; n++) {
            const level = campaignLevel(n);
            validateLevel(level);
            expect(level).toEqual(fixture.levels[n]);
        }
    });
    it.each(fixture.random)('reproduit les tirages CPython pour $seed', ({ seed, values, integers }) => {
        const rng = new PythonRandom(seed);
        expect(values.map(() => rng.random())).toEqual(values);
        expect(integers.map(() => rng.int(20, 980))).toEqual(integers);
    });
    it('importe tous les codes P4 Python et réexporte sans perte', async () => {
        for (let i = 0; i < fixture.codes.length; i++) {
            const level = await decodeLevel(fixture.codes[i]);
            expect(level).toEqual(fixture.levels[i]);
            expect(await decodeLevel(await encodeLevel(level))).toEqual(level);
        }
    });
    it('accepte les anciens codes P1/P2/P3', async () => {
        const l = demoLevel();
        for (const version of [1, 2, 3]) {
            const raw = version === 1 ? new TextEncoder().encode(JSON.stringify(l)) : new Uint8Array([...l.tiles.flat(), ...l.start, ...l.goal, ...(version === 3 ? [0, l.monstres.length, ...l.monstres.flat()] : [])]);
            const bytes = new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(new CompressionStream('deflate'))).arrayBuffer());
            const code = `P${version}-` + btoa(String.fromCharCode(...bytes)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
            expect(await decodeLevel(code)).toEqual({ ...l, monstres: version === 2 ? [] : l.monstres });
        }
    });
    it('valide les codes arcade et calcule le défi du jour', async () => { expect(normalizeCode('ab-cd')).toBe('ABCD'); expect(codeSeed('AAAA')).toBe(0); expect(() => normalizeCode('abc')).toThrow(); expect(await dailyCode(new Date(2026, 9, 24))).toHaveLength(4); });
});
describe('Édition et validation', () => {
    it('protège départ/arrivée et ajoute un support au nouveau départ', () => { const l = demoLevel(); expect(paint(l, 1, 9, 3)).toEqual(l); const next = paint(l, 5, 4, 8); validateLevel(next); expect(next.start).toEqual([5, 4]); expect(next.tiles[5][5]).toBe(1); expect(l.start).toEqual([1, 9]); });
    it('enlève un monstre avant le bloc et refuse les doublons', () => { let l = paint(demoLevel(), 4, 8, 10); l = paint(l, 4, 8, 10); expect(l.monstres.filter(p => p[0] === 4)).toHaveLength(1); l = paint(l, 4, 8, 0); expect(l.tiles[8][4]).toBe(2); });
    it('rejette positions, biomes, types et bombes compressées', async () => {
        const l = demoLevel();
        l.tiles[9][1] = 1;
        expect(() => validateLevel(l)).toThrow();
        for (const code of ['P4-!', 'P4-', 'P4-' + 'a'.repeat(2000), 'P4-eAAA'])
            await expect(decodeLevel(code)).rejects.toThrow();
        const bytes = new Uint8Array(await new Response(new Blob([new Uint8Array(10000)]).stream().pipeThrough(new CompressionStream('deflate'))).arrayBuffer());
        await expect(decodeLevel('P4-' + btoa(String.fromCharCode(...bytes)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, ''))).rejects.toThrow();
    });
});
describe('Parcours', () => {
    it('atterrit, saute avec hauteur variable et traverse la plateforme par dessous', () => {
        const l = flat();
        l.tiles[7][1] = 2;
        const a = new PlatformRun(l), b = new PlatformRun(l);
        for (let i = 0; i < 30; i++) {
            a.step(idle, 1 / 120);
            b.step(idle, 1 / 120);
        }
        expect(a.grounded).toBe(true);
        a.step({ ...idle, jump: true, pressed: true }, 1 / 120);
        b.step({ ...idle, pressed: true }, 1 / 120);
        for (let i = 0; i < 35; i++) {
            a.step({ ...idle, jump: true }, 1 / 120);
            b.step(idle, 1 / 120);
        }
        expect(a.player.y).toBeLessThan(b.player.y);
        expect(a.player.y).toBeLessThan(7 * 48);
    });
    it('accorde une collecte et un checkpoint une seule fois, conserve les objets à la mort', () => {
        const l = flat();
        l.tiles[9][2] = 6;
        l.tiles[9][3] = 4;
        const r = new PlatformRun(l);
        r.player.x = 106;
        r.step(idle, .01);
        r.step(idle, .01);
        expect(r.score).toBe(500);
        r.player.x = 154;
        r.step(idle, .01);
        r.step(idle, .01);
        expect(r.score).toBe(750);
        r.hurt();
        expect(r.player.x).toBe(154);
        expect(r.collected.has('2,9')).toBe(true);
        expect(r.lives).toBe(2);
        expect(l.tiles[9][2]).toBe(6);
    });
    it('borne les vies, rebondit sur ressort, perd et ne change plus après la fin', () => {
        const l = flat();
        l.tiles[9][2] = 7;
        l.tiles[9][3] = 5;
        const r = new PlatformRun(l);
        r.lives = 5;
        r.player.x = 106;
        r.step(idle, .01);
        expect(r.lives).toBe(5);
        r.player.x = 154;
        r.step(idle, .01);
        expect(r.vy).toBe(-690);
        for (let i = 0; i < 5; i++)
            r.hurt();
        expect(r.status).toBe('lost');
        const time = r.time;
        r.step(idle, 1);
        r.hurt();
        expect(r.time).toBe(time);
        expect(r.lives).toBe(0);
    });
    it('gagne sans imposer les gemmes et ne récompense pas deux fois', () => { const l = flat(); l.tiles[9][4] = 6; const r = new PlatformRun(l); r.player.x = 38 * 48; r.step(idle, .01); expect(r.status).toBe('won'); const score = r.score; r.step(idle, 1); expect(r.score).toBe(score); });
    it('termine un parcours complet uniquement avec les commandes de déplacement', () => {
        const r = new PlatformRun(flat());
        let steps = 0;
        while (r.status === 'playing' && steps++ < 120 * 15)
            r.step({ ...idle, x: 1, run: true }, 1 / 120);
        expect(r.status).toBe('won');
        expect(r.lives).toBe(3);
    });
});
describe('Arcade', () => {
    it('est reproductible, réinitialisable et limite les fragments à deux', () => {
        const a = new ArcadeRun('ABCD'), b = new ArcadeRun('ABCD');
        for (let i = 0; i < 1500; i++) {
            a.step(idle, 1 / 120);
            b.step(idle, 1 / 120);
        }
        expect(a).toEqual(b);
        expect(a.gems.length).toBeLessThanOrEqual(2);
        expect(new ArcadeRun('ABCD').time).toBe(0);
    });
    it('termine à 45 secondes et compte le bonus une seule fois', () => { const a = new ArcadeRun('ABCD'); a.invulnerable = 100; for (let i = 0; i < 5401; i++)
        a.step(idle, 1 / 120); expect(a.status).toBe('won'); const score = a.score; a.step(idle, 1); expect(a.score).toBe(score); });
    it('applique collision, esquive, combo et défaite', () => {
        const a = new ArcadeRun('ABCD');
        a.invulnerable = 0;
        a.gems = [{ x: a.x, y: a.y }];
        a.step(idle, .01);
        expect(a.fragments).toBe(1);
        expect(a.score).toBe(150);
        a.gems = [{ x: a.x, y: a.y }];
        a.step(idle, .01);
        expect(a.score).toBe(330);
        a.step({ ...idle, pressed: true }, .01);
        expect(a.cooldown).toBeGreaterThan(1);
        expect(a.dash).toBeGreaterThan(0);
        a.dash = 0;
        a.invulnerable = 0;
        a.lives = 1;
        a.projectiles = [{ x: a.x, y: a.y, vx: 0, vy: 0, r: 10, kind: 0, delay: 0 }];
        a.step(idle, .01);
        expect(a.status).toBe('lost');
    });
});
describe('Sauvegarde', () => {
    it('recharge un brouillon temporairement injouable sans le perdre', () => { let value: string | null = null; const storage = { getItem: () => value, setItem: (_: string, v: string) => { value = v; } }, s = new Saves(storage); const level = demoLevel(); level.tiles[10][1] = 0; s.save({ id: 'draft', name: 'En cours', level }); const next = new Saves(storage); expect(next.data.levels[0].level).toEqual(level); expect(() => validateLevel(next.data.levels[0].level)).toThrow(); });
    it('conserve meilleurs scores et temps et recharge la bibliothèque', () => { let value: string | null = null; const storage = { getItem: () => value, setItem: (_: string, v: string) => { value = v; } }, s = new Saves(storage); s.record('a', 20); s.record('a', 10); s.record('t', 20, true); s.record('t', 10, true); s.save({ id: 'a', name: 'Test', level: demoLevel() }); const next = new Saves(storage); expect(next.data.records).toEqual({ a: 20, t: 10 }); expect(next.data.levels).toHaveLength(1); });
    it('préserve les données inconnues ou corrompues et absorbe les quotas', () => { let writes = 0; for (const value of ['broken', '{"version":9}']) {
        const s = new Saves({ getItem: () => value, setItem: () => { writes++; } });
        s.record('a', 5);
        expect(s.warning).not.toBe('');
    } expect(writes).toBe(0); const s = new Saves({ getItem: () => null, setItem: () => { throw Error('quota'); } }); expect(() => s.record('a', 1)).not.toThrow(); expect(s.warning).toContain('Stockage'); });
});
