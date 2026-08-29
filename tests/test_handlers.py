import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.handlers import (
    quick_response,
    identity_response,
    calculate,
    memory_request,
    format_archive_response,
    ambiguous_input_response,
    search_deca_memory,
)


# ==========================================
# quick_response
# ==========================================


def test_greeting_hola():

    assert quick_response("hola") is not None


def test_greeting_buenas():

    assert quick_response("buenas") is not None


def test_thanks():

    result = quick_response("gracias")

    assert result is not None


def test_no_match():

    assert quick_response("cuéntame algo") is None


# ==========================================
# identity_response
# ==========================================


def test_identity_quien_eres():

    result = identity_response("quién eres")

    assert result is not None
    assert "DECIA" in result


def test_identity_nombre():

    result = identity_response(
        "cómo te llamas"
    )

    assert result is not None


def test_identity_no_match():

    assert identity_response("hola") is None


# ==========================================
# calculate
# ==========================================


def test_calc_add():

    assert calculate("2 + 3") == "5"


def test_calc_multiply():

    assert calculate("4 * 5") == "20"


def test_calc_no_match():

    assert calculate("hola") is None


# ==========================================
# memory_request
# ==========================================


def test_memory_guarda_que():

    result = memory_request(
        "guarda que hoy me sentí bien"
    )

    assert result == "hoy me senti bien"


def test_memory_recuerda_que():

    result = memory_request(
        "recuerda que la reunión fue a las 3"
    )

    assert result is not None


def test_memory_con_decia():

    result = memory_request(
        "decia guarda que llegué tarde"
    )

    assert result is not None


def test_memory_no_match():

    assert memory_request("hola") is None


# ==========================================
# format_archive_response
# ==========================================


def test_format_meaning():

    result = format_archive_response({
        "field": "meaning",
        "data": "Test meaning",
    })

    assert result == "Test meaning"


def test_format_vision():

    result = format_archive_response({
        "field": "vision",
        "data": "Test vision",
    })

    assert result == "Test vision"


def test_format_creator():

    result = format_archive_response({
        "field": "creator",
        "data": "Idelvi",
    })

    assert "Idelvi" in result


def test_format_values():

    result = format_archive_response({
        "field": "values",
        "data": ["a", "b", "c"],
    })

    assert "a" in result
    assert "b" in result
    assert "c" in result


def test_format_unknown_field():

    result = format_archive_response({
        "field": "unknown",
        "data": "test",
    })

    assert result is None


# ==========================================
# ambiguous_input_response
# ==========================================


def test_ambiguous_single_word_name():

    assert ambiguous_input_response("Pedro") is not None


def test_ambiguous_single_word_topic():

    assert ambiguous_input_response("Photoshop") is not None


def test_ambiguous_two_words():

    assert ambiguous_input_response("Photoshop gratis") is not None


def test_ambiguous_three_words_passes():

    assert ambiguous_input_response("Photoshop es gratis") is None


def test_ambiguous_question_mark_passes():

    assert ambiguous_input_response("¿Pedro?") is None


def test_ambiguous_with_question_word_passes():

    assert ambiguous_input_response("¿qué es Pedro?") is None


def test_ambiguous_empty_string():

    result = ambiguous_input_response("")

    assert result is not None


def test_ambiguous_just_punctuation():

    result = ambiguous_input_response("¿?")

    assert result is None


def test_ambiguous_spanish_name():

    assert ambiguous_input_response("Dalín") is not None


def test_ambiguous_common_word():

    assert ambiguous_input_response("ayuda") is not None


def test_ambiguous_two_common_words():

    assert ambiguous_input_response("por favor") is not None


def test_ambiguous_with_intent_keyword_passes():

    assert ambiguous_input_response("hola Pedro") is None


def test_ambiguous_long_message_passes():

    msg = "esto es un mensaje largo para probar"

    assert ambiguous_input_response(msg) is None


def test_ambiguous_four_words_passes():

    assert ambiguous_input_response("cuatro palabras aquí") is None


# ==========================================
# ROUTING: ambiguous input blocks Ollama
# ==========================================


from unittest.mock import patch


def test_ambiguous_blocks_ollama():

    with patch(
        "brain.core.ask_ollama",
        return_value="Ollama respondió",
    ) as mock:

        from brain.core import think

        result = think("Pedro")

        mock.assert_not_called()

        assert result is not None


def test_non_ambiguous_reaches_ollama():

    with patch(
        "brain.core.ask_ollama",
        return_value="Ollama respondió",
    ) as mock:

        from brain.core import think

        result = think("¿Qué es la fotosíntesis?")

        mock.assert_called_once()

        assert result == "Ollama respondió"


# ==========================================
# search_deca_memory: FALSE POSITIVE CREATOR
# ==========================================


def test_garbled_creates_no_creator():

    result = search_deca_memory("y ente creo")

    assert result is None


def test_creates_que_si_no_creator():

    result = search_deca_memory("creo que sí")

    assert result is None


def test_yo_creates_no_creator():

    result = search_deca_memory("yo creo")

    assert result is None


def test_creates_suelto_no_creator():

    result = search_deca_memory("creo")

    assert result is None


# ==========================================
# search_deca_memory: VALID CREATOR QUERIES
# ==========================================


def test_quien_creado_returns_creator():

    result = search_deca_memory("quién creó")

    assert result is not None
    assert result["field"] == "creator"
    assert result["score"] >= 80


def test_quien_creado_deca_returns_creator():

    result = search_deca_memory(
        "quién creó DECA"
    )

    assert result is not None
    assert result["field"] == "creator"
    assert result["score"] >= 80


def test_quien_creador_deca_returns_creator():

    result = search_deca_memory(
        "quién es el creador de DECA"
    )

    assert result is not None
    assert result["field"] == "creator"
    assert result["score"] >= 80


def test_quien_fundo_deca_returns_creator():

    result = search_deca_memory(
        "quién fundó DECA"
    )

    assert result is not None
    assert result["field"] == "creator"
    assert result["score"] >= 80


def test_creador_de_deca_returns_creator():

    result = search_deca_memory(
        "creador de DECA"
    )

    assert result is not None
    assert result["field"] == "creator"
    assert result["score"] >= 80


# ==========================================
# search_deca_memory: OTHER FIELDS STILL
# WORK WITH WORD BOUNDARIES
# ==========================================


def test_significado_de_deca_returns_meaning():

    result = search_deca_memory(
        "qué significa DECA"
    )

    assert result is not None
    assert result["field"] == "meaning"


def test_valores_de_deca_returns_values():

    result = search_deca_memory(
        "valores de DECA"
    )

    assert result is not None
    assert result["field"] == "values"


def test_historias_no_match_memoria():

    result = search_deca_memory("historias")

    assert result is None


def test_memoria_returns_memories():

    result = search_deca_memory(
        "recuerda algo"
    )

    if result is not None:

        assert result["field"] == "memories"


# ==========================================
# search_deca_memory: THRESHOLD
# ==========================================


def test_low_score_returns_none():

    from services.archive import search_archive

    results = search_archive("creo que sí")

    scores = [r["score"] for r in results]

    low_scores = [s for s in scores if s < 80]

    assert len(low_scores) == len(scores)
