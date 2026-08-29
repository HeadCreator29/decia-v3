import json
import re

from datetime import (
    datetime,
    timedelta,
)

from pathlib import Path

from utils.date_parser import parse_relative_date

from utils.normalizer import (
    normalize as _normalize,
)

BASE_DIR = Path(__file__).resolve().parents[2]

ARCHIVE_PATH = BASE_DIR / "data" / "archive"


# ==========================================
# CARGAR ARCHIVOS
# ==========================================


def load_archive(filename):

    path = ARCHIVE_PATH / filename

    try:

        with open(
            path, "r", encoding="utf-8"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        print(
            f"[DECIA ARCHIVE] "
            f"Archivo no encontrado: {filename}"
        )

        return {}

    except json.JSONDecodeError:

        print(
            f"[DECIA ARCHIVE] "
            f"JSON corrupto: {filename}"
        )

        return {}


# ==========================================
# IDENTIDAD
# ==========================================


def get_identity():

    return load_archive("identity.json")


def save_identity(data):

    path = ARCHIVE_PATH / "identity.json"

    try:

        with open(
            path, "w", encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except Exception as error:

        print(
            f"[DECIA ARCHIVE] "
            f"Error al guardar identity: {error}"
        )


# ==========================================
# USUARIO (user.json)
# ==========================================


def get_user():

    return load_archive("user.json")


def save_user(data):

    path = ARCHIVE_PATH / "user.json"

    try:

        with open(
            path, "w", encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except Exception as error:

        print(
            f"[DECIA ARCHIVE] "
            f"Error al guardar user: {error}"
        )


# ==========================================
# HISTORIA
# ==========================================


def get_history():

    return load_archive("history.json")


# ==========================================
# MEMORIAS
# ==========================================


def get_memories():

    path = ARCHIVE_PATH / "memories.json"

    if not path.exists():

        return {}

    try:

        content = path.read_text(encoding="utf-8")

        parsed = json.loads(content)

        if not isinstance(parsed, dict):

            print(
                "[DECIA ARCHIVE] "
                "memories.json tipo invalido, "
                "haciendo backup..."
            )

            backup_corrupted_memories()

            return {}

    except (json.JSONDecodeError, ValueError):

        print(
            "[DECIA ARCHIVE] "
            "memories.json corrupto, "
            "haciendo backup..."
        )

        backup_corrupted_memories()

        return {}

    return load_archive("memories.json")


# ==========================================
# CONTEXTO COMPLETO PARA OLLAMA
# ==========================================


def build_archive_context():

    identity = get_identity()
    history = get_history()
    memories = get_memories()

    context = []

    context.append("IDENTIDAD DE DECA:")

    context.append(
        json.dumps(
            identity,
            ensure_ascii=False,
            indent=2,
        )
    )

    context.append("\nHISTORIA DE DECA:")

    context.append(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        )
    )

    context.append(
        "\nMEMORIAS RECIENTES DE DECIA:"
    )

    context.append(
        json.dumps(
            memories,
            ensure_ascii=False,
            indent=2,
        )
    )

    return "\n".join(context)


# ==========================================
# NORMALIZAR TEXTO
# (centralizado en utils.normalizer.normalize;
#  único delta vs. la versión local previa:
#  - strip perimetral de espacios/tabs)
# ==========================================


def normalize(text):

    return _normalize(text)


# ==========================================
# DEDUPLICAR MEMORIAS
# ==========================================


def deduplicate_memories(memories):

    seen = set()

    unique = []

    for memory in memories:

        date = memory.get("date", "") or ""

        desc = (
            memory.get("description", "")
            or memory.get("content", "")
            or ""
        )

        key = (str(date), normalize(desc))

        if key in seen:

            continue

        seen.add(key)

        unique.append(memory)

    return unique


# ==========================================
# BUSCAR EN EL ARCHIVO
# ==========================================


def _word_match(word, query):

    return bool(
        re.search(r'\b' + word + r'\b', query)
    )


# ==========================================
# FORMA CANÓNICA (PHASE 9.2)
# Recceiling morfológico ADITIVO y explícito:
# nunca sustituye el match exacto (_word_match),
# solo aporta formas canónicas seguras para las
# familias soportadas. No pliega raíces cortas ni
# ambiguas: cada forma de superficie se mapea a
# una base completa (infinitivo o singular).
# ==========================================


_VERB_FAMILY_BASE = {
    # ---------------- repasar ----------------
    "repasar": "repasar", "repaso": "repasar",
    "repasas": "repasar", "repasa": "repasar",
    "repasamos": "repasar",
    "repasan": "repasar", "repase": "repasar",
    "repasaste": "repasar", "repasaron": "repasar",
    "repasando": "repasar", "repasado": "repasar",
    # ---------------- estudiar ----------------
    "estudiar": "estudiar", "estudio": "estudiar",
    "estudias": "estudiar", "estudia": "estudiar",
    "estudiamos": "estudiar",
    "estudian": "estudiar", "estudie": "estudiar",
    "estudiaste": "estudiar",
    "estudiaron": "estudiar", "estudiando": "estudiar",
    "estudiado": "estudiar",
    # ---------------- hacer ----------------
    "hacer": "hacer", "hago": "hacer",
    "haces": "hacer", "hace": "hacer",
    "hacemos": "hacer", "hacen": "hacer",
    "hice": "hacer", "hiciste": "hacer",
    "hizo": "hacer", "hicimos": "hacer",
    "hicieron": "hacer", "hecho": "hacer",
    "hecha": "hacer", "hechas": "hacer",
    "hechos": "hacer", "haciendo": "hacer",
    # ---------------- ir ----------------
    "ir": "ir", "voy": "ir", "vas": "ir",
    "va": "ir", "vamos": "ir", "van": "ir",
    "fui": "ir", "fuiste": "ir", "fue": "ir",
    "fuimos": "ir", "fueron": "ir",
    "iba": "ir", "ibamos": "ir", "iban": "ir",
    "yendo": "ir", "ido": "ir",
    # ---------------- ver ----------------
    "ver": "ver", "veo": "ver", "ves": "ver",
    "ve": "ver", "vemos": "ver", "ven": "ver",
    "vi": "ver", "viste": "ver", "vio": "ver",
    "vimos": "ver", "vieron": "ver",
    "viendo": "ver", "visto": "ver",
    # ---------------- comer ----------------
    "comer": "comer", "como": "comer",
    "comes": "comer", "come": "comer",
    "comemos": "comer", "comen": "comer",
    "comi": "comer", "comiste": "comer",
    "comio": "comer", "comimos": "comer",
    "comieron": "comer", "comiendo": "comer",
    "comido": "comer",
    # ---------------- aprender ----------------
    "aprender": "aprender", "aprendo": "aprender",
    "aprendes": "aprender", "aprende": "aprender",
    "aprendemos": "aprender",
    "aprenden": "aprender", "aprendi": "aprender",
    "aprendiste": "aprender",
    "aprendio": "aprender",
    "aprendimos": "aprender",
    "aprendieron": "aprender",
    "aprendiendo": "aprender",
    "aprendido": "aprender",
    # ---------------- terminar ----------------
    "terminar": "terminar", "termino": "terminar",
    "terminas": "terminar", "termina": "terminar",
    "terminamos": "terminar",
    "terminan": "terminar", "termine": "terminar",
    "terminaste": "terminar",
    "terminaron": "terminar", "terminando": "terminar",
    "terminado": "terminar",
    # ---------------- tener ----------------
    "tener": "tener", "tengo": "tener",
    "tienes": "tener", "tiene": "tener",
    "tenemos": "tener", "tienen": "tener",
    "tuve": "tener", "tuviste": "tener",
    "tuvo": "tener", "tuvimos": "tener",
    "tuvieron": "tener", "tenia": "tener",
    "teniamos": "tener", "tenido": "tener",
    "teniendo": "tener",
    # ---------------- saber ----------------
    "saber": "saber", "sabes": "saber",
    "sabe": "saber", "sabemos": "saber",
    "saben": "saber", "supe": "saber",
    "supiste": "saber", "supo": "saber",
    "supimos": "saber", "supieron": "saber",
    "sabia": "saber", "sabido": "saber",
    # ---------------- hablar ----------------
    "hablar": "hablar", "hablo": "hablar",
    "hablas": "hablar", "habla": "hablar",
    "hablamos": "hablar",
    "hablan": "hablar", "hable": "hablar",
    "hablaste": "hablar",
    "hablaron": "hablar", "hablando": "hablar",
    "hablado": "hablar",
    # ---------------- llegar ----------------
    "llegar": "llegar", "llegas": "llegar",
    "llega": "llegar", "llegamos": "llegar",
    "llegaron": "llegar", "llegando": "llegar",
    "llegado": "llegar",
}


_CANONICAL_EXCEPTIONS = {
    # Invariables o formas que NO deben
    # singularizarse ni plegarse:
    # - días de la semana
    # - sustantivos invariables
    # - términos temporales (para que la
    #   morfología no genere matches)
    "lunes", "martes", "miercoles",
    "miércoles", "jueves", "viernes",
    "sabado", "sábado", "domingo",
    "atlas", "virus", "caos", "dios",
    "hoy", "ayer", "anteayer",
    "dia", "dias", "día", "días",
    "semana", "semanas",
    "mes", "meses",
    "anio", "anios", "año", "años",
    "manana", "mananas",
    "mañana", "mañanas",
    "tarde", "tardes",
    "noche", "noches",
}


def _canonical_word(word):

    # Sólo aporta una forma canónica segura; el
    # match exacto de _word_match nunca se toca.

    if word in _CANONICAL_EXCEPTIONS:

        return word

    base = _VERB_FAMILY_BASE.get(word)

    if base:

        return base

    # Singularización conservadora: se quita el
    # plural -s y se deja la palabra COMPLETA
    # (nunca una raíz corta ni ambigua). Si la
    # forma singular es un verbo soportado, se
    # resuelve a su familia.

    if (
        word.endswith("s")
        and len(word) - 1 >= 4
    ):

        singular = word[:-1]

        base = _VERB_FAMILY_BASE.get(singular)

        if base:

            return base

        return singular

    return word


def _memory_model(description):

    tokens = normalize(description).split()

    return (
        set(tokens),
        {
            _canonical_word(t)
            for t in tokens
        },
    )


def _memory_matches(word, model):

    raw, canonical = model

    if word in raw:

        return True

    if _canonical_word(word) in canonical:

        return True

    return False


# ==========================================
# RESOLVER FILTRO TEMPORAL
# ==========================================


_POINT_TEMPORAL_RE = re.compile(
    r"(?:\bhoy\b"
    r"|\bayer\b"
    r"|\banteayer\b"
    r"|hace\s+(?:una?|\d+)\s+"
    r"(?:dia|dias|semana|semanas|mes|meses)"
    r"|\bel\s+(?:lunes|martes|miercoles|jueves"
    r"|viernes|sabado|domingo))"
)


def _month_range(month_date):

    first = month_date.replace(day=1)

    if first.month == 12:

        next_month = (
            first.replace(
                year=first.year + 1,
                month=1,
            )
        )

    else:

        next_month = first.replace(
            month=first.month + 1
        )

    last = next_month - timedelta(days=1)

    return (
        first.isoformat(),
        last.isoformat(),
    )


def _resolve_temporal_filter(query):

    # ----------------------------------
    # MES PASADO
    # ----------------------------------

    if re.search(
        r"\b(?:el\s+)?mes\s+pasado\b",
        query,
    ):

        today = datetime.now().astimezone().date()

        return _month_range(
            today.replace(day=1) - timedelta(days=1)
        )

    # ----------------------------------
    # ESTE MES
    # ----------------------------------

    if re.search(r"\beste\s+mes\b", query):

        return _month_range(
            datetime.now().astimezone().date()
        )

    # ----------------------------------
    # (LA) SEMANA PASADA  (Lunes-Domingo)
    # ----------------------------------

    if re.search(
        r"\b(?:la\s+)?semana\s+pasada\b",
        query,
    ):

        today = datetime.now().astimezone().date()

        this_monday = (
            today - timedelta(days=today.weekday())
        )

        last_monday = (
            this_monday - timedelta(days=7)
        )

        return (
            last_monday.isoformat(),
            (
                last_monday + timedelta(days=6)
            ).isoformat(),
        )

    # ----------------------------------
    # ESTA SEMANA (Lunes-Domingo)
    # ----------------------------------

    if re.search(r"\besta\s+semana\b", query):

        today = datetime.now().astimezone().date()

        monday = (
            today - timedelta(days=today.weekday())
        )

        return (
            monday.isoformat(),
            (
                monday + timedelta(days=6)
            ).isoformat(),
        )

    # ----------------------------------
    # PUNTUAL: hoy / ayer / anteayer /
    # hace N dias, semanas o meses /
    # el <dia de la semana>
    # ----------------------------------

    if _POINT_TEMPORAL_RE.search(query):

        target = parse_relative_date(query)

        day = target.isoformat()

        return (day, day)

    return None


def search_archive(query):

    query = normalize(query)

    results = []

    # ==========================================
    # INTENCIONES
    # ==========================================

    meaning_words = [
        "representa",
        "significa",
        "significado",
    ]

    origin_words = [
        "comenzo",
        "empezo",
        "inicio",
        "nacio",
    ]

    vision_words = [
        "vision",
        "objetivo",
    ]

    values_words = [
        "valores",
        "principios",
    ]

    creator_words = [
        "creo",
        "creador",
        "fundador",
        "fundada",
        "fundo",
    ]

    history_words = [
        "historia",
        "paso",
        "sucedio",
        "acontecimiento",
        "acontecimientos",
        "acontecio",
        "hechos",
        "eventos",
        "evento",
    ]

    memory_words = [
        "recuerda",
        "recuerdas",
        "recuerdo",
        "recuerdame",
        "memoria",
        "memorias",
        "hicimos",
        "hice",
        "hizo",
        "dije",
        "dijiste",
        "hablamos",
        "hablado",
        "hoy",
        "ayer",
        "anteayer",
        "transmision",
        "transmisión",
        "gusta",
        "quiero",
        "llama",
        "sobre",
        "sabes",
        "favorito",
        "favorita",
        "proyecto",
        "llama",
    ]

    recall_triggers = {
        "recuerda", "recuerdas", "recuerdo",
        "recuerdame", "sabes", "sobre",
    }

    # ==========================================
    # IDENTITY
    # ==========================================

    identity = get_identity()

    # ==========================================
    # SIGNIFICADO
    # ==========================================

    if any(
        _word_match(word, query)
        for word in meaning_words
    ):

        if "meaning" in identity:

            results.append({
                "type": "direct",
                "file": "identity.json",
                "field": "meaning",
                "score": 100,
                "data": identity["meaning"],
            })

    # ==========================================
    # ORIGEN
    # ==========================================

    if any(
        _word_match(word, query)
        for word in origin_words
    ):

        origin = identity.get("origin")

        if origin:

            results.append({
                "type": "direct",
                "file": "identity.json",
                "field": "origin",
                "score": 100,
                "data": origin,
            })

    # ==========================================
    # VISIÓN
    # ==========================================

    if any(
        _word_match(word, query)
        for word in vision_words
    ):

        if "vision" in identity:

            results.append({
                "type": "direct",
                "file": "identity.json",
                "field": "vision",
                "score": 100,
                "data": identity["vision"],
            })

    # ==========================================
    # VALORES
    # ==========================================

    if any(
        _word_match(word, query)
        for word in values_words
    ):

        if "values" in identity:

            results.append({
                "type": "direct",
                "file": "identity.json",
                "field": "values",
                "score": 100,
                "data": identity["values"],
            })

    # ==========================================
    # CREADOR
    # ==========================================

    creator_context = [
        "quien",
        "quien",
        "creador",
        "fundador",
        "fundada",
        "deca",
    ]

    has_creator_word = any(
        _word_match(word, query)
        for word in creator_words
    )

    has_creator_context = any(
        _word_match(word, query)
        for word in creator_context
    )

    if has_creator_word and has_creator_context:

        if "creator" in identity:

            results.append({
                "type": "direct",
                "file": "identity.json",
                "field": "creator",
                "score": 100,
                "data": identity["creator"],
            })

    elif has_creator_word:

        if "creator" in identity:

            results.append({
                "type": "direct",
                "file": "identity.json",
                "field": "creator",
                "score": 50,
                "data": identity["creator"],
            })

    # ==========================================
    # HISTORIA
    # ==========================================

    if any(
        _word_match(word, query)
        for word in history_words
    ):

        history = get_history()

        events = history.get("events", [])

        # G4: cuando la consulta de ARCHIVE/EVENTS
        # trae una referencia temporal explícita,
        # los eventos se filtran por la misma
        # ventana que usa MEMORY (reutiliza
        # _resolve_temporal_filter). Sin
        # referencia temporal no se filtra.

        temporal_range = (
            _resolve_temporal_filter(query)
        )

        if temporal_range:

            start_date, end_date = temporal_range

            events = [
                e
                for e in events
                if start_date
                <= str(e.get("date", ""))
                <= end_date
            ]

        if events:

            results.append({
                "type": "history",
                "file": "history.json",
                "field": "events",
                "score": 100,
                "data": events,
            })

        elif temporal_range:
            # G4: consulta ARCHIVE/EVENTS con
            # referencia temporal pero sin eventos
            # en esa ventana -> resultado EVENTS
            # vacío (score 100) para que el dominio
            # archive no sea ocupado por memorias y
            # core responda el aviso determinista
            # ("No encontré información registrada
            # en el archivo.").
            results.append({
                "type": "history",
                "file": "history.json",
                "field": "events",
                "score": 100,
                "data": [],
            })

    # ==========================================
    # MEMORIAS
    # ==========================================

    if (
        any(
            _word_match(word, query)
            for word in memory_words
        )
        or _resolve_temporal_filter(query)
        is not None
    ):

        memories_data = get_memories()

        memories = memories_data.get(
            "memories", []
        )

        # --------------------------------------
        # FILTRO TEMPORAL
        # (hoy / ayer / anteayer / hace N dias,
        #  semanas o meses / el <dia de la
        #  semana> / esta semana / semana pasada
        #  / este mes / mes pasado)
        # --------------------------------------

        temporal_range = (
            _resolve_temporal_filter(query)
        )

        if temporal_range:

            start_date, end_date = temporal_range

            memories = [
                m
                for m in memories
                if start_date
                <= str(m.get("date", ""))
                <= end_date
            ]

        # --------------------------------------
        # FILTRAR POR PALABRAS CLAVE
        # --------------------------------------

        stop_words = {
            "que", "de", "mi", "el", "la", "los",
            "las", "un", "una", "unos", "unas",
            "del", "al", "en", "y", "o", "a",
            "e", "u", "no", "si", "se", "le",
            "lo", "me", "te", "nos", "les",
            "este", "esta", "esto", "ese", "esa",
            "eso", "hay", "son", "es", "fue",
            "ser", "estar", "haber", "tener",
            "hacer", "poder", "querer", "saber",
        }

        query_words = [
            w for w in query.split()
            if len(w) > 2 and w not in stop_words
        ]

        all_memories = list(memories)

        has_temporal = (
            temporal_range is not None
        )

        has_recall_trigger = any(
            _word_match(w, query)
            for w in recall_triggers
        ) or has_temporal

        if query_words:

            word_rarity = {}

            generic_words = {
                "gusta", "quiero", "tengo", "soy",
                "hago", "digo", "puedo", "voy",
                "fui", "era", "estoy", "hay",
            }

            models = [
                _memory_model(
                    m.get("description", "") or ""
                )
                for m in memories
            ]

            for w in query_words:

                count = sum(
                    1
                    for idx in range(len(memories))
                    if _memory_matches(
                        w, models[idx],
                    )
                )

                word_rarity[w] = count

            scored = []

            for idx, m in enumerate(memories):

                model = models[idx]

                matches = [
                    w for w in query_words
                    if _memory_matches(
                        w, model,
                    )
                ]

                match_count = len(matches)

                if match_count > 0:

                    specificity = sum(
                        (
                            0.5
                            if w in generic_words
                            else 1.0
                        )
                        / max(word_rarity[w], 1)
                        for w in matches
                    )

                    scored.append(
                        (match_count,
                         round(specificity, 4), m)
                    )

            if scored:

                def _sort_key(x):
                    match_count = x[0]
                    specificity = x[1]
                    m = x[2]
                    desc = normalize(
                        m.get("description", "")
                    )
                    tokens = desc.split()

                    def _pos(w):
                        cw = _canonical_word(w)
                        for i, t in enumerate(tokens):
                            if (
                                t == w
                                or _canonical_word(t)
                                == cw
                            ):
                                return i
                        return None

                    positions = [
                        _pos(w)
                        for w in query_words
                        if _pos(w) is not None
                    ]
                    best_pos = (
                        min(positions)
                        if positions else 0
                    )
                    max_word_len = max(
                        (
                            len(w)
                            for w in query_words
                            if _pos(w) is not None
                        ),
                        default=0,
                    )
                    return (
                        match_count,
                        specificity,
                        -best_pos,
                        max_word_len,
                        m.get("date", ""),
                        m.get("time") or "",
                    )

                scored.sort(
                    key=_sort_key,
                    reverse=True,
                )

                memories = [
                    m for _, _, m in scored
                ]

            else:

                if has_recall_trigger:

                    memories = all_memories

                else:

                    memories = []

        else:

            memories = sorted(
                memories,
                key=lambda m: (
                    m.get("date", ""),
                    m.get("time") or "",
                ),
                reverse=True,
            )

        # --------------------------------------
        # DEDUPLICAR (mismo contenido lógico:
        #  misma fecha + misma descripción)
        # --------------------------------------

        memories = deduplicate_memories(
            memories
        )

        # --------------------------------------
        # LIMITAR A 20 RESULTADOS
        # --------------------------------------

        total_available = len(memories)

        memories = memories[:20]

        if memories:

            results.append({
                "type": "memory",
                "file": "memories.json",
                "field": "memories",
                "score": 100,
                "data": memories,
                "total": total_available,
            })

    # ==========================================
    # ORDENAR RESULTADOS
    # ==========================================

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results


# ==========================================
# GUARDAR MEMORIA
# ==========================================


def save_memory(memory):

    path = ARCHIVE_PATH / "memories.json"

    try:

        data = get_memories()

    except Exception:

        data = {}

    if "memories" not in data:

        data["memories"] = []

    new_desc = normalize(
        memory.get("description", "")
        or memory.get("content", "")
    )

    new_key = (
        str(memory.get("date", "") or ""),
        new_desc,
    )

    for existing in data["memories"]:

        existing_desc = normalize(
            existing.get("description", "")
            or existing.get("content", "")
        )

        existing_key = (
            str(existing.get("date", "") or ""),
            existing_desc,
        )

        if new_desc and new_key == existing_key:

            return "duplicate"

    data["memories"].append(memory)

    try:

        with open(
            path, "w", encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return True

    except Exception as error:

        print(
            f"[DECIA ARCHIVE] "
            f"Error al guardar: {error}"
        )

        return False


def backup_corrupted_memories():

    path = ARCHIVE_PATH / "memories.json"
    backup = ARCHIVE_PATH / "memories.corrupt.backup.json"

    try:

        content = path.read_text(encoding="utf-8")

        backup.write_text(
            content, encoding="utf-8"
        )

        print(
            "[DECIA ARCHIVE] "
            "Backup corrupto guardado: "
            "memories.corrupt.backup.json"
        )

        return True

    except Exception:

        return False
