import sys, os
sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

import pytest
from brain.handlers import archive_response
from brain.intent_layer import IntentLayer

il = IntentLayer()


class TestArchiveOrigin:
    """'origen de deca' must return origin description."""

    def test_cual_es_el_origen(self):
        r = archive_response("cual es el origen de deca")
        assert r is not None
        assert "década" in r or "proyecto" in r

    def test_de_donde_viene(self):
        r = archive_response("de donde viene deca")
        assert r is not None
        assert "década" in r or "proyecto" in r

    def test_origen_intent(self):
        r = il.classify("cual es el origen de deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_de_donde_viene_intent(self):
        r = il.classify("de donde viene deca")
        assert r.intent in ("ARCHIVE_DIRECT", "ARCHIVE_SEARCH", "FREE_TALK")

    def test_de_donde_viene_think(self):
        from brain.core import think
        resp = think("de donde viene deca")
        assert resp is not None
        assert "década" in resp or "proyecto" in resp


class TestArchiveExistingCases:
    """Verify existing archive cases still work."""

    def test_cuando_comenzo(self):
        r = archive_response("cuando comenzo deca")
        assert r is not None
        assert "29" in r

    def test_cuando_empezo(self):
        r = archive_response("cuando empezo deca")
        assert r is not None
        assert "29" in r

    def test_que_significa(self):
        r = archive_response("que significa deca")
        assert r is not None

    def test_valores(self):
        r = archive_response("valores de deca")
        assert r is not None

    def test_vision(self):
        r = archive_response("vision de deca")
        assert r is not None

    def test_quien_creo(self):
        r = archive_response("quien creo deca")
        assert r is not None
        assert "Idelvi" in r

    def test_que_es_deca(self):
        r = archive_response("que es deca")
        assert r is not None


class TestBoundaryDeciaVsDeca:
    """DECIA and DECA must not contaminate each other."""

    def test_que_es_deca(self):
        r = il.classify("que es deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_que_es_decia(self):
        r = il.classify("que es decia")
        assert r.intent == "DECIA_SELF"

    def test_quien_es_decia(self):
        r = il.classify("quien es decia")
        assert r.intent == "DECIA_SELF"

    def test_quien_creo_deca(self):
        r = il.classify("quien creo deca")
        assert r.intent == "ARCHIVE_DIRECT"


class TestPreferredName:
    """'como quieres que te llame' must not trigger wrong intents."""

    def test_como_quieres_que_te_llame(self):
        r = il.classify("como quieres que te llame")
        assert r.intent not in ("DECIA_CREATOR", "ARCHIVE_DIRECT")

    def test_como_te_puedo_llamar(self):
        r = il.classify("como te puedo llamar")
        assert r.intent not in ("DECIA_CREATOR", "ARCHIVE_DIRECT")
