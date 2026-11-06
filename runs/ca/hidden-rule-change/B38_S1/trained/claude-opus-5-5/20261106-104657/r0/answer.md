# Editing the network to add birth on 6 neighbours

**Approach.** I worked out which rule the current network computes, from the weights alone. Then I rebuilt the network with clean, uniform weights that implement that rule plus the new birth condition.

## 1. The current rule

Channels 3, 4, 5 and 7 are near-uniform neighbour counters with different thresholds. Channels 0, 1, 2 and 6 are small corrections for the uneven weights at positions (0,2), (1,0) and (2,0). I evaluated y by hand, mostly on typical blocks, and spot-checked blocks that involve those three positions.

**Dead centre:**

| Live neighbours n | y | Result |
|---|---|---|
| 0, 1, 2 | about −10 | dead |
| 3 | about +8 to +10 | alive |
| 4 | about −10 | dead |
| 5 | about −20 | dead |
| 6 | about −12 | dead |
| 7 | about −7 (all 8 blocks checked) | dead |
| 8 | exactly about +5.0 | alive |

**Live centre:**

| Live neighbours n | y | Result |
|---|---|---|
| 0 | −5.8 | dead |
| 1 | +7.6 to +10 (all positions checked) | alive |
| 2 to 8 | −8.6 down to −38 | dead |

So the current rule is **B38/S1**: a dead cell is born with 3 or 8 live neighbours, and a live cell survives with exactly 1. The new rule is **B368/S1**.

## 2. The rebuilt network

All eight neighbour weights are set to 1, so each channel sees n plus a centre term. Only 5 channels are needed; the other 3 have w = 0.

| Channel | Pre-activation | w | Role |
|---|---|---|---|
| 0 | n + 2s + 0.5 (always active) | +2 | rising slope |
| 1 | n + 2s − 3 (starts at n=3 if dead, n=1 if alive) | −4 | first fall |
| 2 | n − 10s − 5 | +6 | rise from n=5, dead centre only |
| 3 | n − 10s − 6 | −6 | fall from n=6, dead centre only |
| 4 | n − 10s − 7 | +4 | rise from n=7, dead centre only |

The output bias is c = −6.

**Check, dead centre (s = 0).**
y = 2n − 5 − 4·relu(n−3) + 6·relu(n−5) − 6·relu(n−6) + 4·relu(n−7)

| n | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| y | −5 | −3 | −1 | **+1** | −1 | −3 | **+1** | −1 | **+1** |

This gives births at n = 3, 6 and 8, as required.

**Check, live centre (s = 1).** Channels 2 to 4 are always off, because their pre-activation is at most −7.
y = 2n − 1 − 4·relu(n−1)

| n | 0 | 1 | 2 | 3 | … | 8 |
|---|---|---|---|---|---|---|
| y | −1 | **+1** | −1 | −3 | … | −13 |

This gives survival only at n = 1, unchanged from the current rule.

All weights are exact decimals, so every one of the 512 blocks gives y = ±1 or further from 0. The output therefore never sits on the y = 0 boundary.

```edits
K[0][0][0] = 1
K[0][0][1] = 1
K[0][0][2] = 1
K[0][1][0] = 1
K[0][1][1] = 2
K[0][1][2] = 1
K[0][2][0] = 1
K[0][2][1] = 1
K[0][2][2] = 1
b[0] = 0.5
w[0] = 2
K[1][0][0] = 1
K[1][0][1] = 1
K[1][0][2] = 1
K[1][1][0] = 1
K[1][1][1] = 2
K[1][1][2] = 1
K[1][2][0] = 1
K[1][2][1] = 1
K[1][2][2] = 1
b[1] = -3
w[1] = -4
K[2][0][0] = 1
K[2][0][1] = 1
K[2][0][2] = 1
K[2][1][0] = 1
K[2][1][1] = -10
K[2][1][2] = 1
K[2][2][0] = 1
K[2][2][1] = 1
K[2][2][2] = 1
b[2] = -5
w[2] = 6
K[3][0][0] = 1
K[3][0][1] = 1
K[3][0][2] = 1
K[3][1][0] = 1
K[3][1][1] = -10
K[3][1][2] = 1
K[3][2][0] = 1
K[3][2][1] = 1
K[3][2][2] = 1
b[3] = -6
w[3] = -6
K[4][0][0] = 1
K[4][0][1] = 1
K[4][0][2] = 1
K[4][1][0] = 1
K[4][1][1] = -10
K[4][1][2] = 1
K[4][2][0] = 1
K[4][2][1] = 1
K[4][2][2] = 1
b[4] = -7
w[4] = 4
w[5] = 0
w[6] = 0
w[7] = 0
c = -6
```