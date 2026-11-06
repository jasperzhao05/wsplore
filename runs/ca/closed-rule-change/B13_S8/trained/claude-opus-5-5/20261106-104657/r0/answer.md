CURRENT RULE: B13/S8

The current network follows B13/S8. Adding birth on 6 gives **B136/S8**. Rather than patch the old weights, I rebuilt the network as a clean count-based one. That is allowed, since any weight may be set to any value.

**How I identified the current rule.** I worked through all 512 blocks by hand, grouped by the cell's state and its live-neighbour count n. Where cases were close, I bounded every channel rather than computing each block.

- **Dead centre:**
  - All 8 single-neighbour blocks give alive, with y between 5.3 and 13.8.
  - All 56 three-neighbour blocks give alive, with y of at least about 5.3.
  - n = 0, 2, 4, 5, 6, 7 and 8 all give dead, each by a margin of at least about 5.7.
- **Live centre:**
  - Channels 2 and 7 add large negative terms whenever n ≤ 7, so every such block is dead (y ≤ −8.2).
  - With all 8 neighbours alive, every channel except channel 5 is zero. Channel 5 is only 0.001, so y = 6.865 and the cell survives.
- All margins are well away from 0, so the rule is exactly B13/S8.

**The new network.** Let n be the number of live neighbours and C the centre cell.

- **Channels 0–5:** every neighbour weight is 1 and the centre weight is −10. Each computes h = relu(n − t − 10C), with t = 0, 1, 2, 3, 4.5 and 6.
  - When C = 1, n − 10 ≤ −2, so all six are zero.
  - When C = 0 they give y = −1 + 2n − 4·relu(n−1) + 4·relu(n−2) − 4·relu(n−3) + 4·relu(n−4.5) − 4·relu(n−6).
  - For n = 0 to 8 this equals −1, 1, −1, 1, −1, −1, 1, −1, −1, so a dead cell is born exactly at n = 1, 3 and 6.
- **Channel 6:** h = relu(n + C − 8.5) with output weight 4. It is non-zero only when C = 1 and n = 8, where it equals 0.5.
  - For a live centre, y = −1 + 4·h6.
  - That is +1 at n = 8 and −1 otherwise, so the cell survives only with 8 neighbours.
- **Channel 7:** switched off by setting its output weight to 0.

This gives exactly B136/S8 on all 512 blocks.

```edits
K[0][0][0] = 1
K[0][0][1] = 1
K[0][0][2] = 1
K[0][1][0] = 1
K[0][1][1] = -10
K[0][1][2] = 1
K[0][2][0] = 1
K[0][2][1] = 1
K[0][2][2] = 1
b[0] = 0
w[0] = 2
K[1][0][0] = 1
K[1][0][1] = 1
K[1][0][2] = 1
K[1][1][0] = 1
K[1][1][1] = -10
K[1][1][2] = 1
K[1][2][0] = 1
K[1][2][1] = 1
K[1][2][2] = 1
b[1] = -1
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
b[2] = -2
w[2] = 4
K[3][0][0] = 1
K[3][0][1] = 1
K[3][0][2] = 1
K[3][1][0] = 1
K[3][1][1] = -10
K[3][1][2] = 1
K[3][2][0] = 1
K[3][2][1] = 1
K[3][2][2] = 1
b[3] = -3
w[3] = -4
K[4][0][0] = 1
K[4][0][1] = 1
K[4][0][2] = 1
K[4][1][0] = 1
K[4][1][1] = -10
K[4][1][2] = 1
K[4][2][0] = 1
K[4][2][1] = 1
K[4][2][2] = 1
b[4] = -4.5
w[4] = 4
K[5][0][0] = 1
K[5][0][1] = 1
K[5][0][2] = 1
K[5][1][0] = 1
K[5][1][1] = -10
K[5][1][2] = 1
K[5][2][0] = 1
K[5][2][1] = 1
K[5][2][2] = 1
b[5] = -6
w[5] = -4
K[6][0][0] = 1
K[6][0][1] = 1
K[6][0][2] = 1
K[6][1][0] = 1
K[6][1][1] = 1
K[6][1][2] = 1
K[6][2][0] = 1
K[6][2][1] = 1
K[6][2][2] = 1
b[6] = -8.5
w[6] = 4
b[7] = 0
w[7] = 0
c = -1
```