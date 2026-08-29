import re

from datetime import (
    datetime,
    timedelta,
)


MONTH_NAMES = {
    "01": "enero",
    "02": "febrero",
    "03": "marzo",
    "04": "abril",
    "05": "mayo",
    "06": "junio",
    "07": "julio",
    "08": "agosto",
    "09": "septiembre",
    "10": "octubre",
    "11": "noviembre",
    "12": "diciembre",
}


WEEKDAY_NAMES = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6,
}

# Written numbers for temporal expressions
_WRITTEN_NUMBERS = {
    "un": 1, "uno": 1, "una": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
}


def _parse_number_token(token):
    """Parse a number token (digit or written) to int."""
    if token.isdigit():
        return int(token)
    return _WRITTEN_NUMBERS.get(token, 0)


def get_month_name(month_number):

    return MONTH_NAMES.get(
        str(month_number), str(month_number)
    )


def format_date_spanish(date_str):

    if not date_str or len(date_str) < 10:

        return date_str

    day = date_str[8:10]
    month = get_month_name(date_str[5:7])
    year = date_str[:4]

    return f"{day} de {month} de {year}"


def parse_relative_date(text, now=None):

    if now is None:

        now = datetime.now().astimezone()

    text_lower = text.lower()

    # ------------------------------------------
    # ANTEAYER
    # ------------------------------------------

    if "anteayer" in text_lower:

        return (
            now - timedelta(days=2)
        ).date()

    # ------------------------------------------
    # AYER
    # ------------------------------------------

    if "ayer" in text_lower:

        return (
            now - timedelta(days=1)
        ).date()

    # ------------------------------------------
    # HACE X DÍAS
    # ------------------------------------------

    match = re.search(
        r"hace\s+(?:una?|(\d+))\s+dias?",
        text_lower,
    )

    if match:

        days = int(match.group(1) or 1)

        return (
            now - timedelta(days=days)
        ).date()

    # ------------------------------------------
    # HACE X SEMANAS
    # ------------------------------------------

    match = re.search(
        r"hace\s+(?:una?|(\d+))\s+semanas?",
        text_lower,
    )

    if match:

        weeks = int(match.group(1) or 1)

        return (
            now - timedelta(weeks=weeks)
        ).date()

    # ------------------------------------------
    # HACE X MESES (aproximado)
    # ------------------------------------------

    match = re.search(
        r"hace\s+(?:una?|(\d+))\s+mes(es)?",
        text_lower,
    )

    if match:

        months = int(match.group(1) or 1)

        return (
            now - timedelta(days=months * 30)
        ).date()

    # ------------------------------------------
    # DÍA DE LA SEMANA
    # ------------------------------------------

    for day_name, day_num in (
        WEEKDAY_NAMES.items()
    ):

        pattern = rf"\bel\s+{day_name}\b"

        if re.search(pattern, text_lower):

            today_weekday = now.weekday()

            days_back = (
                today_weekday - day_num
            ) % 7

            if days_back == 0:

                days_back = 7

            return (
                now - timedelta(days=days_back)
            ).date()

    # ------------------------------------------
    # HOY (por defecto)
    # ------------------------------------------

    return now.date()


def parse_relative_time(text, now=None):

    if now is None:

        now = datetime.now().astimezone()

    text_lower = text.lower()

    match = re.search(
        r"\ba\s+las\s+"
        r"(\d{1,2})"
        r"(?::(\d{2}))?"
        r"\s*"
        r"(de\s+la\s+ma[n\u00f1]ana|de\s+la"
        r"\s+tarde|de\s+la\s+noche|am|pm)?",
        text_lower,
    )

    if not match:

        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3)

    # F1 (9.7.1): aceptar "mañana" y "manana".
    # El periodo capturado es un token fijo de
    # la familia horaria; plegar aqui la ñ no
    # altera el resto del texto ni la semantica.
    if period is not None:

        period = period.replace("\u00f1", "n")

    if period in [
        "de la tarde",
        "de la noche",
        "pm",
    ]:

        if hour < 12:

            hour += 12

    elif period == "de la manana":

        if hour == 12:

            hour = 0

    elif period == "am":

        if hour == 12:

            hour = 0

    if not period:

        if hour >= 1 and hour <= 7:

            hour += 12

    return f"{hour:02d}:{minute:02d}"


def parse_memory_datetime(
    content, now=None
):

    if now is None:

        now = datetime.now().astimezone()

    event_date = parse_relative_date(
        content, now
    )

    event_time = parse_relative_time(
        content, now
    )

    return {
        "date": event_date.strftime("%Y-%m-%d"),
        "time": event_time,
    }


# ==========================================
# PLANNER (9.6) — MARCADORES DE FECHA FUTURA
# ==========================================
#
# Expresión regular de los marcadores que una
# frase debe contener para registrar un
# evento/recordatorio futuro o consultarlo.
# Solo detecta futuro: "manana", "pasado
# manana", "en N dias", "dentro de N
# semanas", dia de la semana siguiente
# ("el lunes"/"lunes"/"este lunes", NUNCA
# "el lunes pasado") y fechas absolutas.
# GUARDAS: "la manana"/"esta manana" (detras
# de "la"/"esta") y "lunes pasado"
# (delante de "pasado") NO son marcadores.
# ==========================================


_PLANNER_WEEKDAYS = "|".join(
    WEEKDAY_NAMES.keys()
)

# Written numbers pattern for regex
_WRITTEN_NUM_PATTERN = "|".join(_WRITTEN_NUMBERS.keys())

_PLACER_WEEKDAYS = "|".join(
    WEEKDAY_NAMES.keys()
)

PLANNER_DATE_MARKERS = (
    "(?:"
    "pasado\\s+ma[n\\u00f1]ana\\b|"
    "(?<!\\bla\\s)(?<!\\besta\\s)"
    "ma[n\\u00f1]ana\\b|"
    "en\\s+(?:un\\b|\\d+|" + _WRITTEN_NUM_PATTERN + ")\\s+dias?\\b|"
    "en\\s+(?:una\\b|\\d+|" + _WRITTEN_NUM_PATTERN + ")\\s+semanas?\\b|"
    "dentro\\s+de\\s+(?:una\\b|\\d+|" + _WRITTEN_NUM_PATTERN + ")\\s+"
    "semanas?\\b|"
    "la\\s+semana\\s+que\\s+viene\\b|"
    "(?:este\\s+|el\\s+)?(?:"
    + _PLACER_WEEKDAYS
    + ")\\b(?!\\s+pasad[oa]s?\\b)|"
    "\\d{4}[-/]?\\d{1,2}[-/]?\\d{1,2}"
    ")"
)


def plan_relative_datetime(text, now=None):
    # PHASE 9.6: devuelve la FECHA FUTURA que
    # expresa texto (solo marcadores de plan),
    # o None si no hay ninguno. El dia de la
    # semana SOLO es futuro si no va seguido
    # de "pasado/a" ("el lunes pasado" no
    # califica). Dia desnudo -> próxima
    # ocurrencia estrictamente posterior.

    if now is None:

        now = datetime.now().astimezone()

    text_lower = text.lower()

    # --------------------------------------
    # PASADO MAÑANA
    # --------------------------------------

    if re.search(
        r"\bpasado\s+ma[n\u00f1]ana\b",
        text_lower,
    ):

        return (now + timedelta(days=2)).date()

    # --------------------------------------
    # MAÑANA (guardas "la manana"/"esta manana")
    # --------------------------------------

    if re.search(
        r"(?<!\bla\s)(?<!\besta\s)"
        r"\bma[n\u00f1]ana\b",
        text_lower,
    ):

        return (now + timedelta(days=1)).date()

    # --------------------------------------
    # EN UN/N DÍAS
    # F6 (9.7.3): tambien "en un dia" (+1).
    # "en 0 dias" es invalido/ambiguo para
    # CREAR un plan -> None: el handler pide
    # aclaracion de forma determinista
    # (0 OLLAMA).
    # --------------------------------------

    match = re.search(
        r"\ben\s+(un|\d+|" + _WRITTEN_NUM_PATTERN + r")\s+dias?\b",
        text_lower,
    )

    if match:

        days = _parse_number_token(match.group(1))

        if days <= 0:

            return None

        return (
            now + timedelta(days=days)
        ).date()

    # --------------------------------------
    # EN UNA/N SEMANA(S)
    # F6 (9.7.3): "en una semana" (+7).
    # Misma politica: "en 0 semanas" -> None.
    # --------------------------------------

    match = re.search(
        r"\ben\s+(una|\d+|" + _WRITTEN_NUM_PATTERN + r")\s+semanas?\b",
        text_lower,
    )

    if match:

        weeks = _parse_number_token(match.group(1))

        if weeks <= 0:

            return None

        return (
            now + timedelta(weeks=weeks)
        ).date()

    # --------------------------------------
    # DENTRO DE UNA/N SEMANA(S)
    # --------------------------------------

    match = re.search(
        r"\bdentro\s+de\s+(una|\d+|" + _WRITTEN_NUM_PATTERN + r")\s+"
        r"semanas?\b",
        text_lower,
    )

    if match:

        weeks = _parse_number_token(match.group(1))

        return (
            now + timedelta(weeks=weeks)
        ).date()

    # --------------------------------------
    # LA SEMANA QUE VIENE
    # --------------------------------------

    if re.search(
        r"\bla\s+semana\s+que\s+viene\b",
        text_lower,
    ):

        return (
            now + timedelta(weeks=1)
        ).date()

    # --------------------------------------
    # FECHA ABSOLUTA (YYYY-MM-DD)
    # F2 (9.7.1): evaluada ANTES del dia de la
    # semana. Cuando hay fecha explícita, esa
    # fecha SIEMPRE gana aunque el weekday la
    # contradiga ("2026-08-30 lunes" -> 30).
    # No se valida coherencia datetime-weekday.
    # --------------------------------------

    match = re.search(
        r"(\d{4})[-/]?(\d{1,2})[-/]?"
        r"(\d{1,2})",
        text_lower,
    )

    if match:

        try:

            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            ).date()

        except ValueError:

            return None

    # --------------------------------------
    # DÍA DE LA SEMANA SIGUIENTE
    # ("el lunes" / "lunes" / "este lunes";
    #  nunca uno pasado)
    # --------------------------------------

    for day_name, day_num in (
        WEEKDAY_NAMES.items()
    ):

        pattern = (
            rf"(?:este\s+|el\s+)?"
            rf"{day_name}\b"
            rf"(?!\s+pasad[oa]s?\b)"
        )

        if re.search(pattern, text_lower):

            days_ahead = (
                day_num - now.weekday()
            ) % 7

            if days_ahead == 0:

                days_ahead = 7

            return (
                now + timedelta(days=days_ahead)
            ).date()

    return None
