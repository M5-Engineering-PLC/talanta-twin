# Detail sheet: People, Crowd and Life

All people, crowd, traffic and night activity in this sheet are Visualization. Counts, densities and colors are build estimates unless a ledger row or source frame supports them. Keep all people anonymous. Do not add slogans, advertisements or real person details.

## Bowl crowd

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-01 | Matchday occupancy | Seated fans across all tiers, with small gaps around aisles | Clothing mix: red #B92332 35%, black #222222 25%, green #18733D 20%, white #E8E4D8 20% | 85–95% of seats occupied; about 1 person per 0.5 m seat pitch | 1.6–1.9 tall | `JWNowpO44rw_000200.000.jpg`; `JWNowpO44rw_000800.000.jpg`; render 03 | conflict | estimated | bowl.seat_pitch | Instance anonymous seated figures and leave aisle gaps. |
| PL-02 | Lower-tier density | Tight rows of seated figures, with visible seat-color speckles between bodies | Red #B92332, green #18733D, black #222222, neutral #E8E4D8 | 16–19 people per 10 m of row; 85–95% occupied | 1.6–1.9 tall | `JWNowpO44rw_000200.000.jpg`; render 03 | conflict | estimated | bowl.seat_pitch | Place one figure at most seat positions. |
| PL-03 | Middle-tier density | Seated rows with breaks at stairs and cross aisles | Red #B92332 40%, black #222222 25%, green #18733D 15%, neutral #E8E4D8 20% | 16–19 people per 10 m of row; 85–95% occupied | 1.6–1.9 tall | `JWNowpO44rw_000200.000.jpg`; `JWNowpO44rw_000800.000.jpg`; render 03 | conflict | estimated | bowl.seat_pitch | Keep seating density even across each block. |
| PL-04 | Upper-tier density | Dense seated rows, with slightly more empty seats near aisles | Red #B92332 40%, black #222222 30%, green #18733D 10%, neutral #E8E4D8 20% | 15–18 people per 10 m of row; 80–90% occupied | 1.6–1.9 tall | `JWNowpO44rw_000200.000.jpg`; `JWNowpO44rw_000800.000.jpg`; render 03 | conflict | estimated | bowl.seat_pitch | Add small gaps beside stairs and rails. |
| PL-05 | Stand-wide clothing mix | Varied shirts, jackets and headwear; no visible marks or lettering | Red #B92332 35%, black #222222 25%, green #18733D 20%, white #E8E4D8 20% | Repeat this mix across each tier | 0.45–0.7 wide per figure | render 03 | render | estimated | new | Randomize colors within the stated mix. |
| PL-06 | Supporter scarves | Narrow fabric strips held overhead or across shoulders | Red #B92332, green #18733D, black #222222, white #F2F0E8 | 1 scarf per 12–20 visible fans | 1.3–1.6 long | render 03 | render | estimated | new | Use plain stripes with no text or logos. |
| PL-07 | Small hand flags | Short poles and rectangular cloth, shown above seated rows | Kenya flag colors: black #111111, red #BB0000, green #006600, white #FFFFFF | 1 per 25–40 visible fans | 0.3–0.5 cloth height | render 03 | render | estimated | new | Use simple cloth planes with gentle bends. |
| PL-08 | Large Kenya flag | Broad cloth flag held across a seating block | Black #111111, red #BB0000, green #006600, white #FFFFFF | 1 large flag in the bowl | About 12–18 wide | render 03 | conflict | estimated | new | Keep the flag within one seating block. |
| PL-09 | Vuvuzelas and hand props | Short tapered horns and a few plain clappers, held above shoulder level | Yellow #E5B52C, red #B92332, green #18733D, black #222222 | 1 prop per 30–50 visible fans | 0.4–0.7 long | render 03 | render | estimated | new | Scatter props sparingly; omit labels. |
| PL-10 | Empty-seat ratio | Visible seat gaps around aisles and scattered through the crowd | Seat colors from ledger: #3ca07e, #c4283a, #2b2b2e | 5–15% empty seats by tier | Existing seat dimensions: 0.44 wide, 0.42 high | `JWNowpO44rw_000200.000.jpg`; `JWNowpO44rw_000800.000.jpg`; render 03 | conflict | estimated | bowl.seat.width; bowl.seat.pan_h | Keep gaps scattered; preserve clear aisles. |

## Players and officials

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-11 | Home team | Generic short-sleeve shirts, shorts and socks; no numbers or marks | Red #B92332 shirts, black #222222 shorts, red #B92332 socks | 11 players | 1.7–1.9 tall | render 03 | conflict | estimated | new | Use plain kit shapes with no lettering. |
| PL-12 | Away team | Generic short-sleeve shirts, shorts and socks; no numbers or marks | White #E8E4D8 shirts, green #18733D shorts, white #E8E4D8 socks | 11 players | 1.7–1.9 tall | render 03 | conflict | estimated | new | Keep kit details plain and unbranded. |
| PL-13 | Goalkeepers | Long-sleeve tops and shorts in a contrasting solid color | Yellow #D8B629 or blue #315E9B | 2 players | 1.7–1.9 tall | render 03 | render | estimated | new | Use one keeper at each goal area. |
| PL-14 | Match officials | Plain dark kit, with one referee near play and assistants near touchlines | Black #222222 with yellow #D8B629 accents | 3 officials | 1.65–1.9 tall | render 03 | conflict | estimated | new | Place officials across the pitch without badges. |
| PL-15 | Player spacing | Small groups around midfield and separate figures near the penalty areas | Kit colors as above | 22 players; typical group gap 3–15 m | 0.45–0.7 shoulder width | render 03 | conflict | estimated | new | Use a simple match layout with no real team identity. |

## Stewards and event staff

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-16 | Hi-vis stewards | Generic vest over dark clothing; blank vest surface | Lime #C6D72C, charcoal #252525 | 1 per 30–50 m along visible touchline | 1.6–1.9 tall | `JWNowpO44rw_000046.932.jpg`; render 03 | frame+render | estimated | new | Use plain vests and no fixed post positions. |
| PL-17 | Pitch-side event staff | Small groups in simple dark clothing and plain hi-vis vests | Charcoal #252525, lime #C6D72C, white #E8E4D8 | 8–16 figures around the pitch edge | 1.6–1.9 tall | `JWNowpO44rw_000046.932.jpg`; render 03 | frame+render | estimated | new | Place figures in loose groups beside the field. |
| PL-18 | Ball attendants | Generic youth-sized figures in plain bibs, outside the playing area | Yellow #D8B629 or orange #C66A2A | 4–6 figures, spaced around touchlines | 1.3–1.7 tall | render 03 | render | estimated | new | Use simple bibs without numbers. |
| PL-19 | General event crew | Plain dark trousers and neutral tops, with occasional hi-vis vest | Charcoal #252525, grey #9A9A96, lime #C6D72C | 6–12 figures near field edge | 1.6–1.9 tall | `JWNowpO44rw_000046.932.jpg`; render 03 | frame+render | estimated | new | Keep figures generic and away from sensitive areas. |

## Forecourt life

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-20 | Families | Pairs and small groups walking together across open paving | Mixed clothing: red #B92332, green #18733D, blue #426A91, neutral #D8D0C1 | 2–5 people per group; 6–12 groups | 1.0–1.9 tall | render 04, 06 | conflict | estimated | site.people.count | Use varied family-sized groups without face detail. |
| PL-21 | Walking groups | Small clusters moving along broad paths | Mixed muted colors: #B92332, #18733D, #426A91, #D8D0C1 | About 20–40 people per 100 m² in the busiest patch | 1.0–1.9 tall | render 04, 06, 07 | conflict | estimated | site.people.count | Leave open walking lanes between groups. |
| PL-22 | Vendors | One or two small handcarts or plain tables beside pedestrian flows | Cart #8B633E; canopy #D8D0C1 | 2–5 vendor figures, 1 cart per cluster | Cart 0.8–1.2 wide, 1.5–2.0 long | render 04, 06 | render | estimated | new | Use blank cart panels with no signs. |
| PL-23 | Forecourt density | Loose pedestrian groups, with open paving visible between them | Clothing mix as above | 5–15 people per 100 m² across open space | 1.0–1.9 tall | render 04, 06, 07; `8n3ILabO8uw_000007.000.jpg` | conflict | estimated | site.people.count | Vary density by path and planting edge. |
| PL-24 | Forecourt gathering | Small stationary groups facing one another | Clothing mix as above | 3–6 figures per group; 4–8 groups | 1.0–1.9 tall | render 04, 06 | render | estimated | new | Give each group a relaxed standing pose. |
| PL-25 | Forecourt scale | Small anonymous figures beside paving, planted edges and fountain zone | Clothing mix as above | 30–80 figures across the broad view | 1.0–1.9 tall | render 04, 06; `8n3ILabO8uw_000012.000.jpg` | conflict | estimated | new | Keep figures small in wide exterior views. |

## Ngong Road and access traffic

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-26 | Matatus | Generic high-roof minibus shapes with blank sides and no route text | White #E7E4DC, blue #356A9A, green #47764B, yellow #C9A52C | 8–15 in the wide road view | 4.5–5.5 long, 1.8–2.1 wide | render 06, 07 | conflict | estimated | new | Use plain color blocks with no slogans. |
| PL-27 | Matatu color mix | Repeated solid-color schemes, with simple windows and dark tires | White #E7E4DC 35%, blue #356A9A 25%, green #47764B 20%, yellow #C9A52C 20% | Repeat in small groups of 2–4 vehicles | As above | render 06, 07 | render | estimated | new | Randomize only among the stated colors. |
| PL-28 | Passenger cars | Compact sedan and hatchback shapes with neutral paint | White #E7E4DC 35%, grey #858681 30%, black #252525 20%, blue #426A91 15% | 25–45 cars across the visible road stretch | 4.0–4.8 long, 1.6–1.9 wide | render 06, 07 | conflict | estimated | new | Use simple unbranded vehicle bodies. |
| PL-29 | Boda bodas | Small motorcycle silhouettes with one or two riders | Black #252525, red #B92332, blue #356A9A, neutral #A8A69F | 6–12 across the visible road stretch | 1.8–2.2 long, 0.7–0.9 wide | render 06, 07 | render | estimated | new | Keep rider shapes anonymous and small. |
| PL-30 | Buses | Full-size plain bus shapes with blank side panels | White #E7E4DC, blue #356A9A or green #47764B | 2–5 in the broad traffic view | 10–12 long, 2.4–2.6 wide | render 06, 07 | render | estimated | new | Do not add operator names or markings. |
| PL-31 | Road traffic density | Multi-lane vehicle flow with visible spaces between vehicles | Road vehicles in colors above | 35–65 vehicles per 500 m visible road section | Vehicle lengths as above | render 06, 07; `020A-X2A2V4_000106.000.jpg` | conflict | estimated | new | Use uneven gaps and mixed vehicle types. |
| PL-32 | Traffic mix | Cars, matatus, boda bodas and buses in a loose mix | Cars 55%, matatus 20%, boda bodas 20%, buses 5% | Apply to moving road traffic | Mixed vehicle sizes as above | render 06, 07 | render | estimated | new | Mix types across the visible lanes. |
| PL-33 | Vehicle spacing | Short gaps in busier lanes and longer gaps near the road edge | Vehicle colors as above | 1–3 vehicle lengths between most vehicles | 2–30 m spacing | render 06, 07 | render | estimated | new | Offset vehicles to avoid a regular pattern. |
| PL-34 | Roadside people | Small figures walking beside the road or near the forecourt | Neutral clothing with occasional red or green | 5–15 figures per visible 100 m of sidewalk | 1.0–1.9 tall | render 06, 07 | render | estimated | new | Keep pedestrians on the broad public walk areas. |
| PL-35 | Access-road vehicles | A few generic cars or service vehicles on the visible access road | White #E7E4DC, grey #858681, blue #356A9A | 2–8 vehicles in view | Cars 4.0–4.8 long | `KEOmkVfjhu8_001330.000.jpg`; render 06 | conflict | estimated | new | Use generic bodies; do not imply an access route. |

## Parked vehicles

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-36 | Parked cars | Short rows of compact cars, separated by visible gaps | White #E7E4DC 35%, grey #858681 30%, black #252525 20%, blue #426A91 15% | 20–50 cars in the visible parking area | 4.0–4.8 long, 1.6–1.9 wide | render 06, 07 | conflict | estimated | new | Keep rows loose and avoid exact stall counts. |
| PL-37 | Parked minivans | A few plain vans among cars | White #E7E4DC, blue #356A9A, grey #858681 | 3–8 vans per visible parking patch | 4.5–5.5 long, 1.8–2.1 wide | render 06, 07 | render | estimated | new | Use unmarked boxy silhouettes. |
| PL-38 | Parking occupancy | Open gaps between parked vehicles, without a fixed stall pattern | Vehicle colors as above | About 50–75% of visible spaces occupied | Spacing 1–2 m between vehicles | render 06, 07 | render | estimated | new | Leave some visibly open parking space. |

## Night activity

| id | element | detail (shape, proportions, materials, finish) | colour (hex, by eye) | count or spacing | size (m, by eye or from ledger) | source (frame file names and/or render numbers) | agreement | status | ledger row (name if it exists, else "new") | build note (one short instruction for Blender) |
|---|---|---|---|---|---|---|---|---|---|---|
| PL-39 | Phone lights | Small cool-white points held above seated rows | White #F3F4FF with a faint blue tint #BFD4FF | 1 light per 40–80 visible fans | Point light; no visible device detail | render 03 | conflict | estimated | new | Scatter dim lights across several blocks. |
| PL-40 | Waving flags | Small flags with cloth bends and slight motion blur in the night scene | Kenya flag colors: #111111, #BB0000, #006600, #FFFFFF | 1 per 25–40 visible fans | 0.3–0.5 cloth height | render 03 | render | estimated | new | Add mild movement to a few flags. |
| PL-41 | Large flag at night | One broad Kenya flag across a seating block | #111111, #BB0000, #006600, #FFFFFF | 1 large flag | About 12–18 wide | render 03 | conflict | estimated | new | Light the cloth softly; keep it plain. |
| PL-42 | Night crowd lights | Scattered phone lights within occupied seating rows | White #F3F4FF, blue-white #BFD4FF | 1–3 lights per 100 visible fans | Point lights only | render 03 | conflict | estimated | new | Keep the lights sparse and low intensity. |
| PL-43 | Night crowd silhouette | Darker figure outlines against the lit bowl and pitch | Clothing colors darken toward #242424, #31513D, #6B252B | 80–95% of seats occupied for the match scene | 1.6–1.9 tall | `JWNowpO44rw_001148.000.jpg`; render 03 | conflict | estimated | bowl.seat_pitch | Preserve the lit bowl shape; keep faces anonymous. |

## Conflicts

- The inspected real bowl frames show empty seating and no match crowd. Render 03 shows heavily occupied tiers, large flags, scarves, props, players and officials. Crowd density and event details are estimates for visualization.
- The real pitch and bowl frames show the pitch and seating structure but do not show a match. Render 03 adds players and officials. Their kits and positions are generic estimates.
- Real forecourt frames show paved areas, planting, fountains and sparse or distant people. Renders 04, 06 and 07 show more pedestrian activity. The family, vendor and crowd counts are estimates.
- The selected real access-road frame shows a site road under construction, while renders 06 and 07 show moving and parked traffic. Vehicle types, mix, density and parking occupancy are estimates.
- The real night frame shows stadium lighting with an empty-looking bowl. Render 03 adds a full night crowd, phone lights and flags. These details are visualization estimates.

## Not visible

- The inspected frames do not show matchday crowd clothing mixes, scarves, vuvuzelas, player kit detail, vendor activity or parked-car occupancy.
- The renders do not establish real event crowd density, traffic counts, parking capacity or vehicle proportions.
- Exact human scale, body proportions, clothing materials and night motion need visual tuning during the Blender build.
- The specific crowd colors and ratios in this sheet are estimates. The frames show seat colors, not fan clothing colors.
