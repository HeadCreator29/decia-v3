"""
PHASE 9.2 — MORPHOLOGICAL MEMORY RECALL

Recall ADITIVO y conservador para MEMORY_SEARCH ante
variaciones naturales del español (singular/plural y
flexiones verbales de familias explícitas). Se apoya en
formas canónicas seguras (infinitivo o singular completo),
nunca en raíces cortas/ambiguas ni en búsqueda borrosa.

Contratos verificados:
A.  el match EXACTO (_word_match) sigue intacto y manda.
B.  singular/plural: clase<->clases, repaso<->repasos.
C.  flexión verbal regular: repaso/repasamos/repasé,
    estudio/estudiamos/estudié.
D.  irregulares: hice/hicimos<->hacer, fui/fue/fuimos<->ir,
    vi/vimos<->ver.
E.  bidireccionalidad consulta<->memoria.
F.  negativos: ella!=ello, prefijos cortos, temporales que
    no ganan matches, coincidencias parciales sin recall,
    sin apertura de ramas fuera de MEMORY (clasificación).
G/H. integración y ranking en search_archive, aditividad.
I. 0 OLLAMA. J. single-pass.
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

from brain.core import think
from brain.context import ConversationContext
from brain.intent_layer import IntentLayer
from brain.intent_types import (
    FREE_TALK,
    AMBIGUOUS_INPUT,
    MEMORY_SEARCH,
)

from services.archive import (
    search_archive,
    _canonical_word,
    _memory_matches,
    _memory_model,
)

IL = IntentLayer()


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "time": "10:00",
        "description": description,
    }


def _memories_result(results):
    for r in results:
        if r.get("field") == "memories":
            return r
    return None


def _desc_ids(result, results):
    mem = _memories_result(results) or result
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
# F. BASE: FORMA CANÓNICA (unit directo)
# ==========================================


class TestCanonicalUnit:

    def test_singular_plural(self):
        assert _canonical_word("clase") == "clase"
        assert _canonical_word("clases") == "clase"
        assert _canonical_word("repaso") == "repasar"
        assert _canonical_word("repasos") == "repasar"

    def test_flexion_regular(self):
        for f in (
            "repaso", "repasos", "repasamos",
            "repase",
        ):
            assert _canonical_word(f) == "repasar", f
        for f in (
            "estudio", "estudiamos", "estudie",
        ):
            assert _canonical_word(f) == "estudiar", f

    def test_irregulares(self):
        for f in ("hice", "hicimos", "hacer"):
            assert _canonical_word(f) == "hacer", f
        for f in ("fui", "fue", "fuimos", "ir"):
            assert _canonical_word(f) == "ir", f
        for f in ("vi", "vimos", "ver"):
            assert _canonical_word(f) == "ver", f

    def test_negativos_raiz_corta(self):
        assert _canonical_word("pasaron") == "pasaron"
        assert _canonical_word("estudiamos") != "estudi"
        assert _canonical_word("repasamos") != "repas"
        assert _canonical_word("se") != "saber"
        assert _canonical_word("se") == "se"

    def test_negativo_ella_ello(self):
        assert (_canonical_word("ella")
                != _canonical_word("ello"))

    def test_temporales_invariantes(self):
        for w in (
            "lunes", "atlas", "dias", "meses",
            "mananas", "semana", "tardes",
        ):
            assert _canonical_word(w) == w, w

    def test_memory_matches_aditivo(self):
        model = _memory_model(
            "hago repaso de vectores"
        )
        assert _memory_matches("repaso", model)
        assert _memory_matches("repasos", model)
        assert _memory_matches("casamiento", model) is False
        assert _memory_matches("vecina", model) is False


# ==========================================
# A. MATCH EXACTO PRESERVADO
# ==========================================


class TestExactoPreservado:

    def test_exacto_sigue_funcionando(self):
        mem = [
            _mem("k1", "2026-08-20",
                 "me gusta la musica de Kanye"),
            _mem("m2", "2026-08-20",
                 "tengo clase manana"),
        ]
        result = search(
            "recuerdas sobre kanye", mem,
        )
        descs = _desc_ids(None, result)
        assert any("Kanye" in d for d in descs)

        result = search(
            "que recuerdas de mi clase", mem,
        )
        descs = _desc_ids(None, result)
        assert any("clase" in d for d in descs)


# ==========================================
# B. SINGULAR / PLURAL
# ==========================================


class TestPlural:

    def test_clase_clases(self):
        mem = [
            _mem("c1", "2026-08-20",
                 "repase algebra en clase"),
            _mem("c2", "2026-08-20",
                 "mi perro corre en el parque"),
        ]
        result = search(
            "recuerdas sobre las clases", mem,
        )
        descs = _desc_ids(None, result)
        assert "repase algebra en clase" in descs
        assert "mi perro corre en el parque" not in descs

    def test_repaso_repasos(self):
        mem = [
            _mem("r1", "2026-08-20",
                 "hago repaso de vectores"),
            _mem("r2", "2026-08-20",
                 "el gato duerme"),
        ]
        result = search(
            "recuerdas sobre los repasos", mem,
        )
        descs = _desc_ids(None, result)
        assert "hago repaso de vectores" in descs
        assert "el gato duerme" not in descs


# ==========================================
# C. FLEXIÓN VERBAL REGULAR
# ==========================================


class TestFlexionRegular:

    def test_repaso_repasamos(self):
        mem = [
            _mem("r1", "2026-08-20",
                 "hago repaso de vectores"),
        ]
        descs = _desc_ids(
            None,
            search(
                "recuerdas sobre repasamos",
                mem,
            ),
        )
        assert "hago repaso de vectores" in descs

    def test_repaso_repase(self):
        mem = [
            _mem("r1", "2026-08-20",
                 "hago repaso de vectores"),
        ]
        descs = _desc_ids(
            None,
            search(
                "recuerdas sobre repase vectores",
                mem,
            ),
        )
        assert "hago repaso de vectores" in descs

    def test_estudio_estudiamos(self):
        mem = [
            _mem("e1", "2026-08-20",
                 "tuve que estudiar mucha algebra"),
        ]
        descs = _desc_ids(
            None,
            search(
                "recuerdas sobre estudiamos",
                mem,
            ),
        )
        assert (
            "tuve que estudiar mucha algebra"
            in descs
        )

    def test_estudio_estudie(self):
        mem = [
            _mem("e1", "2026-08-20",
                 "tuve que estudiar mucha algebra"),
        ]
        descs = _desc_ids(
            None,
            search(
                "recuerdas sobre estudie algebra",
                mem,
            ),
        )
        assert (
            "tuve que estudiar mucha algebra"
            in descs
        )


# ==========================================
# D. VERBOS IRREGULARES
# ==========================================


class TestIrregulares:

    def test_hacer(self):
        mem = [
            _mem("h1", "2026-08-20",
                 "hicimos la tarea de matematica"),
        ]
        for q in (
            "recuerdas sobre hice",
            "recuerdas sobre hacer",
        ):
            descs = _desc_ids(
                None, search(q, mem),
            )
            assert (
                "hicimos la tarea de matematica"
                in descs
            ), q

    def test_ir(self):
        mem = [
            _mem("i1", "2026-08-20",
                 "fui al gimnasio por la tarde"),
        ]
        for q in (
            "recuerdas sobre fuimos",
            "recuerdas sobre fue",
            "recuerdas sobre ir",
        ):
            descs = _desc_ids(
                None, search(q, mem),
            )
            assert (
                "fui al gimnasio por la tarde"
                in descs
            ), q

    def test_ver(self):
        mem = [
            _mem("v1", "2026-08-20",
                 "vi una pelicula en el cine"),
        ]
        for q in (
            "recuerdas sobre vimos",
            "recuerdas sobre ver",
        ):
            descs = _desc_ids(
                None, search(q, mem),
            )
            assert (
                "vi una pelicula en el cine"
                in descs
            ), q


# ==========================================
# E. BIDIRECCIONALIDAD
# ==========================================


class TestBidireccional:

    def test_verbo_memoria_consultada_flexionada(self):
        mem = [
            _mem("m1", "2026-08-20",
                 "hice la compra del mercado"),
            _mem("m2", "2026-08-21",
                 "hicimos la compra del mercado"),
        ]
        descs1 = _desc_ids(
            None,
            search("recuerdas sobre hicimos", [mem[0]]),
        )
        assert "hice la compra del mercado" in descs1
        descs2 = _desc_ids(
            None,
            search("recuerdas sobre hice", [mem[1]]),
        )
        assert "hicimos la compra del mercado" in descs2

    def test_plural_memoria_consultada_base(self):
        mem = [
            _mem("p1", "2026-08-20",
                 "tengo clases de algebra"),
        ]
        descs = _desc_ids(
            None,
            search("recuerdas sobre la clase", mem),
        )
        assert "tengo clases de algebra" in descs


# ==========================================
# F. CASOS NEGATIVOS
# ==========================================


class TestNegativos:

    def test_ella_no_ello(self):
        mem = [
            _mem("n1", "2026-08-20",
                 "hable con ella en la cena"),
        ]
        descs = _desc_ids(
            None,
            search("que hizo ello", mem),
        )
        assert "hable con ella en la cena" not in descs

    def test_prefijo_corto_no_coincide(self):
        mem = [
            _mem("n2", "2026-08-20",
                 "me compre una casa nueva"),
        ]
        for q in (
            "que hizo con el casamiento",
            "que hizo con la casona",
        ):
            descs = _desc_ids(
                None, search(q, mem),
            )
            assert (
                "me compre una casa nueva" not in descs
            ), q

    def test_temporales_no_ganan_matches(self):
        mem = [
            _mem("n3", "2026-08-20",
                 "tengo clase manana"),
        ]
        for q in (
            "que hizo con las mananas",
            "que hizo con los dias",
        ):
            descs = _desc_ids(
                None, search(q, mem),
            )
            assert (
                "tengo clase manana" not in descs
            ), q

    def test_coincidencia_parcial_no_recupera(self):
        mem = [
            _mem("n4", "2026-08-20",
                 "viaje a canada con amigos"),
            _mem("n5", "2026-08-20",
                 "me gusta la canela en el cafe"),
        ]
        descs = _desc_ids(
            None,
            search("que hizo en canas", mem),
        )
        assert "viaje a canada con amigos" not in descs
        assert "me gusta la canela en el cafe" not in descs

    def test_clasificacion_no_abre_memory(self):
        r = IL.classify("que estudiamos")
        assert r.intent != MEMORY_SEARCH
        assert r.intent in (FREE_TALK, AMBIGUOUS_INPUT)

    def test_ramas_fuera_de_memory_intactas(self):
        with (
            patch(
                "services.archive.get_history",
                return_value={"events": [
                    {
                        "id": "ev1",
                        "date": "2026-08-24",
                        "title": "Demo",
                        "description": "evento demo",
                    },
                ]},
            ),
            patch(
                "services.archive.get_memories",
                return_value={"memories": [
                    _mem("n6", "2026-08-20",
                         "hicimos un gran evento"),
                ]},
            ),
        ):
            result = search_archive("que evento hubo")
        fields = [r.get("field") for r in result]
        assert "events" in fields
        assert "memories" not in fields


# ==========================================
# G/H. INTEGRACIÓN, RANKING Y ADITIVIDAD
# ==========================================


class TestIntegracion:

    def test_ranking_mejora_sin_perder_exactos(self):
        mem = [
            _mem("r1", "2026-08-24",
                 "hago repaso de vectores"),
            _mem("r2", "2026-08-22",
                 "tuve repaso de matematica"),
            _mem("r3", "2026-08-25",
                 "mi color favorito es azul"),
        ]
        result = search(
            "recuerdas sobre los repasos", mem,
        )
        descs = _desc_ids(None, result)
        assert "hago repaso de vectores" in descs
        assert "tuve repaso de matematica" in descs
        assert "mi color favorito es azul" not in descs

    def test_aditiva_con_exactos(self):
        mem = [
            _mem("a1", "2026-08-20",
                 "hice repaso de algebra"),
            _mem("a2", "2026-08-21",
                 "hicimos repasos de geometria"),
            _mem("a3", "2026-08-22",
                 "regamos las plantas"),
        ]
        result = search(
            "recuerdas sobre los repasos", mem,
        )
        descs = _desc_ids(None, result)
        assert "hice repaso de algebra" in descs
        assert "hicimos repasos de geometria" in descs
        assert "regamos las plantas" not in descs

    def test_exacto_no_es_eliminado_por_variante(self):
        mem = [
            _mem("x1", "2026-08-20",
                 "tuve repaso con max"),
            _mem("x2", "2026-08-20",
                 "tuve repasos con kanye"),
        ]
        descs = _desc_ids(
            None,
            search("recuerdas sobre repaso max", mem),
        )
        assert "tuve repaso con max" in descs
        assert "tuve repasos con kanye" in descs


# ==========================================
# I/J. think: 0 OLLAMA y SINGLE-PASS
# ==========================================


class TestThink:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_recall_morfologico_via_think(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("r1", "2026-08-24",
                 "hago repaso de vectores"),
            _mem("r2", "2026-08-22",
                 "mi color favorito es azul"),
        ]}
        calls = {"n": 0}
        import brain.core as coremod
        orig = coremod.search_deca_memory

        def wrapped(msg, *args, **kwargs):
            calls["n"] += 1
            return orig(msg, *args, **kwargs)

        coremod.search_deca_memory = wrapped
        try:
            ctx = ConversationContext()
            response = think(
                "que recuerdas sobre los repasos",
                context=ctx,
            )
        finally:
            coremod.search_deca_memory = orig

        assert "hago repaso de vectores" in response
        assert "mi color favorito es azul" not in response
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"
        assert ctx.last_entity == "los repasos"