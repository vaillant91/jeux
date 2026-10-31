import { describe, expect, it } from 'vitest';
import { touchesCircle } from './rules';
describe('touchesCircle', () => {
    it('detects overlapping circles', () => {
        expect(touchesCircle(0, 0, 5, 8, 0, 5)).toBe(true);
    });
    it('does not detect circles that are apart', () => {
        expect(touchesCircle(0, 0, 4, 10, 0, 4)).toBe(false);
    });
    it('does not hit circles that meet exactly at their edges', () => {
        expect(touchesCircle(0, 0, 3, 0, 7, 4)).toBe(false);
    });
});
