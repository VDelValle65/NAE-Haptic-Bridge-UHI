# NAE™ Universal Haptic Interface (UHI): Substrate Calibration v1.1.1
Primary Clinical Validation: Valerie A. Del Valle
(Proof of Concept) Principal Researcher & Program Designer: Valerie A. Del Valle
Affiliation: Neuro-Art for Seniors, LLC
ORCID: 0009-0004-5294-7981

## Project Overview
This haptic bridge facilitates the Substrate calibration necessary for the NAE™ Protocol. It focuses exclusively on the Neural Substrates, Dopaminergic Responses, and Ocular-Motor Protocols, facilitating the mitigation of synaptic pruning. Using OpenAI Codex, we engineered the Universal Haptic Interface (UHI): a core proprietary hardware component facilitating Biaxial Rotary Modulation as part of an ocular-motor stimulation protocol for geriatric care.

## Clinical Framework
The UHI serves as a technical bridge between mechanical input and neural response. By utilizing **Biaxial Rotary Modulation**, the interface engages the primary visual cortex and the pre-cuneus, inducing targeted dopaminergic responses via precise ocular-motor coordination.

## Technical Architecture
- **Language:** Python
- **Engine:** OpenAI Codex
- **Logic:** `haptic_logic.py`
- **MAM audit:** `mam_audit.py` exports a 10x10-grid Midpoint Accuracy Metric CSV from reviewed peg coordinates without making clinical or diagnostic inferences.
- **Substrate:** High-Density LED Stim-Grid

## Legal & Trademark Attribution
- **NAE™** (Neuro-Art Enrichment) is a trademark of Neuro-Art for Seniors, LLC.
- **Entity:** Neuro-Art for Seniors, LLC (Registered DBA).
- **Principal Researcher:** Valerie A. Del Valle

---
*Developed for the Codex Creator Challenge 2026.*


## Midpoint Accuracy Metric (MAM) Audit
The MAM utility performs an objective geometric audit of a post-session workspace capture. It computes the true horizontal center axis, maps reviewed peg coordinates onto the standardized 10x10 grid, and exports signed, absolute, and grid-normalized midpoint deltas to `MAM_Audit_Results.csv`.

Example:

```python
from mam_audit import MamAuditConfig, PegPlacement, mam_geometric_audit

rows = mam_geometric_audit(
    image_dimensions=(1000, 960),
    detected_pegs=[PegPlacement(peg_id=1, x=300, y=480)],
    config=MamAuditConfig(output_csv="MAM_Audit_Results.csv"),
)
```

The audit is non-invasive and does not infer participant neurological status; it only reports coordinate variance from the midpoint axis for longitudinal review.
