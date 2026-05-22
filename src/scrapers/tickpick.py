"""
TickPick scraper.

Uses known direct event URLs for 2026 US Open sessions at Arthur Ashe Stadium.
The reverse-engineered /api/events endpoint returned 404 as of May 2026,
so we now scrape the TickPick listing API using known event IDs extracted
from the public event pages.

Known event URLs (as of May 2026):
  Aug 30 Day   (Session 1, 12pm): /buy-.../7396834/
  Aug 30 Night (Session 2, 7pm):  /buy-.../7396836/
  Aug 31 Day   (Session 3, 11:30am): /buy-.../7396844/ (redirects to session 3)
  Aug 31 Night (Session 4, 7pm):  /buy-.../7396844/
"""
import httpx
import src.config as config

_BASE = "https://www.tickpick.com"
_LISTINGS_URL = f"{_BASE}/api/listing"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; tennis-monitor/1.0)",
    "Accept": "application/json",
    "Referer": _BASE + "/",
}

# Hardcoded known event IDs for target sessions
_TARGET_EVENTS = [
    {
        "event_id": "7396834",
        "session_date": "2026-08-30",
        "session_type": "day",
        "label": "Aug 30 Day (Session 1, 12pm)",
        "event_url": f"{_BASE}/buy-2026-us-open-tennis-championships-session-1-tickets-arthur-ashe-stadium-8-30-26-12pm/7396834/",
    },
    {
        "event_id": "7396836",
        "session_date": "2026-08-30",
        "session_type": "night",
        "label": "Aug 30 Night (Session 2, 7pm)",
        "event_url": f"{_BASE}/buy-2026-us-open-tennis-championships-session-2-tickets-arthur-ashe-stadium-8-30-26-7pm/7396836/",
    },
    {
        "event_id": "7396843",
        "session_date": "2026-08-31",
        "session_type": "day",
        "label": "Aug 31 Day (Session 3, 11:30am)",
        "event_url": f"{_BASE}/buy-2026-us-open-tennis-championships-session-3-tickets-arthur-ashe-stadium-8-31-26-1130am/7396843/",
    },
    {
        "event_id": "7396844",
        "session_date": "2026-08-31",
        "session_type": "night",
        "label": "Aug 31 Night (Session 4, 7pm)",
        "event_url": f"{_BASE}/buy-2026-us-open-tennis-championships-session-4-tickets-arthur-ashe-stadium-8-31-26-7pm/7396844/",
    },
]


async def scrape_tickpick(*, date: str, session: str) -> list[dict]:
    """Fetch listings for all known US Open events on *date* with *session* type."""
    records: list[dict] = []

    # Filter to matching date and session
    targets = [
        e for e in _TARGET_EVENTS
        if e["session_date"] == date and e["session_type"] == session
    ]

    if not targets:
        print(f"[tickpick] no known events configured for {date} {session}")
        return records

    async with httpx.AsyncClient(timeout=20) as client:
        for event in targets:
            event_id = event["event_id"]
            event_url = event["event_url"]
            label = event["label"]

            try:
                resp = await client.get(
                    _LISTINGS_URL,
                    params={"eventId": event_id},
                    headers=_HEADERS,
                )
                resp.raise_for_status()
            except Exception as exc:
                print(f"[tickpick] listing fetch failed for {label}: {exc}")
                continue

            try:
                body = resp.json()
            except Exception as exc:
                print(f"[tickpick] non-JSON response for {label}: {exc}")
                continue

            listings = (
                body if isinstance(body, list)
                else body.get("listings", body.get("data", []))
            )

            for listing in listings:
                try:
                    price = float(
                        listing.get("price") or listing.get("listPrice") or 0
                    )
                except (TypeError, ValueError):
                    continue
                if price <= 0:
                    continue

                listing_id = listing.get("listingId") or listing.get("id") or ""
                listing_url = (
                    f"{event_url}?listing={listing_id}"
                    if listing_id else event_url
                )
                records.append({
                    "platform": "tickpick",
                    "session_date": date,
                    "session_type": session,
                    "price": price,
                    "section": str(listing.get("section") or ""),
                    "row": str(listing.get("row") or ""),
                    "quantity": int(listing.get("quantity") or 1),
                    "listing_url": listing_url,
                    "checked_at": __import__("datetime").datetime.utcnow().isoformat(),
                })

    print(f"[tickpick] {date} {session}: {len(records)} listing(s) returned")
    return records
