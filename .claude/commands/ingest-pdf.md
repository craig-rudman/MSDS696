---
description: Ingest a new source PDF into the literature review (rename, cite, summarize)
---

Ingest new source PDF(s) the student has dropped into `literature/pdf/`.

This is the student-triggered literature-ingestion flow. Follow the conventions in
`literature/CLAUDE.md` exactly — especially: cite in APA 7th edition, never fabricate a
citation, and keep abstracts descriptive only.

Arguments (optional): $ARGUMENTS — a specific filename to process. If omitted, find the
PDF(s) in `literature/pdf/` that have not yet been renamed to the
`author-year-shorttitle.pdf` convention and process each.

Run this flow for each PDF to ingest:

1. **Read** the PDF (front matter, abstract, and enough of the body to describe its scope,
   structure, and what it reports). Extract citation metadata from the source itself.

2. **Build the APA 7th citation** from details actually found in the source. Do not invent
   authors, titles, years, DOIs, page numbers, or URLs. If any field is ambiguous or
   missing — year vs. `n.d.`, an unclear author, an edition, a URL that needs confirming —
   **stop and ask the student** before writing it. This human check on citations is the
   point of keeping ingestion student-triggered; do not skip it.

3. **Rename** the file to `author-year-shorttitle.pdf` (first-author surname, year, then a
   few title keywords; lowercase, hyphenated) inside `literature/pdf/`.

4. **Add** the citation plus a **descriptive-only** abstract to `literature.md`, under the
   appropriate section (`## Literature` for papers/reports). The abstract describes scope,
   structure, and what the resource reports — no analysis, commentary, relevance notes,
   method tie-backs, or caveats. Method-relevance analysis belongs in the synthesis, only
   when the student asks.

After ingesting, briefly report what was renamed and added, note any citation field you had
to confirm with the student, and offer to log the addition to
`coursework/collaboration_log.md` if the source materially advances the project.
