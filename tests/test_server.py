"""Wiring tests for the PlayerElo MCP tools — each tool must hit the right REST path with
the right params. `_get` is monkeypatched so nothing leaves the process. Requires the `mcp`
+ `httpx` deps (this package's env), so it lives here, not in the main football suite."""
import httpx
import pytest

from playerelo_mcp import server


@pytest.fixture
def calls(monkeypatch):
    """Record every _get(path, params) and return a canned payload instead of a real call."""
    recorded = []

    def fake_get(path, params=None):
        recorded.append((path, params or {}))
        return {"ok": True}

    monkeypatch.setattr(server, "_get", fake_get)
    return recorded


def test_search_players_hits_players_with_search(calls):
    server.search_players("Bellingham", limit=5)
    assert calls == [("/v1/players", {"search": "Bellingham", "limit": 5})]


def test_get_player_uses_id_path(calls):
    server.get_player(129718)
    assert calls == [("/v1/players/129718", {})]


def test_value_bets_passes_since_cursor(calls):
    server.get_value_bets(strategy="hs1_v6", since=4821)
    assert calls == [("/v1/value-bets", {"strategy": "hs1_v6", "since": 4821})]


def test_transfer_fit_binds_both_ids(calls):
    server.get_transfer_fit(129718, 165)
    assert calls == [("/v1/fit", {"player_id": 129718, "target_club_id": 165})]


def test_search_clubs_hits_clubs(calls):
    server.search_clubs("Dortmund")
    assert calls == [("/v1/clubs", {"search": "Dortmund", "limit": 10})]


def test_missing_api_key_raises_actionable_error(monkeypatch):
    monkeypatch.delenv("PLAYERELO_API_KEY", raising=False)
    with pytest.raises(server.PlayerEloError) as exc:
        server._get("/v1/players")
    assert "PLAYERELO_API_KEY" in str(exc.value)


def test_rate_limit_translated(monkeypatch):
    monkeypatch.setenv("PLAYERELO_API_KEY", "pe_live_x")

    class _Resp:
        status_code = 429

        def raise_for_status(self):  # pragma: no cover - not reached on 429
            raise AssertionError

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(httpx, "Client", _Client)
    with pytest.raises(server.PlayerEloError) as exc:
        server._get("/v1/value-bets")
    assert "rate limit" in str(exc.value).lower()


def test_404_returns_none(monkeypatch):
    monkeypatch.setenv("PLAYERELO_API_KEY", "pe_live_x")

    class _Resp:
        status_code = 404

        def raise_for_status(self):  # pragma: no cover
            raise AssertionError

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(httpx, "Client", _Client)
    assert server._get("/v1/players/999999999") is None
