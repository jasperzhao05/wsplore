"""The README figures.
  footprint   the tables the footprint prompts show, drawn as maps (Exp 1: the five channels of each game's network,
              plus Breakout's shuffled control; Exp 2: each shape, real and shuffled)
  gif         three models, each given Astra's design paragraph (L1), play the same Breakout episode; each panel
              shows whether the network's most likely move matches what Astra's network would do in that state
  ca          the cellular-automaton edits of round 3: the new rule and each model's edited network, run from the
              same seed, cells unlike the new rule in red (B24/S5 as a GIF, the last step of B128/S0 as a PNG)

  uv run figures.py                      # writes everything in assets/
  uv run figures.py footprint
"""
import argparse, glob, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import design as t
import footprint as fp
import ca_edit as ca

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


GAMES = {"breakout": "Breakout", "freeway": "Freeway", "pacman": "Pac-Man", "pong": "Pong"}
SHAPES = ("circle", "triangle", "square")


def maps(exp, truth, control=None):
    net_id = next(i for i, name in fp.harness.networks(exp).items() if name == truth)
    return fp.footprint(exp, fp.weights_text(exp, net_id, control))


def footprint_figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    sf = "/System/Library/Fonts/SFNS.ttf"
    font_manager.fontManager.addfont(sf)
    plt.rcParams.update({"font.family": font_manager.FontProperties(fname=sf).get_name(), "text.color": FG,
                         "figure.facecolor": BG, "savefig.facecolor": BG})

    def draw(ax, m, lo, hi):
        ax.imshow(m, cmap="magma", vmin=lo, vmax=hi, interpolation="nearest")
        ax.set_xticks([]), ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(GRID)

    rows = [(GAMES[g], maps(1, g)) for g in GAMES] + [("Breakout,\nshuffled", maps(1, "breakout", "shuffled"))]
    fig, axes = plt.subplots(len(rows), 5, figsize=(9, 9.2), gridspec_kw={"wspace": 0.08, "hspace": 0.12})
    for r, (label, m) in enumerate(rows):
        for c in range(5):
            draw(axes[r, c], m[:, :, c], m.min(), m.max())
            if r == 0:
                axes[r, c].set_title(fp.EXPS[1]["tables"][c], fontsize=11, color=MUTED, pad=8)
        axes[r, 0].set_ylabel(label, fontsize=12, color=FG, rotation=0, ha="right", va="center", labelpad=10)
    fig.savefig(os.path.join(HERE, "assets", "footprint_exp1.png"), dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.2), gridspec_kw={"wspace": 0.08, "hspace": 0.12})
    for c, shape in enumerate(SHAPES):
        for r, control in enumerate((None, "shuffled")):
            m = maps(2, shape, control)[:, :, 0]
            draw(axes[r, c], m, m.min(), m.max())
        axes[0, c].set_title(shape, fontsize=12, color=MUTED, pad=8)
    for r, label in enumerate(("real", "shuffled")):
        axes[r, 0].set_ylabel(label, fontsize=12, color=FG, rotation=0, ha="right", va="center", labelpad=10)
    fig.savefig(os.path.join(HERE, "assets", "footprint_exp2.png"), dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("assets/footprint_exp1.png, assets/footprint_exp2.png")


def gif():
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


CA_N, CA_CELL, CA_STEPS, CA_MS = 80, 3, 36, 120
CA_SEEDS = {"B24/S5": [(40, 39), (40, 40)], "B128/S0": [(40, 40)]}
CA_PANELS = [("GPT-6.1 Sol", "gpt-6.1-sol"), ("Claude Opus 5.5", "claude-opus-5-5"), ("GPT-6 Luna", "gpt-6-luna")]


def ca_run(rule, model):
    """The model's closed-round answer for this rule; if it was refused, its answer to the rule-change wording."""
    for variant in ("closed", "closed-rule-change"):
        for f in sorted(glob.glob(os.path.join(HERE, "runs", "ca", variant, ca.rule_id(rule), "trained", model, "*",
                                               "r0", "run.json"))):
            rec = json.load(open(f))
            if not rec["refused"]:
                z = np.load(f.replace("run.json", "net.npz"))
                return {n: z[n] for n in ca.NAMES}, rec["rule_stated"], variant != "closed"
    raise FileNotFoundError(f"no answer for {rule} from {model}")


def ca_frames(rule):
    """The new rule, computed directly, and each model's edited network, run from the same seed on an 80 x 80 torus."""
    def by_rule(g):
        born, survive = ca.parse_rule(target)
        n = sum(np.roll(np.roll(g, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
        return np.where(g == 1, np.isin(n, list(survive)), np.isin(n, list(born))).astype(np.uint8)

    def by_net(net):
        def step(g):
            x = np.stack([np.roll(np.roll(g, 1 - i, 0), 1 - j, 1) for i in range(3) for j in range(3)], -1)
            return ca.alive(net, x.reshape(-1, 9).astype(float)).reshape(g.shape).astype(np.uint8)
        return step

    target = ca.with_birth(rule, 6)
    seed = np.zeros((CA_N, CA_N), np.uint8)
    for r, c in CA_SEEDS[rule]:
        seed[r, c] = 1
    panels = [{"name": "The new rule", "sub": f"{target}, from the rule itself", "step": by_rule}]
    for name, model in CA_PANELS:
        net, stated, reworded = ca_run(rule, model)
        panels.append({"name": name + (" †" if reworded else ""), "sub": f"read the old rule as {stated}",
                       "right": stated == rule, "step": by_net(net)})
    for p in panels:
        g, p["grids"] = seed.copy(), []
        for _ in range(CA_STEPS + 1):
            p["grids"].append(g)
            g = p["step"](g)
    return panels


def ca_render(k, panels, rule):
    board = CA_N * CA_CELL
    pad, gap, outer, head, foot, top = 14, 14, 24, 58, 70, 44
    panel_w = board + 2 * pad
    w = 4 * panel_w + 3 * gap + 2 * outer
    h = top + head + board + foot + outer
    img = Image.new("RGB", (w * S, h * S), BG)
    d = ImageDraw.Draw(img)
    text(d, (outer, 18), f"Hidden rule {rule} plus births at 6 · same seed · each network edited by the model in one reply, "
         "from its weights alone", F_TOP, MUTED)
    text(d, (w - outer, 18), f"step {k:>2}", F_SUB, MUTED, "ra")
    truth = panels[0]["grids"][k]
    for i, p in enumerate(panels):
        x0, y0 = outer + i * (panel_w + gap), top
        g = p["grids"][k]
        wrong = g != truth
        box(d, (x0, y0, x0 + panel_w, y0 + head + board + foot), PANEL, 10)
        text(d, (x0 + pad, y0 + 14), p["name"], F_TITLE, FG)
        color = MUTED if i == 0 else (OK if p["right"] else BAD)
        text(d, (x0 + pad, y0 + 38), p["sub"], F_SUB, color)
        bx, by = x0 + pad, y0 + head
        box(d, (bx, by, bx + board, by + board), BOARD, 6)
        for r, c in np.argwhere((g == 1) | wrong):
            d.rectangle([(bx + c * CA_CELL) * S, (by + r * CA_CELL) * S, (bx + (c + 1) * CA_CELL) * S - 1,
                         (by + (r + 1) * CA_CELL) * S - 1], fill=BAD if wrong[r, c] else BALL)
        fy = by + board + 14
        if i == 0:
            text(d, (x0 + pad, fy), "Alive cells", F_SMALL, MUTED)
            text(d, (x0 + panel_w - pad, fy), f"{int(g.sum())}", F_BIG, FG, "ra")
        else:
            n = int(wrong.sum())
            text(d, (x0 + pad, fy), "Cells unlike the new rule", F_SMALL, MUTED)
            text(d, (x0 + panel_w - pad, fy), f"{n}", F_BIG, OK if n == 0 else BAD, "ra")
            first = next((s for s in range(len(p["grids"])) if (p["grids"][s] != panels[0]["grids"][s]).any()), None)
            if first is not None and k >= first:
                text(d, (x0 + pad, fy + 26), f"first wrong at step {first}", F_SMALL, BAD)
    return img


def ca_gif(rule):
    panels = ca_frames(rule)
    images = [ca_render(k, panels, rule) for k in range(CA_STEPS + 1)]
    sample = images[::6] + [images[-1]]
    sheet = Image.new("RGB", (images[0].width, images[0].height * len(sample)))
    for k, im in enumerate(sample):
        sheet.paste(im, (0, k * images[0].height))
    pal = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    frames = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in images]
    out = os.path.join(HERE, "assets", f"ca_{ca.rule_id(rule)}.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=[CA_MS] * (len(frames) - 1) + [HOLD_MS],
                   optimize=False)    # plays once and stays on the last frame
    print(f"{out}: {len(frames)} frames, {images[0].width}x{images[0].height}, "
          f"{(CA_MS * (len(frames) - 1) + HOLD_MS) / 1000:.1f}s, {os.path.getsize(out) / 1e6:.2f} MB")


def ca_still(rule):
    """The last frame as a PNG (the README's main figure)."""
    img = ca_render(CA_STEPS, ca_frames(rule), rule)
    out = os.path.join(HERE, "assets", f"ca_{ca.rule_id(rule)}.png")
    img.save(out, optimize=True)
    print(f"{out}: {img.width}x{img.height}, {os.path.getsize(out) / 1e6:.2f} MB")


def ca_figures():
    ca_gif("B24/S5")
    ca_still("B128/S0")


def main():
    ap = argparse.ArgumentParser()
    makers = {"footprint": footprint_figures, "gif": gif, "ca": ca_figures}
    ap.add_argument("figures", nargs="*", choices=list(makers), help="default: all")
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    for name in ap.parse_args().figures or makers:
        makers[name]()


if __name__ == "__main__":
    main()
