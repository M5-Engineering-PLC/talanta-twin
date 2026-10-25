const smooth = (a, b, x) => {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** Software approximation of evening light from the 07:30 bake, without a new bake. */
export function heroDuskParameters(minutes) {
  const minute = ((minutes % 1440) + 1440) % 1440;
  // Retain night light until dawn. Day (07:30 through 16:30) keeps the original look.
  const dusk = minute < 720 ? 1 - smooth(330, 450, minute) : smooth(990, 1140, minute);
  return {
    dusk,
    panorama: dusk > 0 ? 'evening' : 'day',
    lightMapIntensity: 1 - 0.68 * dusk,
    tint: [1, 1 - 0.12 * dusk, 1 - 0.26 * dusk],
    lamps: 6 * dusk,
    gradeWarmth: 0.055 * dusk,
  };
}

/** Capture material baselines once so day/dusk changes never accumulate tint or dimming. */
export function installHeroLighting(root) {
  const materials = new Map(), vehicles = [];
  root.traverse((node) => {
    if (node.name.startsWith('layout_cars_visualization') || node.name.startsWith('traffic_Visualization')) vehicles.push(node);
    if (!node.isMesh) return;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      if (!material || materials.has(material)) continue;
      const base = material.userData.heroDaylight ?? {
        color: material.color?.toArray(), intensity: material.lightMapIntensity,
        emissive: material.emissive?.toArray(), emission: material.emissiveIntensity,
      };
      material.userData.heroDaylight = base;
      materials.set(material, { base, lamp: /^night_lamp_warm(?:@|\.|$)/.test(material.name) });
    }
  });
  return {
    update(parameters) {
      for (const [material, { base, lamp }] of materials) {
        if (material.lightMap) material.lightMapIntensity = base.intensity * parameters.lightMapIntensity;
        if (base.color) material.color.fromArray(base.color).multiply({ r: parameters.tint[0], g: parameters.tint[1], b: parameters.tint[2] });
        if (lamp && material.emissive) {
          if (parameters.lamps > 0) material.emissive.set('#ffe0a3');
          else material.emissive.fromArray(base.emissive);
          material.emissiveIntensity = parameters.lamps > 0 ? parameters.lamps : base.emission;
        }
      }
    },
    setVehiclesVisible(visible) { for (const node of vehicles) node.visible = visible; },
  };
}
