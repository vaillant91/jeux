export const ROUND_SECONDS = 45;
export const STARTING_LIVES = 3;
/** The Python version uses strict overlap: touching edges alone is not a hit. */
export function touchesCircle(ax: number, ay: number, ar: number, bx: number, by: number, br: number): boolean {
    return (ax - bx) ** 2 + (ay - by) ** 2 < (ar + br) ** 2;
}
