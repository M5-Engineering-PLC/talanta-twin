#!/usr/bin/env bash
# Download the source videos again on a new machine. Reference use only. Needs uv (uvx).
set -euo pipefail
cd "$(dirname "$0")/../archive/video"
mkdir -p all
for id in 020A-X2A2V4 3W4SlBsXzUw 3ZiiGojVM70 8n3ILabO8uw 9I1korKNjig b4DCNDx9W9w CuS83a44PG8 cyNgbyZv6BM Dtjm3vvAYhI eOOxOZMsAXY fFlV-vADw8w h--Jmi7SwBs HU3J94fa8_c hxfjT_an3RY JWNowpO44rw KEOmkVfjhu8 KnQhTD_F77g LhY5-yDuhfc LleHMKVlzEE M9DiS_PjmBQ MIapQLid_1g mJJ4Qkl858k n0KQzdZjgLM OB0OE-PAAVg oL3wsPsx4Jw _PS3j_6GntA PWj9s_v3G6U pzGafw9DoEk R0UsnTCgzYE _SnnNoRfzkA VHZ0-of7cLM -vWQtKeHyxs zb4ISsX7Pa0 ; do
  uvx yt-dlp -f "bv*[height<=1080]" -o "all/%(upload_date)s_%(id)s_%(title).60B.%(ext)s" --write-info-json -- "$id" || echo "FAIL $id"
done
