"""PlayerElo MCP server — exposes the PlayerElo REST API as MCP tools.

A THIN client over the public REST API (https://data-api.playerelo.football). It never
imports the football model/pipeline (``fapi_elo``) or touches a database — every tool is
one authenticated HTTP call, so the server runs anywhere (a user's laptop over stdio) with
just a PlayerElo API key. See server.py."""

__version__ = "0.1.0"
