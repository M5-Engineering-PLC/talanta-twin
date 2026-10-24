// Visualization only. These functions describe animation, not human behavior.
export const clampFill = (value) => Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;
export const drawLimit = (count, width) => Math.min(count, width < 768 ? 15000 : count);
export const waveDistance = (time, speed, perimeter) => ((time * speed) % perimeter + perimeter) % perimeter;
export function occupancyOrder(seats) {
  // Nearby seats share a block score. The smaller term breaks ties within blocks.
  return seats.map((seat, i) => {
    const block = Math.floor((Math.atan2(seat.z, seat.x) + Math.PI) * 20) + Math.floor(seat.row / 3) * 131 + seat.tier * 997;
    const hash = (n) => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
    return { i, score: hash(block) * 0.92 + hash(i) * 0.08 };
  }).sort((a, b) => a.score - b.score).map(({ i }) => i);
}
export function selectSeats(seats, fraction, width = 1024, order = occupancyOrder(seats)) {
  const occupied = order.slice(0, Math.round(seats.length * clampFill(fraction)));
  const count = drawLimit(occupied.length, width);
  // Sample across the occupied places rather than removing entire sections on phones.
  return Array.from({ length: count }, (_, i) => occupied[Math.floor(i * occupied.length / count)]);
}
