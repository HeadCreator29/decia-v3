from collections import deque


class ConversationContext:

    def __init__(self, max_turns=10):

        self.max_turns = max_turns

        self.history = deque(
            maxlen=max_turns * 2
        )

        self.last_intent = None

        self.last_topic = None

        self.last_entity = None

        self.conversation_mode = None

        self.previous_user_input = None

    def set_context(
        self, intent, mode=None,
        topic=None, entity=None,
        source_message=None,
    ):

        self.last_intent = intent

        self.conversation_mode = mode

        self.last_topic = (
            topic if topic is not None
            else intent
        )

        self.last_entity = entity

        if source_message:

            self.previous_user_input = (
                source_message
            )

    def invalidate(self):

        self.last_intent = None

        self.last_topic = None

        self.last_entity = None

        self.conversation_mode = None

        self.previous_user_input = None

    def add_user_message(self, message):

        self.history.append({
            "role": "user",
            "content": message,
        })

    def add_assistant_message(
        self, message
    ):

        self.history.append({
            "role": "assistant",
            "content": message,
        })

    def get_messages(self):

        return list(self.history)

    def get_context_string(self):

        lines = []

        for entry in self.history:

            role = entry["role"]

            prefix = (
                "Usuario"
                if role == "user"
                else "DECIA"
            )

            lines.append(
                f"{prefix}: {entry['content']}"
            )

        return "\n".join(lines)

    def clear(self):

        self.history.clear()

    def __len__(self):

        return len(self.history)
