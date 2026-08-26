# Pick 6 Member Dashboard — live version

Artifact: https://claude.ai/code/artifact/48d53f4b-ae90-4b3b-908e-ba6fd9825dc2

## How it works now

The page no longer ships a finished set of numbers. It ships the **records** —
487 compact subscription rows, the customer names, the product→tier map, the FX
rate — and computes everything in the browser. One code path (`compute()` in
livejs.js) produces the KPIs, the tier table, the chart, and every list, so no
section can ever be fresher than another.

On open it renders from the baked records (~600ms), then:

1. `watchTool` fetches the live subscriptions (Stripe returns only non-cancelled
   when `status` is omitted — 111 records, 2 pages) and re-fires every 5 minutes.
2. Open invoices are refetched for the past-due figures.
3. Anyone who was live but has dropped off the list is fetched individually to
   learn their `ended_at`.
4. Everything is merged and `compute()` runs again over the whole set.

The ~293 cancelled subscriptions are frozen records. They are never re-fetched.

## Files

  bake.json       the baked records (regenerate with mkbake.py)
  livejs.js       the compute engine — the JS port of build.py
  syncjs.js       the live sync + error handling
  render_live.py  assembles bake + engine + sync + page into live-board.html
  mkbake.py       builds bake.json from all.json / cmap.json / open_slim.json

To rebuild after a full Stripe pull:  python3 mkbake.py && python3 render_live.py

## Verified

The JS engine was diffed against the Python generator on the same input:
every total, every group figure, every list length identical, and the
joined − churned = chart-delta invariant holds in all five windows.

## Not yet verified in production

Stripe list responses are ~350KB. That size has never been round-tripped
through the artifact MCP bridge before, only through the Claude tool path.
If the bridge truncates them the page falls back to the baked numbers with a
"could not sync" note rather than showing anything wrong.
