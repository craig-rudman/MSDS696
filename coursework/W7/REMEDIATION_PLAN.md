# W7 Remediation Plan

**Written 2026-08-17.** Everything between the current state and the three graded W7
submissions (80 pts), in dependency order. The talk itself is finished — 18 slides,
1,405 words, ~9:58 at 150 wpm, deck reconciled to `final_script.md` and verified
programmatically. What remains is artifacts, not content.

Check items off in place as they are done.

---

## Phase 0 — Do before anything else touches a file

- [ ] **Close `MSDS696_W7_Deck.pptx` in PowerPoint.**
  The deck silently reverted to a pre-edit state once this week; an open PowerPoint
  session writing over a synced file is the only mechanism that explains it. Every
  later phase assumes the committed deck is the real one.

- [ ] **Confirm the deck is what git says it is.**
  ```
  git status --short coursework/W7/MSDS696_W7_Deck.pptx     # expect: clean
  ```
  If it shows modified, the working copy is a PowerPoint save. Decide which to keep
  before proceeding — `git checkout` discards, and the scratchpad holds pre-cut backups.

---

## Phase 1 — Notebooks (~10 min, student-run)

Both are submitted artifacts and both currently misrepresent the code.

- [x] **Run `notebook/16_w7_visuals.ipynb` top to bottom.** — done 2026-08-17.
  All 6 code cells executed. The cross-check printed
  `cross-check vs 08_human_cause.ipynb: all four rungs match`, and every regenerated
  figure came out byte-identical to what is already embedded in the deck, so no
  re-embedding was needed.

- [ ] **Re-run `notebook/06_analysis.ipynb`.**
  One cell only needs it — cell 26's stored output still shows
  `RuntimeWarning: Mean of empty slice`, which was fixed with
  `warnings.catch_warnings()` after that output was captured. Nothing numeric changes.

- [ ] **Commit the executed outputs.**

---

## Phase 2 — Measure the pace (~5 min)

- [ ] **Record slide 3 alone and time it.** 102 words, the densest in the deck.
  - ~41 s → 150 wpm, deck runs ~9:58. No action.
  - ~47 s → 130 wpm, deck runs ~10:45. Either accept, or take the standing cut:
    compress slides 11–12 into one (~80 words, the pair makes one argument).
  - This single measurement replaces every pace estimate in the script's timing table.

---

## Phase 3 — Full Dry Run · 30 pts

D2L Discussions → pod's "Wk 7 · Full Dry Run"

- [ ] **Record the full timed run** against the deck, with a visible clock.
- [ ] **Write the self-assessment.** What ran long, what you fumbled, what you would
      cut next. The assignment asks for it explicitly and it is graded with the video.
- [ ] **Post the recording + self-assessment.**
- [ ] **Reply to podmates in writing.** Required by the assignment ("reply to podmates
      in writing"), not optional.
- [ ] **Note one weak slide and one weak answer**, and fix each. That is the pod-lab
      output the assignment names.

---

## Phase 4 — Executive-Challenge Q&A · 30 pts

D2L Discussions → pod's "Wk 7 · Executive Challenge"

- [ ] **Write your three challenge questions about your own project.** The assignment
      requires you to author these. Candidates, all of which the deck can answer and
      none of which it answers on a slide:
  - *"Most fire is human-caused. Why does your deck say lightning drives the burn?"*
    → by count Human is 61%; by acres Natural is 58.9%. Acres are what a mitigation
    budget is sized against. (Slide 3 WATCH carries both denominators.)
  - *"You are telling me five things did not work. What did I pay for?"*
    → a ranked, per-cell-confidence-flagged siting product, and a measured boundary
    on what pre-season data can do. (Slides 14, 16.)
  - *"If we treat the hexes you rank, how many acres do we save?"*
    → no. A targeting claim, not an efficacy one — no before/after, no control.
    (Slide 16 WATCH.)
- [ ] **Prepare the four defaults** in your audience's voice — executives.
- [ ] **Answer in writing** (async) or live in the pod lab.
- [ ] **Capture your three toughest received questions + the answers you will give
      next time.** This is the named output of the pod lab.

**Preparation already done and worth re-reading before this:** the WATCH blocks are
written as Q&A defenses, and the densest are slide 3 (per-cell confidence), slide 6
(the shuffled control, now the deck's only defense of the skill claim), slide 7
(acre attribution, with a 10-second answer and two escalations), and slide 8
(log scale, and why 687x vs 19x is not a controlled comparison).

---

## Phase 5 — Status Report · 20 pts

D2L Assignments → "Wk 7 · Status Report". **Template is `coursework/W6/MSDS696_W6_Status_Report.md`** —
copy its structure forward, per `CLAUDE.md`.

Four required elements, per the assignment: near-final deck, repo link, decision log,
draft LLM reflection.

- [ ] **Near-final deck** — attach or link `coursework/W7/MSDS696_W7_Deck.pptx`.
- [ ] **Repo link.**
- [ ] **Decision log** — W7's decisions are already written contemporaneously as
      collaboration-log entries 7.1–7.36. The report needs a *summary*, not a re-listing.
      The load-bearing ones:
  - The script became authoritative over the deck and over `build_deck.py` (7.2).
  - Per-cell confidence from trailing dispersion — the strongest new result (7.10).
  - The model-family question closed: ridge beats gradient boosting and still loses
    to the floor; the flat alpha sweep is the evidence it is a ceiling (7.14–7.15).
  - Three ambiguity defects found and fixed: the silent starts→acres switch, "both"
    on slide 8, and "predictable" without a quantity on slide 9 (7.22–7.24).
  - Two slides cut (the shuffled control, the ignition gate) with their evidence
    relocated rather than discarded (7.25, 7.29).
  - The retitle: "Rank the ground, not the fire" (7.34).
  - 1,746 → 1,405 words after the content pass (7.31, 7.36).
- [ ] **Draft LLM reflection.** Material the log already supports, with entry numbers:
  - **Where the agent was wrong and I overrode it:** the 43%/68% reading (7.12), the
    natural-vs-human concentration claim it asserted and had to measure and retract
    (7.19), and my cutting slides it argued to keep (7.25, 7.29).
  - **Where it caught things I would have shipped:** the timing table lying by 1:45
    (7.30), the figure printing the same sentence as my SAY (7.35), the deck silently
    reverted with all 18 notes panes stale (7.36).
  - **The division that worked:** it did mechanical work — audits, syncs, word counts,
    verification — and I made the judgment calls about what earns its place (7.31).
  - **The verification habit that paid off:** every number in the script was a dry-run
    prediction until the notebooks ran; all of it held (7.26).
- [ ] **Next week's To Do** — see Phase 7.

---

## Phase 6 — Repository hygiene (before final submission, not before the dry run)

- [ ] **Decide `src/build_deck.py`'s fate.** It is stale and would revert the deck if
      run: it still lists the cut ignition-gate slide, the pre-retitle title, and
      pre-W7 headlines. Either delete it, or add a header saying the deck is now
      maintained directly and this script is historical. Leaving a runnable script that
      destroys the deliverable is the risk.
- [ ] **Add the three missing data sources to `literature/literature.md`** — MTBS
      (Eidenshink et al. 2007), TerraClimate (Abatzoglou et al. 2018), MODIS MOD13A1
      (Didan 2021). Slide 17 cites them; the literature review does not list them.
- [ ] **Update `CLAUDE.md`'s "What is built"** for the W7 additions: the per-cell
      confidence section exists, but `plot_data_sources` and the ridge rung are not
      named in the pipeline description.

---

## Phase 7 — Carry into W8 (do not do now)

- **The slide 9 sequencing question.** Moving it beside slide 6 drops the deck from
  four target flips to three. Deferred deliberately until after a delivered run, when
  it will be clear whether the flips cost the audience anything.
- **The point-attribution fix.** Circular-burn imputation for large point-only fires;
  designed, not built, and correctly scoped as future work. Rebuilding
  `hex_acres_res5.parquet` invalidates notebooks 13–15 and every acres figure.
- **Same-day escape conditions.** The one question the W6 nulls leave genuinely open,
  and a different data requirement rather than a tuning exercise.
- **A hyperparameter search on the booster.** The flat alpha sweep makes it unpromising,
  which is why it is last.

---

## Definition of done for W7

1. Both notebooks executed and committed.
2. Recording posted with a self-assessment; podmate replies written.
3. Three self-authored challenge questions posed; three received questions answered
   and captured.
4. Status report submitted with deck, repo link, decision log, LLM reflection draft.
5. Collaboration log current through the dry run.
