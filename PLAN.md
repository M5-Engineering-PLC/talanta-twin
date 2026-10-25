# Talanta Twin plan

Date: 2026-10-16
Owner: Munene (CEO, M5 Engineering)
Status: plan, updated 2026-10-19. The app and the Blender model exist on branch claude/hopeful-archimedes-lo15is. Section 12 holds the current path to the landing concept. HANDOFF.md and engineering/START_HERE.md hold the build status.
Repository: M5-Engineering-PLC/talanta-twin (private)

## 1. Goal

Build a detailed three.js digital twin of Talanta Stadium (Raila Odinga Talanta Stadium, Ngong Road, Nairobi). The twin runs in a web browser. It shows the stadium, its site and its surroundings, and it simulates weather, crowds, events, traffic and shows.

The twin has two jobs:

1. It is the M5 showcase for 3D and simulation work.
2. It is a product to offer to the Ministry of Sports, Sports Kenya, the AFCON 2027 organizers, broadcasters and event promoters.

Timing: the stadium is due to open in November 2026, and it is a match venue for AFCON 2027. The window to pitch is now.

## 2. Principles

- Build a hero slice first. A hero slice is one short scene at final quality. Do not build all modules at medium quality.
- Every module has a claim label: visualization, simulation, or measured data. Crowd and evacuation visuals are visualizations until an engineer validates them.
- The public demo shows no security-sensitive detail: no control rooms, no security camera positions, no full exit plans. A private client build can hold more.
- Reference frames from YouTube are internal. The product uses our own geometry and textures only.
- The twin runs on a mid-range laptop and on a phone. Performance budgets are in section 8.

## 3. Architecture

### 3.1 Three rings of detail

| Ring | Area | Method |
|---|---|---|
| Hero | The stadium and its plot | Built by hand in Blender from the frame set, design facts and a satellite plan view. Full detail. |
| Near ring | About 1 km around the stadium | Built in code from building footprints and heights, OpenStreetMap roads, and materials matched to the frames. |
| Far ring | The horizon | Terrain from elevation data, low-detail imagery, and simple skyline shapes for Ngong Hills, the CBD and Kibera. |

### 3.2 Technology

- Renderer: three.js with WebGPU, and a WebGL 2 fallback.
- Assets: Blender to glTF, with meshopt geometry compression and KTX2 textures.
- Crowd: GPU instancing with baked vertex animation textures. One instance for each fan. Flow fields move fans through gates and aisles.
- Particles: GPU compute particles for rain, fireworks, drones, fountains and confetti.
- Lighting: a physical sky with a sun position from date, time and the stadium latitude and longitude. Floodlights as light groups with on, off and show states.
- Event logic: a timeline system. Each scenario (match, concert, show) is a script of timed events.
- UI: a control panel with toggles for weather, time of day, scenario and camera.
- Optional context: Google Photorealistic 3D Tiles through 3d-tiles-renderer, only if Google covers Nairobi. Never as the base of the twin.

### 3.3 Proposed repository layout

- `research/` reference data (exists)
- `gis/` clipped GIS data: footprints, roads, terrain
- `blender/` source .blend files and export scripts
- `app/` the three.js application
- `app/src/sim/` one folder for each simulation module
- `app/public/assets/` exported glTF and textures
- `docs/` module specs and test reports

## 4. Data

### 4.1 What we have (2026-10-16)

- 356 labeled reference frames from 33 videos (about 95 MB), with an index and a coverage report.
- Design facts from press reports: 60,000 seats, eight main gates with a shield motif, a seat gradient in green, red and black, a fixed roof on tensioned steel cables.

### 4.2 Is the frame set adequate?

Frame count for each view class: night lighting 54, bowl seating 48, exterior facade 46, roads and parking 42, construction 30, floodlights 30, aerial overview 22, pitch 22, roof canopy 18, other 16, gates and entrances 11, concourse interior 10, landscaping and fountain 7.

The set is adequate for:

- the look of the stadium: facade lattice and louvres, shield panels, roof trusses, seat colors, floodlights under the roof, the main gate and ticket buildings
- the materials and colors for the hero slice
- the night lighting and the fountain look

The set is not adequate for:

- dimensions. Frames from phone and drone videos carry no scale. We need a plan view and known sizes.
- the site plan: the positions of all eight gates, the parking areas and the roads from above
- the roof shape from above, in detail
- the concourse interior, the changing rooms and the VIP areas. These are lower priority, and some are security-sensitive.

Known weakness: the subjects for the 138 gap frames are generic (10 different subjects). The view classes are correct.

### 4.3 Data to add

| Source | Use | License or cost |
|---|---|---|
| Google Open Buildings 2.5D Temporal | Building footprints and heights for the near ring | CC BY 4.0 and ODbL, free |
| OpenStreetMap | Roads, footpaths, rail, names | ODbL, free, credit required |
| Copernicus GLO-30 | Terrain for the far ring | Free |
| Sentinel-2 | Ground color for the far ring | Free |
| Google Earth Pro historical imagery | Plan view reference and ruler measurements of the site (work order W1b). Measurements are facts we record | Do not export or trace the imagery into the product |
| Paid very-high-resolution satellite scene (Maxar or Airbus) | As-built site plan: gates, parking, landscaping | Paid. Buy only if free sources fail |
| Structure from motion on the drone clips (COLMAP) | A rough 3D point cloud of the bowl and roof, scaled with the pitch size | Free. Needs the raw drone videos |
| Football and rugby pitch standards | Scale reference: a FIFA pitch is usually 105 m by 68 m | Public. Confirm the real pitch size |
| Open-Meteo or Kenya Meteorological Department | Live weather for the weather sync module | Free API |
| Site visit with Sports Kenya permission | Photos and measurements | Needs permission. A drone flight needs a KCAA permit |

## 5. Simulation catalog

Status for all modules: planned. The phase numbers are in section 6.

Scope decision 2026-10-25 (Munene): build the full catalog, loaded progressively. engineering/scope_decision_2026-10-25.md gives the build order (phases A to D), the loading tiers, the labels and the state of each module. It replaces the phases in section 6. OPS-01, PPL-04 and MOB-04 go only into a private client build.

### 5.1 Environment and weather

| ID | Module | What it does | Phase |
|---|---|---|---|
| ENV-01 | Time of day | The sun moves for the real date and time in Nairobi. Sunrise, golden hour, sunset, night. | 1 |
| ENV-02 | Sunshine and clouds | Clear, partly cloudy and overcast skies with soft cloud shadows on the roof and pitch. | 1 |
| ENV-03 | Rain | Rain particles, wet seats and concourses with reflections, puddles, rain on the camera. Light, heavy and storm levels. | 1 |
| ENV-04 | Thunderstorm | Lightning flashes, dark sky, heavy rain. | 2 |
| ENV-05 | Fog and mist | Morning mist and haze over the far ring. | 2 |
| ENV-06 | Wind | Flags, trees and loose banners move with wind speed and direction. | 2 |
| ENV-07 | Live weather sync | The twin reads the real Nairobi weather and shows it. | 3 |
| ENV-08 | Seasons | Long rains, short rains and dry season presets. Jacaranda trees bloom purple in October and November. | 4 |
| ENV-09 | Ambient sound | Wind, rain, crowd murmur, traffic on Ngong Road, birds. | 2 |

### 5.2 People

| ID | Module | What it does | Phase |
|---|---|---|---|
| PPL-01 | Seated crowd | Up to 60,000 fans in the stands, in team colors, with idle motion. | 1 |
| PPL-02 | Crowd reactions | Cheer, goal celebration, Mexican wave, scarves up, phone lights at night. | 1 |
| PPL-03 | Fan arrival | Fans walk from roads, bus stops and parking to the gates, then to their seats. | 3 |
| PPL-04 | Gate queues | Queues and turnstile flow at each gate. Shows wait time for each gate. Visualization label. | 3 |
| PPL-05 | Fan exit | Fans leave after the event and the site empties. Visualization label. | 3 |
| PPL-06 | Concourse life | Fans at food stands, toilets and shops at half time. | 4 |
| PPL-07 | Staff and stewards | Stewards, security, medics, ball persons, media on the touchline. | 4 |
| PPL-08 | Accessible seating | Shows the seats and routes for fans with special needs. | 4 |

### 5.3 Sport

| ID | Module | What it does | Phase |
|---|---|---|---|
| SPT-01 | Football match | Two teams, referee and ball. Kick-off, passes, shots, goals, half time. Scripted play first, data-driven play later. | 1 |
| SPT-02 | Rugby fifteens | Scrums, lineouts, tries and kicks at goal. | 4 |
| SPT-03 | Rugby sevens | A sevens match, with the Kenya Shujaa as a showcase team. | 4 |
| SPT-04 | Football training | Warm-up, rondos, passing drills, shooting drills, goalkeeper training. | 4 |
| SPT-05 | Rugby training | Scrum machine, lineout practice, passing lines, fitness drills. | 4 |
| SPT-06 | Pre-match ceremony | Teams walk out, line-up, anthems, flag display on the pitch. | 2 |
| SPT-07 | Training pitch and mini stadium | The training pitch and mini stadium next to the main bowl, with their own sessions. | 4 |
| SPT-08 | Match replay | Replays a real match from published event data. Needs a data source with permission. | 5 |

### 5.4 Concerts and public events

| ID | Module | What it does | Phase |
|---|---|---|---|
| EVT-01 | Concert | A stage at one end, LED screens, stage lights, a crowd on the pitch and in the stands, light that follows the music. | 2 |
| EVT-02 | National celebration | Parade, march past, guard of honour, flypast. For Madaraka Day, Mashujaa Day or Jamhuri Day. | 4 |
| EVT-03 | Event planner sandbox | A promoter places a stage, screens and seating zones, and sees capacity and sight lines. | 5 |

### 5.5 Shows

| ID | Module | What it does | Phase |
|---|---|---|---|
| SHW-01 | Floodlight show | The floodlights switch on in sequence, flash and change color. | 2 |
| SHW-02 | Facade and roof light show | The facade and roof LEDs show colors, the Kenyan flag and moving patterns. | 2 |
| SHW-03 | Drone show | Hundreds of drones fly into shapes: the Kenyan flag, the AFCON logo, a shield, text. | 2 |
| SHW-04 | Fireworks | Shells from the roof edge and from the ground, timed to music. | 2 |
| SHW-05 | Fountain show | The site fountains with water jets and lights in a choreographed sequence. | 2 |
| SHW-06 | Show composer | A timeline tool that combines lights, drones, fireworks, fountains and music into one show. | 5 |

### 5.6 Traffic and mobility

| ID | Module | What it does | Phase |
|---|---|---|---|
| MOB-01 | Cars in and out | Cars enter from Ngong Road, park, and leave after the event. | 3 |
| MOB-02 | Parking fill | Each parking area fills and empties. Shows the percent full. | 3 |
| MOB-03 | Buses and matatus | Buses and matatus drop off and pick up fans. | 3 |
| MOB-04 | VIP convoy | A VIP convoy arrives with escort vehicles. | 4 |
| MOB-05 | Ngong Road traffic | Through traffic on Ngong Road and nearby roads. | 3 |
| MOB-06 | Air traffic | Light aircraft into and out of Wilson Airport, which is near the stadium. | 4 |
| MOB-07 | Rail spur | The proposed rail spur line to the stadium, if the plan is confirmed. | 5 |

### 5.7 Operations

| ID | Module | What it does | Phase |
|---|---|---|---|
| OPS-01 | Evacuation visualization | Fans move to exits in an emergency. Visualization label only. Private build only. | 5 |
| OPS-02 | Pitch care | Mowing patterns, sprinklers and grow lights on the hybrid pitch. | 4 |
| OPS-03 | Power and lighting load | Shows which systems are on and an estimated load. Estimate label. | 5 |
| OPS-04 | Sponsor boards | Preview of sponsor content on the LED boards and screens. | 4 |

### 5.8 Cameras and viewers

| ID | Module | What it does | Phase |
|---|---|---|---|
| CAM-01 | Cinematic fly-in | The camera flies in over Ngong Road to the stadium. The opening of the hero slice. | 1 |
| CAM-02 | Free orbit | The viewer orbits and zooms freely. | 1 |
| CAM-03 | Broadcast cameras | Main camera, cable camera over the pitch, goal cameras, tunnel camera. | 2 |
| CAM-04 | View from your seat | The viewer picks a block, row and seat and sees the view from it. Useful for ticket sales. | 3 |
| CAM-05 | Guided tour | A narrated tour of the stadium for the public. | 4 |
| CAM-06 | VR mode | WebXR view for a headset. | 5 |

### 5.9 Ambient life

| ID | Module | What it does | Phase |
|---|---|---|---|
| AMB-01 | Birds | Black kites and marabou storks over the site. | 2 |
| AMB-02 | Trees and planting | Site landscaping, trees that move in the wind. | 2 |
| AMB-03 | City skyline | The Nairobi CBD skyline and Ngong Hills on the horizon. | 1 |
| AMB-04 | Night city | City lights, street lights and car lights at night. | 2 |

## 6. Phases

Replaced on 2026-10-25 by the phases A to D in engineering/scope_decision_2026-10-25.md. The table below is the original plan.

| Phase | Name | Content | Done when |
|---|---|---|---|
| 0 | Data | Plan view, GIS clip, pitch scale, structure-from-motion test, design facts | A scaled site plan and a terrain tile exist in `gis/` |
| 1 | Hero slice | ENV-01, ENV-02, ENV-03, PPL-01, PPL-02, SPT-01, CAM-01, CAM-02, AMB-03 | A 90-second scene runs at the section 8 budgets and a review panel accepts it |
| 2 | Spectacle | All SHW modules except SHW-06, EVT-01, SPT-06, CAM-03, ENV-04, ENV-05, ENV-06, ENV-09, AMB-01, AMB-02, AMB-04 | Each module runs alone and in the show timeline |
| 3 | Operations | PPL-03, PPL-04, PPL-05, MOB-01, MOB-02, MOB-03, MOB-05, ENV-07, CAM-04 | One full match day runs from arrival to exit |
| 4 | Event library | All rugby and training modules, EVT-02, PPL-06, PPL-07, PPL-08, MOB-04, MOB-06, OPS-02, OPS-04, CAM-05, ENV-08 | Each scenario loads from the menu |
| 5 | Tools | EVT-03, SHW-06, SPT-08, OPS-01, OPS-03, MOB-07, CAM-06 | Client-specific. Starts only with a client |

## 7. Hero slice script (phase 1)

1. The camera flies in over Ngong Road at golden hour. Ngong Hills are on the horizon.
2. The roof catches the last sun. The shield panels on the facade glow.
3. The sun sets. The floodlights switch on.
4. The stands fill with 60,000 fans.
5. The viewer toggles rain. The seats and the concourse become wet and reflect the lights.
6. A football match plays. A goal scores, and the crowd reacts.
7. The camera pulls back to show the stadium in the night city.

Length: about 90 seconds. It also exists as a recorded video for people who do not open the link.

## 8. Performance budgets

| Item | Laptop target | Phone target |
|---|---|---|
| Frame rate | 60 fps | 30 fps |
| First view | 5 s on a 20 Mbit/s link | 8 s on a 20 Mbit/s link |
| Download before first view | 30 MB maximum | 15 MB maximum |
| Draw calls | 300 maximum | 150 maximum |
| Crowd | 60,000 instances, 3 levels of detail | 20,000 instances, then impostors |

Test hardware: a mid-range laptop with integrated graphics and a mid-range Android phone. Record the device names in each test report.

## 9. Build method

This method follows the Argon example from Google: build, render, critique, fix.

1. A builder agent changes the Blender file or the three.js scene.
2. A script renders fixed camera views to images.
3. A critic agent compares the renders with the matching reference frames from the index, and lists the differences.
4. The builder fixes the differences. Repeat until the critic finds no major difference.

Work split:

| Work | Owner |
|---|---|
| Plan, architecture, final review, pitch | Lead (Opus) |
| Blender modeling with visual iteration | Sonnet worker with the Blender MCP |
| three.js engine and simulation modules | Sol (Codex) |
| GIS processing, scripts, batch jobs, test runs | Luna (Codex) |
| Frame lookup and long reading | Haiku worker |
| Cross-review of each change | Sol, read-only |

The current execution plan, with the Codex-first split and the phase 0 work orders, is in engineering/execution_plan_2026-10-16.md.

## 10. Risks

| Risk | Control |
|---|---|
| Copyright on YouTube footage | Frames are internal reference only. License the best clips if the pitch needs real-and-twin comparisons. |
| YouTube terms forbid downloads | Known breach of the terms. Keep the raw videos local, and remove them after use. |
| Security of a national venue | No sensitive detail in the public build. |
| Wrong dimensions | Scale from a satellite plan view and the pitch size. Mark estimated sizes. |
| Overclaiming safety | Visualization labels on every crowd and evacuation module. |
| Official name change | The stadium is now also named after Raila Odinga. Use both names in the pitch. |
| Competing work | A third-party 3D render of Talanta exists (video oL3wsPsx4Jw). The twin must be clearly better. |
| Low-end devices in government offices | WebGL fallback and phone budgets in section 8. |

## 11. Open decisions

1. Track: M5 project or separate venture.
2. Domain: Munene checks and buys the domain.
3. First buyer contact: Ministry of Sports, Sports Kenya, or the AFCON 2027 organizers.
4. Clip licenses: which channel owners to contact.
5. Paid satellite scene: buy one or not, after the free sources are tested.
6. Landing light: keep the morning bake as the web default, or add an evening bake for the sunset landing (section 12, L5).
7. Landing framing: decided 2026-10-19 (Munene): the landing mirrors mockups 06 and 07. Cameras L06 and L07 (section 12, L2).
8. Download budget for hero mode: raise the section 8 budget, or build a light bundle (section 12, L8).

## 12. Path to the landing concept (added 2026-10-19)

Target: the landing mockups 06 (Hillside) and 07 (Cityside) on branch `munene/CAM-01-landing-option`, folder `product/landing-concepts/2026-10-18/`. They are generated images. They set the interface, light and composition only. The footage and `gis/parameter_ledger.csv` still decide geometry and layout (engineering/plan_concept_match_2026-10-17.md, "Decisions"). The mockups never go into a build, texture, pitch or public page.

### 12.1 Gap list against the existing plans

Compared on 2026-10-19: the live landing (`/?hero`, web_hero_v1 bundle) against mockups 06 and 07.

| Gap | Mockup | Live landing today | Already planned in | New in this section |
|---|---|---|---|---|
| Interface | Ivory header, View, Time of day and Event card, Take a tour, compass | Matches. Caption fixed to "60,000 design capacity" (e82b775) | CAM-01 landing mode (fd12fa7) | Real-phone test only |
| Light and sky | Golden or sunset light, cloud sky, warm facade, lamps lit | 07:30 morning bake. In hero mode the Time of day control does not relight the baked model | Roadmap P8 (day, dusk and night presets, procedural scene only). The concept-match decision keeps one morning bake for the web and 17:30 for the C20 still only | L5: an evening bake for hero mode, if Munene approves (open decision 6) |
| Ground and forecourt | Paving, lawns, planted beds, lit paths | Pale, blotchy ground in the bake. The Cycles stills (C19, C20) show the forecourt correctly | Forecourt layout (engineering/forecourt_layout_2026-10-18.md) is built in Blender with claim labels. Roadmap P2 and P4. HANDOFF task 5 (blotches) | L3: the fault is in the bake or the ground tile export, not in the model |
| Framing | Stadium large, camera low and close | C19 and C20 framing: stadium about 37% of the frame width | Concept-match gap 1 (C19 and C20 solved to concepts 05 to 07) | L2: the landing mockups are closer than the lead renders. Choose one (open decision 7) |
| Life | Visitors on the forecourt, cars, lit streetlights | Ngong Road traffic only | Roadmap P9 (seated crowd). The newer `app/src/hero/crowd.js` is uncommitted in the old web-crowd worktree (HANDOFF) | L6: forecourt visitors in hero mode, labelled Visualization |
| Model detail | Quilted roof, full trees, a city skyline from Cityside | Smooth roof, simple tree crowns, box buildings | Stage 03 specialist builds, roadmap P3, concept-match gaps 3, 4 and 6 | none |
| Download size | n/a | About 107 MB of models before the first view | Section 8 sets 30 MB (laptop) and 15 MB (phone). Roadmap P7 sets quality levels | L8: the hero bundle is over budget. Decide (open decision 8) |
| First impression | A finished, photographic picture | About 34 s to the first full view in software GL | Concept-match "stills first" | L1: a Cycles still as the landing backdrop |

### 12.2 New work items

| ID | Work | Size | Depends on | Done when |
|---|---|---|---|---|
| L1 | Landing backdrop. Render C19 (07:30) and C20 (17:30) in CPU Cycles at 1920 x 1080 from our own model. Show the still behind the landing interface at once. Load the live scene behind it and cross-fade when it is ready or when the viewer presses Explore the twin. A small on-screen label says "Rendered from the twin model" | M | none | The landing shows a finished picture in under 5 s on a 20 Mbit/s link. The stills hold no frame, concept or Google Earth pixels |
| L2 | Landing framing. Keep C19 and C20, or add closer landing cameras after open decision 7 | S | decision 7 | Both views match the chosen framing in the app and in Cycles |
| L3 | Ground fault. Find the cause of the pale blotches (terrain colour noise or the light bake), fix it and re-export the ground tiles only | M | none | The ground in the hero view matches the C19 still in colour within the bake limits |
| L4 | Ground tiles and panorama in the app (HANDOFF tasks 2 and 3) | M | none | 61 tiles load near the camera first. The 8K panorama loads on capable devices |
| L5 | Evening bake for hero mode, if approved. About 11 h CPU. Time of day switches the lightmap set and the panorama. Lamps and facade lights on at dusk | L | decision 6 | Sunset in hero mode shows evening light, not the morning bake |
| L6 | Forecourt visitors and lit lamps in hero mode. Commit the crowd work from the web-crowd worktree first | M | crowd.js committed | Visitors stand only on walkable surfaces. Label "Visualization" on screen |
| L7 | Release as `web_hero_v2`. Never replace the files in web_hero_v1 | S | L3, and L5 if approved | A prerelease with a manifest; `npm run fetch-assets -- --bundle web_hero_v2` passes |
| L8 | Download budget. Measure the hero first view on the test laptop (Intel UHD 620) and a mid-range phone. Then raise the budget for hero mode, or split a light bundle | M | L1 | The section 8 table holds the decided numbers and the measured ones |

### 12.2a Status (2026-10-19)

| ID | Status |
|---|---|
| L1 | Code done (1622f12). Stills from cameras L06 (18:05, sunset) and L07 (10:30, daylight) in blender/renders/landing_pass_01/ |
| L2 | Done. L06 and L07 solved to the mockups (004d5f2); C19 and C20 unchanged |
| L3 | Cause found and fixed in export_web.py (dd2f05f): the export shipped ground_site.jpg (600 px raw imagery) as the ground colour instead of the baked albedo. L3b: bake_ground_albedo.py and node/patch_ground_albedo.mjs re-bake the 24 ground albedo maps and patch the site GLB into web_hero_v2 without the 11 h light bake |

### 12.3 Order

1. L1 and L3 first. L1 gives the mockup look on the first screen. L3 removes the most visible fault in the live scene.
2. L4 and L8 next. They make the live scene behind the backdrop fast enough to matter.
3. L2, L5 and L6 after Munene's decisions 6 and 7.
4. L7 last, as one new bundle.

Rules for every item: AGENTS.md applies. The backdrop stills are renders of our own model, so they may appear in the product once Munene approves them. The mockups and the lead concept renders may not. Crowd views carry the Visualization label. No gates, exits, camera positions or control rooms.
