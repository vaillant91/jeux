const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
export function normalizeCode(input: string): string {
    const code = input.toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (code.length !== 4 && code.length !== 6)
        throw Error('Le code arcade doit contenir 4 caractères (ou 6 pour un ancien code).');
    return code;
}
export function codeSeed(code: string): number { return [...normalizeCode(code)].reduce((s, c) => s * 36 + ALPHABET.indexOf(c), 0); }
export function newCode(): string { return Array.from(crypto.getRandomValues(new Uint8Array(4)), n => ALPHABET[n % 36]).join(''); }
export async function dailyCode(date = new Date()): Promise<string> {
    const text = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))).slice(0, 4), n => ALPHABET[n % 36]).join('');
}
// CPython integer seed + MT19937, random() and rejection-based randrange.
// This preserves the Python challenge's random stream, not only its seed label.
export class PythonRandom {
    private mt = new Uint32Array(624);
    private index = 624;
    constructor(seed: number) {
        const key = [seed >>> 0];
        if (seed > 0xffffffff)
            key.push(Math.floor(seed / 4294967296) >>> 0);
        this.mt[0] = 19650218;
        for (let i = 1; i < 624; i++)
            this.mt[i] = (Math.imul(1812433253, this.mt[i - 1] ^ (this.mt[i - 1] >>> 30)) + i) >>> 0;
        let i = 1, j = 0;
        for (let k = 624; k > 0; k--) {
            this.mt[i] = ((this.mt[i] ^ Math.imul(this.mt[i - 1] ^ (this.mt[i - 1] >>> 30), 1664525)) + key[j] + j) >>> 0;
            i++;
            j++;
            if (i >= 624) {
                this.mt[0] = this.mt[623];
                i = 1;
            }
            if (j >= key.length)
                j = 0;
        }
        for (let k = 623; k > 0; k--) {
            this.mt[i] = ((this.mt[i] ^ Math.imul(this.mt[i - 1] ^ (this.mt[i - 1] >>> 30), 1566083941)) - i) >>> 0;
            i++;
            if (i >= 624) {
                this.mt[0] = this.mt[623];
                i = 1;
            }
        }
        this.mt[0] = 0x80000000;
    }
    private word(): number {
        if (this.index >= 624) {
            for (let i = 0; i < 624; i++) {
                const y = (this.mt[i] & 0x80000000) | (this.mt[(i + 1) % 624] & 0x7fffffff);
                this.mt[i] = this.mt[(i + 397) % 624] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0);
            }
            this.index = 0;
        }
        let y = this.mt[this.index++];
        y ^= y >>> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >>> 18;
        return y >>> 0;
    }
    random(): number { return ((this.word() >>> 5) * 67108864 + (this.word() >>> 6)) / 9007199254740992; }
    uniform(a: number, b: number): number { return a + (b - a) * this.random(); }
    int(a: number, b: number): number {
        const n = b - a + 1, k = Math.floor(Math.log2(n)) + 1;
        let r = this.word() >>> (32 - k);
        while (r >= n)
            r = this.word() >>> (32 - k);
        return a + r;
    }
}
