---
title: How to Bulk-Generate Blog Posts from a CSV Without Losing Quality Control
date: 2026-10-26
excerpt: How a bulk run turns a spreadsheet of topics into a batch of drafts, what the cost estimate and provider settings actually do, and how to review fifty drafts without rubber-stamping them.
slug: bulk-generate-blog-posts-from-csv
tags: [bulk-generation, ai-writing, content-ops, workflow]
draft: true
---

## Volume is the easy part

Generating one draft is quick. Generating forty is where a content workflow usually breaks, and it rarely breaks at the generation step. It breaks afterwards, when forty drafts land at once and the review that each one would have had on its own turns into a skim.

Bulk generation in /bulk is built for the first half of that problem: you hand it a list of topics and it produces a draft for each one in a single run. This post walks through how that run works, which settings change the result and which only change the estimate, and how to set up the review so a big batch gets the same scrutiny as a single post.

## Step one: shape the CSV

The input is a CSV with a header row. Only one column is required:

- **`topic`** (required): the working title for the post. It needs at least 3 characters and is capped at 500.
- **`keywords`** (optional): a comma-separated list inside one quoted cell, such as `"content calendar,editorial planning"`. Each keyword is lowercased and trimmed, keywords over 50 characters are cut, and only the first 20 are kept.
- **`tone`** (optional): a tone for that row. A row without one falls back to the shared tone chosen on the page.

Header names are matched without regard to case, and the page offers a template to start from. Rows with an empty topic are skipped and reported by row number, so a missing topic shows up as an error before the run rather than as a blank draft after it.

Two things are easy to get wrong:

1. **Quote the keywords cell.** Commas inside double quotes are kept together; an unquoted keyword list spills into the next column.
2. **Keep each row on one line.** The parser reads the file line by line, so a topic with a line break inside a quoted cell will split into two broken rows.

You can also add or edit items by hand on the page instead of uploading a file. A single run takes up to 100 items.

## Step two: choose the settings

The settings panel controls the cost, the speed and which providers the run uses. What each control actually does:

- **Provider strategy.** *Single provider* sends every item to the provider you pick. *Round robin* rotates through the configured providers item by item. *Cost optimized* and *quality optimized* each pick one provider by a fixed order, cheapest first or highest quality first. None of them switches provider when an item fails. A failed item stays failed until you retry it.
- **Parallel generations.** How many drafts run at once: 1, 2, 3, 5 or 10. Higher numbers finish sooner but do not change the content.
- **Use web research.** Generates each post through the research path instead of the plain one. It adds context to every prompt, so the estimate goes up with it.
- **Proofread and humanize.** Optional passes run on each finished draft with the same provider. Both are on by default on the page. Each one is another model call per item.

## Step three: read the estimate for what it is

As soon as there are items, the page shows an estimated cost, a token count, a confidence percentage and the same batch priced on each provider.

It helps to know how that number is put together. Every blog item is assumed to take the same fixed token budget, plus a little for each keyword and a fixed amount more if research is on. Those totals are multiplied by a per-provider price table. The confidence figure is not computed from your topics at all. It is 80% without research and 70% with it.

The running cost shown during and after the run is also an estimate: each completed item is counted at a flat token figure rather than the tokens it actually used. Both numbers are good for comparing providers and for catching an accidental 100-item run before it starts. Neither one is an invoice.

## Step four: watch the run, and know how it stops

Once started, the run reports progress as items finish: how many completed, how many failed, and which provider handled them. Items finish in whatever order they complete, but the results are sorted back into your CSV order at the end. Three ways a run can end early are worth knowing in advance:

- **Cancel.** Cancelling stops items that have not started yet. Items already being generated finish.
- **Usage limit.** Your plan's quota is checked before each item. Once one item hits the limit, every remaining item in the run is marked failed with a quota error instead of being attempted.
- **Item errors.** One failed topic does not stop the rest. The job finishes as *partial*, and the failed rows keep their error message.

## Step five: retry carefully

Failed items can be retried in one click, optionally on a different provider. The retry is not a replay of the original row, though. It keeps the topic but drops the keywords, uses a professional tone, turns research and humanize off, and leaves proofreading on.

If the keywords or the tone matter for those posts, and in an SEO workflow they usually do, put the failed rows into a fresh CSV and run them again instead of using the retry button.

## Step six: export, then review like an editor

Results export as JSON (everything), CSV (one row per item with a 500-character preview, word count, provider and any error), a single Markdown file, or a ZIP with one file per post. For editorial review, the ZIP or the Markdown export is the easiest to read. The CSV works as a tracking sheet for who reviews what.

The batch saves you the drafting time. The review still needs a person, and it is what keeps forty drafts from turning into forty published mistakes:

1. **Brand voice.** The bulk page does not apply a brand voice profile today. Posts where voice matters most are better generated one at a time from /generate with a trained profile from /brand. /blog/keep-ai-content-on-brand covers setting one up.
2. **Claims and numbers.** Every statistic, date and named source in a batch draft needs the same check as in a single draft. /blog/ai-fact-checking-confidence-scores explains what the fact-check pass catches and what it misses.
3. **SEO fit.** A batch draft has seen its keywords, not the pages it is competing with. Run the ones you plan to publish through the SEO score before editing for style; /blog/how-seo-score-works explains what to fix first.
4. **Overlap between drafts.** Similar topics in one CSV tend to produce similar openings and similar section structures. Read the batch side by side and merge or cut near-duplicates before they compete with each other in search.

## A short checklist

- One topic per row, keywords in a quoted cell, no line breaks inside cells.
- Leave the provider on *single* unless you have a reason to mix them.
- Treat the estimate and the running cost as guides, not billing.
- Check your remaining quota before a large run, or split it into smaller ones.
- Re-run failed rows from a CSV when keywords and tone matter; the retry button drops them.
- Review every draft for voice, facts, search fit and overlap with the rest of the batch.

Bulk generation is part of the Pro plan. Used this way, it turns a quarter's topic list into a stack of first drafts in one sitting, and the editing time goes into making each draft good instead of getting each one started.
