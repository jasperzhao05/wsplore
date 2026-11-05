"""Experiment 5 with the design given: the authors' Breakout prompt, plus part of Astra's own answer to it.
  L0  the authors' prompt, unchanged
  L1  plus Astra's design paragraph (specs/astra_breakout_strategy.txt)
  L2  plus the layout of Astra's edits block with every value left out (specs/astra_breakout_wiring.txt)
Astra's answer (data/exp5/astra_reference in the harness) is from the authors' logs, CC BY 4.0. Each network is
scored with the harness's own code, and compared with Astra's network on states from Astra's own play.

  uv run design.py --level L0 L1 L2 --dry-run                      # build the prompts, call nothing
  uv run design.py --level L0 L1 L2 --models gpt-6.1-sol --reps 3
"""
import argparse, concurrent.futures, datetime, hashlib, json, os, re, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, "..", "weights_editing"))
sys.path.insert(0, HARNESS)
import exp5
import weights_only as harness

GAME = "breakout"
LEVELS = ("L0", "L1", "L2")
MODELS = os.path.join(HARNESS, "models.local.toml")
ASTRA = os.path.join(HARNESS, "data", "exp5", "astra_reference", "breakout.npz")
EFFECT = np.array([0, 1, 0, 3, 0, 0])

GOAL = "plays this game as well as possible."
GOAL_NEW = "plays this game as well as possible, following the design under THE DESIGN."
DESIGN = "THE DESIGN (follow it; every number is yours to choose):\n\n{strategy}\n\n"
LAYOUT = "The network's layout, as an edits block with each value left out:\n\n```\n{wiring}```\n\n"


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def spec(name):
    return open(os.path.join(HERE, "specs", f"astra_breakout_{name}.txt")).read()


def build_prompt(level):
    original = exp5.prompt(GAME)
    if level == "L0":
        return original
    if original.count(GOAL) != 1 or original.count("THE NETWORK (") != 1:
        raise ValueError("the authors' prompt is not in the expected form")
    section = DESIGN.format(strategy=spec("strategy").strip())
    if level == "L2":
        section += LAYOUT.format(wiring=spec("wiring"))
    return original.replace(GOAL, GOAL_NEW, 1).replace("THE NETWORK (", section + "THE NETWORK (", 1)


def channel_map(env):
    names = env.env.channels
    m = np.zeros((len(names), 6), np.float32)
    for c, sources in enumerate(exp5.CHANNELS[GAME]):
        for s in sources:
            m[names[s], c] = 1
    return m


def observe(env, m):
    return (env.state().astype(np.float32) @ m > 0).reshape(600).astype(np.float32)


def effects(net, x):
    """Probability of each effect (no-op, left, right) for a batch of observations."""
    h = np.tanh(x @ net["W1"] + net["b1"])
    h = np.tanh(h @ net["W2"] + net["b2"])
    z = (h @ net["W3"] + net["b3"]).astype(np.float64)
    p = np.exp(z - z.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    return np.stack([p[:, [0, 2, 4, 5]].sum(1), p[:, 1], p[:, 3]], 1)


def network_policy(net):
    return lambda x: (0, 1, 3)[int(effects(net, x[None])[0].argmax())]


def play(act, ids, seed, every=0):
    """Play the given episodes with a policy, seeded like the harness's evaluator. Returns (score, length) per
    episode and, if every > 0, every n-th observation with the policy's action."""
    results, states, actions = [], [], []
    for i in ids:
        env = exp5.make_env(GAME)
        m = channel_map(env)
        env.seed(seed * 1_000_003 + i)
        env.reset()
        score, steps, done = 0.0, 0, False
        while not done and steps < 10_000:
            x = observe(env, m)
            a = act(x)
            if every and steps % every == 0:
                states.append(x.astype(np.uint8))
                actions.append(a)
            r, done = env.act(a)
            score += r
            steps += 1
        results.append((score, steps))
    return results, states, actions


def reference_states(act, episodes=30, every=10, seed=1):
    _, states, actions = play(act, range(episodes), seed, every)
    return np.array(states, np.float32), np.array(actions)


def agreement(net, states, actions):
    p = effects(net, states)
    target = np.searchsorted([0, 1, 3], EFFECT[actions])
    return {"argmax": float(np.mean(p.argmax(1) == target)),
            "sampled": float(np.mean(p[np.arange(len(target)), target])), "states": int(len(target))}


def ask(m, level, rep, out_dir, prompt):
    m = exp5.for_exp5(m)
    d = os.path.join(out_dir, f"{GAME}_r{rep}")
    os.makedirs(d, exist_ok=True)
    t0 = time.time()
    res = harness.PROVIDERS[m["provider"]](m, prompt)
    rec = {"exp": 5, "variant": "design", "level": level, "game": GAME, "rep": rep, "model": m["name"],
           "provider": m["provider"], "model_id": m["model_id"], "reasoning_effort": m.get("reasoning_effort"),
           "thinking_budget": m.get("thinking_budget"), "prompt_sha256": sha256(prompt),
           "wall_s": round(time.time() - t0, 1),
           **{k: res[k] for k in ("attempts", "error", "finish_reason", "refused", "usage")}}
    if res["raw"] is not None:
        json.dump(res["raw"], open(os.path.join(d, "response.json"), "w"), indent=1)
    u = res["usage"] or {}
    if m.get("price_in_per_m") is not None and u.get("input") is not None:
        rec["cost_usd"] = round(u["input"] * m["price_in_per_m"] / 1e6
                                + (u["output"] or 0) * m.get("price_out_per_m", 0) / 1e6, 4)
    open(os.path.join(d, "answer.md"), "w").write(res["answer"])
    net, rec["edits"] = exp5.parse_edits(res["answer"])
    np.savez(os.path.join(d, "net.npz"), **{exp5.NPZ_NAMES[k]: v for k, v in net.items()})
    json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
    return rec, net, d


def run(models, names, levels, reps, workers, episodes):
    harness.load_env()
    harness.check_keys(models, names)
    prompts = {lv: build_prompt(lv) for lv in levels}
    ref = reference_states(network_policy(exp5.load_npz(ASTRA)))
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = {(lv, n): os.path.join(HERE, "runs", "design", lv, re.sub(r"[^A-Za-z0-9._-]+", "_", n), stamp)
           for lv in levels for n in names}
    jobs = [(models[n], lv, r) for lv in levels for n in names for r in range(reps)]
    print(f"{len(jobs)} calls to {', '.join(names)}", flush=True)
    recs = []
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(ask, m, lv, r, out[(lv, m["name"])], prompts[lv]) for m, lv, r in jobs]
        for f in concurrent.futures.as_completed(futures):
            try:
                rec, net, d = f.result()
            except Exception as ex:
                print(f"call failed: {ex!r}", flush=True)
                continue
            written = not rec["error"] and rec["edits"]["applied"]
            rec["eval"] = exp5.evaluate(net, GAME, episodes) if written else None
            rec["agreement"] = agreement(net, *ref) if written else None
            json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
            recs.append(rec)
            ev, ag = rec["eval"] or {}, rec["agreement"] or {}
            print(f"{rec['level']} {rec['model']:20s} r{rec['rep']}  score={ev.get('mean')}  "
                  f"agreement={ag.get('argmax')}  edits {rec['edits']['applied']}/{rec['edits']['statements']}  "
                  f"tokens={rec['usage']}  {rec['wall_s']}s  finish={rec['finish_reason']}"
                  + (f"  ERROR {rec['error']['status']}" if rec["error"] else "")
                  + ("  CUT OFF" if rec["edits"]["cut_off"] else ""), flush=True)
    for (lv, n), d in out.items():
        mine = sorted((r for r in recs if r["model"] == n and r["level"] == lv), key=lambda r: r["rep"])
        summary = {"scores": [(r["eval"] or {}).get("mean") for r in mine],
                   "agreement": [(r["agreement"] or {}).get("argmax") for r in mine]}
        if models[n].get("price_in_per_m") is not None:
            summary["cost_usd"] = round(sum(r.get("cost_usd", 0) for r in mine), 4)
        json.dump({"summary": summary, "runs": mine}, open(os.path.join(d, "summary.json"), "w"), indent=1)
        print(f"{lv} {n}: {json.dumps(summary)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", nargs="+", choices=LEVELS)
    ap.add_argument("--models", nargs="+", help="names from the harness's models.local.toml")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--episodes", type=int, default=1000)
    ap.add_argument("--dry-run", action="store_true", help="build each prompt and show its size, call nothing")
    a = ap.parse_args()
    if not a.level:
        sys.exit("give --level")
    if a.dry_run:
        for lv in a.level:
            text = build_prompt(lv)
            print(f"{lv} {len(text):,} chars (~{len(text) // 4:,} tokens)  sha256 {sha256(text)[:12]}")
        return
    if not a.models:
        sys.exit("give --models or --dry-run")
    models = harness.load_models(MODELS)
    unknown = [n for n in a.models if n not in models]
    if unknown:
        sys.exit(f"not in {MODELS}: {', '.join(unknown)} (known: {', '.join(models)})")
    run(models, a.models, a.level, a.reps, a.workers, a.episodes)


if __name__ == "__main__":
    main()
