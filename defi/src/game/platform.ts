import { STARTING_LIVES } from './rules';
import { clone, TILE, COLS, validateLevel, pyRound } from './levels';
import type { Level, Point } from './levels';
export interface Input {
    x: number;
    y: number;
    jump: boolean;
    pressed: boolean;
    run: boolean;
}
export type Status = 'playing' | 'won' | 'lost';
export interface Rect {
    x: number;
    y: number;
    w: number;
    h: number;
}
export const overlaps = (a: Rect, b: Rect) => a.x + a.w > b.x && a.x < b.x + b.w && a.y + a.h > b.y && a.y < b.y + b.h;
export interface Monster extends Rect {
    min: number;
    max: number;
    direction: number;
}
export class PlatformRun {
    readonly level: Level;
    player: Rect = { x: 0, y: 0, w: 28, h: 38 };
    vx = 0;
    vy = 0;
    grounded = false;
    coyote = 0;
    buffer = 0;
    invulnerable = .8;
    time = 0;
    lives = STARTING_LIVES;
    score = 0;
    gems = 0;
    status: Status = 'playing';
    checkpoint: Point;
    collected = new Set<string>();
    checkpoints = new Set<string>();
    monsters: Monster[] = [];
    private spring = false;
    constructor(level: Level) {
        validateLevel(level);
        this.level = clone(level);
        this.checkpoint = [...level.start];
        this.place();
        for (const [c, r] of level.monstres) {
            const support = [1, 2].includes(level.tiles[r][c]) ? r : r < 10 && [1, 2].includes(level.tiles[r + 1][c]) ? r + 1 : null;
            let left = c, right = c;
            if (support !== null && support > 0) {
                const safe = (x: number) => [1, 2].includes(level.tiles[support][x]) && ![1, 2, 3].includes(level.tiles[support - 1][x]);
                while (left > 0 && safe(left - 1))
                    left--;
                while (right < 39 && safe(right + 1))
                    right++;
            }
            const patrol = support !== null && support > 0, min = patrol ? left * 48 + 4 : c * 48 + 7, max = patrol ? (right + 1) * 48 - 38 : min;
            this.monsters.push({ x: Math.max(min, Math.min(max, c * 48 + 7)), y: patrol ? support * 48 - 34 : r * 48 + 8, w: 34, h: 34, min, max, direction: c % 2 === 0 ? 1 : -1 });
        }
    }
    private place() { this.player.x = this.checkpoint[0] * 48 + 10; this.player.y = this.checkpoint[1] * 48 + 5; }
    hurt() {
        if (this.status !== 'playing')
            return;
        this.lives--;
        this.place();
        this.vx = this.vy = this.buffer = this.coyote = 0;
        this.invulnerable = 1;
        this.grounded = this.spring = false;
        if (this.lives <= 0)
            this.status = 'lost';
    }
    step(input: Input, dt: number) {
        if (this.status !== 'playing')
            return;
        this.time += dt;
        this.invulnerable = Math.max(0, this.invulnerable - dt);
        this.coyote = Math.max(0, this.coyote - dt);
        this.buffer = input.pressed ? .14 : Math.max(0, this.buffer - dt);
        for (const m of this.monsters) {
            m.x += m.direction * 82 * dt;
            if (m.x <= m.min) {
                m.x = m.min;
                m.direction = 1;
            }
            else if (m.x >= m.max) {
                m.x = m.max;
                m.direction = -1;
            }
        }
        const acceleration = input.x ? (this.grounded ? 2300 : 1150) : (this.grounded ? 2600 : 260), target = input.x * (input.run ? 360 : 270);
        this.vx += Math.max(-acceleration * dt, Math.min(acceleration * dt, target - this.vx));
        this.player.x = Math.max(0, Math.min(COLS * TILE - 28, this.player.x + this.vx * dt));
        const tiles: {
            c: number;
            r: number;
            t: number;
            rect: Rect;
        }[] = [];
        for (let r = 0; r < 11; r++)
            for (let c = 0; c < 40; c++)
                if (this.level.tiles[r][c])
                    tiles.push({ c, r, t: this.level.tiles[r][c], rect: { x: c * 48, y: r * 48, w: 48, h: 48 } });
        for (const { t, rect } of tiles)
            if (t === 1 && overlaps(this.player, rect)) {
                this.player.x = this.vx > 0 ? rect.x - 28 : rect.x + 48;
                this.vx = 0;
            }
        if (this.buffer > 0 && (this.grounded || this.coyote > 0)) {
            this.vy = -510;
            this.grounded = false;
            this.buffer = this.coyote = 0;
        }
        const bottom = this.player.y + 38;
        this.vy = Math.min(780, this.vy + (this.vy < 0 && input.jump ? 900 : 1450) * dt);
        this.player.y += this.vy * dt;
        this.grounded = false;
        for (const { t, rect } of tiles)
            if (t === 1 || t === 2) {
                const horizontal = this.player.x + 28 > rect.x && this.player.x < rect.x + 48;
                if (this.vy >= 0 && horizontal && bottom <= rect.y && this.player.y + 38 >= rect.y) {
                    this.player.y = rect.y - 38;
                    this.vy = 0;
                    this.grounded = true;
                    this.coyote = .1;
                }
                else if (t === 1 && this.vy < 0 && overlaps(this.player, rect)) {
                    this.player.y = rect.y + 48;
                    this.vy = 0;
                }
            }
        let springContact = false;
        for (const { c, r, t, rect } of tiles)
            if (overlaps(this.player, rect)) {
                const key = `${c},${r}`;
                if (t === 4 && !this.checkpoints.has(key)) {
                    this.checkpoints.add(key);
                    this.checkpoint = [c, r];
                    this.score += 250;
                }
                if (t === 5) {
                    springContact = true;
                    if (!this.spring && this.vy >= 0) {
                        this.player.y = rect.y + 8 - 38;
                        this.vy = -690;
                        this.grounded = false;
                        this.coyote = 0;
                        this.spring = true;
                    }
                }
                if ((t === 6 || t === 7) && !this.collected.has(key)) {
                    this.collected.add(key);
                    this.score += t === 6 ? 500 : 250;
                    if (t === 6)
                        this.gems++;
                    else
                        this.lives = Math.min(5, this.lives + 1);
                }
                if (t === 3 && this.invulnerable <= 0 && overlaps(this.player, { x: rect.x + 4, y: rect.y + 12, w: 40, h: 36 })) {
                    this.hurt();
                    return;
                }
            }
        if (!springContact)
            this.spring = false;
        if (this.invulnerable <= 0 && this.monsters.some(m => overlaps(this.player, m))) {
            this.hurt();
            return;
        }
        if (overlaps(this.player, { x: this.level.goal[0] * 48, y: this.level.goal[1] * 48 - 22, w: 48, h: 70 })) {
            this.status = 'won';
            this.score += Math.max(0, 10000 - pyRound(this.time * 50));
        }
        else if (this.player.y > 638)
            this.hurt();
    }
}
