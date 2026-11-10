/** sRGB bytes to CIELAB with a D65 reference white. Alpha is not part of the metric. */
export function rgbToLab(r, g, b) {
  const linear = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  r = linear(r); g = linear(g); b = linear(b);
  const f = (v) => v > (6 / 29) ** 3 ? Math.cbrt(v) : v / (3 * (6 / 29) ** 2) + 4 / 29;
  const x = f((0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047);
  const y = f(0.2126729 * r + 0.7151522 * g + 0.0721750 * b);
  const z = f((0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883);
  return [116 * y - 16, 500 * (x - y), 200 * (y - z)];
}

/** CIEDE2000, unit parametric factors kL=kC=kH=1. Angles use degrees. */
export function ciede2000([l1, a1, b1], [l2, a2, b2]) {
  const rad = Math.PI / 180;
  const cos = (v) => Math.cos(v * rad), sin = (v) => Math.sin(v * rad);
  const c1 = Math.hypot(a1, b1), c2 = Math.hypot(a2, b2), c = (c1 + c2) / 2;
  const g = 0.5 * (1 - Math.sqrt(c ** 7 / (c ** 7 + 25 ** 7)));
  const ap1 = (1 + g) * a1, ap2 = (1 + g) * a2;
  const cp1 = Math.hypot(ap1, b1), cp2 = Math.hypot(ap2, b2);
  const hue = (a, b) => (Math.atan2(b, a) / rad + 360) % 360;
  const h1 = cp1 === 0 ? 0 : hue(ap1, b1), h2 = cp2 === 0 ? 0 : hue(ap2, b2);
  let dh = h2 - h1;
  if (cp1 * cp2 === 0) dh = 0;
  else if (dh > 180) dh -= 360;
  else if (dh < -180) dh += 360;
  const dl = l2 - l1, dc = cp2 - cp1, dH = 2 * Math.sqrt(cp1 * cp2) * sin(dh / 2);
  const lm = (l1 + l2) / 2, cm = (cp1 + cp2) / 2;
  let hm = h1 + h2;
  if (cp1 * cp2 !== 0) {
    if (Math.abs(h1 - h2) <= 180) hm /= 2;
    else hm = (hm + (hm < 360 ? 360 : -360)) / 2;
  }
  const t = 1 - 0.17 * cos(hm - 30) + 0.24 * cos(2 * hm) + 0.32 * cos(3 * hm + 6) - 0.20 * cos(4 * hm - 63);
  const sl = 1 + 0.015 * (lm - 50) ** 2 / Math.sqrt(20 + (lm - 50) ** 2);
  const sc = 1 + 0.045 * cm, sh = 1 + 0.015 * cm * t;
  const rt = -2 * Math.sqrt(cm ** 7 / (cm ** 7 + 25 ** 7)) * sin(60 * Math.exp(-(((hm - 275) / 25) ** 2)));
  return Math.sqrt((dl / sl) ** 2 + (dc / sc) ** 2 + (dH / sh) ** 2 + rt * dc / sc * dH / sh);
}

/** Rectangles are [x0,y0,x1,y1] fractions, with a top-left origin. Every pixel is measured. */
export function meanColorDifference(first, second, width, height, rect = [0, 0, 1, 1]) {
  if (first.length !== width * height * 4 || second.length !== first.length) throw new RangeError('RGBA dimensions differ');
  if (rect.length !== 4 || !rect.every((v) => Number.isFinite(v) && v >= 0 && v <= 1)
      || rect[0] >= rect[2] || rect[1] >= rect[3]) throw new RangeError('Invalid comparison rectangle');
  const x0 = Math.floor(rect[0] * width), y0 = Math.floor(rect[1] * height);
  const x1 = Math.ceil(rect[2] * width), y1 = Math.ceil(rect[3] * height);
  let sum = 0, pixels = 0;
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
    const i = 4 * (y * width + x);
    sum += ciede2000(rgbToLab(first[i], first[i + 1], first[i + 2]), rgbToLab(second[i], second[i + 1], second[i + 2]));
    pixels++;
  }
  return { mean: sum / pixels, pixels };
}
