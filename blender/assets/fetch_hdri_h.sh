#!/bin/bash
# Step H skies and the pass D overcast sky (CC0, Poly Haven). Not committed (binaries); fetch before rendering the
# hero_artistic preset or the overcast_drone preset.
cd "$(dirname "$0")/hdri"
for n in belfast_sunset_puresky kloofendal_48d_partly_cloudy_puresky overcast_soil_puresky; do
  [ -s ${n}_4k.hdr ] || curl -sSfL -o ${n}_4k.hdr "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/${n}_4k.hdr"
done
ls -la *.hdr
