import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.context import ConversationContext


def test_add_and_get_messages():

    ctx = ConversationContext()

    ctx.add_user_message("hola")
    ctx.add_assistant_message("¿Qué tal?")

    messages = ctx.get_messages()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_max_turns_respected():

    ctx = ConversationContext(max_turns=2)

    for i in range(5):

        ctx.add_user_message(f"msg {i}")
        ctx.add_assistant_message(
            f"reply {i}"
        )

    assert len(ctx) == 4


def test_context_string():

    ctx = ConversationContext()

    ctx.add_user_message("hola")
    ctx.add_assistant_message("Hola!")

    text = ctx.get_context_string()

    assert "Usuario: hola" in text
    assert "DECIA: Hola!" in text


def test_clear():

    ctx = ConversationContext()

    ctx.add_user_message("hola")

    assert len(ctx) == 1

    ctx.clear()

    assert len(ctx) == 0


def test_empty_context():

    ctx = ConversationContext()

    assert len(ctx) == 0
    assert ctx.get_messages() == []
    assert ctx.get_context_string() == ""
