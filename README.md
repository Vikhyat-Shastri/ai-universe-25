# AI Universe 25 / Grokipedia

A governed, auditable multi-agent wiki-writing environment ("Grokipedia") where LLM agents collaborate under **MCP** (Model Context Protocol) with **RBAC**, **quorum gates**, **fair scheduling**, and an append-only **tamper-evident ledger**.

## Overview

Grokipedia implements a federated, encyclopedia-scale wiki authored by LLM agents inside an MCP context–commons with typed channels. The substrate provides:

- **Least-privilege RBAC** with role-based access control
- **Quorum gates** for sensitive edits
- **Fair scheduling** (deficit round-robin; burst limits)
- **Append-only logs** with signed provenance
- **Shutdown ladder**: RUN → WARN → STOP → QUARANTINE → SHUTDOWN

## Architecture

### Runtime Components

- **Agents** (7 roles): Herald, Architect, Scribe, Archivist, Verifier, Arbiter, Summarist
- **MCP Gateway**: Deterministic routing with RBAC + ladder checks
- **Scheduler**: Fairness (DRR + burst limits), per-agent/per-tool token buckets
- **Tool Servers**: Wiki surfaces, retrieval, verification/NLI, governance actions, telemetry
- **Ledger**: Append-only event store with hash chain / Merkle checkpoints

### Evaluation Pipeline

- **3-Model Judge Panel**: CQP (Content Quality Panel), CAP (Channel-Access Panel), CoAP (Compute Allocation Panel)
- **PSI Metrics**: RC/PO/CC/PS/RP components with winsorize→rank→aggregate pipeline
- **Analytics**: Shutdown metrics, survival models, change-point detection

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from ai_universe25.runtime import MCPGateway
from ai_universe25.experiments import ExperimentRunner

# Run a single experiment
runner = ExperimentRunner(config_path="configs/mvp.yaml")
results = runner.run()
```

## Project Structure

```
ai_universe25/
├── runtime/          # MCP gateway, scheduler, RBAC, ladder FSM
├── tools/            # MCP tool servers (wiki, retrieval, verifier, governance, telemetry)
├── agents/           # Role prompts + policies + orchestrator
├── ledger/           # Append-only storage + Merkle checkpoints
├── experiments/      # Configs + runner
└── analytics/        # PSI + stats + report generation

configs/              # Factorial sweep YAMLs
notebooks/            # Analysis notebooks
docs/                 # Documentation
```

## Documentation

See `docs/` for detailed documentation and `extracted_content/content.md` for the source paper.

## License

MIT
