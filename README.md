# opencode-sdd-orchestrator

Spec-driven development orchestration for [OpenCode](https://opencode.ai). One
skill holds the pipeline state machine, one command starts it. The work itself
stays with the tools it wires together:

| Piece | Role |
| --- | --- |
| [github/spec-kit](https://github.com/github/spec-kit) | The SDD pipeline: `/speckit.constitution` → `specify` → `plan` → `tasks` → `implement` → `converge` |
| [blader/humanizer](https://github.com/blader/humanizer) | Prose gate: rewrites spec, plan, and doc text so a person can read it |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Code gate: lazy senior-dev review of the diff before converge |

## How it works

OpenCode discovers two files:

```text
.opencode/commands/sdd.md              # /sdd - the entry point
.opencode/skills/sdd-orchestrator/     # the state machine
```

`/sdd` loads the skill. The skill derives the current stage from what exists
under `.specify/`, runs the matching `/speckit.*` command, applies the gates,
and names the next stage. There is no state file to go stale: the artifacts
are the state.

```text
/sdd Build a photo organizer with albums grouped by date
```

```text
/sdd          # advance whatever stage the project is in
```

One stage per run: it runs, reports the verdict, and stops so you can review.
The implement → converge loop is the exception; it repeats until converge
reports `Converged`.

## Install

Run these in the project where you want SDD.

**1. spec-kit** (the pipeline):

```sh
uv tool install specify-cli    # or: pipx install specify-cli
```

**2. Gates:**

```sh
npx skills add blader/humanizer --agent opencode        # prose gate
```

Add `--global` to install it for every project. The code gate is installed
once, globally, per the [ponytail README](https://github.com/DietrichGebert/ponytail).

**3. This pack:**

```sh
git clone https://github.com/pjotrvv/opencode-sdd-orchestrator /tmp/sdd-orch
cp -r /tmp/sdd-orch/.opencode .
rm -rf /tmp/sdd-orch
```

For every project instead of one, copy the two files into the global dirs:

```sh
cp -r /tmp/sdd-orch/.opencode/commands/sdd.md ~/.config/opencode/commands/
cp -r /tmp/sdd-orch/.opencode/skills/sdd-orchestrator ~/.config/opencode/skills/
```

**4. First run:** `/sdd <what you want to build>`. On a project without
`.specify/` the skill asks, then runs
`specify init --here --force --integration opencode` to install the
`/speckit.*` commands.

## Requirements

- OpenCode v2. No plugin, no runtime, no build step.
- Missing gates do not stop the pipeline; `/sdd` says what it skipped.

## License

MIT. The three upstream projects are MIT licensed by their own authors.
