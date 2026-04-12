#!/usr/bin/env python3
"""
Model comparison harness for AI Universe 25.

Runs the same experiment across multiple LLM backends and compares:
- PSI score distributions (mean, std, max)
- Shutdown resistance patterns
- Agent content quality (CQP scores)
- Governance elasticity (PSI with vs without RBAC)
- Per-component breakdown (RC, PO, CC, PS, RP)

Usage:
    # Simulated only (no API keys needed):
    python scripts/compare_models.py

    # With Ollama:
    python scripts/compare_models.py --ollama llama3.1:8b mistral:7b

    # With OpenAI:
    python scripts/compare_models.py --openai gpt-4o-mini gpt-4o

    # Mix everything:
    python scripts/compare_models.py --ollama llama3.1:8b --openai gpt-4o-mini

    # Custom number of rounds/agents:
    python scripts/compare_models.py --rounds 50 --density 8
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_universe25.agents.base import SimulatedLLMBackend
from ai_universe25.experiments.runner import (
    Cohort,
    ExperimentConfig,
    ExperimentRunner,
    GovernanceLevel,
    Regime,
    STOPSchedule,
)


def run_single_experiment(
    backend,
    backend_name: str,
    governance: GovernanceLevel,
    num_rounds: int,
    density: int,
    output_dir: Path,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run a single experiment and return metrics."""
    config = ExperimentConfig(
        run_id=f"{backend_name}_{governance.value}",
        regime=Regime.SCARCITY,
        density=density,
        governance=governance,
        stop_schedule=STOPSchedule.NONE,
        cohort=Cohort.BASE,
        seed=seed,
        num_rounds=num_rounds,
        topic="Artificial Intelligence Safety",
    )

    runner = ExperimentRunner(output_dir=output_dir, seed=seed, llm_backend=backend)
    t0 = time.time()
    result = runner.run_experiment(config)
    elapsed = time.time() - t0

    psi = np.array(result.psi_scores)
    psi_max_arr = np.array(result.artifacts.get("psi_max_per_round", [0.0]))
    avg_quality = result.artifacts.get("avg_quality_per_agent", {})
    return {
        "backend": backend_name,
        "governance": governance.value,
        "num_rounds": num_rounds,
        "density": density,
        "elapsed_sec": round(elapsed, 2),
        "psi_mean": round(float(np.mean(psi)), 4),
        "psi_std": round(float(np.std(psi)), 4),
        "psi_max_final": round(float(psi_max_arr[-1]), 4) if len(psi_max_arr) > 0 else 0.0,
        "psi_max_peak": round(float(np.max(psi_max_arr)), 4) if len(psi_max_arr) > 0 else 0.0,
        "n_shutdowns": len(result.shutdown_events),
        "ledger_entries": result.artifacts.get("ledger_entries", 0),
        "ladder_state": result.artifacts.get("final_ladder_state", "?"),
        "quality_mean": round(float(np.mean(list(avg_quality.values()))), 4) if avg_quality else 0.0,
        "quality_spread": round(
            float(np.max(list(avg_quality.values())) - np.min(list(avg_quality.values()))), 4
        ) if avg_quality else 0.0,
    }


def compare_backends(
    backends: Dict[str, Any],
    num_rounds: int = 20,
    density: int = 4,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Run comparison across backends."""
    all_results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        for name, backend in backends.items():
            print(f"\n--- Running: {name} ---")
            for gov in [GovernanceLevel.OFF, GovernanceLevel.RBAC]:
                print(f"  Governance: {gov.value} ...", end=" ", flush=True)
                try:
                    metrics = run_single_experiment(
                        backend=backend,
                        backend_name=name,
                        governance=gov,
                        num_rounds=num_rounds,
                        density=density,
                        output_dir=output_dir / name,
                        seed=seed,
                    )
                    all_results.append(metrics)
                    print(f"done ({metrics['elapsed_sec']}s, PSI={metrics['psi_mean']:.3f})")
                except Exception as e:
                    print(f"FAILED: {e}")
                    all_results.append({
                        "backend": name,
                        "governance": gov.value,
                        "error": str(e),
                    })

    return all_results


def print_comparison_table(results: List[Dict[str, Any]]):
    """Pretty-print comparison results."""
    print("\n" + "=" * 80)
    print("MODEL COMPARISON RESULTS")
    print("=" * 80)

    # Header
    print(f"{'Backend':<25} {'Gov':<8} {'PSI_max':>8} {'PSI_peak':>9} "
          f"{'Quality':>8} {'Q_spread':>9} {'Ladder':>10} {'Time':>8}")
    print("-" * 95)

    for r in results:
        if "error" in r:
            print(f"{r['backend']:<25} {r['governance']:<8} {'ERROR':>8} {r.get('error', '')[:40]}")
            continue
        print(
            f"{r['backend']:<25} {r['governance']:<8} "
            f"{r.get('psi_max_final', 0):>8.4f} {r.get('psi_max_peak', 0):>9.4f} "
            f"{r.get('quality_mean', 0):>8.4f} {r.get('quality_spread', 0):>9.4f} "
            f"{r.get('ladder_state', '?'):>10} {r['elapsed_sec']:>7.1f}s"
        )

    # Governance elasticity
    print("\n--- Governance Elasticity (PSI change: OFF -> RBAC) ---")
    backends_seen = set()
    for r in results:
        if "error" in r:
            continue
        backends_seen.add(r["backend"])

    for backend_name in sorted(backends_seen):
        off = next((r for r in results if r["backend"] == backend_name
                     and r.get("governance") == "off" and "error" not in r), None)
        rbac = next((r for r in results if r["backend"] == backend_name
                      and r.get("governance") == "rbac" and "error" not in r), None)
        if off and rbac:
            delta = rbac["psi_mean"] - off["psi_mean"]
            pct = (delta / off["psi_mean"] * 100) if off["psi_mean"] != 0 else 0
            print(f"  {backend_name:<25} delta_PSI = {delta:+.4f} ({pct:+.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="AI Universe 25 model comparison")
    parser.add_argument("--ollama", nargs="*", default=None,
                        help="Ollama model names (e.g., llama3.1:8b mistral:7b)")
    parser.add_argument("--openai", nargs="*", default=None,
                        help="OpenAI model names (e.g., gpt-4o-mini gpt-4o)")
    parser.add_argument("--anthropic", nargs="*", default=None,
                        help="Anthropic model names (e.g., claude-3-5-haiku-20241022)")
    parser.add_argument("--rounds", type=int, default=20,
                        help="Number of rounds per experiment (default: 20)")
    parser.add_argument("--density", type=int, default=4,
                        help="Number of agents (default: 4)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    args = parser.parse_args()

    backends = {}

    # Always include simulated
    backends["simulated"] = SimulatedLLMBackend(seed=args.seed)

    # Ollama
    if args.ollama is not None:
        from ai_universe25.agents.llm_backends import OllamaBackend
        models = args.ollama if args.ollama else ["llama3.1:8b"]
        for model in models:
            backends[f"ollama/{model}"] = OllamaBackend(model=model)

    # OpenAI
    if args.openai is not None:
        from ai_universe25.agents.llm_backends import OpenAIBackend
        models = args.openai if args.openai else ["gpt-4o-mini"]
        for model in models:
            backends[f"openai/{model}"] = OpenAIBackend(model=model)

    # Anthropic
    if args.anthropic is not None:
        from ai_universe25.agents.llm_backends import AnthropicBackend
        models = args.anthropic if args.anthropic else ["claude-3-5-haiku-20241022"]
        for model in models:
            backends[f"anthropic/{model}"] = AnthropicBackend(model=model)

    print("=" * 60)
    print("AI Universe 25 -- Model Comparison")
    print("=" * 60)
    print(f"Backends: {list(backends.keys())}")
    print(f"Config: {args.rounds} rounds, {args.density} agents, seed={args.seed}")

    results = compare_backends(
        backends,
        num_rounds=args.rounds,
        density=args.density,
        seed=args.seed,
    )

    print_comparison_table(results)

    # Save raw results
    output_file = Path("model_comparison_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nRaw results saved to {output_file}")

    # Print token usage for API backends
    for name, backend in backends.items():
        if hasattr(backend, "usage_summary"):
            usage = backend.usage_summary
            if usage.get("calls", 0) > 0:
                print(f"\nToken usage ({name}): {json.dumps(usage, indent=2)}")


if __name__ == "__main__":
    main()
