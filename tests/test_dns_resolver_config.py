"""Tests for reverse DNS resolver configuration behavior."""

from unittest.mock import MagicMock, patch

from unifi_topology.adapters.dns import resolve_hostnames


def test_resolve_hostnames_sets_nameserver():
    with (
        patch("unifi_topology.adapters.dns.dns.resolver.Resolver") as mock_resolver_cls,
        patch("unifi_topology.adapters.dns.dns.reversename.from_address"),
    ):
        mock_resolver = MagicMock()
        mock_resolver_cls.return_value = mock_resolver
        mock_resolver.resolve.side_effect = Exception("fail")

        resolve_hostnames(["192.168.1.10"], "10.0.0.53")

    assert mock_resolver.nameservers == ["10.0.0.53"]


def test_resolve_hostnames_invalid_dns_server():
    """Setting an invalid DNS server address returns empty dict."""
    with patch("unifi_topology.adapters.dns.dns.resolver.Resolver") as mock_resolver_cls:
        mock_resolver = MagicMock()
        mock_resolver_cls.return_value = mock_resolver
        type(mock_resolver).nameservers = property(
            fget=lambda self: [],
            fset=MagicMock(side_effect=ValueError("Invalid address")),
        )

        result = resolve_hostnames(["192.168.1.10"], "not-an-ip")

    assert result == {}
