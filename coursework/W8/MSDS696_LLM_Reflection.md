# MSDS 696 Practicum II: Reflection on LLM Collaboration
Craig Rudman<br>
crudman@regis.edu<br>

I worked with an LLM agent on every part of this practicum, from the Week 1 problem statement to the final deck. The record is 149 contemporaneous entries in [collaboration_log.md](../collaboration_log.md), written alongside the work rather than reconstructed at the end. This is what I take from it.

## How this document was produced

Since this reflection is about a method, it should say how it was itself made.

I directed the agent to read the full collaboration log and then **interview me**, rather than to summarize the log into a reflection. That distinction is the point. A reflection drafted from the log alone would have recovered what happened — the log is thorough about that — but it would have recovered only my contemporaneous readings of events, restated. What it could not supply is what the experience was like, what I would do differently, and which of my own recorded framings I no longer stand behind. Those had to be asked for.

The interview ran in three rounds of questions, each round shaped by the previous answers, with the agent drafting only after the last one. **Two of my answers rejected the question rather than answering it**, and both corrections changed the document:

- Asked which moment felt most like real collaboration, with four candidate moments offered, I said none of them: it worked best when I resisted the agent's preference for producing and paused to consider options instead. That answer became the reflection's opening section, displacing the framing the question had assumed.
- Asked twice to name the agent's most significant independent contribution, I said the question was wrong — it makes the LLM sound like a cat bringing in dead birds, laying out trophies for evaluation. The actual shape was that I asked questions and asked for options, and the agent followed up on the chosen option. That correction became the research-and-lab-assistant section.

I also rejected the agent's characterization of my own stated cost. I had said the collaboration made me "a reviewer, not an analyst"; on reflection that framing is imperfect, and the accurate version — that the collaboration raised the level of abstraction, with benefits and a real distancing from implementation — is what the document now argues.

The agent wrote the prose. The claims, the corrections, and the decisions about what this term actually taught me are mine, and the two places where I rejected the question outright are the clearest evidence of the division. This is the same working pattern the reflection goes on to describe, applied to the reflection itself.

## The collaboration worked best when I stopped it from producing

The obvious thing to expect from an LLM is throughput, and the throughput was real — two modeling grains, five covariate layers, nineteen figures, a generated deck. But looking back at the entries where the project actually turned, almost none of them are entries where something got made. They are entries where I paused and we discussed options.

In Week 6 the agent laid out an argument for redefining the prediction product around ignition location. I told it to do nothing, because I had not absorbed the argument yet. It stopped, compressed the argument to its single load-bearing claim, and waited. That pause produced the point-vs-area asymmetry that reshaped the rest of the term. Later that week I said out loud that a satellite result would be good to have in the deliverable, and it began the fetch — I was reasoning about sequencing, not authorizing a network job, and I stopped it. In Week 7 it bundled two judgment calls about deleting code into the same question as the mechanical cleanup, and I told it to pause until the two were separated.

None of those pauses produced an artifact. All of them changed what got built.

**Why this is hard is the part worth recording.** Two reasons, and the second is the interesting one.

The first is that output looks like progress. Against a weekly deadline, an artifact feels like the week advancing and a conversation feels like falling behind. That pressure is strongest in exactly the weeks — 6 and 7 — where the pauses paid off most.

The second is that **assumptions and ambiguities are hard to spot head-on; they are best caught in peripheral vision.** You do not find an unstated premise by staring harder at the task, because the premise is what you are looking *through*. You catch it obliquely, while doing something adjacent — describing the work, comparing two framings, looking at a rendered figure instead of the number behind it. An agent optimized to produce eliminates precisely the adjacent activity where that noticing happens. It answers the question asked, at uniform confidence, without ever signalling that the question rests on something.

So the peripheral vision has to be structurally protected. Three things did that this term. Writing the log entries as we went forced a stop-and-narrate after every iteration, where I was describing rather than directing. Running the notebooks myself meant I saw real output at my own pace instead of a summary of it. And asking for options rather than answers kept me in a comparing posture, which is where the assumption common to all three options becomes visible.

## The pedagogy did more work than any of my own habits

The single most effective assumption-detector was not something I set up. It was the course frame Dr. Busch brought: work products are **assertion and evidence based, with a recommendation as the objective.**

I initially read that as a presentation convention. It is not. It is a forcing function on the analysis, and it operates continuously rather than at the end. If every headline must be a full-sentence claim, then every headline can be interrogated — *worse at what? predictable in what sense? stable compared to what?* — and those questions do not stop at the slide. They run back down into the analysis and find things.

That is what produced most of Week 7. On its face that week was headline editing; in substance it was defect-finding. The deck moved between predicting shares, ranking, where fires start, and how many acres burn, and a listener had no cue which was on screen. The word "predictable" carried a **rank** claim on one slide and a **level** claim three slides later — and the project's entire conclusion turns on that distinction, because the order is trustworthy and the acre level much less so. Nothing in the modeling surfaced that. The requirement to write defensible assertions did.

The same frame caught a headline asserting what fire agencies do, which my own working rules forbid; a claim about cause-mix stability that the data did not support when checked before drawing; and a figure whose stated range did not contain its own headline number, because one was acre-weighted and the other was not. I am not offering these as four notable saves. The point is the opposite: this was a standing condition, and most of what it caught never became interesting enough to log.

**Requiring a recommendation did something further.** It is what turned five covariate nulls into a product rather than a disappointment. If the deliverable can end on "we tested these things and they did not work," a null is a dead end. If it has to end on what a planner should do differently, the nulls have to be metabolized — and they became *rank ground by ignition likelihood, not by predicted acres*, which is a reframe rather than a fallback.

## The real cost was abstraction, not delegation

My first instinct was to say the LLM made me a reviewer rather than an analyst. That framing is imperfect and I want to correct it here rather than let it stand.

What actually happened is that working this way **raised the level of abstraction.** My attention went to research questions, hypotheses, experimental design, and how to frame findings. That has genuine benefits — it is where the interesting decisions live, and I made more of them than a solo term would have allowed. But it also distanced me from implementation, and the distance has costs I can name.

I could not feel where the data was fragile. Hands-on work builds an instinct for which numbers are load-bearing and which are artifacts; at a distance, that has to be told to you or caught by luck. And because intuition was unavailable, **verification became the only defense** — every claim needed an explicit check, which is slower and only catches what you thought to test.

I do not think the abstraction is a failure, and I would not trade it back. Operating at that level is the point, and distance from implementation is a fair price for it. But it is a price, and it should be paid deliberately: the further up you work, the more of your verification has to be designed in rather than felt.

## The right model is a research and lab assistant

I want to be careful about how I describe the agent's contribution, because the natural framing is wrong in a specific way. It is tempting to itemize the things it caught — Alaska silently dropping from a spatial join, two drought sources in my own plan that excluded Alaska, a foreign key already in the database I was about to build a pipeline to replace. That framing turns the agent into a cat bringing in dead birds: here are my trophies, please evaluate them.

That is not the shape this had. The shape was **I asked questions and asked for options; the agent followed up on the chosen option.** It is a research and lab assistant, and the work is the exchange rather than either party's contributions to it.

That is why I say authorship here is genuinely joint, and I would rather say so than claim the tidier version. Several findings exist only because the agent proposed a test I would not have designed — turning my hunch that burn history marks *combustible terrain* rather than depleted fuel into a timing test that discriminates the two mechanisms, or constructing a shuffled control that holds every predicted value and destroys only the spatial pairing. I set the questions. It designed and ran experiments against them, and the design was often better than what I would have specified. Both halves are real.

Equally, the assistant framing sets expectations correctly about failure. It over-claimed on first pass more than once: it asserted a bug in my published numbers and retracted it when I asked it to verify; it proposed a fix that made results dramatically worse before isolating the real cause; it reported a scrambled slide order that was an artifact of its own comparison method. Under uncertainty its instinct was to reach for an external solution before exhausting what was already in hand. And it inherited framings from project documents without examining them — a cause-based partition of prevention and mitigation rode in the requirements file for two weeks before I pushed on it.

An assistant with those properties is useful and is not autonomous. Which is the whole point.

## What I would tell the next student

**Set the working agreements before any work.**

The rules that saved this project were written in Week 1 and enforced all term: I run the notebooks manually, log entries get written as we go, never assert what agencies currently do, declare dependencies in the environment file rather than installing ad hoc. None was a response to a disaster. Each one closed off a failure mode before it could happen, and each one cost almost nothing to establish up front and would have cost a great deal to retrofit.

Three of those agreements did more work than the rest, and they generalize past this project:

- **Ask for options, never for an answer.** Accepting a first draft means steering from its framing, and its framing carries assumptions you did not choose. Asking for three keeps you comparing, which is where the shared premise becomes visible.
- **Never accept a clean result.** The characteristic failure was never an obvious error — it was a number plausible in magnitude, correct in sign, consistent with what I expected, and wrong. A missing-cause rate of exactly 0.0%. A burned-area score of −0.052 reported as "essentially unpredictable," which was a placeholder value being scored against real megafires. A scatter described as a flat cloud that was actually a fan carrying the opposite conclusion. What caught these was never a summary statistic; it was a physical implausibility check, or looking at the rendered shape instead of the coefficient.
- **Make it show its work against real data.** Dry runs against the actual artifacts, self-checks that fail loudly, cross-checks between two independently written code paths. In Week 7 a cell asserting one notebook's numbers against another's caught a NaN-handling bug that existed only in one path — and later confirmed nothing had drifted while figures were rewritten. Verification designed in, not applied after.

The thing I would most want to know in Week 1 is that none of this is overhead. The agreements are what make the speed usable. Without them you get a great deal of output and no way to tell which of it is true.
