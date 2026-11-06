CURRENT RULE: B78/S167

**How I read the current rule**

In every channel, the four cells x[0][2], x[1][2], x[2][0] and x[2][2] have the same weight. So each pre-activation depends only on three things:
- the centre,
- the four "special" neighbours x[0][0], x[0][1], x[1][0], x[2][1],
- m, the number of live cells among those four equal-weight cells.

That leaves 2 × 16 × 5 = 160 distinct cases. I evaluated all of them by hand. The pattern was consistent, with margins of about 7 or more on both sides:

- **Dead centre:** y < 0 for 0–6 live neighbours. For example, y = −105.8 at n = 0, and −8.5 to −52.5 at n = 6. y > 0 for every 7-neighbour case (+9.0 to +15.7) and at n = 8 (+22.8).
- **Live centre:** y > 0 for every 1-neighbour case (+6.7 to +8.5) and every 6- or 7-neighbour case (+7.3 to +25.3). y < 0 at n = 0 (−6.1), at n = 2–5 (−8.7 or lower) and at n = 8 (−7.0).

So the network follows the Life-like rule B78/S167.

**New rule: B678/S167**

I rebuilt the network with all eight neighbour weights set to 1, so n is the neighbour count and c is the centre.

- **Alive-gated channels.** Centre weight is +10 and bias is −10 − t. If c = 1, the channel gives relu(n − t). If c = 0, the pre-activation is at most −2, so the channel is 0.
  - Channels 0, 1, 2 use t = 0, 1, 2 with output weights 2, −4, 2. Together they give 2 at n = 1 and 0 for every other n.
  - Channels 3, 4, 5 use t = 5, 6, 7 with output weights 2, −2, −2. Together they give 2 at n = 6 and n = 7, and 0 for every other n, including n = 8.
- **Dead-gated channel 6.** Centre weight is −10 and bias is −5, giving relu(n − 5) when c = 0 and 0 when c = 1. Its output weight is 2.
- **Channel 7** is switched off with w[7] = 0.
- **Output bias** c = −1.

**Check of the new network**
- Dead centre: y = −1 for n ≤ 5, and +1, +3, +5 for n = 6, 7, 8.
- Live centre: y = +1 for n = 1, 6, 7, and −1 for all other n.

This gives exactly B678/S167, with margin 1 on every block.

```edits
K[0][0][0] = 1
K[0][0][1] = 1
K[0][0][2] = 1
K[0][1][0] = 1
K[0][1][1] = 10
K[0][1][2] = 1
K[0][2][0] = 1
K[0][2][1] = 1
K[0][2][2] = 1
b[0] = -10
w[0] = 2
K[1][0][0] = 1
K[1][0][1] = 1
K[1][0][2] = 1
K[1][1][0] = 1
K[1][1][1] = 10
K[1][1][2] = 1
K[1][2][0] = 1
K[1][2][1] = 1
K[1][2][2] = 1
b[1] = -11
w[1] = -4
K[2][0][0] = 1
K[2][0][1] = 1
K[2][0][2] = 1
K[2][1][0] = 1
K[2][1][1] = 10
K[2][1][2] = 1
K[2][2][0] = 1
K[2][2][1] = 1
K[2][2][2] = 1
b[2] = -12
w[2] = 2
K[3][0][0] = 1
K[3][0][1] = 1
K[3][0][2] = 1
K[3][1][0] = 1
K[3][1][1] = 10
K[3][1][2] = 1
K[3][2][0] = 1
K[3][2][1] = 1
K[3][2][2] = 1
b[3] = -15
w[3] = 2
K[4][0][0] = 1
K[4][0][1] = 1
K[4][0][2] = 1
K[4][1][0] = 1
K[4][1][1] = 10
K[4][1][2] = 1
K[4][2][0] = 1
K[4][2][1] = 1
K[4][2][2] = 1
b[4] = -16
w[4] = -2
K[5][0][0] = 1
K[5][0][1] = 1
K[5][0][2] = 1
K[5][1][0] = 1
K[5][1][1] = 10
K[5][1][2] = 1
K[5][2][0] = 1
K[5][2][1] = 1
K[5][2][2] = 1
b[5] = -17
w[5] = -2
K[6][0][0] = 1
K[6][0][1] = 1
K[6][0][2] = 1
K[6][1][0] = 1
K[6][1][1] = -10
K[6][1][2] = 1
K[6][2][0] = 1
K[6][2][1] = 1
K[6][2][2] = 1
b[6] = -5
w[6] = 2
w[7] = 0
c = -1
```