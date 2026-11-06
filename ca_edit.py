"""Editing a cellular-automaton network: can a model change one rule inside a network it did not write?
  network    3 x 3 convolution (1 -> 8 channels) + bias, ReLU, 1 x 1 convolution (8 -> 1) + bias. A cell is alive at
             the next step if the output is > 0. The next state depends only on the cell's 3 x 3 block, so the 512
             possible blocks check the whole network.
  sources    hand       written by us: channels 0-3 or so handle dead cells, the rest live cells; each channel is a
                        ramp max(0, n - t) on the neighbour count n, gated by the centre weight
             scrambled  the hand-written network with its channels shuffled and each channel rescaled (input weights
                        times a, output weight divided by a): the same outputs on all 512 blocks
             trained    trained with Adam on the 512 blocks, with all 8 channels in use
             scratch    no network given: write the target rule from zero (the baseline)
  variants   stated     Life (B3/S23) -> HighLife (B36/S23); the prompt states both rules
             hidden     three random Life-like rules, each -> the same rule plus births at 6. The prompt states
                        neither rule, only the change: a dead cell with 6 live neighbours becomes alive and every
                        other block keeps its output. (The scratch baseline is given the target rule.)
             closed     as hidden, with four new rules and trained networks only, chosen so that there is no way
                        around reading the network: no two channels can be freed (removed, or folded into a channel
                        with a proportional activation) without changing an output, and no single freed channel can
                        add the births on its own. The answer must also say which rule the network follows now
                        (a CURRENT RULE line), which is scored on its own.
  In every case 28 blocks must change (dead centre, 6 live neighbours) and the other 484 must not, and no source
  network can make the change through its output layer alone.

  uv run ca_edit.py --sources                            # build the source networks and check them
  uv run ca_edit.py --variant closed --dry-run           # write the prompts to prompts/ca/, call nothing
  uv run ca_edit.py --variant closed --models gpt-6.1-sol gpt-6-luna claude-opus-5-5
"""
import argparse, concurrent.futures, datetime, glob, hashlib, itertools, json, os, re, sys, time
import numpy as np
from scipy.optimize import linprog
import design as t

harness, exp5 = t.harness, t.exp5
HERE = t.HERE
K = 8
BLOCKS = np.array(list(itertools.product((0, 1), repeat=9)), np.float64)   # row-major; index 4 is the cell itself
CELL = BLOCKS[:, 4].astype(int)
NEIGHBOURS = (BLOCKS.sum(1) - BLOCKS[:, 4]).astype(int)
CONDITIONS = ("hand", "scrambled", "trained", "scratch")
VARIANTS = ("stated", "hidden", "closed")
SOURCES = os.path.join(HERE, "runs", "ca", "sources")
NAMES = {"K": (K, 3, 3), "b": (K,), "w": (K,), "c": ()}
TITLES = {"B3/S23": "Conway's Game of Life", "B36/S23": "HighLife"}
WELL_KNOWN = {"B3/S23", "B36/S23", "B2/S", "B3678/S34678", "B3/S012345678", "B36/S125", "B368/S245", "B34/S34",
              "B1357/S1357", "B3/S12345", "B3/S1234", "B37/S23", "B38/S23", "B35678/S5678", "B4678/S35678"}


# --- rules ---------------------------------------------------------------------------------------------------------

def parse_rule(rule):
    b, s = rule.upper().split("/")
    return {int(ch) for ch in b[1:]}, {int(ch) for ch in s[1:]}


def make_rule(born, survive):
    return "B" + "".join(map(str, sorted(born))) + "/S" + "".join(map(str, sorted(survive)))


def with_birth(rule, n):
    born, survive = parse_rule(rule)
    return make_rule(born | {n}, survive)


def rule_id(rule):
    return rule.replace("/", "_")


def table(rule):
    born, survive = parse_rule(rule)
    return np.array([(n in survive) if c else (n in born) for c, n in zip(CELL, NEIGHBOURS)])


def words(ns, exactly):
    items = [("exactly " if exactly else "") + str(n) for n in sorted(ns)]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " or " + items[-1]


def rule_text(rule):
    born, survive = parse_rule(rule)
    title = TITLES.get(rule)
    noun = lambda ns: "neighbour" if ns == {1} else "neighbours"
    return ((f"{title}, rule {rule}: " if title else f"rule {rule}: ")
            + f"a dead cell with {words(born, True)} live {noun(born)} becomes alive; a live cell with "
            f"{words(survive, False)} live {noun(survive)} stays alive; every other cell is dead at the next step")


# --- networks ------------------------------------------------------------------------------------------------------

def empty():
    return {name: np.zeros(shape) for name, shape in NAMES.items()}


def hidden(net, x=BLOCKS):
    return np.maximum(x @ net["K"].reshape(K, 9).T + net["b"], 0)


def alive(net, x=BLOCKS):
    return hidden(net, x) @ net["w"] + net["c"] > 0


def channels_in_use(net):
    """(channels active on some block with a non-zero output weight, channels whose removal changes an output)"""
    h = hidden(net)
    active = int(((h > 0).any(0) & (net["w"] != 0)).sum())
    base, needed = alive(net), 0
    for k in range(K):
        n2 = {name: v.copy() for name, v in net.items()}
        n2["w"][k] = 0
        needed += int((alive(n2) != base).any())
    return active, needed


def output_layer_suffices(net, rule):
    """Whether some w, c reach the rule with this network's hidden layer unchanged (a linear feasibility problem)."""
    h = hidden(net)
    y = np.where(table(rule), 1.0, -1.0)
    r = linprog(np.zeros(K + 1), A_ub=-y[:, None] * np.hstack([h, np.ones((len(h), 1))]), b_ub=-np.ones(len(h)),
                bounds=[(None, None)] * (K + 1), method="highs")
    return r.status == 0


def ramps(counts):
    """{t: d} such that sum of d * max(0, n - t) is 1 for n in counts and 0 for the other n in 0..8."""
    g = lambda n: int(n in counts)
    out = {}
    for t in range(-1, 8):
        d = g(t + 1) - 2 * g(t) + g(t - 1)
        if d:
            out[t] = d
    return out


def hand(rule):
    """Dead-cell channels: max(0, n - 9c - t); live-cell channels: max(0, n + 9c - 9 - t); output weights from
    ramps(), output bias -0.5. A weight of +-2 is split into two channels, so that all 8 channels are used."""
    born, survive = parse_rule(rule)
    units = [(-9, 0, t, d) for t, d in ramps(born).items()] + [(9, -9, t, d) for t, d in ramps(survive).items()]
    while len(units) < K:
        big = [i for i, u in enumerate(units) if abs(u[3]) >= 2]
        i = big[0] if big else 0
        centre, shift, t0, d = units[i]
        half = (np.sign(d), d - np.sign(d)) if big else (d / 2, d / 2)
        units[i:i + 1] = [(centre, shift, t0, half[0]), (centre, shift, t0, half[1])]
    if len(units) > K:
        return None
    net = empty()
    ring = np.ones((3, 3)); ring[1, 1] = 0
    for k, (centre, shift, t0, d) in enumerate(units):
        net["K"][k] = ring; net["K"][k][1, 1] = centre; net["b"][k] = shift - t0; net["w"][k] = d
    net["c"] = np.array(-0.5)
    return net


def fits(rule):
    """An existence check: the rule can be written with 8 channels (by hand() or by ramps on x = 2n + c)."""
    if hand(rule) is not None:
        return True
    born, survive = parse_rule(rule)
    s = [(x // 2 in survive) if x % 2 else (x // 2 in born) for x in range(18)]
    return not s[0] and sum(s[x] != s[x + 1] for x in range(17)) <= K


def scramble(net, seed=0):
    rng = np.random.default_rng(seed)
    perm, a = rng.permutation(K), rng.uniform(0.3, 3.0, K)
    return {"K": net["K"][perm] * a[:, None, None], "b": net["b"][perm] * a, "w": net["w"][perm] / a, "c": net["c"]}


def train(rule, seed, steps=6000, lr=0.02):
    """Full-batch Adam on the 512 blocks, logistic loss."""
    rng = np.random.default_rng(seed)
    y = table(rule).astype(float)
    p = {"K": rng.normal(0, np.sqrt(2 / 9), (K, 3, 3)), "b": rng.normal(0, 0.1, K),
         "w": rng.normal(0, np.sqrt(2 / K), K), "c": np.zeros(())}
    m1 = {n: np.zeros_like(v) for n, v in p.items()}
    m2 = {n: np.zeros_like(v) for n, v in p.items()}
    for i in range(1, steps + 1):
        pre = BLOCKS @ p["K"].reshape(K, 9).T + p["b"]
        h = np.maximum(pre, 0)
        g = (1 / (1 + np.exp(-(h @ p["w"] + p["c"]))) - y) / len(y)
        dpre = np.outer(g, p["w"]) * (pre > 0)
        grad = {"K": (dpre.T @ BLOCKS).reshape(K, 3, 3), "b": dpre.sum(0), "w": h.T @ g, "c": np.array(g.sum())}
        for n in p:
            m1[n] = 0.9 * m1[n] + 0.1 * grad[n]
            m2[n] = 0.999 * m2[n] + 0.001 * grad[n] ** 2
            p[n] = p[n] - lr * (m1[n] / (1 - 0.9 ** i)) / (np.sqrt(m2[n] / (1 - 0.999 ** i)) + 1e-8)
    return p


def free(net, ks, h, base):
    """A copy of the network with channels ks freed (output weight 0), each one removed or folded into another
    channel with a proportional activation, keeping all 512 outputs; None if there is no such way."""
    options = []
    for k in ks:
        opts = [None]
        for m in range(K):
            if m not in ks and h[:, m].any():
                opts.append((m, float(h[:, k] @ h[:, m]) / float(h[:, m] @ h[:, m])))
        options.append(opts)
    for choice in itertools.product(*options):
        n2 = {n: v.copy() for n, v in net.items()}
        for k, o in zip(ks, choice):
            if o is not None:
                n2["w"][o[0]] += o[1] * net["w"][k]
            n2["w"][k] = 0
        if (alive(n2) == base).all():
            return n2
    return None


def one_channel_births(net, target):
    """Whether max(0, n - t) on dead cells alone, with a suitable output weight, takes this network to the target."""
    y = hidden(net) @ net["w"] + net["c"]
    want = table(target)
    for t0 in (5, 5.5):
        g = np.maximum(NEIGHBOURS - t0 - 10 * CELL, 0)
        if (y[g == 0] > 0).tolist() != want[g == 0].tolist():
            continue
        on = g > 0
        low = max([-y[i] / g[i] for i in np.where(on & want)[0]], default=-np.inf)
        high = min([-y[i] / g[i] for i in np.where(on & ~want)[0]], default=np.inf)
        if low < high:
            return True
    return False


def spare(net, target):
    """How much room the network leaves for a change that does not need reading it."""
    h, base = hidden(net), alive(net)
    alone = [k for k in range(K) if free(net, (k,), h, base) is not None]
    pairs = [ks for ks in itertools.combinations(range(K), 2) if free(net, ks, h, base) is not None]
    single = any(one_channel_births(free(net, (k,), h, base), target) for k in alone)
    return {"freeable_channels": alone, "freeable_pairs": len(pairs), "one_channel_births": single,
            "closed": not pairs and not single}


def rounded(net, places=3):
    return {n: np.round(v, places) for n, v in net.items()}


def describe(net, rule, target):
    active, needed = channels_in_use(net)
    return {"source_blocks_right": int((alive(net) == table(rule)).sum()), "channels_active": active,
            "channels_needed": needed, "output_layer_suffices": output_layer_suffices(net, target)}


# --- source networks -----------------------------------------------------------------------------------------------

def target_of(variant, rule):
    return "B36/S23" if variant == "stated" else with_birth(rule, 6)


def sources_for(rule, target, seeds=20, closed=False):
    """hand, scrambled and trained networks for one rule, or None if the rule does not meet the conditions.
    With closed, the trained network must also leave no room for a change that does not need reading it."""
    h = hand(rule)
    if h is None or not fits(target) or output_layer_suffices(h, target):
        return None
    want = channels_in_use(h)[1]
    usable = []
    for seed in range(seeds):
        net = rounded(train(rule, seed))
        d = describe(net, rule, target)
        if d["source_blocks_right"] == 512 and d["channels_active"] == K and not d["output_layer_suffices"] \
                and (not closed or spare(net, target)["closed"]):
            usable.append((abs(d["channels_needed"] - want), seed, net))
    if not usable:
        return None
    _, seed, trained = min(usable, key=lambda u: u[:2])
    return {"hand": h, "scrambled": rounded(scramble(h)), "trained": trained,
            "trained_seed": seed, "seeds_tried": seeds, "seeds_usable": len(usable)}


def hidden_rules(n=3, seed=2026, closed=False, exclude=()):
    """Random Life-like rules: 1-3 birth counts out of 1-5, 7, 8 (never 6), 1-4 survival counts out of 0-8, each rule
    with its own set of birth counts."""
    rng = np.random.default_rng(seed)
    chosen = {}
    while len(chosen) < n:
        born = rng.choice([1, 2, 3, 4, 5, 7, 8], size=int(rng.integers(1, 4)), replace=False)
        survive = rng.choice(range(9), size=int(rng.integers(1, 5)), replace=False)
        rule = make_rule(born, survive)
        if rule in WELL_KNOWN or rule in exclude or any(parse_rule(r)[0] == set(born) for r in chosen):
            continue
        src = sources_for(rule, with_birth(rule, 6), seeds=60 if closed else 20, closed=closed)
        if src:
            chosen[rule] = src
            if closed:
                print(f"closed: found {rule} ({len(chosen)}/{n})", flush=True)
    return chosen


def build_sources():
    found = {"stated": {"B3/S23": sources_for("B3/S23", "B36/S23")}, "hidden": hidden_rules()}
    found["closed"] = hidden_rules(4, seed=2027, closed=True, exclude={"B3/S23", *found["hidden"]})
    index = {}
    for variant, rules in found.items():
        index[variant] = []
        for rule, src in rules.items():
            target = target_of(variant, rule)
            d = os.path.join(SOURCES, rule_id(rule))
            os.makedirs(d, exist_ok=True)
            info = {"rule": rule, "target": target, "trained_seed": src["trained_seed"],
                    "seeds_tried": src["seeds_tried"], "seeds_usable": src["seeds_usable"]}
            for name in ("hand", "scrambled", "trained"):
                np.savez(os.path.join(d, f"{name}.npz"), **src[name])
                info[name] = describe(src[name], rule, target) | {"spare": spare(src[name], target)}
            json.dump(info, open(os.path.join(d, "sources.json"), "w"), indent=1)
            index[variant].append(rule)
            sp = info["trained"]["spare"]
            print(f"{variant:6s} {rule:12s} -> {target:12s} " + "  ".join(
                f"{n}: right {info[n]['source_blocks_right']}, channels {info[n]['channels_active']}/"
                f"{info[n]['channels_needed']}" for n in ("hand", "scrambled", "trained"))
                  + f"  (trained seed {src['trained_seed']}, {src['seeds_usable']}/{src['seeds_tried']} usable; "
                  f"trained freeable channels {sp['freeable_channels']}, pairs {sp['freeable_pairs']}, "
                  f"one-channel births {sp['one_channel_births']}, closed {sp['closed']})")
    json.dump(index, open(os.path.join(SOURCES, "rules.json"), "w"), indent=1)


def rules_of(variant):
    return json.load(open(os.path.join(SOURCES, "rules.json")))[variant]


def load_source(rule, name):
    f = np.load(os.path.join(SOURCES, rule_id(rule), f"{name}.npz"))
    return {n: f[n] for n in NAMES}


# --- prompts -------------------------------------------------------------------------------------------------------

def num(v):
    s = f"{float(v):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def weights_text(net):
    rows = []
    for k in range(K):
        kern = ", ".join("[" + ", ".join(num(v) for v in r) + "]" for r in net["K"][k])
        rows.append(f"K[{k}] = [{kern}]    b[{k}] = {num(net['b'][k])}    w[{k}] = {num(net['w'][k])}")
    return "\n".join(rows + [f"c = {num(net['c'])}"])


NETWORK = """A cellular automaton updates a grid of cells, each 0 (dead) or 1 (alive). The network below computes the next \
state of one cell from the 3 x 3 block of cells centred on it, and the same network is applied to every cell at every \
step.

THE NETWORK
- Input: x[i][j] for rows i = 0, 1, 2 and columns j = 0, 1, 2. x[1][1] is the cell itself; the other eight are its \
neighbours.
- Hidden layer, 8 channels: h[k] = max(0, b[k] + sum over i, j of K[k][i][j] * x[i][j]), for k = 0, ..., 7.
- Output: y = c + sum over k of w[k] * h[k]. The cell is alive at the next step if y > 0 and dead otherwise.

"""
FORMAT = """- End your answer with one edits block. Each line sets one weight: K[k][i][j] = value, b[k] = value, \
w[k] = value or c = value. {unlisted} For example:

```edits
K[0][1][1] = -3
b[0] = 0.5
w[0] = 2
c = -1
```
"""
READ_LINE = ("- Before the edits block, write one line of the form CURRENT RULE: B.../S... saying which rule the network "
             "follows now, if it follows a Life-like rule (the next state depends only on the cell's own state and how "
             "many of its 8 neighbours are alive), or CURRENT RULE: not Life-like if it does not.\n")


def edit_rules(read=False):
    return ("RULES\n- Keep the network's form: 8 channels and the layers above. You may change any weight to any "
            "value.\n- You cannot run code. Work from the weights.\n" + (READ_LINE if read else "")
            + FORMAT.format(unlisted="Weights you do not list keep their current values."))


EDIT_RULES = edit_rules()


WORDINGS = ("original", "rule-change")
RULE_CHANGE = ("WHAT IT DOES NOW\nThe network implements the update rule of a cellular automaton. The rule is not "
               "stated here.\n\nYOUR TASK\nThe automaton's rule is changing in one way: from now on, a dead cell with "
               "exactly 6 live neighbours is also born (it becomes alive at the next step). Nothing else about the rule "
               "changes. Edit the weights so that the network implements the new rule. The edited network will be "
               "checked on all 512 possible 3 x 3 blocks: the 28 blocks with a dead centre and exactly 6 live "
               "neighbours must give alive, and every other block must give the same next state as under the current "
               "rule.\n\n")


def label(variant, wording):
    return variant if wording == "original" else f"{variant}-{wording}"


def build_prompt(variant, rule, condition, wording="original"):
    target = target_of(variant, rule)
    if wording == "rule-change":
        if variant == "stated" or condition == "scratch":
            raise ValueError("the rule-change wording is for the hidden and closed edit prompts")
        return (NETWORK + "THE CURRENT WEIGHTS\n" + weights_text(load_source(rule, condition)) + "\n\n" + RULE_CHANGE
                + edit_rules(read=variant == "closed"))
    if condition == "scratch":
        return (NETWORK + f"YOUR TASK\nChoose the weights so that the network implements {rule_text(target)}. The "
                "network will be checked on all 512 possible 3 x 3 blocks and must be right on every one.\n\nRULES\n"
                "- Keep the network's form: 8 channels and the layers above.\n- You cannot run code.\n"
                + FORMAT.format(unlisted="Every weight starts at 0; list each weight you set."))
    weights = "THE CURRENT WEIGHTS\n" + weights_text(load_source(rule, condition)) + "\n\n"
    if variant == "stated":
        return (NETWORK + weights + f"WHAT IT DOES NOW\nIt implements {rule_text(rule)}. It gives the right next "
                f"state for all 512 possible 3 x 3 blocks.\n\nYOUR TASK\nEdit the weights so that the network "
                f"implements {rule_text(target)}. The edited network will be checked on all 512 possible 3 x 3 "
                "blocks and must be right on every one.\n\n" + EDIT_RULES)
    return (NETWORK + weights + "WHAT IT DOES NOW\nIt gives every cell a next state by some rule, which is not stated "
            "here.\n\nYOUR TASK\nEdit the weights so that a dead cell with exactly 6 live neighbours becomes alive at "
            "the next step, and every other cell gets the same next state as the current network gives it. The "
            "edited network will be checked on all 512 possible 3 x 3 blocks: on the 28 blocks with a dead centre "
            "and exactly 6 live neighbours it must give alive, and on the other 484 it must give the same output as "
            "the current network.\n\n" + edit_rules(read=variant == "closed"))


STATED = re.compile(r"CURRENT RULE:\s*[`*]*\s*(B[0-8]*\s*/\s*S[0-8]*|not\s+Life-like)", re.I)


def stated_rule(answer):
    """The rule the answer says the network follows now (its last CURRENT RULE line), or None."""
    found = STATED.findall(answer)
    if not found:
        return None
    s = re.sub(r"\s+", "", found[-1]).upper()
    return "not Life-like" if s.startswith("NOT") else make_rule(*parse_rule(s))


# --- answers -------------------------------------------------------------------------------------------------------

NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
LINE = re.compile(rf"^\s*(K\[(\d)\]\[(\d)\]\[(\d)\]|b\[(\d)\]|w\[(\d)\]|c)\s*=\s*({NUMBER})\s*$")
KERNEL = re.compile(r"^\s*K\[(\d)\]\s*=\s*(\[\s*\[.*\]\s*\])\s*$")   # a whole kernel, as the prompt shows the weights


def apply_edits(answer, net):
    blocks = re.findall(r"```edits\s*\n(.*?)```", answer, re.S)
    net = {n: v.astype(float).copy() for n, v in net.items()}
    rec = {"found": bool(blocks), "statements": 0, "applied": 0, "bad": []}
    for line in (blocks[-1].splitlines() if blocks else []):
        if not line.strip():
            continue
        rec["statements"] += 1
        whole = KERNEL.match(line)
        if whole:
            k, values = int(whole.group(1)), [float(v) for v in re.findall(NUMBER, whole.group(2))]
            rows = re.findall(r"\[([^\[\]]*)\]", whole.group(2))
            if k >= K or len(values) != 9 or len(rows) != 3 or any(len(re.findall(NUMBER, r)) != 3 for r in rows):
                rec["bad"].append(line.strip())
                continue
            net["K"][k] = np.array(values).reshape(3, 3)
            rec["applied"] += 1
            continue
        m = LINE.match(line)
        if not m:
            rec["bad"].append(line.strip())
            continue
        name, v = m.group(1), float(m.group(7))
        if name.startswith("K"):
            idx = tuple(int(m.group(i)) for i in (2, 3, 4))
            if idx[0] >= K or idx[1] > 2 or idx[2] > 2:
                rec["bad"].append(line.strip()); continue
            net["K"][idx] = v
        elif name == "c":
            net["c"] = np.array(v)
        else:
            k = int(m.group(5) or m.group(6))
            if k >= K:
                rec["bad"].append(line.strip()); continue
            net[name[0]][k] = v
        rec["applied"] += 1
    return net, rec


def score(net, before, rule, target):
    want, was = table(target), table(rule)
    out = alive(net)
    change = want != was
    diff = {n: np.abs(net[n] - before[n]) > 1e-9 for n in NAMES}
    touched = diff["K"].reshape(K, 9).any(1) | diff["b"] | diff["w"]
    return {"exact": bool((out == want).all()), "blocks_right": int((out == want).sum()),
            "target_right": int((out == want)[change].sum()), "target_blocks": int(change.sum()),
            "broken_elsewhere": int((out != want)[~change].sum()), "other_blocks": int((~change).sum()),
            "weights_changed": int(sum(d.sum() for d in diff.values())), "weights_total": 8 * 9 + 8 + 8 + 1,
            "channels_touched": int(touched.sum())}


# --- runs ----------------------------------------------------------------------------------------------------------

def ask(m, variant, rule, condition, rep, out_dir, prompt, wording="original"):
    m = exp5.for_exp5(m)
    target = target_of(variant, rule)
    d = os.path.join(out_dir, f"r{rep}")
    os.makedirs(d, exist_ok=True)
    t0 = time.time()
    res = harness.PROVIDERS[m["provider"]](m, prompt)
    rec = {"exp": "ca_edit", "variant": variant, "wording": wording, "condition": condition, "source_rule": rule,
           "target_rule": target,
           "rep": rep, "model": m["name"], "provider": m["provider"], "model_id": m["model_id"],
           "reasoning_effort": m.get("reasoning_effort"), "thinking_budget": m.get("thinking_budget"),
           "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "wall_s": round(time.time() - t0, 1),
           **{k: res[k] for k in ("attempts", "error", "finish_reason", "refused", "usage")}}
    if res["raw"] is not None:
        json.dump(res["raw"], open(os.path.join(d, "response.json"), "w"), indent=1)
    u = res["usage"] or {}
    if m.get("price_in_per_m") is not None and u.get("input") is not None:
        rec["cost_usd"] = round(u["input"] * m["price_in_per_m"] / 1e6
                                + (u["output"] or 0) * m.get("price_out_per_m", 0) / 1e6, 4)
    answer = res["answer"] or ""
    open(os.path.join(d, "answer.md"), "w").write(answer)
    before = empty() if condition == "scratch" else load_source(rule, condition)
    net, rec["edits"] = apply_edits(answer, before)
    rec["score"] = score(net, before, rule, target) if rec["edits"]["applied"] else None
    rec["rule_stated"] = stated_rule(answer)
    rec["rule_right"] = rec["rule_stated"] == rule if variant == "closed" else None
    np.savez(os.path.join(d, "net.npz"), **net)
    json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
    return rec


def run(variant, names, conditions, reps, workers, only=None, wording="original"):
    harness.load_env()
    models = harness.load_models(t.MODELS)
    unknown = [n for n in names if n not in models]
    if unknown:
        sys.exit(f"not in {t.MODELS}: {', '.join(unknown)}")
    harness.check_keys(models, names)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    jobs = [(models[n], variant, rule, c, r,
             os.path.join(HERE, "runs", "ca", label(variant, wording), rule_id(rule), c, n, stamp),
             build_prompt(variant, rule, c, wording), wording)
            for rule in rules_of(variant) if not only or rule in only
            for c in conditions for n in names for r in range(reps)]
    print(f"{len(jobs)} calls to {', '.join(names)}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        for f in concurrent.futures.as_completed([pool.submit(ask, *j) for j in jobs]):
            try:
                rec = f.result()
            except Exception as ex:
                print(f"call failed: {ex!r}", flush=True)
                continue
            s = rec["score"] or {}
            print(f"{rec['source_rule']:10s} {rec['condition']:9s} {rec['model']:18s} r{rec['rep']}  "
                  + (f"read {rec['rule_stated']} ({'right' if rec['rule_right'] else 'wrong'})  "
                     if rec["rule_right"] is not None else "") +
                  f"exact={s.get('exact')}  target {s.get('target_right')}/{s.get('target_blocks')}  broken "
                  f"elsewhere {s.get('broken_elsewhere')}/{s.get('other_blocks')}  weights changed "
                  f"{s.get('weights_changed')}/{s.get('weights_total')}  edits {rec['edits']['applied']}/"
                  f"{rec['edits']['statements']}  tokens={rec['usage']}  {rec['wall_s']}s  "
                  f"cost={rec.get('cost_usd')}" + (f"  ERROR {rec['error']['status']}" if rec["error"] else ""),
                  flush=True)


def selftest():
    life, highlife = table("B3/S23"), table("B36/S23")
    assert life.sum() == 140 and (life != highlife).sum() == 28
    assert rule_text("B36/S23").startswith("HighLife, rule B36/S23: a dead cell with exactly 3 or exactly 6 live")
    h = hand("B3/S23")
    assert list(h["b"]) == [-2, -3, -3, -4, -10, -11, -12, -13] and list(h["w"]) == [1, -1, -1, 1, 1, -1, -1, 1]
    assert (alive(h) == life).all() and not output_layer_suffices(h, "B36/S23")
    assert (alive(scramble(h)) == life).all()
    for rule in ("B1/S0", "B2578/S0468", "B378/S012345678"):
        net = hand(rule)
        assert net is None or (alive(net) == table(rule)).all(), rule
    ans = "```edits\nK[7][2][2] = 1.5\nb[3] = -2\nw[0] = 4\nc = 0.25\nnonsense\n```"
    net, rec = apply_edits(ans, h)
    assert rec["applied"] == 4 and rec["bad"] == ["nonsense"]
    assert net["K"][7, 2, 2] == 1.5 and net["b"][3] == -2 and net["w"][0] == 4 and float(net["c"]) == 0.25
    assert score(net, h, "B3/S23", "B36/S23")["weights_changed"] == 4
    net, rec = apply_edits("```edits\nK[2] = [[1, 2, 3], [4, -5.5, 6], [7, 8, 9e0]]\nK[3] = [[1, 2], [3]]\n```", h)
    assert rec["applied"] == 1 and len(rec["bad"]) == 1 and net["K"][2, 1, 1] == -5.5 and net["K"][2, 2, 2] == 9
    assert stated_rule("so CURRENT RULE: B83/S1 ... **CURRENT RULE:** `B38 / S1`\n```edits\n```") == "B38/S1"
    assert stated_rule("CURRENT RULE: not Life-like") == "not Life-like" and stated_rule("no line") is None
    assert stated_rule("CURRENT RULE: B3/S") == "B3/S"
    assert not spare(hand("B3/S23"), "B36/S23")["closed"]     # its two copies of max(0, n - 3) fold into one
    print("selftest ok")


def rescore():
    """Score every recorded answer again with the current edits reader; writes runs/ca/scores.json."""
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "runs", "ca", "*", "*", "*", "*", "*", "r*", "run.json"))):
        r = json.load(open(f))
        variant = f.split(os.sep)[-7]
        answer = open(f.replace("run.json", "answer.md")).read()
        before = empty() if r["condition"] == "scratch" else load_source(r["source_rule"], r["condition"])
        net, edits = apply_edits(answer, before)
        s = score(net, before, r["source_rule"], r["target_rule"]) if edits["applied"] else None
        stated = stated_rule(answer)
        rows.append({"variant": variant, "source_rule": r["source_rule"], "target_rule": r["target_rule"],
                     "condition": r["condition"], "model": r["model"], "run": os.path.relpath(os.path.dirname(f), HERE),
                     "finish_reason": r["finish_reason"], "refused": r["refused"], "edits": edits, "score": s,
                     "rule_stated": stated, "rule_right": stated == r["source_rule"] if variant.startswith("closed") else None,
                     "wording": r.get("wording", "original"),
                     "output_tokens": (r["usage"] or {}).get("output"), "wall_s": r["wall_s"],
                     "cost_usd": r.get("cost_usd")})
        changed = "" if (s or {}).get("exact") == (r["score"] or {}).get("exact") else "   (changed by the new reader)"
        print(f"{variant:6s} {r['source_rule']:8s} {r['condition']:9s} {r['model']:18s} "
              f"exact={(s or {}).get('exact')}  weights changed {(s or {}).get('weights_changed')}  "
              f"finish={r['finish_reason']}{changed}")
    json.dump(rows, open(os.path.join(HERE, "runs", "ca", "scores.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", action="store_true", help="build and check the source networks")
    ap.add_argument("--variant", choices=VARIANTS, default="hidden")
    ap.add_argument("--dry-run", action="store_true", help="write the prompts to prompts/ca/, call nothing")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rescore", action="store_true", help="score every recorded answer again; writes runs/ca/scores.json")
    ap.add_argument("--models", nargs="+", help="names from the harness's models.local.toml")
    ap.add_argument("--conditions", nargs="+", choices=CONDITIONS,
                    help="default: trained for closed, all four for the others")
    ap.add_argument("--wording", choices=WORDINGS, default="original",
                    help="rule-change: the hidden/closed task worded as a change of rule (a check on refusals)")
    ap.add_argument("--rules", nargs="+", help="only these source rules, e.g. B38/S1 (default: all of the variant's)")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    a.conditions = a.conditions or (["trained"] if a.variant == "closed" else list(CONDITIONS))
    if a.selftest:
        return selftest()
    if a.rescore:
        return rescore()
    if a.sources:
        return build_sources()
    if a.dry_run:
        for rule in rules_of(a.variant):
            d = os.path.join(HERE, "prompts", "ca", label(a.variant, a.wording), rule_id(rule))
            os.makedirs(d, exist_ok=True)
            for c in a.conditions:
                text = build_prompt(a.variant, rule, c, a.wording)
                open(os.path.join(d, f"{c}.txt"), "w").write(text)
                print(f"{rule:10s} {c:9s} {len(text):,} chars  sha256 {hashlib.sha256(text.encode()).hexdigest()[:12]}")
        return
    if not a.models:
        sys.exit("give --models, --sources or --dry-run")
    if a.rules and not set(a.rules) <= set(rules_of(a.variant)):
        sys.exit(f"--rules must be among {', '.join(rules_of(a.variant))}")
    run(a.variant, a.models, a.conditions, a.reps, a.workers, a.rules, a.wording)


if __name__ == "__main__":
    main()
