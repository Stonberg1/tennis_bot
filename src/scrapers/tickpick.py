"""
TickPick scraper.

Uses the internal listings API:
  https://api.tickpick.com/1.0/listings/internal/event/{eventId}?mid={eventId}

Response fields: id, sid (section), p (price), n (notes), sp (num_seats list)
Source: https://github.com/sdgass13/Super-Bowl-Tickets/blob/master/super.py

Known event IDs for 2026 US Open at Arthur Ashe Stadium (confirmed May 2026):
  Aug 30 Day   (Session 1, 12pm): 7396834
  Aug 30 Night (Session 2, 7pm):  7396836
  Aug 31 Day   (Session 3, 11:30am): 7396843
  Aug 31 Night (Session 4, 7pm):  7396844
"""
import datetime
import httpx

_BASE_API = "https://api.tickpick.com/1.0/listings/internal/event"
_BASE_WEB = "https://www.tickpick.com"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; tennis-monitor/1.0)",
    "Accept": "application/json",
    "Referer": "https://www.tickpick.com/",
}

_TARGET_EVENTS = [
    {
        "event_id": "7396834",
        "session_date": "2026-08-30",
        "session_type": "day",
        "label": "Aug 30 Day (Session 1, 12pm)",
        "event_url": f"{_BASE_WEB}/buy-2026-us-open-tennis-championships-session-1-tickets-arthur-ashe-stadium-8-30-26-12pm/7396834/",
    },
    {
        "event_id": "7396836",
        "session_date": "2026-08-30",
        "session_type": "night",
        "label": "Aug 30 Night (Session 2, 7pm)",
        "event_url": f"{_BASE_WEB}/buy-2026-us-open-tennis-championships-session-2-tickets-arthur-ashe-stadium-8-30-26-7pm/7396836/",
    },
    {
        "event_id": "7396843",
        "session_date": "2026-08-31",
        "session_type": "day",
        "label": "Aug 31 Day (Session 3, 11:30am)",
        "event_url": f"{_BASE_WEB}/buy-2026-us-open-tennis-championships-session-3-tickets-arthur-ashe-stadium-8-31-26-1130am/7396843/",
    },
    {
        "event_id": "7396844",
        "session_date": "2026-08-31",
        "session_type": "night",
        "label": "Aug 31 Night (Session 4, 7pm)",
        "event_url": f"{_BASE_WEB}/buy-2026-us-open-tennis-championships-session-4-tickets-arthur-ashe-stadium-8-31-26-7pm/7396844/",
    },
]


async def scrape_tickpick(*, date: str, session: str) -> list[dict]:
    """Fetch listings for known US Open events matching date and session type."""
    records: list[dict] = []
    checked_at = datetime.datetime.utcnow().isoformat()

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
            url = f"{_BASE_API}/{event_id}?mid={event_id}"

            try:
                resp = await client.get(url, headers=_HEADERS)
                resp.raise_for_status()
            except Exception as exc:
                print(f"[tickpick] listing fetch failed for {event['label']}: {exc}")
                continue

            try:
                body = resp.json()
            except Exception as exc:
                print(f"[tickpick] non-JSON response for {event['label']}: {exc}")
                continue

            listings = body if isinstance(body, list) else body.get("listings", [])

            for listing in listings:
                try:
                    price = float(listing.get("p") or listing.get("price") or 0)
                except (TypeError, ValueError):
                    continue
                if price <= 0:
                    continue

                seats = listing.get("sp") or [1]
                quantity = len(seats) if isinstance(seats, list) else int(seats)
                listing_id = str(listing.get("id") or "")
                listing_url = (
                    f"{event['event_url']}?listing={listing_id}"
                    if listing_id else event["event_url"]
                )

                records.append({
                    "platform": "tickpick",
                    "session_date": date,
                    "session_type": session,
                    "price": price,
                    "section": str(listing.get("sid") or ""),
                    "row": str(listing.get("row") or ""),
                    "quantity": quantity,
                    "listing_url": listing_url,
                    "checked_at": checked_at,
                })

    print(f"[tickpick] {date} {session}: {len(records)} listing(s) returned")
    return records
