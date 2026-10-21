# Roof fix 01: replica plan pass B (internal)

Pass B of the lead order of 2026-10-20. Internal only: the sheets hold reference frames. No 4K and no W.

## What changed

Code: commit 38bd950. Values: new ledger rows.

- **Cushion count from the frames:**
  - Columns: brightness profiles across the near side of D03 (000617.567, rows 150, 160 and 170 px) give a seam pitch of 26–30 px.
  - The solved D03 camera projects one topside-rib bay (30 bays, `bowl.roof.cushion_bays`) at 52–55 px there. That is two cushion columns per rib bay: `bowl.roof.cushion_cols_per_bay` 2, or 60 round the roof.
  - The topside ribs stay on every other seam.
  - Rows: column profiles from the opening trim to the rim count 5–6 intervals in D03 (x 560–680 px) and 6 in 001221.500 (x 500–900 px). `bowl.roof.cushion_rows` 6 supersedes 8.
- **Pillows:** raised until D03 shows a pillow in every row. Crop renders: 2.0 m read faint; 2.8 m with exponent 0.4 reads.
  New rows: `bowl.roof.cushion_bulge_blockout` 2.8 m and `cushion_pillow_blockout` 0.4.
- **Membrane:** bright white and soft (albedo 0.93, was 0.86; roughness 0.75, was 0.55).

## Renders

- Rebuild: the step F chain, frozen as `blender/out/step_FB.blend`. It took 28 min (08:23 to 08:51) and ran beside the pass A renders.
- Cycles 1920 x 1080 hero, 128 samples, look layer on.
- D03 was restarted once after a worker restart.
- The pass C rebuild ran on the same 4 cores, so the times are long.

| Render | Camera | Light | Time |
|---|---|---|---|
| D03_overcast_hero.png | D03, solved drone camera (as for facade_fix_01) | overcast 11:00 | 21.9 min (after a restart) |
| F32_overcast_hero.png | F32, solved to 001232.600 | overcast | 18.5 min |

## Measured (D03 against 000617.567, near roof band, rows 140–180 and x 420–820 of 1280)

| | Frame | facade_fix_01 | roof_fix_01 |
|---|---|---|---|
| Pillow contrast: std of the 4 px high-pass luminance over the mean | 3.24 % | 6.33 % (dominated by the 30 raised rib seams, not by pillows) | 3.22 % |
| Median roof colour | (228, 232, 237) | (175, 196, 220) | (180, 200, 222) |

The pillow shading now matches the frame in strength, and every row shows a pillow as in the frame.

## Sheets (sheets/, internal)

Made with `engineering/review_sheet.py` (render, frame, blend, edges); JPG at quality 90.

## Gaps (honest list)

1. **Roof tone:**
   - The membrane reads blue-grey: about 48 levels darker than the frame and bluer.
   - The albedo is now 0.93. The cause is the blue procedural overcast sky and its exposure.
   - The grey cloud sky with lower exposure is pass D.
2. **Shoulder band:**
   - In D03 the frame's pillows run out to the outer rim.
   - Our rolled top (step G profile) leaves a smooth white band between the fascia line and the first cushion row.
   - The cushions start at the facade-roof junction of the fitted profile. Not changed here: it is the bowl profile, not the cushions.
3. **Opening trim:** the frame shows a broad white flat trim round the opening, about 25 px in D03. Ours is a narrow dark trim. Not in this order.
4. **Pillow shape:** the frame's cushions read squarer, with a crisp shaded downhill seam. Under the diffuse overcast our pillows are softer.
5. **F32:** the pillows now cover the roof as in 001232.600 (sheet 002). Far side: no change, logged as a known gap (lead answer 4). The far roof rim and opening sit 40–60 px low in F32.
