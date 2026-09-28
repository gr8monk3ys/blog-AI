---
title: How AI Fact-Checking Confidence Scores Work (and When to Trust Them)
date: 2026-09-28
excerpt: What happens when a draft's claims get cross-referenced against live sources, how the confidence score is built, and where a human still needs to step in.
slug: ai-fact-checking-confidence-scores
tags: [fact-checking, ai-writing, seo, content-ops]
draft: true
---

## The problem a spell-checker can't solve

A draft can be grammatically perfect, on-brand, and still wrong. Not wrong in a way that reads as wrong — a confident sentence with a specific number in it, sourced from whatever the model saw during training instead of the current state of the world. That's the failure mode fact-checking exists to catch, and it's a different problem than tone or originality: the sentence can be original, well-written, and still cite a statistic that changed two years ago.

The fix isn't asking the model to "double-check itself." A model checking its own claim against its own memory is the same blind spot twice. What actually works is pulling in sources outside the model at generation time and testing each claim against them.

## What happens during generation

Every /generate run that has fact-checking enabled follows the same three-step pass after the draft is written:

**Claim extraction.** The draft is scanned for statements that could be verified — statistics, dates, named studies, direct attributions — as distinct from opinion or stylistic filler. "Adoption grew 40% year over year" is a claim. "This approach works well for most teams" is not.

**Source cross-referencing.** Each extracted claim is checked against live web sources pulled through SerpAPI, Tavily, and Metaphor, not against the model's training data. This is the part that catches claims that were true when the model was trained and aren't anymore, along with claims that were never quite right.

**Confidence scoring.** Each claim gets a score based on how many independent sources support it, how directly those sources match the specific number or fact stated, and how recent those sources are. A claim backed by three current sources that agree scores very differently than a claim with one older source that's adjacent but not exact.

## Reading the score correctly

A confidence score is a measure of source support, not a truth guarantee. Three different failure modes produce a low score for three different reasons, and they call for different fixes:

- **No sources found.** The claim might be true but is too niche, too new, or too specific for the search providers to surface anything. Fix: rewrite to cite the specific source yourself, or soften the claim to something the draft can actually back up.
- **Sources disagree.** Genuinely contested territory — a statistic that different outlets report differently, or a fast-moving number that's already stale in half the search results. Fix: name the source in the text itself so the reader can weigh it, rather than stating the number as settled fact.
- **Sources found but don't quite match.** The closest sources are adjacent to the claim, not a direct match — a study about a related but different population, or a number from a different year than the one stated. Fix: tighten the claim to what the sources actually support.

A high score across the board means the claim is well-supported by current, consistent sources — it doesn't mean the draft is done. It means the easy category of error, the one a human proofreader would probably miss because the sentence reads fine, has been checked. Everything that isn't a checkable factual claim — argument structure, whether the framing is fair, whether the piece says something worth reading — is still an editorial judgment call.

## Where this fits with everything else in the pipeline

Fact-checking, plagiarism checking, and brand-voice matching solve three different problems and none of them substitutes for the others. Brand voice is about whether the draft sounds like you. Plagiarism checking is about whether the wording is original. Fact-checking is about whether the claims are current and supported. A draft can pass all three checks and still need an editorial pass, and it can fail one while passing the other two — a perfectly on-brand, fully original sentence can still cite a number that's two years stale.

Run fact-checking as part of generation, not as a separate step bolted on afterward — a claim extracted from the final draft is a claim checked against the text the reader will actually see, not an earlier version that already changed.

## A pre-publish checklist

- Treat a high confidence score as "well-supported by current sources," not "verified true" — the two aren't the same claim.
- For any claim scored low because sources disagree, name the source in the sentence instead of stating the number as settled.
- For a claim with no sources found, either cite your own source directly or soften the wording to what you can actually back up.
- Re-run the check after substantive edits — a claim's supporting sources are tied to its exact wording, and a rewrite can change what it's even checking.
- Remember fact-checking, plagiarism checking, and brand-voice matching each catch a different failure mode; passing one says nothing about the other two.

Fact-checking is part of the Pro workflow — check /pricing for plan details, and /tools for where it sits alongside plagiarism checking and SEO scoring in the rest of the pipeline.
