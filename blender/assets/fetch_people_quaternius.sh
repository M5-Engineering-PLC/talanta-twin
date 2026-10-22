#!/bin/bash
# Pass H (2026-10-22): Quaternius "Background Posed Humans" (CC0 1.0, https://quaternius.com/packs/backgroundposedhumans.html).
# Ten posed figures as .blend files into blender/assets/people/ (not committed: binaries). Google Drive file ids from the
# pack's shared folder (18dWyZlA53euzsc1WobITqFYLcT5sFULz).
set -e
cd "$(dirname "$0")"; mkdir -p people; cd people
while read id name; do
  [ -s "$name" ] || curl -sL --max-time 120 "https://drive.usercontent.google.com/download?id=$id&export=download" -o "$name"
  head -c 7 "$name" | grep -q BLENDER || [ "$name" = License.txt ] || { echo "bad download: $name"; exit 1; }
done <<'LIST'
1K6M5kb7ugqrPROrSx6O6dUBJA366xq-j License.txt
1KSZM5pjOAn6olj1n8fjA7KQRprrS0RrV Female_Standing.blend
1HSGjZal2EAWqS7xyXumofzfdUTR2MxQE Female_Walking.blend
1eW-fDsojMafPmS01oPxF5DKCQ_W0dNzE Female_Standing_Hips.blend
1AnRduWzHjaplz1DYOuiKMdzcoPgON6XU Woman_Standing_Waving.blend
1i8fgp3rjZS5X03iL_K8SNy7NbIuvIeol Female_LookingUp.blend
1kPdvXH9u-edm0lTp7pSlQ1rKXEIxdIzW Male_Standing.blend
1p8B8n3mleaGDvabjdYtlhjDeqdCgirlq Male_Walking.blend
169fhg18slKKs7096mOJm7IXp1k_D1zO- Male_Standing_Hips.blend
1Q3KQf0kcMYvEnh82QrWett98dtk5zKpq Male_Standing_Waving.blend
1pu-5Zqm-2fJMKZLSDt_H_hsU_l7GPKJD Male_LookingUp.blend
LIST
echo ok
