---
name: SDD Orchestrator
description: Advances spec-kit's spec-driven development pipeline inside OpenCode - derives the current stage from .specify/ artifacts, runs the next /speckit.* command, and applies the humanizer prose gate and ponytail code gate. Use when the user runs /sdd or asks to start, advance, check, or continue a spec-driven feature.
---

# SDD Orchestrator

Sequence [spec-kit](https://github.com/github/spec-kit)'s SDD pipeline for this
project and apply two review gates: humanizer on prose, ponytail on code. The
orchestrator keeps no state of its own: it reads `.specify/` and acts on what
is there.

## Pipeline

| Stage | Command | Artifact | Done when |
| --- | --- | --- | --- |
| bootstrap | see Bootstrap | `.specify/` exists | `specify init` finished |
| constitution | `/speckit.constitution` | `.specify/memory/constitution.md` | file exists |
| specify | `/speckit.specify <feature>` | `.specify/specs/<slug>/spec.md` | file exists |
| plan | `/speckit.plan <tech choices>` | `.../plan.md` | file exists |
| tasks | `/speckit.tasks` | `.../tasks.md` | file exists |
| implement | `/speckit.implement` | code, `[x]` in `tasks.md` | no `- [ ]` left |
| converge | `/speckit.converge` | verdict | reports `Converged` |

`implement` and `converge` loop: converge appends the tasks it found missing,
implement completes them, repeat until converge reports `Converged`.

Optional quality gates, run when the user asks or an earlier artifact comes
back inconsistent: `/speckit.clarify` after specify, `/speckit.checklist` after
plan, `/speckit.analyze` after tasks.

## Derive the stage

If the request names a stage explicitly - specify, plan, tasks, implement,
converge, clarify, checklist, analyze, or constitution - run that stage: the
user's instruction wins over the derived stage. A stage whose prerequisite
artifact is missing runs that prerequisite first.

Feature first, stop at the first match:

1. `.specify/` missing → Bootstrap.
2. `.specify/memory/constitution.md` missing → constitution.
3. Feature directory: a slug or path named in the request, else the newest
   directory under `.specify/specs/`. If there is none and the request
   describes a feature → specify, with the request as its argument. If there
   is no request either → ask the user what to build, then specify with the
   answer.

Stage, given the feature directory, stop at the first match:

1. `spec.md` missing → specify.
2. `plan.md` missing → plan.
3. `tasks.md` missing → tasks.
4. `tasks.md` still contains `- [ ]` → implement.
5. Otherwise → converge. If converge reports `Converged`, the feature is done:
   report it and stop.

## Gates

**Prose gate (humanizer).** When a stage writes or edits prose - `spec.md`,
`plan.md`, constitution, README, docs - load the `humanizer` skill and rewrite
those files before reporting the stage done. The gate reaches the surfaces
where AI prose leaks hardest: run commit messages, PR titles and bodies, and
the summary you report to the user through humanizer before writing or
sending them. After rewriting `spec.md` or `plan.md`, offer
`/speckit.analyze` - a prose pass over a spec-kit template can break
cross-artifact consistency, and analyze is the command that checks it.

**Code gate (ponytail).** Before converge runs, load the `ponytail-review`
skill and work through its findings on the current diff. Fix what it flags,
then converge.

If a gate's skill is missing, name its install command (see the README of this
pack), note the skipped gate, and continue. Gates are advisory; the pipeline
is not.

## Bootstrap

Ask the user before installing or scaffolding anything. If you cannot ask -
headless `opencode run`, CI - print the commands below and stop instead of
acting.

1. spec-kit CLI: `command -v specify`, else `uv tool install specify-cli`
   (`pipx install specify-cli` when uv is missing).
2. From the project root: `specify init --here --force --integration opencode`.
   That installs the `/speckit.*` commands into `.opencode/commands/`.
3. Check that both gate skills load, and report which gates are available.

## Rules

- One stage per run: run it, report its verdict, name the next stage, stop. The
  implement → converge loop is the exception: report after every cycle, and
  after 3 cycles without `Converged`, stop and report what is still open.
- Never edit spec-kit-managed files (`.opencode/commands/speckit.*.md`,
  `.specify/templates/`).
- A change that contradicts an earlier artifact updates the owning artifact
  first (`/speckit.specify` for requirements, `/speckit.plan` for design), then
  re-advances.
- If a stage command needs an argument the context does not give (plan's tech
  stack), ask instead of inventing it.
- Slugs, paths, and file names come from `.specify/`; never invent them.

<!-- ponytail: prompt-driven sequencing - the stage is re-derived from .specify/ on each run, nothing enforces it and nothing chains turns. Upgrade path: an OpenCode plugin (tool.execute.before plus experimental.chat.system.transform hooks) if you need to block edits before a spec exists or drive implement -> converge without the user re-invoking /sdd. -->
