from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag


def extract_results_kpis(html: str) -> Dict[str, Any]:
    """
    Extrae la información de la página 'Tasas de resultados' de GAUSS.

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

    def parse_table(table: Tag) -> List[Dict[str, Any]]:
        headers = [clean(th.get_text(" ", strip=True)) for th in table.select("thead th")]
        rows = []

        for tr in table.select("tbody tr"):
            cells = [clean(td.get_text(" ", strip=True)) for td in tr.select("td")]
            if not any(cells):
                continue
            if headers and len(headers) == len(cells):
                rows.append({headers[i]: cells[i] for i in range(len(headers))})
            else:
                rows.append({"values": cells})

        return rows

    soup = BeautifulSoup(html, "html.parser")
    apartado = soup.select_one("div.apartado")
    if apartado is None:
        return {}

    result: Dict[str, Any] = {}

    main_title_el = apartado.select_one(":scope > div.vista")
    main_title = clean(main_title_el.get_text(" ", strip=True)) if main_title_el else "Tasas de resultados"

    result[main_title] = {}

    caja = apartado.select_one(":scope > div.caja")
    if caja is None:
        return result

    titles = caja.select(":scope > div.titulo")
    fondos = caja.select(":scope > div.fondo_resultado")

    # 4.1
    if len(titles) >= 1:
        section_title = clean(titles[0].get_text(" ", strip=True))
        section_data: Dict[str, Any] = {}

        if len(fondos) >= 1:
            satisfaction_table = fondos[0].select_one("table.tabla_satisfaccion")
            if satisfaction_table:
                parsed_rows = parse_table(satisfaction_table)
                section_data["tabla"] = parsed_rows[0] if len(parsed_rows) == 1 else parsed_rows

        if len(fondos) >= 2:
            scale_notes = [
                clean(p.get_text(" ", strip=True))
                for p in fondos[1].select("p")
                if clean(p.get_text(" ", strip=True))
            ]
            if scale_notes:
                section_data["escala"] = scale_notes

        result[main_title][section_title] = section_data

    # 4.2
    if len(titles) >= 2:
        section_title = clean(titles[1].get_text(" ", strip=True))
        section_text = None

        if len(fondos) >= 3:
            section_text = clean(fondos[2].get_text(" ", strip=True))

        result[main_title][section_title] = section_text if section_text else None

    return result