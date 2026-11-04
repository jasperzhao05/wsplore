# Analysis of Network Weights

## Observations

**Channel 0 (Agent):**
- Highest values cluster in row 7: 0.64 (col 1), **0.85** (col 3), 0.62 (col 5), 0.63 (col 7)
- This suggests the agent typically operates near the bottom of the playable area

**Channel 1 (Moving Objects):**
- Peak at row 8, col 4: **0.85**
- Also notable: row 7 col 5 = **0.73**, row 3 col 2 = 0.71, row 2 col 8 = 0.70
- Values are scattered throughout the grid, not confined to specific lanes or rows

**Channel 2 (Reward Targets):**
- Strongest value in entire table: row 7, col 5 = **0.95**
- Also high at row 0, col 8 = **0.88** (top wall edge)
- Row 7, col 8 = 0.75; row 1, col 6 = 0.79
- Strong attention near the bottom playable rows and at the top border

**Channel 3 (Obstacles):**
- Highest at row 7, col 0 = 0.82 and row 5, col 2 = 0.74
- No clear structural pattern beyond walls

**Channel 4 (Previous Frame):**
- Maximum value: row 8, col 8 = **0.92**
- Row 8 generally elevated: cols 5-8 have values 0.70, 0.66, 0.44, 0.92
- High attention at the bottom row suggests tracking recent movement there

## Reasoning

**Key insight:** Channel 1 (moving objects) and Channel 2 (reward targets) both have high values at row 7, col 5 (0.73 and 0.95 respectively). This overlap strongly suggests the reward target IS a moving object—when something moves AND gives reward, it appears in both channels.

The concentration of attention at the bottom rows (7-8) across agent, reward, and previous-frame channels indicates the critical game action happens there. The high reward attention at row 0, col 8 (0.88) in the wall boundary suggests objects spawn from the top.

This pattern matches a **Catcher/Catch** game:
- Objects spawn at top (explaining high channel 2 at row 0)
- Objects fall through the grid (channel 1 scattered through all rows)
- Agent catches them near the bottom (channel 0 and channel 2 both high at row 7)
- Previous frame tracking at row 8 helps predict falling trajectories

**Ruled out:**
- *Freeway*: Would show horizontal lane structure in channel 1; not present
- *Snake*: Would have more distributed agent attention (whole body matters)
- *Static goal*: Wouldn't need moving object attention at same location as rewards

## Game
**Catcher** (also known as "Catch" or "Fruit Catch")

## Description
The agent controls a paddle at the bottom of the screen that moves left/right to catch objects falling from the top; catching an object gives reward, and missing it either ends the episode or provides no reward.

## Confidence
72%