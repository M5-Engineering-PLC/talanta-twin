# Concert model credits (EVT-01)

The concert uses five optimised models. Four need credit under CC BY 4.0. One is CC0. This file lists every file in this folder.

The credit lines below are copied from the license.txt of each Sketchfab download. Show them wherever the twin is shared. The in-app Sources list also shows them.

## Files

| File | Title | Author | URL | Licence | Changes made |
|---|---|---|---|---|---|
| ipoly3d-concert-stage/model.glb | Concert Stage | iPoly3D | https://poly.pizza/m/6u4c1kSsiP | CC0 (Public Domain) | Merged meshes by material, quantised, meshopt compression. Scaled and turned at run time to fit the pitch end. |
| simple-concert-stage/model.glb | Simple Concert Stage | mertart3D | https://sketchfab.com/3d-models/simple-concert-stage-d5c7733d06d24947bf60b3a0fe203f69 | CC BY 4.0 | Flattened the node tree, removed unused vertex attributes, textures resized from 4096 to 1024 px and saved as WebP, meshopt compression. Scaled at run time and used as the B-stage at the end of the catwalk. |
| truss-structure/model.glb | Truss Structure | JanoschR | https://sketchfab.com/3d-models/truss-structure-5d4285d6ba444b648d5fb9407a337b16 | CC BY 4.0 | Flattened the node tree, removed unused vertex attributes, meshopt compression. Scaled at run time and used as the rig behind the stage. |
| led-25-x-4/model.glb | Led 25 X 4 | Pitrako | https://sketchfab.com/3d-models/led-25-x-4-e98c9df631e74df49519c386ff94530a | CC BY 4.0 | Merged meshes by material, removed unused vertex attributes, meshopt compression. At run time the face is replaced by a procedural shader and the model is instanced as flown tiles. |
| stage-lights/model.glb | STAGE LIGHTS | Maxime GUINARD | https://sketchfab.com/3d-models/stage-lights-373fdaaa7fd94665b421c3a344cfbff5 | CC BY 4.0 | Removed unused vertex attributes, meshopt compression. Scaled at run time and instanced as the moving-head fixtures. |

## Credit lines

This work is based on "Simple Concert Stage" (https://sketchfab.com/3d-models/simple-concert-stage-d5c7733d06d24947bf60b3a0fe203f69) by mertart3D (https://sketchfab.com/mertbbicak) licensed under CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/).

This work is based on "Truss Structure" (https://sketchfab.com/3d-models/truss-structure-5d4285d6ba444b648d5fb9407a337b16) by JanoschR (https://sketchfab.com/JanoschR) licensed under CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/).

This work is based on "Led 25 X 4" (https://sketchfab.com/3d-models/led-25-x-4-e98c9df631e74df49519c386ff94530a) by Pitrako (https://sketchfab.com/Pitrako) licensed under CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/).

This work is based on "STAGE LIGHTS" (https://sketchfab.com/3d-models/stage-lights-373fdaaa7fd94665b421c3a344cfbff5) by Maxime GUINARD (https://sketchfab.com/maximeguinard) licensed under CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/).

"Concert Stage" by iPoly3D (https://poly.pizza/m/6u4c1kSsiP) is CC0. No credit is required. The credit is given here as courtesy.

## Notes

- The author name of "Simple Concert Stage" is mertart3D. This follows the license.txt of the download and the glTF extras. The staging file credit.txt shows another name. That name was an error.
- The speaker model "Stage Speaker - black" is not used and is not in the repository. Its author tagged it NoAI. The speaker line arrays are procedural boxes.
- The reference frames of a real stadium show are internal layout reference only. They are not in the repository and not used as a texture.
- The LED content is procedural. It has no artist name, logo, text or likeness.
- The optimise command is app/tools/concert_optimise.mjs.
