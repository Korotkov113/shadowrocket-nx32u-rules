#!/usr/bin/env python3

import argparse
import ipaddress
import re
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW = "https://raw.githubusercontent.com/itdoginfo/allow-domains/main"
PUBLIC_RAW = "https://raw.githubusercontent.com/Korotkov113/shadowrocket-nx32u-rules/main"
DOMAIN_SOURCES = (
    "Services/google_ai.lst",
    "Services/telegram.lst",
    "Services/discord.lst",
    "Services/meta.lst",
    "Services/twitter.lst",
    "Services/youtube.lst",
    "Russia/inside-raw.lst",
    "Categories/geoblock.lst",
    "Categories/block.lst",
)
IPV4_SOURCES = (
    "Subnets/IPv4/telegram.lst",
    "Subnets/IPv4/discord.lst",
    "Subnets/IPv4/meta.lst",
    "Subnets/IPv4/twitter.lst",
)
LABEL = re.compile(r"(?:[a-z0-9_]|[a-z0-9_][a-z0-9_-]{0,61}[a-z0-9_])")


def fetch(path: str) -> list[str]:
    request = Request(f"{RAW}/{path}", headers={"User-Agent": "shadowrocket-nx32u-rules/1"})
    text = urlopen(request, timeout=30).read().decode("utf-8-sig")
    values = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not values:
        raise ValueError(f"Пустой upstream-список: {path}")
    return values


def domain(value: str, source: str) -> str:
    value = value.lower().lstrip(".")
    if len(value) > 253 or not value or any(not LABEL.fullmatch(label) for label in value.split(".")):
        raise ValueError(f"Некорректный домен в {source}: {value!r}")
    return value


def validate_config() -> None:
    active = [
        line.strip()
        for line in (ROOT / "shadowrocket.conf").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    required = {
        f"update-url = {PUBLIC_RAW}/shadowrocket.conf",
        "dns-server = https://dns.adguard-dns.com/dns-query#proxy",
        f"RULE-SET,{PUBLIC_RAW}/rules/domains.list,PROXY",
        f"RULE-SET,{PUBLIC_RAW}/rules/ipv4.list,PROXY,no-resolve",
    }
    if not required.issubset(active) or active[-1] != "FINAL,DIRECT":
        raise ValueError("Публичный shadowrocket.conf потерял обязательные настройки")
    excluded_routes = {
        route.strip()
        for line in active
        if line.startswith("tun-excluded-routes = ")
        for route in line.split("=", 1)[1].split(",")
    }
    if "0.0.0.0/8" in excluded_routes or any(
        "https://d.adguard-dns.com/dns-query/" in line for line in active
    ):
        raise ValueError("Публичный shadowrocket.conf содержит небезопасную настройку")


def generate() -> dict[Path, str]:
    domains = {
        domain(value, source)
        for source in DOMAIN_SOURCES
        for value in fetch(source)
    }
    networks = {
        ipaddress.IPv4Network(value, strict=True)
        for source in IPV4_SOURCES
        for value in fetch(source)
    }
    domain_text = "# Generated automatically; do not edit.\n" + "".join(
        f"DOMAIN-SUFFIX,{value}\n" for value in sorted(domains)
    )
    ipv4_text = "# Generated automatically; do not edit.\n" + "".join(
        f"IP-CIDR,{network}\n"
        for network in sorted(networks, key=lambda item: (int(item.network_address), item.prefixlen))
    )
    return {
        ROOT / "rules/domains.list": domain_text,
        ROOT / "rules/ipv4.list": ipv4_text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Обновляет правила Shadowrocket из itdoginfo/allow-domains")
    parser.add_argument("--check", action="store_true", help="проверить актуальность без записи")
    check = parser.parse_args().check
    validate_config()
    generated = generate()
    stale = [path for path, text in generated.items() if not path.exists() or path.read_text(encoding="utf-8") != text]

    if check and stale:
        parser.error("устарели: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))
    if not check:
        for path in stale:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(generated[path], encoding="utf-8")
            temporary.replace(path)

    counts = [text.count("\n") - 1 for text in generated.values()]
    print(f"OK: {counts[0]} доменов, {counts[1]} IPv4-подсетей; изменено файлов: {0 if check else len(stale)}")


if __name__ == "__main__":
    main()
