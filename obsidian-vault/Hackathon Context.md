# Hackathon Context

## Event

**IBM Bob 2.0 Hackathon** — lablab.ai, September 25–27, 2026, 48 hours, fully online.

- Registration closes at kickoff: Fri Sep 25, 15:00 UTC.
- Submissions close: Sun Sep 27, 15:00 UTC.
- Teams of 1–6, solo allowed. Prize pool $10,000 ($5k / $3k / $2k).
- Platform: lablab.ai + Discord. Tracks announced before the event.

## Judging criteria and where CDR answers them

| Criterion | CDR answer |
| --- | --- |
| **Application of Technology** | Bob 2.0 as dev partner (IDE + Shell, agent mode, parallel tasks, subagents, document understanding) **and** runtime analyzer doing real repo reads and edits. Evidence in `bob_sessions/`. |
| **Business Value** | Downtime > $300k/h; measured p95/error-rate collapse elimination; diagnosis 3.2 min vs 95 min manual. |
| **Originality** | Only solution combining real telemetry collapse + business-logic rewrite in the repo + autonomous verification. Blue ocean vs chaos tools, APM and reactive AI agents. |
| **Presentation** | Live progress dashboard, demo script (`docs/DEMO_SCRIPT.md`), slides, recorded run. |

Full mapping: [`docs/JUDGING_MAP.md`](../docs/JUDGING_MAP.md).

## Submission requirements

- Title, short/long description, technology & category tags, cover image, video presentation,
  slide presentation, demo app platform + URL, code repository URL.
- Include the code where IBM Bob 2.0 assisted.
- Include screenshots of IBM Bob task session summaries (mandatory).
- Original work, MIT-compliant license.

## Bob rules

- Must use Bob for development; export task session reports into the repo (`bob_sessions/`).
- Each participant gets **40 Bobcoins** (the team account has a 50-Bobcoin trial budget).
- `$80` IBM Cloud credits when watsonx is enabled.
- **Out-of-scope watsonx models** (using them hurts judging):
  `meta-llama/llama-3-405b-instruct`, `mistralai/mistral-medium-2505`,
  `mistralai/mistral-small-3-1-24b-instruct-2503`. Blocked in code.
- Never commit credentials; IBM deactivates accounts that leak Bob/IBM Cloud secrets.

## Demo checklist

- [ ] Dashboard deployed and showing at least one completed run with a real Bob patch.
- [ ] Worker running (`cdr watch --pace 6`) for the live queue demo.
- [ ] `bob_sessions/` with IDE exports + screenshots and headless session JSONs.
- [ ] Video, slides and cover uploaded to lablab before the deadline.

Related: [[Evidence]], [[IBM Bob Integration]], [[Roadmap]].
