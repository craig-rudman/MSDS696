# Week 5 · Critical-Thinking Activity
Chart Redesign: Find the Lie, Then Fix It
20 points
due Sunday 11:59 PM
D2L Assignments → “Wk 5 · Chart Redesign Activity”

## Goal
Take a chart that misleads on purpose, name exactly how it does it, and rebuild it so it tells the truth — without becoming boring.

*Why this exists:* In class we practice making honest charts. This activity points the same skill the other way: at the charts other people put in front of you. You will be handed misleading visuals for the rest of your career — by vendors, by the news, by colleagues who didn't mean to. Spotting the move is the defense.

## Step 1 — Get your chart
Use one of the four charts in the chart bank, posted alongside this handout in D2L Content → Week 5 (chart_bank/). Each one contains one dominant, deliberate distortion. Pick whichever you like — you only need one.

Chart A — Patient safety scores. A hospital quality dashboard reporting a new protocol's effect.
Chart B — Highway fatalities. A state DOT chart covering a speed-limit change.
Chart C — Platform response time. A software vendor's performance benchmark.
Chart D — Revenue by product line. A company's FY2025 revenue comparison.

Optional alternative: you may use a chart you found in the wild (news article, vendor deck, annual report, social media) if it contains a real, nameable distortion — not merely an ugly chart. Include the source link. If you're not sure it qualifies, use the bank; there's no bonus for going hunting.

Don't use one of your own project figures for this one. Your charts are probably cluttered, not dishonest — and there'd be no lie to find. Your own visuals get their workout in the pod lab and the status report.

## Step 2 — Write it up (four parts)
These four parts are the assignment. Use them as your headings.

1. Name the lie. Not “it's misleading” — which distortion, and the mechanism. What does the chart make a reader believe, and what does the data actually say? Give the numbers.
2. Name the victim. Who could be misled by this, and what decision would they get wrong? A chart that fools nobody isn't a problem; a chart that changes a budget, a policy, or a purchase is.
3. Rebuild it. Produce an honest version and label each fix — what you changed and why. Recreating the data by eye from the chart is fine; you don't need the original file. Any tool: Python, Excel, whatever.
4. Say what you preserved. An honest chart still has to make a point. What is the real, defensible message of your rebuilt version? If your fix turned it into a shrug, you've over-corrected.

## Example (a chart not in your bank, so you can see the shape without being handed an answer):
1. The y-axis starts at 92%, not 0. A move from 93.1% to 94.0% — nine-tenths of a point — fills the entire plot area and reads as a doubling.
2. A VP approving next year's budget sees a program transforming the metric and renews it. The honest read is a 0.9-point drift that may be noise.
3. Rebuilt with a zero baseline; added a bracket annotating the 0.9-point change so the real movement is still visible rather than invisible.
4. Preserved message: the metric is improving slowly and consistently — four straight quarters of gains is a genuine result, just a small one.

## Format
One document (Word, PDF, or Markdown) containing: the original chart, your four sections, and your rebuilt chart. Roughly one to two pages. Length is not the point; specificity is.

## How it's graded
20 points
Scored on the standard Participation Activity rubric.

| Criterion | Pts | Full credit looks like |
| --- | --- | --- |
| Engagement & completion | 6 | All four parts present, on time, with both charts included. The rebuild is actually rebuilt — not described. |
| Quality of thinking | 9 | The distortion is named precisely and its mechanism explained. The decision at risk is real and specific. Your fixes address the lie rather than just prettifying the chart. |
| Constructiveness & specificity | 5 | Numbers, not adjectives. Each fix labeled. The preserved message is stated as a sentence someone could act on. |

You've nailed it when
You can state the lie in one sentence, with a number in it
A named person makes a named decision differently because of the distortion
Every change to your rebuild is labeled and justified
Your honest chart still says something worth hearing
Common way to lose points: stopping at “the axis is misleading.” That's an observation, not an analysis. The points are in how much it distorts, who it fools, and what it costs them.
This week's other two submissions are separate: your Status Report (2–3 polished visuals) and your Practice Talk (record, post, reply to podmates). Don't merge them with this.