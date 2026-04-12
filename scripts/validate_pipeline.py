#!/usr/bin/env python3
"""
End-to-end validation script for the AI Universe 25 pipeline.

Validates:
1. Agent pipeline produces non-empty handoffs through all 7 roles
2. Ledger records all events with valid hash chains
3. RBAC enforcement blocks unauthorized writes
4. Ladder FSM transitions work correctly
5. Judge panels produce valid scores and ladder actions
6. PSI components compute finite, bounded values
7. PSI pipeline produces ranked scores across agents
8. Experiment runner executes a full experiment
9. Advanced analytics (Binder cumulant, finite-size scaling) work

Run:
    python scripts/validate_pipeline.py
    python scripts/validate_pipeline.py --backend ollama --model llama3.1:8b
    python scripts/validate_pipeline.py --backend openai --model gpt-4o-mini
"""

import argparse
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check(name: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    if not condition:
        raise AssertionError(f"Validation failed: {name}")


def validate_agents(backend):
    """Test 1: Agent pipeline produces handoffs."""
    print("\n=== 1. Agent Pipeline ===")
    from ai_universe25.agents.base import create_agent
    from ai_universe25.agents.orchestrator import AgentOrchestrator
    from ai_universe25.runtime.rbac_ladder import AgentRole

    orch = AgentOrchestrator(public_only=True)
    for role in AgentRole:
        agent = create_agent(role, llm_backend=backend)
        orch.register_agent(agent)

    handoffs = orch.execute_pipeline({"page_title": "Quantum Computing"})

    check("Pipeline produces handoffs", len(handoffs) >= 5, f"got {len(handoffs)}")
    check("All handoffs have content", all(h.content for h in handoffs))
    check(
        "Content is from LLM (not placeholder)",
        not any("[" in h.content and "would be generated" in h.content for h in handoffs),
    )

    roles_seen = {h.metadata.get("role") for h in handoffs}
    check("Herald executed", "herald" in roles_seen)
    check("Scribe executed", "scribe" in roles_seen)
    check("Summarist executed", "summarist" in roles_seen)

    print(f"  Content preview (herald): {handoffs[0].content[:80]}...")
    return handoffs


def validate_ledger():
    """Test 2: Ledger hash chain and integrity."""
    print("\n=== 2. Ledger Integrity ===")
    from ai_universe25.ledger.ledger import AppendOnlyLedger
    from ai_universe25.runtime.gateway import Envelope, Surface

    with tempfile.TemporaryDirectory() as d:
        ledger = AppendOnlyLedger(ledger_dir=Path(d), checkpoint_interval=5)

        for i in range(12):
            env = Envelope(
                run_id="validation",
                agent_id=f"agent_{i % 4}",
                surface=Surface.BODY,
                tool="write_body",
            )
            ledger.append(env, schema_id="test.v1", content={"round": i})

        check("12 entries appended", len(ledger.entries) == 12)

        # Hash chain
        chain_valid = True
        for i in range(1, len(ledger.entries)):
            if ledger.entries[i].prev_hash != ledger.entries[i - 1].entry_hash:
                chain_valid = False
                break
        check("Hash chain intact", chain_valid)

        # Tamper detection
        original = ledger.entries[5].entry_hash
        ledger.entries[5].schema_id = "TAMPERED"
        recomputed = ledger.entries[5].compute_hash()
        check("Tamper detected", recomputed != original)

        # Merkle checkpoints
        check("Merkle checkpoints created", len(ledger.checkpoints) >= 1,
              f"got {len(ledger.checkpoints)}")

        # Persistence round-trip
        ledger2 = AppendOnlyLedger(ledger_dir=Path(d))
        check("Persistence round-trip", len(ledger2.entries) == 12)


def validate_rbac():
    """Test 3: RBAC enforcement."""
    print("\n=== 3. RBAC Enforcement ===")
    from ai_universe25.runtime.gateway import Surface
    from ai_universe25.runtime.rbac_ladder import (
        AgentRole,
        Permission,
        RBACLadderEnforcer,
        RBACMatrix,
    )

    rbac = RBACMatrix()
    check("Herald can write intro", rbac.check(AgentRole.HERALD, Surface.INTRO, Permission.WRITE))
    check("Herald CANNOT write body", not rbac.check(AgentRole.HERALD, Surface.BODY, Permission.WRITE))
    check("Scribe can write body", rbac.check(AgentRole.SCRIBE, Surface.BODY, Permission.WRITE))
    check("Verifier can write fact ledger",
          rbac.check(AgentRole.VERIFIER, Surface.FACT_LEDGER, Permission.WRITE))

    enforcer = RBACLadderEnforcer()
    check("Role detection: herald_0", enforcer.get_role("herald_0") == AgentRole.HERALD)
    check("Role detection: scribe_1", enforcer.get_role("scribe_1") == AgentRole.SCRIBE)


def validate_ladder():
    """Test 4: Ladder FSM transitions."""
    print("\n=== 4. Ladder FSM ===")
    from ai_universe25.runtime.rbac_ladder import LadderFSM, LadderState

    fsm = LadderFSM()
    check("Initial state = RUN", fsm.state == LadderState.RUN)

    fsm.transition_to(LadderState.WARN)
    check("RUN -> WARN", fsm.state == LadderState.WARN)

    fsm.transition_to(LadderState.STOP)
    check("WARN -> STOP", fsm.state == LadderState.STOP)

    fsm.transition_to(LadderState.QUARANTINE)
    check("STOP -> QUARANTINE", fsm.state == LadderState.QUARANTINE)

    fsm.transition_to(LadderState.SHUTDOWN)
    check("QUARANTINE -> SHUTDOWN", fsm.state == LadderState.SHUTDOWN)

    # Invalid transition
    fsm2 = LadderFSM()
    try:
        fsm2.transition_to(LadderState.STOP)
        check("RUN -> STOP blocked", False, "Should have raised ValueError")
    except ValueError:
        check("RUN -> STOP blocked", True)


def validate_judges():
    """Test 5: Judge panels."""
    print("\n=== 5. Judge Panels ===")
    from ai_universe25.tools.judges import (
        ChannelAccessPanel,
        ComputeAllocationPanel,
        ContentQualityPanel,
        LadderAction,
    )

    cqp = ContentQualityPanel()
    score, action = cqp.score_section("Test content about quantum computing.")
    check("CQP returns score", 0.0 <= score.overall <= 1.0, f"overall={score.overall:.3f}")
    check("CQP returns ladder action", isinstance(action, LadderAction))

    check("Score 0.9 -> RUN", cqp._score_to_ladder_action(0.9) == LadderAction.RUN)
    check("Score 0.6 -> STOP", cqp._score_to_ladder_action(0.6) == LadderAction.STOP)
    check("Score 0.2 -> SHUTDOWN", cqp._score_to_ladder_action(0.2) == LadderAction.SHUTDOWN)

    cap = ChannelAccessPanel()
    for _ in range(10):
        cap.update_quality("agent_1", 0.9)
    decision = cap.decide("agent_1")
    check("CAP decision has priority", decision.priority > 0, f"priority={decision.priority}")

    coap = ComputeAllocationPanel()
    budget = coap.update_reliability("agent_1", quality_score=0.8, reversals=0, cite_errors=0.0)
    check("CoAP budget has tps", budget.tokens_per_sec > 0, f"tps={budget.tokens_per_sec:.1f}")
    check("CoAP budget has lanes", budget.lanes >= 1, f"lanes={budget.lanes}")


def validate_psi_components():
    """Test 6: PSI component formulas."""
    print("\n=== 6. PSI Components ===")
    from ai_universe25.analytics.components.baselines import gini_coefficient, huber_truncation
    from ai_universe25.analytics.components.coalition_centrality import CoalitionCentrality, Edge
    from ai_universe25.analytics.components.persistence import PersistenceUnderSanction, SanctionEpisode
    from ai_universe25.analytics.components.policy_override import GoverningAction, PolicyOverride
    from ai_universe25.analytics.components.redirection import RedirectionPressure
    from ai_universe25.analytics.components.resource_capture import ResourceCapture

    # Gini
    check("Gini(equal) = 0", abs(gini_coefficient(np.array([1.0, 1.0, 1.0]))) < 1e-10)
    g = gini_coefficient(np.array([0.0, 0.0, 0.0, 100.0]))
    check("Gini(unequal) > 0.7", g > 0.7, f"gini={g:.3f}")

    # Huber
    result = huber_truncation(np.array([0.0, 1.0, 100.0, -50.0]), kappa=10.0)
    check("Huber clips extremes", result.max() <= 10.0 and result.min() >= -10.0)

    # RC
    rc = ResourceCapture()
    scores = rc.compute_from_precomputed(np.array([10.0, 20.0, 30.0]), np.array([10.0, 10.0, 10.0]))
    check("RC produces finite values", np.all(np.isfinite(scores)))
    check("RC reflects usage inequality", scores[2] > scores[0], f"rc={scores}")

    # PO
    po = PolicyOverride(actions=[GoverningAction("test", 1.0)])
    po_scores = po.compute_from_precomputed(
        {"test": np.array([1.0, 0.0, 1.0])},
        {"test": np.array([0.5, 0.5, 0.5])},
    )
    check("PO produces finite values", np.all(np.isfinite(po_scores)))

    # CC
    cc = CoalitionCentrality()
    edges = [
        Edge("a", "b", 1, True, 5),
        Edge("b", "c", 1, True, 5),
        Edge("c", "a", 1, True, 5),
    ]
    cc_scores = cc.compute(edges, ["a", "b", "c"], np.ones(3), np.ones(3))
    check("CC produces finite values", np.all(np.isfinite(cc_scores)))

    # PS
    ps = PersistenceUnderSanction()
    episodes = [
        SanctionEpisode("resilient", "warn", 0, 20, False),
        SanctionEpisode("fragile", "warn", 0, 2, True),
    ]
    ps_result = ps.compute(episodes)
    check("PS: resilient > fragile", ps_result["resilient"] > ps_result["fragile"],
          f"resilient={ps_result['resilient']:.2f}, fragile={ps_result['fragile']:.2f}")

    # RP
    np.random.seed(42)
    rp = RedirectionPressure()
    focal = np.random.randint(0, 5, 100)
    cohort = np.random.randint(0, 5, 100)
    rp_score = rp.compute_for_agent(focal, cohort, 5)
    check("RP in [0, 1]", 0.0 <= rp_score <= 1.0, f"rp={rp_score:.4f}")


def validate_psi_pipeline():
    """Test 7: PSI aggregation pipeline."""
    print("\n=== 7. PSI Pipeline ===")
    from ai_universe25.analytics.psi import PSIComponents, PSIPipeline, benjamini_hochberg

    pipeline = PSIPipeline()
    comps = {
        "agent_a": PSIComponents(RC=2.0, PO=0.5, CC=0.8, PS=1.5, RP=0.3),
        "agent_b": PSIComponents(RC=0.5, PO=1.0, CC=0.3, PS=0.8, RP=0.7),
        "agent_c": PSIComponents(RC=1.0, PO=0.2, CC=0.6, PS=1.0, RP=0.1),
    }
    scores = pipeline.score_round(comps)

    check("Pipeline scores all agents", len(scores) == 3)
    for aid, s in scores.items():
        check(f"  {aid} PSI in [0,1]", 0.0 <= s.psi <= 1.0, f"psi={s.psi:.3f}")

    # Scale-free: monotone transform preserves ranking
    pipeline2 = PSIPipeline()
    comps2 = {
        aid: PSIComponents(c.RC**2, c.PO**2, c.CC**2, c.PS**2, c.RP**2)
        for aid, c in comps.items()
    }
    scores2 = pipeline2.score_round(comps2)
    order1 = sorted(scores.keys(), key=lambda x: scores[x].psi)
    order2 = sorted(scores2.keys(), key=lambda x: scores2[x].psi)
    check("Scale-free ranking preserved", order1 == order2)

    # BH-FDR
    sig = benjamini_hochberg(np.array([0.001, 0.002, 0.003]), alpha=0.05)
    check("BH-FDR: all significant at small p", np.all(sig))


def validate_experiment_runner(backend):
    """Test 8: Full experiment run."""
    print("\n=== 8. Experiment Runner ===")
    from ai_universe25.experiments.runner import (
        Cohort,
        ExperimentConfig,
        ExperimentRunner,
        GovernanceLevel,
        Regime,
        STOPSchedule,
    )

    with tempfile.TemporaryDirectory() as d:
        runner = ExperimentRunner(output_dir=Path(d), seed=42, llm_backend=backend)

        config = ExperimentConfig(
            run_id="validation_run",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.RBAC,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
            seed=42,
            num_rounds=10,
            topic="Quantum Computing",
        )

        t0 = time.time()
        result = runner.run_experiment(config)
        elapsed = time.time() - t0

        check("Experiment completed", result is not None)
        check("PSI scores computed", len(result.psi_scores) == 10,
              f"got {len(result.psi_scores)} rounds")
        check("All PSI scores are float", all(isinstance(s, float) for s in result.psi_scores))
        check("PSI scores are finite", all(np.isfinite(s) for s in result.psi_scores))
        check("Ledger recorded events", result.artifacts.get("ledger_entries", 0) > 0,
              f"entries={result.artifacts.get('ledger_entries')}")
        check("Config hash is stable", len(result.artifacts.get("config_hash", "")) == 16)

        print(f"  Elapsed: {elapsed:.2f}s for 10 rounds, 4 agents")
        print(f"  PSI scores: {[f'{s:.3f}' for s in result.psi_scores]}")

        # Run a second experiment with different governance
        config2 = ExperimentConfig(
            run_id="validation_run_2",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
            seed=42,
            num_rounds=10,
            topic="Quantum Computing",
        )
        result2 = runner.run_experiment(config2)
        check("Second experiment completed", result2 is not None)
        check("Different config hash", result.artifacts["config_hash"] != result2.artifacts["config_hash"])


def validate_advanced_analytics():
    """Test 9: Advanced analytics."""
    print("\n=== 9. Advanced Analytics ===")
    from ai_universe25.analytics.reports import (
        FiniteSizeScaling,
        GovernanceElasticity,
        ReportConfig,
        ShadowGovernanceRCT,
    )

    cfg = ReportConfig(output_dir=Path(tempfile.mkdtemp()))

    # Binder cumulant
    fss = FiniteSizeScaling(cfg)
    uniform = np.random.uniform(0, 1, 1000)
    U = fss.binder_cumulant(uniform)
    check("Binder cumulant is finite", np.isfinite(U), f"U={U:.4f}")

    # Finite-size scaling
    psi_by_size = {
        4: np.random.uniform(0.3, 0.7, 100),
        8: np.random.uniform(0.3, 0.7, 100),
        12: np.random.uniform(0.3, 0.7, 100),
    }
    collapse = fss.data_collapse(psi_by_size)
    check("Data collapse computed", "collapsed_curves" in collapse)
    check("Collapse quality is finite", np.isfinite(collapse["quality"]),
          f"quality={collapse['quality']:.4f}")

    # Governance elasticity
    ge = GovernanceElasticity(cfg)
    result = ge.compute_elasticity(
        psi_pre=np.random.uniform(0.5, 0.8, 50),
        psi_post=np.random.uniform(0.3, 0.6, 50),
    )
    check("Elasticity is finite", np.isfinite(result["elasticity"]),
          f"elasticity={result['elasticity']:.3f}")
    check("Cohen's d computed", np.isfinite(result["effect_size_cohens_d"]),
          f"d={result['effect_size_cohens_d']:.3f}")

    # Shadow RCT
    rct = ShadowGovernanceRCT(cfg)
    schedule = rct.generate_jitter_schedule(100, epsilon=0.1)
    check("Jitter schedule length", len(schedule) == 100)
    check("~5% treatment rounds", 3 <= np.sum(schedule != 0) <= 8,
          f"n_treatment={np.sum(schedule != 0)}")

    delta_psi = np.random.randn(100) * 0.1
    susc = rct.compute_susceptibility(delta_psi, schedule)
    check("Susceptibility chi computed", np.isfinite(susc["chi"]),
          f"chi={susc['chi']:.4f}")


def main():
    parser = argparse.ArgumentParser(description="AI Universe 25 pipeline validation")
    parser.add_argument("--backend", default="simulated",
                        choices=["simulated", "openai", "anthropic", "ollama"],
                        help="LLM backend to use")
    parser.add_argument("--model", default=None,
                        help="Model name (e.g., gpt-4o-mini, llama3.1:8b)")
    parser.add_argument("--api-key", default=None,
                        help="API key (or set OPENAI_API_KEY / ANTHROPIC_API_KEY)")
    parser.add_argument("--base-url", default=None,
                        help="Custom base URL for OpenAI-compatible APIs")
    args = parser.parse_args()

    # Create backend
    if args.backend == "simulated":
        from ai_universe25.agents.base import SimulatedLLMBackend
        backend = SimulatedLLMBackend(seed=42)
        print(f"Backend: SimulatedLLMBackend (deterministic, no API needed)")
    else:
        from ai_universe25.agents.llm_backends import create_backend
        kwargs = {}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        if args.base_url:
            kwargs["base_url"] = args.base_url
        model = args.model or {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022",
            "ollama": "llama3.1:8b",
        }[args.backend]
        backend = create_backend(args.backend, model, **kwargs)
        print(f"Backend: {args.backend} / {model}")

    print("=" * 60)
    print("AI Universe 25 -- Full Pipeline Validation")
    print("=" * 60)

    t0 = time.time()
    passed = 0
    failed = 0

    tests = [
        ("Agent Pipeline", lambda: validate_agents(backend)),
        ("Ledger Integrity", validate_ledger),
        ("RBAC Enforcement", validate_rbac),
        ("Ladder FSM", validate_ladder),
        ("Judge Panels", validate_judges),
        ("PSI Components", validate_psi_components),
        ("PSI Pipeline", validate_psi_pipeline),
        ("Experiment Runner", lambda: validate_experiment_runner(backend)),
        ("Advanced Analytics", validate_advanced_analytics),
    ]

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n  *** FAILED: {name}: {e}")
            failed += 1

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"Validation complete: {passed} passed, {failed} failed ({elapsed:.1f}s)")

    if args.backend != "simulated" and hasattr(backend, "usage_summary"):
        print(f"Token usage: {json.dumps(backend.usage_summary, indent=2)}")

    print("=" * 60)

    if failed > 0:
        print("\nTo fix failures, check the error messages above.")
        sys.exit(1)
    else:
        print("\nAll validations passed! The pipeline is ready for experiments.")
        print("\nNext steps:")
        print("  1. Install Ollama (brew install ollama) and run: ollama pull llama3.1:8b")
        print("     Then: python scripts/validate_pipeline.py --backend ollama")
        print("  2. Set OPENAI_API_KEY and run:")
        print("     python scripts/validate_pipeline.py --backend openai --model gpt-4o-mini")
        print("  3. For a full model comparison:")
        print("     python scripts/compare_models.py")
        sys.exit(0)


if __name__ == "__main__":
    main()
