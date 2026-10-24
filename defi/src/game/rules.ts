export const TARGET_STARS = 8
export const ROUND_SECONDS = 45
export const STARTING_LIVES = 3

export function touchesCircle(
  ax: number,
  ay: number,
  ar: number,
  bx: number,
  by: number,
  br: number,
): boolean {
  const dx = ax - bx
  const dy = ay - by
  const reach = ar + br
  return dx * dx + dy * dy <= reach * reach
}
