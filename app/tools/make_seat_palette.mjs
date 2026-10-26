import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoDir = path.resolve(appDir, '..');
const ledgerPath = path.join(repoDir, 'gis', 'parameter_ledger.csv');
const outputPath = path.join(appDir, 'src', 'world', 'seatPalette.js');

function parseCsvLine(line) {
  const fields = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"' && quoted && line[i + 1] === '"') { field += '"'; i++; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { fields.push(field); field = ''; }
    else field += char;
  }
  fields.push(field);
  return fields;
}

const rowNames = [
  'bowl.seat.green_hex', 'bowl.seat.red_hex',
  'bowl.seat.lower_tones', 'bowl.seat.lower_tone_weights',
  'bowl.seat.middle_tones', 'bowl.seat.middle_tone_weights',
  'bowl.seat.upper_tones', 'bowl.seat.upper_tone_weights',
  'bowl.seat.mix_lower_red_top', 'bowl.seat.mix_middle_green',
];

export async function makeSeatPalette() {
  const csv = await readFile(ledgerPath, 'utf8');
  const rows = new Map(csv.trimEnd().split(/\r?\n/).slice(1).map(parseCsvLine).map((cols) => [cols[0], cols[1]]));
  for (const name of rowNames) {
    if (!rows.has(name) || rows.get(name) === '') throw new Error(`Missing ledger row: ${name}`);
  }
  const value = (name) => rows.get(`bowl.seat.${name}`);
  const tier = (name) => ({
    tones: value(`${name}_tones`).split(';'),
    weights: value(`${name}_tone_weights`).split(';').map(Number),
  });
  const palette = {
    greenHex: value('green_hex'),
    redHex: value('red_hex'),
    mixLowerRedTop: Number(value('mix_lower_red_top')),
    mixMiddleGreen: Number(value('mix_middle_green')),
    lower: tier('lower'),
    middle: tier('middle'),
    upper: tier('upper'),
  };
  const output = `// Generated from gis/parameter_ledger.csv rows: ${rowNames.join(', ')}.\n// Regenerate with: node tools/make_seat_palette.mjs\nexport const seatPalette = ${JSON.stringify(palette, null, 2)};\n`;
  await writeFile(outputPath, output);
  return output;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await makeSeatPalette();
  process.stdout.write('Generated src/world/seatPalette.js from gis/parameter_ledger.csv\n');
}
