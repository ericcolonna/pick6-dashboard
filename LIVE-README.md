# Pick 6 Member Dashboard

Live board: https://claude.ai/code/artifact/48d53f4b-ae90-4b3b-908e-ba6fd9825dc2

A single self-contained HTML page showing Lockdown Academy membership, built from
Stripe. Private to Eric unless shared from the page's own share menu.

---

## How it stays current — two mechanisms

**1. The page syncs itself, every 30 minutes, while it is open.**
It calls Stripe through the viewer's own connector, re-fetches every live
subscription plus open invoices, looks up names and countries for anyone new,
then recomputes the *entire* page from the merged records. Nothing on screen is
ever fresher than anything else. Close the tab and it stops; open it and it
syncs immediately. So whatever you are looking at is current.

**2. A scheduled task rebuilds and republishes it every morning at 9am ET.**
That run clones this repo, pulls Stripe fresh, fetches the day's USD→CAD rate,
rebuilds the page and publishes over the same URL. It runs in the cloud and does
**not** need Eric's computer to be awake.

The daily run exists mainly for the **exchange rate**, which is baked into the
page as a number and cannot be refreshed by the browser (the page can only reach
connected apps, and Stripe does not quote FX). Member data does not depend on it.

---

## The files

| File | What it is |
|---|---|
| `render_live.py` | Assembles the page. Holds all HTML, CSS and the view layer. |
| `livejs.js` | The calculation engine that runs in the browser. |
| `syncjs.js` | The 30-minute live sync and its per-error-code handling. |
| `mkbake.py` | Builds `bake.json` (the baked snapshot) from the Stripe pulls. |
| `prodmap.json` | Stripe product id → tier name. |
| `fx.json` | The USD→CAD rate and the date it was read. |
| `countries.json` | Stripe customer id → ISO country code. |

Build order: `python3 mkbake.py` then `python3 render_live.py` → `live-board.html`.

`mkbake.py` reads `all.json`, `cmap.json`, `open_slim.json`, `prodmap.json`,
`fx.json` and `countries.json` from the same directory. The first three come
from Stripe at build time and are not kept in the repo.

**Files must sit at the repo root.** Do not upload a folder — GitHub nests it
inside itself, and the rebuild then reads a stale copy. Upload individual files.

---

## Rules the code depends on

**One code path.** Everything on the page — chart, tiles, lists, search, country
counts — is computed by `compute()` in `livejs.js` from the subscription records.
Never patch one section independently; that is how sections drift apart.

**Joined and churned must reconcile.** `joined` = every subscription that
*started* in the window, even if it has since ended. `churned` = every
subscription that *ended* in the window, keyed on `ended_at` (never
`canceled_at`). joined − churned always equals the chart's change.

**Currencies never merge.** USD and CAD are shown separately and never summed.
The one converted figure ("Total CAD") is explicitly labelled with its rate and
date.

**People vs subscriptions.** The money tiles count *subscriptions*. "Members by
country" counts *people* — one member holding two plans is one person. As of
Aug 2026 that is 111 subscriptions across 110 people.

**Tier grouping.** Anything that is not Coach / Athlete / Pro is Legacy. Labels
read "Legacy - …" and "Pro - …", never "Lockdown Academy" or "Lockdown Pro".

**Country is the card's country**, read from the customer's charges — not a
declared address. A member with no successful charge has none, and shows a dash.

---

## Stripe access

Account `acct_1QAluWL1hlk0mE2U` ("Pick6athletics"), livemode.
**Read only. Never call `stripe_api_write`, for any reason.**

Two Stripe quirks that have caused bugs before:

- `GetSubscriptions` without `status:"all"` silently returns only non-cancelled
  records. The full history needs `status:"all"` (~490 records, 5 pages).
- Customer names are usually **not** in `.name` — take
  `.name // .description // .metadata.name`.

---

## Making a change

1. Claude edits the source and republishes — visible immediately.
2. Claude writes the changed files into
   `~/Claude/Projects/Brainstorming/pick6-dashboard/`.
3. **Eric uploads them to this repo** (individual files, at the root).

Step 3 is not optional. If it is skipped, the next 9am run rebuilds from the old
code and the change quietly disappears. Nothing errors; it just reverts.

Claude cannot push to GitHub — that needs Eric's credentials.

---

## Known limits

- **Page size** is ~320 bytes per subscription, all of history baked in. Fine to
  roughly 1,000 members; needs pre-aggregated history past ~2,000.
- **All-time country data is partial** — 138 of 503 former members mapped. Current
  members are complete except one $0 test account.
- **The daily run cannot write back to this repo**, so countries it discovers are
  baked into the published page but looked up again the next morning.
- **"Newly leaving" cannot be detected** — the run holds no memory between days,
  so every leaving member is reported each time.
