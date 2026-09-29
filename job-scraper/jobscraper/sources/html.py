"""Tiện ích đọc HTML: mỗi trường thử nhiều selector vì các trang VN hay đổi giao diện."""
import re
import unicodedata

from bs4 import BeautifulSoup, Tag


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def first(node: Tag, selectors: list[str]) -> Tag | None:
    for sel in selectors:
        found = node.select_one(sel)
        if found:
            return found
    return None


def text(node: Tag, selectors: list[str]) -> str:
    found = first(node, selectors)
    if not found:
        return ""
    return " ".join((found.get("title") or found.get_text(" ")).split())


def all_text(node: Tag, selector: str) -> str:
    return ", ".join(" ".join(n.get_text(" ").split()) for n in node.select(selector))


def slugify(term: str) -> str:
    term = unicodedata.normalize("NFKD", term.lower()).replace("đ", "d")
    term = "".join(c for c in term if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", term).strip("-")
