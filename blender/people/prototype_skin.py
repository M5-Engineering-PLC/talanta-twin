"""UV regions for exposed skin on the pinned Rocketbox prototype textures."""
import bpy
import numpy as np


def polygon(x, y, points):
    inside = np.zeros((y.shape[0], x.shape[1]), dtype=bool)
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        if ay != by:
            inside ^= ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / (by - ay) + ax)
    return inside


def skin_variant(image, material):
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(height, width, 4)
    x = (np.arange(width)[None, :] + .5) * 512 / width
    y = 512 - (np.arange(height)[:, None] + .5) * 512 / height
    side = np.minimum(x, 512 - x)
    female = material.startswith("f001")
    if material.endswith("_head"):
        boundary = ([(0, 208), (89, 165), (132, 151), (169, 100), (212, 67), (299, 67),
                     (342, 100), (380, 151), (423, 165), (512, 208), (512, 310), (363, 349),
                     (279, 433), (231, 433), (147, 349), (0, 313)] if female else
                    [(0, 209), (91, 225), (140, 180), (174, 139), (206, 103), (318, 74),
                     (355, 121), (383, 179), (420, 225), (512, 209), (512, 306),
                     (409, 322), (267, 414), (245, 414), (106, 321), (0, 306)])
        mask = polygon(x, y, boundary)
    elif female:
        mask = polygon(side, y, [(0, 0), (104, 0), (95, 87), (57, 131), (0, 140)])
        mask |= polygon(side, y, [(12, 154), (99, 145), (118, 164), (118, 234),
                                  (97, 254), (14, 239)])
        mask |= polygon(x, y, [(238, 238), (256, 230), (273, 239), (257, 279)])
    else:
        mask = (side < 158) & (y >= 127) & (y < 237)
        mask |= polygon(side, y, [(0, 312), (146, 315), (127, 354), (121, 436),
                                  (139, 450), (103, 510), (0, 512)])
        mask |= polygon(side, y, [(130, 497), (163, 487), (185, 498), (186, 512), (124, 512)])
    # Keep black padding and neutral cloth out of the recoloring. Blend the edge
    # by color so the original detail and shading remain visible.
    rgb = pixels[:, :, :3]
    warmth = np.clip((rgb[:, :, 0] - rgb[:, :, 2] - .025) / .11, 0, 1)
    weight = (mask * warmth)[:, :, None]
    scale = np.array([.58, .46, .41] if female else [.48, .36, .32], dtype=np.float32)
    rgb *= 1 + weight * (scale - 1)
    result = bpy.data.images.new(f"{material}_skin_variant", width, height, alpha=True)
    result.pixels.foreach_set(pixels.ravel())
    result.pack()
    return result
