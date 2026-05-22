"""
StubHub scraper.

Uses StubHub's catalog API to find US Open listings for target dates.
No API key required for basic catalog searches.

Known StubHub event IDs for 2026 US Open at Arthur Ashe Stadium:
  Searched via: https://www.stubhub.com/us-open-tennis-tickets/
"""
import datetime
import httpx

_SEARCH_URL = "https://www.stubhub.com/search/catalog/events/v3"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.stubhub.com/",
}
_US_OPEN_KEYWORDS = ("us open", "arthur ashe", "flushing", "usta")


async def scrape_stubhub(*, date: str, session: str) -> list[dict]:
    """Search StubHub for US Open listings on *date*."""
    records: list[dict] = []
    checked_at = datetime.datetime.utcnow().isoformat()

    params = {
        "q": "US Open Tennis 2026",
        "dateLocal": date,
        "rows": 100,
        "start": 0,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(_SEARCH_URL, params=params, headers=_HEADERS)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[stubhub] search failed for {date}: {exc}")
            return records

        try:
            body = resp.json()
        except Exception as exc:
            print(f"[stubhub] non-JSON response for {date}: {exc}")
            return records

    events = body.get("events", body.get("results", []))
    if not events:
        # Try alternate response shape
        events = body.get("document", {}).get("event", [])
        if isinstance(events, dict):
            events = [events]

    for event in events:
        name = (event.get("name") or event.get("title") or "").lower()
        if not any(kw in name for kw in _US_OPEN_KEYWORDS):
            continue

        # Detect session type from event name
        event_session = "night" if any(
            kw in name for kw in ("night", "evening", "7pm", "7:00")
        ) else "day"
        if event_session != session:
            continue

        price = 0.0
        try:
            price = float(
                event.get("minPrice") or
                event.get("minListingPrice") or
                event.get("ticketInfo", {}).get("minListPrice") or 0
            )
        except (TypeError, ValueError):
            pass

        event_id = str(event.get("id") or event.get("eventId") or "")
        listing_url = (
            event.get("url") or
            event.get("eventUrl") or
            (f"https://www.stubhub.com/event/{event_id}" if event_id else "")
        )

        if price > 0:
            records.append({
                "platform": "stubhub",
                "session_date": date,
                "session_type": session,
                "price": price,
                "section": "",
                "row": "",
                "quantity": 1,
                "listing_url": listing_url,
                "checked_at": checked_at,
            })

    print(f"[stubhub] {date} {session}: {len(records)} listing(s) returned")
    return records
