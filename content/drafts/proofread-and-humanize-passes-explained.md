---
title: What the Proofread and Humanize Passes Actually Do to an AI Draft
date: 2026-10-29
excerpt: What happens to a draft between generation and your screen when proofreading and humanizing are switched on, what each pass is told to change, and the one setting the humanize pass ignores.
slug: proofread-and-humanize-passes-explained
tags: [ai-writing, editing, brand-voice, workflow]
draft: true
---

## Two switches most people never look at

On /generate, two toggles sit under the main settings: *Proofread content* and *Humanize content*. Both are on by default, so most drafts go through them without anyone deciding they should. That is a reasonable default. It is still worth knowing what the two passes do, because they change the text after it is written, and the changes are not always the ones you would guess from the labels.

This post walks through the order things happen in, what each pass is instructed to change, and where that leaves the editing work you still need to do yourself.

## The order of operations

When you generate a blog post, the draft goes through these steps in this order:

1. **Generation.** The outline and sections are written using your topic, keywords, tone and, if one is selected, your brand voice profile.
2. **Proofread** (if on).
3. **Humanize** (if on).
4. **SEO optimization** (Pro, if on).
5. **Fact-check** (Pro, if on).

Two things follow from that order. First, the fact-check reads the final, humanized text, not the first draft, so anything the humanize pass changes is still checked. Second, both post-processing passes work **one subsection at a time**. Each piece of body text under a heading is sent to the model on its own. Neither pass ever sees the whole post, so neither one can fix repetition between sections, a weak transition from one heading to the next, or an argument that wanders over the length of the piece.

## What the proofread pass does

Proofreading is a two-step process for each subsection:

- **Find issues.** The model is asked to list specific problems in three groups: grammar (agreement, tense, dangling modifiers, comma splices), spelling (typos, confused homophones, inconsistent spelling of the same term) and style (unnecessary passive voice, wordiness, weak intensifiers, repeated sentence shapes, and stock AI phrases such as "it's important to note that"). It is told to flag real errors rather than matters of taste.
- **Apply fixes.** Only if it found something does a second call rewrite the subsection with those corrections. A clean subsection is left exactly as it was.

The list of issues itself is not shown to you; you get the corrected text. That means you cannot see what was changed, only the result. If you want to know what the proofreader caught, generate once with the pass off and once with it on, and compare.

The proofreader does not look for copied text at all; its plagiarism check is switched off in this pass. For a similarity check before publishing, use /plagiarism; /blog/ai-content-plagiarism-check explains what that check can and cannot tell you.

## What the humanize pass does

Humanizing is a single rewrite of each subsection. The instructions are specific, which is why the result usually reads better:

- **Sentence rhythm.** Mix short, medium and long sentences, and let some start with "But", "And", "So" or "Still".
- **Stock phrasing out.** Replace phrases like "in today's fast-paced world", "furthermore", "utilize", "leverage", "delve", "robust" and "seamless" with plainer words, and turn most semicolons into full stops or dashes.
- **Human texture in.** Use contractions, the occasional dash or short aside, and speak to the reader as "you".
- **Plainer transitions.** "However" becomes "But" or "That said", "therefore" becomes "So".
- **Meaning kept.** Keep every fact, number and argument, keep the structure, and add no new claims.

There is one tension in that list worth knowing about. Alongside "add no new claims", the pass is also asked to include a concrete example, analogy or specific detail where the original is vague. Most of the time that produces a helpful illustration. Sometimes it produces a specific-sounding detail that was not in the draft and is not true. This is the main reason to read humanized drafts as carefully as unhumanized ones, and to keep the fact-check on for anything with numbers in it. /blog/ai-fact-checking-confidence-scores covers what the fact-check catches and what it misses.

## The setting the humanize pass ignores

This is the part that surprises people. The generation step uses the tone you pick (informative, conversational, professional, friendly, authoritative or technical) and your brand voice profile if one is selected. The humanize pass does not receive either. It rewrites every subsection with the same fixed voice settings: a casual tone, neutral formality and a friendly personality.

In practice:

- If you chose **conversational** or **friendly**, the two agree and humanizing mostly polishes.
- If you chose **professional**, **authoritative** or **technical**, the humanize pass pulls the draft toward a looser, chattier register than you asked for, with more contractions and asides than a formal piece usually wants.
- If you trained a **brand voice** on /brand, the generation step writes toward it, and the humanize pass then rewrites the text with its own defaults. Distinctive habits from your profile, such as a house preference for short paragraphs or a deliberately formal register, can be smoothed away.

So the rule of thumb is simple. For formal or technical pieces, and for anything where a trained brand voice matters, try generating with *Humanize content* switched off and compare the two versions before deciding. /blog/keep-ai-content-on-brand goes through setting up a profile and checking a draft against it.

## What neither pass does

Even with both switched on, a few jobs stay with you:

- **Structure.** Neither pass sees the whole post, so section order, repetition across headings and the overall argument are yours to fix.
- **Facts.** Proofreading does not check claims at all, and humanizing can add specific-sounding detail. Check every statistic, date and named source.
- **Search fit.** Neither pass looks at keywords or competing pages. If the post is meant to rank, run it through the SEO score after editing; /blog/how-seo-score-works explains what to fix first.
- **Detection.** The humanize pass is written to make text read better, not to defeat AI detectors, and nothing in it is tested against one. Treat it as an editing aid, not a disguise.

## A short checklist

- Leave proofreading on. It only rewrites a subsection when it finds something.
- Keep humanizing on for conversational and friendly pieces.
- Turn humanizing off, or compare both versions, for professional, authoritative and technical tones and for brand-voice work.
- Read humanized drafts for specific details that were not in your brief, and keep the fact-check on when numbers matter.
- Do the structural edit yourself. Both passes work one subsection at a time.

The two passes take care of the line-level cleanup that makes a first draft tiring to edit. Knowing where they stop, and the one setting the humanize pass ignores, is what lets you trust them with that job and keep the rest for yourself.
