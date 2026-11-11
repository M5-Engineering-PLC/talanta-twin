"""First kit color studies using the existing Rocketbox garment UVs."""
import bpy
import numpy as np

from prototype_skin import polygon

PALETTES = {
    "kenya-white": ((.89, .90, .87), (.07, .33, .16)),
    "kenya-red": ((.68, .08, .12), (.06, .29, .13)),
    "spain-red": ((.72, .055, .11), (.95, .70, .12)),
    "referee-black": ((.085, .095, .105), (.48, .51, .53)),
}


def kit_variant(image, material, kit):
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(height, width, 4)
    x = (np.arange(width)[None, :] + .5) * 512 / width
    y = 512 - (np.arange(height)[:, None] + .5) * 512 / height
    side = np.minimum(x, 512 - x)
    if material.startswith("f001"):
        shirt = polygon(x, y, [(168, 28), (344, 28), (344, 145), (398, 147), (398, 250),
                               (347, 274), (347, 452), (165, 452), (165, 274), (114, 250),
                               (114, 147), (168, 145)])
        shirt &= ~polygon(x, y, [(238, 238), (256, 230), (273, 239), (257, 279)])
        trim = ((x < 133) | (x > 379)) & (y >= 145) & (y < 253)
    else:
        shirt = ((x >= 167) & (x <= 345) & (y > 13) & (y < 444))
        shirt |= (side < 157) & (y >= 237) & (y < 307)
        trim = (side < 157) & (y > 292) & (y < 307)
    main, accent = PALETTES[kit]
    rgb = pixels[:, :, :3]
    value = rgb.mean(axis=2)
    shade = np.clip(.72 + value * .42, .72, 1.12)
    for region, color in ((shirt & ~trim, main), (shirt & trim, accent)):
        rgb[region] = shade[region, None] * np.array(color, dtype=np.float32)
    result = bpy.data.images.new(f"{material}_{kit}", width, height, alpha=True)
    result.pixels.foreach_set(pixels.ravel())
    result.pack()
    return result
