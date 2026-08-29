"""
PHASE 9.3 — CENTRAL TEXT NORMALIZATION

Centralización de la normalización textual en
utils.normalizer.normalize. services.archive.normalize
pasa a delegar en la utilidad central (única delta:
strip perimetral). Nada de persistencia, scoring, gates,
búsqueda, dedup, entidades, fechas, ranking ni memoria
cambia.

Contratos verificados:
A.  equivalencia archive.normalize ↔ utils.normalizer.normalize.
B.  whitespace periférico: strip de bordes, sin colapso interior.
C.  deduplicación con/sin espacios periféricos.
D.  search_archive conserva matches (docs y queries
    perimetralmente sucias).
E.  _memory_model / _memory_matches conservan matches.
F.  nombres, entidades, fechas y contenido almacenado se
    conservan verbatim (nunca se re-escriben).
G.  puntuación de queries: comportamiento existente intacto.
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent),
)

from utils import normalizer as central_normalizer

from services.archive import (
    search_archive,
    normalize,
    deduplicate_memories,
    _memory_model,
    _memory_matches,
)


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "time": "10:00",
        "type": "actividad",
        "title": "Memoria de DECIA",
        "description": description,
    }


def _memories_result(results):
    for r in results:
        if r.get("field") == "memories":
            return r
    return None


def _desc_ids(results):
    mem = _memories_result(results)
    if not isinstance(mem, dict):
        return []
    return [
        m.get("description")
        for m in mem.get("data") or []
    ]


EMPTY_HISTORY = {"events": []}


def search(query, memories):
    with (
        patch(
            "services.archive.get_history",
            return_value=EMPTY_HISTORY,
        ),
        patch(
            "services.archive.get_memories",
            return_value={"memories": memories},
        ),
    ):
        return search_archive(query)


# ==========================================
# A. EQUIVALENCIA CON EL CENTRAL
# ==========================================


class TestEquivalencia:

    def test_equivalencia_corpus(self):
        corpus = [
            "Hola",
            "Qué pasó?",
            "recuerda que llegué tarde",
            "hago repaso de VECTORES",
            "JÚPITER",
            "3.5",
            "me gusta la música",
            "¿cuándo fue la sesión?",
            "sobre el planeta marte",
            "mi perro se llama Max.",
            "",
        ]
        for text in corpus:
            assert (
                normalize(text)
                == central_normalizer.normalize(text)
            ), text

    def test_equivalencia_puntuacion_y_acentos(self):
        text = "¿Qué hicimos en la transmisión?"
        assert normalize(text) == (
            "¿que hicimos en la transmision?"
        )
        assert normalize(text) == (
            central_normalizer.normalize(text)
        )


# ==========================================
# B. WHITESPACE PERIFÉRICO
# ==========================================


class TestWhitespacePeriferico:

    def test_strip_bordes(self):
        assert normalize("  repasos  ") == "repasos"
        assert normalize("\tclases\n") == "clases"

    def test_sin_colapso_interior(self):
        """El núcleo central no colapsa espacios
        interiores (eso es normalize_strict; NO
        debe filtrarse aquí)."""
        assert normalize("a  b") == "a  b"

    def test_vacio(self):
        assert normalize("") == ""
        assert normalize("   ") == ""


# ==========================================
# C. DEDUPLICACIÓN CON/SIN ESPACIOS PERIFÉRICOS
# ==========================================


class TestDeduplicacion:

    def test_padding_no_genera_duplicado(self):
        memories = [
            _mem("a1", "2026-08-27",
                 "quiero terminar decia"),
            _mem("a2", "2026-08-27",
                 "  quiero terminar decia  "),
        ]
        unique = deduplicate_memories(memories)
        assert len(unique) == 1

    def test_deduplicacion_preserva_original(self):
        memories = [
            _mem("a1", "2026-08-27",
                 "  quiero terminar decia  "),
            _mem("a2", "2026-08-27",
                 "quiero terminar decia"),
        ]
        unique = deduplicate_memories(memories)
        assert unique[0]["description"] == (
            "  quiero terminar decia  "
        )
        assert unique[0]["date"] == "2026-08-27"

    def test_contenidos_legitimos_con_padding_se_mantienen(
        self,
    ):
        memories = [
            _mem("a1", "2026-08-27",
                 "quiero terminar decia"),
            _mem("a2", "2026-08-27",
                 "quiero terminar decia esta semana"),
        ]
        unique = deduplicate_memories(memories)
        assert len(unique) == 2


# ==========================================
# D. SEARCH_ARCHIVE CONSERVA MATCHES
# ==========================================


class TestSearchMatches:

    def test_descripcion_con_padding_perimetral(self):
        memories = [
            _mem("m1", "2026-08-27",
                 "hago repaso de vectores  "),
            _mem("m2", "2026-08-27",
                 "el gato duerme"),
        ]
        result = search(
            "recuerdas sobre repaso", memories,
        )
        descs = _desc_ids(result)
        assert "hago repaso de vectores  " in descs
        assert "el gato duerme" not in descs

    def test_query_con_padding_perimetral(self):
        memories = [
            _mem("m1", "2026-08-27",
                 "hago repaso de vectores"),
        ]
        for q in (
            "recuerdas sobre repaso ",
            " recuerdas sobre repaso",
        ):
            descs = _desc_ids(search(q, memories))
            assert "hago repaso de vectores" in descs, q

    def test_query_puntuacion_filtrada(self):
        """Puntuación aislada (len <= 2) se filtra del
        matching de igual forma que antes de la
        centralización."""
        memories = [
            _mem("m1", "2026-08-27",
                 "hago repaso de vectores"),
        ]
        a = _desc_ids(
            search("recuerdas sobre repaso", memories)
        )
        b = _desc_ids(
            search(
                "¿ recuerdas ! sobre repaso ?",
                memories,
            )
        )
        assert a == b
        assert "hago repaso de vectores" in a

    def test_puntuacion_pegada_conserva_contrato(self):
        """El token 'repaso.' conserva el punto (igual
        que antes); el matching NO se altera por la
        centralización."""
        assert normalize(
            "recuerdas sobre repaso."
        ) == "recuerdas sobre repaso."
        assert normalize(
            "recuerdas, sobre repaso"
        ) == "recuerdas, sobre repaso"


# ==========================================
# E. MODELO DE MEMORIA / MATCHES
# ==========================================


class TestModelMatches:

    def test_memory_model_padding(self):
        model = _memory_model(
            " hago repaso de vectores "
        )
        assert _memory_matches("repaso", model)
        assert _memory_matches("repasos", model)
        assert _memory_matches("vecina", model) is False

    def test_memory_model_sin_padding_mismos_tokens(
        self,
    ):
        clean = _memory_model("hago repaso de vectores")
        padded = _memory_model(
            "  hago repaso de vectores  "
        )
        assert clean == padded


# ==========================================
# F. CONTENIDO ALMACENADO VERBATIM
# ==========================================


class TestContenidoVerbatim:

    def test_nombres_entidades_fechas_sin_modificacion(
        self,
    ):
        stored = {
            "id": "c1",
            "date": "2026-08-27",
            "time": "19:30",
            "title": "Reunión con Kanye",
            "description": (
                "Hable con Carlos sobre el planeta "
                "Marte."
            ),
        }
        result = search(
            "recuerdas sobre carlos", [stored],
        )
        mem = _memories_result(result)
        data = mem["data"]
        assert data[0]["description"] == stored[
            "description"
        ]
        assert data[0]["date"] == stored["date"]
        assert data[0]["time"] == stored["time"]
        assert data[0]["title"] == stored["title"]
        assert data[0]["id"] == stored["id"]

    def test_nada_se_reescribe_en_disco(self):
        """El flujo de búsqueda no persiste ni toca
        las memorias (solo lee)."""
        memories = [
            _mem("f1", "2026-08-27",
                 "  quiero terminar decia  "),
        ]
        search("recuerdas sobre decia", memories)
        assert memories[0]["description"] == (
            "  quiero terminar decia  "
        )
        assert memories[0]["date"] == "2026-08-27"


# ==========================================
# G. INTEGRACIÓN CON PADDING EN PIPE REAL
# ==========================================


class TestIntegracionPadding:

    def test_doc_y_query_padding_operan_juntos(self):
        memories = [
            _mem("r1", "2026-08-27",
                 "hago repaso de vectores "),
            _mem("r2", "2026-08-27",
                 "mi color favorito es azul"),
        ]
        result = search(
            " recuerdas sobre los repasos ",
            memories,
        )
        descs = _desc_ids(result)
        assert "hago repaso de vectores " in descs
        assert "mi color favorito es azul" not in descs