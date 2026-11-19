import asyncio
import logging
from datetime import date, datetime
from time import monotonic
from typing import NamedTuple, Optional
from zoneinfo import ZoneInfo

import httpx

from api.src.models.nba_analytics import NbaRecord, NbaTeamComparison, NbaTeamResults

logger = logging.getLogger(__name__)
_EASTERN = ZoneInfo("America/New_York")
_SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team}/schedule"
_LOOKUP_SECONDS = 4.0
_CACHE_SECONDS = 900

# Odds provider names mapped to ESPN schedule abbreviations.
_TEAM_SLUG = {
    "Atlanta Hawks": "atl", "Boston Celtics": "bos", "Brooklyn Nets": "bkn",
    "Charlotte Hornets": "cha", "Chicago Bulls": "chi", "Cleveland Cavaliers": "cle",
    "Dallas Mavericks": "dal", "Denver Nuggets": "den", "Detroit Pistons": "det",
    "Golden State Warriors": "gs", "Houston Rockets": "hou", "Indiana Pacers": "ind",
    "LA Clippers": "lac", "Los Angeles Clippers": "lac", "Los Angeles Lakers": "lal",
    "Memphis Grizzlies": "mem", "Miami Heat": "mia", "Milwaukee Bucks": "mil",
    "Minnesota Timberwolves": "min", "New Orleans Pelicans": "no", "New York Knicks": "ny",
    "Oklahoma City Thunder": "okc", "Orlando Magic": "orl", "Philadelphia 76ers": "phi",
    "Phoenix Suns": "phx", "Portland Trail Blazers": "por", "Sacramento Kings": "sac",
    "San Antonio Spurs": "sa", "Toronto Raptors": "tor", "Utah Jazz": "utah",
    "Washington Wizards": "wsh",
}


class _Result(NamedTuple):
    day: date
    opponent: str
    venue: str
    margin: int


# At most one season per team, shared by matchup requests in this process.
_cache: dict[str, tuple[int, float, list[_Result]]] = {}


def _parse_schedule(payload: dict, team: str, season: int) -> list[_Result]:
    requested = payload["requestedSeason"]
    if requested["year"] != season or requested["type"] != 2 or payload["team"]["abbreviation"].lower() != team:
        raise ValueError("Unexpected ESPN team or regular season")

    results = {}
    for event in payload["events"]:
        if event["seasonType"]["type"] != 2:
            continue
        competition = event["competitions"][0]
        if competition["status"]["type"]["name"] != "STATUS_FINAL":
            continue
        # The Cup final is tagged as regular season but does not count in the standings.
        if any("nba cup championship" in note.get("headline", "").lower() for note in competition.get("notes", [])):
            continue

        first, second = competition["competitors"]
        side, opponent = (first, second) if first["team"]["abbreviation"].lower() == team else (second, first)
        if side["team"]["abbreviation"].lower() != team:
            raise ValueError("ESPN result missing the requested team")
        margin = int(side["score"]["value"]) - int(opponent["score"]["value"])
        if not margin:
            raise ValueError("Tied final score in ESPN NBA results")
        day = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(_EASTERN).date()
        venue = "neutral" if competition["neutralSite"] else side["homeAway"]
        results[event["id"]] = _Result(day, opponent["team"]["abbreviation"].lower(), venue, margin)

    return sorted(results.values(), key=lambda result: result.day, reverse=True)


async def _load_schedule(client: httpx.AsyncClient, team: str, season: int) -> Optional[list[_Result]]:
    cached = _cache.get(team)
    if cached is not None and cached[0] == season and cached[1] > monotonic():
        return cached[2]

    try:
        response = await client.get(_SCHEDULE_URL.format(team=team), params={"season": season, "seasontype": 2})
        response.raise_for_status()
        results = _parse_schedule(response.json(), team, season)
    except (httpx.HTTPError, AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        logger.warning("ESPN NBA results unavailable for %s season %s: %s", team, season, exc)
        return None

    _cache[team] = (season, monotonic() + _CACHE_SECONDS, results)
    return results


def _record(results: list[_Result]) -> NbaRecord:
    wins = sum(result.margin > 0 for result in results)
    return NbaRecord(wins=wins, losses=len(results) - wins)


def _summarize(results: list[_Result], before: date, venue: str, opponent: str) -> NbaTeamResults:
    season = [result for result in results if result.day < before]
    recent = season[:10]
    return NbaTeamResults(
        season_record=_record(season),
        recent_record=_record(recent),
        venue_record=_record([result for result in season if result.venue == venue]),
        head_to_head_record=_record([result for result in season if result.opponent == opponent]),
        season_margin=sum(result.margin for result in season) / len(season) if season else None,
        recent_margin=sum(result.margin for result in recent) / len(recent) if recent else None,
        latest_result=season[0].day if season else None,
    )


async def get_nba_team_comparison(home_team: str, away_team: str, game_day: date) -> Optional[NbaTeamComparison]:
    home_slug, away_slug = _TEAM_SLUG.get(home_team), _TEAM_SLUG.get(away_team)
    if home_slug is None or away_slug is None:
        logger.warning("Unmapped NBA matchup for ESPN results: %s at %s", away_team, home_team)
        return None
    # ESPN uses the ending year (e.g. 2027 for 2026–27).
    season = game_day.year + (game_day.month >= 7)
    try:
        async with httpx.AsyncClient(timeout=_LOOKUP_SECONDS) as client:
            home, away = await asyncio.wait_for(
                asyncio.gather(_load_schedule(client, home_slug, season), _load_schedule(client, away_slug, season)),
                timeout=_LOOKUP_SECONDS,
            )
    except asyncio.TimeoutError:
        logger.warning("ESPN NBA results deadline exceeded for %s at %s", away_team, home_team)
        return None

    if home is None or away is None:
        return None
    return NbaTeamComparison(
        before=game_day,
        home=_summarize(home, game_day, "home", away_slug),
        away=_summarize(away, game_day, "away", home_slug),
    )
