# Astra review: path to hyperrealism

Date: 2026-10-17
Model: gpt-6-astra, read-only, branch at 1d82282
Reference: Google Antigravity video "Gemini 4 Argon: 3D World in Blender" (youtu.be/1dAcJEIlQM8)
Status: software strategy review. Not a render comparison or a measurement.

## Verdict

Recommend option (b), with one refinement: sourced dimensions remain authoritative above Blender. Keep the real-time web twin and the goal in PLAN.md. Blender owns hero geometry and materials, Cycles produces stills and film, and three.js delivers optimized interaction. This restores the planned architecture rather than replacing the product.

This is a software strategy review of checkout `1d82282`. It is not a render comparison or physical measurement. The reference assessment uses the supplied video summary. The four concept images were unavailable in this checkout.

The gap is structural before it is cosmetic. In `bowl.js`, one procedural profile defines the shell, repeated tubes define the lattice, and box beams represent roof trusses. Seats use the same simple pan, back and leg. Hero views need supported roof structure, membrane seams, facade depth, joints, bevels, seat variants and believable ground contact. Their dimensions must remain estimated until evidence supports them. The reported 56,972 seats are 5.05% below 60,000. Increasing density to match the headline capacity will not resolve the geometry.

Materials use mostly uniform roughness and generated color textures. The next step is physically based materials with correct texture scale, normal detail, restrained roughness variation and separate material identities. White coated metal, membrane, concrete, glass, plastic seats and paving must respond differently to light. The 10 m Sentinel-2 texture belongs in distant context. Enlarging it or generating a finer texture does not create finer measured detail.

Lighting already includes a sun, hemisphere illumination and four spotlights, plus emissive strips. It lacks convincing indirect illumination, material reflections and detailed fixture behavior. Bloom cannot supply those effects. Atmosphere is currently distance fog and a painted sky gradient. Cycles can add restrained aerial haze and atmospheric scattering. The browser needs cheaper approximations.

Vegetation consists of repeated solid crowns without visible branches or leaves. People are capsule figures, and the matchday crowd remains disabled. Hero scenes need varied tree silhouettes, leaf translucency, believable human proportions, clothing and ground contact. Distant trees and people can remain simplified. Crowd actions remain visualizations.

The camera system supplies orbit views and smooth transitions, but not a controlled photographic sequence. Its initial time is 08:20, rather than the planned golden-hour opening. The process also lacks a demonstrated Blender reference loop, independent held-out comparisons and real-device performance evidence. The Sol review identifies unresolved correctness problems, including render fallback and fountain visibility.

Option (a), three.js alone, can produce convincing selected views with good assets, lighting and careful limits. It cannot reliably deliver Cycles-quality vegetation, reflections, atmospheric effects and dense crowds at the existing laptop and phone budgets. Browser path tracing also conflicts with responsive movement on this hardware.

Option (b) offers the strongest route. Keep dimensions, provenance and uncertainty in a shared parameter record. Generate or constrain Blender geometry from that record. Export glTF assets with LODs, meaning simpler models for greater distances, and KTX2 compressed textures. Keep the current procedural bowl as a temporary fallback while replacing components incrementally.

Cycles materials do not transfer automatically into glTF. Bake supported texture maps and explicitly rebuild browser materials. Bake indirect illumination for selected lighting states, while keeping moving sunlight and crowd lighting separate. A single golden-hour lighting bake will look wrong during a day-to-night transition. Treat offline film and interactive output as separate deliverables from the same asset source.

Option (c), remote rendering streamed to the browser, can show high-end imagery interactively. It adds continuous GPU cost, latency and network dependence. It is unnecessary for the first hero slice. A prerecorded hero film can accompany the browser app, but it must not imply that the browser rendered it live.

The production pipeline needs seven gated stages.

Stage 00 establishes evidence and a baseline. Luna inventories source records, dimensions, uncertainty, licenses and existing defects in a cloud session. Munene supplies Google Earth Pro measurements locally, as numbers only. Sol resolves the listed software defects in a separate work order. Outputs are a parameter ledger, source register and fixed browser captures. The gate requires explicit units, coordinate origin, north direction, evidence dates and unresolved conflicts. Search extracts in the sourced-facts file remain provisional.

Stage 01 restores W6. Sol prepares reproducible Blender scripts in the cloud from the ledger and current geometry. Outputs are a scaled blockout, plan, elevations and sections. Cycles previews run on a rented GPU. The gate compares dimensions and silhouettes against evidence before material work begins. Do not manufacture an authoritative OpenBIM blueprint from incomplete photographs. An estimated section must say that it is estimated.

Stage 02 locks visual targets. The lead and Sol assemble four-angle reference sheets for the roof, facade, bowl and forecourt. Internal footage establishes shape. The four AI concepts establish mood only. Outputs pair each desired detail with its evidence or estimate label. The gate rejects concept features that contradict the real building. Reference sheets never become textures.

Stage 03 builds four separate Blender asset collections. The lead assigns roof and envelope to Sol, facade and bowl to a separate Sol work order, landscape to Sonnet, and people dressing to Sonnet. Luna owns assembly and export scripts. Each worker receives bounded files and frozen shared parameters. Outputs are linked collections with provenance and preview renders. The gate requires correct scale, no visible intersections, credible silhouettes and no unsupported structural additions. Cloud sessions prepare code and assets. GPU machines run assembly and render jobs.

Stage 04 develops materials, light and cameras. Sol owns the render setup under lead review. Inputs are accepted geometry and licensed material sources. Outputs include daylight, golden-hour and night presets, plus material close-ups. The gate requires readable white surfaces, plausible reflections and consistent exposure.

Adapt the reference techniques selectively. Use gobo shadows, meaning patterned light occlusion, only where foliage or another object plausibly casts them. Do not impose random intensity noise on daylight. Use restrained roughness variation and edge detail. Avoid universal edge wear on a new stadium. Pointiness and ambient occlusion are artistic aids, not evidence of damage. Use a 36 mm-wide sensor with a chosen focal length. Start the stadium aerial near f/8. Reserve f/1.8–f/2.8 for suitable close-ups.

Stage 05 runs the critic loop. Luna submits deterministic renders to the GPU host. Astra reviews returned images against evidence and the previous accepted pass. The lead turns findings into bounded corrections. Outputs are annotated comparisons, scores and a short defect queue. The gate follows the stop rule below.

Stage 06 exports and integrates. Sol owns glTF loading, material conversion and quality levels. Luna owns mesh optimization, texture compression and artifact reports. Sonnet owns browser controls and mobile access. Outputs include the accepted hero still, a short film test and the same assets in three.js. The gate requires correct transforms, material appearance, labels and real-device results within PLAN.md budgets.

The critic needs 16 frozen virtual views. C01–C04 are north, east, south and west elevations. C05 is a roof plan. C06–C09 are four elevated diagonals. C10–C11 look across the bowl along its two axes. C12 shows a representative seat section. C13 shows the roof underside. C14 shows a facade and shield detail. C15 shows the forecourt and fountain. C16 shows the approach and horizon. These are render viewpoints, not real security-camera locations.

Freeze camera transforms, projection, lens, crop, resolution, exposure, sun state and random seed in one manifest. Use neutral daylight for geometry review. Reuse C06, C10 and C15 for golden-hour and night variants. Compare geometry with measured constraints and matched real frames. Compare materials with real close-ups under comparable light. Compare mood with concepts only after geometry passes. Compare web exports with accepted Cycles views, with documented rendering differences.

Reserve genuinely unused footage for final review. The current forecourt source overlaps a held-out frame identified by Sol. Resolve that contamination before scoring. For photographs with unknown camera calibration, record alignment uncertainty instead of claiming exact pixel agreement.

Score eight categories from 0 to 5: geometry, materials, lighting, atmosphere, vegetation, people, camera and process reproducibility. Weight them 30%, 15%, 15%, 5%, 10%, 10%, 5% and 10%. A score of 0 means missing, 3 means recognizable with visible defects, and 5 means no material discrepancy at the agreed review scale. Mark unobserved details as unknown.

Accept a release candidate after two consecutive passes reach 85/100, every applicable category reaches 4/5, and no critical evidence or software defect remains. Accuracy, provenance and public-content restrictions are hard gates that appearance cannot offset. Stop for lead review after three passes improve by less than two points, or after eight passes. Do not copy the reference’s 32-pass count as a production target.

During days 1–2, Munene captures six browser baselines and completes priority measurements. The lead freezes one hero composition and the evidence hierarchy. Luna prepares the ledger and camera manifest. Sol addresses the existing correctness defects. During days 3–4, Sol restores the Blender blockout and produces neutral comparison renders. Day 5 is the geometry gate, including an early glTF round trip and a representative GPU benchmark.

During days 6–8, the four specialist packages develop only the detail visible in the first hero shot. Sol develops materials and lighting while Luna runs assembly jobs. During days 9–10, Astra critiques fixed views and the lead selects corrections. During days 11–12, Sol exports browser assets and Sonnet integrates controls. During days 13–14, Munene tests the laptop and phone, and the lead accepts or rejects the still and short film test. Two weeks targets one accepted shot, not the complete 90-second phase-one experience.

The first hero shot is a dry golden-hour aerial from the northeast, looking southwest toward the bowl and Ngong Hills. Use the current overview pose as a starting point, then freeze it after reference alignment. Keep the stadium dominant, with readable roof, lattice and shield colors. Begin without crowd, rain or a light show. This isolates geometry, materials and geographic identity.

Cloud Claude sessions suit evidence processing, script generation, GIS work, asset manifests, browser builds and image critique. They do not inherently provide a GPU. Headless Blender with CPU Cycles can run if the environment supports the binary, dependencies, memory and execution duration. Eevee also needs a working graphics context and driver. The `-b` flag removes the interface, not that dependency. Do not assume software graphics will provide useful Eevee performance.

For planning only, allow roughly 1–10 minutes for small CPU previews and 30 minutes to several hours for a complex CPU hero frame. These are unbenchmarked ranges. An eight-thread laptop can take longer, especially with insufficient memory. Cloud CPU rendering is useful for low-resolution diagnostics, not the main critic loop.

Rent a CUDA/OptiX-capable NVIDIA GPU with about 24 GB VRAM and at least 32 GB system RAM. A 4090-class machine is a reasonable benchmark candidate. Use an unverified allowance of US$0.50–$2 per GPU-hour, excluding storage and transfer. At an assumed 5–30 minutes per frame, compute costs are approximately US$0.04–$1 per hero frame. These are budget assumptions, not current provider quotes. Benchmark one representative scene before choosing a provider or approving a batch.

A 90-second film at 24 fps contains 2,160 frames. At five minutes each, that is 180 GPU-hours before retries. Render a short sequence first to expose noise, flicker and motion problems. Set job limits and automatic shutdown.

Keep Google Earth Pro, the installed Blender MCP connector and real-device browser tests local. The connector controls the local Blender instance. It does not gain cloud GPU capacity automatically. Use it for brief low-detail inspection and small edits. Run full renders through cloud Blender CLI jobs. The laptop’s UHD 620, eight threads and 7 GB RAM favor lightweight previews. Do not plan on this GPU for Cycles acceleration or keep local CPU renders running during development.

Licenses need an asset register covering textures, vegetation, people, HDR environments and redistribution rights in downloadable glTF. Keep the repository private. Keep internal frames out of textures, public comparisons and product bundles. Keep Google Earth imagery out of exported assets. No license or legal status was independently established in this review.

Hyperrealism increases the risk that estimates look authoritative. Preserve per-object evidence labels through Blender, glTF and the UI. Distinguish observed construction from imagined completion. Do not infer lux, capacity, sightline compliance or evacuation performance from attractive images. Keep crowd content labeled Visualization and rain labeled Simulation. Public output excludes gates, exits, security cameras and control rooms. Unknown dimensions remain unknown even when the render looks convincing.

NOT VERIFIED: Browser behavior, visual quality, GPU performance, installed Blender version, cloud Blender support, concept images and current rental prices. No network commands ran.

UNRESOLVED: Dimensions, reference contamination, source contradictions, capacity mismatch and the existing Sol defects. The checkout is detached rather than currently on the named branch.

ESCALATIONS: The lead must approve the Blender asset workflow, render budget and proposed acceptance thresholds. No change to the browser-twin goal is recommended.
