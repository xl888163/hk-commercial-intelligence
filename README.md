# Hong Kong Commercial Intelligence

A dashboard of Hong Kong industry events and commercial property movements, rated for
security-system opportunities (CCTV, access control, alarms). Every run fetches fresh data from the internet.

## Shared web page
Live page: https://claude.ai/artifact/XfPuT7fwVqc4gCkv2o7k1S
- PIC, Status and the change history are stored in the page's shared database. They carry over every time the data is refreshed and republished.
- To refresh: run the fetcher (below), then ask Claude to "republish the dashboard". The same URL is kept.
- To let colleagues edit: in the page's Share menu, give them Contributor access or above (view-only people can't assign PICs).

## Run it
- Double-click **`Update Dashboard.command`**, or
- in Terminal: `python3 run.py` (`--no-open` to skip opening the browser, `--days 60` to change the news window)

It takes about 40 seconds, then opens `dashboard.html`. Only the Python 3 standard library is used, so there is nothing to install.

## What it collects

| Section | Sources |
|---|---|
| Industry events (next 12 months) | HKCEC event calendar, AsiaWorld-Expo, InvestHK (HKSAR Gov) API, HKGCC, AmCham HK, BritCham HK |
| Property movements (last 90 days) | Google News HK editions (10 English and 7 Chinese searches), SCMP Property, Mingtiandi, HKSAR Government press releases |

## No-fabrication rules
- Each row links back to its source, and headlines and event names appear exactly as published.
- Company, building, area, size and floors are filled in only when they are present in the source text. Otherwise the field shows "Not stated".
- Event access (Trade / Public / By registration / **By invitation**) is copied from the venue listing.
- Reports of the same deal are grouped across outlets and languages. The **Verification** column shows
  `Official source`, `Corroborated by N outlets` or `Single outlet: open source to confirm`.
- The **opportunity rating and angle are rule-based analysis**. Each row has a "Why this rating" list.
- The *Sources & verification* tab shows which sources worked on each run. A failed source is reported there; its data is never invented.

## Files
- `run.py`: entry point
- `intel/events.py`, `intel/property.py`: source collectors
- `intel/analyze.py`: filtering, extraction, corroboration, scoring
- `intel/taxonomy.py`: sector keywords, HK districts, buildings and venues (edit to tune)
- `intel/companies.py`: bilingual company and landlord names (add new ones as you meet them)
- `templates/dashboard.html`: dashboard UI
- `data/latest.json`, `data/snapshots/`: data from each run; `data/history.json` drives the "NEW since last run" badge

## Notes
- Websites change their layouts. If a source shows "Unavailable" for several runs in a row, its collector in `intel/` needs updating.
- Truly private invite-only events (e.g. vendor dinners) are not published online. The dashboard covers invitation-only events listed by venues and chamber events.
