"""Where each written network agrees with Astra's, and where it does not.
  Astra's states      19,783 states from 30 episodes of Astra's own play (every 10th step), as in design.py,
                      split into landing states (ball falling, in rows 6-8) and the rest
  own states          every 5th state of the network's own play (10 episodes, up to 3,000 steps each)
  before a loss       the last 5 states before each lost ball in the network's own play

  uv run agreement.py                    # writes runs/design/agreement.json
"""
import glob, json, os
import numpy as np
import design as t

exp5 = t.exp5
HERE = os.path.dirname(os.path.abspath(__file__))
TURING = os.path.join(t.HARNESS, "runs", "exp5")


def moves(net, states):
    return np.array((0, 1, 3))[t.effects(net, states).argmax(1)]


def landing(states):
    g = states.reshape(-1, 10, 10, 6)
    ball_row = np.where(g[:, :, :, 3].any(2), np.arange(10), -1).max(1)
    trail_row = np.where(g[:, :, :, 4].any(2), np.arange(10), -1).max(1)
    return (ball_row >= 6) & (ball_row <= 8) & (trail_row >= 0) & (trail_row < ball_row)


def sample(net, x, rng):
    """The harness's action choice: sample from the softmax over all six actions."""
    h = np.tanh(x @ net["W1"] + net["b1"])
    h = np.tanh(h @ net["W2"] + net["b2"])
    z = (h @ net["W3"] + net["b3"]).astype(np.float64)
    q = np.cumsum(np.exp(z - z.max()))
    return min(int(np.searchsorted(q, rng.random() * q[-1], side="right")), 5)


def own_play(net, episodes=10, cap=3000, every=5, seed=2):
    seen, before = [], []
    for i in range(episodes):
        env = exp5.make_env(t.GAME)
        m = t.channel_map(env)
        env.seed(seed * 1_000_003 + i)
        env.reset()
        rng = np.random.default_rng([seed, i, 1])
        recent, done, steps = [], False, 0
        while not done and steps < cap:
            x = t.observe(env, m)
            if steps % every == 0:
                seen.append(x)
            recent = (recent + [x])[-5:]
            _, done = env.act(sample(net, x, rng))
            steps += 1
        if done:
            before += recent
    return np.array(seen, np.float32), np.array(before, np.float32).reshape(-1, 600)


def networks():
    for f in sorted(glob.glob(os.path.join(HERE, "runs", "design", "L*", "*", "*", "breakout_r*", "run.json"))):
        yield f
    for f in sorted(glob.glob(os.path.join(TURING, "claude-*", "*", "breakout_r*", "run.json"))):
        yield f


def main():
    astra = exp5.load_npz(t.ASTRA)
    ref, ref_moves = t.reference_states(t.network_policy(astra))
    land = landing(ref)
    rows = []
    for f in networks():
        r = json.load(open(f))
        if r["error"] or not r["edits"]["applied"]:
            continue
        net = exp5.load_npz(f.replace("run.json", "net.npz"))
        mine = moves(net, ref)
        same = mine == ref_moves
        seen, before = own_play(net)
        row = {"model": r["model"], "level": r.get("level", "L0"), "run": os.path.basename(os.path.dirname(f)),
               "score": round(r["eval"]["mean"], 1),
               "astra_states": round(float(same.mean()), 3),
               "landing": round(float(same[land].mean()), 3),
               "other": round(float(same[~land].mean()), 3),
               "own_states": round(float((moves(net, seen) == moves(astra, seen)).mean()), 3),
               "before_loss": round(float((moves(net, before) == moves(astra, before)).mean()), 3) if len(before) else None,
               "losses_in_10": len(before) // 5 if len(before) else 0}
        rows.append(row)
        print(f"{row['model']:20s} {row['level']} {row['run'][-2:]}  score {row['score']:6.1f}  Astra's states "
              f"{row['astra_states']:.0%} (landing {row['landing']:.0%}, other {row['other']:.0%})  own states "
              f"{row['own_states']:.0%}  before a loss {'-' if row['before_loss'] is None else f'{row['before_loss']:.0%}'} "
              f"({row['losses_in_10']} lost balls in 10 episodes)", flush=True)
    print(f"landing states: {int(land.sum())} of {len(land)}")
    json.dump(rows, open(os.path.join(HERE, "runs", "design", "agreement.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
