import { validateLevel } from './game/levels';
import type { Level } from './game/levels';
export interface SavedLevel {
    id: string;
    name: string;
    level: Level;
}
interface Save {
    version: 1;
    records: Record<string, number>;
    levels: SavedLevel[];
}
const KEY = 'defi-ton-pote:v1';
export class Saves {
    data: Save = { version: 1, records: {}, levels: [] };
    warning = '';
    private writable = true;
    constructor(private storage: Pick<Storage, 'getItem' | 'setItem'>) {
        try {
            const raw = storage.getItem(KEY);
            if (!raw)
                return;
            const data: unknown = JSON.parse(raw);
            if (!data || typeof data !== 'object' || !('version' in data) || data.version !== 1)
                throw Error('Version de sauvegarde inconnue : données conservées.');
            const d = data as Save;
            if (!d.records || typeof d.records !== 'object' || !Array.isArray(d.levels))
                throw Error('Sauvegarde invalide : données conservées.');
            for (const l of d.levels) {
                if (typeof l.id !== 'string' || typeof l.name !== 'string')
                    throw Error('Bibliothèque invalide.');
                validateLevel(l.level, false);
            }
            if (Object.values(d.records).some(n => !Number.isFinite(n) || n < 0))
                throw Error('Records invalides.');
            this.data = d;
        }
        catch (e) {
            this.writable = false;
            this.warning = e instanceof Error ? e.message : 'Stockage inaccessible.';
        }
    }
    flush() { if (!this.writable)
        return false; try {
        this.storage.setItem(KEY, JSON.stringify(this.data));
        return true;
    }
    catch {
        this.warning = 'Stockage indisponible : exporte ton code pour conserver le parcours.';
        return false;
    } }
    record(key: string, value: number, lower = false) { const old = this.data.records[key]; this.data.records[key] = old === undefined ? value : lower ? Math.min(old, value) : Math.max(old, value); this.flush(); return this.data.records[key]; }
    save(level: SavedLevel) { const i = this.data.levels.findIndex(l => l.id === level.id); if (i < 0)
        this.data.levels.unshift(structuredClone(level));
    else
        this.data.levels[i] = structuredClone(level); return this.flush(); }
}
