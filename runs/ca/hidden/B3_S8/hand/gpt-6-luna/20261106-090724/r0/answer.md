Let \(q\) be the sum of the eight neighbours minus \(9\) times the centre cell. The unchanged channels contribute their original output if channel 3’s weight is raised to \(1\), since it then alone replaces the original combined contribution of channels 0–3.

Use channels 0–2 to add
\[
(q-5)_+ - 2(q-6)_+ + (q-7)_+.
\]
For integer \(q\), this is \(1\) when \(q=6\) and \(0\) otherwise. A dead centre with six live neighbours has \(q=6\), so its output rises from \(-0.5\) to \(0.5\). For a live centre, \(q\le -1\), so the added term is zero. All other blocks retain their original output.

```edits
b[0] = -5
b[1] = -6
b[2] = -7
w[0] = 1
w[1] = -2
w[2] = 1
w[3] = 1
```