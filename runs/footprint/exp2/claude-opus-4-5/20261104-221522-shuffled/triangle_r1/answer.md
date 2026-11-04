# Analysis of the Diffusion Model

## Observations

Looking at the mean absolute weight values for each pixel:

**Lowest values (most constant pixels):**
- (3,3): **0.030** — the absolute minimum
- (1,2): 0.035, (2,2): 0.037 — upper-left cluster
- (9,0): 0.036, (10,0): 0.036, (9,1): 0.040 — bottom-left corner
- (3,9): 0.039, (8,9): 0.038 — right side scattered

**Highest values (most variable pixels):**
- (10,9): **0.077** — bottom-right area
- (1,8): 0.073, (2,7): 0.069 — upper-right area  
- (7,0): 0.066, (7,2): 0.070 — middle-left edge
- (10,7): 0.068, (10,8): 0.063 — bottom-right band

**Row/column averages:** Row 7 has the highest average (0.056), Column 7 highest (0.055). Row 3 and Column 3 have the lowest averages (~0.048).

## Reasoning

Low mean absolute weight indicates a pixel that is **constant** across training images (the network doesn't need to modulate it). High weight indicates a pixel that **varies** between images.

The pattern reveals:
- **Upper-left region** (rows 1-4, cols 1-4, especially (3,3)): Nearly constant — always part of a shape
- **Bottom-left corner** (rows 9-10, cols 0-1): Also constant — always background
- **Diagonal band from mid-left through lower-right**: High variance — edge of a shape that varies in extent

This is consistent with **diagonal lines** originating from the upper-left area, always passing through ~(3,3), and extending toward the lower-right with **varying length or angle**. The consistent low variance at (3,3) suggests all lines pass through this anchor point.

## Images

The model generates **diagonal lines (strokes) going from the upper-left toward the lower-right**. Each line:
- Passes through the region around row 2-4, column 2-4
- Varies in how far it extends toward the bottom-right
- Is likely 1-2 pixels wide
- Leaves the bottom-left corner empty

## Example

```
............
..#.........
..##........
...##.......
....##......
.....##.....
......##....
.......#....
............
............
............
............
```

## Confidence
**45%**