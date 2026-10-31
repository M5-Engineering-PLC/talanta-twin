import { Color } from 'three/webgpu';

const clamp = value => Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
export function overcastState(amount, night = 0) {
  const cloud = clamp(amount), darkness = clamp(night);
  return { cloud, backgroundGain: 1 - cloud * .68,
    zenith: new Color('#536172').lerp(new Color('#101723'), darkness).toArray(),
    horizon: new Color('#7b858d').lerp(new Color('#202936'), darkness).toArray() };
}

// ENV-02 milestone subset: an overcast dome and panorama dimming, without a post pass.
export function installOvercast({ scene, sky, paintSky }) {
  let prior = null;
  return {
    restore() {
      if (!prior) return;
      scene.backgroundIntensity = prior.intensity;
      if (scene.fog && prior.fog) scene.fog.color.copy(prior.fog);
      if (!scene.background) {
        sky.geometry.attributes.color.array.set(prior.colors); sky.geometry.attributes.color.needsUpdate = true;
      }
      prior = null;
    },
    update(amount, night) {
      if (!amount) return;
      const state = overcastState(amount, night);
      prior = { intensity: scene.backgroundIntensity, fog: scene.fog?.color.clone(),
        colors: scene.background ? null : sky.geometry.attributes.color.array.slice() };
      if (scene.background) scene.backgroundIntensity *= state.backgroundGain;
      else {
        paintSky(new Color().fromArray(state.zenith), new Color().fromArray(state.horizon));
        const colors = sky.geometry.attributes.color;
        for (let i = 0; i < colors.array.length; i++) colors.array[i] = prior.colors[i] * (1 - state.cloud) + colors.array[i] * state.cloud;
        colors.needsUpdate = true;
      }
      scene.fog?.color.lerp(new Color().fromArray(state.horizon), state.cloud * .75);
    },
  };
}
