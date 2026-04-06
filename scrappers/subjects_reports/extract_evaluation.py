from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, NavigableString, Tag


def extract_evaluation(html: str) -> Dict[str, Any]:
    """
    Extrae la información de la página 'Valoración de la evaluación' de GAUSS.

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

    def extract_text_blocks(container: Tag) -> List[str]:
        """
        Extrae bloques de texto del fondo_resultado respetando los cortes
        naturales por div/p/br en la medida de lo posible.
        """
        blocks: List[str] = []

        for child in container.children:
            if isinstance(child, NavigableString):
                txt = clean(str(child))
                if txt:
                    blocks.append(txt)
                continue

            if not isinstance(child, Tag):
                continue

            txt = clean(child.get_text(" ", strip=True))
            if txt:
                blocks.append(txt)

        # Fallback por si todo viene muy compactado
        if not blocks:
            full_text = clean(container.get_text(" ", strip=True))
            if full_text:
                blocks.append(full_text)

        return blocks

    soup = BeautifulSoup(html, "html.parser")
    apartado = soup.select_one("div.apartado")
    if apartado is None:
        return {}

    result: Dict[str, Any] = {}

    main_title_el = apartado.select_one(":scope > div.vista")
    main_title = clean(main_title_el.get_text(" ", strip=True)) if main_title_el else "Valoración de la evaluación"

    result[main_title] = {}

    fondo = apartado.select_one(":scope > div.caja > div.fondo_resultado")
    if fondo is None:
        result[main_title]["contenido"] = None
        return result

    text_blocks = extract_text_blocks(fondo)
    full_text = clean(fondo.get_text(" ", strip=True))

    result[main_title]["contenido"] = full_text if full_text else None
    result[main_title]["bloques"] = text_blocks

    return result