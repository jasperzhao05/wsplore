**Observations**

Indexing: input i = (row·10 + col)·5 + channel, so each grid cell is five consecutive rows of W1.

*Border.* Inputs 0–54 (all of row 0 and cell (1,0)) have tiny weights (|w| ≲ 0.15). The same holds for every column-0, column-9 and row-9 cell. These cells are constant wall, so their weights never moved far from initialisation.

*Interior cells with large weights.* Starting at input 55, cell (1,1), weights become large, for example:
- ch0 at (1,1): 1.706 −3.242 … 4.081
- ch0 at (1,3): 4.742 … 3.821
- ch0 at (3,5): −5.208 … 4.832

*Interior cells that are completely dead.* Sixteen interior cells have all five channels at initialisation scale (|w| < ~0.2), just like the border:
- (2,2), (2,3), (2,6), (2,7)
- (3,2), (3,7)
- (4,4), (4,5), (5,4), (5,5)
- (6,2), (6,7)
- (7,2), (7,3), (7,6), (7,7)

These form a left-right and top-bottom symmetric layout: four L-shaped blocks near the corners plus a 2×2 block in the centre. That is a fixed maze of walls the agent never enters.

*Per-channel patterns.*
- **Channel 0 (agent)** has the largest weights (|w| up to about 5–7) in every open corridor cell. The network is clearly encoding the agent's position within the corridors.
- **Channel 1 (moving objects)** has substantial weights in open cells, for example:
  - (2,5): −5.209
  - (2,4): 3.745
  - (3,5): 4.201
  - (5,7): 3.248
  - (1,6), (1,7): −3.386, −3.354

  So there are things other than the agent moving through the corridors, and their positions strongly affect the policy, as enemies would.
- **Channel 2 (reward targets)** is mostly small (|w| < 0.7) but not dead, and it is spread over all open cells. One recurring unit, unit 6, has negative weights on ch2 in the top rows:
  - −1.49 at (1,1)
  - −2.36 at (1,2)
  - −1.91 at (1,3)
  - −4.88 at (2,4)

  The same unit 6 has a consistent +0.6 to +0.9 on channel 4 almost everywhere. Weak, diffuse target weights suggest many reward items scattered across the maze (pellets) rather than one decisive target.
- **Channel 3 (obstacles)** is tiny in every interior cell. The walls never change, so the network learns nothing from them; they are effectively a constant input.
- **Channel 4 (previous frame)** has moderate weights everywhere open, with a consistent sign pattern (unit 6 ≈ +0.7 to +0.9, unit 9 often around −2 to −3). This gives the network motion and direction information, chiefly about the moving objects.

*Output layer.* The biases are b3 = [−0.873, 0.703, 0.712, 0.595, −0.092]. No-op is clearly disfavoured, and the four movement actions are used. That fits a game where standing still is bad, for example because enemies close in or pellets remain uneaten.

**Reasoning**

- A fixed, symmetric internal wall layout with corridors rules out open-field games such as Snake, Catch/Breakout-style paddle games, and Frogger-like lane crossers. A fixed structure is also why the obstacle channel carries no information.
- Strong moving-object weights with motion (previous-frame) channels indicate enemies that roam the corridors and must be tracked and avoided.
- Weak, diffuse reward-target weights spread over all open cells indicate many collectible items filling the corridors, not a single goal.
- The no-op penalty in the output biases points to constant movement.

Maze plus wandering enemies plus dots everywhere is the Pac-Man pattern. A single-goal maze-navigation task would instead show strong, structured ch2 weights and probably no important ch1.

**Game:** A Pac-Man-style maze game on a fixed symmetric maze, with ghosts and pellets.

**Description:** The agent moves through the corridors of a fixed maze, eating the pellets that fill the open cells for reward. It must avoid the ghosts (moving objects) chasing it, since contact ends the episode.

**Confidence:** 65%