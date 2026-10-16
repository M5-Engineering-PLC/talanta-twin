# Interaction and visual style reference

Date: 2026-10-16
From: Munene

## Reference

- Target style for interactivity: https://x.com/DilumSanjaya/status/2108241054298415258/video/1
- Munene has the video in Downloads on the lead machine. The lead reviewed two stills (below).
- Do not commit the video or its stills (AGENTS.md rule 1). The description below is enough for workers.
- Same rule as the frames: reference only. Do not copy assets or code from it.

## Description of the reference

Reviewed 2026-10-16 from two stills Munene shared (video at 0:56 and later). The app in the video is a wildfire analysis tool, "FireTrace". Screenshots are not committed: they show another person's design.

| Aspect | What the video does |
|---|---|
| Overall look | A stylised but believable 3D terrain, like a painted relief model. Warm, slightly faded colours, soft haze towards the horizon, small rounded trees. Calm and readable, not photoreal and not cartoon |
| Layout | Top bar, large 3D map, right side panel, bottom timeline with three small charts and an event list. Every part is visible at once; no pop-up windows |
| Top bar | Product name, incident selector, place, date range, mode tabs with count badges (Incident, Drones 6, Resources 6), then View, Analysis, Share |
| UI surfaces | Cream and warm grey panels, thin dividers, dark grey text, one orange accent. Small type, plenty of space, numbers aligned in columns |
| Camera | Oblique 3D view with orbit and zoom. A compass in the top-left corner that turns with the camera. 2D and 3D toggle, a zoom-level menu (2.5x, 2.9x), full-screen button, scale bar |
| Labels on the map | Peaks with a small triangle and the height in metres, place names (creek, reservoir) in plain text with a soft halo |
| Data on the map | Glowing path from the ignition point with time-stamped nodes (Aug 14, 18:00), animated arrows for direction, a glowing perimeter, heat-coloured burn area. The data glows; the terrain stays muted |
| Hover | A small dark tooltip at the cursor: height, slope, aspect, whether inside the perimeter, land cover, coordinates |
| Weather card | Updates with the cursor ("at cursor") or the fire front: wind speed and bearing, temperature, humidity, fuel moisture, ERC, flame length, each with a small icon |
| Layers panel | Tabs: Layers, Analysis, Evidence, Notes. Each layer row: checkbox, small thumbnail of the layer, name, opacity slider, percentage. The name says what kind of data it is: "Fire Spread (Modeled)", "Spot Fire (prob.)", "Cause (Prelim.)" |
| Overview card | Key-value list with an Edit link and a status dot (In Progress) |
| Timeline | Play, pause, step, speed (1x). A scrubber with a time bubble (Aug 15, 02:32), event markers on the track, a red band for the active period |
| Linked charts | Fire area, rate of spread, elevation profile. A vertical cursor in each chart follows the timeline scrubber. The elevation profile follows the selected path |
| Key Events list | Icon, name, time. Clicking an event moves the camera to it and sets the time. Between the two stills the camera flew from the overview to the ignition area and the scrubber moved |
| Motion | Smooth camera fly-to, glowing pulses on key points, arrows that move along the path. Nothing jumps |

## What this means for the Talanta twin

Take the structure and the calm. Change the content to the stadium.

- **Map:** the bowl with the near ring and the far ring (`gis/`), shown as a stylised relief. Labels with heights from GLO-30: Ngong Hills, Ngong Road Forest, Kibera, Kilimani, the CBD skyline, Jamhuri Park.
- **Top bar:** "Talanta Twin", a scenario selector (Match day, Concert, Construction 2023-2026), date and time, mode tabs (Venue, Crowd, Weather, Transport).
- **Layers panel:** Terrain, Satellite, Buildings, Roads, Floodlights, Crowd density (Visualization), Rain (Simulation), Traffic (Visualization), Construction stage (Measured: Sentinel-2). The claim label goes in the layer name, as in the reference. That satisfies AGENTS.md rule 7.
- **Timeline:** for match day: gates open, kick-off, half-time, full-time, crowd leaves. For construction: the dates in `gis/coverage_report.md` (groundbreaking 1 Mar 2024, roof ring complete Feb 2026, and so on). Clicking an event flies the camera.
- **Linked charts:** people inside the stadium (visualization), rain and temperature, and a height profile along the selected walking route.
- **Hover tooltip:** height, ground type, distance to the bowl, coordinates. No gate or exit detail in the public build (AGENTS.md rule 8).
- **Weather card:** Open-Meteo values for the time on the timeline: wind, temperature, humidity, rain. Later, sun height and lux on the pitch.

## Kenyan theme: subtle

Direction from Munene: a Kenyan theme, but subtle. Proposed rules, for review:

1. **The stadium carries the theme.** The real building already has the shield and spear facade and the green, red and black seat gradient. The UI does not repeat them loudly.
2. **Flag colours as accents only.** The UI uses the cream and warm grey surfaces of the reference. The reference's orange accent becomes Kenyan flag red. Black, green and white appear in small amounts: the selection outline, the active toggle, one thin line under the title. Never full flag stripes as a background. Data colours (crowd density, rain) use their own ramps, not the flag.
3. **Warm local palette for neutrals.** Take tones from the site itself: murram red-brown soil, the dry grass of Jamhuri Park, the dark green of Ngong Road Forest, jacaranda purple for one highlight. The Sentinel-2 images in `gis/derived/` show these colours.
4. **Pattern as texture, at low contrast.** A faint shuka check or kikoi stripe in a panel header or loading screen, at 3-6% opacity. One pattern only.
5. **Shield shape as a UI motif.** It is the stadium's own motif (design facts). Use it for map pins, gate markers in private builds, and the logo mark. Keep it geometric and plain.
6. **Language.** English first. Swahili for a few labels where it reads naturally, for example "Karibu" on the start screen and "Hali ya hewa" beside "Weather". No mixed sentences.
7. **Light and sky.** Use the real sun path at 1.306 S, 36.750 E. The sun is near the zenith at midday and the dusk is short at the equator. Getting the light right does more for the sense of place than any graphic.
8. **Avoid** savannah animals, safari clichés, the national coat of arms (protected), and anything that reads as an official government product.
