# `Batch Joint Pre-signing (BJP)`

This project models `Batch Joint Pre-signing (BJP)` for the off-chain `Pre-swap`
phase of ParaSwap-style multi-party atomic swaps. The code follows the module
layout suggested in the guide and keeps the same experimental breakdown:

- `E1`: end-to-end latency comparison
- `E2`: message and byte counting
- `E3`: scalability with batch size `k`
- `E4`: isolated ECC / cryptographic cost
- `E5`: full `Pre-swap` cycle simulation
- `E7`: packet-loss sensitivity analysis
- `E8`: batch-failure recovery overhead

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
│   ├── e5_full_cycle.py
│   ├── e7_loss_sensitivity.py
│   └── e8_batch_failure.py
├── results/
└── plots/
```

## Environment

Recommended dependencies from the guide:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy scipy matplotlib seaborn pandas coincurve
```

## Quick Start

From inside `bjp_experiment/`:

```bash
python experiments/e1_latency.py
python experiments/e2_messages.py
python experiments/e3_scalability.py
python experiments/e4_crypto.py
python experiments/e5_full_cycle.py
sudo python experiments/e7_loss_sensitivity.py
python experiments/e8_batch_failure.py
```

Outputs are written under:

- `results/e1_latency.json`
- `results/e2_messages.json`
- `results/e3_scalability.json`
- `results/e4_crypto.json`
- `results/e5_full_cycle.json`
- `results/e7_loss_sensitivity.json`
- `results/e8_batch_failure.json`
- `plots/e1_latency_distribution.png`
- `plots/e2_communication.png`
- `plots/e3_scalability.png`
- `plots/e4_crypto.png`
- `plots/e5_full_cycle.png`
- `plots/e7_loss_sensitivity.png`
- `plots/e8_batch_failure.png`

## Experiments

- `E1` compares end-to-end latency between `Sequential` and `BJP`, then saves a
  violin plot plus box plot.
- `E2` measures real bidirectional message counts and byte counts from the TCP
  session, then saves a grouped bar chart.
- `E3` evaluates scalability by sweeping `k` and plotting median latency for
  `Sequential` and `BJP`.
- `E4` measures isolated cryptographic cost and saves a bar chart over `k`.
- `E5` simulates a full pre-swap cycle for multiple `n` values and saves a line
  chart for median pre-swap time.
- `E7` sweeps several packet-loss rates with `tc netem`, reruns the latency
  benchmark, and saves a loss-sensitivity figure.
- `E8` injects one faulty pre-signature, measures detection and retry cost, and
  compares recovery overhead between `Sequential` and `BJP`.

