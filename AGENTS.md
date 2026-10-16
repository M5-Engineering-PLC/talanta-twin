# Agent rules for talanta-twin

This repository holds the reference data and build work for a three.js digital twin of Talanta Stadium (Raila Odinga Talanta Stadium, Ngong Road, Nairobi). Read README.md first.

## Repository layout

- research/frames/ holds reference frames from YouTube videos. One folder for each video ID.
- research/video_index/MASTER_INDEX.csv has one row for each frame: file, video ID, timestamp, source URL, view class, subject, notes.
- research/video_index/labels_manual.csv holds the manual label and keep decision for each frame. engineering/frame_extract.sh reads it.
- research/video_index/COVERAGE.txt gives the frame count for each view class and the known gaps.
- research/Talanta_design_facts_2026-10-16.md lists sourced design facts.
- engineering/ holds scripts and work orders.
- archive/video/ holds the raw videos. It is git-ignored and exists only on the lead machine.

## Rules

1. Do not commit raw videos. They are too large for GitHub, and the repository must not redistribute them.
2. The frames are internal reference only. Do not put a frame in a product build, a texture, a pitch or a public page.
3. Keep this repository private.
4. Do not change existing rows in labels_manual.csv. Add rows, or write a correction file and tell the lead.
5. Video oL3wsPsx4Jw is a third-party 3D render. Do not use it for geometry.
6. Video PWj9s_v3G6U and frames with "Nyayo" in the subject show another stadium. Use them only as show and lighting references.
7. Crowd and evacuation visuals are visualizations, not validated safety simulations. Label them that way.
8. Do not add security-sensitive detail (exits, camera positions, control rooms) to a public demo.
9. Many agents share this repository. Work on a branch. Do not rewrite history on main.
