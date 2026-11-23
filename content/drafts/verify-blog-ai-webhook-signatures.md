---
title: What a Blog AI Webhook Sends, and How to Verify It Came From Blog AI
date: 2026-11-23
excerpt: Which webhook events Blog AI sends today, what a signed delivery looks like on the wire, and a short verifier that checks the signature against the raw request body.
slug: verify-blog-ai-webhook-signatures
tags: [webhooks, automation, workflow, content-ops]
draft: true
---

## A URL that anyone can post to

A webhook endpoint is a public URL that accepts JSON and acts on it. That is the appeal: a post finishes generating, and a message lands in your team's channel telling the editor it is ready, without anyone watching the screen. It is also the whole risk. Anything on the internet that learns the URL can send it a body shaped like yours, and your handler will believe it unless it checks.

Blog AI signs its deliveries so that you can check. This post covers what gets sent from /settings/webhooks, which events fire today, and how to verify a delivery in about fifteen lines of code. It also covers two behaviours that trip people up: retries that arrive with a new signature each time, and a generation request that waits for your endpoint to answer.

## Setting one up

On /settings/webhooks you add an endpoint with three things: the URL to deliver to, the events you want, and an optional signing secret. Fill in the secret. Without one, the delivery has no signature you can check, so you are back to trusting anything that posts to the URL.

The URL has to be reachable from the public internet. Blog AI checks it when you save the subscription and again before every delivery, and it refuses `localhost`, `127.0.0.1` and private network addresses such as `192.168.x.x`. For local development, put a tunnel in front of your machine and register the tunnel's public URL.

Each saved endpoint gets a Test button. It sends one event of type `test`, signed with that endpoint's secret, makes a single attempt without retries, and shows the HTTP status and response time, or the error, in a toast. That is the quickest way to check your verifier before real events start arriving.

## Which events actually fire

The event picker lists nine types in four groups: two content events, four batch events, two quota events and `test`. Only three of them are sent by anything in the API today:

- `content.generated`, when a post finishes on /generate,
- `batch.completed`, when a bulk run from /bulk finishes,
- `test`, from the Test button.

You can subscribe to `content.published`, `batch.started`, `batch.progress`, `batch.failed`, `quota.warning` and `quota.exceeded`, and the subscription saves without complaint, but no code path emits them yet. If you build an automation around `batch.failed`, it will never run. A bulk run in which every topic failed still arrives as `batch.completed`, with `failed_items` equal to `total_items` and a `success_rate` of 0, so check those fields instead.

## What a delivery looks like

Every delivery is a `POST` with a JSON body. Here is a real `content.generated` body, captured from Blog AI's own delivery code against a local test receiver:

```json
{"id":"5b766092-b32a-464a-847c-1e3a47da8f90","event_type":"content.generated","api_version":"2024-01-01","created_at":"2026-11-23T18:43:02.466313+00:00","source":"blog-ai","data":{"content_type":"blog","content_id":"c-1","title":"Demo post","word_count":1234,"generated_at":"2026-11-23T18:43:02.466271","metadata":{"tone":"informative"}},"metadata":{}}
```

From /generate, `data.metadata` also carries the topic, the research flag and up to five of the keywords you entered.

Note what is missing: the post itself. A `content.generated` event tells you that a post exists, its title and its word count. It does not carry the text. The `content_id` is a fresh ID created for the event, so it will not match anything in your history either. If your automation needs the body, it has to get it some other way, such as the Export menu (/blog/export-ai-draft-to-wordpress-medium-markdown covers what each format produces).

A `batch.completed` body carries `job_id`, `total_items`, `completed_items`, `failed_items`, `success_rate`, `total_cost_usd` and `completed_at`. The /bulk page uses the same job ID, which is the one useful handle if you want to fetch the results afterwards (/blog/bulk-generate-blog-posts-from-csv walks through a bulk run).

The headers that come with it:

- `Content-Type: application/json`
- `User-Agent: BlogAI-Webhooks/1.0`
- `X-Webhook-ID`, the same value as the body's `id`
- `X-Webhook-Event`, the event type
- `X-Webhook-Timestamp`, Unix seconds
- `X-Webhook-Signature`, in the form `t=<timestamp>,v1=<hex digest>`, present only when a secret is set

## How the signature is built

The signature is an [HMAC](https://www.rfc-editor.org/rfc/rfc2104) using SHA-256, keyed with your secret. The message it signs is the timestamp, a full stop, and the request body exactly as sent: `{t}.{body}`. The result is written as lowercase hex in the `v1` field. The format follows the one [Stripe documents for its own webhooks](https://docs.stripe.com/webhooks), so if you have written a Stripe verifier before, this will look familiar.

Putting the timestamp inside the signed message is what makes the timestamp trustworthy. An attacker who captured an old delivery cannot change `t` to look fresh without breaking the signature. Blog AI does not reject old timestamps for you, though. Your verifier has to decide how old is too old. Stripe's libraries default to a [tolerance of five minutes](https://docs.stripe.com/webhooks#replay-attacks), which is a reasonable place to start.

## A verifier in Node

```js
import crypto from 'node:crypto'

export function verifyBlogAiWebhook(rawBody, signatureHeader, secret, toleranceSeconds = 300) {
  const parts = Object.fromEntries(
    (signatureHeader ?? '').split(',').map((pair) => pair.split('=', 2))
  )
  const timestamp = Number(parts.t)
  if (!parts.v1 || !Number.isInteger(timestamp)) return false

  const age = Math.abs(Date.now() / 1000 - timestamp)
  if (age > toleranceSeconds) return false

  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${parts.t}.${rawBody}`)
    .digest('hex')

  const a = Buffer.from(expected, 'utf8')
  const b = Buffer.from(parts.v1, 'utf8')
  return a.length === b.length && crypto.timingSafeEqual(a, b)
}
```

The length check before `timingSafeEqual` matters. Node's [`crypto.timingSafeEqual`](https://nodejs.org/api/crypto.html#cryptotimingsafeequala-b) throws an error when the two buffers have different byte lengths, so a truncated or junk header would crash your handler instead of returning `false`.

## The same thing in Python

```python
import hashlib
import hmac
import time


def verify_blog_ai_webhook(raw_body: bytes, signature_header: str, secret: str, tolerance: int = 300) -> bool:
    parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
    t, v1 = parts.get("t", ""), parts.get("v1", "")
    if not t.isdigit() or not v1:
        return False
    if abs(time.time() - int(t)) > tolerance:
        return False
    expected = hmac.new(secret.encode(), t.encode() + b"." + raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)
```

[`hmac.compare_digest`](https://docs.python.org/3/library/hmac.html#hmac.compare_digest) compares in a way designed to avoid leaking, through timing, how many leading characters matched. A plain `==` is free to stop at the first difference, and that early exit is the leak.

## The raw body, and why your framework is the usual suspect

When a delivery that really did come from Blog AI fails verification, the usual cause is hashing a different string than the one Blog AI signed. Blog AI sends compact JSON, with no spaces after colons or commas. If a framework parses the body into an object and your code turns it back into a string, you hash something with different whitespace, and the signature never matches.

That is easy to check. Against the delivery shown above, the Node verifier returned `true` for the raw body and `false` for the same body after `JSON.parse` and `JSON.stringify(..., null, 2)`. Stripe's documentation makes the [same point about its own signatures](https://docs.stripe.com/webhooks): any change to the raw body makes verification fail. Read the body as bytes before any JSON middleware touches it, verify, and only then parse.

## Retries come with a new signature

Blog AI counts a delivery as successful only on a 2xx status. Timeouts (30 seconds) and refused connections count as failures, and so do redirects, which it does not follow. A `301` from `http` to `https`, or from a missing trailing slash, therefore fails every time. Register the final URL.

On failure it tries again, up to five attempts in all, waiting roughly 1, 2, 4 and then 8 seconds between them, with a little random jitter on top. In a run against a test endpoint that always returned `500`, the five attempts landed at 0, 1.1, 3.1, 7.1 and 15.1 seconds.

Two details of those retries shape how you write the handler:

- The event `id` and `X-Webhook-ID` stay the same on every attempt. If your handler did its work and then answered slowly or with an error, the retry is the same event again. Store the IDs you have processed and skip repeats.
- The timestamp and signature are recomputed for each attempt. A retry is signed fresh, so it passes the five-minute window even if the first attempt was a while ago. Don't cache a signature and compare later deliveries against it.

The counters on the endpoint card count attempts, not events. An event that failed twice and then succeeded shows as three deliveries, one successful and two failed, with the last error message underneath.

## Answer fast, then do the work

When a post finishes on /generate, the API sends the `content.generated` webhooks before it returns the post, and it waits for those deliveries to finish. A fast endpoint adds one round trip. An endpoint that returns errors adds the whole retry sequence, about fifteen seconds in the test above, and one that hangs can add up to 30 seconds per attempt. While that happens, the person who pressed Generate is still watching a spinner.

So the handler should do as little as possible before it answers: verify the signature, record the event ID, put the work on a queue, return `200`. The slow part, calling your CMS or posting to a chat channel, happens after the response. Bulk runs do not have this problem in the same way, since `batch.completed` is sent from the background job, after the /bulk page has its job ID.

## Before you rely on it

The secret is a password. Generate a long random one and keep it out of the client code. If it leaks, change it in the endpoint's edit form and update your verifier at the same time, because every delivery after the change is signed with the new one.

The Test button tells you whether the endpoint answers and whether your verifier accepts a signed `test` event. It does not tell you that real events will look like what your code expects. The first real `content.generated` is worth reading by eye, field by field, before anything downstream acts on it. Treat the event names the picker offers with the same caution. Six of the nine are still names waiting for something to send them.
