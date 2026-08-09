"""PlayerElo MCP server.

Exposes the PlayerElo REST API (player + coach Elo ratings, EAR, market-value estimates,
predictions, value bets, playing-style and recruitment-fit) as MCP tools an AI agent can
call. It is a THIN client: every tool is one authenticated GET against
``https://data-api.playerelo.football`` — no database, no model code, no ``fapi_elo`` import,
so the whole thing runs on a user's machine over stdio with just an API key.

Config via env:
  PLAYERELO_API_KEY   your key (free tier at https://playerelo.football/api-access) — required
  PLAYERELO_BASE_URL  override the API base (default https://data-api.playerelo.football)

Run:  playerelo-mcp        (stdio transport; the default for Claude Desktop / Cursor)
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

DEFAULT_BASE = "https://data-api.playerelo.football"
_DOCS = "https://playerelo.football/api-access"

mcp = FastMCP("playerelo")


class PlayerEloError(RuntimeError):
    """A user-actionable error surfaced to the agent (bad key, quota, network)."""


def _base_url() -> str:
    return os.environ.get("PLAYERELO_BASE_URL", DEFAULT_BASE).rstrip("/")


def _get(path: str, params: Optional[dict] = None) -> Any:
    """One authenticated GET. Drops None-valued params, translates the common HTTP
    failures into readable guidance, and returns None on 404 (unknown id) so a tool can
    report "not found" instead of raising. Reads the key at call time (not import) so the
    server starts even before the env is populated."""
    key = os.environ.get("PLAYERELO_API_KEY", "")
    if not key:
        raise PlayerEloError(
            f"No API key set. Put your PlayerElo key in the PLAYERELO_API_KEY environment "
            f"variable — get a free one at {_DOCS}.")
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        with httpx.Client(base_url=_base_url(), timeout=30,
                          headers={"Authorization": f"Bearer {key}"}) as client:
            resp = client.get(path, params=clean)
    except httpx.RequestError as exc:  # DNS, connect, timeout
        raise PlayerEloError(f"Could not reach the PlayerElo API: {exc}") from exc
    if resp.status_code in (401, 403):
        raise PlayerEloError(f"Unauthorized — check PLAYERELO_API_KEY (manage keys at {_DOCS}).")
    if resp.status_code == 429:
        raise PlayerEloError(
            f"Monthly or per-minute rate limit reached for your plan — wait and retry, or "
            f"upgrade at {_DOCS}.")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


# ── Players ──────────────────────────────────────────────────────────────────
@mcp.tool()
def search_players(query: str, limit: int = 10) -> list[dict]:
    """Find football players by name (case-insensitive). Returns matches with their
    player_id, name, Elo rating, position, current club and league — use the player_id
    with the other player tools. This is how you resolve a name like "Bellingham" to an id."""
    return _get("/v1/players", {"search": query, "limit": limit}) or []


@mcp.tool()
def list_top_players(limit: int = 20, offset: int = 0) -> list[dict]:
    """The highest-rated players worldwide by current Elo (active players only).
    Paginate with limit (max 100) and offset."""
    return _get("/v1/players", {"limit": limit, "offset": offset}) or []


@mcp.tool()
def get_player(player_id: int) -> Optional[dict]:
    """Full current record for one player by id: name, age, position, club, league, Elo
    rating and EAR (Elo Above Replacement). Returns null if no player has that id."""
    return _get(f"/v1/players/{player_id}")


@mcp.tool()
def get_player_history(player_id: int) -> list[dict]:
    """A player's Elo and EAR over time (one point per date) — the rating trajectory,
    useful for form/trend analysis and charts."""
    return _get(f"/v1/players/{player_id}/history") or []


@mcp.tool()
def get_player_value(player_id: int) -> Optional[dict]:
    """PlayerElo's own model-based market-value estimate for a player (in euros), with the
    signals behind it. This is our computed estimate, not a third-party valuation."""
    return _get(f"/v1/players/{player_id}/value")


@mcp.tool()
def get_player_style(player_id: int) -> Optional[dict]:
    """A player's playing-style profile — per-90 output and a multi-axis process fingerprint
    describing how they play, not just how good they are."""
    return _get(f"/v1/players/{player_id}/style")


@mcp.tool()
def get_player_opportunities(player_id: int, top_n: int = 25) -> Optional[dict]:
    """Recruitment opportunity map for a player: realistically reachable clubs that could
    plausibly sign them, ranked by fit. Requires a Business-tier key."""
    return _get(f"/v1/players/{player_id}/opportunities", {"top_n": top_n})


# ── Coaches ──────────────────────────────────────────────────────────────────
@mcp.tool()
def search_coaches(query: str, limit: int = 10) -> list[dict]:
    """Find coaches/managers by name (case-insensitive). Returns matches with their coach_id
    (a string like "coach_4"), name, Elo and current club — PlayerElo is the only public
    system that rates coaches. Use the coach_id with the other coach tools."""
    return _get("/v1/coaches", {"search": query, "limit": limit}) or []


@mcp.tool()
def get_coach(coach_id: str) -> Optional[dict]:
    """Full current record for one coach by id (e.g. "coach_4"): name, club, league and Elo
    rating. Returns null if no coach has that id."""
    return _get(f"/v1/coaches/{coach_id}")


# ── Clubs ────────────────────────────────────────────────────────────────────
@mcp.tool()
def search_clubs(query: str, limit: int = 10) -> list[dict]:
    """Find clubs by name (case-insensitive). Returns matches with their team_id, name,
    Team Elo (squad-derived strength), league and country. Use the team_id with the other
    club tools."""
    return _get("/v1/clubs", {"search": query, "limit": limit}) or []


@mcp.tool()
def get_club(team_id: int) -> Optional[dict]:
    """One club's current record by team_id: name, Team Elo, league, country and its
    standout player. Returns null if no club has that id."""
    return _get(f"/v1/clubs/{team_id}")


@mcp.tool()
def get_club_squad_gaps(team_id: int) -> Optional[dict]:
    """A club's squad-need analysis: which positions are weakest relative to its level —
    the recruitment gaps a sporting director would target."""
    return _get(f"/v1/clubs/{team_id}/squad-gaps")


# ── Leagues ──────────────────────────────────────────────────────────────────
@mcp.tool()
def list_leagues() -> list[dict]:
    """All competitions PlayerElo covers, with each league's id, name and country. Use a
    league_id with get_league_ranking."""
    return _get("/v1/leagues") or []


@mcp.tool()
def get_league_ranking(league_id: int) -> Optional[dict]:
    """A league's clubs ranked by Team Elo (current-season strength order)."""
    return _get(f"/v1/leagues/{league_id}/ranking")


# ── Predictions & betting ────────────────────────────────────────────────────
@mcp.tool()
def get_predictions(league: Optional[str] = None) -> list[dict]:
    """Upcoming-match win/draw/win probabilities from confirmed lineups, refreshed roughly
    every 10 minutes. Optionally filter by a league name/code. These are lineup-aware
    predictions, not just team form."""
    return _get("/v1/predictions", {"league": league}) or []


@mcp.tool()
def get_value_bets(strategy: Optional[str] = None, since: Optional[int] = None) -> list[dict]:
    """Current value-bet signals — where PlayerElo's fair odds diverge from the market price.
    Optionally filter by strategy ("hs2_v6" = High Volume, "hs1_v6" = Sweet Spot). To poll
    for only NEW picks, pass since=<the largest id from your previous call>; signals refresh
    about every 10 minutes."""
    return _get("/v1/value-bets", {"strategy": strategy, "since": since}) or []


# ── Recruitment fit ──────────────────────────────────────────────────────────
@mcp.tool()
def get_transfer_fit(player_id: int, target_club_id: int) -> Optional[dict]:
    """A 0-100 transfer-fit score for a specific player → club move, blending tactical fit
    (style match to the club's system), financial fit (our value estimate vs the club's
    typical spend) and strategic fit (squad need, age, level), with the per-signal breakdown.
    Requires an Ultra-tier key or higher."""
    return _get("/v1/fit", {"player_id": player_id, "target_club_id": target_club_id})


def main() -> None:
    """Console-script entry point — runs the server over stdio (the transport Claude Desktop,
    Cursor and other MCP clients launch it with)."""
    mcp.run()


if __name__ == "__main__":
    main()
