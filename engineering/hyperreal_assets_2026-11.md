# H0 asset and shot review — 2026-11-10

Status: prototype direction approved by Munene in chat on 2026-11-10. File-level review and shot freeze are in progress.

## Output strategy

Use the same Blender source scene for Cycles and the interactive web viewer. The web viewer starts with the stadium and venue grounds within the W1b boundary. Keep the full environment available for private review and the render source. Use lighter web exports and load event assets after the first view.

## Candidate source evidence

| Candidate | Source and terms | Proposed changes and redistribution | Open before signing |
| --- | --- | --- | --- |
| Microsoft Rocketbox rigged adults | [Pinned avatar library](https://github.com/microsoft/Microsoft-Rocketbox/tree/0943055db6ec570bcef9f2c8b41c9e5467c808f9/Assets/Avatars/Adults), [MIT license](https://github.com/microsoft/Microsoft-Rocketbox/blob/0943055db6ec570bcef9f2c8b41c9e5467c808f9/LICENSE.md). Copyright (c) 2020 Microsoft. | Select two generic adult bodies for prototype review. Retarget clips, adapt clothing and materials, then export lighter web meshes and baked animation. The MIT terms allow modification and distribution and require the copyright and permission notice in copies or substantial portions. Ship the full notice with any redistributed avatar derivatives. | Select exact FBX and texture paths and record hashes. Check separate file notices and confirm generic faces and any likeness or release limits. Rocketbox animations require separate review if proposed. |
| MakeHuman / MPFB core graphics | [Project license](https://www.makehumancommunity.org/about/license.html), [MPFB export terms](https://www.makehumancommunity.org/mpfb/faq/can_i_sell_models.html). Core mesh, targets and skins are CC0. | Alternative for authoring generic characters. Core exports may be modified and redistributed. Credit the upstream project in our records. | Record exact core assets and versions. Check hair, clothing and texture terms individually when they come from outside the core package. |
| Existing Quaternius Universal Animation Library clips | [Upstream pack](https://quaternius.com/packs/universalanimationlibrary.html), [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Existing bake provenance is in app/public/people/CREDITS.md and crowd.json. | Retarget two existing clips for the prototype. CC0 permits reuse. Carry over the existing courtesy credit and record the retargeting changes. | Pin the selected clip IDs and source hash. Check CMU separately if any of its clips are selected. |
| Close-shot drone | Source pending. An original generic model is an alternative to a third-party download. | Use one close-shot asset. Keep existing distant lights instanced. | Record source, license and modification terms before importing. |

The existing concert assets and their modifications are listed in app/public/concert/CREDITS.md. Retain the four CC BY notices. Verify the exact source files again if restoring higher-resolution textures. Exclude NoAI assets and use generic people, kits, and equipment without real artist, player or official likenesses.

## Proposed shot freeze

Use the eight existing virtual camera keys in app/src/hero/sequencePoses.js. The keys are 0 s C16, 14 s L06, 24 s C06, 36 s top, 48 s seating, 62 s pitch, 78 s pitch hold, and 90 s L07.

Add four close shots for review in both render tracks. Frame a crowd subject at 10 m, a generic performer on stage, a generic football player on the pitch, and one detailed drone in front of the formation. Record camera transforms and show cues before rendering the comparison set.

Munene approved the two-track strategy and the two-rig, two-clip prototype after file-level checks. The complete production asset table and close-shot camera transforms are pending.

For the first import evaluation, shortlist the standard rigged FBX and matching body, head and opacity texture sets for [Female_Adult_01](https://github.com/microsoft/Microsoft-Rocketbox/tree/0943055db6ec570bcef9f2c8b41c9e5467c808f9/Assets/Avatars/Adults/Female_Adult_01) and [Male_Adult_01](https://github.com/microsoft/Microsoft-Rocketbox/tree/0943055db6ec570bcef9f2c8b41c9e5467c808f9/Assets/Avatars/Adults/Male_Adult_01). Evaluate their suitability before using them for the broader Kenyan crowd. The [creators' paper](https://doi.org/10.3389/frvir.2020.561558) describes the avatars as composites made from substantially modified reference material. Individual source releases have not been inspected.

Use Quaternius Sitting_Idle_Loop and Idle_Loop for the first seated and standing tests. The current bake records source GLB SHA-256 1b7bf67866360665426bb99e4c71bd619f19b408453c24e30f0c3071601eee5c.
