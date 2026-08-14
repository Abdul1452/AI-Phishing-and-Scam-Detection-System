# Onboarding

Read this once before your first prompt. Ten minutes now saves an argument on
Wednesday.

## First fifteen minutes

Clone the repo, `cp .env.example .env`, then `make test`. Fourteen tests should
pass. Then `docker compose up --build` and check that http://localhost:8501
loads and a pasted message returns a result. If both work, your environment is
correct and any problem after this is a real problem.

In VS Code, open the Chat view and confirm the agent picker lists architect,
implementer, reviewer, test-engineer and docs-writer. If it does not, the
`.github/agents/` files are not being picked up and nothing below will behave as
described.

Then check the tool names actually resolve. Open `reviewer.agent.md`, look at
its `tools` list, and confirm each one exists in your VS Code build. An unknown
tool name is ignored silently, which would quietly give the reviewer edit rights
it is not supposed to have.

## How the repo instructs Copilot

Three layers, and each answers a different question about when it loads.

`.github/copilot-instructions.md` is always active. Stack, scope, boundaries, and
the rules about how results are described.

`.github/instructions/*.instructions.md` load by file path. Editing something
under `app/api/` pulls in the gateway rules automatically; editing a test pulls
in the test rules. You do not select these and you cannot forget them.

`.github/agents/*.agent.md` are chosen per task. They set what the agent does and
which tools it may use. The architect and reviewer are read-only by design.

Instruction files merge rather than replace. Editing `app/api/routes.py` loads
the Python rules, the gateway rules, and the always-on file together. To see what
was applied, expand References on a response, or right-click in Chat and pick
Diagnostics.

## Which agent for what

Use **architect** when you are about to change how services talk to each other,
or when a task is vague enough that you would otherwise start guessing. It
produces a plan and cannot touch files.

Use **implementer** for all code changes. It is the only agent with edit rights.

Use **reviewer** before every pull request. Read-only, checks against the
project instructions.

Use **test-engineer** when adding tests, and after any change to a route or a
task.

Use **docs-writer** for the README and the accessibility, ethics and privacy
sections. It verifies claims against the code instead of describing intentions.

Handoff buttons appear under a finished response: architect hands to
implementer, implementer hands to reviewer or test-engineer. Use them rather than
re-explaining context in a fresh chat.

## Starter prompts

Copy these. Each is scoped so that one person can finish it without colliding
with anyone else. Set the named agent first.

### Replace the text model with a real one

Agent: **implementer**. Files: `app/workers/models.py`, `requirements-ml.txt`,
`Dockerfile.worker`.

> Replace the stub body of `TextClassifier.load` and `TextClassifier.predict` in
> `app/workers/models.py` with a real Hugging Face text-classification pipeline
> using the model ID from settings. Keep the method signatures exactly as they
> are, because the tests mock this class. `predict` must still return a float
> between 0 and 1 and a list of plain-language signals. Uncomment the ML
> requirements install in `Dockerfile.worker` and add the build-time model
> download so the container starts offline. Do not change anything under
> `app/api/`.

### Move the similarity guard into Redis

Agent: **implementer**. Files: `app/api/guards.py`.

> Rewrite `SimilarityGuard` in `app/api/guards.py` to store per-client submission
> history in Redis instead of a process dictionary, with a TTL from settings, and
> to use `rapidfuzz.fuzz.ratio` instead of `difflib.SequenceMatcher`. Keep the
> `check(client_id, payload) -> bool` signature and the `reset()` method, because
> the tests use both. Threshold, window and strike count stay configurable. Keep
> the comment about what this guard does and does not stop, and do not strengthen
> the claim.

### Wire up the image check

Agent: **implementer**. Files: `app/workers/models.py`.

> Replace the stub body of `ImageChecker.load` and `ImageChecker.predict` in
> `app/workers/models.py` with a pretrained image-classification pipeline. Keep
> the signatures. The result caveat must continue to state that this is a
> single-frame, low-confidence check that has not been evaluated on real data. Do
> not add video handling, frame extraction, or audio.

### Accessibility pass on the interface

Agent: **implementer**. Files: `ui/app.py`.

> Review `ui/app.py` against the accessibility rules in
> `.github/instructions/ui.instructions.md` and fix anything failing. Check
> specifically that every input has a visible label, that no result is signalled
> by colour alone, that the flow works from the keyboard, and that every error
> message says what to do next. List what you changed and why.

### Widen the test suite

Agent: **test-engineer**. Files: `tests/`.

> Add tests for the job status route in `app/api/main.py`: a queued job, a
> completed job returning an Assessment with a non-empty caveat, and a failed job
> returning a readable error rather than a traceback. Keep everything offline with
> Celery in eager mode and inference mocked at the model wrapper. Do not change
> application code.

### Write the graded documentation

Agent: **docs-writer**. Files: `README.md`, `docs/`.

> Write the accessibility, ethics, privacy and fairness documentation for this
> project. Read the code first and only claim behaviour you can point at a line
> for. Where the code does not do what the project plan promised, say so plainly.
> The limitations section covers false positives and negatives, variation across
> languages and image quality, what the submission guard does not stop, and the
> single-frame nature of the image check.

### Before you present

Agent: any. Run `/demo-check` in Chat. It walks the repo and reports what would
break on a projector. Do this on Wednesday, not Thursday morning.

## Ground rules

Branch per task, small pull requests, reviewer agent before you open one.

Never commit `.env`. Every new setting goes in `.env.example` and
`app/common/config.py`, never as a literal in code.

If Copilot writes something you would not be able to explain on Thursday, delete
it and ask for a simpler version. Every one of you has to be able to defend every
file.

Do not let an agent add a service, a dependency, or a feature that is not in the
scope list. If it suggests one, that is a conversation for the group, not a
commit.

Write your learning diary at the end of each day. Four people times eight days is
a real cost, and it is much worse discovered on Day 8.
