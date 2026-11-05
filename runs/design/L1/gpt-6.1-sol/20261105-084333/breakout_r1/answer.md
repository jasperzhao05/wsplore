I use a predictive interception policy:

- **Hidden units 0–3:** landing errors for descending-left, descending-right, ascending-left, and ascending-right. Predictions include the walls’ repeated-edge reflections. Ascending predictions assume the earliest possible brick bounce and are revised each frame.
- **Hidden units 4–5:** horizontal and vertical direction estimates from the ball and trail, with position-dependent tie-breaks for zero displacement.
- Early positioning targets the catch column that preserves horizontal direction. In rows 6–8, the target becomes the midpoint of both valid catch columns, so either is accepted.
- **Second-layer units 0–7:** direction-gated left/right tests. Their deadband selects no-op when correctly positioned. Large output margins make sampling nearly deterministic; sticky actions remain environmental.

All unedited parameters remain zero.

```edits
# Paddle position subtracted from all four landing predictions.
W1[540:600:6, 0] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 1] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 2] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 3] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]

# Ball row 0: descending-left/right, ascending-left/right.
W1[3:60:6, 0] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[3:60:6, 1] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]
W1[3:60:6, 2] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
W1[3:60:6, 3] = [9, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# Ball row 1.
W1[63:120:6, 0] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[63:120:6, 1] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[63:120:6, 2] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
W1[63:120:6, 3] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Ball row 2.
W1[123:180:6, 0] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[123:180:6, 1] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[123:180:6, 2] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[123:180:6, 3] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]

# Ball row 3.
W1[183:240:6, 0] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[183:240:6, 1] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]
W1[183:240:6, 2] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[183:240:6, 3] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]

# Ball row 4.
W1[243:300:6, 0] = [3, 2, 1, 0, 0, 1, 2, 3, 4, 5]
W1[243:300:6, 1] = [4, 5, 6, 7, 8, 9, 9, 8, 7, 6]
W1[243:300:6, 2] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[243:300:6, 3] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]

# Ball row 5.
W1[303:360:6, 0] = [2, 1, 0, 0, 1, 2, 3, 4, 5, 6]
W1[303:360:6, 1] = [3, 4, 5, 6, 7, 8, 9, 9, 8, 7]
W1[303:360:6, 2] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[303:360:6, 3] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]

# Ball row 6: descending targets accept either catch column.
W1[363:420:6, 0] = [1.5, 0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
W1[363:420:6, 1] = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5, 7.5]
W1[363:420:6, 2] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[363:420:6, 3] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]

# Ball row 7.
W1[423:480:6, 0] = [0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
W1[423:480:6, 1] = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5]
W1[423:480:6, 2] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[423:480:6, 3] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]

# Ball row 8.
W1[483:540:6, 0] = [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
W1[483:540:6, 1] = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9]
W1[483:540:6, 2] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
W1[483:540:6, 3] = [9, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# Terminal-row completion.
W1[543:600:6, 0] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 1] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
W1[543:600:6, 2] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
W1[543:600:6, 3] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Horizontal direction: positive means right.
# Ball-column terms include wall-reflection tie-breaks.
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

# Trail-column terms.
W1[10:600:60, 4] = -8
W1[16:600:60, 4] = -16
W1[22:600:60, 4] = -24
W1[28:600:60, 4] = -32
W1[34:600:60, 4] = -40
W1[40:600:60, 4] = -48
W1[46:600:60, 4] = -56
W1[52:600:60, 4] = -64
W1[58:600:60, 4] = -72

# Vertical direction: positive means descending.
# Equal-row observations favor down near bricks and up near the paddle.
W1[3:60:6, 5] = 4
W1[63:120:6, 5] = 12
W1[123:180:6, 5] = 20
W1[183:240:6, 5] = 28
W1[243:300:6, 5] = 36
W1[303:360:6, 5] = 36
W1[363:420:6, 5] = 44
W1[423:480:6, 5] = 52
W1[483:540:6, 5] = 60
W1[543:600:6, 5] = 68

# Trail-row terms.
W1[64:120:6, 5] = -8
W1[124:180:6, 5] = -16
W1[184:240:6, 5] = -24
W1[244:300:6, 5] = -32
W1[304:360:6, 5] = -40
W1[364:420:6, 5] = -48
W1[424:480:6, 5] = -56
W1[484:540:6, 5] = -64
W1[544:600:6, 5] = -72

# Second layer: paired left/right gates for DL, DR, UL, UR.
W2[0:6, 0:8] = [
[-32, 32, 0, 0, 0, 0, 0, 0],
[0, 0, -32, 32, 0, 0, 0, 0],
[0, 0, 0, 0, -32, 32, 0, 0],
[0, 0, 0, 0, 0, 0, -32, 32],
[-32, -32, 32, 32, -32, -32, 32, 32],
[32, 32, 32, 32, -32, -32, -32, -32]
]
b2[0:8] = -84

# Inactive gates contribute -40 each; one active gate raises its action by 80.
W3[0:8:2, 1] = 40
W3[1:8:2, 3] = 40
b3[0:6] = [40, 160, -40, 160, -40, -40]
```