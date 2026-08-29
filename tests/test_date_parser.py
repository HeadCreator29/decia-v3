import sys

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from utils.date_parser import (
    get_month_name,
    format_date_spanish,
    parse_relative_date,
    parse_relative_time,
    parse_memory_datetime,
)


FIXED_NOW = datetime(
    2026, 8, 26, 15, 30, 0,
    tzinfo=timezone.utc,
)


# ==========================================
# get_month_name
# ==========================================


def test_month_january():

    assert get_month_name("01") == "enero"


def test_month_august():

    assert get_month_name("08") == "agosto"


def test_month_december():

    assert get_month_name("12") == "diciembre"


def test_month_unknown():

    assert get_month_name("13") == "13"


# ==========================================
# format_date_spanish
# ==========================================


def test_format_date():

    result = format_date_spanish("2025-08-29")

    assert result == "29 de agosto de 2025"


def test_format_date_short():

    result = format_date_spanish("2026-01-01")

    assert result == "01 de enero de 2026"


def test_format_date_none():

    assert format_date_spanish(None) is None


def test_format_date_too_short():

    assert format_date_spanish("2026") == "2026"


# ==========================================
# parse_relative_date
# ==========================================


def test_ayer():

    result = parse_relative_date(
        "ayer", FIXED_NOW
    )

    expected = (
        FIXED_NOW - timedelta(days=1)
    ).date()

    assert result == expected


def test_anteayer():

    result = parse_relative_date(
        "anteayer", FIXED_NOW
    )

    expected = (
        FIXED_NOW - timedelta(days=2)
    ).date()

    assert result == expected


def test_hace_3_dias():

    result = parse_relative_date(
        "hace 3 dias", FIXED_NOW
    )

    expected = (
        FIXED_NOW - timedelta(days=3)
    ).date()

    assert result == expected


def test_hace_2_semanas():

    result = parse_relative_date(
        "hace 2 semanas", FIXED_NOW
    )

    expected = (
        FIXED_NOW - timedelta(weeks=2)
    ).date()

    assert result == expected


def test_hace_1_mes():

    result = parse_relative_date(
        "hace 1 mes", FIXED_NOW
    )

    expected = (
        FIXED_NOW - timedelta(days=30)
    ).date()

    assert result == expected


def test_el_lunes():

    result = parse_relative_date(
        "el lunes", FIXED_NOW
    )

    days_back = (
        FIXED_NOW.weekday() - 0
    ) % 7

    if days_back == 0:

        days_back = 7

    expected = (
        FIXED_NOW - timedelta(days=days_back)
    ).date()

    assert result == expected


def test_hoy_por_defecto():

    result = parse_relative_date(
        "algo random", FIXED_NOW
    )

    assert result == FIXED_NOW.date()


# ==========================================
# parse_relative_time
# ==========================================


def test_time_tarde():

    result = parse_relative_time(
        "a las 3 de la tarde"
    )

    assert result == "15:00"


def test_time_manana():

    result = parse_relative_time(
        "a las 9 de la manana"
    )

    assert result == "09:00"


def test_time_noche():

    result = parse_relative_time(
        "a las 10 de la noche"
    )

    assert result == "22:00"


def test_time_am():

    result = parse_relative_time(
        "a las 7 am"
    )

    assert result == "07:00"


def test_time_pm():

    result = parse_relative_time(
        "a las 2 pm"
    )

    assert result == "14:00"


def test_time_with_minutes():

    result = parse_relative_time(
        "a las 3:30 de la tarde"
    )

    assert result == "15:30"


def test_time_no_period():

    result = parse_relative_time(
        "a las 5"
    )

    assert result == "17:00"


def test_time_no_match():

    result = parse_relative_time(
        "hola mundo"
    )

    assert result is None


# ==========================================
# parse_memory_datetime
# ==========================================


def test_memory_datetime_full():

    result = parse_memory_datetime(
        "ayer a las 3 de la tarde me vi",
        FIXED_NOW,
    )

    expected_date = (
        FIXED_NOW - timedelta(days=1)
    ).date().strftime("%Y-%m-%d")

    assert result["date"] == expected_date
    assert result["time"] == "15:00"


def test_memory_datetime_date_only():

    result = parse_memory_datetime(
        "hoy fue genial",
        FIXED_NOW,
    )

    assert result["date"] == (
        FIXED_NOW.date().strftime("%Y-%m-%d")
    )

    assert result["time"] is None


def test_memory_datetime_time_only():

    result = parse_memory_datetime(
        "a las 8 pm",
        FIXED_NOW,
    )

    assert result["time"] == "20:00"
