# `bjp_experiment`

Prototype repository scaffolded from the implementation guidance in `HD.pdf`.

This project models `Batch Joint Pre-signing (BJP)` for the off-chain `Pre-swap`
phase of ParaSwap-style multi-party atomic swaps. The code follows the module
layout suggested in the guide and keeps the same experimental breakdown:

- `E1`: end-to-end latency comparison
- `E2`: message and byte counting
- `E3`: scalability with batch size `k`
- `E4`: isolated ECC / cryptographic cost
- `E5`: full `Pre-swap` cycle simulation

## Structure

```text
bjp_experiment/
├── src/
│   ├── adaptor_sig.py
│   ├── sequential.py
│   ├── bjp.py
│   ├── server.py
│   ├── client.py
│   └── utils.py
├── experiments/
│   ├── e1_latency.py
│   ├── e2_messages.py
│   ├── e3_scalability.py
│   ├── e4_crypto.py
│   └── e5_full_cycle.py
├── results/
└── plots/
```

## Environment

Recommended dependencies from the guide:

```bash
python3 -m pip install numpy scipy matplotlib seaborn pandas coincurve
```

`coincurve` is optional in this scaffold. If it is unavailable, the repository
falls back to a deterministic toy public-key representation so the transport and
benchmark scripts can still run.

## Quick Start

From inside `bjp_experiment/`:

```bash
python3 experiments/e1_latency.py
python3 experiments/e2_messages.py
python3 experiments/e3_scalability.py
python3 experiments/e4_crypto.py
python3 experiments/e5_full_cycle.py
```

Outputs are written under:

- `results/` for JSON summaries
- `plots/` for charts

## Notes

- The scaffold intentionally mirrors the code style suggested in `HD.pdf`.
- `pre_verify()` remains simplified, matching the guide's note that it is a
  placeholder for the full ECC relation check from the paper.
- This is a prototype for experimentation and reporting, not a hardened
  implementation for deployment.
