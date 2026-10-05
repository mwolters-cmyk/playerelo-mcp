# PlayerElo MCP server

Give any MCP client (Claude Desktop, Cursor, …) live access to **PlayerElo** — player- and
coach-level football Elo ratings, EAR, model market-value estimates, lineup-aware match
predictions, a settled value-bet track record, playing-style profiles and recruitment-fit —
through the [PlayerElo REST API](https://playerelo.football/api-access).

Ask things like *"What's Jude Bellingham's Elo and how has it trended this season?"*,
*"Which clubs are a good tactical + financial fit for player 129718?"* or *"What are the
predicted probabilities for today's Premier League matches?"* and the model answers from live
data.

It's a thin client over the public API — no database, no model code. You bring an API key
(**free tier available**); the server just makes authenticated calls.

## Install & configure

You need a PlayerElo API key — get a free one at <https://playerelo.football/api-access>.

### Claude Desktop

Add to `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "playerelo": {
      "command": "uvx",
      "args": ["playerelo-mcp"],
      "env": { "PLAYERELO_API_KEY": "pe_live_your_key_here" }
    }
  }
}
```

Restart Claude Desktop. (`uvx` comes with [uv](https://docs.astral.sh/uv/); or use
`pipx run playerelo-mcp`, or `pip install playerelo-mcp` and set `"command": "playerelo-mcp"`.)

### Cursor / other MCP clients

Same shape — command `uvx`, args `["playerelo-mcp"]`, and `PLAYERELO_API_KEY` in the env.

## Tools

| Tool | What it does |
|---|---|
| `search_players` / `list_top_players` | find players by name / top by Elo |
| `get_player`, `get_player_history`, `get_player_value`, `get_player_style` | one player's rating, trajectory, model value, style |
| `get_player_opportunities` | reachable-club shortlist |
| `search_coaches`, `get_coach` | coaches by name / by id (unique to PlayerElo) |
| `search_clubs`, `get_club`, `get_club_squad_gaps` | clubs by name / by id / recruitment needs |
| `list_leagues`, `get_league_ranking` | competitions + Team-Elo tables (off-season only) |
| `get_predictions` | upcoming-match probabilities (refreshed every few minutes) |
| `get_value_bets` | settled value-bet track record (won/lost); not betting tips |
| `get_transfer_fit` | 0–100 player→club fit score |

Every tool is available on every plan; plans differ only by monthly request volume.

## Config

| Env var | Default | |
|---|---|---|
| `PLAYERELO_API_KEY` | — | **required**; your key |
| `PLAYERELO_BASE_URL` | `https://data-api.playerelo.football` | override the API base |

## Develop

```bash
pip install -e ".[test]"    # or: pip install -e . mcp httpx pytest
pytest tests/
```

Data & docs: <https://playerelo.football/api-access> · A [LivingMeta](https://livingmeta.ai) project.
