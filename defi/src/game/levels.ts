export const COLS = 40, ROWS = 11, TILE = 48;
export const THEMES = ['prairie', 'volcan', 'glace', 'desert'] as const;
export type Theme = typeof THEMES[number];
export type Point = [
    number,
    number
];
export interface Level {
    tiles: number[][];
    start: Point;
    goal: Point;
    monstres: Point[];
    theme: Theme;
}
export const same = (a: Point, b: Point) => a[0] === b[0] && a[1] === b[1];
export const clone = (level: Level): Level => structuredClone(level);
export function emptyLevel(): Level {
    return { tiles: Array.from({ length: ROWS }, () => Array<number>(COLS).fill(0)), start: [1, 9], goal: [38, 9], monstres: [], theme: 'prairie' };
}
// Python round uses ties to even, unlike Math.round.
export function pyRound(n: number): number { const f = Math.floor(n); return n - f === .5 ? f + f % 2 : Math.round(n); }
export function demoLevel(): Level {
    const l = emptyLevel(), holes = [8, 9, 17, 18, 26, 27, 34];
    for (let c = 0; c < COLS; c++)
        if (!holes.includes(c))
            l.tiles[10][c] = 1;
    for (const [c, r] of [[3, 8], [4, 8], [5, 8], [8, 8], [11, 8], [12, 8], [14, 7], [15, 7], [17, 8], [20, 8], [21, 8], [22, 8], [24, 7], [25, 7], [27, 8], [29, 8], [30, 8], [31, 8], [32, 7], [33, 7], [34, 8], [36, 8], [37, 8]])
        l.tiles[r][c] = 2;
    for (const c of [5, 12, 15, 21, 25, 32])
        l.tiles[9][c] = 3;
    for (const [c, r] of [[4, 7], [12, 7], [15, 6], [21, 7], [25, 6], [30, 7], [33, 6], [37, 7]])
        l.tiles[r][c] = 6;
    for (const c of [2, 10, 20, 28, 35])
        l.tiles[9][c] = 6;
    for (const c of [3, 36])
        l.tiles[9][c] = 7;
    for (const c of [13, 29])
        l.tiles[9][c] = 4;
    l.tiles[9][19] = 5;
    l.monstres = [[6, 9], [14, 9], [23, 9], [31, 9]];
    return l;
}
const nearest = (values: number[], target: number) => values.sort((a, b) => Math.abs(a - target) - Math.abs(b - target) || a - b)[0];
export function campaignLevel(number: number): Level {
    const n = Math.max(1, Math.min(12, Math.trunc(number))), l = emptyLevel(), holes = new Set<number>();
    const count = 1 + Math.floor((n - 1) / 2);
    for (let i = 0; i < count; i++) {
        const start = pyRound(8 + i * 24 / Math.max(1, count - 1)), width = 1 + Number(n >= 7 && i % 2 === 0);
        for (let c = start; c < Math.min(38, start + width); c++)
            holes.add(c);
    }
    for (let c = 0; c < COLS; c++)
        if (!holes.has(c))
            l.tiles[10][c] = 1;
    const spikes: number[] = [], candidates = Array.from({ length: 32 }, (_, i) => i + 4).filter(c => !holes.has(c));
    for (let i = 0; i < Math.min(14, n + 2); i++) {
        let available = candidates.filter(c => !spikes.includes(c) && spikes.every(p => Math.abs(c - p) >= 2));
        if (!available.length)
            available = candidates.filter(c => !spikes.includes(c));
        if (!available.length)
            break;
        const c = nearest(available, pyRound(4 + i * 31 / Math.max(1, Math.min(14, n + 2) - 1)));
        spikes.push(c);
        l.tiles[9][c] = 3;
    }
    const monsters = 1 + Math.floor(n / 2), positions = Array.from({ length: 30 }, (_, i) => i + 5).filter(c => !holes.has(c) && !spikes.includes(c));
    for (let i = 0; i < monsters; i++) {
        let available = positions.filter(c => l.monstres.every(p => Math.abs(c - p[0]) >= 3));
        if (!available.length)
            available = positions.filter(c => l.monstres.every(p => c !== p[0]));
        if (!available.length)
            break;
        const c = nearest(available, pyRound(5 + i * 29 / Math.max(1, monsters - 1)));
        l.monstres.push([c, 9]);
        positions.splice(positions.indexOf(c), 1);
    }
    const platforms = Math.floor(n / 2);
    for (let i = 0; i < platforms; i++) {
        const available = candidates.filter(c => l.tiles[8][c] === 0);
        if (available.length)
            l.tiles[8][nearest(available, pyRound(6 + i * 28 / Math.max(1, platforms - 1)))] = 2;
    }
    l.tiles[9][2] = l.tiles[9][37] = 6;
    const safe = Array.from({ length: 25 }, (_, i) => i + 8).filter(c => !holes.has(c) && !spikes.includes(c) && !l.monstres.some(p => p[0] === c));
    for (let i = 0; i < Math.min(2, Math.floor(n / 6)); i++)
        if (safe.length) {
            const c = nearest(safe, i === 0 ? 13 : 27);
            l.tiles[9][c] = 4;
            safe.splice(safe.indexOf(c), 1);
        }
    if (n >= 5)
        l.tiles[9][3] = l.tiles[9][36] = 7;
    return l;
}
export function validateLevel(value: unknown, playable = true): asserts value is Level {
    if (!value || typeof value !== 'object')
        throw Error('Carte invalide.');
    const l = value as Partial<Level>;
    if (!THEMES.includes(l.theme as Theme))
        throw Error('Biome inconnu.');
    if (!Array.isArray(l.tiles) || l.tiles.length !== ROWS || l.tiles.some(r => !Array.isArray(r) || r.length !== COLS || r.some(t => !Number.isInteger(t) || t < 0 || t > 7)))
        throw Error('La carte doit contenir 40 × 11 blocs valides.');
    const point = (p: unknown): p is Point => Array.isArray(p) && p.length === 2 && p.every(Number.isInteger) && p[0] >= 0 && p[0] < COLS && p[1] >= 0 && p[1] < ROWS;
    if (!point(l.start) || !point(l.goal))
        throw Error('Départ ou arrivée hors de la carte.');
    const [c, r] = l.start;
    if (playable && (r >= 10 || l.tiles[r][c] !== 0 || ![1, 2].includes(l.tiles[r + 1][c])))
        throw Error('Le départ doit être libre et posé sur un sol sûr.');
    if (same(l.start, l.goal) || (playable && ![0, 4].includes(l.tiles[l.goal[1]][l.goal[0]])))
        throw Error('Arrivée invalide.');
    if (!Array.isArray(l.monstres) || l.monstres.length > 440)
        throw Error('Liste de monstres invalide.');
    const used = new Set<string>();
    for (const p of l.monstres) {
        if (!point(p) || same(p, l.start) || same(p, l.goal) || used.has(p.join(',')))
            throw Error('Position de monstre invalide ou dupliquée.');
        used.add(p.join(','));
    }
}
export function paint(level: Level, c: number, r: number, tool: number): Level {
    const l = clone(level);
    if (c < 0 || c >= COLS || r < 0 || r >= ROWS)
        return l;
    if (tool === 8)
        r = Math.min(9, r);
    const p: Point = [c, r];
    if (tool === 8 || tool === 9) {
        if (same(p, tool === 8 ? l.goal : l.start) || l.monstres.some(m => same(p, m)))
            return l;
        l[tool === 8 ? 'start' : 'goal'] = p;
        l.tiles[r][c] = 0;
        if (tool === 8 && ![1, 2].includes(l.tiles[r + 1][c]))
            l.tiles[r + 1][c] = 1;
    }
    else if (!same(p, l.start) && !same(p, l.goal)) {
        if (tool === 10) {
            if (!l.monstres.some(m => same(p, m)))
                l.monstres.push(p);
        }
        else {
            const has = l.monstres.some(m => same(p, m));
            l.monstres = l.monstres.filter(m => !same(p, m));
            if (!(tool === 0 && has))
                l.tiles[r][c] = tool;
        }
    }
    return l;
}
