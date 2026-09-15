# Evaluation strategy

Risk detection is only useful if we can measure whether changes improve it. Evaluations are therefore part of the product architecture, not an afterthought.

## What we measure

A reasoning implementation should be evaluated on at least:

- **Detection** — did it find the meaningful signal?
- **Classification** — risk vs. issue vs. dependency vs. decision
- **Categorization** — schedule, dependency, resource, technical, etc.
- **Evidence grounding** — does every finding point to supporting source signals?
- **Inference quality** — can it detect meaningful risk that is implied across multiple signals?
- **Decision awareness** — does it recognize when leadership action is required?
- **Noise** — does it avoid turning routine project updates into risks?

## Why synthetic cases

The repository must never contain real employer, customer, employee, email, chat, meeting, or project data. Evaluation fixtures use synthetic project situations that represent common patterns.

## Current cases

`cases.json` includes examples for:

- schedule/dependency risk
- active issue
- normal update / false-positive control
- decision needed
- hidden risk emerging across multiple sources

The hidden-risk case is especially important: a useful project-risk agent cannot depend only on explicit phrases such as "at risk." It needs to reason across time and across sources.

## Contributor expectation

When changing reasoning behavior, contributors should add a regression case whenever practical. The goal is to make the project's reasoning improve measurably over time rather than simply becoming more complex.
