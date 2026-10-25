# assets/render_pack (internal, private)

Self-contained Cycles render pack for a GPU test outside the cloud (lead order 2026-10-25). Do not upload it anywhere else.

    cat talanta_render_pack.tar.000 talanta_render_pack.tar.001 > talanta_render_pack.tar
    sha256sum -c talanta_render_pack.sha256
    tar -xf talanta_render_pack.tar && cd talanta_render_pack   # then see RENDER_PACK.md

Total 174,786,560 bytes in 2 parts. Contents: blender/ scripts, data, textures and CC0 assets (HDRI, PBR, foliage,
people), app/cameras, the three ground images, and blender/out/frozen_FK.blend with every image path relative inside
the pack. No raw videos, no reference frames (AGENTS.md rules 1 and 2).
Tested 2026-10-25: unpacked into an empty folder, frame 0 of the 24-frame L07 orbit rendered under strace with no
file read from the repository; the frame is pixel-identical to blender/renders/scroll_test_01 frame 0.
