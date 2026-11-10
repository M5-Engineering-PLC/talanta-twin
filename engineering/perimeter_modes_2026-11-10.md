# Perimeter event integration — 2026-11-10

Status: software and headless browser evidence, not device acceptance. Base included concert geometry fix `b070c92`.

Football, concert and drone show are selectable in the perimeter viewer. Event modules and concert/people assets load on selection, while the initial venue load stays separate. The active event is disposed on switching; a late module load is disposed rather than taking over. Pitch events use the bearing and pad in `data/manifest.json`. On entry the camera points inside the bowl for pitch events, and towards the airborne formation for the drone show. Crowd/show visualization claims and a concert sources/credits link are visible. Football does not yet add a seated crowd in this viewer. These are existing stylized assets, not H1 realistic people.

Software evidence: `npm test` passed 196 of 196; see `perimeter_modes_test_2026-11-10.log`. `npx vite build` passed with 109 modules. The controller tests cover selection races and disposal. The v3 bundle and linker checks are in `backup_compare_2026-11.md`.

Browser evidence: headless Chrome on this host displayed football actors and the concert floor crowd/stage on the pitch, and a separate drone run displayed an airborne formation. A 375 x 812 run changed football → concert → drone → venue with matching selection and claim text, scroll width 375 px, and no page errors; the first view requested no event, crowd or show resources. The drone module warned that the shipped facade-lines export failed validation and it used estimated fallback geometry. The first combined desktop screenshot run timed out after concert; an independent drone session completed. The screenshot artifacts are local temporary files under `%TEMP%/talanta-demo-qa-20261109/` and are not committed.

Open: compare geometry visually with internal references, complete viewport and keyboard accessibility review, test full sequence and repeated switches on named laptop and Android, and measure frame rate and transfers. Browser output here does not establish device acceptance or hyper-realistic quality.
