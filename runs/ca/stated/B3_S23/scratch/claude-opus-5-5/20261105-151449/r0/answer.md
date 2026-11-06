# HighLife (B36/S23) as an 8-channel ReLU network

**Approach:** encode the neighbour count and the cell's own state in one number, then build a function of that number that is positive only on the "alive" values.

## Step 1: Combine the cell and its neighbours into one variable

Let n be the number of live neighbours and s the state of the centre cell. Give every neighbour weight 2 and the centre weight 1, so each hidden channel sees v = 2n + s.

Since n ≤ 8, the value of v (0 to 17) determines both n and s. The alive cases map to these values:

| Case | v |
|---|---|
| s = 0, n = 3 | 6 |
| s = 0, n = 6 | 12 |
| s = 1, n = 2 | 5 |
| s = 1, n = 3 | 7 |

So the next state is alive exactly when v ∈ {5, 6, 7, 12}.

## Step 2: Build a bump function from ReLUs

Define

g(v) = R(v−4) − R(v−5) − R(v−7) + R(v−8) + R(v−11) − 2R(v−12) + R(v−13), where R = max(0, ·).

**Values of g at each integer v:**

| v | ≤4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | ≥14 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| g | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |

For v ≥ 13 the slopes cancel: 1 − 1 − 1 + 1 + 1 − 2 + 1 = 0. So g stays at 0 for all larger v.

## Step 3: Set the output threshold

Use y = g(v) − 0.5:
- On alive cases, y = 0.5 > 0.
- On every other case, y = −0.5.

This is correct on all 512 blocks, because the output depends only on (n, s), and every (n, s) pair has been checked above. Channel 7 is left unused, with all its weights at 0.

```edits
K[0][0][0] = 2
K[0][0][1] = 2
K[0][0][2] = 2
K[0][1][0] = 2
K[0][1][1] = 1
K[0][1][2] = 2
K[0][2][0] = 2
K[0][2][1] = 2
K[0][2][2] = 2
b[0] = -4
w[0] = 1
K[1][0][0] = 2
K[1][0][1] = 2
K[1][0][2] = 2
K[1][1][0] = 2
K[1][1][1] = 1
K[1][1][2] = 2
K[1][2][0] = 2
K[1][2][1] = 2
K[1][2][2] = 2
b[1] = -5
w[1] = -1
K[2][0][0] = 2
K[2][0][1] = 2
K[2][0][2] = 2
K[2][1][0] = 2
K[2][1][1] = 1
K[2][1][2] = 2
K[2][2][0] = 2
K[2][2][1] = 2
K[2][2][2] = 2
b[2] = -7
w[2] = -1
K[3][0][0] = 2
K[3][0][1] = 2
K[3][0][2] = 2
K[3][1][0] = 2
K[3][1][1] = 1
K[3][1][2] = 2
K[3][2][0] = 2
K[3][2][1] = 2
K[3][2][2] = 2
b[3] = -8
w[3] = 1
K[4][0][0] = 2
K[4][0][1] = 2
K[4][0][2] = 2
K[4][1][0] = 2
K[4][1][1] = 1
K[4][1][2] = 2
K[4][2][0] = 2
K[4][2][1] = 2
K[4][2][2] = 2
b[4] = -11
w[4] = 1
K[5][0][0] = 2
K[5][0][1] = 2
K[5][0][2] = 2
K[5][1][0] = 2
K[5][1][1] = 1
K[5][1][2] = 2
K[5][2][0] = 2
K[5][2][1] = 2
K[5][2][2] = 2
b[5] = -12
w[5] = -2
K[6][0][0] = 2
K[6][0][1] = 2
K[6][0][2] = 2
K[6][1][0] = 2
K[6][1][1] = 1
K[6][1][2] = 2
K[6][2][0] = 2
K[6][2][1] = 2
K[6][2][2] = 2
b[6] = -13
w[6] = 1
c = -0.5
```