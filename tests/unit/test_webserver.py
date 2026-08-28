from unittest.mock import patch

from lib.services import webserver
from lib.services.webserver import _addon_capabilities, _is_local_or_private_host


def test_addon_capabilities_requires_supported_movie_prefixes():
    manifest = {
        "types": ["movie", "series"],
        "idPrefixes": ["kitsu:"],
        "resources": [{"name": "stream", "types": ["movie", "series"]}],
    }

    capabilities = _addon_capabilities(manifest)

    assert capabilities == {"stream": False, "catalog": False, "tv": False}


def test_addon_capabilities_accepts_tmdb_stream_prefixes():
    manifest = {
        "types": ["movie", "series"],
        "idPrefixes": ["tmdb:"],
        "resources": ["stream"],
    }

    capabilities = _addon_capabilities(manifest)

    assert capabilities == {"stream": True, "catalog": False, "tv": False}


def test_addon_capabilities_accepts_wildcard_stream_prefixes():
    manifest = {
        "types": ["movie", "series"],
        "resources": [{"name": "stream", "types": ["movie", "series"]}],
    }

    capabilities = _addon_capabilities(manifest)

    assert capabilities == {"stream": True, "catalog": False, "tv": False}


def test_addon_capabilities_keeps_tv_streams_without_movie_prefixes():
    manifest = {
        "types": ["tv"],
        "resources": [{"name": "stream", "types": ["tv"]}],
    }

    capabilities = _addon_capabilities(manifest)

    assert capabilities == {"stream": False, "catalog": False, "tv": True}


def test_local_or_private_host_accepts_public_name_resolving_to_private_ip():
    with patch("lib.services.webserver.socket.getaddrinfo") as getaddrinfo:
        getaddrinfo.return_value = [
            (2, 1, 6, "", ("192.168.50.26", 0)),
        ]

        assert _is_local_or_private_host("https://aiostream.gear5.top/manifest.json") is True


def test_local_or_private_host_accepts_ip_literal_and_localhost():
    assert _is_local_or_private_host("http://192.168.1.10:8080/manifest.json") is True
    assert _is_local_or_private_host("http://localhost:8080/manifest.json") is True


def test_local_or_private_host_rejects_public_name_resolving_to_public_ip():
    with patch("lib.services.webserver.socket.getaddrinfo") as getaddrinfo:
        getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 0)),
        ]

        assert _is_local_or_private_host("https://example.com/manifest.json") is False


def test_local_or_private_host_rejects_when_any_address_is_public():
    with patch("lib.services.webserver.socket.getaddrinfo") as getaddrinfo:
        getaddrinfo.return_value = [
            (2, 1, 6, "", ("192.168.50.26", 0)),
            (2, 1, 6, "", ("93.184.216.34", 0)),
        ]

        assert _is_local_or_private_host("https://dual.example.com/manifest.json") is False


def test_local_or_private_host_rejects_unresolvable_name():
    with patch("lib.services.webserver.socket.getaddrinfo") as getaddrinfo:
        getaddrinfo.side_effect = OSError("name resolution failed")

        assert _is_local_or_private_host("https://does-not-exist.example/manifest.json") is False


def test_sync_add_addon_surfaces_validation_error_message():
    with patch.object(
        webserver, "_fetch_manifest", return_value=(None, None, "invalid manifest URL")
    ):
        addon, error = webserver._sync_add_addon("https://example.com/manifest.json")

    assert addon is None
    assert error == "Failed to fetch manifest: invalid manifest URL"
