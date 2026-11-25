# Talanta Twin private demo review

21 November 2026, Nairobi

The candidate is based on merge `5f775a7`, on branch `codex/EVT-01-demo-acceptance`. Review the interactive build at [Talanta Twin full-site viewer](http://127.0.0.1:4174/full-site.html) while the local preview server is running. Use the [perimeter viewer](http://127.0.0.1:4174/) for the lighter interactive concert. Select **Concert**, then choose a view under **Concert camera**. Select **Hero** in the full-site viewer to run the venue sequence.

## Review media

- [Concert walkthrough](talanta-concert-walkthrough.webm)
- [Concert still](talanta-concert-review.png)
- [Hero walkthrough](talanta-hero-review.webm)

## Verified

- All 199 repository tests passed and the production build succeeded. All 398 files in the web hero bundle matched their size and SHA-256 records.
- The complete 90-second hero sequence reached the ending and Replay in Chrome WebGPU on an Apple M1 MacBook Air. The review recording includes startup and the final replay prompt. Sampled scenes included fly-in, roof, floodlights, rain, match, and night.
- Concert has four selectable camera views, closer floor-crowd detail, cue-driven catwalk lights and beams, and stage-coloured audience phone lights. The performer stands on the catwalk. The B-stage sits at the catwalk height to preserve the front-of-house sightline.
- The lead performer uses a 5,900-triangle textured Rocketbox rig at 678,868 bytes. Chrome confirmed that opening Concert loads the performer, seeking changes its skeleton pose, and switching to Football removes it. The MIT notice ships with the model. The dance is retargeted from the original CC0 Quaternius clip.
- The production perimeter viewer reached the concert outro during continuous playback, with all four camera views exercised.
- At 1366 × 768 and 375 × 812, the perimeter concert camera selector was 44 px tall, all four views could be selected, and the page had zero horizontal overflow. The camera selector disappeared on switching to Football. The full-site Modules dialog also passed keyboard opening, focus trapping, Escape dismissal, focus return, and disabled-entry checks at both sizes.

## Hyperreal concert work-order gates

| Gate | Current evidence | Remaining for acceptance |
| --- | --- | --- |
| G1 · Human topology and skin | The web demo has a textured lead and four textured foreground dancers. The Cycles look tests use a textured lead and ten textured foreground dancers within the milestone crowd. | Production crowd archetypes, skin shaders, hair, and a neck and joint seam review under moving lights. |
| G2 · Wardrobe | Two textured outfits are visible in the Golden Circle. | Six distinct outfits and a clipping review across the dance animations. |
| G3 · Backline | Five draw groups contain 2,972 triangles of modeled web props. The deck waveforms and mixer meters follow cues. | Production-quality equipment meshes, materials, effects fixtures, and the verified Blender and GLB prop library. |
| G4 · Front of house | Booth, deck, cable protectors, and barricades are present in the web demo. Placement tests verify the deck contact and sampled crowd clearance. | Equivalent placement checks and detailed booth crew in the unified scene. The web deck now has light-responsive surface relief. |
| G5 · Lighting and audience effects | The interactive build has cue-driven beams, laser visuals, LED patterns, and audience phone colours. Cycles previews show the milestone lasers and revised LED shader. | Unified cue timing for volumetrics, lasers, and stadium-wide wristbands. Four foreground wristbands ship in the web demo. |
| G6 · WebGPU | The perimeter demo completed all five cues and four views on the review Mac at 56.7 frame callbacks/sec. The 41.94 MB milestone master contains 712 mesh primitives before culling. | Meshopt or Draco optimization, the unified master integrated at the work-order draw-call and sustained FPS budgets, and target-device tests. |
| G7 · Cinematic | Three Cycles shot previews and a textured lead close-up are available. Blender verified pose changes on 313 milestone rigs. | Final photoreal look, 4K Cycles sequence, generated video pass, and sign-off. One 4K lead look-test frame has been rendered. |

## Acceptance still open

| Gate | Evidence or decision needed |
| --- | --- |
| Laptop and Android performance | The earlier throttled Chrome run reached first view at 1.19 s and 2.70 MB on the laptop viewport, and 0.97 s and 2.15 MB at the phone viewport. Both WebGPU runs sampled around 30 FPS in Concert on the same Mac. Repeat on the target laptop and a physical Android device, and record the sustained FPS and any approved exception to 60 FPS on laptop. |
| Site and panorama decisions | Review the south-west loop, Jamhuri road gaps, west service track, north-east road gap, and estimated plaza paths. The 10:30 and 18:05 panoramas are still deferred. |
| Visual acceptance | The hero review recording predates the shadow setting correction and generated PCF shadow and missing UV-channel warnings. Full-site continuous concert capture slowed substantially on the review machine. In the night frame the façade shield highlights read very bright. Concert has a detailed lead and four textured Golden Circle dancers. The wider floor and seated audience still uses simplified figures. |
| Photoreal concert | The broader work order still calls for the detailed crowd, wardrobe, DJ, stage and front-of-house production hardware, atmospheric effects, and final offline cinematic render. The new lead and camera views are available for review now. |
| Final approval | Approve the tested revision, site and panorama limitations, and the recording before merging or distributing. |

The [demo completion plan](https://github.com/M5-Engineering-PLC/talanta-twin/blob/main/engineering/completion_plan_2026-11-09.md) and [concert production order](https://github.com/M5-Engineering-PLC/talanta-twin/blob/wo/web-hero-v2/engineering/workorder_concert_hyperreal_production_2026-11-16.md) define the remaining gates.

In a 12-second full-site Chrome WebGPU sample at 1366 × 768 on the review Mac, the concert timeline reached 12 seconds after the elapsed-time fix (previously 6 seconds). The same sample delivered 214 frame callbacks in 11.9 seconds, with a 33 ms median frame interval. Sustained playback and target-device performance remain open.

A full-site low-tier WebGPU trace on the review Mac reached all five concert cues and looped at 60 seconds. The CPU profile traced a 4.12-second opening frame gap to desktop EXR panorama decoding. The low tier now requests the smaller HDR through the time-of-day loader. In a 13-second opening retest, the longest frame gap fell to 1.07 seconds and the build cue still started on time. This was a local Chrome run, and the remaining stall still affects the demo opening.

Added the 6 × 4 × 3.2 m front-of-house booth on the pitch centerline with truss, canopy, illuminated consoles, and a crowd-free access path. Geometry and clearance checks passed across all tested crowd tiers. The production perimeter browser check selected Skybox Tier 2 and FOH Soundboard without page errors. The image shows the booth at the right edge of the pitch. Yellow-and-black cable protectors now run from the stage underdeck around the crowd and into the booth’s rear access lane. Tests verify that every sampled crowd position stays at least 0.7 m from the route centerline and the route fits on the pitch. The 80 × 90 m pitch protection deck now has staggered seams and a procedural diamond tread pattern. The geometry check verified that the cable protectors sit flush on the deck and stay within its footprint. The 1.2 m barricades along the stage front and catwalk and between the Golden Circle and general admission now include footplates and security steps. Tests verified that they sit on the deck and every sampled crowd position stays at least 0.7 m from the barricade centerlines. The web deck adds light-responsive tread and seam relief through a generated bump map without adding geometry. The production perimeter camera check passed. The web booth now includes seated operator figures. [FOH still](talanta-concert-foh.png)

The interactive stage now includes a twin-deck DJ table with illuminated mixer and laptop, ten foldback monitors, guitar and bass cabinets, and a dual-tier keyboard stand. The production full-site viewer loaded all five backline draw groups without page errors. The stand-ins total 2,972 triangles against the 35,000-triangle prop gate. Detailed materials, branded modeling, the Blender prop library, and visual-effects fixtures remain open. [Stage backline still](talanta-concert-backline.png)

The twin deck waveforms now scroll with the concert beat. Four twelve-segment mixer meters respond to cue energy and pulse. Unit tests checked that the display data changes across cues, and a production browser run confirmed the live animation. [DJ console close-up](talanta-concert-dj-console.png)

Four Golden Circle positions now use a textured Rocketbox figure on desktop medium and higher tiers. Two women and two men use two distinct outfits, individual skeletons, and dance offsets. The female figure reuses the lead performer asset. Chrome confirmed that they animate independently and disappear when leaving concert mode. Blocking a detailed crowd asset in Chrome preserved all four procedural crowd zones and the lead performer. The rest of the audience still uses the original instanced crowd. [Golden Circle close-up](talanta-concert-vip-crowd.png)

The Golden Circle VIP bookmark now frames the lead performer and the four textured dancers together. A 1366 × 768 Chrome WebGPU run selected the bookmark from the normal full-site controls and verified that all five figure anchors were inside the frame. [Golden Circle camera still](talanta-concert-vip-bookmark.png)

The current 60.68-second interactive walkthrough shows all five cues and four cameras in the production perimeter viewer. Chrome decoded and sought through the 1366 × 768 WebM, and sampled opening, middle, and outro frames. [Updated concert walkthrough](talanta-concert-walkthrough.webm)

The current production perimeter build completed a 60-second loop and all four camera views in two Chrome WebGL runs on the M1 Mac. At 1366 × 768 it averaged 56.7 animation callbacks per second with a longest gap of 1.70 s. At the 375 × 812 phone viewport it averaged 56.8 with a longest gap of 1.47 s. Both had a 17 ms 95th-percentile gap and zero horizontal overflow. The detailed crowd asset loaded on the wider viewport only. These measurements include startup and camera switches, and are still pending confirmation on the target laptop and a physical Android device.

Blender 5.2.2 rendered three 640 × 360 Cycles checks from the earlier milestone GLB using `blender/render_concert_cinematic.py`. The source matches the 41,937,460-byte repository blob at `68b27f4`, with 313 skins and no embedded images. The preview exposed a roof-obstructed flyover, overexposed stage screens, and rest-pose crowd figures. These checks establish the import and render path. Corrected camera motion, animation binding, look development, and the final 4K sequence remain open.

The second Cycles preview showed the pitch through the roof opening, patterned LED screens in the front-pit view, and an unobstructed reverse view from behind the frontman. Blender restored 273 additional action bindings. The second preview visibly shows dancing poses, while the initial automated sampler reported zero moving rigs because it inspected original rather than evaluated bones. A full rerun with the evaluated-pose sampler confirmed that all 313 rigs changed pose between frames 24 and 72. The optional local Blender checkpoint avoids reimporting the milestone GLB. The 640 × 360 previews still use the milestone crowd materials. [Flyover](talanta-cycles-flyover.png) · [Front pit](talanta-cycles-front-pit.png) · [Catwalk reverse](talanta-cycles-catwalk-reverse.png)

The milestone master is within the 45 MB file limit at 41.94 MB. Its default scene contains 712 mesh primitives before culling, including 626 skinned mesh nodes, and declares no Draco or Meshopt extension. Runtime draw-call and 60 FPS acceptance for the unified master remain open. The interactive walkthrough uses the optimized event viewer assets.

A 960 × 540 Cycles look test replaced the milestone lead with the textured Rocketbox performer. It shows the performer from behind at the catwalk with the animated LED pattern and milestone crowd. The reproducible Blender scripts are staged. The 1.1 GB prepared Blender checkpoint is local, and the textured crowd, detailed materials and final 4K sequence remain open. [Textured lead look test](talanta-cycles-performer-closeup.png)

Blender produced a 3840 × 2160 textured lead still at 64 Cycles samples with OpenImageDenoise on the seven-core M1 GPU. The first frame completed after 8 min 21 s including scene setup and Metal compilation. It shows the lead facing toward the audience and retains the stylized milestone crowd. This verifies one frame only, with no measured sustained frame throughput for the sequence. [4K Cycles look test](talanta-cycles-performer-4k.png)

The 960 × 540 Cycles crowd material test assigned separate skin, shirt, trousers, and footwear surfaces to 622 animated meshes using their existing bone weights. The render uses varied muted clothing colours, UV-based fabric relief on 11 materials, and a skin subsurface response. Blender reopened the local `crowd-fabrics.blend` checkpoint and verified all 11 fabric materials and the active camera. The milestone body shapes and joint seams remain visible, and the six modeled wardrobes and final look remain open. [Offline crowd material look test](talanta-cycles-crowd-materials.png)

The offline Golden Circle preview now replaces ten milestone dancers in place with the textured Rocketbox assets, alternating two outfits and offsetting their dance phases. Blender reopened the local checkpoint, verified all ten rigs changed pose, and confirmed all ten figure anchors are within the new camera frame. The surrounding crowd still uses milestone mannequin geometry. [Offline Golden Circle preview](talanta-cycles-golden-circle.png)

The two-second Golden Circle motion preview rendered all 48 frames at 24 fps in Blender EEVEE at 480 × 270. The local render took 48 min 21 s. The encoded WebM decoded to 48 distinct frames, and the first and last frames show the camera push and changing crowd poses. The 4K Cycles cinematic remains open. [Golden Circle motion preview](talanta-golden-circle-motion.webm)

The production full-site viewer now shows eight cyan and violet laser rays during the drop and chorus. Chrome verified the intro hides them and the drop shows them, with no page errors. The refreshed perimeter walkthrough includes the laser cues, updated deck, booth crew, and foreground wristbands. [Laser cue still](talanta-concert-laser-cue.png)

Two seated front-of-house operators with headsets are visible at the audio and lighting consoles in the production full-site viewer. Their simplified geometry stays within the existing booth footprint. [Front-of-house crew close-up](talanta-concert-foh-crew.png)

Four Golden Circle wristbands follow the textured dancers’ left wrists and take their colour and brightness from the concert cues. They render in two instanced batches and preserve the 60-draw concert estimate. Chrome verified bone tracking, colour changes, and cleanup when switching events. [Golden Circle wristbands](talanta-concert-wristbands.png)

A repeat of the 60-second perimeter browser benchmark after the laser, deck, crew, and wristband updates measured 56.9 callbacks/sec at 1366 × 768 (longest gap 833 ms) and 56.7 callbacks/sec at 375 × 812 (longest gap 1417 ms). Both Mac Chrome WebGL viewport runs covered all five cues and four views with no page errors or horizontal overflow. These are browser callback measurements on the review Mac. Physical Android and target laptop acceptance remain open.

The perimeter viewer uses the Three.js WebGPU renderer with its WebGL backend forced. A phone-sized Chrome profile did not reproduce the previous long intro stall. The concert render loop now owns animated camera redraws, eliminating extra render calls from camera and resize handlers. The production camera smoke check passed. There is no new full-loop timing result for this change.
