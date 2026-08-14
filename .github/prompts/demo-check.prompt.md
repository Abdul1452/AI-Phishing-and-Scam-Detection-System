---
description: Check the repository is ready to demo on a laptop that has never run it.
---

# Demo readiness check

Walk the repository and report anything that would break a live demo. Do not fix
anything; produce a list.

Check that `docker compose up` starts all four services with no manual step
beforehand, and that every environment variable the code reads has a default or
appears in `.env.example`.

Check that the worker loads its models at process start and that a first request
after a cold start does not time out.

Check that a submission with an empty message, a 15 MB file, a `.txt` renamed to
`.png`, and a two-character message each return a readable error rather than a
traceback.

Check that a result renders with its caveat visible, and that the result is
distinguishable in greyscale.

Check that no accuracy figure, unmeasured claim, or MITRE identifier other than
T1598 appears in the UI, the README, or the code comments.

Check that the sample data used in the demo is committed and does not contain a
real person's message, email address, or photograph.

Report each finding as: what breaks, what the audience would see, and the
smallest fix. Order by how bad it looks on a projector.
