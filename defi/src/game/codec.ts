import { COLS, ROWS, THEMES, validateLevel } from './levels';
import type { Level } from './levels';
async function transform(bytes: Uint8Array<ArrayBuffer>, decompress: boolean): Promise<Uint8Array<ArrayBuffer>> {
    const stream = new Blob([bytes]).stream().pipeThrough(decompress ? new DecompressionStream('deflate') : new CompressionStream('deflate'));
    const reader = stream.getReader(), chunks: Uint8Array[] = [];
    let size = 0;
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done)
                break;
            size += value.length;
            if (size > 5000)
                throw Error('Carte trop volumineuse.');
            chunks.push(value);
        }
    }
    finally {
        await reader.cancel();
    }
    const out = new Uint8Array(size);
    let at = 0;
    for (const c of chunks) {
        out.set(c, at);
        at += c.length;
    }
    return out;
}
export async function encodeLevel(l: Level): Promise<string> {
    validateLevel(l);
    const bytes = new Uint8Array([...l.tiles.flat(), ...l.start, ...l.goal, l.monstres.length >> 8, l.monstres.length & 255, ...l.monstres.flat(), THEMES.indexOf(l.theme)]);
    return 'P4-' + btoa(String.fromCharCode(...await transform(bytes, false))).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
}
export async function decodeLevel(input: string): Promise<Level> {
    const code = input.trim(), version = code.slice(0, 3).toUpperCase();
    if (!/^P[1-4]-$/i.test(version) || code.length > 2000 || !code.slice(3) || !/^[\w-]+$/.test(code.slice(3)))
        throw Error('Code de parcours non reconnu.');
    try {
        const bytes = await transform(Uint8Array.from(atob(code.slice(3).replaceAll('-', '+').replaceAll('_', '/')), c => c.charCodeAt(0)), true);
        let l: Level;
        if (version === 'P1-') {
            const data: unknown = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
            if (!data || typeof data !== 'object' || Array.isArray(data))
                throw Error();
            const candidate = { monstres: [], theme: 'prairie', ...data };
            validateLevel(candidate);
            l = candidate;
        }
        else {
            const base = COLS * ROWS + 4, themeSize = Number(version === 'P4-'), count = version === 'P2-' ? 0 : (bytes[base] << 8 | bytes[base + 1]);
            if (bytes.length !== (version === 'P2-' ? base : base + 2 + count * 2 + themeSize))
                throw Error();
            l = { tiles: Array.from({ length: ROWS }, (_, r) => Array.from(bytes.slice(r * COLS, (r + 1) * COLS))), start: [bytes[440], bytes[441]], goal: [bytes[442], bytes[443]], monstres: [], theme: themeSize ? THEMES[bytes[bytes.length - 1]] : 'prairie' };
            for (let i = 0; i < count; i++)
                l.monstres.push([bytes[base + 2 + i * 2], bytes[base + 3 + i * 2]]);
        }
        validateLevel(l);
        return l;
    }
    catch {
        throw Error('Le code contient une carte invalide, incomplète ou abîmée.');
    }
}
