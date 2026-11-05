# Breakout policy network: hand-set weights

## Strategy

Three facts about the game drive the design:

- **Horizontal motion is uniform.** Walls, bricks, the top wall and a straight paddle hit all leave the horizontal direction unchanged. In "unfolded" coordinates the ball's x simply moves by ±1 every frame. The real column is a reflection R of the unfolded column: R(u) = u for u in 0..9, R(u) = −1−u for u < 0, and R(u) = 19−u for u > 9. This also covers the frame where the ball sits clamped against a wall.
- **Vertical turnarounds are predictable.** At every turnaround (brick, top wall or paddle) the ball spends two frames in the same row.
- **The catch check uses the paddle position after this step's move.** When the ball is in row 8 and descending, the paddle must end up either under the ball (straight bounce, horizontal direction kept) or at the diagonal landing column (horizontal direction reversed).

## Layer 1 (each unit 0..3 = tanh(target − paddle column))

- **Paddle input:** weight −p for paddle column p, in all four units.
- **Unit 0 (descending-right) and unit 1 (descending-left):**
  - Rows 0..5: the target is R(c ± (8−r)). This is the column the ball will occupy in row 8. Catching there gives a straight bounce that keeps the horizontal direction, so the ball sweeps across the bricks.
  - Rows 6..8: the target is the midpoint of the two valid catch columns. Being on either column then gives an error of ±0.5, which falls in the dead zone, so the paddle stays put.
- **Unit 2 (ascending-right) and unit 3 (ascending-left):** the target is R(c ± S(r)). S is the number of steps until the ball is back in row 8, assuming the earliest possible bounce:
  - S = r+1 for rows 4..8 (the ball bounces off a row-3 brick).
  - S = 6 in row 3, 7 in row 2, 10 in row 1 and 9 in row 0.
  
  The target is revised automatically as the ball climbs past missing bricks. Each revision shifts the target by only about 2 columns and always adds time.
- **Unit 4 (horizontal direction):** ball-column weight 8c, trail-column weight −8c, with the ball's column 0 and column 9 offset by ±4.
  - Normal motion gives ±8.
  - A clamped wall frame (ball and trail in the same column) gives +4 at column 0 (now moving right) or −4 at column 9 (now moving left).
- **Unit 5 (vertical direction, + = descending):** ball-row weight 10r, trail-row weight −10r, bias +3.
  - Rows 1 and 8 get an extra −6. A ball that stays in row 8 has just bounced off the paddle, and one that stays in row 1 has just hit a brick from above; both are now ascending.
  - Staying in rows 0, 2, 3 or 4 means descending (top wall, a brick hit from below, or the reset).
  - Every case has |pre-activation| ≥ 3, so the unit saturates.

## Layer 2: four gated pairs (left, right)

Each pair has pre-activation ±30·h_j + 8.2·(±h4) + 8.2·(±h5) − 35.

- **Direction matches:** the pre-activation is ±30·h_j − 18.6. This threshold sits between tanh(0.5) and tanh(1), so the unit fires only when the error is at least 1.
- **Any mismatch:** the pre-activation is at most −5, so the unit stays off.

## Output

- Each even unit (left) and odd unit (right) of layer 2 feeds its action with weight 8.
- Biases: 24 for left and right, 0 for no-op, −10 for up, down and fire.
- Resulting logits: +8 for the needed move, otherwise no-op wins with −8 on the moves.

```edits
# Units 0..3: descending-right, descending-left, ascending-right, ascending-left.
W1[540:600:6, 0] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 1] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 2] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 3] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]

# Ball row 0.
W1[3:60:6, 0] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]
W1[3:60:6, 1] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[3:60:6, 2] = [9, 9, 8, 7, 6, 5, 4, 3, 2, 1]
W1[3:60:6, 3] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]

# Ball row 1.
W1[63:120:6, 0] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[63:120:6, 1] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[63:120:6, 2] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
W1[63:120:6, 3] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Ball row 2.
W1[123:180:6, 0] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[123:180:6, 1] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[123:180:6, 2] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[123:180:6, 3] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]

# Ball row 3.
W1[183:240:6, 0] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]
W1[183:240:6, 1] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[183:240:6, 2] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[183:240:6, 3] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]

# Ball row 4.
W1[243:300:6, 0] = [4, 5, 6, 7, 8, 9, 9, 8, 7, 6]
W1[243:300:6, 1] = [3, 2, 1, 0, 0, 1, 2, 3, 4, 5]
W1[243:300:6, 2] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]
W1[243:300:6, 3] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]

# Ball row 5.
W1[303:360:6, 0] = [3, 4, 5, 6, 7, 8, 9, 9, 8, 7]
W1[303:360:6, 1] = [2, 1, 0, 0, 1, 2, 3, 4, 5, 6]
W1[303:360:6, 2] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[303:360:6, 3] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]

# Ball row 6: descending targets become catch-interval midpoints.
W1[363:420:6, 0] = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5, 7.5]
W1[363:420:6, 1] = [1.5, 0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
W1[363:420:6, 2] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[363:420:6, 3] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]

# Ball row 7.
W1[423:480:6, 0] = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5]
W1[423:480:6, 1] = [0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
W1[423:480:6, 2] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]
W1[423:480:6, 3] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]

# Ball row 8.
W1[483:540:6, 0] = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9]
W1[483:540:6, 1] = [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
W1[483:540:6, 2] = [9, 9, 8, 7, 6, 5, 4, 3, 2, 1]
W1[483:540:6, 3] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]

# Terminal-row fallback.
W1[543:600:6, 0] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 1] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 2] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 3] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Unit 4: horizontal direction, including stationary wall-reflection frames.
W1[3:600:60, 4] = 4
W1[9:600:60, 4] = 8
W1[15:600:60, 4] = 16
W1[21:600:60, 4] = 24
W1[27:600:60, 4] = 32
W1[33:600:60, 4] = 40
W1[39:600:60, 4] = 48
W1[45:600:60, 4] = 56
W1[51:600:60, 4] = 64
W1[57:600:60, 4] = 68
W1[10:600:60, 4] = -8
W1[16:600:60, 4] = -16
W1[22:600:60, 4] = -24
W1[28:600:60, 4] = -32
W1[34:600:60, 4] = -40
W1[40:600:60, 4] = -48
W1[46:600:60, 4] = -56
W1[52:600:60, 4] = -64
W1[58:600:60, 4] = -72

# Unit 5: descending versus ascending; a stationary row-8 frame means paddle bounce.
b1[5] = 3
W1[63:120:6, 5] = 4
W1[123:180:6, 5] = 20
W1[183:240:6, 5] = 30
W1[243:300:6, 5] = 40
W1[303:360:6, 5] = 50
W1[363:420:6, 5] = 60
W1[423:480:6, 5] = 70
W1[483:540:6, 5] = 74
W1[543:600:6, 5] = 90
W1[64:120:6, 5] = -10
W1[124:180:6, 5] = -20
W1[184:240:6, 5] = -30
W1[244:300:6, 5] = -40
W1[304:360:6, 5] = -50
W1[364:420:6, 5] = -60
W1[424:480:6, 5] = -70
W1[484:540:6, 5] = -80
W1[544:600:6, 5] = -90

# Four context-gated pairs of left/right comparisons (even unit = left, odd unit = right).
W2[0, 0:2] = [-30, 30]
W2[1, 2:4] = [-30, 30]
W2[2, 4:6] = [-30, 30]
W2[3, 6:8] = [-30, 30]
W2[4, 0:8] = [8.2, 8.2, -8.2, -8.2, 8.2, 8.2, -8.2, -8.2]
W2[5, 0:8] = [8.2, 8.2, 8.2, 8.2, -8.2, -8.2, -8.2, -8.2]
b2[0:8] = -35

# Near-deterministic movement when needed; otherwise no-op.
W3[0:8:2, 1] = 8
W3[1:8:2, 3] = 8
b3[:] = [0, 24, -10, 24, -10, -10]
```