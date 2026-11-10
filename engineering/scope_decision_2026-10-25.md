# Scope decision: the full catalog, loaded progressively (2026-10-25)

Date: 2026-10-25
Project: Talanta twin (M5)
Decision by: Munene, 2026-10-25
Status: decided. This file replaces the phases in PLAN.md section 6. The module tables in PLAN.md section 5 stay.
Update 2026-10-27 (Munene): keep both plans. Phase A is the base. The PLAN.md section 7 hero slice is the first demo milestone, built on phase A (see "Demo milestone: the hero slice").
Basis: a read-only review by Sol of all PLAN.md section 5 modules against pitch/Talanta_value_proposition_2026-10-18.md (2026-10-25).

## Decision

1. Build the broad catalog. The goal is to impress. Sol advised a small promotion-first pilot. Munene chose a broad scope.
2. Keep the security rule. Three modules stay out of the public product, because they need security-sensitive detail. They go only into a private client build (see "Private build only").
3. Every other module that Sol dropped comes back into the public product, with a clear label.
4. The page loads progressively. The first view stays light. The modules load in the background or when a visitor selects them (see "Loading").
5. The labels from Sol's review are mandatory (see "Labels").

## Loading

The first view must meet the PLAN.md section 8 budgets: first view in 5 s on a laptop and 8 s on a phone at 20 Mbit/s, and 30 MB and 15 MB before the first view.

| Tier | When it loads | Content |
|---|---|---|
| 0, first view | At once | The landing still (Cycles, L06 or L07), the page interface, a light scene shell |
| 1, background | After the first view, when the browser is idle | The web_hero_v2 baked scene, time of day, the seated crowd |
| 2, on demand | When a visitor opens the menu or points at a module, the module starts to download. It runs when the visitor selects it. | Each module is its own code chunk with its own assets |

Rules:
- Each module is a separate dynamic import. No module adds to the tier 0 download.
- Show a small progress indicator while a module loads. The scene stays usable.
- Each heavy module has a phone version (fewer instances, simpler effects) or a short pre-rendered clip as a fallback. Examples: the drone show, fireworks, thunderstorm, the full crowd.
- Remove a module from memory when the visitor leaves it, if the device is low on memory.
- Measure each module against section 8 on a named office PC and a named phone before it ships.

## Private build only

| ID | Module | Reason |
|---|---|---|
| OPS-01 | Evacuation visualization | Needs real exits and routes. PLAN.md already limits it to private builds. |
| PPL-04 | Gate queues | Needs real gate positions and flow, and wait times would read as predictions. |
| MOB-04 | VIP convoy | Shows protected arrival routes. |

Each one needs separate authorization from the client and a security boundary before design starts.

## Build order

The modules already built are marked "built". "Partial" means that part of the module exists.

### Phase A: base (now)

| ID | Module | What the visitor sees | State |
|---|---|---|---|
| - | Landing stills | The approved hero_artistic_04 stills as the landing backdrop, with a portrait crop for phones | Not started |
| - | web_hero_v2 | The baked scene with passes I, J and K | In progress (cloud, W3) |
| - | Module loader | Tiers 0, 1 and 2 above, and a correct registry.js | Not started |
| ENV-01 | Time of day | The real sun path in Nairobi, sunrise to night, on the baked scene | Partial |
| PPL-01 | Seated crowd | Fans in the stands, in team colours | Built |
| PPL-02 | Crowd reactions | Cheer, goal, Mexican wave, scarves, phone lights | Built |
| SHW-01 | Floodlight show | The floodlights switch on in sequence and change colour | Built |
| SHW-02 | Facade and roof light show | Colours, the Kenyan flag and patterns on the facade and roof | Built |
| SHW-03 | Drone show | Drones form shapes above the north forecourt | Built |
| CAM-01 | Cinematic fly-in | The camera approaches the stadium | Partial |
| CAM-02 | Free orbit | Turn and zoom around the venue | Built |
| AMB-02 | Trees and planting | The landscaped grounds | Partial |
| AMB-03 | City skyline | Nairobi and the Ngong Hills on the horizon | Partial |

### Demo milestone: the hero slice (added 2026-10-27)

The first demo is phase A plus the 90-second hero slice from PLAN.md section 7. The hero slice runs on the phase A base and its module loader. It is also recorded as a video for people who do not open the link.

These items move forward from phases B and C into the milestone. Only the parts that the script uses are in scope. The rest of each module stays in its phase.

| ID | Module | Part in the milestone | From phase |
|---|---|---|---|
| ENV-02 | Sunshine and clouds | Clear and overcast skies for the golden hour and the rain beat | C |
| ENV-03 | Rain | Rain on and off, wet seats and concourse that reflect the floodlights | C |
| SPT-01 | Football match | One scripted goal and the crowd reaction (PPL-02) | B |
| CAM-01 | Cinematic fly-in | The full directed sequence of PLAN.md section 7, steps 1 to 7 | A (partial) |

Script (PLAN.md section 7): fly-in over Ngong Road at golden hour, the roof catches the last sun, sunset and floodlights on, the stands fill, the viewer toggles rain, a goal and the crowd reaction, pull back to the night city.

Done when:
- Phase A meets its own acceptance and the section 8 budgets.
- The 90-second sequence plays end to end in the browser on a named laptop and a named phone.
- The recorded video of the sequence exists.
- A review panel accepts the build.

The labels in "Labels" apply. The rendered crowd is a Visualization and does not show the capacity of the venue.

### Phase B: the headline events

| ID | Module | What the visitor sees |
|---|---|---|
| SPT-01 | Football match | A scripted match: kick-off, goals, celebrations |
| SPT-06 | Pre-match ceremony | Teams walk out, flags, anthems |
| EVT-01 | Concert | A stage at one end, LED screens, stage lights, a crowd on the pitch, light that follows the music |
| OPS-04 | Sponsor boards | Sample sponsor content on the LED boards and screens |
| EVT-02 | National celebration | A parade, march past, guard of honour and flypast for a national day |
| SHW-04 | Fireworks | Shells from the roof edge and the ground, timed to music |
| CAM-04 | View from your seat | The visitor picks a seat and sees the view |
| CAM-05 | Guided tour | A tour with short explanations |
| PPL-08 | Accessible seating | Seats and routes for fans with special needs |
| ENV-09 | Ambient sound | Crowd, wind, rain, traffic and birds (sound off by default) |

### Phase C: the living venue

| ID | Module | What the visitor sees |
|---|---|---|
| ENV-02 | Sunshine and clouds | Clear, partly cloudy and overcast skies with cloud shadows |
| ENV-03 | Rain | Rain, wet seats and concourses, puddles |
| ENV-04 | Thunderstorm | Lightning, a dark sky, heavy rain |
| ENV-05 | Fog and mist | Morning mist and haze |
| ENV-06 | Wind | Flags, trees and banners move |
| ENV-07 | Live weather sync | The scene follows the real Nairobi weather (now a read-only card) |
| ENV-08 | Seasons | Long rains, short rains, dry season; jacaranda bloom in October and November |
| AMB-01 | Birds | Birds above the site |
| AMB-04 | Night city | The city lights up after dark |
| PPL-03 | Fan arrival | Fans walk from the roads and stops to the stadium, in general terms |
| PPL-05 | Fan exit | The site empties after the event, in general terms |
| PPL-06 | Concourse life | Fans at food stands and shops at half time |
| PPL-07 | Staff and stewards | Stewards, medics, ball persons, media, in general positions |
| MOB-01 | Cars in and out | Cars arrive, park and leave |
| MOB-02 | Parking fill | Car parks fill and empty, with an illustrative percent |
| MOB-03 | Buses and matatus | Drop-off and pick-up of fans |
| MOB-05 | Ngong Road traffic | Through traffic on the nearby roads |
| MOB-06 | Air traffic | Light aircraft to and from Wilson Airport |

### Phase D: depth and tools

| ID | Module | What the visitor sees |
|---|---|---|
| SPT-02 | Rugby fifteens | A rugby match |
| SPT-03 | Rugby sevens | A sevens match |
| SPT-04 | Football training | Training drills |
| SPT-05 | Rugby training | Rugby drills |
| SPT-07 | Training pitch and mini stadium | Sessions on the side facilities |
| SPT-08 | Match replay | A match rebuilt from event data |
| SHW-05 | Fountain show | Water jets and lights in a sequence |
| SHW-06 | Show composer | A timeline tool that combines lights, drones, fireworks and music |
| EVT-03 | Event planner sandbox | A promoter places a stage, screens and seating zones |
| CAM-03 | Broadcast cameras | Broadcast-style views (not the real camera positions) |
| CAM-06 | VR mode | Explore with a headset |
| OPS-02 | Pitch care | Mowing, sprinklers, grow lights |
| OPS-03 | Power and lighting load | Which systems are on, and an estimated load |
| MOB-07 | Rail spur | The proposed rail spur, shown as a proposal |

Two product items are not in the section 5 catalog. Add them in phase B: approved venue information, and an "enquire about an event" path.

## Labels

These labels are mandatory on screen:

| Modules | Label |
|---|---|
| PPL-01 to PPL-07 | Visualization. Illustrative crowd behaviour, not validated safety, capacity or crowd-flow evidence. |
| PPL-08 | Illustrative access preview. Follow approved venue accessibility information. |
| CAM-04 | Approximate view from the model. |
| EVT-03 | Concept layout. Capacity and sight lines are not verified. |
| SHW-01 to SHW-06, EVT-01, EVT-02 | Illustrative event concept. Installed equipment and operational feasibility are not confirmed. |
| MOB-02 | Illustrative occupancy, not a measurement. |
| OPS-03 | Estimate. |
| MOB-07 | Proposal. Not a confirmed connection. |
| ENV-07 | Name the provider, the time, the place, and whether the value is observed or a forecast. |

Rendered fan counts do not show the capacity of the venue. CAM-03 must not show the real broadcast or security camera positions.

## Open decisions

- The first buyer. Sol suggests Sports Kenya as a provisional choice. Not decided.
