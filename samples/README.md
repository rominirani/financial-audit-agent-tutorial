# Sample Apps

This directory contains additional use cases that apply the same **delegation architecture** from the [Financial Audit Agent](../) to different enterprise domains.

| Sample | Domain | Subagents |
|:---|:---|:---|
| [insurance-claims-agent](insurance-claims-agent/) | Automated claims adjudication | Claims Researcher → Document Analyzer → Adjudication Engine |
| [hr-onboarding-agent](hr-onboarding-agent/) | Employee onboarding compliance | HR Researcher → Document Verifier → Compliance Checker |

Both samples implement the same patterns as the main tutorial:

- **Orchestrator with delegation tools only** — zero direct data access
- **Model tiering** — `gemini-3.6-flash` for orchestrator/writer, `gemini-3.5-flash-lite` for data agents
- **State accumulation with truncation** — full results stored for downstream agents, concise summaries returned to orchestrator
- **Guardrails** — write-agent delegation blocked until all prior steps complete
- **Defense-in-depth** — hardcoded `VALID_STATUSES` validation on write tools
- **Dev / Staging / Prod policy tiers** — with rich human-in-the-loop approval handlers in staging

Refer to the README in each sample directory for domain-specific setup instructions (BigQuery tables, GCS buckets, etc.).

---

> **Disclaimer:** These sample apps are provided on an **as-is, where-is** basis for educational and reference purposes only. They are not production-ready and come with no warranties or guarantees. Use at your own discretion.
