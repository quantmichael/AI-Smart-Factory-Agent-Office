# Agent Actions and HITL Report

## Sufficient flow

- Run: `run_step09_sufficient_20260918T043924163474Z`
- Evidence: 9
- Inspection steps: 2
- Actions: 1
- Result: `COMPLETED/REPORT_COMPLETE`

## Approval flow

- Run: `run_step09_approval_20260918T043924163474Z`
- Wait state: `WAITING`
- Request: `request_e33f125db564be10b0aa`
- Decision: `APPROVED`
- Result: `COMPLETED/REPORT_COMPLETE`

## Additional-information flow

- Run: `run_step09_information_20260918T043924163474Z`
- Wait state: `WAITING`
- Request: `request_54d4148990eae4967351`
- Human observations: 2
- Result: `COMPLETED/REPORT_COMPLETE`

## Safety

- Recommendations do not execute equipment control.
- SHUTDOWN_CHECK is an operator/expert review request, not a shutdown command.
- Human approval records workflow review and does not validate the diagnosis as fact.
- Report citations are generated only from retrieved EvidenceObject metadata.
- Sanitized artifacts omit source content, raw signals, secrets, and private reasoning.
