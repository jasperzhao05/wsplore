"""Experiment 1 with each network's weights replaced by a footprint of its first layer: for every input, the mean
absolute weight to the 32 first-layer units, laid out as one 10 x 10 table per channel. The rest of the prompt is the
authors' Experiment 1 prompt; answers are scored with the scorer of Turing's weights_editing harness.

  uv run footprint.py --show breakout                      # one network's tables
  uv run footprint.py --show breakout --control shuffled   # the same, from the shuffled weights
  uv run footprint.py --dry-run                            # build every prompt, call nothing
  uv run footprint.py --models claude-opus-4-5 --reps 1
  uv run footprint.py --models claude-opus-4-5 --control shuffled
"""
import argparse, concurrent.futures, datetime, hashlib, json, os, re, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, "..", "weights_editing"))
sys.path.insert(0, HARNESS)
import weights_only as harness

TEMPLATE = os.path.join(HERE, "prompts", "exp1_footprint.txt")
MODELS = os.path.join(HARNESS, "models.local.toml")
GRID, CHANNELS, UNITS = 10, ("agent", "moving objects", "reward targets", "obstacles", "previous frame"), 32


def shuffle_seed(net_id):
    return int(hashlib.sha256(net_id.encode()).hexdigest()[:8], 16)


def weights_text(net_id, control=None):
    text = open(os.path.join(harness.ROOT, harness.EXPS[1]["weights"].format(id=net_id))).read()
    return harness.shuffle_weights(text, shuffle_seed(net_id)) if control == "shuffled" else text


def first_layer(text):
    lines = text.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith("W1 ")) + 1
    rows = lines[start:start + GRID * GRID * len(CHANNELS)]
    w1 = np.array([[float(v) for v in row.split()] for row in rows])
    if w1.shape != (GRID * GRID * len(CHANNELS), UNITS):
        raise ValueError(f"W1 has shape {w1.shape}")
    return w1


def footprint(w1):
    return np.abs(w1).mean(axis=1).reshape(GRID, GRID, len(CHANNELS))


def tables(fp):
    header = "      " + " ".join(f"{f'col{c}':>5s}" for c in range(GRID))
    blocks = []
    for ch, name in enumerate(CHANNELS):
        rows = [f"row {r}  " + " ".join(f"{fp[r, c, ch]:5.2f}" for c in range(GRID)) for r in range(GRID)]
        blocks.append("\n".join([f"channel {ch}  {name}", header, *rows]))
    return "\n\n".join(blocks)


def build_prompt(net_id, control=None):
    fp = footprint(first_layer(weights_text(net_id, control)))
    return open(TEMPLATE).read().replace("{FOOTPRINT_TEXT}", tables(fp))


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def network_id(name):
    nets = harness.networks(1)
    if name in nets:
        return name
    ids = [i for i, truth in nets.items() if truth == name]
    if not ids:
        sys.exit(f"unknown network {name!r} (known: {', '.join(nets.values())})")
    return ids[0]


def run_one(m, net_id, truth, rep, out_dir, control=None):
    d = os.path.join(out_dir, f"{truth}_r{rep}")
    os.makedirs(d, exist_ok=True)
    prompt = build_prompt(net_id, control)
    open(os.path.join(d, "prompt.txt"), "w").write(prompt)
    t0 = time.time()
    res = harness.PROVIDERS[m["provider"]](m, prompt)
    rec = {"exp": 1, "variant": "footprint", "network": net_id, "truth": truth, "rep": rep, "model": m["name"],
           "provider": m["provider"], "model_id": m["model_id"], "reasoning_effort": m.get("reasoning_effort"),
           "thinking_budget": m.get("thinking_budget"), "control": control, "prompt_sha256": sha256(prompt),
           "template_sha256": sha256(open(TEMPLATE).read()), "wall_s": round(time.time() - t0, 1),
           **{k: res[k] for k in ("attempts", "error", "finish_reason", "refused", "usage")}}
    if res["raw"] is not None:
        json.dump(res["raw"], open(os.path.join(d, "response.json"), "w"), indent=1)
    u = res["usage"] or {}
    if m.get("price_in_per_m") is not None and u.get("input") is not None:
        rec["cost_usd"] = round(u["input"] * m["price_in_per_m"] / 1e6
                                + (u["output"] or 0) * m.get("price_out_per_m", 0) / 1e6, 4)
    open(os.path.join(d, "answer.md"), "w").write(res["answer"])
    rec["score"] = harness.score(1, res["answer"], truth) if res["answer"] else None
    json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
    return rec


def report(r):
    s = r["score"] or {}
    return (f"{r['model']:20s} {r['truth']:9s} r{r['rep']}  guess={s.get('guess')!s:9s} correct={s.get('correct')!s:5s} "
            f"conf={s.get('confidence')}  tokens={r.get('usage')}  {r['wall_s']}s"
            + ("  REFUSED" if r["refused"] else "") + (f"  ERROR {r['error']['status']}" if r["error"] else "")
            + ("  NEEDS REVIEW" if s.get("needs_review") else ""))


def run(models, names, reps, control, workers):
    harness.load_env()
    harness.check_keys(models, names)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{control}" if control else "")
    out = {n: os.path.join(HERE, "runs", "footprint", re.sub(r"[^A-Za-z0-9._-]+", "_", n), stamp) for n in names}
    jobs = [(models[n], i, t, r) for n in names for i, t in harness.networks(1).items() for r in range(reps)]
    print(f"{len(jobs)} calls to {', '.join(names)}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        recs = list(pool.map(lambda j: run_one(*j, out[j[0]["name"]], control), jobs))
    for r in recs:
        print(report(r))
    for n in names:
        mine = [r for r in recs if r["model"] == n]
        summary = harness.summarize(mine, [1], models[n].get("price_in_per_m") is not None)
        json.dump({"summary": summary, "runs": mine}, open(os.path.join(out[n], "summary.json"), "w"), indent=1)
        print(f"{n}: {json.dumps(summary)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", help="names from the harness's models.local.toml")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--control", choices=["shuffled"], help="build the tables from the shuffled weights")
    ap.add_argument("--show", metavar="NET", help="print one network's tables (its id or its game)")
    ap.add_argument("--dry-run", action="store_true", help="build every prompt and print its size, call nothing")
    a = ap.parse_args()
    if a.show:
        return print(tables(footprint(first_layer(weights_text(network_id(a.show), a.control)))))
    if a.dry_run:
        for net_id, truth in harness.networks(1).items():
            p = build_prompt(net_id, a.control)
            print(f"{truth:9s} {net_id}  {len(p):,} chars (~{len(p) // 4:,} tokens)  sha256 {sha256(p)[:12]}")
        return
    if not a.models:
        sys.exit("give --models, --show or --dry-run")
    models = harness.load_models(MODELS)
    unknown = [n for n in a.models if n not in models]
    if unknown:
        sys.exit(f"not in {MODELS}: {', '.join(unknown)} (known: {', '.join(models)})")
    run(models, a.models, a.reps, a.control, a.workers)


if __name__ == "__main__":
    main()
