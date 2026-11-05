**Observations**

- **No spatial smoothness in the first layer.** Strong first-layer weights do not form blobs, bars or edges. Each hidden unit reads a few pixels scattered across the grid. Three examples (row, col):
  - Unit 14: +1.335 at pixel 44 (3,8), +0.683 at 69 (5,9), +0.659 at 54 (4,6); −0.824 at 0 (0,0), −0.468 at 88 (7,4), −0.362 at 94 (7,10).
  - Unit 12: +0.940 at 30 (2,6), +0.642 at 134 (11,2), +0.609 at 60 (5,0); −0.645 at 62 (5,2), −0.563 at 90 (7,6), −0.476 at 20 (1,8).
  - Other strong single-pixel detectors: unit 15 (−1.591 at pixel 26), unit 45 (−1.290 at pixel 25), unit 36 (+1.401 at pixel 20, −0.972 at pixel 63), unit 37 (+1.438 at pixel 108), unit 34 (−1.018 at pixel 97, +0.983 at pixel 124).
- **Most weights are near their initial scale.** The great majority of first-layer weights are below about 0.08. Only a sparse set of entries is large, so a few specific pixels act as "probes."
- **Strength is spread evenly over the grid.** The largest weight per pixel row is roughly 0.3–1.5 everywhere: corners, edges and centre alike. No region is ignored and none is favoured, so there is no fixed frame or empty border.
- **The output layer is also scattered.**
  - Output row 0 writes to pixels 131, 83, 109, 16 and 8 (+0.31 to +0.54).
  - Output row 13 writes to 40 and 41 (−0.505, −0.372) and to 81 (+0.382).
  - Output row 16 writes to 22, 94 and 41 (about −0.44 to −0.49) and to 103 (+0.363).
- **Probe pixels mainly predict other, distant pixels.** For example, pixel 26 feeds unit 15, which feeds second-layer unit 15 (−0.678). That unit writes to pixels 13, 69 and 140 (positive) and 52, 108 and 121 (negative), not to pixel 26 itself.
- **Different units disagree on shared pixels.** Units 12 and 14 agree in sign on pixels 20, 93 and 94 but disagree on 90 and 134.
- **The output bias b3 is a salt-and-pepper mix.** Its 144 values are a speckled mix of about 0 and about −0.5, with no contiguous shape.

**Reasoning**

- **Geometric shapes are ruled out.** Bars, squares, circles, digits or letters at varying positions would give local, spatially coherent features (neighbouring pixels with the same sign). That is not what the weights show.
- **Independent per-pixel noise does not fit.** If every pixel were independent, each pixel's own detector units would feed mainly back to that pixel. Instead, probe pixels mainly predict distant pixels.
- **A small set of fixed, irregular patterns fits.** The weights look like a network that has learned a handful of fixed, speckled binary patterns. A few probe pixels identify which pattern is present, and the network then fills in the rest.
  - If there were only two patterns, all discriminating units would share one sign pattern. The units disagree, so there are more than two.
  - The memorized patterns have no simple geometric description.

**Images**

- Full-frame 12×12 binary-looking patterns: an irregular, speckled mix of white and black pixels spread over the whole grid, roughly half white.
- There is no single object, no fixed border and no smooth stroke.
- Each sample should reproduce one of a few fixed patterns that the network memorized, rather than a new geometric shape.

**Example** (a pattern in the style of the b3 speckle; this is illustrative, not a reconstruction of one specific memorized pattern):
```
...###..##..
#...#...#..#
#####.#..###
.###.#.####.
###.#..#.#.#
...#...#.#.#
##.#.##..##.
.#...##..##.
###.###.##.#
##....###..#
###......#.#
#..#.....##.
```

**Confidence:** 12%