# Past-year paper PDFs

Commit your past-year PSLE paper PDFs here, then run:

```bash
pslecompiler ingest-paper --paper <filename>.pdf
```

This extracts raw MCQ items; the agent then authors tagging + answer/feedback
(see prompts/), which are merged and QA-checked before export to the app.
