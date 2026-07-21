---
name: debugging-strategies
description: "Transform debugging from frustrating guesswork into systematic problem-solving with proven strategies, powerful tools, and methodical approaches."
risk: safe
source: community
date_added: "2026-02-27"
---

# Debugging Strategies

Transform debugging from frustrating guesswork into systematic problem-solving with proven strategies, powerful tools, and methodical approaches.

## Use this skill when

- Tracking down elusive bugs
- Investigating performance issues
- Debugging production incidents
- Analyzing crash dumps or stack traces
- Debugging distributed systems and complex interactions

## Do not use this skill when

- There is no reproducible issue or observable symptom
- The task is purely feature development
- You cannot access logs, traces, or runtime signals

## Instructions

1. **Reproduce** the issue and capture logs, traces, and environment details.
2. **Form hypotheses** and design controlled experiments.
3. **Narrow scope** with binary search and targeted instrumentation.
   - Example: isolate whether the issue is in the client, the network layer, or the backend service.
4. **Document findings** and verify the fix.
5. Always check:
   - Application and system logs first
   - Cross-reference with project knowledge base or documentation for known issues

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
