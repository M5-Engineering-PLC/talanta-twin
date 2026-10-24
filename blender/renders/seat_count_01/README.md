# Seat count pass 01: upper tier overhang and vomitories (internal)

HANDOFF task 6. The build had 63,949 places against the narrated 60,000 (+6.6 %, tier_section_01). Two causes named there
are now modelled. Seat pitch unchanged (0.5 m). Every new value is estimated; no old ledger row was edited.

Time: code 1.5 h, build 45 s, check renders 8 min (4 x about 2 min, 960 x 540, 32 samples, neutral sun).

## Changes

- Upper tier depth and overhang (ledger `bowl.tier_upper.t0_blockout` = 0.54, was 0.70).
  - The 32 derived rows need 0.7-0.9 m treads (brief). Front-to-back depth runs 52.1-61.9 m round the bowl (mean 57.3 m).
  - t0 = 1 - 32 x 0.82 / 57.3. Treads are now 0.75-0.89 m round the bowl (were 0.49 m); risers stay 0.34 m.
  - The upper front now sits about 7 m over the middle tier (middle t1 0.66). Frames 000745-000805 show its parapet
    overhanging the middle tier.
  - A flat soffit closes the underside, 0.7 m below the upper front row (`bowl.tier_upper.soffit_drop_blockout`). That
    leaves about 2.8 m of clear height over the middle tier's back row.
- Vomitories (ledger `bowl.portals.cut_rows`). The IT03 portal mouths were drawn over the seats before. Now:
  - Upper mouths, one per aisle, run back into the tier until its treads reach the portal head (about 9 rows).
  - No seat stands inside a mouth or within 0.25 m of its jambs. Middle mouths, at every other aisle, cut the back rows.
  - They are generic openings, with no signage or egress meaning (AGENTS.md rule 8).
- C34 (002320.200, upper tier front walkway) follows the moved upper front (`make_interior_cameras.py` reads the ledger).

## Places

| | before | after |
|---|---|---|
| bowl seats (regular, incl. media) | 63,107 | 60,197 |
| of which media block | 583 | 517 |
| seats cut by portal mouths | 0 | 1,088 |
| VIP seats | 218 | 218 |
| sky boxes, 52 x 12 (estimated) | 624 | 624 |
| total | 63,949 | 61,039 |
| against the narrated 60,000 | +6.6 % | +1.7 % |

The overhang takes about 1,820 seats (the upper rows move onto shorter rings) and the vomitories 1,088.

## Check renders

`C34_neutral_check.png`, `C10_neutral_check.png`, `C32_neutral_check.png`, `C12_neutral_check.png`
(`blender/render_cycles.py seat_count_01 <cam> neutral check`, built from this commit).
- C34: the upper front reads as an overhang above the middle tier's back rows, with the portal frames at its edge.
- C10: the upper portal trenches show in the foreground rows; the far stand's overhang reads.
- C32, C12: no camera stands inside geometry; the lower tier is unchanged.

## Still open

- The tread is a mid-range assumption, not a measurement. A measured section would settle the depth, the rise and the overhang.
- The remaining +1,039 places may be camera platforms, media desks, wheelchair bays or the real seat pitch. None of these is
  modelled, and the frames don't resolve them.
- The web blockout (`app/public/data/blockout.glb`) was restored after the build. The app still shows the old upper tier
  until its owner re-exports it.
