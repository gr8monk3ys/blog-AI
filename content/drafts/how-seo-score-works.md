---
title: How the SEO Score Actually Works (and What to Fix First When It Fails)
date: 2026-10-01
excerpt: The five dimensions behind the SEO score, how they're weighted, and why readability is the one writers chase first even though it matters least.
slug: how-seo-score-works
tags: [seo, ai-writing, content-ops]
draft: true
---

## Why "the SEO score is low" isn't one problem

A single number is easy to react to and hard to act on. When a draft comes back with an SEO score of 54, the instinct is to reread the whole thing for anything that feels "off." That's slow, and it usually lands on the wrong fix, because the score isn't one measurement — it's five, combined with different weights, and most of the weight sits in places a read-through won't catch.

## The five dimensions, and what they're actually worth

The overall score is a weighted sum of five sub-scores, each 0-100:

- **Topic coverage — 30%.** Does the draft cover the topics that competing top-ranking pages cover?
- **Term usage — 25%.** Does it use the semantically related terms search engines associate with the keyword?
- **Structure — 20%.** Do the draft's headings align with the heading patterns of top-ranking competitors?
- **Word count — 15%.** Is the length close to what's actually ranking for this keyword?
- **Readability — 10%.** A simplified Flesch Reading Ease estimate from sentence and word length.

That ordering surprises most people the first time they see it. Readability is the dimension a human editor notices fastest — clunky sentences jump out on a read-through — and it's worth the least of the five. Topic coverage, the dimension that requires actually knowing what the top-ranking pages for a keyword say, carries three times the weight and is invisible without the competitive data behind it.

## Where the competitive data comes from

Topic coverage, term usage, structure, and the target word count aren't guessed — they come from an actual SERP analysis for the target keyword: the top-ranking Google results are fetched and an LLM pass extracts the topics those pages share, the headings they use, the "People Also Ask" questions they answer, and a list of semantically related terms, plus a recommended word count based on how long the competing pages actually are. The score then checks the draft against that extracted data, not against a generic SEO checklist. A draft can be well-written and still score low on topic coverage if it skips something every top-ranking competitor covers.

Readability is the one exception — it's computed from the draft alone, with no competitive lookup, which is part of why it's weighted lowest. It tells you whether the sentences are readable; it doesn't tell you whether the content is complete.

## What "passing" means

A draft passes only when every dimension clears its own floor, not just the overall average:

- Overall: 70+
- Topic coverage: 60+
- Term usage, structure, word count, readability: 50+ each

That matters because a draft can have a respectable overall score and still fail outright. A piece that nails readability and word count but ignores half the topics competitors cover can post an overall number in the 60s while failing the topic coverage floor on its own — the average hides exactly the gap that needed fixing.

## The automatic fix-up loop, and its limit

Scoring a draft against the SERP data also produces a prioritized list of suggestions — add this heading, cover this topic, include this term — ranked high, medium, or low. The optimization pass takes the top three high-priority suggestions, asks the model to rewrite the draft around them while keeping the same structure and voice, and rescores. By default it tries this up to three times. If a draft is still short of the thresholds after the third pass, it ships as the best version reached, not a passing one — the loop doesn't retry indefinitely, and a human read-through at that point is the actual next step, not another automated pass.

## What to fix first, in priority order

When a score comes back low, work down the weights, not down the page:

1. **Check topic coverage before anything else.** If the draft is missing topics every competitor covers, no amount of sentence-level polish moves the number that matters most. Read the missing-topics list, not the draft.
2. **Add the missing terms next**, but naturally — term usage checks for presence, not frequency, so there's no benefit to repeating a term past the first natural use.
3. **Match the heading pattern**, if structure is the laggard. A draft with three headings scores worse on structure than one with five that cover the same ground, independent of prose quality.
4. **Get the length into the 80-120% band of the recommended word count.** Scores drop off in both directions — padding a short draft to hit a number works about as well as cutting a long one does, which is to say: match the target, don't just move toward it.
5. **Leave readability for last.** It's real, but it's one-tenth of the score, and it's the dimension most likely to already be fine.

## Where this fits with the rest of the pipeline

SEO scoring runs on the content itself — it has nothing to say about whether a claim in that content is true, which is what fact-checking inside /generate is for, or about whether the wording is original, which is what /blog/ai-content-plagiarism-check covers. And none of the three dimensions that need competitive data (topic coverage, term usage, structure) will score well if the draft was never run through SERP analysis in the first place — a brand-voice-trained draft from /blog/keep-ai-content-on-brand's workflow still needs the keyword data to optimize against. The three checks are independent and a draft can pass any one of them while failing the other two.

## A checklist for a low score

- Pull the missing-topics list before rereading the draft — it tells you where the 30% went.
- Treat the term list as a coverage check, not a quota; one natural use per term is enough.
- Compare your heading list against the suggested headings directly, not from memory.
- Check word count as a ratio to the recommendation, not against a fixed target like "1,500 words is always enough."
- Don't spend a fourth optimization pass chasing a dimension that's already above its floor — fix whichever one is still under 50 (or under 60 for topic coverage).

None of this replaces an editor's judgment about whether the piece is actually good. It just tells you, before publishing, which 30% of "good" the draft is currently missing.
