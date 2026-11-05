---
title: How to Export an AI Draft to WordPress, Medium, or Markdown (and What to Clean Up First)
date: 2026-11-05
excerpt: What each option in the Export menu actually produces, what lands on your clipboard for WordPress and Medium, and the short cleanup list to run before an exported draft goes live.
slug: export-ai-draft-to-wordpress-medium-markdown
tags: [publishing, ai-writing, content-ops, workflow]
draft: true
---

## The last step nobody plans for

A draft can pass the SEO score, the fact-check and an editor's read, and still go wrong on the way into your CMS. Formatting that looked fine on screen turns into stray asterisks, the title shows up twice, and a footer line you never wrote ends up on the live page. None of it is hard to fix. It is just easy to miss, because by the time a post is being exported everyone thinks the work is done.

This post walks through the Export menu on /generate: what each option produces, which ones download a file and which ones copy to your clipboard, and what to tidy up for each destination before you hit publish.

## What gets exported

When a post finishes generating, the Export button sits above it. Whatever format you pick, the starting material is the same: the post exactly as it was generated. The page shows the result read-only, so any editing you want to do happens after export, in your own editor or CMS.

The body that gets exported is built like this:

- the post title on its own line,
- the meta description underneath it,
- each section as a level-two heading (`##`),
- each subtopic as a level-three heading (`###`), followed by its text.

Alongside that body, the export also receives the post's date, description and tags. Most formats print those as a small header above the body. That is where the first piece of cleanup comes from: because the body already starts with the title and description, several formats end up showing them twice.

## The download options

The **Download** group has five entries.

**Copy to Clipboard.** Copies the body above as plain text, Markdown headings included. Nothing is added or removed. This is the quickest way to get a draft into a doc for editing.

**Markdown (.md).** Adds a header on top of the body: the title as a `#` heading, the date in italics, the description as a blockquote, a **Tags:** line and a horizontal rule. At the bottom it adds another rule and a line reading *Generated with Blog AI on* followed by the export date. There is no YAML frontmatter, so if the file is going into a static site generator (Next.js, Hugo, Astro, Jekyll), you will need to write the frontmatter block yourself and delete the Markdown header it replaces.

**HTML (.html).** A complete, styled page you can open in any browser: headings, bold and italic, bullet lists, code blocks, blockquotes and links are all converted. Links and images are only kept if they point to `http`, `https`, `mailto` or a relative path; anything else becomes `#`. The date, description and tags appear in a metadata block under the title, and the same "Generated with Blog AI" line sits in the footer. This is the best option for sending a draft to a reviewer who does not want to open a Markdown file.

**Plain Text (.txt).** The title underlined with `=` signs, then *Date:*, *Description:* and *Tags:* lines, then the body with all Markdown removed. Headings become ordinary lines. Links keep their visible text but **lose the URL**, so a plain-text export of a post with links is not something to publish from.

**PDF.** Uses the same styled HTML as the HTML export. If the downloaded file will not open in your PDF reader, download the HTML version instead, open it in a browser and use *Print* then *Save as PDF*. The result is the same layout.

File names come from the title: lowercased, with anything that is not a letter or number replaced by a hyphen, and cut at 50 characters.

## The two publishing options

The **Copy for Publishing** group does not publish anything and does not connect to your WordPress or Medium account. Both entries convert the post on the server and copy the result to your clipboard. What you paste is the markup, not a formatted preview.

### WordPress

The WordPress option produces Gutenberg block markup: every heading, paragraph and bullet list is wrapped in the `<!-- wp:... -->` comments the block editor uses. The most reliable place to paste it is the block editor's **Code editor** view (from the editor's options menu); switch back to the visual editor afterwards and each piece shows up as its own block.

Three things to fix once it is in:

- **The title is in the body.** The post title becomes a level-one heading block at the top, and the body's own title line follows it as a paragraph. WordPress already has a title field, so delete both and put the title there.
- **Bold, italic and links are not converted.** Paragraph text is passed through as written, so `**bold**` arrives with its asterisks and a Markdown link arrives as `[text](url)`. Search the post for `**`, `*` and `](` and redo those as real formatting and links.
- **Numbered lists are not recognized.** Bullet lists become list blocks, but the items of a numbered list are run together into a single paragraph ("1. First step 2. Second step"). Rebuild them as a numbered list block.

### Medium

The Medium option produces simple HTML: headings (capped at level four), paragraphs, bullet lists, blockquotes, bold and italic. As with WordPress, the title is added as a top-level heading and the body's own title line follows as a paragraph, so expect it twice. Markdown links are not converted here either, and numbered lists collapse into one paragraph the same way they do for WordPress.

Because it is copied as HTML source, what you see after pasting depends on the editor. If the tags show up as literal text, use the HTML download instead: open the file in a browser, select the article and copy it from there. Pasting formatted text from a rendered page generally keeps headings, emphasis and links, which also gets around the link problem.

## A cleanup checklist for any destination

Whichever format you used, run through this before the post goes live:

- **One title.** Delete the duplicate title line, and in Markdown and plain text the duplicate description.
- **No footer.** Remove the "Generated with Blog AI on..." line from Markdown, HTML and plain-text exports, unless you want it there.
- **Real formatting.** In WordPress and Medium pastes, search for leftover `**`, `*` and `[text](url)` patterns.
- **Frontmatter.** For a static site, write the frontmatter (title, date, description, tags, slug) and drop the generated Markdown header.
- **Links.** Add the internal links the draft does not have yet, and never publish from the plain-text export if the post links out.
- **One last score.** If you made more than light edits after exporting, run the post through the SEO score again; /blog/how-seo-score-works explains which fixes move it most.

## Where export fits in the workflow

Export is the end of the pipeline, so it is worth doing everything that changes the text first. The proofread and humanize passes have already run by the time the post appears (/blog/proofread-and-humanize-passes-explained covers what they change), and if the post has numbers in it, the fact-check results should be cleared before it leaves the app (/blog/ai-fact-checking-confidence-scores). If the same post is also going out as a thread or a newsletter, repurpose it from the finished version, not the raw draft; /blog/repurpose-blog-post-into-other-formats walks through that.

The Export menu gets a draft out of the app in the shape your next tool expects. The last five minutes of cleanup, a single title, no footer, real links, are what make it look like you wrote it there.
