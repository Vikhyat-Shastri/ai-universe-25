#!/usr/bin/env python3
"""
Full real-LLM experiment with diverse topics + automatic plot generation.

Runs experiments across:
  - Multiple real wiki topics
  - Governance on/off
  - Real LLM only (no simulated backend)

After all runs complete, generates 6 paper-relevant figures from the results.

All output saved under results/:
  results/real_llm_experiment.json    -- aggregated JSON
  results/real_llm_runs/              -- per-run artifacts + ledger
  results/figures/real_topics/        -- PNG plots (300 DPI)

Usage:
    python scripts/run_real_experiment.py
    python scripts/run_real_experiment.py --topics 3 --rounds 10   # quick test
    python scripts/run_real_experiment.py --topics 10 --rounds 30  # thorough
    python scripts/run_real_experiment.py --model qwen2.5:7b       # bigger model
"""

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Ensure Ollama is reachable before doing anything ──────────────────
def ensure_ollama(model: str):
    """Check Ollama is running and the requested model is available."""
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=5)
        resp.raise_for_status()
        available = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        print("ERROR: Ollama is not running. Start it with:  ollama serve")
        sys.exit(1)

    if model not in available:
        print(f"Model '{model}' not found locally. Pulling it now...")
        subprocess.run(["ollama", "pull", model], check=True)
        print(f"Pulled {model} successfully.")

# ── Imports (after path setup) ────────────────────────────────────────
from ai_universe25.agents.llm_backends import OllamaBackend
from ai_universe25.experiments.runner import (
    Cohort,
    ExperimentConfig,
    ExperimentRunner,
    GovernanceLevel,
    Regime,
    STOPSchedule,
)

TOPICS = [
    "CRISPR Gene Editing",
    "The Byzantine Empire",
    "Quantum Computing",
    "Climate Change Mitigation Strategies",
    "The History of the Silk Road",
    "Artificial Neural Networks",
    "The French Revolution",
    "Antibiotic Resistance",
    "Black Holes and Hawking Radiation",
    "The Economics of Universal Basic Income",
]

RESULTS_DIR = Path(__file__).parent.parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures" / "real_topics"


# =====================================================================
# PART 1: Experiment runner
# =====================================================================

def run_one(backend, topic, governance, num_rounds, density, seed, output_dir):
    safe_topic = topic.lower().replace(" ", "_")[:30]
    run_id = f"{safe_topic}_{governance.value}_s{seed}"

    config = ExperimentConfig(
        run_id=run_id,
        regime=Regime.SCARCITY,
        density=density,
        governance=governance,
        stop_schedule=STOPSchedule.SCORE_TRIGGERED,
        cohort=Cohort.BASE,
        seed=seed,
        num_rounds=num_rounds,
        topic=topic,
    )

    runner = ExperimentRunner(output_dir=output_dir, seed=seed, llm_backend=backend)
    t0 = time.time()
    result = runner.run_experiment(config)
    elapsed = time.time() - t0

    psi = np.array(result.psi_scores)
    psi_max_arr = np.array(result.artifacts.get("psi_max_per_round", [0.0]))
    avg_quality = result.artifacts.get("avg_quality_per_agent", {})

    return {
        "topic": topic,
        "governance": governance.value,
        "seed": seed,
        "num_rounds": num_rounds,
        "density": density,
        "elapsed_sec": round(elapsed, 1),
        "psi_mean": round(float(np.mean(psi)), 4),
        "psi_std": round(float(np.std(psi)), 4),
        "psi_max_trajectory": [round(float(v), 4) for v in psi_max_arr],
        "psi_max_final": round(float(psi_max_arr[-1]), 4),
        "psi_max_peak": round(float(np.max(psi_max_arr)), 4),
        "n_shutdowns": len(result.shutdown_events),
        "ledger_entries": result.artifacts.get("ledger_entries", 0),
        "ladder_state": result.artifacts.get("final_ladder_state", "?"),
        "avg_quality_per_agent": {k: round(v, 4) for k, v in avg_quality.items()},
        "quality_mean": round(float(np.mean(list(avg_quality.values()))), 4) if avg_quality else 0.0,
        "quality_spread": round(
            float(np.max(list(avg_quality.values())) - np.min(list(avg_quality.values()))), 4
        ) if avg_quality else 0.0,
    }


def print_table(results):
    ok = [r for r in results if "error" not in r]
    if not ok:
        print("No successful runs to display.")
        return

    print("\n" + "=" * 115)
    print("EXPERIMENT RESULTS  (Real LLM — all topics)")
    print("=" * 115)
    print(f"{'Topic':<35} {'Gov':<6} {'PSI_peak':>9} {'Quality':>8} "
          f"{'Spread':>7} {'Ladder':>10} {'Time':>7}")
    print("-" * 115)

    for r in ok:
        print(f"{r['topic'][:33]:<35} {r['governance']:<6} "
              f"{r['psi_max_peak']:>9.4f} {r['quality_mean']:>8.4f} "
              f"{r['quality_spread']:>7.4f} {r['ladder_state']:>10} "
              f"{r['elapsed_sec']:>6.0f}s")

    off = [r for r in ok if r["governance"] == "off"]
    rbac = [r for r in ok if r["governance"] == "rbac"]
    if off and rbac:
        print("\n--- Aggregate ---")
        fmt = "  {:<22} OFF={:.4f}   RBAC={:.4f}   delta={:+.4f}"
        print(fmt.format("Mean PSI_max_peak:",
              np.mean([r["psi_max_peak"] for r in off]),
              np.mean([r["psi_max_peak"] for r in rbac]),
              np.mean([r["psi_max_peak"] for r in rbac]) - np.mean([r["psi_max_peak"] for r in off])))
        print(fmt.format("Mean Quality:",
              np.mean([r["quality_mean"] for r in off]),
              np.mean([r["quality_mean"] for r in rbac]),
              np.mean([r["quality_mean"] for r in rbac]) - np.mean([r["quality_mean"] for r in off])))
        off_l = [r["ladder_state"] for r in off]
        rbac_l = [r["ladder_state"] for r in rbac]
        print(f"  Ladder (OFF):  {dict((s, off_l.count(s)) for s in set(off_l))}")
        print(f"  Ladder (RBAC): {dict((s, rbac_l.count(s)) for s in set(rbac_l))}")


# =====================================================================
# PART 2: Plot generation (reads the saved JSON, no LLM calls)
# =====================================================================

def generate_plots(results: List[Dict]):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme(style="whitegrid", font_scale=1.1)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ok = [r for r in results if "error" not in r]
    if not ok:
        print("  No data to plot.")
        return

    topics = sorted(set(r["topic"] for r in ok))
    off = [r for r in ok if r["governance"] == "off"]
    rbac = [r for r in ok if r["governance"] == "rbac"]

    # ── Fig 1: PSI_max trajectories per topic, governance off vs rbac ─
    n_topics = len(topics)
    cols = min(3, n_topics)
    rows = math.ceil(n_topics / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows), squeeze=False)

    for idx, topic in enumerate(topics):
        ax = axes[idx // cols][idx % cols]
        for r in ok:
            if r["topic"] != topic:
                continue
            traj = r["psi_max_trajectory"]
            gov = r["governance"]
            color = "#2196F3" if gov == "off" else "#E91E63"
            marker = "o" if gov == "off" else "s"
            ax.plot(traj, f"-{marker}", color=color, markersize=4, linewidth=1.5,
                    label=f"{'OFF' if gov == 'off' else 'RBAC'}", alpha=0.85)
        ax.set_title(topic[:28], fontsize=10)
        ax.set_xlabel("Round")
        ax.set_ylabel("PSI$_{\\mathrm{max}}$")
        ax.legend(fontsize=8, frameon=True)
        ax.set_ylim(0.4, 0.85)
        ax.axhline(y=0.5, color="gray", linestyle=":", alpha=0.4)

    for idx in range(n_topics, rows * cols):
        axes[idx // cols][idx % cols].set_visible(False)
    fig.suptitle("Figure 1: PSI$_{\\mathrm{max}}$ Trajectories by Topic", fontsize=14, y=1.01)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "real_fig1_psi_trajectories.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved real_fig1_psi_trajectories.png")

    # ── Fig 2: Per-agent quality by topic ─────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, max(4, 0.6 * n_topics)), sharey=True)
    for ax, gov_label, subset in [
        (axes[0], "Governance OFF", off),
        (axes[1], "Governance RBAC", rbac),
    ]:
        topic_labels = []
        agent_names = None
        matrix = []
        for r in sorted(subset, key=lambda x: x["topic"]):
            aq = r.get("avg_quality_per_agent", {})
            if not aq:
                continue
            if agent_names is None:
                agent_names = [k.split("_")[0].capitalize() for k in aq.keys()]
            matrix.append(list(aq.values()))
            topic_labels.append(r["topic"][:25])

        if matrix:
            mat = np.array(matrix)
            im = ax.imshow(mat, aspect="auto", vmin=0, vmax=1, cmap="RdYlGn")
            ax.set_yticks(range(len(topic_labels)))
            ax.set_yticklabels(topic_labels, fontsize=9)
            ax.set_xticks(range(len(agent_names)))
            ax.set_xticklabels(agent_names, fontsize=9, rotation=45, ha="right")
            for i in range(mat.shape[0]):
                for j in range(mat.shape[1]):
                    ax.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if mat[i,j] < 0.4 else "black")
        ax.set_title(gov_label)

    fig.colorbar(im, ax=axes, shrink=0.6, label="CQP Quality Score")
    fig.suptitle("Figure 2: Per-Agent Quality by Topic", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "real_fig2_quality_by_topic.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved real_fig2_quality_by_topic.png")

    # ── Fig 3: Ladder outcomes bar chart ──────────────────────────────
    state_order = ["RUN", "WARN", "STOP", "QUARANTINE", "SHUTDOWN"]
    state_colors = {"RUN": "#4CAF50", "WARN": "#FF9800", "STOP": "#F44336",
                    "QUARANTINE": "#9C27B0", "SHUTDOWN": "#212121"}

    fig, axes = plt.subplots(1, 2, figsize=(12, max(3, 0.5 * n_topics)), sharey=True)
    for ax, gov_label, subset in [
        (axes[0], "Governance OFF", off),
        (axes[1], "Governance RBAC", rbac),
    ]:
        sorted_sub = sorted(subset, key=lambda x: x["topic"])
        labels = [r["topic"][:25] for r in sorted_sub]
        states = [r["ladder_state"] for r in sorted_sub]
        positions = [state_order.index(s) if s in state_order else 0 for s in states]
        colors = [state_colors.get(s, "#999") for s in states]

        bars = ax.barh(labels, positions, color=colors, edgecolor="white", height=0.6)
        for bar, s in zip(bars, states):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    s, va="center", fontweight="bold", fontsize=9)
        ax.set_xticks(range(len(state_order)))
        ax.set_xticklabels(state_order, fontsize=8)
        ax.set_title(gov_label)

    fig.suptitle("Figure 3: Final Ladder State by Topic and Governance", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "real_fig3_ladder_outcomes.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved real_fig3_ladder_outcomes.png")

    # ── Fig 4: PSI_max peak comparison (off vs rbac, per topic) ──────
    if off and rbac:
        fig, ax = plt.subplots(figsize=(10, max(4, 0.5 * n_topics)))
        topic_list = sorted(set(r["topic"] for r in off))
        y = np.arange(len(topic_list))
        off_vals = [next((r["psi_max_peak"] for r in off if r["topic"] == t), 0) for t in topic_list]
        rbac_vals = [next((r["psi_max_peak"] for r in rbac if r["topic"] == t), 0) for t in topic_list]

        height = 0.35
        ax.barh(y - height/2, off_vals, height, label="OFF", color="#2196F3", alpha=0.85)
        ax.barh(y + height/2, rbac_vals, height, label="RBAC", color="#E91E63", alpha=0.85)
        ax.set_yticks(y)
        ax.set_yticklabels([t[:28] for t in topic_list], fontsize=9)
        ax.set_xlabel("PSI$_{\\mathrm{max}}$ (peak)")
        ax.legend(frameon=True)
        ax.axvline(x=0.5, color="gray", linestyle=":", alpha=0.5)
        ax.set_title("Figure 4: PSI$_{\\mathrm{max}}$ Peak by Topic")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "real_fig4_psi_peak_by_topic.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved real_fig4_psi_peak_by_topic.png")

    # ── Fig 5: Tail mass curves (aggregated across topics) ───────────
    from ai_universe25.analytics.reports import FiniteSizeScaling, ReportConfig
    cfg = ReportConfig(output_dir=FIGURES_DIR)
    fss = FiniteSizeScaling(cfg)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for gov_label, subset, color in [("OFF", off, "#2196F3"), ("RBAC", rbac, "#E91E63")]:
        all_psi = []
        for r in subset:
            all_psi.extend(r["psi_max_trajectory"])
        if all_psi:
            thresholds, tail = fss.compute_tail_mass(np.array(all_psi))
            axes[0].plot(thresholds, tail, "-", label=gov_label, color=color, linewidth=2)

    axes[0].set_xlabel("Threshold $\\rho$")
    axes[0].set_ylabel("$T(\\rho) = \\Pr(\\mathrm{PSI}_{\\mathrm{max}} > \\rho)$")
    axes[0].set_title("Tail Mass Curves")
    axes[0].legend(frameon=True)

    # Governance elasticity per topic
    if off and rbac:
        from ai_universe25.analytics.reports import GovernanceElasticity
        ge = GovernanceElasticity(cfg)
        elas_data = []
        for t in topics:
            r_off = next((r for r in off if r["topic"] == t), None)
            r_rbac = next((r for r in rbac if r["topic"] == t), None)
            if r_off and r_rbac:
                psi_pre = np.array(r_off["psi_max_trajectory"])
                psi_post = np.array(r_rbac["psi_max_trajectory"])
                e = ge.compute_elasticity(psi_pre, psi_post)
                elas_data.append((t[:20], e["elasticity"], e["effect_size_cohens_d"]))

        if elas_data:
            labels_, elas_, cohd_ = zip(*elas_data)
            x_ = np.arange(len(labels_))
            w = 0.35
            axes[1].bar(x_ - w/2, elas_, w, label="Elasticity", color="#2196F3")
            axes[1].bar(x_ + w/2, cohd_, w, label="Cohen's $d$", color="#FF9800")
            axes[1].set_xticks(x_)
            axes[1].set_xticklabels(labels_, fontsize=7, rotation=45, ha="right")
            axes[1].axhline(y=0, color="black", linewidth=0.5)
            axes[1].legend(frameon=True, fontsize=8)
            axes[1].set_title("Governance Elasticity per Topic")

    fig.suptitle("Figure 5: Tail Mass & Governance Elasticity", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "real_fig5_tail_mass.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved real_fig5_tail_mass.png")

    # ── Fig 6: Governance contrast summary ────────────────────────────
    if off and rbac:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # 6a: quality mean
        off_q = [r["quality_mean"] for r in sorted(off, key=lambda x: x["topic"])]
        rbac_q = [r["quality_mean"] for r in sorted(rbac, key=lambda x: x["topic"])]
        t_labels = [r["topic"][:20] for r in sorted(off, key=lambda x: x["topic"])]
        x = np.arange(len(t_labels))
        axes[0].bar(x - 0.2, off_q, 0.4, label="OFF", color="#2196F3")
        axes[0].bar(x + 0.2, rbac_q, 0.4, label="RBAC", color="#E91E63")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(t_labels, fontsize=7, rotation=45, ha="right")
        axes[0].set_ylabel("Mean CQP Quality")
        axes[0].legend(fontsize=8)
        axes[0].set_title("Quality by Topic")

        # 6b: PSI peak
        off_p = [r["psi_max_peak"] for r in sorted(off, key=lambda x: x["topic"])]
        rbac_p = [r["psi_max_peak"] for r in sorted(rbac, key=lambda x: x["topic"])]
        axes[1].bar(x - 0.2, off_p, 0.4, label="OFF", color="#2196F3")
        axes[1].bar(x + 0.2, rbac_p, 0.4, label="RBAC", color="#E91E63")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(t_labels, fontsize=7, rotation=45, ha="right")
        axes[1].set_ylabel("PSI$_{\\mathrm{max}}$ Peak")
        axes[1].legend(fontsize=8)
        axes[1].set_title("PSI Peak by Topic")

        # 6c: ladder state counts
        state_counts = {}
        for gov_label, subset in [("OFF", off), ("RBAC", rbac)]:
            counts = {}
            for r in subset:
                s = r["ladder_state"]
                counts[s] = counts.get(s, 0) + 1
            state_counts[gov_label] = counts

        all_states = sorted(set(s for c in state_counts.values() for s in c))
        x_s = np.arange(len(all_states))
        for i, (gov_label, color) in enumerate([("OFF", "#2196F3"), ("RBAC", "#E91E63")]):
            vals = [state_counts[gov_label].get(s, 0) for s in all_states]
            axes[2].bar(x_s + (i - 0.5) * 0.4, vals, 0.4, label=gov_label, color=color)
        axes[2].set_xticks(x_s)
        axes[2].set_xticklabels(all_states, fontsize=9)
        axes[2].set_ylabel("Count (# topics)")
        axes[2].legend(fontsize=8)
        axes[2].set_title("Ladder State Distribution")

        fig.suptitle("Figure 6: Governance Contrast Summary", fontsize=14)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "real_fig6_governance_contrast.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved real_fig6_governance_contrast.png")


# =====================================================================
# PART 3: Main
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Universe 25 -- Real LLM experiment with plots")
    parser.add_argument("--model", default="qwen2.5:3b",
                        help="Ollama model (default: qwen2.5:3b)")
    parser.add_argument("--rounds", type=int, default=15,
                        help="Rounds per experiment (default: 15)")
    parser.add_argument("--density", type=int, default=4,
                        help="Number of agents (default: 4)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--topics", type=int, default=5,
                        help="Number of topics (default: 5, max: 10)")
    parser.add_argument("--governance", nargs="*", default=["off", "rbac"],
                        help="Governance levels (default: off rbac)")
    args = parser.parse_args()

    # ── Preflight ─────────────────────────────────────────────────────
    ensure_ollama(args.model)

    topics = TOPICS[:min(args.topics, len(TOPICS))]
    gov_levels = [GovernanceLevel(g) for g in args.governance]
    total_runs = len(topics) * len(gov_levels)
    est_per_run = args.rounds * args.density * 10
    est_total = timedelta(seconds=int(total_runs * est_per_run))

    print("=" * 60)
    print("AI Universe 25 -- Real LLM Experiment")
    print("=" * 60)
    print(f"Model:       {args.model} (Ollama)")
    print(f"Topics:      {len(topics)}")
    for i, t in enumerate(topics):
        print(f"  {i+1}. {t}")
    print(f"Governance:  {[g.value for g in gov_levels]}")
    print(f"Rounds:      {args.rounds}")
    print(f"Density:     {args.density} agents")
    print(f"Seed:        {args.seed}")
    print(f"Total runs:  {total_runs}")
    print(f"Est. time:   {est_total}")
    print("=" * 60, flush=True)

    backend = OllamaBackend(model=args.model)
    output_dir = RESULTS_DIR / "real_llm_runs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Run experiments ───────────────────────────────────────────────
    all_results = []
    start_time = time.time()

    for topic in topics:
        for gov in gov_levels:
            print(f"\n>> {topic} / {gov.value}", flush=True)
            try:
                result = run_one(
                    backend=backend, topic=topic, governance=gov,
                    num_rounds=args.rounds, density=args.density,
                    seed=args.seed, output_dir=output_dir,
                )
                all_results.append(result)
                print(f"   Done in {result['elapsed_sec']:.0f}s | "
                      f"Quality={result['quality_mean']:.3f} | "
                      f"PSI_peak={result['psi_max_peak']:.3f} | "
                      f"Ladder={result['ladder_state']}", flush=True)
            except Exception as e:
                print(f"   FAILED: {e}", flush=True)
                all_results.append({
                    "topic": topic, "governance": gov.value, "error": str(e)
                })

            done = len(all_results)
            elapsed = time.time() - start_time
            if done > 0:
                eta = timedelta(seconds=int((total_runs - done) * elapsed / done))
            else:
                eta = "?"
            print(f"   [{done}/{total_runs}] elapsed={timedelta(seconds=int(elapsed))} "
                  f"ETA={eta}", flush=True)

    total_time = time.time() - start_time
    print(f"\n\nTotal experiment time: {timedelta(seconds=int(total_time))}")

    # ── Print table ───────────────────────────────────────────────────
    print_table(all_results)

    # ── Save JSON ─────────────────────────────────────────────────────
    output_file = RESULTS_DIR / "real_llm_experiment.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {output_file}")

    # ── Generate plots ────────────────────────────────────────────────
    print(f"\nGenerating plots...")
    generate_plots(all_results)
    print(f"\nAll plots saved to {FIGURES_DIR}/")
    for f in sorted(FIGURES_DIR.glob("*.png")):
        print(f"  {f.name}")

    # ── Token usage ───────────────────────────────────────────────────
    if hasattr(backend, "usage_summary"):
        u = backend.usage_summary
        print(f"\nLLM calls: {u.get('calls', 0)}")

    print("\nDone.")


if __name__ == "__main__":
    main()
