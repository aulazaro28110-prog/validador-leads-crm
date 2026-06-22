# -*- coding: utf-8 -*-
"""
Tests automáticos para validador.py (se ejecutan con: pytest -v).

Cada función que empieza por 'test_' es una prueba. Dentro usamos 'assert':
afirmamos que algo es verdad. Si lo es, el test pasa; si no, pytest avisa.
"""

from validador import (
    validar_email,
    validar_telefono,
    validar_nombre,
    detectar_duplicados,
)


# ---------------------------------------------------------------------------
# validar_email
# ---------------------------------------------------------------------------

def test_email_validos():
    """Emails con formato correcto deben aceptarse."""
    assert validar_email("ana@gmail.com")
    assert validar_email("juan.perez@empresa.es")
    assert validar_email("  luis@dominio.org  ")  # con espacios alrededor


def test_email_invalidos():
    """Emails mal formados deben rechazarse (incluye los casos raros)."""
    assert not validar_email("ana gmail.com")        # sin @
    assert not validar_email("ana@@gmail.com")        # dos @
    assert not validar_email("ana@@b@gmail.com")      # varias @
    assert not validar_email("ana@gmailcom")          # dominio sin punto
    assert not validar_email("ana @gmail.com")        # espacio en medio
    assert not validar_email("@gmail.com")            # sin usuario
    assert not validar_email("ana@")                  # sin dominio
    assert not validar_email("ana@gmail.c")           # extensión de 1 letra


# ---------------------------------------------------------------------------
# validar_telefono
# ---------------------------------------------------------------------------

def test_telefono_validos():
    """Teléfonos correctos (se normalizan antes: quitan espacios y prefijos)."""
    assert validar_telefono("612345678")              # 9 dígitos
    assert validar_telefono("+34 612 34 56 78")        # con prefijo y espacios
    assert validar_telefono("0034612345678")           # prefijo 0034
    assert validar_telefono("612-34-56-78")            # con guiones


def test_telefono_invalidos():
    """Teléfonos incorrectos deben rechazarse."""
    assert not validar_telefono("61234")               # demasiado corto
    assert not validar_telefono("6123456ABC")          # con letras
    assert not validar_telefono("")                    # vacío
    assert not validar_telefono("1234567890123456")    # demasiado largo (16)


# ---------------------------------------------------------------------------
# validar_nombre
# ---------------------------------------------------------------------------

def test_nombre_validos():
    """Nombres con al menos nombre + apellido, con tildes, ñ, guiones, apóstrofos."""
    assert validar_nombre("Ana García")
    assert validar_nombre("José-María Núñez")
    assert validar_nombre("O'Connor Smith")
    assert validar_nombre("María José Peña")


def test_nombre_invalidos():
    """Nombres incompletos o con caracteres no permitidos deben rechazarse."""
    assert not validar_nombre("Ana")                   # una sola palabra
    assert not validar_nombre("")                      # vacío
    assert not validar_nombre("Ana García3")           # con número
    assert not validar_nombre("Ana_García")            # con guion bajo


# ---------------------------------------------------------------------------
# detectar_duplicados
# ---------------------------------------------------------------------------

def test_duplicado_sucio():
    """Detecta un duplicado 'sucio': mismo contacto con mayúsculas y prefijo +34.

    La clave de comparación normaliza email (minúsculas) y teléfono (sin +34),
    así que estos dos contactos son la MISMA persona aunque se vean distintos.
    """
    contactos = [
        {"nombre": "Ana García", "email": "ana@gmail.com",
         "telefono": "612345678", "empresa": "TechCorp"},
        {"nombre": "ANA GARCIA", "email": "ANA@GMAIL.COM",
         "telefono": "+34 612 345 678", "empresa": "TechCorp"},
    ]
    duplicados = detectar_duplicados(contactos)
    assert len(duplicados) == 1                        # el segundo es el repetido


def test_sin_duplicados():
    """Dos personas distintas no deben marcarse como duplicado."""
    contactos = [
        {"nombre": "Ana García", "email": "ana@gmail.com",
         "telefono": "612345678", "empresa": "TechCorp"},
        {"nombre": "Luis Pérez", "email": "luis@gmail.com",
         "telefono": "699888777", "empresa": "DataSoft"},
    ]
    assert detectar_duplicados(contactos) == []
