# Bob sessions (hackathon evidence)

This folder holds the **IBM Bob 2.0 task session exports** required for judging.

## Required contents

For every Bob task used to build CDR:

1. A screenshot of the task session consumption summary (Bobcoins used per task) in `*.png`.
2. The exported task history markdown file from Bob IDE (History → task → Export task history).

## Naming convention

```
phase-1-chaos-runner.md / phase-1-chaos-runner.png
phase-2-classifier.md / phase-2-classifier.png
phase-2-dashboard.md / phase-2-dashboard.png
phase-3-watsonx-diagnosis.md / phase-3-watsonx-diagnosis.png
phase-4-verification.md / phase-4-verification.png
...
```

Group exports by the pipeline phase they contributed to so judges can trace how Bob 2.0 was used
in each part of the build.

## Rules

- **Never include credentials or API keys** in exported session files or screenshots. Remove
  secrets from code before exporting; IBM security scans submission repositories and deactivates
  accounts that leak IBM Cloud or Bob credentials.
- Keep sessions scoped to this project workspace.
- Export sessions progressively during the build — do not wait until submission time.
