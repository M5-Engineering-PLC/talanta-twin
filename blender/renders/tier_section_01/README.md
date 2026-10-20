# Tier section 01: row counts derived, tread/riser fit rejected

Internal review only. Frames are from JWNowpO44rw, internal reference only (AGENTS.md rule 2). Geometry fitting of
the outer profile closed after geometry pass 3. This pass covers the bowl's tier section only.

## 1. Relabelled

The pass 2 FFT counts (lower 16, middle 11) are now evidence rows bowl.tier_lower.rows_fft_pass2 and
bowl.tier_middle.rows_fft_pass2, "estimated (FFT, superseded by the hand count)". The build does not read them.

## 2. Row counts by hand at native resolution (gis/scripts/tier_section/rows.json)

Method: one full block per tier, square on, at 1280 x 720. The dark seat-back minima were counted down two or three
block-centre columns and checked by eye at 4-10x with row guides. Splits (2 px spacing) are merged and missed rows
(about 2x the spacing) are filled. Two overlapping frames within +-1 mark a count derived.

| tier | 000745.000 | 000747.000 | other | set | status |
|---|---|---|---|---|---|
| upper | 32 (31-33) | 32 | 002348.000 (other stand): 29-31 | 32 (was 21) | derived (2 frames) |
| middle | 11-12 | 12-13 | 002348.000: 12-14 | 12 (pass 2 FFT: 11) | derived (2 frames) |
| lower | 14-15 | 15-16 | 000945.200: 15 | 15 (pass 2 FFT: 16) | derived (2 frames) |

Frames used against the brief:
- Upper tier, 000745-000805: 000745 and 000747 show the far (west) stand square on, with every tier sharp. The
  close views 000751-000805 show only partial blocks of the near upper tier, around the media rows, so they are not
  used for counts. 002348-002412: 002348 shows the far (east) stand from the VIP rows and is the third check. 002403
  (the lounge), 002409 and 002412 (roof views) show no full block.
- Lower tier, 002500-002506: shot with a shallow depth of field, so the stand behind the speaker is blurred and its
  rows can't be counted. 000945.200 counts 15 by hand. The pass 2 FFT on the same frame gave 16.
- Camera position: the frames 000745-000805 are taken from the upper tier (its rows climb to the roof, and its
  parapet overhangs the middle tier), not from the middle tier.

## 3. Depth and rise fit: rejected

gis/scripts/tier_section/tier_fit.py fits a two-view section. The views are 000747.000, high on the east upper tier
looking at the west stand, and 002348.000, at the west VIP rows looking at the east stand. Both stands are assumed to
share one section. Unknowns: tread and riser per tier, the middle and upper front offsets, one focal length, a
pitch per view, and each camera's row position in its own stand. Measurements: the back and front rows of each tier,
the row spacing in its back and front thirds, and the measured plan depth (front ring to back ring 52.1 m, soft limit
+-1.5 m). Plausibility: tread 0.7-0.9 m, riser 0.3-0.6 m.

| variant | rms (px) | at a bound | result |
|---|---|---|---|
| every row position, free cameras | 1.48 | upper tread 0.30, camera B (both bounds) | upper back at 21 m: impossible |
| features, one focal length, f >= 500 | 3.47 | all three treads, f, camera ties | treads 1.6 / 0.3 / 0.3 m |
| features, f >= 300 (wide lens allowed) | 3.76 | lower tread and riser, middle and upper treads, camera ties | treads 1.6 / 0.3 / 0.3 m, f 378 px |
| treads fixed at 0.80 m | 7.73 | f, offsets, camera ties | risers 0.66 / 0.58 / 0.23 m |

Every variant puts the treads (or the focal length) on a bound, and none meets the plan depth. The fit is rejected:
no tread or riser from it enters the build. The reason is the data, not the solver. At 1280 x 720, with cameras
100-150 m from the far stand, the row spacing barely changes from back to front (upper tier 3.0 vs 3.1 px, lower
3.05 vs 3.05 px in 000747). Tread depth trades freely against camera distance, height and focal length. The seat
period, the only in-frame horizontal scale, sits at 3-4 px. In 000745 it merges into lines, and the FFT picks up 8 px
JPEG blocks.

## 4. Rebuild and places

The build reads the derived rows (bowl.tier_*.rows_blockout 15 / 12 / 32). The tier extents (t0, t1, y0, y1) keep
their estimates. The implied steps fall outside the plausible ranges and are flagged here, not fixed:

| tier | rows | depth (m) | rise (m) | implied tread | implied riser |
|---|---|---|---|---|---|
| lower | 15 | 19.8 | 11.3 | 1.32 | 0.75 |
| middle | 12 | 10.9 | 9.0 | 0.91 | 0.75 |
| upper | 32 | 15.6 | 11.0 | 0.49 | 0.34 |

| places | count |
|---|---|
| bowl seats (regular) | 62,524 |
| media seats (in the bowl) | 583 |
| VIP seats | 218 |
| sky boxes, 52 x 12 (estimated, 10-20 each) | 624 |
| total | 63,949 |
| narrated capacity | 60,000 |
| difference | +3,949 (+6.6 %) |

Interior pass 2 had 50,085 places. The row changes (upper +11, middle +1, lower -1) add 13,864 net. The total now sits above the
narrated 60,000. The likely causes are an upper tier that is really deeper and overhangs the middle tier (with
0.8 m treads its 32 rows need about 25.6 m, against 15.6 m modelled), which puts its rows on shorter rings, and
places lost to vomitories, camera and media positions not modelled. The seat pitch is unchanged (0.5 m).

## Still open

- Tier depths and rises. A measured section (drawing or survey), or a side-on frame of each tier with a person or
  a known object for scale, would settle them. The brief's ranges (0.7-0.9 m, 0.3-0.6 m) show that the modelled lower and
  middle tiers are too tall for their row counts, and the upper tier is too shallow.
- The places total depends on the upper tier's plan position as well as its rows.

## Files

- gis/scripts/tier_section/rows.json: counts, windows and the views used for the fit.
- gis/scripts/tier_section/tier_fit.py: the fit (its last run, with f >= 300, is in tier_fit_result.json).
- Ledger: bowl.tier_{lower,middle,upper}.rows_blockout (derived), bowl.tier_{lower,middle}.rows_fft_pass2
  (estimated, superseded).

No renders in this pass: the build changed only in row counts, so the renders would show the same tier extents.
