# Lead review of facade_fix_01, 2026-10-20

Cloud push: c9ad652 on m5/vibrant-ride-5er9ju. Compared against JWNowpO44rw 001216.000, 001232.600, 000645.000, 000714.767 and 000617.567.

## Accepted

- Ribs: slim flat strips, sharp V joints under the fascia, X crossings at mid-height. 24 bays and 8 shields read correctly in D01 to D03.
- Shield position: centred on the V lines, top at the V point, foot on the ring beam.
- Base: white ring beam, dark set-back ground floor and white piers.
- Bay width 31.8 m on the fascia line against 32.5 m on the roof outer ring. The 2 % difference is inside the rib width tolerance.

## Decisions

| item | decision |
|---|---|
| Shield colour | Change the paint, not the grade. Tune the albedo until the F16 render samples within 12 levels in each channel of the frame red (166, 11, 58) and the frame black. Record the new value as a new ledger row. |
| Fascia band | Yes. bowl.fin.fascia_h = 2.5 m (new ledger row). |
| Louvre tone | Change the backing first: a light grey backing behind the fins, not a dark void. Keep the fin depth and the fin slope. |
| F32 far side | No change now. Log it as a known gap (heights are estimated). |
| Next step | Fixes first, then 4K H stills. W waits for Munene's approval of the 4K stills. |

## Extra corrections

- Spear blades: the render shows wide spoon-shaped ovals. The frame shows long slender leaf blades with a pointed tip. Use blade length 6.5 m (ledger) and a maximum blade width of 2.2 times the shaft diameter.
- Jacaranda crowns read navy-blue in D02 and in the app. Make them a lighter lilac, or use them less.
