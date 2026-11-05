# Design Description

## Strategy
The network predicts where the ball will land at the bottom row (accounting for wall reflections) and computes the error between that target column and the paddle's current position. When the error is positive (target to the right), it moves right; when negative, it moves left; when near zero, it stays put.

## Hidden Units (Layer 1)
- **Units 0-3**: Compute landing position errors for each of the 4 ball directions (descending-right, descending-left, ascending-right, ascending-left). Each sums the predicted landing column from the ball position minus the paddle column.
- **Unit 4**: Horizontal direction detector. Positive when ball moves right (ball_col > trail_col), negative when moving left.
- **Unit 5**: Vertical direction detector. Positive when descending (trail above ball), negative when ascending.

## Layer 2
Gates the four error signals based on detected direction, producing left/right decision pairs for each context.

## Output Layer
Converts gated errors to action logits: positive error → move right, negative error → move left, with strong bias against useless actions (up, down, fire).

```edits
# Paddle position (subtract column from all error units)
W1[540:600:6, 0] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 1] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 2] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 3] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]

# Ball row 0 landing columns
W1[3:60:6, 0] = [9, 9, 8, 7, 6, 5, 4, 3, 2, 1]
W1[3:60:6, 1] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
W1[3:60:6, 2] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 1]
W1[3:60:6, 3] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Ball row 1
W1[63:120:6, 0] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]
W1[63:120:6, 1] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[63:120:6, 2] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
W1[63:120:6, 3] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 1]

# Ball row 2
W1[123:180:6, 0] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[123:180:6, 1] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[123:180:6, 2] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[123:180:6, 3] = [8, 9, 8, 7, 6, 5, 4, 3, 2, 2]

# Ball row 3
W1[183:240:6, 0] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[183:240:6, 1] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[183:240:6, 2] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[183:240:6, 3] = [7, 8, 9, 8, 7, 6, 5, 4, 3, 3]

# Ball row 4
W1[243:300:6, 0] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]
W1[243:300:6, 1] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[243:300:6, 2] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[243:300:6, 3] = [6, 7, 8, 9, 8, 7, 6, 5, 4, 4]

# Ball row 5
W1[303:360:6, 0] = [4, 5, 6, 7, 8, 9, 9, 8, 7, 6]
W1[303:360:6, 1] = [3, 2, 1, 0, 0, 1, 2, 3, 4, 5]
W1[303:360:6, 2] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[303:360:6, 3] = [5, 6, 7, 8, 9, 8, 7, 6, 5, 5]

# Ball row 6 (catch-interval midpoints)
W1[363:420:6, 0] = [3, 4, 5, 6, 7, 8, 9, 9, 8, 7]
W1[363:420:6, 1] = [2, 1, 0, 0, 1, 2, 3, 4, 5, 6]
W1[363:420:6, 2] = [3, 2, 1, 0, 0, 1, 2, 3, 4, 5]
W1[363:420:6, 3] = [4, 5, 6, 7, 8, 9, 8, 7, 6, 6]

# Ball row 7
W1[423:480:6, 0] = [2, 3, 4, 5, 6, 7, 8, 9, 9, 8]
W1[423:480:6, 1] = [1, 0, 0, 1, 2, 3, 4, 5, 6, 7]
W1[423:480:6, 2] = [2, 1, 0, 0, 1, 2, 3, 4, 5, 6]
W1[423:480:6, 3] = [3, 4, 5, 6, 7, 8, 9, 8, 7, 7]

# Ball row 8
W1[483:540:6, 0] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 9]
W1[483:540:6, 1] = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8]
W1[483:540:6, 2] = [1, 0, 0, 1, 2, 3, 4, 5, 6, 7]
W1[483:540:6, 3] = [2, 3, 4, 5, 6, 7, 8, 9, 8, 8]

# Ball row 9 (terminal fallback)
W1[543:600:6, 0] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 1] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 2] = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8]
W1[543:600:6, 3] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 9]

# Unit 4: horizontal direction (ball_col - trail_col, positive=right)
W1[3:600:60, 4] = 0.5
W1[9:600:60, 4] = 1
W1[15:600:60, 4] = 2
W1[21:600:60, 4] = 3
W1[27:600:60, 4] = 4
W1[33:600:60, 4] = 5
W1[39:600:60, 4] = 6
W1[45:600:60, 4] = 7
W1[51:600:60, 4] = 8
W1[57:600:60, 4] = 8.5
W1[10:600:60, 4] = -1
W1[16:600:60, 4] = -2
W1[22:600:60, 4] = -3
W1[28:600:60, 4] = -4
W1[34:600:60, 4] = -5
W1[40:600:60, 4] = -6
W1[46:600:60, 4] = -7
W1[52:600:60, 4] = -8
W1[58:600:60, 4] = -9

# Unit 5: vertical direction (positive=descending)
b1[5] = 0
W1[63:120:6, 5] = 1
W1[123:180:6, 5] = 2
W1[183:240:6, 5] = 3
W1[243:300:6, 5] = 4
W1[303:360:6, 5] = 5
W1[363:420:6, 5] = 6
W1[423:480:6, 5] = 7
W1[483:540:6, 5] = 8
W1[543:600:6, 5] = 9
W1[64:120:6, 5] = -1
W1[124:180:6, 5] = -2
W1[184:240:6, 5] = -3
W1[244:300:6, 5] = -4
W1[304:360:6, 5] = -5
W1[364:420:6, 5] = -6
W1[424:480:6, 5] = -7
W1[484:540:6, 5] = -8
W1[544:600:6, 5] = -9

# Layer 2: context-gated left/right pairs
W2[0, 0:2] = [2, -2]
W2[1, 2:4] = [2, -2]
W2[2, 4:6] = [2, -2]
W2[3, 6:8] = [2, -2]
W2[4, 0:8] = [1, 1, -1, -1, 1, 1, -1, -1]
W2[5, 0:8] = [1, 1, 1, 1, -1, -1, -1, -1]
b2[0:8] = -0.5

# Output layer: movement decisions
W3[0:8:2, 1] = 4
W3[1:8:2, 3] = 4
b3[:] = [1, 0, -5, 0, -5, -5]
```