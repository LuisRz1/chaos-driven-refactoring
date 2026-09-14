# Glossary

| Term | Meaning |
| --- | --- |
| **CDR** | Chaos-Driven Refactoring — this project. |
| **APM** | Application Performance Monitoring (Datadog, New Relic, Dynatrace). |
| **APM-to-code gap** | The market gap CDR fills: observability localizes problems but never changes code. |
| **Chaos engineering** | Deliberately injecting faults to learn how a system fails. |
| **k6** | Load-testing tool used to generate virtual users against the target. |
| **Toxiproxy** | TCP proxy used to inject latency/abort faults into a service dependency. |
| **Pumba** | Docker chaos tool (container kill/pause) listed as an alternative fault injector. |
| **Collapse** | State where p95 exceeds 3× the threshold or error rate exceeds the collapse threshold. |
| **Time to collapse** | Seconds from run start until the collapse condition is met. |
| **Finding** | Classified root cause with category, confidence, evidence and location. |
| **Diagnosis** | Analyzer output: analysis markdown, proposed change, `bob_task_id`, `bobcoins`, `target_files`. |
| **Patch** | The real `git diff` (Bob) or template diff, with branch, files and `source`. |
| **Verification** | Re-running the same scenario against the patched code; stability verdict + improvements. |
| **Run** | One experiment: queued → … → completed/failed, with all artifacts above. |
| **Analyzer precedence** | `auto` → Bob Shell → watsonx Granite → deterministic rules. |
| **Bob** | IBM Bob 2.0, the AI development partner (IDE and Bob Shell CLI). |
| **Bob Shell** | Bob's terminal/CLI client (`bob run`, `bob chat`); used headlessly by the runner. |
| **Bobcoins** | Consumption-based billing metric for Bob; the trial grants 50. |
| **Bob session/task id** | Identifier of a Bob run; stored in diagnoses/patches for traceability. |
| **Granite** | IBM watsonx.ai model family; allowed models only (`ibm/granite-3-8b-instruct` default). |
| **Controlled schema `cdr`** | Isolated Postgres schema holding all CDR tables in a shared Supabase project. |
| **PostgREST profile headers** | `Accept-Profile`/`Content-Profile` select the schema in Supabase REST. |
| **RLS** | Row Level Security; public read policies for `anon`, writes via service role. |
| **Worker** | `cdr watch`; claims queued runs and executes the pipeline. |
| **Progress streaming** | Publishing phase rows and status transitions so the UI shows live progress. |
| **Mock mode / live mode** | Simulated deterministic telemetry vs real chaos lab execution. |
| **MOC** | Map of Content — an index note like [[Home]]. |
| **Evidence** | `bob_sessions/` exports and session JSONs required for judging. |
| **lablab.ai** | Hackathon platform hosting the IBM Bob 2.0 Hackathon. |
