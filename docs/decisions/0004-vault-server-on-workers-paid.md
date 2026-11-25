# 0004: Run vault-server on Workers Paid

Date: 2026-11-24. Status: accepted.

## Context

On 2026-11-24, from about 00:40 UTC, most `guide` and `search` calls to the vault-server Worker failed with Cloudflare error 1102. Small `read` calls sometimes failed too.

Measured:

- `wrangler tail` on the live Worker: a three-word `search` ended with outcome `exceededCpu` at 24 ms of CPU, and another call was killed at 10 ms. A `guide` that succeeded used 21 ms.
- An offline replay of the Worker's own `untar` and `search` against the vault tarball (817 Markdown files, 3.2 MB): turning the snapshot into files costs about 20 ms, and one keyword search costs 75 to 110 ms. Both figures are Node on an Apple laptop, three rounds each.
- The account was on Workers Free, which allows 10 ms of CPU per request. Cloudflare tolerates occasional overruns per isolate but terminates an isolate that keeps going over, which takes down any small calls it is serving at the same time.

`guide`, `search`, `list` and `lint` all parse the whole vault snapshot, and `search` ranks every page in the Worker. That cost grows with the vault (1.8 MB on 2026-11-17, 3.2 MB on 2026-11-24). The deploy of 2026-11-25 00:23 UTC (#7, #8, #9) did not change those paths, so rolling it back would not have helped.

## Decision

Move the account to Workers Paid (30 s CPU per request by default; $5 a month minimum with 30 million CPU milliseconds included). No code change.

## Rejected

- Rewriting to fit 10 ms: `guide` could read two files directly, but in-Worker keyword search cannot rank 3 MB of text in 10 ms, and `list`, `lint` and the index cron would still go over. Hybrid search in AI Search alone would drop the stale and superseded flags.
- Rolling back the 00:23 UTC deploy: the failing paths were unchanged since 2026-11-09.

## Revisit when

A single `search` approaches the Paid per-request CPU limit, or monthly CPU use approaches the included 30 million milliseconds. Either way, move keyword ranking out of the request (precomputed index in KV, or AI Search hybrid retrieval).
