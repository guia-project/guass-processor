from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag


def extract_annexes(html: str) -> Dict[str, Any]:
    """
    Extract annexes data from the GAUSS annexes HTML page.

    Returns a JSON-serializable dict where:
    - each annex title is a key
    - inside each annex, each section title is a key
    - each section contains its tables and optional explanatory text/info
    """

    def clean(text: Optional[str]) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def parse_table(table: Tag) -> Any:
        rows: List[List[str]] = []

        for tr in table.select("tr"):
            cells = tr.select("th, td")
            row = [clean(cell.get_text(" ", strip=True)) for cell in cells]
            if any(row):
                rows.append(row)

        if not rows:
            return []

        header = rows[0]
        normalized_header = [
            h if h else "concept"
            for h in header
        ]

        same_len = all(len(row) == len(normalized_header) for row in rows[1:])
        if len(rows) > 1 and same_len:
            return [
                {normalized_header[i]: row[i] for i in range(len(normalized_header))}
                for row in rows[1:]
            ]

        return rows

    def parse_info_block(info_tag: Tag) -> List[str]:
        paragraphs = [
            clean(p.get_text(" ", strip=True))
            for p in info_tag.select("p")
            if clean(p.get_text(" ", strip=True))
        ]
        if paragraphs:
            return paragraphs

        text = clean(info_tag.get_text(" ", strip=True))
        return [text] if text else []

    def parse_fondo_resultado(fondo_tag: Tag) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        # direct nested titles, e.g. "Convocatoria ordinaria"
        inner_titles = [
            clean(t.get_text(" ", strip=True))
            for t in fondo_tag.find_all("div", class_="titulo", recursive=False)
            if clean(t.get_text(" ", strip=True))
        ]
        if inner_titles:
            data["titles"] = inner_titles

        # direct info blocks inside fondo_resultado
        info_blocks = []
        for info in fondo_tag.find_all("div", class_=lambda c: c and "info_tecnica" in c, recursive=False):
            parsed = parse_info_block(info)
            if parsed:
                info_blocks.append(parsed)
        if info_blocks:
            data["info"] = info_blocks

        # direct paragraphs
        paragraphs = [
            clean(p.get_text(" ", strip=True))
            for p in fondo_tag.find_all("p", recursive=False)
            if clean(p.get_text(" ", strip=True))
        ]
        if paragraphs:
            data["paragraphs"] = paragraphs

        # direct tables
        tables = [
            parse_table(table)
            for table in fondo_tag.find_all("table", class_="tabla_resultado", recursive=False)
        ]
        if tables:
            data["tables"] = tables[0] if len(tables) == 1 else tables

        # fallback
        if not data:
            text = clean(fondo_tag.get_text(" ", strip=True))
            if text:
                data["text"] = text

        return data

    def parse_annex_inner(inner: Tag) -> Dict[str, Any]:
        """
        Parse one accordion-inner.
        Uses each .vista as the section key.
        Collects subsequent info/fondo blocks until the next .vista.
        """
        result: Dict[str, Any] = {}
        children = [c for c in inner.children if isinstance(c, Tag)]

        current_section_title: Optional[str] = None
        current_section_data: Dict[str, Any] = {}

        def flush_current():
            nonlocal current_section_title, current_section_data
            if current_section_title:
                result[current_section_title] = current_section_data
            current_section_title = None
            current_section_data = {}

        for child in children:
            classes = child.get("class", [])

            if "vista" in classes:
                flush_current()
                current_section_title = clean(child.get_text(" ", strip=True))
                current_section_data = {}
                continue

            if "info_tecnica" in classes:
                info = parse_info_block(child)
                if info:
                    current_section_data.setdefault("info", []).append(info)
                continue

            if "fondo_resultado" in classes:
                fondo_data = parse_fondo_resultado(child)

                # merge multiple fondo_resultado blocks if needed
                if "content" not in current_section_data:
                    current_section_data["content"] = fondo_data
                else:
                    existing = current_section_data["content"]
                    if isinstance(existing, list):
                        existing.append(fondo_data)
                    else:
                        current_section_data["content"] = [existing, fondo_data]
                continue

        flush_current()
        return result

    soup = BeautifulSoup(html, "html.parser")
    accordion_groups = soup.select("#gia_anexos_listados > .accordion-group")

    result: Dict[str, Any] = {}

    for group in accordion_groups:
        heading = group.select_one(".accordion-heading .accordion-toggle")
        annex_title = clean(heading.get_text(" ", strip=True)) if heading else None
        if not annex_title:
            continue

        inner = group.select_one(".accordion-inner")
        if inner is None:
            result[annex_title] = {}
            continue

        result[annex_title] = parse_annex_inner(inner)

    return result