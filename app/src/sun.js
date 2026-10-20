// Solar position (NOAA simplified). Site default: Talanta pitch centre.
const rad = Math.PI / 180;

export function sunPosition(dateUTC, lat, lon) {
  const jd = dateUTC.getTime() / 86400000 + 2440587.5;
  const n = jd - 2451545.0;
  const L = (280.46 + 0.9856474 * n) % 360;
  const g = ((357.528 + 0.9856003 * n) % 360) * rad;
  const lambda = (L + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * rad;
  const eps = (23.439 - 0.0000004 * n) * rad;
  const ra = Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda));
  const dec = Math.asin(Math.sin(eps) * Math.sin(lambda));
  const gmst = (18.697374558 + 24.06570982441908 * n) % 24;
  const lst = (gmst * 15 + lon) * rad;
  const ha = lst - ra;
  const la = lat * rad;
  const el = Math.asin(Math.sin(la) * Math.sin(dec) + Math.cos(la) * Math.cos(dec) * Math.cos(ha));
  const az = Math.atan2(-Math.sin(ha), Math.tan(dec) * Math.cos(la) - Math.sin(la) * Math.cos(ha));
  return { elevation: el / rad, azimuth: ((az / rad) + 360) % 360 };
}

// Minutes after local midnight (EAT = UTC+3) -> Date in UTC.
export function eatDate(isoDay, minutes) {
  const [y, m, d] = isoDay.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d, 0, 0) + (minutes - 180) * 60000);
}

export function sunEvents(isoDay, lat, lon) {
  const out = {};
  let prev = sunPosition(eatDate(isoDay, 0), lat, lon).elevation;
  let best = -90;
  for (let t = 1; t <= 1440; t++) {
    const e = sunPosition(eatDate(isoDay, t), lat, lon).elevation;
    if (prev < -0.83 && e >= -0.83) out.sunrise = t;
    if (prev >= -0.83 && e < -0.83) out.sunset = t;
    if (prev < 6 && e >= 6) out.goldenEnd = t;
    if (prev >= 6 && e < 6) out.goldenStart = t;
    if (e > best) { best = e; out.noon = t; out.noonEl = e; }
    prev = e;
  }
  return out;
}

/** Resolve the opening EAT time from a URL value, otherwise use 07:30. */
export function openingMinutes(value) {
  if (value == null || value.trim() === '') return 450;
  const match = /^(\d{1,2}):(\d{2})$/.exec(value);
  const minutes = match ? Number(match[1]) * 60 + Number(match[2]) : Number(value);
  if (match && (Number(match[1]) > 23 || Number(match[2]) > 59)) return 450;
  return Number.isFinite(minutes) && minutes >= 0 && minutes < 1440 ? minutes : 450;
}
