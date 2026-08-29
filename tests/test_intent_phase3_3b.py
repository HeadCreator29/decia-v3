import sys, os
sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

import pytest
from brain.intent_layer import IntentLayer
from brain.handlers import identity_response, archive_response
from brain.core import think
from personality.personality import NAME, ROLE

il = IntentLayer()


# =========================================================
# A) DECIA SELF - Intent classification
# =========================================================

class TestDeciaSelfIntent:
    """DECIA identity questions must classify as DECIA_SELF."""

    def test_que_es_decia(self):
        r = il.classify("que es decia")
        assert r.intent == "DECIA_SELF"

    def test_hablame_de_decia(self):
        r = il.classify("hablame de decia")
        assert r.intent == "DECIA_SELF"

    def test_hablame_sobre_decia(self):
        r = il.classify("hablame sobre decia")
        assert r.intent == "DECIA_SELF"

    def test_que_significa_decia(self):
        r = il.classify("que significa decia")
        assert r.intent == "DECIA_SELF"

    def test_quien_es_decia(self):
        r = il.classify("quien es decia")
        assert r.intent == "DECIA_SELF"


# =========================================================
# B) DECIA SELF - Handler response
# =========================================================

class TestDeciaSelfHandler:
    """DECIA identity questions must return DECIA identity info."""

    def test_que_es_decia_response(self):
        r = il.classify("que es decia")
        assert r.intent == "DECIA_SELF"
        resp = identity_response("que es decia")
        assert resp is not None
        assert "DECIA" in resp

    def test_hablame_de_decia_response(self):
        r = il.classify("hablame de decia")
        assert r.intent == "DECIA_SELF"
        resp = identity_response("hablame de decia")
        assert resp is not None
        assert "DECIA" in resp

    def test_que_significa_decia_response(self):
        r = il.classify("que significa decia")
        assert r.intent == "DECIA_SELF"
        resp = identity_response("que significa decia")
        assert resp is not None
        assert "DECIA" in resp

    def test_quien_es_decia_response(self):
        r = il.classify("quien es decia")
        assert r.intent == "DECIA_SELF"
        resp = identity_response("quien es decia")
        assert resp is not None
        assert "DECIA" in resp


# =========================================================
# C) DECA ARCHIVE - Must NOT change
# =========================================================

class TestDecaArchiveUnchanged:
    """DECA archive questions must still classify as ARCHIVE_DIRECT."""

    def test_que_es_deca(self):
        r = il.classify("que es deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_que_significa_deca(self):
        r = il.classify("que significa deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_hablame_de_deca(self):
        r = il.classify("hablame de deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_quien_creo_deca(self):
        r = il.classify("quien creo deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_origen_de_deca(self):
        r = il.classify("cual es el origen de deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_que_es_deca_response(self):
        resp = archive_response("que es deca")
        assert resp is not None
        assert "DECA" in resp

    def test_que_significa_deca_response(self):
        resp = archive_response("que significa deca")
        assert resp is not None
        assert "DECA" in resp


# =========================================================
# D) NO CROSS-CONTAMINATION
# =========================================================

class TestNoCrossContamination:
    """DECIA must not return DECA info and vice versa."""

    def test_que_es_decia_not_deca(self):
        resp = identity_response("que es decia")
        if resp:
            assert "década" not in resp.lower()
            assert "legado" not in resp.lower()

    def test_que_es_deca_not_decia(self):
        resp = archive_response("que es deca")
        assert resp is not None
        assert "DECA" in resp

    def test_que_significa_decia_not_deca_meaning(self):
        resp = identity_response("que significa decia")
        if resp:
            assert "década" not in resp.lower()


# =========================================================
# E) EXISTING INTENTS - Regression protection
# =========================================================

class TestExistingIntents:
    """Verify existing DECIA/DECA patterns still work."""

    def test_quien_eres(self):
        r = il.classify("quien eres")
        assert r.intent == "DECIA_SELF"
        resp = identity_response("quien eres")
        assert resp is not None
        assert "DECIA" in resp

    def test_quien_te_creo(self):
        r = il.classify("quien te creo")
        assert r.intent == "DECIA_CREATOR"
        resp = identity_response("quien te creo")
        assert resp is not None
        assert "Idelvi" in resp

    def test_que_es_deca_archive(self):
        r = il.classify("que es deca")
        assert r.intent == "ARCHIVE_DIRECT"
        resp = archive_response("que es deca")
        assert resp is not None

    def test_hola_greeting(self):
        r = il.classify("hola")
        assert r.intent == "GREETING"

    def test_gracias_thanks(self):
        r = il.classify("gracias")
        assert r.intent == "THANKS"

    def test_adios_exit(self):
        r = il.classify("adios")
        assert r.intent == "EXIT"

    def test_guarda_que_memory_create(self):
        r = il.classify("guarda que manana tengo clase")
        assert r.intent == "MEMORY_CREATE"

    def test_que_recuerdas_memory_search(self):
        r = il.classify("que recuerdas")
        assert r.intent == "MEMORY_SEARCH"

    def test_dos_mas_dos_calculate(self):
        r = il.classify("2 mas 2")
        assert r.intent == "CALCULATE"
