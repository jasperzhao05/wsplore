The policy predicts interception points rather than chasing the ball. Early in a descent it prefers the contact that preserves horizontal direction, encouraging coverage of remaining bricks. From row 4 downward, it accepts either legal catch column; this gives sticky actions room to overshoot safely.

During ascent, brick-lookahead gates identify an impending collision with the bottom brick row and pre-position the paddle for the resulting descent. Otherwise, the paddle returns toward the center. Two additional gates anticipate short descents ending at a wall.

Hidden-layer 1 computes candidate interception errors, motion direction, brick-lookahead conditions, and a special direction estimate immediately after paddle contact. Hidden-layer 2 selects the applicable left/right command. Large output margins make action sampling effectively deterministic.

```edits
# Paddle coordinates subtracted from candidate interception coordinates.
W1[540:600:6, 0:4] = [[0, 0, 0, 0], [-1, -1, -1, -1], [-2, -2, -2, -2], [-3, -3, -3, -3], [-4, -4, -4, -4], [-5, -5, -5, -5], [-6, -6, -6, -6], [-7, -7, -7, -7], [-8, -8, -8, -8], [-9, -9, -9, -9]]
W1[540:600:6, 6] = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
W1[540:600:6, 30] = [0, -40, -80, -120, -160, -200, -240, -280, -320, -360]
b1[6] = 4.5

# Descending, hypothesized horizontal direction right.
W1[3:60:6, 0] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]
W1[63:120:6, 0] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[123:180:6, 0] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[183:240:6, 0] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]
W1[243:300:6, 0] = [4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5, 7.5, 6.5, 5.5]
W1[303:360:6, 0] = [3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5, 7.5, 6.5]
W1[363:420:6, 0] = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5, 7.5]
W1[423:480:6, 0] = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9, 8.5]
W1[483:540:6, 0] = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9]

# Descending, hypothesized horizontal direction left.
W1[3:60:6, 1] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[63:120:6, 1] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[123:180:6, 1] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[183:240:6, 1] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[243:300:6, 1] = [3.5, 2.5, 1.5, 0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5]
W1[303:360:6, 1] = [2.5, 1.5, 0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
W1[363:420:6, 1] = [1.5, 0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
W1[423:480:6, 1] = [0.5, 0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
W1[483:540:6, 1] = [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]

# Ascending predictions, assuming the projected row-3 brick is present.
W1[3:240:6, 2:4] = 4.5
W1[243:300:6, 2] = [5, 6, 7, 8, 9, 9, 8, 7, 6, 5]
W1[303:360:6, 2] = [6, 7, 8, 9, 9, 8, 7, 6, 5, 4]
W1[363:420:6, 2] = [7, 8, 9, 9, 8, 7, 6, 5, 4, 3]
W1[423:480:6, 2] = [8, 9, 9, 8, 7, 6, 5, 4, 3, 2]
W1[483:540:6, 2] = [9, 9, 8, 7, 6, 5, 4, 3, 2, 1]
W1[243:300:6, 3] = [4, 3, 2, 1, 0, 0, 1, 2, 3, 4]
W1[303:360:6, 3] = [5, 4, 3, 2, 1, 0, 0, 1, 2, 3]
W1[363:420:6, 3] = [6, 5, 4, 3, 2, 1, 0, 0, 1, 2]
W1[423:480:6, 3] = [7, 6, 5, 4, 3, 2, 1, 0, 0, 1]
W1[483:540:6, 3] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]

# Additional imminent row-2 brick collisions leading to wall interceptions.
W1[201, 2] = 9
W1[219, 3] = 0

# Horizontal direction from ball minus trail, with wall-clamp correction.
b1[4] = 9
W1[9:600:60, 4] = 18
W1[15:600:60, 4] = 36
W1[21:600:60, 4] = 54
W1[27:600:60, 4] = 72
W1[33:600:60, 4] = 90
W1[39:600:60, 4] = 108
W1[45:600:60, 4] = 126
W1[51:600:60, 4] = 144
W1[57:600:60, 4] = 162
W1[10:600:60, 4] = -20
W1[16:600:60, 4] = -40
W1[22:600:60, 4] = -60
W1[28:600:60, 4] = -80
W1[34:600:60, 4] = -100
W1[40:600:60, 4] = -120
W1[46:600:60, 4] = -140
W1[52:600:60, 4] = -160
W1[58:600:60, 4] = -180

# Vertical direction: equal rows mean descending except after paddle contact.
b1[5] = 10
W1[63:120:6, 5] = 20
W1[123:180:6, 5] = 40
W1[183:240:6, 5] = 60
W1[243:300:6, 5] = 80
W1[303:360:6, 5] = 100
W1[363:420:6, 5] = 120
W1[423:480:6, 5] = 140
W1[483:540:6, 5] = 140
W1[64:120:6, 5] = -20
W1[124:180:6, 5] = -40
W1[184:240:6, 5] = -60
W1[244:300:6, 5] = -80
W1[304:360:6, 5] = -100
W1[364:420:6, 5] = -120
W1[424:480:6, 5] = -140
W1[484:540:6, 5] = -160

# Brick lookahead units: AND of a projected collision column and its brick.
b1[7:30] = -30
W1[182, 7:18:10] = 20
W1[188, 8:19:10] = 20
W1[194, 9:20:10] = 20
W1[200, 10:21:10] = 20
W1[206, 11:22:10] = 20
W1[212, 12:23:10] = 20
W1[218, 13:24:10] = 20
W1[224, 14:25:10] = 20
W1[230, 15:26:10] = 20
W1[236, 16:27:10] = 20

# Right-moving rays to row 3.
W1[243, 8] = 20
W1[249:304:54, 9] = 20
W1[255:364:54, 10] = 20
W1[261:424:54, 11] = 20
W1[267:484:54, 12] = 20
W1[537, 12] = 20
W1[273:490:54, 13] = 20
W1[477:532:54, 13] = 20
W1[279:496:54, 14] = 20
W1[417:526:54, 14] = 20
W1[285:502:54, 15] = 20
W1[357:520:54, 15] = 20
W1[291:508:54, 16] = 20
W1[297:514:54, 16] = 20

# Left-moving rays to row 3.
W1[249:514:66, 17] = 20
W1[243:508:66, 17] = 20
W1[255:520:66, 18] = 20
W1[303:502:66, 18] = 20
W1[261:526:66, 19] = 20
W1[363:496:66, 19] = 20
W1[267:532:66, 20] = 20
W1[423:490:66, 20] = 20
W1[273:538:66, 21] = 20
W1[483, 21] = 20
W1[279:478:66, 22] = 20
W1[285:418:66, 23] = 20
W1[291:358:66, 24] = 20
W1[297, 25] = 20

# Critical row-2 lookahead.
W1[201, 27] = 20
W1[146, 27] = 20
W1[219, 28] = 20
W1[152, 28] = 20

# Paddle-contact flag: current ball and trail both on row 8.
W1[483:540:6, 29] = 20
W1[484:540:6, 29] = 20

# Correct outgoing horizontal direction immediately after paddle contact.
b1[30] = 9
W1[9:600:60, 30] = 18
W1[15:600:60, 30] = 36
W1[21:600:60, 30] = 54
W1[27:600:60, 30] = 72
W1[33:600:60, 30] = 90
W1[39:600:60, 30] = 108
W1[45:600:60, 30] = 126
W1[51:600:60, 30] = 144
W1[57:600:60, 30] = 162
W1[10:600:60, 30] = 20
W1[16:600:60, 30] = 40
W1[22:600:60, 30] = 60
W1[28:600:60, 30] = 80
W1[34:600:60, 30] = 100
W1[40:600:60, 30] = 120
W1[46:600:60, 30] = 140
W1[52:600:60, 30] = 160
W1[58:600:60, 30] = 180

# Layer 2: paired right/left commands for each applicable mode.
W2[0, 0:2] = [64, -64]
W2[1, 2:4] = [64, -64]
W2[2, 4:6] = [64, -64]
W2[3, 6:8] = [64, -64]
W2[6, 8:12] = [64, -64, 64, -64]
W2[2, 12:14] = [64, -64]
W2[3, 14:16] = [64, -64]
W2[6, 16:20] = [64, -64, 64, -64]

# Direction and vertical-mode gates.
W2[4, 0:12] = [64, 64, -64, -64, 64, 64, -64, -64, 64, 64, -64, -64]
W2[30, 12:20] = [64, 64, -64, -64, 64, 64, -64, -64]
W2[5, 0:4] = 64
W2[5, 4:20] = -64
W2[29, 4:12] = -64
W2[29, 12:20] = 64

# Ordinary ascent: use predicted landing if a lookahead brick is present.
W2[7:17, 4:6] = 64
W2[17:27, 6:8] = 64
W2[27, 4:6] = 64
W2[28, 6:8] = 64

# Ordinary ascent: otherwise center.
W2[7:17, 8:10] = -64
W2[17:27, 10:12] = -64
W2[27, 8:10] = -64
W2[28, 10:12] = -64

# Immediate post-contact ascent, using corrected outgoing direction.
W2[7:17, 12:14] = 64
W2[17:27, 14:16] = 64
W2[27, 12:14] = 64
W2[28, 14:16] = 64
W2[7:17, 16:18] = -64
W2[17:27, 18:20] = -64
W2[27, 16:18] = -64
W2[28, 18:20] = -64

b2[0:4] = -168
b2[4:8] = 344
b2[8:12] = -936
b2[12:16] = 344
b2[16:20] = -936

# One applicable command raises its action above no-op.
W3[0:20:2, 3] = 40
W3[1:20:2, 1] = 40
b3[0:6] = [0, 360, -80, 360, -80, -80]
```