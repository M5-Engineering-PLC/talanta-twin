# 14 Talanta Twin

Created: 2026-10-15
Status: idea and reference collection
Track: to decide. This is a candidate M5 3D showcase. M5 scope today is Sawa, BomaHealth and Biodesign, so this folder stays separate until Munene decides the track.

## Objective

Build a detailed three.js digital twin of Talanta Stadium (Raila Odinga Talanta Stadium, Nairobi). Use it as a showcase of M5 3D work and pitch it to the Ministry of Sports, Sports Kenya and the AFCON 2027 organizers.

## Folder map

- notes/ - brainstorm, decisions, meeting notes
- research/ - sourced facts and the frame reference set
  - research/frames/ - selected reference frames, one subfolder per source video
  - research/video_index/ - per-video index of what each frame shows
- product/ - scope, feature list, hero slice spec
- engineering/ - three.js and Blender build notes
- pitch/ - pitch plan and outreach
- archive/ - source material as received
  - archive/video/ - downloaded YouTube videos with their info.json provenance files

## Phases

| Phase | Content |
|---|---|
| 1. Hero slice | Exterior and bowl, day to night, rain toggle, floodlights, full crowd, one football match |
| 2. Spectacle | Fireworks, drone show, light show, fountains |
| 3. Operations | Cars in and out, gate queues, crowd entry and exit |
| 4. Event library | Rugby, concert stage, training sessions, athletics |

## Rules

- The downloaded videos are reference material only. Do not put footage or frames into the product or the pitch without a license from the channel owner.
- Every frame keeps its source video ID and timestamp.
- Crowd and evacuation visuals are visualizations, not validated safety simulations.
- Do not put security-sensitive detail (exits, camera positions, control rooms) into a public demo.
- Munene buys any domain. Agents do not.

## Plan

The full plan is in PLAN.md: architecture, data sources, the simulation catalog (55 modules), phases, budgets and risks.

## Reference frame set (2026-10-16)

- 356 frames from 33 videos in research/frames/, indexed in research/video_index/MASTER_INDEX.csv. Built by Luna with engineering/frame_extract.sh. The output repeats exactly on a rerun.
- Coverage and gaps: research/video_index/COVERAGE.txt. Floodlights 30, gates and entrances 11, roads and parking 42.
- The set shows the look of the stadium well. It gives no dimensions and no site plan. See PLAN.md section 4.2.
- Video oL3wsPsx4Jw is a third-party 3D render, not real footage. Its seats and roof do not match the real stadium. Do not use it for geometry. It shows that someone else already made a Talanta 3D model.
- Video PWj9s_v3G6U and the "Nyayo" frames show another venue. Use them only as drone and light show references.
- Seat pattern: green lower tier, red upper tiers, black seats in some rows, on grey steel rails.
- Facade: a white diagonal lattice with horizontal louvres and large red, black and white shield panels (frame 9I1korKNjig_000638.000). Main gate and ticket buildings: frame KEOmkVfjhu8_000206.000.

## Sources of the status facts (retrieved 2026-10-15)

- Citizen Digital, CS Mvurya: Talanta Stadium scheduled to open in November. https://citizen.digital/article/cs-mvurya-talanta-stadium-scheduled-to-open-in-november-n388620
- Nation, Talanta stadium Sh7bn payment deadline. https://nation.africa/kenya/news/talanta-stadium-state-faces-critical-sh7bn-payment-deadline--5523016
- Google, Gemini 4 Argon post (temple complex built in Blender with visual critique loops). https://blog.google/intl/es-419/noticias-de-la-empresa/tecnologia/gemini-4/
