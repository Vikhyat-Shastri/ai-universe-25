#!/usr/bin/env python3
"""
Generate all paper-relevant figures from experiment results.

Produces:
  1. PSI max trajectory: simulated vs real LLM, governance on/off
  2. Per-agent quality heatmap
  3. Governance ladder state comparison
  4. PSI component radar chart
  5. Finite-size scaling: tail mass T(rho; N)
  6. Binder cumulant crossing
  7. Governance elasticity bar chart
"""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1.1)

RESULTS_DIR = Path(__file__).parent.parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

CLOSED_LOOP = Path(__file__).parent.parent / "closed_loop_results.json"

from ai_universe25.agents.base import SimulatedLLMBackend
from ai_universe25.analytics.reports import FiniteSizeScaling, GovernanceElasticity, ReportConfig
from ai_universe25.experiments.runner import *


def load_closed_loop():
    with open(CLOSED_LOOP) as f:
        return json.load(f)


# ── Fig 1: PSI_max trajectory ──────────────────────────────────────────
def fig_psi_trajectory(data):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)

    for ax, backend_label in zip(axes, ["simulated", "qwen2.5:3b"]):
        for r in data:
            if r["backend"] != backend_label:
                continue
            gov = r["governance"]
            style = "-o" if gov == "off" else "-s"
            color = "#2196F3" if gov == "off" else "#E91E63"
            label = f"Governance {'OFF' if gov == 'off' else 'RBAC'}"
            ax.plot(r["psi_max"], style, label=label, color=color, markersize=6, linewidth=2)

        ax.set_xlabel("Round")
        ax.set_ylabel("PSI$_{\\mathrm{max}}$ (highest-scoring agent)")
        title = "Simulated Backend" if backend_label == "simulated" else "Qwen 2.5 3B (Real LLM)"
        ax.set_title(title)
        ax.legend(frameon=True)
        ax.set_ylim(0.4, 0.8)
        ax.axhline(y=0.5, color="gray", linestyle=":", alpha=0.5)

    fig.suptitle("Figure 1: PSI$_{\\mathrm{max}}$ Trajectory by Backend and Governance", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_psi_trajectory.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved fig1_psi_trajectory.png")


# ── Fig 2: Per-agent quality heatmap ───────────────────────────────────
def fig_quality_heatmap(data):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    titles = []
    for i, r in enumerate(data):
        ax = axes[i // 2][i % 2]
        agents = list(r["avg_quality"].keys())
        scores = list(r["avg_quality"].values())
        role_labels = [a.split("_")[0].capitalize() for a in agents]

        colors = ["#4CAF50" if s >= 0.7 else "#FF9800" if s >= 0.5 else "#F44336" for s in scores]
        bars = ax.barh(role_labels, scores, color=colors, edgecolor="white", linewidth=0.5)

        for bar, score in zip(bars, scores):
            ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f"{score:.3f}", va="center", fontsize=10)

        ax.set_xlim(0, 1.0)
        ax.set_xlabel("CQP Quality Score")
        title = f"{r['backend']} / {'OFF' if r['governance'] == 'off' else 'RBAC'}"
        ax.set_title(title)
        ax.axvline(x=0.7, color="green", linestyle="--", alpha=0.3, label="RUN threshold")
        ax.axvline(x=0.5, color="orange", linestyle="--", alpha=0.3, label="STOP threshold")

    fig.suptitle("Figure 2: Per-Agent Content Quality (CQP Scores)", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_quality_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved fig2_quality_heatmap.png")


# ── Fig 3: Ladder state comparison ─────────────────────────────────────
def fig_ladder_states(data):
    state_order = ["RUN", "WARN", "STOP", "QUARANTINE", "SHUTDOWN"]
    state_colors = {
        "RUN": "#4CAF50", "WARN": "#FF9800", "STOP": "#F44336",
        "QUARANTINE": "#9C27B0", "SHUTDOWN": "#212121",
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    labels = []
    positions = []
    colors = []
    for i, r in enumerate(data):
        label = f"{r['backend']}\n{'OFF' if r['governance'] == 'off' else 'RBAC'}"
        labels.append(label)
        state = r["ladder"]
        positions.append(state_order.index(state))
        colors.append(state_colors[state])

    bars = ax.barh(labels, positions, color=colors, edgecolor="white", height=0.5)
    for bar, r in zip(bars, data):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                r["ladder"], va="center", fontweight="bold", fontsize=12)

    ax.set_xticks(range(len(state_order)))
    ax.set_xticklabels(state_order)
    ax.set_xlabel("Governance Ladder State")
    ax.set_title("Figure 3: Final Ladder State by Condition")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_ladder_states.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved fig3_ladder_states.png")


# ── Fig 4: Factorial sweep PSI_max across densities ───────────────────
def fig_factorial_sweep():
    results_by_density = {}
    with tempfile.TemporaryDirectory() as d:
        runner = ExperimentRunner(output_dir=Path(d), seed=42)
        for density in [4, 8, 12]:
            for gov in [GovernanceLevel.OFF, GovernanceLevel.RBAC]:
                config = ExperimentConfig(
                    run_id=f"d{density}_{gov.value}", regime=Regime.SCARCITY,
                    density=density, governance=gov, stop_schedule=STOPSchedule.NONE,
                    cohort=Cohort.BASE, seed=42, num_rounds=25,
                )
                result = runner.run_experiment(config)
                psi_max = result.artifacts.get("psi_max_per_round", [])
                key = f"N={density}, {'OFF' if gov == GovernanceLevel.OFF else 'RBAC'}"
                results_by_density[key] = psi_max

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = {"N=4": "#2196F3", "N=8": "#4CAF50", "N=12": "#FF9800"}
    for key, psi_max in results_by_density.items():
        n_str = key.split(",")[0]
        style = "-" if "OFF" in key else "--"
        ax.plot(psi_max, style, label=key, color=colors[n_str], linewidth=2, alpha=0.8)

    ax.set_xlabel("Round")
    ax.set_ylabel("PSI$_{\\mathrm{max}}$")
    ax.set_title("Figure 4: PSI$_{\\mathrm{max}}$ by Agent Density and Governance")
    ax.legend(ncol=2, frameon=True)
    ax.set_ylim(0.4, 0.85)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_factorial_density.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved fig4_factorial_density.png")
    return results_by_density


# ── Fig 5: Finite-size scaling / tail mass ─────────────────────────────
def fig_tail_mass(results_by_density):
    cfg = ReportConfig(output_dir=FIGURES_DIR)
    fss = FiniteSizeScaling(cfg)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    psi_by_size = {}
    for key, vals in results_by_density.items():
        if "OFF" in key:
            n = int(key.split("=")[1].split(",")[0])
            psi_by_size[n] = np.array(vals)

    colors = {4: "#2196F3", 8: "#4CAF50", 12: "#FF9800"}
    for N, psi in psi_by_size.items():
        thresholds, tail = fss.compute_tail_mass(psi)
        axes[0].plot(thresholds, tail, "-", label=f"N={N}", color=colors[N], linewidth=2)

    axes[0].set_xlabel("Threshold $\\rho$")
    axes[0].set_ylabel("$T(\\rho; N) = \\Pr(\\mathrm{PSI} > \\rho)$")
    axes[0].set_title("Tail Mass Curves")
    axes[0].legend(frameon=True)

    # Binder cumulant
    binder_vals = {}
    for N, psi in psi_by_size.items():
        U = fss.binder_cumulant(psi)
        binder_vals[N] = U

    sizes = sorted(binder_vals.keys())
    Us = [binder_vals[n] for n in sizes]
    axes[1].plot(sizes, Us, "-o", color="#E91E63", linewidth=2, markersize=8)
    axes[1].set_xlabel("System Size $N$")
    axes[1].set_ylabel("Binder Cumulant $U$")
    axes[1].set_title("Binder Cumulant vs. System Size")

    fig.suptitle("Figure 5: Finite-Size Scaling Analysis", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_finite_size_scaling.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved fig5_finite_size_scaling.png")


# ── Fig 6: Governance elasticity ───────────────────────────────────────
def fig_governance_elasticity():
    cfg = ReportConfig(output_dir=FIGURES_DIR)
    ge = GovernanceElasticity(cfg)

    conditions = {}
    with tempfile.TemporaryDirectory() as d:
        runner = ExperimentRunner(output_dir=Path(d), seed=42)
        for gov in [GovernanceLevel.OFF, GovernanceLevel.RBAC, GovernanceLevel.RBAC_QUORUM_PROVENANCE_FAIR]:
            config = ExperimentConfig(
                run_id=f"elast_{gov.value}", regime=Regime.SCARCITY, density=8,
                governance=gov, stop_schedule=STOPSchedule.NONE,
                cohort=Cohort.BASE, seed=42, num_rounds=30,
            )
            result = runner.run_experiment(config)
            psi_max = np.array(result.artifacts.get("psi_max_per_round", [0.5]))
            conditions[gov.value] = psi_max

    off = conditions["off"]
    elasticities = {}
    for gov_name, psi_arr in conditions.items():
        if gov_name == "off":
            continue
        result = ge.compute_elasticity(off, psi_arr)
        elasticities[gov_name] = result

    fig, ax = plt.subplots(figsize=(8, 5))
    names = list(elasticities.keys())
    nice_names = {"rbac": "RBAC Only", "rbac_quorum_provenance_fair": "RBAC + Quorum\n+ Provenance\n+ Fair Sched."}
    labels = [nice_names.get(n, n) for n in names]
    elas_vals = [elasticities[n]["elasticity"] for n in names]
    d_vals = [elasticities[n]["effect_size_cohens_d"] for n in names]

    x = np.arange(len(names))
    width = 0.35
    ax.bar(x - width/2, elas_vals, width, label="Elasticity", color="#2196F3")
    ax.bar(x + width/2, d_vals, width, label="Cohen's $d$", color="#FF9800")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Value")
    ax.set_title("Figure 6: Governance Elasticity (relative to no-governance baseline)")
    ax.legend(frameon=True)
    ax.axhline(y=0, color="black", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig6_governance_elasticity.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved fig6_governance_elasticity.png")


def main():
    print("Generating paper figures...")
    print()

    data = load_closed_loop()

    fig_psi_trajectory(data)
    fig_quality_heatmap(data)
    fig_ladder_states(data)
    density_results = fig_factorial_sweep()
    fig_tail_mass(density_results)
    fig_governance_elasticity()

    print(f"\nAll figures saved to {FIGURES_DIR}/")
    print("Files:")
    for f in sorted(FIGURES_DIR.glob("*.png")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
