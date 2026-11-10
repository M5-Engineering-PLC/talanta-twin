# Work order: hyper-realistic build and the fold into main

Date: 2026-11-10 (Africa/Nairobi)
Project: Talanta twin, private demonstration
Owner: Munene
From: the local lead session
To: the cloud Talanta build chat, Codex workers and Sonnet workers
Status: open. Draft for Munene's review before work starts.
Branch: `wo/web-hero-v2`
Sources: `engineering/completion_plan_2026-11-09.md`, `PLAN.md` sections 5, 8 and 9, `engineering/workorder_hyperreal_phaseA_2026-10-17.md`, `engineering/roads_check_2026-11-02.md`, `app/public/concert/CREDITS.md`, `app/public/people/CREDITS.md`.

Read AGENTS.md and `.claude/rules/commit-ownership.md` before you start.

## 1. Direction change

Munene changed the direction on 2026-11-10.

1. The target is now a hyper-realistic twin. People, the concert and the shows must look real at close range. The earlier goal was a stylised demo that is complete.
2. All work folds into `main`. The repository keeps `main` as the single line of record, and `wo/web-hero-v2` stays as the one work branch.

The completion plan of 2026-11-09 stays valid. This work order adds to it. Section 4 shows where each completion step goes.

## 2. Why the current build does not look real

These findings are from the code on `wo/web-hero-v2` at `44c93cd`. They are software evidence.

1. The concert floor crowd uses the 82-triangle body for every figure. `app/src/events/concert.js` passes `farDistance: 0` to `installStandingCrowd`, so no floor figure gets the near body. The performer passes `farDistance: 100`. `installStandingCrowd` does not pass a camera, so the crowd code measures distance from the event origin, not from the viewer.
2. The near body has 2,104 triangles. It is the Quaternius Universal Animation Library mannequin (CC0). It has no face, hair or clothing detail. The shader paints flat shirt, skin and trouser colours.
3. The phone file and the low tier contain only the 82-triangle body.
4. The staging folder has no realistic human. It has Quaternius packs, Kenney blocky and mini figures, and CMU motion capture without bodies.
5. The concert models from Sketchfab are in the build: stage B, truss, LED tile and stage lights (CC BY 4.0), and the iPoly3D main stage (CC0). Their textures were reduced from 4096 to 1024 pixels. Nobody has checked the concert on a real GPU yet.
6. The drones are 0.65 m octahedrons with an emissive colour. No drone model was imported.
7. The web view must run on the test laptop, which has an Intel UHD 620. That GPU cannot draw film-quality people, haze and lights at 60 fps.

## 3. Strategy: two output tracks from one asset set

Use one set of source assets in Blender. Make two outputs from it.

| Track | Output | Renderer | Quality ceiling |
|---|---|---|---|
| R (render) | The 90-second video, stills, panoramas | Blender Cycles on Kaggle GPU (2 x T4) | Hyper-realistic: full people, volumetric light, real haze |
| W (web) | The interactive twin | three.js WebGPU, tiers low to ultra | Best real-time result on each device, within PLAN.md section 8 budgets |

Reason: the video is what an audience remembers, and only Cycles gives film-quality people and light. The web twin then uses lighter versions of the same assets. This keeps the R and W outputs consistent.

Kaggle cost for the video (measured on 2026-10-25, L07 orbit at 1080p):
- 90 s at 24 fps is 2,160 frames.
- At 128 samples with haze (54.4 s per frame), the video needs about 32.6 GPU hours. The weekly quota is 30 hours.
- At 48 samples without haze (22.3 s per frame), the video needs about 13.4 GPU hours.
- These figures come from the old scene. The rebuilt scene with realistic people will be slower. Before you plan the video, benchmark 3 representative shots of the rebuilt scene. Record whether both T4 GPUs were in use. Count setup, warm-up, retries and panoramas against the quota, not only render time.
- Working assumption until the benchmark: about 20 GPU hours at 64 samples with the denoiser, and haze only in the shots that need it. Split the render over two or more weeks if necessary.
- On 2026-11-04 the quota was 0 of 30 hours used.

## 4. Phases

Each phase has an owner, a gate and evidence. A phase that fails its gate stops the next phase that depends on it.

### H0. Decisions and licences (lead and Munene)

1. Munene approves the two-track strategy in section 3.
2. Select the human source set. Candidates, in order of preference. Each candidate is unconfirmed until its licence evidence is recorded:
   - Microsoft Rocketbox avatars: reported as MIT licence, rigged, realistic, with varied skin tones.
   - MakeHuman with MPFB2 for Blender: exported bodies are reported as CC0. Clothing, skin textures and hair assets can have other licences. Check each one.
   - CC0 or CC BY scanned people from Sketchfab.
3. For each shipped asset, record the evidence: the licence file or page, the notice text, the attribution, the changes made, the redistribution terms for a public web build, and any likeness or model-release limits.
4. Project rule, separate from the licence check: do not use a model tagged NoAI. Also do not use Renderpeople free models, Mixamo raw files or Character Creator content until their redistribution terms are checked and recorded. The lead expects that they do not allow redistribution in a web build.
5. Faces stay generic. Do not model a real person, player, artist or official.
6. Freeze the target shots: the 8 hero sequence poses in `app/src/hero/sequencePoses.js` plus 4 close shots (crowd at 10 m, performer, player, drone formation).
7. Gate: a signed licence table in `engineering/hyperreal_assets_2026-11.md`, with the evidence in item 3 for each asset.

### H1. Realistic people (worker, lead review)

1. Build a body set in Blender: 12 to 16 bodies (men, women, ages 18 to 65, Kenyan skin tones). Add 3 clothing sets: casual, home kit, away kit. Kits are generic, with no club or national badge.
2. Retarget the existing clips to the new rig: sit, stand, cheer, clap, wave, scarf, phone light. Use the Quaternius clips and CMU motion capture (free use). Record the clip source in the credits.
3. Track R: use the full skinned bodies in Cycles. Use hair cards and skin subsurface scattering.
4. Prototype first. Before you make all bodies, build 2 bodies and 2 clips through the whole track W chain. Measure triangles, draw calls, GPU memory and fps on the test laptop. Continue only if the prototype fits the budget in item 5.
5. Track W: extend the current vertex-animation bake (`app/public/people/crowd.json`, `animation.bin`) to three detail levels, with a total budget:
   - LOD0: about 6,000 triangles, with a 512-pixel texture atlas. At most 64 figures on the medium tier and 192 on the high tier, nearest the viewer. Maximum 1.2 million crowd triangles on the high tier.
   - LOD1: about 1,200 triangles. Replaces the 82-triangle body. At most 2,000 figures.
   - LOD2: camera-facing impostors for all other figures. This meets the PLAN.md section 8 rule "3 levels of detail".
   - Animation textures: the current file uses 9,437,184 bytes for one body. Set a limit for each body and clip before the bake, and keep the total crowd animation data at 40 MB or less on desktop.
   - The current shader has no texture coordinates and no animated normals. Add both, so that LOD0 and LOD1 can show textured, correctly lit clothing and skin.
6. Fix the concert:
   - Pass the viewer camera through `installStandingCrowd` to the crowd code. Now the crowd measures distance from the event origin.
   - Remove `farDistance: 0` from the floor crowd.
   - Reserve LOD0 for the performer at all distances.
7. Players and the referee (SPT-01) use LOD0 bodies.
8. Phone: LOD1 near the camera and impostors beyond, inside the 15 MB first-view budget. The crowd loads after the first view.
9. Gates. Track R and track W have separate gates:
   - Track R: a figure at 10 m reads as a person in a Cycles still.
   - Track W: a figure at 10 m reads as a person on the ultra tier. With 60,000 crowd instances, the test laptop meets the PLAN.md target of 60 fps on the medium tier, or Munene records an accepted exception with the measured value.
   - Test the actual browser backend (WebGPU or WebGL) and record it.
   - Crowds keep the Visualization label.

### H2. Concert and shows (worker, lead review)

1. Concert: restore the Sketchfab textures to 2048 pixels for the ultra tier and track R. Keep 1024 pixels for the other tiers.
2. Add volumetric beam cones and stage haze in track R. In track W use additive cone meshes with soft edges.
3. LED content stays procedural. Do not show an artist name, logo, text or likeness.
4. Drone show: keep the instanced lights for the far view. Add one licensed drone model for the close shot only. Add bloom on the lights.
5. Floodlights and facade show: match the light colour and brightness to the show reference frames by eye (internal reference only).
6. Gate: the concert and the drone show pass the close-shot review in H7, on a real GPU and in Cycles.

### H3. Stadium, site and ambient life (worker, lead review)

1. Materials: use Poly Haven (CC0) materials for concrete, paving, grass, metal and glass. Bake new light maps for the hero surfaces at a higher resolution for the ultra tier.
2. Trees: replace the leaf cards with CC0 tree models in the near ring. Keep the current trees in the far ring.
3. Cars: model the five reference cars (Probox, Premio, Vitz, Hilux, Prado) from the staging photos as generic cars with no badges. The photos are reference only, not textures.
4. Roads: apply the decisions that Munene makes in completion step 4. Do not change geometry before he decides.
5. Gate: the 8 frozen poses render with no missing material, and the bundle checksums match.

### H4. Light and atmosphere (Kaggle and cloud)

1. Render the 10:30 and 18:05 panoramas (completion step 5). This stays deferred until Munene resumes Kaggle.
2. Use AgX tone mapping in Cycles and in the web view, with the same exposure per time of day.
3. Track W ultra tier: screen-space reflections on wet surfaces and bloom. Check each effect on the test laptop before you keep it.
4. Gate: the four time sets and the rain beat look consistent between track R and track W.

### H5. Cinematic render (Kaggle)

1. Rebuild the render pack from the frozen scene after H1 to H4 pass.
2. Render the 90-second sequence at 1920 x 1080, 24 fps, about 64 samples with the denoiser. Use the `talanta-chapter-render` notebook.
3. Render in chapters. Check each chapter before you render the next one.
4. Gate: the video passes the review in completion step 7.

### H6. Web budgets (worker and Munene)

1. Measure on the named laptop and Android phone (completion step 6).
2. The PLAN.md section 8 budgets stay: 30 MB and 5 s first view on the laptop, 15 MB and 8 s on the phone, 60 and 30 fps.
3. Realistic assets load after the first view, in order of distance to the camera.
4. Gate: named devices meet the budgets, or Munene records an accepted exception.

### H7. Review and acceptance (lead, panel and Munene)

1. Compare each frozen shot and close shot with the internal reference frames. Use the eight categories in `engineering/review_astra_hyperreal_2026-10-17.md`. The target score is 85 of 100 or higher.
2. Keep reference images and comparison sheets internal.
3. Record the result for each shot in a dated report under `engineering/`.

## 5. Order with the completion plan

| Order | Step | Depends on |
|---|---|---|
| 1 | Completion step 1: one tested candidate, with M1 inside it | none |
| 2 | M1 (backup comparison) before the candidate is frozen, then M2 to M4: fold into main | Munene's approval for each push to main |
| 3 | H0 decisions and licences | none, can run beside steps 1 and 2 |
| 4 | Completion steps 2 and 3: layout and laptop rendering of the current build | step 1 |
| 5 | Completion step 4: road decisions | none |
| 6 | H1 people, H2 concert and shows, H3 stadium and site | H0 |
| 7 | H4 light and atmosphere, with completion step 5 | Munene resumes Kaggle |
| 8 | H6 web budgets, with completion step 6 | H1 to H3 |
| 9 | H5 cinematic render | H1 to H4 |
| 10 | H7 review, then completion step 7 | H5, H6 |

## 6. Fold everything into main

Main is an ancestor of `wo/web-hero-v2`. On 2026-11-10, origin `main` was 0 commits ahead and 112 commits behind the work branch. The merge has no conflicts.

WARNING: do not push to `main` without Munene's approval in the chat for that push. Do not rewrite or force-push `main`.

This fold changes completion plan step 7. That step merged into `main` only after the panel accepted the release. Munene now wants `main` to carry the work as it goes. Acceptance moves from "merged into main" to an acceptance record: an approved commit hash in a dated report under `engineering/`. A commit on `main` is not accepted until such a record names it.

### M1. Fold the backup branch (before the candidate is frozen)

`origin/munene/talanta-local-backup-2026-11-09` holds the local implementation through `77c375f`. Origin later made its own versions of the menu, loading and layout work.

1. Compare the two implementations of the module menu, the first-load change and the Pass K README.
2. Keep each better part on the work branch. Port it by hand, with a test.
3. Save the comparison in `engineering/backup_compare_2026-11.md`.
4. Then finish completion step 1 on the result. Record the candidate commit, the test count and the build result.
5. Ask Munene before you delete the branch. The commits stay reachable only while the branch exists.

### M2. Merge the work branch into main

1. Ask Munene to approve the merge of the exact candidate commit from M1.
2. Merge with a merge commit: `git checkout main`, then `git merge --no-ff <candidate>`. Do not squash and do not rebase. A merge commit keeps the worker history that the completion plan says to preserve.
3. State in the merge message that the commit has not passed device acceptance, and name the open completion steps.
4. Run `npm test` and `npx vite build` from `app/` on the merge result.
5. Push `main`. The `commit-ownership` GitHub check must pass.

### M3. Fold the render pack branch

`origin/assets/render_pack` content is in `main` since `9c5a059`.

1. Check that the files in `main` match the branch tip `c14cc71` by SHA-256.
2. Record the result in the merge record.
3. Ask Munene before you delete the branch.

### M4. After the fold

1. The repository has two branches: `main` and `wo/web-hero-v2`.
2. Merge `main` into the work branch after each merge to `main`, so that both stay in step.
3. Repeat M2 after each phase in section 4 that passes its gate. Write an acceptance record for each.
4. Remove local worker branches (`worker/sol-*`) only after Munene approves.

## 7. Rules

1. Commit as Munene with his own git identity. Do not add AI attribution.
2. Merge, never rebase. Do not rewrite history on `main`.
3. Frames, Google Earth records, concept images and the AI dusk image are internal reference only. Never use them as textures or in public output.
4. Do not add security detail (exits, gates, turnstiles, CCTV, control rooms, access routes, real camera positions) to public output.
5. Crowds and shows keep their claim labels.
6. Every new asset has a row in the licence table before it enters the repository. Keep the credit files current.
7. Do not commit raw downloads, raw videos or `.blend` files over 50 MB. Use the render pack process.
8. Label each result as software evidence, browser evidence or device measurement.

## 8. Report back

For each phase and merge step, report:
- the commits,
- the test count and the build result,
- the gate result with evidence paths,
- the GPU hours used, for Kaggle work,
- open questions for Munene.
