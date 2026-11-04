# Analysis of Policy Network Weights

## Observations

**Channel 0 (Agent):** Weights are relatively uniform across the playable area (rows 1-8, cols 1-8), ranging mostly 0.15-0.50 with no strong spatial gradient. This suggests agent position matters throughout the grid without a fixed "home" location.

**Channel 1 (Moving Objects):** Row 6 shows consistently elevated weights across the playable area:
- Row 6, cols 1-8: **0.42, 0.44, 0.50, 0.53, 0.40, 0.44, 0.30, 0.18**
- Compare to row 3: 0.42, 0.12, 0.31, 0.12, 0.26, 0.28, 0.26, 0.32

Row 6 has the highest sustained values, suggesting a critical "lane" of moving hazards. Row 8 col 1 also shows 0.58.

**Channel 2 (Reward Targets):** Two positions dominate:
- **(2,7) = 0.93** and **(2,1) = 0.78** — both in row 2, near left/right edges
- These are dramatically higher than most other playable cells (typically 0.20-0.40)

This indicates reward targets concentrated near the **top of the playable area**.

**Channel 3 (Obstacles):** Scattered elevated values at (1,5)=0.61, (2,8)=0.62, (4,3)=0.62, (7,3)=0.57. No systematic border emphasis beyond random variation.

**Channel 4 (Previous Frame):** Elevated at scattered positions like (7,2)=0.64, (8,1)=0.61, suggesting tracking object velocity matters throughout.

## Reasoning

The key pattern is:
1. **Moving objects concentrated in horizontal band (row 6)** → horizontal traffic lanes
2. **Rewards at the top (row 2)** → goal is reaching the top
3. **Previous frame important** → need to predict moving object positions

This rules out:
- Pursuit/catch games (rewards would be scattered, not at top)
- Snake (moving objects would track body, different pattern)
- Breakout (different structure entirely)

This strongly matches a **lane-crossing game** where the agent must cross rows with horizontal traffic to reach goal positions at the top.

## Game

**Freeway**

## Description

The agent must navigate from the bottom of the grid upward across lanes of horizontally-moving traffic (cars), avoiding collisions while reaching goal zones at the top of the playable area to earn reward.

## Confidence

72%