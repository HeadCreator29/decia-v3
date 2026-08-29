import sys, os
sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

import pytest
from utils.speech_corrections import correct_transcription
from brain.intent_layer import IntentLayer
from brain.core import think

il = IntentLayer()


# =========================================================
# A) CORRECCIONES DETERMINISTAS — speech_corrections.py
# =========================================================

class TestDeterministicCorrections:
    """Verificar que speech_corrections.py corrige errores
    foneticos/ortograficos comunes de Whisper."""

    def test_kien_to_quien(self):
        result = correct_transcription("kien")
        assert result == "quien"

    def test_kien_eres_to_quien_eres(self):
        result = correct_transcription("kien eres")
        assert result == "quien eres"

    def test_ke_to_que(self):
        result = correct_transcription("ke")
        assert result == "que"

    def test_ke_significa_to_que_significa(self):
        result = correct_transcription("ke significa")
        assert result == "que significa"

    def test_grasias_to_gracias(self):
        result = correct_transcription("grasias")
        assert result == "gracias"


# =========================================================
# B) INTEGRATION — despues de correccion, Intent correcto
# =========================================================

class TestIntegrationWithIntentLayer:
    """Verificar que el texto corregido produce el intent
    correcto en la Intent Layer."""

    def test_kien_eres_to_decia_self(self):
        corrected = correct_transcription("kien eres")
        r = il.classify(corrected)
        assert r.intent == "DECIA_SELF"

    def test_kien_tecre_to_decia_creator(self):
        corrected = correct_transcription("kien te creo")
        r = il.classify(corrected)
        assert r.intent == "DECIA_CREATOR"

    def test_ke_significa_deca_to_archive_direct(self):
        corrected = correct_transcription("ke significa deca")
        r = il.classify(corrected)
        assert r.intent == "ARCHIVE_DIRECT"

    def test_grasias_to_thanks(self):
        corrected = correct_transcription("grasias")
        r = il.classify(corrected)
        assert r.intent == "THANKS"


# =========================================================
# C) PALABRAS CORRECTAS NO DEBEN ALTERARSE
# =========================================================

class TestCorrectWordsUnchanged:
    """Verificar que palabras correctamente escritas no son
    alteradas por las correcciones."""

    def test_quien_eres_unchanged(self):
        result = correct_transcription("quien eres")
        assert result == "quien eres"

    def test_que_significa_deca_unchanged(self):
        result = correct_transcription("que significa deca")
        assert result == "que significa deca"

    def test_gracias_unchanged(self):
        result = correct_transcription("gracias")
        assert result == "gracias"

    def test_creo_unchanged(self):
        result = correct_transcription("creo")
        assert result == "creo"

    def test_deca_unchanged(self):
        result = correct_transcription("deca")
        assert result == "deca"


# =========================================================
# D) FALSOS POSITIVOS — palabras que NO deben corregirse
# =========================================================

class TestFalsePositiveProtection:
    """Verificar que palabras donde 'ke', 'kien' o 'grasias'
    aparecen dentro de una palabra valida no son alteradas."""

    def test_ketchup_not_corrupted(self):
        result = correct_transcription("ketchup")
        assert result == "ketchup"

    def test_kerguelen_not_corrupted(self):
        result = correct_transcription("islas kerguelen")
        assert result == "islas kerguelen"

    def test_kiwi_not_corrupted(self):
        result = correct_transcription("kiwi")
        assert result == "kiwi"

    def test_kleenex_not_corrupted(self):
        result = correct_transcription("kleenex")
        assert result == "kleenex"


# =========================================================
# E) PROTECCION DE INTENTS EXISTENTES
# =========================================================

class TestExistingIntentProtection:
    """Verificar que intents existentes no se afectan."""

    def test_hola_greeting(self):
        r = il.classify("hola")
        assert r.intent == "GREETING"

    def test_quien_eres_decia_self(self):
        r = il.classify("quien eres")
        assert r.intent == "DECIA_SELF"

    def test_que_significa_deca_archive_direct(self):
        r = il.classify("que significa deca")
        assert r.intent == "ARCHIVE_DIRECT"

    def test_gracias_thanks(self):
        r = il.classify("gracias")
        assert r.intent == "THANKS"

    def test_calcular_calculate(self):
        r = il.classify("2 mas 2")
        assert r.intent == "CALCULATE"

    def test_guarda_que_memory_create(self):
        r = il.classify("guarda que manana tengo clase")
        assert r.intent == "MEMORY_CREATE"

    def test_que_recuerdas_memory_search(self):
        r = il.classify("que recuerdas")
        assert r.intent == "MEMORY_SEARCH"

    def test_adios_exit(self):
        r = il.classify("adios")
        assert r.intent == "EXIT"
