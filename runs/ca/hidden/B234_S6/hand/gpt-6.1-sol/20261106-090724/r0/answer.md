Let \(n\) be the number of live neighbours. The current network makes dead cells alive for \(n\in\{2,3,4\}\), and keeps live cells alive only for \(n=6\).

Change the first four channels so that, for a dead centre, the score becomes
\[
y=-0.5+(n-1)_+-4(n-4)_++4(n-5)_+-4(n-6)_+,
\]
where \((t)_+=\max(0,t)\). The last four channels are inactive for a dead centre.

The resulting scores are:

| \(n\) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| \(y\) | −0.5 | −0.5 | 0.5 | 1.5 | 2.5 | −0.5 | 0.5 | −2.5 | −5.5 |

Thus the only changed next state is for a dead centre with six live neighbours. For a live centre, the first four channels remain inactive, so every live-centre case is unchanged.

```edits
b[1] = -4
w[1] = -4
b[2] = -5
w[2] = 4
b[3] = -6
w[3] = -4
```