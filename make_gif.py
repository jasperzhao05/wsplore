"""Render the README animation: three models, each given Astra's design paragraph (L1), play the same Breakout episode.
Each panel shows whether the network's most likely move matches what Astra's network would do in the same state.

  uv run make_gif.py                     # writes assets/l1_three_models.gif
"""
import glob, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import design as t

exp5 = t.exp5
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs", "design", "L1")
PANELS = [
    ("GPT-6.1 Sol", "gpt-6.1-sol", "r0", "503"),
    ("GPT-6 Luna", "gpt-6-luna", "r1", "7"),
    ("Claude Opus 5.5", "claude-opus-5-5", "r0", "442"),
]
EPISODE, SEED, STEP_MS, HOLD_MS, S = 2, 0, 60, 3000, 2

BG, PANEL, BOARD, GRID = "#100d1f", "#1c1733", "#1a1530", "#272043"
FG, MUTED, OK, BAD = "#ece9f3", "#a39db3", "#7fc4a4", "#e8675e"
PADDLE, BALL, TRAIL, BRICK = "#d07e93", "#c1caf3", "#1f6642", "#a07949"
MOVE = {0: "stay", 1: "left", 3: "right"}

CELL, PAD, GAP, OUTER, HEAD, FOOT, TOP = 28, 16, 18, 24, 58, 96, 44
BOARD_W = 10 * CELL
PANEL_W = BOARD_W + 2 * PAD
W = 3 * PANEL_W + 2 * GAP + 2 * OUTER
H = TOP + HEAD + BOARD_W + FOOT + OUTER + 8


def font(size, weight="Regular", mono=False):
    f = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf" if mono else "/System/Library/Fonts/SFNS.ttf", size * S)
    try:
        f.set_variation_by_name(weight)
    except (OSError, ValueError):
        pass
    return f


F_TITLE, F_SUB, F_SMALL = font(18, "Semibold"), font(13, mono=True), font(13)
F_BIG, F_TOP = font(15, "Semibold"), font(13)


def play(net, astra, steps):
    """The harness's way of playing: softmax sampling, sticky actions, per-episode seeds."""
    env = exp5.make_env("breakout")
    m = t.channel_map(env)
    env.seed(SEED * 1_000_003 + EPISODE)
    env.reset()
    rng = np.random.default_rng([SEED, EPISODE, 1])
    frames, score, done = [], 0, False
    while not done and len(frames) < steps:
        x = t.observe(env, m)
        g = x.reshape(10, 10, 6)
        mine = (0, 1, 3)[int(t.effects(net, x[None])[0].argmax())]
        theirs = (0, 1, 3)[int(t.effects(astra, x[None])[0].argmax())]
        h = np.tanh(x @ net["W1"] + net["b1"])
        h = np.tanh(h @ net["W2"] + net["b2"])
        z = (h @ net["W3"] + net["b3"]).astype(np.float64)
        q = np.cumsum(np.exp(z - z.max()))
        a = min(int(np.searchsorted(q, rng.random() * q[-1], side="right")), 5)
        frames.append({"grid": g.copy(), "mine": mine, "astra": theirs, "score": score})
        r, done = env.act(a)
        score += r
    return frames, done, score


def box(d, xy, fill, r=0):
    d.rounded_rectangle([v * S for v in xy], radius=r * S, fill=fill)


def text(d, xy, s, f, fill, anchor="la"):
    d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor=anchor)


def draw_board(d, x0, y0, g, lost):
    box(d, (x0, y0, x0 + BOARD_W, y0 + BOARD_W), BOARD, 6)
    for k in range(1, 10):
        d.line([((x0 + k * CELL) * S, y0 * S), ((x0 + k * CELL) * S, (y0 + BOARD_W) * S)], fill=GRID, width=S)
        d.line([(x0 * S, (y0 + k * CELL) * S), ((x0 + BOARD_W) * S, (y0 + k * CELL) * S)], fill=GRID, width=S)

    def cell(r, c, color, inset):
        box(d, (x0 + c * CELL + inset, y0 + r * CELL + inset, x0 + (c + 1) * CELL - inset, y0 + (r + 1) * CELL - inset), color, 2)

    for r, c in np.argwhere(g[:, :, 2]):
        cell(r, c, BRICK, 2)
    for r, c in np.argwhere(g[:, :, 4]):
        cell(r, c, TRAIL, 4)
    for r, c in np.argwhere(g[:, :, 3]):
        cell(r, c, BALL, 4)
    for c in np.flatnonzero(g[9, :, 0]):
        cell(9, c, PADDLE, 2)
    if lost:
        overlay = Image.new("RGBA", (BOARD_W * S, BOARD_W * S), (16, 13, 31, 170))
        return overlay
    return None


def render(step, runs):
    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)
    text(d, (OUTER, 18), "MinAtar Breakout · same episode · each network written in one reply from Astra's 60-word design",
         F_TOP, MUTED)
    text(d, (W - OUTER, 18), f"step {min(step, max(len(r['frames']) for r in runs)):>3}", F_SUB, MUTED, "ra")
    for k, run in enumerate(runs):
        x0 = OUTER + k * (PANEL_W + GAP)
        y0 = TOP
        frames, n = run["frames"], len(run["frames"])
        lost = run["ended"] and step >= n
        f = frames[min(step, n - 1)]
        seen = frames[:min(step + 1, n)]
        agree = sum(fr["mine"] == fr["astra"] for fr in seen)
        mismatch = not lost and f["mine"] != f["astra"]
        box(d, (x0, y0, x0 + PANEL_W, y0 + HEAD + BOARD_W + FOOT), PANEL, 10)
        text(d, (x0 + PAD, y0 + 14), run["name"], F_TITLE, FG)
        text(d, (x0 + PAD, y0 + 38), f"1,000-episode mean {run['mean']}", F_SUB, MUTED)
        bx, by = x0 + PAD, y0 + HEAD
        overlay = draw_board(d, bx, by, f["grid"], lost)
        if mismatch:
            d.rounded_rectangle([(bx - 3) * S, (by - 3) * S, (bx + BOARD_W + 3) * S, (by + BOARD_W + 3) * S],
                                radius=8 * S, outline=BAD, width=3 * S)
        if overlay is not None:
            img.paste(Image.alpha_composite(img.crop((bx * S, by * S, (bx + BOARD_W) * S, (by + BOARD_W) * S))
                                            .convert("RGBA"), overlay).convert("RGB"), (bx * S, by * S))
            d = ImageDraw.Draw(img)
            text(d, (bx + BOARD_W / 2, by + BOARD_W / 2 - 12), "BALL LOST", font(22, "Bold"), BAD, "mm")
            text(d, (bx + BOARD_W / 2, by + BOARD_W / 2 + 16), f"at step {n}", F_SUB, FG, "mm")
        fy = by + BOARD_W + 14
        score = run["final"] if lost else f["score"]
        text(d, (x0 + PAD, fy), "Matches Astra", F_SMALL, MUTED)
        text(d, (x0 + PANEL_W - PAD, fy), f"{agree} / {len(seen)} steps", F_BIG, OK if agree == len(seen) else BAD, "ra")
        text(d, (x0 + PAD, fy + 26), "Score", F_SMALL, MUTED)
        text(d, (x0 + PANEL_W - PAD, fy + 26), f"{int(score)}", F_BIG, FG, "ra")
        if lost:
            text(d, (x0 + PAD, fy + 52), "game over", F_SMALL, BAD)
        else:
            color = BAD if mismatch else MUTED
            text(d, (x0 + PAD, fy + 52), f"picks {MOVE[f['mine']]}", F_SMALL, color)
            text(d, (x0 + PANEL_W - PAD, fy + 52), f"Astra picks {MOVE[f['astra']]}", F_SMALL, color, "ra")
    return img


def main():
    astra = exp5.load_npz(t.ASTRA)
    runs = []
    for name, model, rep, mean in PANELS:
        path = sorted(glob.glob(os.path.join(RUNS, model, "*", f"breakout_{rep}", "net.npz")))[-1]
        frames, ended, final = play(exp5.load_npz(path), astra, 72)
        runs.append({"name": name, "mean": mean, "frames": frames, "ended": ended, "final": final})
    last = next(len(r["frames"]) for r in runs if r["ended"])
    images = [render(s, runs) for s in range(last + 1)]
    sample = images[::6] + [images[-1]]
    sheet = Image.new("RGB", (W * S, H * S * len(sample)))
    for k, im in enumerate(sample):
        sheet.paste(im, (0, k * H * S))
    pal = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    frames = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in images]
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    out = os.path.join(HERE, "assets", "l1_three_models.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=[STEP_MS] * (len(frames) - 1) + [HOLD_MS],
                   optimize=False)    # no loop count: plays once and stays on the last frame
    print(f"{out}: {len(frames)} frames, {W * S}x{H * S}, {(STEP_MS * (len(frames) - 1) + HOLD_MS) / 1000:.1f}s, "
          f"{os.path.getsize(out) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
