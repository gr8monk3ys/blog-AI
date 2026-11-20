---
title: How to Export an AI Draft to WordPress, Medium, or Markdown (and What to Clean Up First)
date: 2026-11-05
excerpt: What each option in the Export menu actually produces, and the cleanup to do before an exported draft goes live on WordPress, Medium or a static site.
slug: export-ai-draft-to-wordpress-medium-markdown
tags: [publishing, ai-writing, content-ops, workflow]
draft: true
---

## The last step nobody plans for

A draft can pass the SEO score and an editor's read and still go wrong on the way into your CMS. Formatting that looked fine on screen turns into stray asterisks, the title shows up twice, and a footer line you never wrote ends up on the live page. None of it is hard to fix. It is just easy to miss, because by the time a post is being exported everyone thinks the work is done.

This post walks through the Export menu on /generate, option by option, and ends with what to tidy up before you hit publish.

## What gets exported

When a post finishes generating, the Export button sits above it. Whatever format you pick, the starting material is the same: the post exactly as it was generated. The page shows the result read-only, so any editing you want to do happens after export, in your own editor or CMS.

The body that gets exported is built like this:

- the post title on its own line,
- the meta description underneath it,
- each section as a level-two heading (`##`),
- each subtopic as a level-three heading (`###`), followed by its text.

Alongside that body, the export also receives the post's date, description and tags. Most formats print those as a small header above the body. That is where the first piece of cleanup comes from: because the body already starts with the title and description, several formats end up showing them twice.

## The download options

The Download group has five entries.

### Copy to Clipboard

This copies the body above as plain text, Markdown headings included. Nothing is added or removed. This is the quickest way to get a draft into a doc for editing.

### Markdown (.md)

The Markdown download adds a header on top of the body: the title as a `#` heading, the date in italics, the description as a blockquote, a Tags line and a horizontal rule. At the bottom it adds another rule and a line reading *Generated with Blog AI on* followed by the export date. There is no YAML frontmatter, so if the file is going into a static site generator (Next.js, Hugo, Astro, Jekyll), you will need to write the frontmatter block yourself and delete the Markdown header it replaces.

### HTML (.html)

The HTML download is a complete, styled page you can open in any browser: headings, bold and italic, bullet lists, code blocks, blockquotes and links are all converted. Two things do not survive cleanly. Numbered lists are not converted, so their items run together into one paragraph. And the italic conversion runs before links and code are handled, so any word joined by underscores gets italic tags pushed into the middle of it: a link to a URL with two or more underscores in it (`.../Search_engine_optimization`, say) ends up pointing at a broken address, and `snake_case` names in code blocks pick up stray italics. Links and images are only kept if they point to `http`, `https`, `mailto` or a relative path; anything else becomes `#`. The date, description and tags appear in a metadata block under the title (so the description shows twice here too, since the body already opens with it), and the same "Generated with Blog AI" line sits in the footer. This is the best option for sending a draft to a reviewer who does not want to open a Markdown file.

### Plain Text (.txt)

The plain-text download has the title underlined with `=` signs, then *Date:*, *Description:* and *Tags:* lines, then the body with all Markdown removed. Headings become ordinary lines, and numbered list items lose their numbers. Links keep their visible text but lose the URL, and code blocks are deleted along with everything inside them, so a plain-text export of a post with links or code is not something to publish from.

### PDF

Right now the PDF option does not produce a PDF. The server has no PDF renderer installed, so it falls back to the same styled HTML as the HTML export, and the menu saves that file with a `.pdf` name. To get a real PDF, download the HTML version, open it in a browser and use *Print* then *Save as PDF*. The layout is the same.

File names come from the title: lowercased, with anything that is not a letter or number replaced by a hyphen, and cut at 50 characters.

## The two publishing options

The Copy for Publishing group does not publish anything and does not connect to your WordPress or Medium account. Both entries convert the post on the server and copy the result to your clipboard. What you paste is the markup, not a formatted preview.

### WordPress

The WordPress option produces Gutenberg block markup: every heading, paragraph and bullet list is wrapped in the `<!-- wp:... -->` comments the block editor uses. Paste it into the block editor's Code editor view (from the editor's options menu), then switch back to the visual editor and check the result. The list markup is written as plain `<li>` items rather than WordPress's own list-item blocks, so if the editor flags a block as invalid, use its block recovery option or rebuild the list by hand.

Things to fix once it is in:

- The post title becomes a level-one heading block at the top, and the body's own title line follows it as a paragraph. WordPress already has a title field, so delete both and put the title there.
- Bold, italic and links are not converted. Paragraph text is passed through as written, so `**bold**` arrives with its asterisks and a Markdown link arrives as `[text](url)`. Search the post for `**`, `*` and `](` and redo those as real formatting and links.
- Bullet lists become list blocks, but the items of a numbered list are run together into a single paragraph ("1. First step 2. Second step"). Rebuild them as a numbered list block.
- A blockquote is not converted: it arrives as a paragraph that starts with a literal `>`. Turn it into a Quote block.
- A code block collapses into one paragraph with the triple backticks still in it and the line breaks gone. Rebuild it as a Code block from your original draft, since the line breaks cannot be recovered from the paste.

### Medium

The Medium option produces simple HTML: headings (capped at level four), paragraphs, bullet lists, blockquotes, bold and italic. As with WordPress, the title is added as a top-level heading and the body's own title line follows as a paragraph, so expect it twice. Markdown links are not converted here either, and numbered lists and code blocks collapse into one paragraph the same way they do for WordPress. Blockquotes, unlike in the WordPress output, do come through as quotes.

The option copies the HTML source as plain text, and Medium's editor has no way to paste HTML source, so pasting it gives you the tags as literal text. Use the HTML download instead: open the file in a browser, select the article and copy it from there, then paste into a Medium draft. Copying from a rendered page keeps headings, emphasis and most links, which also gets around the link problem, but it carries over the HTML export's own gaps: check any link whose URL contains underscores, and rebuild numbered lists by hand.

## A cleanup checklist for any destination

Whichever format you used, run through this before the post goes live:

- Delete the duplicate title line, and in the Markdown, HTML and plain-text exports the duplicate description as well.
- Remove the "Generated with Blog AI on..." line from Markdown, HTML and plain-text exports, unless you want it there.
- In WordPress and Medium pastes, search for leftover `**`, `*` and `[text](url)` patterns, rebuild any code blocks, and in WordPress turn lines starting with `>` back into quotes.
- In the HTML export, and anything copied from it, rebuild numbered lists and click every link whose URL has underscores in it; check code blocks for stray italics.
- For a static site, write the frontmatter (title, date, description, tags, slug) and drop the generated Markdown header.
- Add the internal links the draft does not have yet, and never publish from the plain-text export if the post links out or contains code.
- If you made more than light edits after exporting, run the post through the SEO score again; /blog/how-seo-score-works explains which fixes move it most.

## Where export fits in the workflow

Export is the end of the pipeline, so it is worth doing everything that changes the text first. If you left Proofread and Humanize on, those passes have already run by the time the post appears (/blog/proofread-and-humanize-passes-explained covers what they change), and if the post has numbers in it, the fact-check results should be cleared before it leaves the app (/blog/ai-fact-checking-confidence-scores). If the same post is also going out as a thread or a newsletter, repurpose it from the finished version, not the raw draft; /blog/repurpose-blog-post-into-other-formats walks through that.
