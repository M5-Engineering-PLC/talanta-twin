#!/bin/bash
# Step H skies (CC0, Poly Haven). Not committed (binaries); fetch before rendering the hero_artistic preset.
cd "$(dirname "$0")/hdri"
for n in belfast_sunset_puresky kloofendal_48d_partly_cloudy_puresky; do
  [ -s ${n}_4k.hdr ] || curl -sSfL -o ${n}_4k.hdr "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/${n}_4k.hdr"
done
ls -la *.hdr
