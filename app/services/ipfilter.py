import ipaddress
from collections.abc import Sequence
from enum import StrEnum


class IPPattern:
    """
    IP pattern matcher.
    Supports:
      - Exact IP: "1.2.3.4"
      - CIDR: "192.168.0.0/24"
      - Wildcard: "10.0.*.*"
      - Range: "10.0.0.5-10.0.0.20"
      - Any: "*"
    """

    class Kind(StrEnum):
        ANY = "any"
        SINGLE = "single"
        RANGE = "range"
        WILDCARD = "wildcard"
        CIDR = "cidr"

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern.strip()

        if self.pattern == "*":
            self.kind = self.Kind.ANY

        elif "-" in self.pattern:
            # IP range like 10.0.0.5-10.0.0.20
            start, end = self.pattern.split("-", 1)
            self.start = ipaddress.ip_address(start.strip())
            self.end = ipaddress.ip_address(end.strip())
            self.kind = self.Kind.RANGE

        elif "*" in self.pattern:
            # Wildcard
            parts = self.pattern.split(".")
            if len(parts) != 4:  # noqa: PLR2004
                msg = f"Invalid wildcard IP: {self.pattern}"
                raise ValueError(msg)
            self.parts = parts
            self.kind = self.Kind.WILDCARD

        elif "/" in self.pattern:
            # CIDR notation
            self.network = ipaddress.ip_network(self.pattern, strict=False)
            self.kind = self.Kind.CIDR

        else:
            # Single exact IP
            self.ip = ipaddress.ip_address(self.pattern)
            self.kind = self.Kind.SINGLE

    def matches(self, ip: str) -> bool:
        ip_obj = ipaddress.ip_address(ip)

        if self.kind is self.Kind.ANY:
            return True
        elif self.kind is self.Kind.SINGLE:  # noqa: RET505
            return ip_obj == self.ip
        elif self.kind is self.Kind.RANGE:
            return self.start <= ip_obj <= self.end  # type: ignore  # noqa: PGH003
        elif self.kind is self.Kind.WILDCARD:
            ip_parts = ip.split(".")
            return all(p in ("*", ip_part) for p, ip_part in zip(self.parts, ip_parts, strict=True))
        elif self.kind is self.Kind.CIDR:
            return ip_obj in self.network
        return False

    @classmethod
    def parse_str(cls, patterns_str: str) -> list["IPPattern"]:
        return [IPPattern(p) for p in patterns_str.split(",") if p.strip()]


class IPFilterService:
    """Allow-list-based IP filter."""

    def __init__(self, allow_patterns: Sequence[str | IPPattern] | str) -> None:
        if isinstance(allow_patterns, str):
            self.allow_rules = IPPattern.parse_str(allow_patterns)
        elif isinstance(allow_patterns, list):
            self.allow_rules = [p if isinstance(p, IPPattern) else IPPattern(p) for p in allow_patterns]
        else:
            msg = f"Invalid allow patterns: {allow_patterns}"
            raise TypeError(msg)

    def is_allowed(self, ip: str) -> bool:
        # If allow list is empty => deny everything (secure default)
        if not self.allow_rules:
            return False
        # Otherwise allow if any rule matches
        return any(rule.matches(ip) for rule in self.allow_rules)
