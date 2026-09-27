# CDR submission package

## Title and hook

**CDR - Break it. Let Bob rewrite it. Prove it survives.**

CDR injects a controlled failure into a running application, gives IBM Bob the physical evidence
and full repository context, then rebuilds the changed service and repeats the identical
experiment. A repair is accepted only when the measured system becomes resilient.

## Short description

Chaos tools stop at the failure. APM stops at the diagnosis. Coding agents start from a human
prompt. CDR closes that gap: k6 and Toxiproxy reproduce a collapse, IBM Bob applies a minimal fix
inside the real repository, and CDR re-runs the same fault against the rebuilt service to produce
an auditable before/after result.

## Why it is different

- OpsPilot-style incident assistants begin with user-supplied traces or snippets; CDR generates
  runtime evidence from a controlled physical experiment.
- Architecture resilience simulators recommend patterns; CDR changes business-logic source code
  and uses the real git diff.
- Generic coding agents report that work is complete; CDR requires the patched artifact to pass
  the same experiment that exposed the weakness.

## Four-minute video

1. **0:00-0:25 - The gap:** chaos, APM and coding agents are disconnected.
2. **0:25-1:10 - Break it:** show the live badge, Toxiproxy injection and collapsing k6 graph.
3. **1:10-2:15 - Let Bob rewrite it:** show task id, Bobcoins, source file and real diff.
4. **2:15-3:15 - Prove it survives:** show the rebuilt container and identical second run.
5. **3:15-4:00 - Business case:** reduced diagnosis time, incident risk and downtime exposure.

Use only values from a completed `live` run. Mock mode is a product-development fallback and must
remain visibly labelled as simulation.

## Community launch

Target at least 30 genuine votes with one visual story: red collapse graph, Bob diff, green rerun.
Publish the direct submission link with a 15-second clip on the event Discord, LinkedIn and X.
Ask SRE and DevOps practitioners to try the demo before voting. Do not use automated accounts,
vote exchanges, purchased votes or unsolicited bulk messages.

## Final evidence checklist

- [ ] Public demo opens without credentials.
- [ ] Completed result displays `LIVE EVIDENCE`.
- [ ] k6 JSONL and console logs are preserved under the run artifact.
- [ ] Bob task id, Bobcoins and session export are present.
- [ ] Patch source is `bob-shell`, with repository-real files and diff.
- [ ] Patched checkoutservice image was built and restarted.
- [ ] Before and after use the same scenario, VUs, duration and toxic.
- [ ] Video, deck, repository and submission links work in an incognito browser.
- [ ] No credential appears in video, logs, Git history or screenshots.
