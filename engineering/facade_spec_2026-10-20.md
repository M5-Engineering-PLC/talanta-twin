# Façade spec from the drone frames, 2026-10-20

Author: lead session. Status: values derived from frame pixels, not surveyed. Internal reference only.

## Method

- Frames: JWNowpO44rw 001216.000 (1920 x 1080, close, sunlit), 001221.500 and 000714.767 (1280 x 720), 001232.600 (shade).
- The scale comes from the plan. The façade perimeter at the fascia is 780.4 m (roof_outer superellipse: a 106.24 m, b 124.04 m, n 3.08).
- On the long side, a shield sits on every third top V point. With 8 shields, the façade has 24 bays. One bay is 780.4 / 24 = 32.5 m.
- In 001216.000, one bay near the frame centre is 625 px. All the widths below are pixel widths across the member (FWHM), scaled by 32.5 m / 625 px.
- The ribs and the louvre pitch are measured on the same face of the same frame. This removes most of the scale error.

## Values (new rows in gis/parameter_ledger.csv)

| item | value | uncertainty | old value |
|---|---|---|---|
| Lattice members in each direction | 24 | +-2 | 20 |
| Louvre pitch | 0.65 m | +-0.08 m | 0.6 m |
| Rib face width | 0.45 m | +-0.15 m | 1.5 m |
| Rib stand-off from the louvre faces | 0.25 m | +-0.15 m | 0.8 m |
| Spear shaft radius | 0.37 m | +-0.1 m | 0.5 m |
| Shield red | #ad2750 sRGB | hue +-8 deg, value +-15 % | #d0202a |
| Shield black | #1c1e22 sRGB | +-10 % | 0.04 grey |
| Shield roughness | 0.6, metallic 0 | +-0.15 | glossy |
| Base ring beam height | 2.0 m | +-0.5 m | none |

## Geometry rules seen in the frames

1. Each rib is a slim flat strip with square edges. The face is flat and the rib is almost flush with the louvres.
2. Each rib runs from a top V point down to the bottom point one bay along. The bottom points sit directly below the top V points.
3. Two ribs cross in an X at mid-height, midway between two V points.
4. At the top, two ribs meet in a sharp V directly under the fascia band. The joint is a sharp mitre, not a round fork.
5. At the bottom, the ribs meet in the same sharp way on the white base ring beam.
6. The shield is centred on a V line. Its top touches a top V point and its foot touches the bottom point under it.
7. Two white spears cross behind each shield in an X. The blades show above the shield, left and right, just under the fascia. The shafts show below the shield.
8. The shield is flat paint on a panel. The edge has the face colour. There is no chrome or bright rim.
9. The shield looks maroon only in overcast or shade frames (000714.767, 001232.600). In sun (001216.000) the paint is a clear crimson.
10. Under the base ring beam, the ground floor is set back and in shadow, so it reads dark. White piers stand at about one per bay. This is not a continuous white colonnade.

## Limits

- The 24-bay count assumes that the end bays follow the 3-bay rhythm of the long side. If an end shows a different rhythm, the bay width changes. All widths then scale by 24 / N.
- The colour values come from graded video. Compare the render with frame 001216.000 in the same light before you accept a colour.
- Do not show gates, exits, signs or access routes from the ground floor in public output.
