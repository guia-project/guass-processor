from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag


def extract_next_improvements(html: str) -> Dict[str, Any]:
    """
    Extrae la información de la página 'Propuestas de mejora' de GAUSS.

    Parámetros
    ----------
    html : str
        HTML completo de la página.

    Retorna
    -------
    dict
        JSON serializable con la información extraída.
    """

    def clean(text: Optional[str]) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def parse_single_row_table(table: Tag) -> Dict[str, Any]:
        headers = [clean(th.get_text(" ", strip=True)) for th in table.select("thead th")]
        row = table.select_one("tbody tr")
        if row is None:
            return {}

        values = [clean(td.get_text(" ", strip=True)) for td in row.select("td")]
        if headers and len(headers) == len(values):
            return {headers[i]: values[i] for i in range(len(headers))}

        return {"values": values}

    soup = BeautifulSoup(html, "html.parser")
    apartado = soup.select_one("div.apartado")
    if apartado is None:
        return {}

    result: Dict[str, Any] = {}

    main_title_el = apartado.select_one(":scope > div.vista")
    main_title = clean(main_title_el.get_text(" ", strip=True)) if main_title_el else "Propuestas de mejora"

    result[main_title] = {}

    children = [c for c in apartado.children if isinstance(c, Tag)]

    pending_title: Optional[str] = None

    for child in children:
        classes = child.get("class", [])

        if "vista" in classes:
            continue

        if child.name == "div" and "titulo" in classes:
            pending_title = clean(child.get_text(" ", strip=True))
            continue

        if child.name == "div" and "caja" in classes:
            box = child

            # Caso 6.2: el título está dentro de la caja
            inner_title = box.find("div", class_="titulo", recursive=False)
            if inner_title is not None:
                section_title = clean(inner_title.get_text(" ", strip=True))
            else:
                section_title = pending_title

            if not section_title:
                continue

            fondo = box.find("div", class_="fondo_resultado")
            if fondo is None:
                result[main_title][section_title] = None
                continue

            table = fondo.find("table")
            if table is not None:
                result[main_title][section_title] = parse_single_row_table(table)
            else:
                text = clean(fondo.get_text(" ", strip=True))
                result[main_title][section_title] = text if text else None

    return result