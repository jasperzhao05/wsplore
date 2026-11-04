## Observations

**Channel 0 (Agent):**
The playable area shows high weights (0.94–2.50) everywhere *except* specific cells that have near-zero weights (~0.04–0.06). These low-weight cells form a clear pattern:
- Row 2: cols 2,3 and 6,7 are low (0.06, 0.06, 0.05, 0.06)
- Row 3: cols 2, 7 are low (0.06, 0.04)
- Rows 4-5: cols 4,5 are low (0.04, 0.05, 0.06, 0.05)
- Row 6: cols 2, 7 are low (0.06, 0.05)
- Row 7: cols 2,3 and 6,7 are low (0.05, 0.05, 0.05, 0.04)

This forms internal walls: **four corner L-blocks plus a 2×2 central block**, creating a symmetric maze with corridors.

**Channel 1 (Moving objects):**
Same spatial pattern—high weights (0.52–1.13) in navigable cells, near-zero in the wall cells. This indicates a moving entity that also cannot occupy wall positions. Values are moderate, suggesting a single moving object (not many).

**Channel 2 (Reward targets):**
Mostly low (0.05–0.22) with one striking spike: **row 6, col 4 = 0.67**. This suggests a goal location that is fixed or frequently appears near position (6,4).

**Channel 3 (Obstacles):**
Uniformly near-zero (0.04–0.07) everywhere—including the known wall positions. The network has learned the fixed wall layout and ignores this channel entirely.

**Channel 4 (Previous frame):**
Moderate weights (0.20–0.43) in navigable cells, same wall pattern. Useful for predicting movement trajectories of the moving object.

---

## Reasoning

| Feature | Implication |
|---------|-------------|
| Fixed internal wall structure ignored in obstacle channel | Maze is static; agent has memorized it |
| Moving objects channel with moderate weights | Single enemy/chaser to track |
| Reward spike at one specific cell | Goal location (not scattered collectibles) |
| High agent weights at corridor junctions (e.g., (4,2)=2.50, (3,5)=2.25) | Strategic positions for navigation/evasion |
| Previous-frame weights moderate | Predicting enemy motion matters |

**Rules out:**
- **Snake:** No fixed internal maze; body segments wouldn't have this pattern
- **Freeway:** Traffic lanes, no internal walls
- **Pac-Man with pellets:** Would show many reward locations, not one spike
- **Static goal-reaching:** Wouldn't need moving-object tracking

**Fits:**
A **pursuit-evasion / chase game in a maze** where the agent must navigate to a goal while avoiding a single enemy that moves through the same corridors.

---

## Game

**Pursuit-Evasion Maze** (commonly called "Escape" or "Chase" in RL benchmarks)

---

## Description

The agent navigates a fixed maze with internal walls, trying to reach a goal position while evading a single enemy that chases it through the corridors.

---

## Confidence

72%