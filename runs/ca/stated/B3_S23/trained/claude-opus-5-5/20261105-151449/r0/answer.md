The edited network below computes HighLife (B36/S23) correctly on all 512 blocks. Rather than patch the existing weights, I rebuilt the network around a single number that each block can be summarised by.

**The key quantity**

Let n be the number of live neighbours and s the centre cell (0 or 1). Define

z = n + 0.5·s.

Each z value corresponds to exactly one (n, s) pair:

| z | Cell | Next state |
|---|---|---|
| 0, 1, 2 | dead cell, n = 0, 1, 2 | dead |
| 0.5, 1.5 | live cell, n = 0, 1 | dead |
| 2.5, 3.5 | live cell, n = 2, 3 | **alive** |
| 3 | dead cell, n = 3 | **alive** |
| 4, 5 | dead cell, n = 4, 5 | dead |
| 4.5, 5.5 | live cell, n = 4, 5 | dead |
| 6 | dead cell, n = 6 | **alive** |
| 6.5, 7.5, 8.5 | live cell, n = 6, 7, 8 | dead |
| 7, 8 | dead cell, n = 7, 8 | dead |

So the cell is alive exactly when z ∈ {2.5, 3, 3.5} or z = 6. That is two "bumps" along one variable.

**Building the bumps**

Each hidden channel computes relu(z − t). It does this with all eight neighbour weights set to 1, the centre weight set to 0.5, and bias b = −t.

The output is a piecewise-linear function of z:

g(z) = −1 + 4·r(2) − 4·r(2.5) − 4·r(3.5) + 4·r(4) + 4·r(5.5) − 8·r(6) + 4·r(6.5), where r(t) = relu(z − t).

Values of g:

| z | g(z) | Result |
|---|---|---|
| ≤ 2 | −1 | dead |
| 2.5, 3, 3.5 | +1 | alive |
| 4, 4.5, 5, 5.5 | −1 | dead |
| 6 | +1 | alive |
| ≥ 6.5 | −1 | dead (slopes sum to 4 − 4 − 4 + 4 + 4 − 8 + 4 = 0, so g stays flat) |

For example, at z = 3: −1 + 4·1 − 4·0.5 = 1. At z = 6: −1 + (16 − 14 − 10 + 8) + 4·0.5 = 1.

Every case has a margin of exactly 1, and every number involved is a multiple of 0.5. That means the arithmetic is exact, with no rounding issues.

Channels 0–6 implement the seven breakpoints. Channel 7 is switched off by setting w[7] = 0, and c = −1.

```edits
K[0][0][0] = 1
K[0][0][1] = 1
K[0][0][2] = 1
K[0][1][0] = 1
K[0][1][1] = 0.5
K[0][1][2] = 1
K[0][2][0] = 1
K[0][2][1] = 1
K[0][2][2] = 1
b[0] = -2
w[0] = 4
K[1][0][0] = 1
K[1][0][1] = 1
K[1][0][2] = 1
K[1][1][0] = 1
K[1][1][1] = 0.5
K[1][1][2] = 1
K[1][2][0] = 1
K[1][2][1] = 1
K[1][2][2] = 1
b[1] = -2.5
w[1] = -4
K[2][0][0] = 1
K[2][0][1] = 1
K[2][0][2] = 1
K[2][1][0] = 1
K[2][1][1] = 0.5
K[2][1][2] = 1
K[2][2][0] = 1
K[2][2][1] = 1
K[2][2][2] = 1
b[2] = -3.5
w[2] = -4
K[3][0][0] = 1
K[3][0][1] = 1
K[3][0][2] = 1
K[3][1][0] = 1
K[3][1][1] = 0.5
K[3][1][2] = 1
K[3][2][0] = 1
K[3][2][1] = 1
K[3][2][2] = 1
b[3] = -4
w[3] = 4
K[4][0][0] = 1
K[4][0][1] = 1
K[4][0][2] = 1
K[4][1][0] = 1
K[4][1][1] = 0.5
K[4][1][2] = 1
K[4][2][0] = 1
K[4][2][1] = 1
K[4][2][2] = 1
b[4] = -5.5
w[4] = 4
K[5][0][0] = 1
K[5][0][1] = 1
K[5][0][2] = 1
K[5][1][0] = 1
K[5][1][1] = 0.5
K[5][1][2] = 1
K[5][2][0] = 1
K[5][2][1] = 1
K[5][2][2] = 1
b[5] = -6
w[5] = -8
K[6][0][0] = 1
K[6][0][1] = 1
K[6][0][2] = 1
K[6][1][0] = 1
K[6][1][1] = 0.5
K[6][1][2] = 1
K[6][2][0] = 1
K[6][2][1] = 1
K[6][2][2] = 1
b[6] = -6.5
w[6] = 4
w[7] = 0
c = -1
```