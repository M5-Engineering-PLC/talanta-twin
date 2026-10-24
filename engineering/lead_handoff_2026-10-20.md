# Lead handoff: Talanta twin, 2026-10-20

From the previous lead session (local Claude Code on Munene's laptop) to the new lead chat.
Read this file first. Then read AGENTS.md, HANDOFF.md, blender/STATUS.md and blender/renders/landing_pass_02/README.md.

## Goal (locked by Munene)

- Blender Cycles stills L06 (sunset, 18:05) and L07 (daylight, 10:30) that match landing mockups 06 and 07 like for like. This covers shape, layout, background and look, at the same sharpness.
- A three.js live twin (app/) that shows the same baked scene.
- A hyperreal, artistic 4K version of L06 and L07 (preset hero_artistic).
- The mockups are look and layout targets only. Where a mockup contradicts a JWNowpO44rw frame, the frame wins for geometry.

## How the work is split

- The lead plans, writes the cloud prompts, reviews every result against the drone frames and the mockups, and creates GitHub releases.
- The cloud chat (Claude Code on claude.ai) does all CPU work: builds, bakes, renders and exports. Munene pastes the lead's prompts into it.
- The laptop only writes code (app/). Munene's rule: "anything cpu heavy w processes to be run in the cloud, just building on local".
- The cloud cannot create GitHub releases. It pushes bundles to orphan branches assets/<name>. The lead fetches the branch, checks every file against manifest.json (size and sha256) and runs `gh release create <name> --prerelease` from a machine where gh is logged in as nenemwaniki.
- Codex workers (m5-worker luna or sol) are optional for local code work. Run `codex-status` before each launch.

## Branches and assets

| what | where |
|---|---|
| Active cloud branch (newest work) | `m5/vibrant-ride-5er9ju`. It contains everything on the work branch plus 16 commits (G, L, T, R, B, F, H, W scripts). |
| Work branch (merge target) | `claude/hopeful-archimedes-lo15is` |
| Live bundle v1 | GitHub prerelease `web_hero_v1`: web_hero_v1.tar (149 MB, 70 files), .sha256, manifest. Checked on 2026-10-19: 0 problems. |
| Bake backup | orphan branch `assets/web_hero_v1_bake`: baked blend, maps/stages.json and the recovered lightmaps |
| App fetch script | app/tools/fetch_assets.mjs (`npm run fetch-assets`), with tests |
| Landing concept images (internal only) | `munene/CAM-01-landing-option` |

The orphan branch `assets/web_hero_v1` is gone from origin. The release still holds the bundle.

## Where the cloud is now

Done on `m5/vibrant-ride-5er9ju` (details and times in blender/renders/landing_pass_02/README.md):

| step | result |
|---|---|
| G convex barrel | Fit with wall_bulge >= 0: bulge 2.02 m and shoulder_rv 4.74 m accepted; shoulder_rh 8.5 m set by eye. Roof cushions 1.2 m. Drone box costs changed only a little (D01 39.2 to 42.4, D02 0.23 to 1.02, D03 2.26 to 2.52). |
| L site layout | Traced from Munene's Google Earth screenshot: apron ring, NE road, east buildings, east car park |
| T trees | Trees only on beds, along paths, in the forest belt and the city. 645 of 823 site trees removed. |
| R Rubis station | OSM node 30092080, Ngong Road at Dagoretti Corner, north-west of the site. Munene chose this one. The brand fascia and the pylon are tagged internal_only; the public export shows a plain canopy. |
| B background | Forest belt densified, far land green-grey, mid-rise city masses, CBD clusters, dusk town lights |
| F plaza | 133 bed sections, 17 paths, 194 shrubs, 148 flower clumps, 38 trees, 48 lamps |
| H preset | hero_artistic: 4K, uplights, base glow, haze, glare, bevels, CC0 sunset and cumulus skies |
| W scripts | v2 bake groups written. The re-bake is costed at about 4.7 h CPU, over the 4 h limit. |

The last prompt sent to the cloud (2026-10-20) changed the order:
1. Stop the 4K H renders.
2. Fix the façade members, the shields, the base band, the roof cushion read and the context.
3. Render checks: D01 to D03 with the exact drone cameras, a façade close-up that matches frame 001232.600, and 1080p L06 and L07 previews. Push them.
4. Render the 4K H stills. Push them.
5. Do not start the W re-bake until Munene approves the 4K stills.

## Findings from the last drone comparison (lead, 2026-10-20)

Sheets compared: L07 against 000714.767, L06 against 000645.000, and a façade close-up against 001232.600.
- Shape: the convex barrel and the rolled top now match the frames.
- White diagonal façade members: wrong. Ours are thick round tubes that stand off the louvres and merge in rounded forks. The real members are slim flat ribs, about one third of our width, almost flush, and meet in sharp V points at the fascia band.
- Shields: ours are bright glossy red with a chrome-looking rim. The real shields are dark matte crimson-maroon with black.
- Base band: dark in the footage, a white colonnade in the twin. This is not checked yet.
- Roof cushions: they barely read from the L07 distance.
- Context: the city is beige boxes; lollipop crowns remain in the middle distance.
- South-west foreground: the as-built frame shows a lawn in a road loop and a grandstand with a white roof. The twin has a track and a pitch. The transcript says the west training pitch has a 1,500-seat stand and an 8-lane track. Not resolved yet.

## Next steps for the new lead

1. When the cloud pushes the checks (step 3 above): fetch `m5/vibrant-ride-5er9ju`. Put the D01 to D03 renders and the façade close-up next to their frames. Accept or send corrections.
2. When the 4K stills land, show them to Munene. W runs only after his approval.
3. When the cloud pushes `assets/web_hero_v2`, verify it and create the prerelease web_hero_v2. Do not change web_hero_v1.
4. App side (laptop): load the ground tiles, the 8K panorama, shadows, anti-aliasing and tree impostors. Then compare the live twin with the stills in Chrome. The built-in browser pane has no WebGL.
5. Merge `m5/vibrant-ride-5er9ju` into `claude/hopeful-archimedes-lo15is` when Munene asks.
6. Open items:
   - The seat count is 63,949 against 60,000 (+6.6 %).
   - The heights and tier steps are estimated, not measured.
   - The media offices and the tunnel side are placeholders.
   - The landing has not been tested at 375 px phone width.

## Open decisions for Munene

- Approve the W re-bake (about 4.7 h) after the 4K review.
- Delete the old remote branches codex/lookdev, codex/shield-fix, codex/suburbs and web/hero-match.
- Remove the old local worktrees web-crowd and web-tour. The web-crowd worktree holds an uncommitted app/src/hero/crowd.js.
- Reinstall the Codex CLI: `npm install -g @openai/codex@latest`.

## Rules (all agents)

- Frames, Google Earth captures, mockups and comparison sheets are internal reference only. Never use them as textures or in public output.
- No security detail in public output: no gates, turnstiles, exits, exit signs, CCTV, control rooms or access routes. Keep the tunnel and portals out of the public export unless Munene approves them.
- People and crowds are labelled Visualization. Do not name the architect or the guides. Do not copy sign or door text.
- No sacco names or logos on vehicles. The Rubis brand stays internal_only. Credit the CC-BY nganya model.
- Video oL3wsPsx4Jw is never used for geometry. PWj9s_v3G6U and "Nyayo" frames are show and lighting references only.
- Do not change existing rows in labels_manual.csv or in the parameter ledger. Add new rows.
- No raw videos and no binaries in work branches. Keep the repository private.
- Work on branches. Never rewrite main. Merge, never rebase.
- Commit as munene <nenemwaniki@gmail.com> with the configured git identity. No AI attribution, no --author, no -c user.*. If git shows an AI identity, stop and ask Munene.
- Ask Munene before any outward or irreversible action: releases on new names, deletion of branches or worktrees, pushes to main.
