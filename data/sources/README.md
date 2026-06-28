# Source syllabus PDFs

This environment's egress policy blocks `moe.gov.sg` / `moe.edu.sg`, so the
syllabus PDFs cannot be auto-downloaded here. **Commit the official MOE PDFs
into this folder** using the exact filenames below — the ingestion pipeline
looks for these names (see `src/pslecompiler/sources.py`).

| Filename | Subject | Version | Effective | Source URL |
|----------|---------|---------|-----------|------------|
| `science-primary-2023.pdf`  | Science | 2023 | from 2023 | https://www.moe.gov.sg/-/media/files/primary/syllabus/2023-primary-science.pdf |
| `maths-primary-2021.pdf`    | Mathematics | 2021 | P6 from 2026 | https://www.moe.gov.sg/-/media/files/primary/2021-primary-mathematics-syllabus-p1-to-p6-updated-october-2025.pdf |
| `english-primary-2020.pdf`  | English | 2020 | from 2020 | https://libris.nie.edu.sg/sites/default/files/2020-01/primary_els-2020-_syllabus.pdf |
| `chinese-primary-2015.pdf`  | Chinese | 2015 | current PSLE cohort | https://www.moe.gov.sg/-/media/files/primary/chinese-primary-2015.pdf |
| `chinese-primary-2024.pdf`  | Chinese | 2024 | P1 from 2026 | https://www.moe.gov.sg/-/media/files/primary/cl-syllabus-pri-2024.pdf |

The **vertical slice** for this build is `science-primary-2023.pdf`. Once it is
committed, run:

```bash
pslecompiler ingest --source science-primary-2023.pdf
```

PDFs are intentionally **not** git-ignored (they are the ingestion inputs).
