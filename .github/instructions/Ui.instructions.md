---
name: 'Streamlit UI'
description: 'UI rules: polling, result presentation, and accessibility'
applyTo: 'ui/**'
---

# Streamlit UI

The UI talks to the API over HTTP and nothing else. No Redis client, no Celery
import, no `transformers`, no reaching into `app/`.

Submit returns a job ID. Poll the status route on an interval with a visible
progress indicator and a timeout that ends in a readable message rather than an
endless spinner.

## Accessibility

This is graded, and every rule here is checkable on a projector.

Every input has a visible label. Placeholder text is not a label; it disappears
when typing starts and screen readers treat it differently.

Never signal a result by colour alone. Each result gets text and an icon or shape
next to the colour, so it survives greyscale and colour blindness.

Text and background contrast at least 4.5:1. Do not rely on Streamlit defaults
being sufficient without checking.

Error messages say what went wrong and what to do next.

The whole flow works from the keyboard, including submitting and reading the
result. Do not build an interaction that needs hover or drag.

Do not hide meaning in an emoji alone.

## Presenting a result

Show the label, the score, the signals, and the caveat. The caveat is never
collapsed, never behind an expander, never conditional.

Frame the result as an assessment the user should judge, not an answer. The
wording near the result makes clear it can be wrong in both directions.

Do not display a percentage as though it were accuracy. It is a model score on
one submission.

Do not display raw model output, tracebacks, or internal field names.