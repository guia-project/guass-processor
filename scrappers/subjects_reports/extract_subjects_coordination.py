from __future__ import annotations

import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup, Tag, NavigableString


def extract_subjects_coordination(html: str) -> Dict[str, Any]:
    """
    Extrae la información de la página 'Coordinación entre asignaturas' de GAUSS.
    """

    def clean(text: Optional[str]) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def clean_question(text: str) -> str:
        text = clean(text)
        return text[:-1].strip() if text.endswith(":") else text

    def extract_text_excluding_strong(tag: Tag) -> str:
        """
        Devuelve el texto del tag excluyendo el contenido de <strong>.
        """
        parts = []

        for child in tag.children:
            if isinstance(child, NavigableString):
                txt = clean(str(child))
                if txt:
                    parts.append(txt)
            elif isinstance(child, Tag):
                if child.name == "strong":
                    continue
                txt = clean(child.get_text(" ", strip=True))
                if txt:
                    parts.append(txt)

        return clean(" ".join(parts))

    def parse_question_answer_pairs(box: Tag) -> Dict[str, Any]:
        """
        Extrae pares pregunta/respuesta de una caja con estructura variable.
        """
        result: Dict[str, Any] = {}
        fondos = box.find_all("div", class_="fondo_resultado", recursive=False)

        i = 0
        while i < len(fondos):
            current = fondos[i]
            strong = current.find("strong")

            if strong is None:
                i += 1
                continue

            question = clean_question(strong.get_text(" ", strip=True))
            answer = None

            # Caso 1: la respuesta viene en el mismo bloque, fuera del <strong>
            inline_answer = extract_text_excluding_strong(current)
            if inline_answer:
                answer = inline_answer

            # Caso 2: si no hay respuesta inline, buscar en bloques siguientes
            if not answer:
                j = i + 1
                while j < len(fondos):
                    next_block = fondos[j]
                    next_strong = next_block.find("strong")

                    # Si el siguiente bloque ya contiene otra pregunta, paramos
                    if next_strong is not None:
                        break

                    candidate = clean(next_block.get_text(" ", strip=True))
                    if candidate:
                        answer = candidate
                        i = j  # avanzamos el índice hasta el bloque consumido
                        break

                    j += 1

            result[question] = answer
            i += 1

        return result

    soup = BeautifulSoup(html, "html.parser")
    apartado = soup.find("div", class_="apartado")
    if apartado is None:
        return {}

    result: Dict[str, Any] = {}

    main_title_el = apartado.find("div", class_="vista", recursive=False)
    main_title = clean(main_title_el.get_text(" ", strip=True)) if main_title_el else "Coordinación entre asignaturas"
    result[main_title] = {}

    children = [c for c in apartado.children if isinstance(c, Tag)]
    current_title = None

    for child in children:
        classes = child.get("class", [])

        if "vista" in classes:
            continue

        # 5.2 aparece como título directo
        if child.name == "div" and "titulo" in classes:
            current_title = clean(child.get_text(" ", strip=True))
            continue

        # cajas de contenido
        if child.name == "div" and "caja" in classes:
            box = child

            # 5.1 tiene el título dentro de la propia caja
            inner_title = box.find("div", class_="titulo", recursive=False)
            if inner_title is not None:
                section_title = clean(inner_title.get_text(" ", strip=True))
            else:
                section_title = current_title

            if section_title:
                result[main_title][section_title] = parse_question_answer_pairs(box)

    return result