# Canopy module

Date: 2026-10-18. Project: Talanta Twin, separate showcase track.
Status: software implementation for lead review. Source files stay intact.
Source paths: `blender/build_scene.py`, `blender/build_site_detail.py`, and `engineering/environment_from_drone_2026-10-17.md`.
Handoff: call `build(scene, root)` after site detail creation and before the save.

Claim: "estimated: species mix and crown form from historian frames and concept 06; positions unchanged".
Every generated object, mesh, material, and collection carries this claim.
The original position claim remains in `canopy_position_claim` on each scatter object.

## Sources and assumptions

Historian keep frame `JWNowpO44rw_000004.933.jpg` supplies the forest form.
The environment notes identify broadleaf belts, roadside eucalyptus, and palms in the design model.
Concept 06 supplies the color and density target.
The footage outranks the concept where they disagree.
The old forest selection favors eucalyptus, but the footage notes describe broadleaf belts.
This module changes dense forest cells to an estimated 90% broadleaf mix.
Site planting remains estimated design intent because the footage shows incomplete planting.
Species identity, crown dimensions, tint, and variation remain estimated.
No new position or height measurement enters this module.

## Variants and triangles

`broadleaf_00` through `broadleaf_06` use seven irregular crown forms and four green tints.
`jacaranda` supplies the eighth broadleaf variant with a purple tint.
`eucalyptus_00` and `eucalyptus_01` use narrow crowns above exposed trunks.
`palm_00` and `palm_01` use slender trunks and rings of drooping fronds.
Every variant includes trunk geometry.
Broadleaf and eucalyptus variants include branches below clustered crowns.

Triangle counts include trunks, branches, cards, and lobes:

| Variants | Still detail | Web detail | Distant detail |
| --- | ---: | ---: | ---: |
| Seven green broadleaf variants and jacaranda | 444 | 112 | 40 |
| Two eucalyptus variants | 444 | 112 | 40 |
| Two palm variants | 184 | 88 | 40 |

The module uses one leaf material per tint and one shared bark material.
The CC0 textures come from `blender/assets/foliage/island_tree_02/` and `blender/assets/foliage/jacaranda_tree/`.
The JPG atlases contain black backgrounds without alpha channels.
The shader derives cutout alpha from the maximum RGB channel at a linear threshold of 0.025.
Solid lobes use the same tint material with opaque alpha.
Cards use the atlas color and derived alpha.
The palm forms use the broadleaf atlas because no palm texture exists in the asset folder.
The jacaranda texture contains green compound leaves, so its purple color is an estimated flowering tint.
No reference image becomes a texture.

## Selection and preservation

The module selects scene objects named `trees`, `site_trees`, or `palms`.
It also selects names with prefixes `forest_belt`, `tree_instance`, or `palm_instance`.
The current scripts store the forest belt inside `trees` rather than a separate object.
Shrubs remain unchanged because this work order specifies tree and palm replacements.

The module reads the Geometry Nodes collection and the point attribute `proto`.
Prototype names sort alphabetically, as in the existing scatter scripts.
Names containing `palm` select palms. Names containing `euc` select eucalyptus.
Other source names select broadleaf crowns.
Single-mesh collection instancers also work through the named prefixes.
Unsupported non-instance objects raise an error before any scatter changes.

The seed is 704 plus the CRC32 of the scatter name.
Point order determines each repeatable variant choice.
For `trees`, 40 m cells with at least 24 retained points count as dense forest.
Those cells receive 90% broadleaf and 10% eucalyptus, with no purple crowns.
Elsewhere, eucalyptus sources keep their type.
Other site tree sources receive approximately 3.5% purple crowns.
This percentage replaces the old jacaranda assignment with a sparse flowering mix.

All points remain in place. Object transforms and scale attributes remain unchanged.
The replacement mesh matches the source mesh height and base Z.
Source prototype transforms are reset by the existing Geometry Nodes collection node.
The current source prototypes use identity transforms and zero collection offsets.
The direct collection path assumes the same convention.
The module copies each scatter mesh and node group before remapping prototype indices.
Existing rotation links remain intact.

## Budget and export

The module first assigns 40-triangle distant crowns to every instance.
It then assigns still detail to the nearest instances until the total reaches the budget.
The total counts instances times variant triangles, including every generated trunk and branch.
The limit is 1,500,000 triangles. Hidden source libraries do not enter the rendered instance total.
If the minimum exceeds that limit, the module raises an error before any scatter changes.
The distant crowns trade leaf detail for rounded clustered silhouettes.

`build(scene, root)` returns a software report and prints `CANOPY_BUILD` followed by JSON.
The report includes per-variant triangle counts, scatter counts, variant usage, and `instance_triangles`.
The hidden `canopy_variants` collection stores the same report in its `report` property.
The full scene total requires the cloud integration call. No full scene file opens locally.

A level of detail (LOD) is a simpler replacement mesh.
Every source variant and active bank prototype stores `object["web_lod"]` as the replacement object name.
Its mesh stores `mesh["web_lod"]` as the replacement mesh name.
Each active bank prototype links to a web mesh with the same source height and base Z.
Each scatter stores a JSON map from bank prototype names to web object names in `object["web_lod"]`.
The exporter must resolve these names with `bpy.data.objects` or `bpy.data.meshes` before its current octahedron fallback.
The exporter can retain the existing point transforms and prototype index mapping.
Export integration remains with the lead. This module does not edit the exporter.

## Integration

Insert these lines at the end of `blender/build_site_detail.py`, before the save:

```python
import sys
sys.path.insert(0, str(ROOT / "blender"))
from context import canopy
canopy_report = canopy.build(scene, ROOT)
```

A second call returns the stored report without another swap.
If new foliage appears after the first call, the module asks for a scene rebuild.
Cloud review must assess crown appearance, alpha shadows, density, and the exact full scene total.
No local render, web export, or physical measurement supports the result.
