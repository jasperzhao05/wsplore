"""Experiments 1 and 2 with each network's weights replaced by a footprint of one layer: the mean absolute weight per
input of the first layer (Exp 1, W1) or per output pixel of the last layer (Exp 2, W3), laid out on the grid. The
rest of each prompt is the authors'; answers are scored with the scorer of Turing's weights_editing harness.

  uv run footprint.py --exp 1 --show breakout                     # one network's tables
  uv run footprint.py --exp 2 --show circle --control shuffled    # the same, from the shuffled weights
  uv run footprint.py --exp 1 2 --dry-run                         # build every prompt, call nothing
  uv run footprint.py --exp 2 --models claude-opus-4-5 --reps 3
  uv run footprint.py --exp 2 --models claude-opus-4-5 --control shuffled
"""
import argparse, concurrent.futures, datetime, hashlib, json, os, re, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, "..", "weights_editing"))
sys.path.insert(0, HARNESS)
import weights_only as harness

MODELS = os.path.join(HARNESS, "models.local.toml")
EXPS = {
    1: {"layer": "W1", "shape": (500, 32), "axis": 1, "grid": (10, 10), "decimals": 2,
        "tables": ("agent", "moving objects", "reward targets", "obstacles", "previous frame")},
    2: {"layer": "W3", "shape": (64, 144), "axis": 0, "grid": (12, 12), "decimals": 3, "tables": (None,)},
}


def template(exp):
    return os.path.join(HERE, "prompts", f"exp{exp}_footprint.txt")


def shuffle_seed(net_id):
    return int(hashlib.sha256(net_id.encode()).hexdigest()[:8], 16)


def weights_text(exp, net_id, control=None):
    text = open(os.path.join(harness.ROOT, harness.EXPS[exp]["weights"].format(id=net_id))).read()
    return harness.shuffle_weights(text, shuffle_seed(net_id)) if control == "shuffled" else text


def layer(text, name, shape):
    lines = text.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith(f"{name} ")) + 1
    w = np.array([[float(v) for v in row.split()] for row in lines[start:start + shape[0]]])
    if w.shape != shape:
        raise ValueError(f"{name} has shape {w.shape}, expected {shape}")
    return w


def footprint(exp, text):
    e = EXPS[exp]
    rows, cols = e["grid"]
    return np.abs(layer(text, e["layer"], e["shape"])).mean(axis=e["axis"]).reshape(rows, cols, len(e["tables"]))


def tables(exp, fp):
    e = EXPS[exp]
    rows, cols = e["grid"]
    d = e["decimals"]
    label = len(f"row {rows - 1}")
    width = d + 3
    header = " " * (label + 1) + " ".join(f"{f'col{c}':>{width}s}" for c in range(cols))
    blocks = []
    for t, name in enumerate(e["tables"]):
        body = [f"{f'row {r}':<{label}s}  " + " ".join(f"{fp[r, c, t]:{width}.{d}f}" for c in range(cols))
                for r in range(rows)]
        title = [f"channel {t}  {name}"] if name else []
        blocks.append("\n".join([*title, header, *body]))
    return "\n\n".join(blocks)


def build_prompt(exp, net_id, control=None):
    fp = footprint(exp, weights_text(exp, net_id, control))
    return open(template(exp)).read().replace("{FOOTPRINT_TEXT}", tables(exp, fp))


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def network_id(exp, name):
    nets = harness.networks(exp)
    if name in nets:
        return name
    ids = [i for i, truth in nets.items() if truth == name]
    if not ids:
        sys.exit(f"unknown network {name!r} (known: {', '.join(nets.values())})")
    return ids[0]


def run_one(m, exp, net_id, truth, rep, out_dir, control=None):
    d = os.path.join(out_dir, f"{truth}_r{rep}")
    os.makedirs(d, exist_ok=True)
    prompt = build_prompt(exp, net_id, control)
    open(os.path.join(d, "prompt.txt"), "w").write(prompt)
    t0 = time.time()
    res = harness.PROVIDERS[m["provider"]](m, prompt)
    rec = {"exp": exp, "variant": "footprint", "network": net_id, "truth": truth, "rep": rep, "model": m["name"],
           "provider": m["provider"], "model_id": m["model_id"], "reasoning_effort": m.get("reasoning_effort"),
           "thinking_budget": m.get("thinking_budget"), "control": control, "prompt_sha256": sha256(prompt),
           "template_sha256": sha256(open(template(exp)).read()), "wall_s": round(time.time() - t0, 1),
           **{k: res[k] for k in ("attempts", "error", "finish_reason", "refused", "usage")}}
    if res["raw"] is not None:
        json.dump(res["raw"], open(os.path.join(d, "response.json"), "w"), indent=1)
    u = res["usage"] or {}
    if m.get("price_in_per_m") is not None and u.get("input") is not None:
        rec["cost_usd"] = round(u["input"] * m["price_in_per_m"] / 1e6
                                + (u["output"] or 0) * m.get("price_out_per_m", 0) / 1e6, 4)
    open(os.path.join(d, "answer.md"), "w").write(res["answer"])
    rec["score"] = harness.score(exp, res["answer"], truth) if res["answer"] else None
    json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
    return rec


def report(r):
    s = r["score"] or {}
    return (f"{r['model']:20s} exp{r['exp']} {r['truth']:9s} r{r['rep']}  guess={s.get('guess')!s:9s} "
            f"correct={s.get('correct')!s:5s} conf={s.get('confidence')}  tokens={r.get('usage')}  {r['wall_s']}s"
            + ("  REFUSED" if r["refused"] else "") + (f"  ERROR {r['error']['status']}" if r["error"] else "")
            + ("  NEEDS REVIEW" if s.get("needs_review") else ""))


def run(models, names, exps, reps, control, workers):
    harness.load_env()
    harness.check_keys(models, names)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{control}" if control else "")
    out = {(e, n): os.path.join(HERE, "runs", "footprint", f"exp{e}", re.sub(r"[^A-Za-z0-9._-]+", "_", n), stamp)
           for e in exps for n in names}
    jobs = [(models[n], e, i, t, r) for n in names for e in exps for i, t in harness.networks(e).items()
            for r in range(reps)]
    print(f"{len(jobs)} calls to {', '.join(names)}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        recs = list(pool.map(lambda j: run_one(*j, out[(j[1], j[0]["name"])], control), jobs))
    for r in recs:
        print(report(r))
    for (e, n), d in out.items():
        mine = [r for r in recs if r["model"] == n and r["exp"] == e]
        summary = harness.summarize(mine, [e], models[n].get("price_in_per_m") is not None)
        json.dump({"summary": summary, "runs": mine}, open(os.path.join(d, "summary.json"), "w"), indent=1)
        print(f"{n} exp{e}: {json.dumps(summary)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", type=int, nargs="+", default=[1], choices=sorted(EXPS))
    ap.add_argument("--models", nargs="+", help="names from the harness's models.local.toml")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--control", choices=["shuffled"], help="build the tables from the shuffled weights")
    ap.add_argument("--show", metavar="NET", help="print one network's tables (its id or its label)")
    ap.add_argument("--dry-run", action="store_true", help="build every prompt and print its size, call nothing")
    a = ap.parse_args()
    if a.show:
        for e in a.exp:
            print(tables(e, footprint(e, weights_text(e, network_id(e, a.show), a.control))))
        return
    if a.dry_run:
        for e in a.exp:
            for net_id, truth in harness.networks(e).items():
                p = build_prompt(e, net_id, a.control)
                print(f"exp{e} {truth:9s} {net_id}  {len(p):,} chars (~{len(p) // 4:,} tokens)  sha256 {sha256(p)[:12]}")
        return
    if not a.models:
        sys.exit("give --models, --show or --dry-run")
    models = harness.load_models(MODELS)
    unknown = [n for n in a.models if n not in models]
    if unknown:
        sys.exit(f"not in {MODELS}: {', '.join(unknown)} (known: {', '.join(models)})")
    run(models, a.models, a.exp, a.reps, a.control, a.workers)


if __name__ == "__main__":
    main()
