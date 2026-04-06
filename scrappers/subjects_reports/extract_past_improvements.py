from __future__ import annotations

import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup


def extract_past_improvements(html: str) -> Dict[str, Any]:
    """
    Extrae la información de la página
    'Propuestas de mejora del curso anterior' de GAUSS.

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

    soup = BeautifulSoup(html, "html.parser")
    apartado = soup.select_one("div.apartado")
    if apartado is None:
        return {}

    result: Dict[str, Any] = {}

    main_title_el = apartado.select_one(":scope > div.vista")
    main_title = clean(main_title_el.get_text(" ", strip=True)) if main_title_el else "Propuestas de mejora del curso anterior"

    result[main_title] = {}

    section_titles = apartado.select(":scope > div.titulo")
    section_boxes = apartado.select(":scope > div.caja")

    for idx, title_el in enumerate(section_titles):
        section_title = clean(title_el.get_text(" ", strip=True))

        if idx >= len(section_boxes):
            result[main_title][section_title] = None
            continue

        box = section_boxes[idx]
        fondo = box.select_one("div.fondo_resultado")

        if fondo is None:
            result[main_title][section_title] = None
            continue

        text = clean(fondo.get_text(" ", strip=True))
        result[main_title][section_title] = text if text else None

    return result