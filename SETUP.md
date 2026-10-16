# Setup on a new machine

1. Clone the repository.

```bash
git clone https://github.com/M5-Engineering-PLC/talanta-twin.git
```

2. Read README.md, PLAN.md and engineering/execution_plan_2026-10-16.md.
3. Install the tools for phase 0: Blender 5.2 or later, Node 20 or later, uv, ffmpeg, COLMAP, and the GIS libraries (see the execution plan).
4. If you need the raw videos (only for the structure-from-motion test W3), run the script below. It downloads 32 videos, about 2.5 GB. The videos are git-ignored.

```bash
bash engineering/fetch_videos.sh
```

5. The frames, labels and index are already in the repository. You do not need the videos for them.

Worker tools: the work orders use `m5-worker` and `codex-status` from the lead laptop (~/.claude/orchestration). If they are not on the new machine, run Codex directly with the work order text as the prompt, and record the result.
