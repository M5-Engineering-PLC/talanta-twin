# Talanta demo completion plan

Date: 2026-11-09 (Africa/Nairobi)
Project: Talanta twin, private demonstration
Owner: Munene
Status: open, pending device tests and final acceptance
Branch: `wo/web-hero-v2`
Source snapshot: origin commit `168d64b`
Sources: `PLAN.md`, `engineering/scope_decision_2026-10-25.md`, `engineering/roads_check_2026-11-02.md`, and the branch history.

## Target and current state

Complete the phase A base and the 90-second hero sequence described in the scope decision.
Include the existing football, concert, crowd reactions, facade lights, and drone show in acceptance testing.
The full module catalog remains a later product goal.
Forecourt visitors remain optional unless Munene adds them to milestone acceptance.

Origin includes the hero sequence, rain, GPU repairs, painted texture repair, module menu, loading changes, and viewport fixes.
Origin also includes the Pass K approval correction and the roads report.
These commits provide software evidence. They do not establish acceptable output or performance on physical devices.

Local `talanta_work` was at `77c375f` before this plan. Origin was at `168d64b`.
The two histories contain separate implementations of the menu and loading changes.
Preserve both histories until a lead compares them. Do not overwrite origin or delete local commits.
The recorded 198-test result belongs to the local implementation, not the newer origin implementation.

## Completion record

Use OPEN, IN PROGRESS, PASS, FAIL, or DEFERRED BY MUNENE for each step.
Record the candidate commit, device, browser version, result, evidence path, owner, and next action.
Save each acceptance round in a new dated report under `engineering/`.
Keep reference images and comparison overlays internal.

| Step | Owner | State | Evidence required to close |
|---|---|---|---|
| 1. Establish one tested candidate | Lead | OPEN | Branch comparison, preserved local history, test output, clean build, bundle integrity result |
| 2. Finish layout acceptance | Lead or worker | OPEN | Measurements and screenshots at both viewport sizes |
| 3. Accept laptop rendering | Lead and Munene | OPEN | Named GPU, browser, sequence frames, event results, console results |
| 4. Accept site accuracy | Lead and Munene | OPEN | Decision for every roads finding and generated layout |
| 5. Complete panoramas | Kaggle and cloud | DEFERRED BY MUNENE | Panorama files, manifests, checksums, and time transitions |
| 6. Accept loading and phone performance | Lead and Munene | OPEN | Named laptop and Android results against the budgets |
| 7. Record and approve the release | Lead and Munene | OPEN | Video, panel decision, approved commit and merge record |

## 1. Establish one tested candidate

1. Fetch `origin/wo/web-hero-v2`.
2. Compare origin with the preserved local commits through `77c375f`.
3. Resolve differences on the work branch without rewriting history.
4. Make sure that the app uses the repaired `assets/web_hero_v3` bundle.
5. Run `npm test` from `app/`.
6. Run `npx vite build` from `app/`.
7. Save the test count, build result, bundle integrity result, and candidate commit.

Acceptance: one candidate contains every required feature, with passing tests and a clean build.
A missing phone manifest must produce a clear failure instead of downloading desktop assets.

## 2. Finish layout acceptance

1. Test the candidate at 375 x 812 and 1366 x 768.
2. Inspect the landing page, full interface, module panel, and hero caption.
3. Measure horizontal overflow and interactive target sizes.
4. Test keyboard navigation, Escape, focus return, and disabled planned entries.
5. Save screenshots and measured values.
6. Fix failures and repeat the affected cases.

Acceptance: no horizontal page scroll, readable captions, reachable controls, and touch targets of at least 44 x 44 pixels.
A headless browser can establish layout results. It cannot establish acceptable GPU rendering.
Origin commit `7ba7568` contains layout fixes. Save acceptance evidence for the final candidate.

## 3. Accept laptop rendering

1. Open the candidate in Munene's selected Chromium instance.
2. Record the laptop model, GPU, browser version, renderer backend, and quality level.
3. Play the complete 90-second hero sequence.
4. Inspect the fly-in, roof, sunset, floodlights, crowd fill, rain, goal, and final night view.
5. Inspect crowd reactions, the drone show, football, and the concert separately.
6. Test medium and high quality, then the low-quality fallback.
7. Test seeking, replay, cancellation, module switching, and time changes.
8. Save screenshots and console results for failures and successful repeats.

Acceptance: no blank view, lost graphics context, shader failure, or missing required event.
Painted shields and tree materials must render correctly.
Rain, wet surfaces, lighting, players, and crowd reactions must appear during their intended beats.
Low quality currently omits the seated crowd. Define and test its visible fallback before accepting the phone demonstration.

## 4. Accept site accuracy

Read `engineering/roads_check_2026-11-02.md` before changing geometry.
The report compares shipped meshes with numeric Google Earth records and OSM lines.
A construction-date record cannot prove every finished-state detail.

1. Resolve the south-west loop difference, including the southern extent difference of about 60 meters.
2. Resolve partly missing or offset Jamhuri Road and Jamhuri Park Road segments.
3. Resolve the missing west service track against its cited source.
4. Record whether the intentional 40-meter gap in the north-east road remains correct.
5. Review the generated-mockup source of the `fp_*` plaza, paths, and beds.
6. Record a correction, accepted uncertainty, or explicit deferral for every finding.
7. If geometry changes, export affected assets and repeat the relevant visual and integrity tests.

Acceptance: Munene accepts each remaining uncertainty, and every shipped layout feature has a stated source or visualization label.
The report found no geometry sourced only from the AI dusk image.
This finding does not establish that generated landing mockups provide measured geometry.

## 5. Complete panoramas when resumed

This step remains paused at Munene's request. Do not start Kaggle from this plan alone.
The 10:30 and 18:05 panorama fields remain null in the desktop and phone time sets.
The panorama fallback does not close this step.

1. When Munene resumes this step, render both panoramas with the `talanta-pano` notebook.
2. Package the outputs in the bundle environment folder.
3. Update the two desktop and two phone time records.
4. Reindex the bundle and make sure that file sizes and checksums match.
5. Inspect both panoramas and all four time transitions in the app.

Acceptance: every supported time loads its intended panorama without missing files or broken transitions.
For an earlier release, Munene must explicitly accept the panorama limitation in the release record.

## 6. Accept loading and phone performance

1. Record the laptop and Android device models, browser versions, network conditions, and candidate commit.
2. Measure initial landing traffic separately from interactive hero traffic.
3. Measure first-view time, event-ready time, frame rate, and memory use.
4. Measure each supported event and repeated module switches.
5. Make sure that phones request phone assets and release unused heavy resources.
6. Fix failures or obtain an explicit scope decision before recording the final video.

The first-view limits are 30 MB and 5 seconds on laptop, and 15 MB and 8 seconds on phone.
Both timing limits assume a 20 Mbit/s connection.
The frame-rate targets are 60 FPS on laptop and 30 FPS on phone.
These limits come from `PLAN.md` section 8 and the scope decision.
The earlier 199.5 MB desktop and 41.8 MB phone estimates describe interactive hero preparation, not the landing first view.
They exclude code, decoders, crowd assets, and HTTP overhead. Measure actual browser transfers before accepting performance.

Acceptance: named devices meet the agreed budgets, and repeated event changes cause no progressive memory failure.

## 7. Record and approve the release

1. Record the accepted 90-second sequence from the accepted candidate.
2. Inspect the complete recording for missing effects, loading interruptions, and unreadable labels.
3. Present the recording, device results, site decisions, and remaining limitations to the review panel.
4. Record Munene's approval of the exact candidate commit.
5. With Munene's approval, merge the accepted work into `main` through the repository review process.
6. Publish only the approved version and its permitted assets.

Acceptance: the video exists, the panel accepts the candidate, and the merge and release records identify the approved commit.
Crowd and show claims remain visible. Internal reference images and security-sensitive detail remain outside public output.

## Handoff

On 2026-11-10 Munene changed the direction. Read `engineering/workorder_hyperreal_main_2026-11-10.md` with this plan. It adds the hyper-realistic phases and changes the merge timing of step 7.


Start with step 1. Preserve local and origin implementations until their differences are resolved.
Keep Kaggle deferred until Munene resumes it.
Update the completion record after each step, with evidence paths and the tested commit.
