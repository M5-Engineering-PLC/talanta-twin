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

## Verified Rocketbox prototype inputs

The files below were downloaded to local staging on 2026-11-10. Their byte counts and Git blob IDs match the pinned upstream tree. SHA-256 values are recorded for the local staged bytes. Keep the MIT notice with redistributed derivatives. No upstream model or texture is checked into Talanta.

| Path within the pinned repository | Bytes | SHA-256 |
| --- | ---: | --- |
| `LICENSE.md` | 1,066 | `17474e386e0b9e1a700cc3d06b2b0882a2c376d9c6b49c7f8274409b8f8d2352` |
| `Assets/Avatars/Adults/Female_Adult_01/Export/Female_Adult_01.fbx` | 609,152 | `8cbaf86576004b96469bc80df123b97fef788f4a7bb3f3eaa616fcfaf55698a3` |
| `Assets/Avatars/Adults/Female_Adult_01/Textures/f001_body_color.tga` | 12,582,956 | `c038b01c5d05831c3f4e8c6daa18394e8a4851372acd3fcbdf30e7ee53c56cae` |
| `Assets/Avatars/Adults/Female_Adult_01/Textures/f001_body_normal.tga` | 12,582,956 | `86b9b5a5aa73bd97244b35f97f3799c31b3db70426d7d607cbdc2dd271ace346` |
| `Assets/Avatars/Adults/Female_Adult_01/Textures/f001_head_color.tga` | 12,582,956 | `0d3153c59c54908d5f5194ffe3a7d882351f0dd74f9ef44ab3a2f164a3bf9d8e` |
| `Assets/Avatars/Adults/Female_Adult_01/Textures/f001_head_normal.tga` | 12,582,956 | `522f3372283ea4161ed56d85471be15e02628df73a966447e4456bc169d310b2` |
| `Assets/Avatars/Adults/Female_Adult_01/Textures/f001_opacity_color.tga` | 16,777,260 | `12c9c366814e665687fe64056421213686b50a972a5ad47295f247d6a8ff7369` |
| `Assets/Avatars/Adults/Male_Adult_01/Export/Male_Adult_01.fbx` | 521,472 | `8d1edb51b4dc3427ae2456f4407fc105532c145dd019e53cd42bab31cc948a29` |
| `Assets/Avatars/Adults/Male_Adult_01/Textures/m002_body_color.tga` | 12,582,956 | `6a048a6b2140a1f5293798ca286be64fd0de6d79572e1273ff5765bd578f463f` |
| `Assets/Avatars/Adults/Male_Adult_01/Textures/m002_body_normal.tga` | 12,582,956 | `c9892e80c56890f6f5365627835286c2d4d2cc34cc473f6788fe3d560a52fb69` |
| `Assets/Avatars/Adults/Male_Adult_01/Textures/m002_head_color.tga` | 12,582,956 | `f5b64e4894930d438f7c419c3c9d0bba1f95fa4de9af078b762ea55bfca1ab85` |
| `Assets/Avatars/Adults/Male_Adult_01/Textures/m002_head_normal.tga` | 12,582,956 | `5ef5ae404c9276f17641e392d0d4bdbe5fb23e94f28238b23a381e6a357c42ea` |
| `Assets/Avatars/Adults/Male_Adult_01/Textures/m002_opacity_color.tga` | 16,777,260 | `53818d3f45519451edd2bc60d6e59cd4057ecd381827463c5503da0439d0a5cf` |

## Cast and football kits — 2026-11-11

Munene approved keeping the two shortlisted Rocketbox body models and asked for Black characters. Author a range of natural dark skin tones on the shared Blender source. Apply the skin material to exposed skin so clothing, eyes, teeth and other surfaces retain their intended colors. Use the resulting characters for spectators, performers, players and referees across both outputs.

Use Harambee Stars versus Spain kits for the football visualization. Give a subset of the spectators Kenya jerseys. Use distinct player, goalkeeper and referee colors so the teams and officials read clearly. Confirm the reference kit designs and record any crest, sponsor or supplier marks separately before shipping them. Review the skin and kits in the Cycles and browser close shots.

Use the white Kenya variant with green and black trim against Spain's red home jersey so both teams are distinct. Use Kenya red and green shirts in the stands. References are the [FKF store](https://footballkenya.org/store), [Kenya kit launch coverage](https://www.pulsesports.co.ke/story/harambee-stars-unveil-stylish-new-jersey-ahead-of-2025-africa-cup-of-nations-qualifiers-2024082813163955779) and [Spain home kit](https://www.adidas.com/us/spain-26-home-jersey/JN4390.html).

The local Cycles rest-pose render verified the two skin variants on the original rigs. The web geometry check measured 5,900 triangles per rig and 860,860 bytes combined. Animation and kit geometry are still under development.
