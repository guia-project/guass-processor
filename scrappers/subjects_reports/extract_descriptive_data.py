from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag


def extract_descriptive_data(html: str) -> Dict[str, Any]:
    """
    Extrae la información de la página 'Datos de la asignatura' de GAUSS
    a partir del HTML ya descargado.

    Parámetros
    ----------
    html : str
        HTML completo de la página.

    Retorna
    -------
    dict
        JSON serializable con la información descriptiva.
    """

    def clean(text: Optional[str]) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def table_to_matrix(table: Tag) -> List[List[str]]:
        rows: List[List[str]] = []
        for tr in table.select("tr"):
            cells = tr.select("th, td")
            row = [clean(cell.get_text(" ", strip=True)) for cell in cells]
            if any(cell != "" for cell in row):
                rows.append(row)
        return rows

    def parse_identification_table(table: Tag) -> Dict[str, Any]:
        """
        Tabla de 1.1:
        - primeras filas especiales: titulación y curso
        - resto: pares clave/valor
        """
        matrix = table_to_matrix(table)
        data: Dict[str, Any] = {}

        one_cell_rows: List[str] = []
        two_cell_rows: List[List[str]] = []

        for row in matrix:
            if len(row) == 1:
                one_cell_rows.append(row[0])
            elif len(row) == 2:
                two_cell_rows.append(row)

        if len(one_cell_rows) >= 1:
            data["Titulación"] = one_cell_rows[0]
        if len(one_cell_rows) >= 2:
            data["Curso"] = one_cell_rows[1]

        for row in two_cell_rows:
            key, value = row
            data[key] = value if value != "" else None

        return data

    def parse_regular_table(table: Tag) -> List[Dict[str, Any]]:
        """
        Tabla normal con cabecera en la primera fila.
        Si la primera cabecera está vacía, se renombra a 'Rol'.
        """
        matrix = table_to_matrix(table)
        if not matrix:
            return []

        header = matrix[0]
        normalized_header = []
        for idx, h in enumerate(header):
            if h:
                normalized_header.append(h)
            else:
                normalized_header.append("Rol" if idx == 0 else f"col_{idx+1}")

        data: List[Dict[str, Any]] = []
        for row in matrix[1:]:
            if len(row) != len(normalized_header):
                continue
            data.append({normalized_header[i]: row[i] for i in range(len(row))})

        return data

    soup = BeautifulSoup(html, "html.parser")
    apartado = soup.select_one("div.apartado")
    if apartado is None:
        return {}

    result: Dict[str, Any] = {}

    main_title_el = apartado.select_one(":scope > div.vista")
    main_title = clean(main_title_el.get_text(" ", strip=True)) if main_title_el else "Datos descriptivos"
    result[main_title] = {}

    section_titles = apartado.select(":scope > div.titulo")
    section_boxes = apartado.select(":scope > div.caja")

    # -------- 1.1 Identificación --------
    if len(section_titles) >= 1 and len(section_boxes) >= 1:
        section_title = clean(section_titles[0].get_text(" ", strip=True))
        box = section_boxes[0]

        table = box.select_one("table.tabla_resultado")
        section_data = parse_identification_table(table) if table else {}

        notes = [
            clean(p.get_text(" ", strip=True))
            for p in box.select("div.fondo_resultado > p")
            if clean(p.get_text(" ", strip=True))
        ]
        if notes:
            section_data["_notes"] = notes

        result[main_title][section_title] = section_data

    # -------- 1.2 Profesorado --------
    if len(section_titles) >= 2 and len(section_boxes) >= 2:
        section_title = clean(section_titles[1].get_text(" ", strip=True))
        box = section_boxes[1]

        tables = box.select("table.tabla_resultado")
        teaching_data: Dict[str, Any] = {}

        if len(tables) >= 1:
            teaching_data["Coordinación"] = parse_regular_table(tables[0])

        if len(tables) >= 2:
            teaching_data["Profesorado de la asignatura"] = parse_regular_table(tables[1])

        notes = [
            clean(p.get_text(" ", strip=True))
            for p in box.select("div.fondo_resultado > p")
            if clean(p.get_text(" ", strip=True))
        ]
        if notes:
            teaching_data["_notes"] = notes

        result[main_title][section_title] = teaching_data

    return result