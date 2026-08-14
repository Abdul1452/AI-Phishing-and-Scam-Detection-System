---
name: 'Tests'
description: 'pytest rules: offline, mocked inference, eager Celery'
applyTo: 'tests/**'
---

# Tests

`pytest`. The suite runs offline on a laptop with no containers started.

Never download a model and never touch the network. Mock at the model wrapper
class in `app/workers/`, so the task and queue path still execute for real.

Run Celery in eager mode to test submit-to-result in process. Do not require a
live Redis for unit tests; fake it or use a stub client.

Every route gets its rejection cases, not only the happy path. For uploads that
means a file over 10 MB, a wrong content type, a `.txt` renamed to `.png`, an
empty file, and a missing field.

Assert that a returned `Assessment` always carries a non-empty caveat. That test
is the one keeping an ethics claim honest, so do not delete it to make a refactor
pass.

Assert that an oversized upload is rejected before the body is read.

Assert on behaviour and status codes, not on log text or exact wording. Wording
will change.

Keep tests fast. If one takes over a second, something real is running that
should be mocked.

Do not write tests that assert model accuracy or output on real samples. The
models are pretrained and unmeasured, so those tests would be flaky and the
numbers unsupported.

Do not change application code to make a test pass. If the application is wrong,
say which line.