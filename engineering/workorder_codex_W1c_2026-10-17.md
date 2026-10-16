# Work order W1c: more reference frames and a GPU check

Date: 2026-10-17
Worker: Luna (Codex) on the lead laptop, or Munene
Why: the cloud session cannot reach YouTube and has no GPU.

## Task 1: frames from the historians video at full resolution

The raw video is `archive/video/main/` (ID JWNowpO44rw). Extract one frame per second in these windows. Keep only frames that show the outside of the stadium, the roof, the shields, the fountain or the plaza.

| Window (mm:ss) | Subject |
|---|---|
| 00:00-00:30 | roof lattice from the air |
| 04:40-05:20 | fountain and plaza (scale model) |
| 07:00-07:20 | north forecourt from the air |
| 10:00-10:40 | roof trusses, shield with spears |
| 10:35-10:45 | roof membrane from inside |
| 12:30-12:45 | finished shell from the air |
| 26:10-26:20 | facade louvres and shield |
| 28:15-28:25 | shield close-up |
| 20:00-20:10 | fountain at night |

Command pattern: `ffmpeg -ss 00:12:30 -to 00:12:45 -i <video> -vf fps=1 -q:v 2 research/frames/JWNowpO44rw/JWNowpO44rw_%06d.jpg`. Name the frames as before (mmss.ms), add rows to MASTER_INDEX.csv, and add rows to labels_manual.csv. Do not change existing rows.

## Task 2: the second video

Download WcsgPTBRwlI with the same yt-dlp settings as `engineering/fetch_videos.sh`. Add the ID to that script. Extract frames at 1 fps, keep stadium views, and index them as above. Do not commit the video.

## Task 3: GPU check of the app

Run `cd app && npm install && npm run dev` and open the page in Chrome. For each focus chip (Overview, Main forecourt, Fountain, Shield facade, Ngong Hills, Pitch, Roof canopy, Seating tiers), save a screenshot to `docs/screens/2026-10-17/`. Also save one at 19:30 with Overview selected. Record the frame rate (Chrome performance overlay) and the console line "renderer backend". Write the results in `docs/screens/2026-10-17/README.md`.

## Task 4 (Munene): Google Earth Pro, numbers only

On the 26 Dec 2025 image, measure each of these 3 times. Put the results in `gis/site_measurements.md`:
- the fountain pool outline (corner lat, lon)
- the plaza outline (8 points)
- the centre of each shield on the facade, if visible
- the roof inner edge, long axis and short axis

## Done when

New frames are indexed and labelled, the screenshots and README are in `docs/screens/2026-10-17/`, the measurements are in the form, and the work is committed on a branch named `w1c-frames-gpu-check`.
