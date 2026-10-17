# Detail sheet: roof and facade

The frame images set the geometry and materials. The concept images guide the look only. Size and color values by eye are estimates unless the ledger marks them measured or derived. “Trapezoid section” means a four-sided member with a flat outer face. “Node” means a point where structural members meet.

### Louvre fins and lattice

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| RF01 | Louvre fins | Horizontal, slim rectangular fins; slight outward slope. | Warm white `#E5E4DF` | About 18 per bay; ledger pitch 0.6 | Pitch 0.6; depth 0.7 | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | `bowl.fin.pitch`, `bowl.fin.depth` | Repeat fins across each facade bay. |
| RF02 | Fin drop | Fin ends descend slightly toward the exterior. | Warm white `#E5E4DF` | Continuous across each bay | 0.25 drop | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg` | frame | estimated | `bowl.fin.drop` | Tilt fins downward toward the facade face. |
| RF03 | Dark backing | Recessed dark surface behind the open fins. | Charcoal `#303033` | Continuous behind fin field | Set back 1.4 | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | `bowl.fin.backing_inset` | Keep the backing dark and recessed. |
| RF04 | Lattice members | Broad diagonal members form repeated triangles and diamonds over the fins. | Pale gray `#D8D9D6` | 40 members per direction in ledger | Face width 1.5; depth 0.8 | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001028.000.jpg`; renders 05–07 | frame+render | estimated | `bowl.lattice.members`, `bowl.lattice.section_w`, `bowl.lattice.section_d` | Use flat-faced trapezoid sections. |
| RF05 | Lattice tubes | Slim round ties and cross-members sit behind the broad lattice. | Light gray `#C9CBC8` | Many repeated ties; exact count unclear | Radius 0.42 | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg` | frame | estimated | `bowl.lattice.tube_r` | Place narrow round members behind the broad diagonals. |
| RF06 | Lattice ring | Heavier members form a perimeter ring at roof level. | White `#E2E2DE` | Continuous around the roof edge | Radius 0.5 | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg` | frame | estimated | `bowl.lattice.ring_r` | Continue the ring around the roof perimeter. |
| RF07 | Lattice nodes | Diagonals meet in small, clean joints; individual plates are not resolved. | Gray-white `#D4D5D2` | At each diagonal crossing | Not visible | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001028.000.jpg` | frame | estimated | new | Use simple flush joints without exposed bolts. |
| RF08 | Lower lattice ends | Diagonal members descend toward the base band and columns. | Pale gray `#D8D9D6` | Repeated at facade bays | Not visible | `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | new | End the diagonals at the roof and lower perimeter structure. |

### Shields and spears

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| RF09 | Shield panels | Tall convex panels with pointed ends and rounded sides. | Red `#D0202A` | 8 panels | Width 21; height about 39.5 | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001028.000.jpg`; renders 05–07 | frame+render | estimated | `bowl.shields.count`, `bowl.shield.width`, `bowl.shield.y0`, `bowl.shield.y1` | Space eight panels around the facade. |
| RF10 | Shield bulge | Each panel bows outward at its center. | Red `#D0202A` | One bulge per panel | 1.2 | `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | `bowl.shield.bulge` | Add a shallow convex face. |
| RF11 | Shield inset | White central oval and narrow vertical white forms create the shield motif. | White `#F1F0EA` | Repeated on each panel | Not visible | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001028.000.jpg`; renders 05–07 | frame+render | estimated | new | Build the motif as raised, simple shapes. |
| RF12 | Shield dark side fields | Dark curved fields frame the red panel at both sides. | Near-black `#202126` | Two side fields per panel | Not visible | `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | new | Add dark side fields to match the frame pattern. |
| RF13 | Shield edge trim | A narrow pale rim follows the shield outline. | White `#E7E6E0` | Full panel perimeter | Not visible | `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | new | Add a thin light edge strip. |
| RF14 | Shield fixings | Visible attachment points are not resolved in the frames. | Not assigned | Not visible | Not visible | `JWNowpO44rw_001212.500.jpg` | frame | estimated | new | Omit visible fasteners until a close detail is available. |
| RF15 | Spear shafts | Long, pale round shafts cross behind each shield. | White `#E6E6E1` | Two shafts per shield | Radius 0.5; span about 1.4 shield widths | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001028.000.jpg`; renders 05–07 | frame+render | estimated | `bowl.spear.radius`, `bowl.spear.span_shields` | Cross two shafts behind each shield. |
| RF16 | Spear blades | Short tapered blades finish the shaft ends. | White `#E6E6E1` | Four visible ends per pair | Length 6.5; width ratio 1.2 | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg` | frame | estimated | `bowl.spear.blade_len`, `bowl.spear.blade_r` | Taper each blade to a rounded point. |
| RF17 | Spear crossing | The two shafts cross behind the shield centerline. | White `#E6E6E1` | One crossing per shield | Not visible | `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | new | Keep the crossing behind the panel face. |
| RF18 | Spear tip clearance | Blade tips end just below the roof fascia. | White `#E6E6E1` | Repeated around facade | 0.6 below fascia | `JWNowpO44rw_001028.000.jpg`, `JWNowpO44rw_001212.500.jpg` | frame | estimated | `bowl.spear.tip_below_fascia` | Stop spear tips below the fascia line. |

### Roof canopy, fascia, and underside

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| RF19 | Roof outer plan | Rounded rectangular ring with cut corners. | White `#E9E8E3` | 12 measured outline points | 250.1 × 214.5 outer dimensions | `JWNowpO44rw_000004.000.jpg`, `OB0OE-PAAVg_000012.345.jpg`; renders 05–07 | frame+render | measured | `roof_outer.length`, `roof_outer.width` | Use the measured 12-point roof outline. |
| RF20 | Roof opening | Large rounded rectangular opening reveals the bowl. | Dark inside edge `#35363A` | One central opening | 130.0 × 88.1 | `JWNowpO44rw_000016.934.jpg`, `JWNowpO44rw_000004.000.jpg`; renders 05–07 | frame+render | measured | `roof_inner.length`, `roof_inner.width` | Cut the opening to the measured outline. |
| RF21 | Roof depth | Broad canopy band between the outer edge and opening. | White `#EEEDE8` | Continuous | 63.2 side depth; 60.1 end depth | `JWNowpO44rw_000004.000.jpg`, `OB0OE-PAAVg_000012.345.jpg` | frame | derived | `roof.depth_side`, `roof.depth_end` | Preserve the wide roof band. |
| RF22 | Roof membrane | Smooth, pale membrane with a soft sheen. | Off-white `#EEEDE8` | Continuous canopy | Not measured | `JWNowpO44rw_000016.934.jpg`, `JWNowpO44rw_001004.000.jpg`; renders 05–07 | frame+render | estimated | new | Use a pale, low-gloss surface. |
| RF23 | Roof panel seams | Radial seams divide the membrane into long wedge-like panels. | Light gray `#D4D4CF` | Many radial seams; count unclear | Not measured | `JWNowpO44rw_000016.934.jpg`, `JWNowpO44rw_000004.000.jpg`; renders 05–07 | frame+render | estimated | new | Run seams from the opening edge toward the outer fascia. |
| RF24 | Roof fascia | Thick, smooth perimeter edge caps the membrane. | White `#E7E6E1` | Continuous perimeter | Not measured | `JWNowpO44rw_000016.934.jpg`, `JWNowpO44rw_001028.000.jpg`; renders 05–07 | frame+render | estimated | new | Use a continuous fascia band. |
| RF25 | Fascia edge lights | Small lights trace sections of the roof edge at night. | White and colored `#FFFFFF`, `#32C6FF`, `#B35CFF` | Closely spaced points along visible sections | Exact spacing unclear | `JWNowpO44rw_001148.000.jpg`; renders 02, 05–07 | frame+render | estimated | new | Add small fixture points along the roof edge. |
| RF26 | Opening edge | Dark inner trim outlines the roof opening. | Charcoal `#333438` | Continuous rounded rectangle | Not measured | `JWNowpO44rw_000016.934.jpg`, `JWNowpO44rw_001004.000.jpg`; render 03 | frame+render | estimated | new | Add a narrow dark border around the opening. |
| RF27 | Visible underside steel | Pale main beams and curved secondary members support the canopy. | Warm gray `#C7C5B9` | About 30 primary members per direction; 9 purlin rings in ledger | Primary radius 0.4; 1.2 drop | `JWNowpO44rw_001004.000.jpg`, `JWNowpO44rw_000016.934.jpg`; render 03 | frame+render | estimated | `bowl.roofsteel.members`, `bowl.roofsteel.member_r`, `bowl.roofsteel.drop`, `bowl.roofsteel.purlin_rings` | Show the beam grid beneath the membrane. |
| RF28 | Roof catwalk | Narrow metal walkway follows the opening. | Gray `#A6A69F` | Continuous near inner edge | Width 1.4; drop 3.0 | `JWNowpO44rw_001004.000.jpg`; render 03 | frame+render | estimated | `bowl.catwalk.width`, `bowl.catwalk.drop` | Place the walkway below the canopy near the opening. |
| RF29 | Daylight fixtures | Rectangular floodlight heads sit in rows on the roof structure. | Gray housings `#777873` | Repeated along roof beams and catwalk | Exact count unclear | `JWNowpO44rw_001004.000.jpg` | frame | estimated | new | Use small rectangular fixture housings. |
| RF30 | Floodlight spacing | Individual light heads form a close line at the inner roof edge. | Gray housings `#777873` | About 2.5 spacing in ledger | 2.5 | `JWNowpO44rw_001004.000.jpg` | frame | estimated | `bowl.floodlights.spacing` | Repeat light heads along the inner edge. |
| RF31 | Opening light row | A bright line of small lights follows the inner roof rim at night. | White `#FFFFFF` | Continuous visible arc | Exact spacing unclear | `JWNowpO44rw_001148.000.jpg`; render 03 | frame+render | estimated | new | Add a separate light row at the opening edge. |

### Base band and columns

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| RF32 | Base step | Low light concrete step follows the bowl outline. | Pale concrete `#D1D0CA` | Continuous | 0.6 high | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001216.000.jpg`; renders 05–07 | frame+render | estimated | `bowl.base.step_h` | Follow the measured plinth outline. |
| RF33 | Recessed base wall | Shaded wall sits behind the columns. | Dark gray `#4A4945` | Continuous recessed band | Set back 4.0 | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001216.000.jpg`; renders 05–07 | frame+render | estimated | `bowl.base.recess` | Set the wall behind the columns. |
| RF34 | Base band | Pale horizontal band runs below the louvres. | White `#E2E1DB` | Continuous | 1.6 high | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001216.000.jpg`; renders 05–07 | frame+render | estimated | `bowl.base.band_h` | Continue the band around the facade. |
| RF35 | Base columns | White vertical columns stand in the recessed base. | White `#E2E2DE` | About 9 spacing; count varies with perimeter | Width 1.2; spacing 9.0 | `JWNowpO44rw_001216.000.jpg`, `JWNowpO44rw_001212.500.jpg`; renders 05–07 | frame+render | estimated | `bowl.base.column_w`, `bowl.base.column_spacing` | Repeat columns behind the outer facade band. |
| RF36 | Upper columns | White columns appear behind the upper seating tier. | White `#E2E2DE` | About 8 spacing | Radius not established | `zb4ISsX7Pa0_000114.073.jpg`, `Dtjm3vvAYhI_000025.000.jpg`; render 03 | frame+render | estimated | `bowl.colonnade.spacing` | Use plain round columns behind the upper tier. |
| RF37 | Weathering and dirt | Frames show a mostly clean pale facade; localized construction residue is not a stable finish cue. | Pale gray `#D8D8D2` | No regular pattern | Not measured | `JWNowpO44rw_001212.500.jpg`, `JWNowpO44rw_001216.000.jpg` | frame | estimated | new | Keep the facade clean with very subtle surface variation. |

### Night facade lights

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| RF38 | Facade wash lights | Low lights wash the facade upward with colored light. | Green, white, and red `#00C878`, `#FFFFFF`, `#E12832` | Repeated around the base | Fixture spacing unclear | `JWNowpO44rw_002005.366.jpg`, `JWNowpO44rw_001148.000.jpg`; render 02 | frame+render | estimated | new | Add colored light pools at the facade base. |
| RF39 | Shield lights | Shields catch stronger highlights than the surrounding lattice. | Red and white `#D0202A`, `#FFFFFF` | One illuminated surface per shield | Not measured | `JWNowpO44rw_002005.366.jpg`, `9I1korKNjig_001428.000.jpg`; render 02 | frame+render | estimated | new | Light the shield faces without changing their base colors. |
| RF40 | Roof membrane glow | The roof appears softly lit from below at night. | Pale green-white `#DDE8D9` | Broad canopy area | Not measured | `JWNowpO44rw_001148.000.jpg`, `-vWQtKeHyxs_000001.000.jpg`; render 02 | frame+render | estimated | new | Add a restrained underside glow. |
| RF41 | Ground fixtures | Freestanding lights are visible near the stadium in night views, but their exact form is unclear. | White `#F5F3E8` | Repeated around visible paved areas | Not measured | `JWNowpO44rw_001148.000.jpg`, `9I1korKNjig_001428.000.jpg` | frame | estimated | new | Use generic low-detail light poles outside the facade. |

## Conflicts

- The concept renders show a dark, tall base plinth. The facade frames show a pale low step, a recessed wall, and pale horizontal bands. Use the frame treatment.
- Some renders show the shields as larger and more uniformly spaced than the close facade views. The ledger records eight shields, each about 21 m wide. Use those estimates and the frame pattern.
- The renders show the roof as a smooth surface with clear radial divisions. The frames show the membrane and its seams, but the seam count and exact spacing remain unclear. Keep seam detail estimated.
- The renders show bright, continuous lighting across more facade areas. The frames show night lighting, but they do not establish permanent fixture positions or a complete lighting layout. Model the visible effect as a visualization.

## Not visible

- Exact louvre count per bay, fin gap, fastener type, lattice joint plates, shield fixings, and verified spear shaft or blade sections.
- Exact membrane panel count, seam spacing, material specification, roof edge flashing, and drainage details.
- Complete roof support connections, concealed underside steel, day fixture wiring, and precise fixture locations.
- A reliable total column count and measured spacing around the full base.
- A validated dirt pattern, maintenance condition, or long-term weathering pattern.

