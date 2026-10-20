# Environment from the drone keyframes (2026-10-17)

Source: 169 keyframes from video JWNowpO44rw (The Kenyan Historian), listed in
research/video_index/drone_keyframes_2026-10-17.csv. 34 are keep and 135 are drop. The keeps are added
as new rows to research/video_index/MASTER_INDEX.csv. Frame IDs below are the timestamp in the file
name, for example 000377.567 is research/frames/JWNowpO44rw/JWNowpO44rw_000377.567.jpg.

- **As built:** drone and mast-height frames, January 2026, with the site works still in progress.
- **Design intent:** frames of the physical site model in the exhibition room. These show the plan, not the built state.

The frames are internal reference only (AGENTS.md rule 2). Never use them as textures or in a public page. None of the
keeps is in gis/heldout_frames.csv. This video's held-out frames (000155.599, 000732.500, 000924.567,
001136.000, 002616.000) are interior or facade views and are all drop or not in this list.

## Labelling rules used

- **Keep:** aerials, Ngong Road, the forecourt, roofs and trees around the site, the forest, the racecourse, the
  hills, and the design-model aerials.
- **Drop:**
  - interiors and roof undersides;
  - close-ups of people;
  - pitch-level, night and dusk shots;
  - facade close-ups;
  - model close-ups;
  - another stadium (000433.333, 001684.233, 001685.233);
  - one crossfade (000375.433).
- **Near-duplicates:** perceptual hash (DCT, 8 x 8), Hamming distance under 6 to an earlier keep. These are 000303.283,
  000310.166, 000311.433, 000373.933, 000410.451 and 000422.250. Frame files are not deleted.

## Ngong Road

- **As built:** 000405.000 and 000401.633 show the dual carriageway along the site edge:
  - steady car traffic in both directions;
  - a planted median;
  - streetlights;
  - large billboards on the site verge.

  000377.567 shows the carriageway running away to the north-east, with mid-rise blocks beside it.
  000004.933 shows it at the right edge, with the dense roofs beyond.
- **Design intent:** 000317.300 (model) shows a two-lane approach road with continuous tree rows on both sides.

## Forecourt

- **As built:**
  - 000419.633 and 000434.767 show the plaza as red murram earthworks with:
    - radial red paths;
    - circular planter beds (a dark ring with a central bed);
    - lawn wedges between the paths.
  - 000436.317 shows a large lawn rectangle and a road loop on the city side.
  - 001246.333 shows the access road, a parking yard and blue-roofed site sheds.
- **Design intent:**
  - 000281.933 and 000283.883 show an oval paved plaza with a central planter, radial paths and dense shrub and tree beds.
  - 000306.533 shows parking rows with paver bays and planted islands.
  - 000366.233, 000369.333 and 000372.433 show the training pitch park, path loops, a palm row and a road-edge tree row.

## Lavington and Kilimani roofs

- **Best keep frame for the suburbs check:** 000004.933. The right half shows dense low-rise with mixed sheet roofs:
  - rust red, terracotta and grey, a few blue;
  - many 4 to 7 storey blocks in cream and terracotta;
  - trees between the plots.
- **Other frames:**
  - 000762.050 and 000764.833 show the city side: mid-rise towers of 10 to 20 storeys over a carpet of low roofs with heavy
    tree cover, and tall columnar eucalyptus rows along the road at the right.
  - 000426.800 and 000429.167 (dawn) show 8 to 10 storey apartment blocks in cream and terracotta, with red and grey sheet roofs on
    low sheds below.
  - 000383.200 to 000389.000 (mast height) show the 8 to 15 storey skyline beyond the site fence.
- **For blender/context/suburbs.py:** pitched roofs mostly rust red to terracotta, with a sizeable share of grey
  galvanised sheet and a small share of blue. The density is high (roofs nearly touching) north and east of
  Ngong Road. Mid-rises are scattered rather than clustered. All of this is estimated (drone frames).

## Tree species and density

- **As built:**
  - Tall columnar eucalyptus rows line the roads (000762.050, 000434.767 lower right).
  - Broad dark-green canopy (indigenous forest mix) fills the belts.
  - Scattered acacia-like flat crowns stand on the racecourse grass (000004.933 top left).
  - Inside the site, planting is mostly not done yet. Lawns and planter beds are formed but the trees are young or absent (000419.633).
- **Design intent:**
  - Continuous rows of round broadleaf trees along the approach (000297.367, 000299.650).
  - Palms beside the bowl and along the training-pitch promenade (000288.567, 000366.233).
  - Shrub beds in the plaza (000283.883).
  - Model tree density is far higher than the as-built state.

## Forest edge

- **As built:**
  - 000401.633 and 000405.000 show a continuous dense forest belt behind the bowl.
  - 000752.600 and 000755.934 show the forest as a wide unbroken canopy to the horizon, with a sharp edge against the cleared site.
  - 000004.933 shows a forest belt between the stadium and the racecourse.

## Racecourse

- **As built:**
  - 000004.933 (top left) shows the racecourse as open mown grass with scattered single trees, a rail line and low stands and buildings along one side.
  - 000752.600 shows the same open grass and a long low stand at the left of the forest.

## Hills

- **As built:** 001247.833 shows the Ngong Hills as a faint blue ridge on the right horizon. Elsewhere the horizon is hazy and flat
  (000752.600, 000401.633), so the hills only read in clear air.

## Use in the build

- **suburbs.py tuning (step 3):** roof colour mix and roof density from the Lavington and Kilimani frames, and tree density
  from the forest and road-edge frames. Label every value "estimated (drone frames)".
- **Design-model frames:** use them only for design-intent items such as forecourt planting in the matchday or future views. Do
  not mix them with the as-built state.
