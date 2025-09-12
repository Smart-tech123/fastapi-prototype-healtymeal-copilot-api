import pytest

from app.services.ipfilter import IPFilterService, IPPattern


def test_single_ip_match() -> None:
    p = IPPattern("192.168.1.10")
    assert p.matches("192.168.1.10")
    assert not p.matches("192.168.1.11")


def test_range_ip_match() -> None:
    p = IPPattern("10.0.0.5-10.0.0.10")
    assert p.matches("10.0.0.5")
    assert p.matches("10.0.0.7")
    assert p.matches("10.0.0.10")
    assert not p.matches("10.0.0.4")
    assert not p.matches("10.0.0.11")


def test_wildcard_ip_match() -> None:
    p = IPPattern("10.0.*.*")
    assert p.matches("10.0.1.1")
    assert p.matches("10.0.255.255")
    assert not p.matches("10.1.1.1")


def test_cidr_ip_match() -> None:
    p = IPPattern("192.168.0.0/24")
    assert p.matches("192.168.0.1")
    assert p.matches("192.168.0.200")
    assert not p.matches("192.168.1.1")


def test_any_ip_match() -> None:
    p = IPPattern("*")
    assert p.matches("1.2.3.4")
    assert p.matches("10.10.10.10")


def test_filter_service_with_string() -> None:
    svc = IPFilterService("192.168.1.1,10.0.*.*")
    assert svc.is_allowed("192.168.1.1")
    assert svc.is_allowed("10.0.55.55")
    assert not svc.is_allowed("8.8.8.8")


def test_filter_service_with_list_of_patterns() -> None:
    rules: list[str | IPPattern] = [IPPattern("127.0.0.1"), "10.0.0.0/8"]
    svc = IPFilterService(rules)
    assert svc.is_allowed("127.0.0.1")
    assert svc.is_allowed("10.1.2.3")
    assert not svc.is_allowed("192.168.1.1")


def test_empty_filter_blocks_all() -> None:
    svc = IPFilterService([])
    assert not svc.is_allowed("127.0.0.1")
    assert not svc.is_allowed("8.8.8.8")


def test_invalid_wildcard_pattern_raises() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        IPPattern("10.*.*")  # wrong length
