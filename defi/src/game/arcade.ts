import { ROUND_SECONDS, STARTING_LIVES, touchesCircle } from './rules';
import { PythonRandom, codeSeed, normalizeCode } from './random';
import type { Input, Status } from './platform';
export interface Projectile {
    x: number;
    y: number;
    vx: number;
    vy: number;
    r: number;
    kind: number;
    delay: number;
}
export class ArcadeRun {
    readonly code: string;
    private rng: PythonRandom;
    x = 500;
    y = 395;
    time = 0;
    score = 0;
    lives = STARTING_LIVES;
    fragments = 0;
    combo = 0;
    lastCollect = -10;
    invulnerable = 1;
    dash = 0;
    cooldown = 0;
    status: Status = 'playing';
    projectiles: Projectile[] = [];
    gems: {
        x: number;
        y: number;
    }[] = [];
    private nextProjectile = 1.1;
    private nextFragment = 1;
    private direction = [1, 0];
    private dashDirection = [1, 0];
    constructor(code: string) { this.code = normalizeCode(code); this.rng = new PythonRandom(codeSeed(code)); }
    private finish(won: boolean) { this.status = won ? 'won' : 'lost'; this.score += this.lives * 100; }
    private spawn() {
        const edge = this.rng.int(0, 3), x = edge === 0 || edge === 2 ? this.rng.int(20, 980) : edge === 1 ? 980 : 20, y = edge === 1 || edge === 3 ? this.rng.int(120, 680) : edge === 0 ? 100 : 680;
        const dx = this.x - x, dy = this.y - y, length = Math.hypot(dx, dy) || 1, choice = this.rng.random() * 10, kind = choice < 5 ? 0 : choice < 8 ? 1 : 2;
        const speed = kind === 0 ? 145 + Math.min(145, this.time * 2.3) : kind === 1 ? 225 + Math.min(100, this.time * 1.8) : 105 + Math.min(75, this.time * 1.5);
        const r = kind === 0 ? this.rng.int(10, 13) : kind === 1 ? this.rng.int(7, 9) : this.rng.int(12, 15);
        this.projectiles.push({ x, y, vx: dx / length * speed, vy: dy / length * speed, r, kind, delay: .34 });
    }
    step(input: Input, dt: number) {
        if (this.status !== 'playing')
            return;
        if (input.pressed && this.cooldown <= 0) {
            this.dash = .19;
            this.cooldown = 1.05;
            this.dashDirection = [...this.direction];
            this.invulnerable = Math.max(this.invulnerable, .24);
        }
        this.time = Math.min(ROUND_SECONDS, this.time + dt);
        this.dash = Math.max(0, this.dash - dt);
        this.cooldown = Math.max(0, this.cooldown - dt);
        this.invulnerable = Math.max(0, this.invulnerable - dt);
        const length = Math.hypot(input.x, input.y) || 1;
        let dx = input.x / length, dy = input.y / length;
        if (dx || dy)
            this.direction = [dx, dy];
        if (this.dash > 0)
            [dx, dy] = this.dashDirection;
        const speed = 310 * (this.dash > 0 ? 2.45 : 1);
        this.x = Math.max(40, Math.min(960, this.x + dx * speed * dt));
        this.y = Math.max(127, Math.min(650, this.y + dy * speed * dt));
        if (this.time >= this.nextProjectile) {
            this.spawn();
            const interval = Math.max(.52, 1.45 - this.time * .018);
            this.nextProjectile += this.rng.uniform(interval * .75, interval * 1.2);
        }
        if (this.time >= this.nextFragment && this.gems.length < 2) {
            this.gems.push({ x: this.rng.int(90, 910), y: this.rng.int(155, 610) });
            this.nextFragment = this.time + this.rng.uniform(2.2, 3.1);
        }
        for (const p of [...this.projectiles]) {
            if (p.delay > 0) {
                p.delay = Math.max(0, p.delay - dt);
                continue;
            }
            if (p.kind === 2) {
                const a = 115 * Math.PI / 180 * dt, vx = p.vx;
                p.vx = vx * Math.cos(a) - p.vy * Math.sin(a);
                p.vy = vx * Math.sin(a) + p.vy * Math.cos(a);
            }
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            if (p.x < -60 || p.x > 1060 || p.y < 80 || p.y > 840) {
                this.projectiles = this.projectiles.filter(q => q !== p);
                continue;
            }
            if (touchesCircle(this.x, this.y, 13, p.x, p.y, p.r)) {
                this.projectiles = this.projectiles.filter(q => q !== p);
                if (this.invulnerable <= 0 && this.dash <= 0) {
                    this.lives--;
                    this.combo = 0;
                    this.invulnerable = 1.35;
                    this.projectiles = [];
                    if (this.lives <= 0) {
                        this.finish(false);
                        return;
                    }
                    break;
                }
            }
        }
        for (const g of [...this.gems])
            if (touchesCircle(this.x, this.y, 13, g.x, g.y, 14)) {
                this.gems = this.gems.filter(p => p !== g);
                this.fragments++;
                this.combo = this.time - this.lastCollect < 4 ? this.combo + 1 : 1;
                this.lastCollect = this.time;
                this.score += 150 + Math.min(150, (this.combo - 1) * 30);
            }
        this.score = Math.max(this.score, Math.floor(this.time * 12) + this.fragments * 150);
        if (this.time >= ROUND_SECONDS)
            this.finish(true);
    }
}
