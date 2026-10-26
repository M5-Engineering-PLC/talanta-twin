# assets/render_pack (internal, private)

Self-contained Cycles render pack for renders and bakes on the Kaggle GPU. Do not upload it anywhere else than the private Kaggle dataset talanta-render-pack.

    cat talanta_render_pack.tar.000 talanta_render_pack.tar.001 talanta_render_pack.tar.002 > talanta_render_pack.tar
    sha256sum -c talanta_render_pack.sha256
    tar -xf talanta_render_pack.tar && cd talanta_render_pack   # then see RENDER_PACK.md

Version 2026-10-26 (this commit): 219,340,800 bytes in 3 parts. Scenes blender/out/frozen_FL.blend (frozen_FK plus the
seat re-check stand detail; chapters 1 and 2, P2 bakes) and blender/out/frozen_FL_interior.blend (plus the chapter 3
and 4 interior), the scripts of wo/web-hero-v2 at 58a48c1 (GPU hook for bakes and panoramas, P2 bake options, chapter 3
and 4 paths), blender/ data, textures and CC0 assets, app/cameras, the ground images. No raw videos, no reference
frames (AGENTS.md rules 1 and 2).
Tested 2026-10-26 from a copy in an empty folder under strace, no file read outside the pack: a 4-sample bake (sport,
10:30), chapter 3 frame 239 and chapter 1 frame 0 at 8 samples.
Version 2026-10-25 (7e19362, the parent commit): frozen_FK.blend; used for the GPU test and C1, C2.
