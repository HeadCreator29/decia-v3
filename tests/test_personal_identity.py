"""Tests for personal identity / preferred_name."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.handlers import (
    personal_identity_handler,
    archive_response,
    identity_response,
)
from services.archive import (
    get_identity,
    get_user,
)


USER_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "archive"
    / "user.json"
)

IDENTITY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "archive"
    / "identity.json"
)


@pytest.fixture
def backup_user():
    """Save and restore user.json around tests."""
    original = USER_PATH.read_text(
        encoding="utf-8"
    )
    yield
    USER_PATH.write_text(
        original, encoding="utf-8"
    )


@pytest.fixture
def backup_identity():
    """Save and restore identity.json around tests."""
    original = IDENTITY_PATH.read_text(
        encoding="utf-8"
    )
    yield
    IDENTITY_PATH.write_text(
        original, encoding="utf-8"
    )


# ==========================================
# 1. identity.json CONTIENE CREATOR
# ==========================================


def test_identity_contains_creator():
    identity = get_identity()
    assert "creator" in identity
    assert identity["creator"] == "Idelvi"


# ==========================================
# 2. user.json CONTIENE PREFERRED_NAME
# ==========================================


def test_user_contains_preferred_name():
    user = get_user()
    assert "preferred_name" in user


# ==========================================
# 3. "QUIEN CREÓ DECA" DEVUELVE CREATOR
# ==========================================


def test_who_created_deca_returns_creator():
    response = archive_response(
        "quién creó DECA"
    )
    assert "Idelvi" in response
    assert "creado por" in response


# ==========================================
# 4. "CÓMO ME LLAMO" DEVUELVE USER_NAME
# ==========================================


def test_how_am_i_called():
    user = get_user()
    expected = user.get(
        "user_name", "Idelvi"
    )
    response = personal_identity_handler(
        "¿cómo me llamo?"
    )
    assert response is not None
    assert expected in response


# ==========================================
# 5. "CÓMO QUIERES LLAMARME" DEVUELVE
#    PREFERRED_NAME
# ==========================================


def test_how_do_you_want_to_call_me():
    user = get_user()
    expected = user.get(
        "preferred_name", "Creador"
    )
    response = personal_identity_handler(
        "¿cómo quieres llamarme?"
    )
    assert response is not None
    assert expected in response


# ==========================================
# 6. "LLÁMAME CREADOR" ACTUALIZA
#    PREFERRED_NAME
# ==========================================


def test_call_me_updates_preferred_name(
    backup_user,
):
    response = personal_identity_handler(
        "llámame Creador"
    )
    assert "Creador" in response

    user = get_user()
    assert user["preferred_name"] == "Creador"


# ==========================================
# 7. CAMBIAR PREFERRED_NAME NO CAMBIA CREATOR
# ==========================================


def test_changing_name_does_not_change_creator(
    backup_user,
):
    personal_identity_handler(
        "llámame Amigo"
    )

    user = get_user()
    assert user["preferred_name"] == "Amigo"
    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 8. "MI NOMBRE ES IDELVI" NO DESTRUYE CREATOR
# ==========================================


def test_my_name_does_not_destroy_creator(
    backup_user,
):
    personal_identity_handler(
        "mi nombre es Idelvi"
    )

    user = get_user()
    assert user["user_name"] == "Idelvi"
    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 9. "LLÁMAME" SIN NOMBRE NO GUARDA VACÍO
# ==========================================


def test_call_me_without_name_does_not_save(
    backup_user,
):
    response = personal_identity_handler(
        "llámame"
    )
    assert response is not None
    assert "¿Cómo quieres que te llame?" in response

    user = get_user()
    assert user["preferred_name"] != ""


# ==========================================
# 10. PREFERRED_NAME PERSISTE DESPUÉS DE
#     GUARDAR
# ==========================================


def test_preferred_name_persists(
    backup_user,
):
    personal_identity_handler(
        "llámame Amiga"
    )

    loaded = get_user()
    assert loaded["preferred_name"] == "Amiga"


# ==========================================
# 11. CONSULTAS DE IDENTIDAD NO LLAMAN A
#     OLLAMA (se resuelven localmente)
# ==========================================


def test_identity_queries_are_local(
    backup_user,
):
    r1 = personal_identity_handler(
        "¿cómo me llamo?"
    )
    r2 = personal_identity_handler(
        "llámame Test"
    )
    r3 = personal_identity_handler(
        "mi nombre es Test"
    )
    r4 = archive_response("quién creó DECA")

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None
    assert r4 is not None


# ==========================================
# 12. CONTEXTO CONVERSACIONAL SIGUE
#     FUNCIONANDO
# ==========================================


def test_context_still_works():
    from brain.context import ConversationContext

    ctx = ConversationContext()
    ctx.add_user_message("hola")
    ctx.add_assistant_message("qué tal")

    messages = ctx.get_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


# ==========================================
# 13. ARCHIVO DECA SIGUE CARGÁNDOSE
#     CORRECTAMENTE
# ==========================================


def test_deca_archive_still_loads():
    response = archive_response(
        "cuándo comenzó DECA"
    )
    assert response is not None
    assert "2025" in response


# ==========================================
# 14. PREGUNTAS SOBRE DECIA NO SE MEZCLAN
# ==========================================


def test_decia_identity_not_confused():
    response = identity_response(
        "¿quién eres?"
    )
    assert "DECIA" in response

    user = get_user()
    name = user.get("preferred_name")
    assert name not in response or name != "DECIA"


# ==========================================
# 15. "Y CUÁLES ES MI NOMBRE" → USER_NAME
# ==========================================


def test_y_cuales_es_mi_nombre():
    user = get_user()
    expected = user.get(
        "user_name", "Idelvi"
    )
    response = personal_identity_handler(
        "y cuáles es mi nombre"
    )
    assert response is not None
    assert expected in response


# ==========================================
# 16. "EL NOMBRE MÍO ES X" → USER_NAME
# ==========================================


def test_el_nombre_mio_es(backup_user):
    response = personal_identity_handler(
        "el nombre mío es Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["user_name"] == "Idelby"


# ==========================================
# 17. TEXTO ANTES DE LA DECLARACIÓN
# ==========================================


def test_prefix_before_name_declaration(
    backup_user,
):
    response = personal_identity_handler(
        "todo está mal, el nombre mío es Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["user_name"] == "Idelby"


# ==========================================
# 18. "YO ME LLAMO X" → USER_NAME
# ==========================================


def test_yo_me_llamo(backup_user):
    response = personal_identity_handler(
        "yo me llamo Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["user_name"] == "Idelby"


# ==========================================
# 19. "QUIERO QUE ME LLAMES X" → PREFERRED
# ==========================================


def test_quiero_que_me_llames(backup_user):
    response = personal_identity_handler(
        "quiero que me llames Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["preferred_name"] == "Idelby"


# ==========================================
# 20. "PUEDES LLAMARME X" → PREFERRED
# ==========================================


def test_puedes_llamarme(backup_user):
    response = personal_identity_handler(
        "puedes llamarme Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["preferred_name"] == "Idelby"


# ==========================================
# 21. CORRECCIÓN "NO, MI NOMBRE ES PEDRO"
#     → USER_NAME
# ==========================================


def test_no_mi_nombre_es_pedro(backup_user):
    personal_identity_handler(
        "mi nombre es Juan"
    )

    response = personal_identity_handler(
        "no, mi nombre es Pedro"
    )
    assert "Pedro" in response

    user = get_user()
    assert user["user_name"] == "Pedro"


# ==========================================
# 22. CREATOR NO CAMBIA AL CAMBIAR NOMBRE
# ==========================================


def test_creator_never_changes(
    backup_user,
):
    original = get_identity()["creator"]

    personal_identity_handler(
        "mi nombre es Pedro"
    )
    personal_identity_handler(
        "no, mi nombre es Sofia"
    )
    personal_identity_handler(
        "llámame Ana"
    )

    user = get_user()
    assert get_identity()["creator"] == original
    assert user["preferred_name"] == "Ana"
    assert user["user_name"] == "Sofia"


# ==========================================
# 23. "ME LLAMO X" → USER_NAME
# ==========================================


def test_me_llamo(backup_user):
    response = personal_identity_handler(
        "me llamo Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["user_name"] == "Idelby"


# ==========================================
# 24. NOMBRE NO SE INVENTA (SIN APELLIDO)
# ==========================================


def test_no_inventa_apellido(backup_user):
    response = personal_identity_handler(
        "mi nombre es Idelby"
    )

    user = get_user()
    assert user["user_name"] == "Idelby"
    assert "Becolta" not in user.get(
        "user_name", ""
    )


# ==========================================
# 25. "EL MÍO ES X" → USER_NAME
# ==========================================


def test_el_mio_es(backup_user):
    response = personal_identity_handler(
        "el mío es Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["user_name"] == "Idelby"


# ==========================================
# 26. "DESDE AHORA LLÁMAME X" → PREFERRED
# ==========================================


def test_desde_ahora_llamame(backup_user):
    response = personal_identity_handler(
        "desde ahora llámame Carlos"
    )
    assert "Carlos" in response

    user = get_user()
    assert user["preferred_name"] == "Carlos"


# ==========================================
# 27. "NOMBRE MÍO ES X" → USER_NAME
# ==========================================


def test_nombre_mio_es(backup_user):
    response = personal_identity_handler(
        "nombre mío es Idelby"
    )
    assert "Idelby" in response

    user = get_user()
    assert user["user_name"] == "Idelby"


# ==========================================
# 28. SECUENCIA COMPLETA DE CONVERSACIÓN
# ==========================================


def test_full_conversation_sequence(
    backup_user,
):
    # "¿Cómo me llamo?" → user_name
    user = get_user()
    expected = user.get(
        "user_name", "Idelvi"
    )
    r1 = personal_identity_handler(
        "¿cómo me llamo?"
    )
    assert expected in r1

    # "Mi nombre es Edelbi." → user_name
    r2 = personal_identity_handler(
        "mi nombre es Edelbi"
    )
    assert "Edelbi" in r2
    assert get_user()["user_name"] == "Edelbi"

    # "Todo está mal, el nombre mío es Idelby."
    r3 = personal_identity_handler(
        "todo está mal, el nombre mío es Idelby"
    )
    assert "Idelby" in r3
    assert get_user()["user_name"] == "Idelby"

    # "¿Cuál es mi nombre?" → user_name
    r4 = personal_identity_handler(
        "¿cuál es mi nombre?"
    )
    assert "Idelby" in r4

    # "¿Quién creó DECA?" → creator
    r5 = archive_response("¿quién creó DECA?")
    assert "Idelvi" in r5
    assert get_user()["user_name"] == "Idelby"

    # "¿Cómo quieres llamarme?" → preferred_name
    r6 = personal_identity_handler(
        "¿cómo quieres llamarme?"
    )
    user = get_user()
    expected_pref = user.get(
        "preferred_name", "Creador"
    )
    assert expected_pref in r6

    # "Mi nombre es Pedro." → user_name
    r7 = personal_identity_handler(
        "mi nombre es Pedro"
    )
    assert "Pedro" in r7
    assert get_user()["user_name"] == "Pedro"
    assert (
        get_user()["preferred_name"] != "Pedro"
        or get_user()["preferred_name"]
        == user.get("preferred_name", "Creador")
    )

    # "¿Quién creó DECA?" → sigue siendo Idelvi
    r8 = archive_response("¿quién creó DECA?")
    assert "Idelvi" in r8
    assert get_user()["user_name"] == "Pedro"


# ==========================================
# 29. user.json TIENE USER_NAME
# ==========================================


def test_user_json_has_user_name():
    user = get_user()
    assert "user_name" in user
    assert isinstance(user["user_name"], str)
    assert len(user["user_name"]) > 0


# ==========================================
# 30. user.json TIENE PREFERRED_NAME
# ==========================================


def test_user_json_has_preferred_name():
    user = get_user()
    assert "preferred_name" in user
    assert isinstance(
        user["preferred_name"], str
    )
    assert len(user["preferred_name"]) > 0


# ==========================================
# 31. identity.json TIENE CREATOR
# ==========================================


def test_identity_json_has_creator():
    identity = get_identity()
    assert "creator" in identity
    assert isinstance(identity["creator"], str)
    assert len(identity["creator"]) > 0


# ==========================================
# 32. "MI NOMBRE ES X" CAMBIA USER_NAME
# ==========================================


def test_mi_nombre_cambia_user_name(
    backup_user,
):
    personal_identity_handler(
        "mi nombre es Pedro"
    )
    user = get_user()
    assert user["user_name"] == "Pedro"


# ==========================================
# 33. "MI NOMBRE ES X" NO CAMBIA PREFERRED
# ==========================================


def test_mi_nombre_no_cambia_preferred_name(
    backup_user,
):
    original = get_user()["preferred_name"]

    personal_identity_handler(
        "mi nombre es Pedro"
    )

    user = get_user()
    assert user["preferred_name"] == original


# ==========================================
# 34. "LLÁMAME X" CAMBIA PREFERRED_NAME
# ==========================================


def test_llamame_cambia_preferred_name(
    backup_user,
):
    personal_identity_handler(
        "llámame Jefe"
    )
    user = get_user()
    assert user["preferred_name"] == "Jefe"


# ==========================================
# 35. "LLÁMAME X" NO CAMBIA USER_NAME
# ==========================================


def test_llamame_no_cambia_user_name(
    backup_user,
):
    original = get_user()["user_name"]

    personal_identity_handler(
        "llámame Jefe"
    )

    user = get_user()
    assert user["user_name"] == original


# ==========================================
# 36. CAMBIAR USER_NAME NO CAMBIA CREATOR
# ==========================================


def test_cambiar_user_name_no_cambia_creator(
    backup_user,
):
    personal_identity_handler(
        "mi nombre es Pedro"
    )
    user = get_user()
    assert user["user_name"] == "Pedro"
    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 37. CAMBIAR PREFERRED NO CAMBIA CREATOR
# ==========================================


def test_cambiar_preferred_name_no_cambia_creator(
    backup_user,
):
    personal_identity_handler(
        "llámame Jefe"
    )
    user = get_user()
    assert user["preferred_name"] == "Jefe"
    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 38. "¿CÓMO ME LLAMO?" DEVUELVE USER_NAME
# ==========================================


def test_como_me_llamo_devuelve_user_name(
    backup_user,
):
    user = get_user()
    user_name = user.get(
        "user_name", "Idelvi"
    )

    response = personal_identity_handler(
        "¿cómo me llamo?"
    )

    assert user_name in response
    assert "Tu nombre es" in response


# ==========================================
# 39. "¿CÓMO QUIERES LLAMARME?" DEVUELVE
#     PREFERRED_NAME
# ==========================================


def test_como_quieres_llamarme_devuelve_preferred(
    backup_user,
):
    user = get_user()
    preferred = user.get(
        "preferred_name", "Creador"
    )

    response = personal_identity_handler(
        "¿cómo quieres llamarme?"
    )

    assert preferred in response
    assert "Quiero llamarte" in response


# ==========================================
# 40. "¿QUIÉN CREÓ DECA?" DEVUELVE CREATOR
# ==========================================


def test_quien_creo_deca_devuelve_creator():
    response = archive_response(
        "¿quién creó DECA?"
    )

    assert "Idelvi" in response
    assert "creado por" in response


# ==========================================
# 41. HANDLERS DE IDENTIDAD SON LOCALES
# ==========================================


def test_handlers_son_locales(backup_user):
    r1 = personal_identity_handler(
        "¿cómo me llamo?"
    )
    r2 = personal_identity_handler(
        "mi nombre es Test"
    )
    r3 = personal_identity_handler(
        "llámame Test"
    )
    r4 = personal_identity_handler(
        "¿cómo quieres llamarme?"
    )
    r5 = archive_response("¿quién creó DECA?")

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None
    assert r4 is not None
    assert r5 is not None


# ==========================================
# 42. IDENTIDAD NO USA OLLAMA
# ==========================================


def test_no_se_llama_ollama_para_identidad(
    backup_user,
):
    queries = [
        "¿cómo me llamo?",
        "¿cuál es mi nombre?",
        "¿cómo quieres llamarme?",
        "mi nombre es Test",
        "llámame Test",
    ]

    for q in queries:
        result = personal_identity_handler(q)
        assert result is not None


# ==========================================
# 43. USER_NAME PERSISTE EN user.json
# ==========================================


def test_user_name_persiste(backup_user):
    personal_identity_handler(
        "mi nombre es Idelvi"
    )

    loaded = get_user()
    assert loaded["user_name"] == "Idelvi"


# ==========================================
# 44. PREFERRED_NAME PERSISTE EN user.json
# ==========================================


def test_preferred_name_persiste_2(
    backup_user,
):
    personal_identity_handler(
        "llámame Creador"
    )

    loaded = get_user()
    assert loaded["preferred_name"] == "Creador"


# ==========================================
# 45. PALABRA SUELTA "DALÍN" NO CAMBIA
#     USER_NAME
# ==========================================


def test_palabra_suelta_no_cambia_user_name(
    backup_user,
):
    original = get_user()["user_name"]

    result = personal_identity_handler("Dalín")

    assert result is None
    assert get_user()["user_name"] == original


# ==========================================
# 46. "PEDRO" SUELTO NO CAMBIA USER_NAME
# ==========================================


def test_pedro_suelto_no_cambia_user_name(
    backup_user,
):
    original = get_user()["user_name"]

    result = personal_identity_handler("Pedro")

    assert result is None
    assert get_user()["user_name"] == original


# ==========================================
# 47. "HOLA" NO CAMBIA USER_NAME
# ==========================================


def test_hola_no_cambia_user_name(
    backup_user,
):
    original = get_user()["user_name"]

    result = personal_identity_handler("hola")

    assert result is None
    assert get_user()["user_name"] == original


# ==========================================
# 48. "MI NOMBRE ES PEDRO" SÍ CAMBIA
#     USER_NAME
# ==========================================


def test_mi_nombre_es_pedro_si_cambia(
    backup_user,
):
    result = personal_identity_handler(
        "mi nombre es Pedro"
    )

    assert result is not None
    assert get_user()["user_name"] == "Pedro"


# ==========================================
# 49. "ME LLAMO PEDRO" SÍ CAMBIA USER_NAME
# ==========================================


def test_me_llamo_pedro_si_cambia(
    backup_user,
):
    result = personal_identity_handler(
        "me llamo Pedro"
    )

    assert result is not None
    assert get_user()["user_name"] == "Pedro"


# ==========================================
# 50. SYSTEM PROMPT PROHÍBE INVENTAR NOMBRES
# ==========================================


def test_ollama_prompt_prohibe_inventar_nombres():
    from services.ollama_service import (
        SYSTEM_PROMPT,
    )

    assert "NUNCA" in SYSTEM_PROMPT
    assert "inventes el nombre" in SYSTEM_PROMPT
    assert "user_name" in SYSTEM_PROMPT
    assert "palabra aislada" in SYSTEM_PROMPT


# ==========================================
# 51. CREATOR PERMANECE INTACTO TRAS
#     PALABRA SUELTA
# ==========================================


def test_creator_intacto_tras_palabra_suelta():
    personal_identity_handler("Dalín")

    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 52. PREFERRED PERMANECE INTACTO TRAS
#     PALABRA SUELTA
# ==========================================


def test_preferred_intacto_tras_palabra_suelta(
    backup_user,
):
    original = get_user()["preferred_name"]

    personal_identity_handler("Pedro")

    assert (
        get_user()["preferred_name"] == original
    )


# ==========================================
# 53. "QUIÉN SOY" → USER_NAME
# ==========================================


def test_quien_soy_devuelve_user_name():
    user = get_user()
    expected = user.get(
        "user_name", "Idelvi"
    )

    response = personal_identity_handler(
        "¿quién soy?"
    )

    assert response is not None
    assert expected in response


# ==========================================
# 54. "Y QUIÉN SOY" → USER_NAME
# ==========================================


def test_y_quien_soy_devuelve_user_name():
    user = get_user()
    expected = user.get(
        "user_name", "Idelvi"
    )

    response = personal_identity_handler(
        "¿y quién soy?"
    )

    assert response is not None
    assert expected in response


# ==========================================
# 55. "QUIÉN SOY" NO DEVUELVE DECIA
# ==========================================


def test_quien_soy_nunca_devuelve_decia():
    response = personal_identity_handler(
        "¿quién soy?"
    )

    assert response is not None
    assert "DECIA" not in response


# ==========================================
# 56. "PEDRO" SUELTO RETORNA NONE
# ==========================================


def test_pedro_suelto_retorna_none():
    result = personal_identity_handler("Pedro")
    assert result is None


# ==========================================
# 57. "DALÍN" SUELTO RETORNA NONE
# ==========================================


def test_dalin_suelto_retorna_none():
    result = personal_identity_handler("Dalín")
    assert result is None


# ==========================================
# 58. "DARLING" SUELTO RETORNA NONE
# ==========================================


def test_darling_suelto_retorna_none():
    result = personal_identity_handler("Darling")
    assert result is None


# ==========================================
# 59. PALABRA SUELTA NO CAMBIA USER_NAME
# ==========================================


def test_palabra_suelta_no_cambia_user_name_2(
    backup_user,
):
    original = get_user()["user_name"]

    for word in [
        "Pedro",
        "Dalín",
        "Darling",
        "Idelvi",
        "Adelante",
    ]:
        personal_identity_handler(word)

    assert get_user()["user_name"] == original


# ==========================================
# 60. PALABRA SUELTA NO CAMBIA PREFERRED
# ==========================================


def test_palabra_suelta_no_cambia_preferred(
    backup_user,
):
    original = get_user()["preferred_name"]

    for word in [
        "Pedro",
        "Dalín",
        "Darling",
    ]:
        personal_identity_handler(word)

    assert (
        get_user()["preferred_name"] == original
    )


# ==========================================
# 61. PALABRA SUELTA NO CAMBIA CREATOR
# ==========================================


def test_palabra_suelta_no_cambia_creator():
    for word in [
        "Pedro",
        "Dalín",
        "Darling",
    ]:
        personal_identity_handler(word)

    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 62. "MI NOMBRE ES PEDRO" CAMBIA USER_NAME
# ==========================================


def test_mi_nombre_es_pedro_cambia_user_name(
    backup_user,
):
    personal_identity_handler("mi nombre es Pedro")
    assert get_user()["user_name"] == "Pedro"


# ==========================================
# 63. "ME LLAMO PEDRO" CAMBIA USER_NAME
# ==========================================


def test_me_llamo_pedro_cambia_user_name(
    backup_user,
):
    personal_identity_handler("me llamo Pedro")
    assert get_user()["user_name"] == "Pedro"


# ==========================================
# 64. "LLÁMAME JEFE" CAMBIA PREFERRED
# ==========================================


def test_llamame_jefe_cambia_preferred(
    backup_user,
):
    personal_identity_handler("llámame Jefe")
    assert get_user()["preferred_name"] == "Jefe"


# ==========================================
# 65. "LLÁMAME JEFE" NO CAMBIA USER_NAME
# ==========================================


def test_llamame_jefe_no_cambia_user_name(
    backup_user,
):
    original = get_user()["user_name"]

    personal_identity_handler("llámame Jefe")

    assert get_user()["user_name"] == original


# ==========================================
# 66. "QUIÉN SOY" NO USA OLLAMA
# ==========================================


def test_quien_soy_no_usa_ollama():
    r1 = personal_identity_handler("¿quién soy?")
    r2 = personal_identity_handler("¿y quién soy?")
    r3 = personal_identity_handler(
        "¿quién soy, DECIA?"
    )

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None


# ==========================================
# 67. "QUIÉN SOY" NUNCA DICE QUE ES DECIA
# ==========================================


def test_quien_soy_nunca_dice_decia():
    response = personal_identity_handler(
        "¿quién soy?"
    )

    assert response is not None
    assert "DECIA" not in response
    assert "decia" not in response.lower()


# ==========================================
# 68. "QUIÉN CREÓ DECA" SIGUE DEVOLVIENDO
#     CREATOR
# ==========================================


def test_quien_creo_deca_sigue_devolviendo_creator():
    response = archive_response(
        "¿quién creó DECA?"
    )

    assert "Idelvi" in response
    assert "creado por" in response


# ==========================================
# 69. CREATOR NUNCA CAMBIA
# ==========================================


def test_creator_nunca_cambia(backup_user):
    personal_identity_handler("mi nombre es Pedro")
    personal_identity_handler("llámame Jefe")
    personal_identity_handler("¿quién soy?")

    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 70. USER_NAME PERSISTE
# ==========================================


def test_user_name_persiste_2(backup_user):
    personal_identity_handler("mi nombre es Pedro")
    loaded = get_user()
    assert loaded["user_name"] == "Pedro"


# ==========================================
# 71. PREFERRED_NAME PERSISTE
# ==========================================


def test_preferred_name_persiste_3(
    backup_user,
):
    personal_identity_handler("llámame Jefe")
    loaded = get_user()
    assert loaded["preferred_name"] == "Jefe"


# ==========================================
# 72. "¿QUIÉN SOY?" CON TEXTO ADICIONAL
# ==========================================


def test_quien_soy_con_texto_adicional():
    user = get_user()
    expected = user.get(
        "user_name", "Idelvi"
    )

    response = personal_identity_handler(
        "quién soy, DECIA?"
    )

    assert response is not None
    assert expected in response


# ==========================================
# 73. "¿CÓMO ME LLAMA?" → PREFERRED_NAME
# ==========================================


def test_como_me_llama_devuelve_preferred(
    backup_user,
):
    user = get_user()
    preferred = user.get(
        "preferred_name", "Creador"
    )

    response = personal_identity_handler(
        "¿cómo me llama?"
    )

    assert response is not None
    assert preferred in response
    assert "Te llamo" in response


# ==========================================
# 74. "¿CÓMO ME LLAMAS?" → PREFERRED_NAME
# ==========================================


def test_como_me_llamas_devuelve_preferred(
    backup_user,
):
    user = get_user()
    preferred = user.get(
        "preferred_name", "Creador"
    )

    response = personal_identity_handler(
        "¿cómo me llamas?"
    )

    assert response is not None
    assert preferred in response
    assert "Te llamo" in response


# ==========================================
# 75. "¿CÓMO ME LLAMAS TÚ?" → PREFERRED_NAME
# ==========================================


def test_como_me_llamas_tu_devuelve_preferred(
    backup_user,
):
    user = get_user()
    preferred = user.get(
        "preferred_name", "Creador"
    )

    response = personal_identity_handler(
        "¿cómo me llamas tú?"
    )

    assert response is not None
    assert preferred in response
    assert "Te llamo" in response


# ==========================================
# 76. "¿CÓMO ME LLAMAS?" NO CAMBIA USER_NAME
# ==========================================


def test_como_me_llamas_no_cambia_user_name(
    backup_user,
):
    original = get_user()["user_name"]

    personal_identity_handler("¿cómo me llamas?")

    assert get_user()["user_name"] == original


# ==========================================
# 77. "¿CÓMO ME LLAMA?" NO CAMBIA CREATOR
# ==========================================


def test_como_me_llama_no_cambia_creator(
    backup_user,
):
    personal_identity_handler("¿cómo me llama?")

    assert get_identity()["creator"] == "Idelvi"


# ==========================================
# 78. "¿CÓMO ME LLAMAS?" NO CAMBIA PREFERRED
# ==========================================


def test_como_me_llamas_no_cambia_preferred(
    backup_user,
):
    original = get_user()["preferred_name"]

    personal_identity_handler("¿cómo me llamas?")

    assert (
        get_user()["preferred_name"] == original
    )


# ==========================================
# 79. NINGUNA MODIFICA OLLAMA (LOCAL)
# ==========================================


def test_como_me_llamas_no_usa_ollama():
    r1 = personal_identity_handler(
        "¿cómo me llama?"
    )
    r2 = personal_identity_handler(
        "¿cómo me llamas?"
    )
    r3 = personal_identity_handler(
        "¿cómo me llamas tú?"
    )

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None


# ==========================================
# 80. NINGUNA RESPONDE "DECIA" COMO NOMBRE
# ==========================================


def test_como_me_llamas_nunca_dice_decia():
    r1 = personal_identity_handler(
        "¿cómo me llama?"
    )
    r2 = personal_identity_handler(
        "¿cómo me llamas?"
    )
    r3 = personal_identity_handler(
        "¿cómo me llamas tú?"
    )

    assert "DECIA" not in r1
    assert "DECIA" not in r2
    assert "DECIA" not in r3


# ==========================================
# 81. VARIANTES DE MAYÚSCULAS/MINÚSCULAS
# ==========================================


def test_como_me_llamas_case_variations(
    backup_user,
):
    user = get_user()
    preferred = user.get(
        "preferred_name", "Creador"
    )

    variants = [
        "¿cómo me llamas?",
        "CÓMO ME LLAMAS",
        "Cómo Me Llamas",
        "¿Cómo Me Llamas Tú?",
        "¿CÓMO ME LLAMA?",
    ]

    for v in variants:
        response = personal_identity_handler(v)
        assert response is not None
        assert preferred in response


# ==========================================
# 82. TESTS EXISTENTES SIGUEN FUNCIONANDO
# ==========================================


def test_existing_patterns_still_work(
    backup_user,
):
    user = get_user()
    user_name = user.get("user_name", "Idelvi")
    preferred = user.get(
        "preferred_name", "Creador"
    )

    r1 = personal_identity_handler(
        "¿cómo me llamo?"
    )
    assert user_name in r1

    r2 = personal_identity_handler(
        "¿quién soy?"
    )
    assert user_name in r2

    r3 = personal_identity_handler(
        "¿cómo quieres llamarme?"
    )
    assert preferred in r3

    r4 = personal_identity_handler(
        "¿cómo me llamas?"
    )
    assert preferred in r4


# ==========================================
# 83. "¿QUIÉN TE CREÓ?" → IDENTITY_RESPONSE
# ==========================================


def test_quien_te_creo_devuelve_creator():
    response = identity_response(
        "¿quién te creó?"
    )

    assert response is not None
    assert "Idelvi" in response
    assert "DECA" in response


# ==========================================
# 84. "¿QUÉ ERES?" → IDENTITY_RESPONSE
# ==========================================


def test_que_eres_devuelve_decia():
    response = identity_response("¿qué eres?")

    assert response is not None
    assert "DECIA" in response


# ==========================================
# 85. IDENTITY.JSON NO TIENE USER_NAME
# ==========================================


def test_identity_json_no_tiene_user_name():
    identity = get_identity()
    assert "user_name" not in identity


# ==========================================
# 86. IDENTITY.JSON NO TIENE PREFERRED_NAME
# ==========================================


def test_identity_json_no_tiene_preferred_name():
    identity = get_identity()
    assert "preferred_name" not in identity
