# -*- coding: utf-8 -*-
"""
Campo de pruebas EXTRA con casos límite muy difíciles, pensados para bases de
leads REALES (nombres europeos, erratas típicas de email, bordes de teléfono).
Se lanza con: pytest test_dificil.py -v
No sustituye a test_validador.py; es para estresar los validadores.
"""

from validador import validar_email, validar_telefono, validar_nombre, detectar_duplicados


# ---------------------------------------------------------------------------
# EMAIL — formatos reales que SÍ deben pasar
# ---------------------------------------------------------------------------

def test_email_validos_reales():
    assert validar_email("ana.maria.perez@correo.empresa.co.uk")  # subdominios
    assert validar_email("a@b.io")                                 # mínimo
    assert validar_email("TECNICO@Empresa.ES")                     # mayúsculas
    assert validar_email("jose_luis@mail.com")                     # guion bajo
    assert validar_email("j.o-c@sub.dominio.org")                  # puntos y guion
    assert validar_email("firma+etiqueta@gmail.com")              # +etiqueta (Gmail)
    assert validar_email("  rodeado@espacios.com  ")               # espacios alrededor


# ---------------------------------------------------------------------------
# EMAIL — erratas típicas de un CSV real que NO deben pasar
# ---------------------------------------------------------------------------

def test_email_invalidos_reales():
    assert not validar_email("ana..perez@gmail.com")   # punto doble en usuario
    assert not validar_email("ana.@gmail.com")          # usuario acaba en punto
    assert not validar_email(".ana@gmail.com")          # usuario empieza en punto
    assert not validar_email("ana@gmail..com")          # punto doble en dominio
    assert not validar_email("ana@gmailcom")            # dominio sin punto
    assert not validar_email("ana@gmail.c")             # extensión de 1 letra
    assert not validar_email("dos@@arrobas.com")        # dos @
    assert not validar_email("ana @gmail.com")          # espacio en medio
    assert not validar_email("ana@.com")                # dominio empieza en punto
    assert not validar_email("ana@dominio.")            # dominio acaba en punto
    assert not validar_email("")                        # vacío


# ---------------------------------------------------------------------------
# TELEFONO — bordes exactos y formatos sucios reales
# ---------------------------------------------------------------------------

def test_telefono_validos_reales():
    assert validar_telefono("612345678")           # 9 dígitos (mínimo)
    assert validar_telefono("123456789012345")     # 15 dígitos (máximo)
    assert validar_telefono("+34 (612) 34-56-78")  # paréntesis + guiones + prefijo
    assert validar_telefono("0034 612 345 678")     # prefijo 0034
    assert validar_telefono("  612-345-678  ")      # guiones y espacios alrededor


def test_telefono_invalidos_reales():
    assert not validar_telefono("12345678")          # 8 -> corto
    assert not validar_telefono("1234567890123456")  # 16 -> largo
    assert not validar_telefono("+34 600 11 22 3")   # 8 tras quitar +34
    assert not validar_telefono("6123456AB")         # con letras
    assert not validar_telefono("+34")               # solo prefijo
    assert not validar_telefono("")                  # vacío


# ---------------------------------------------------------------------------
# NOMBRE — nombres europeos REALES (acentos de varios idiomas)
# ---------------------------------------------------------------------------

def test_nombre_validos_europeos():
    assert validar_nombre("Anne-Marie Lefèvre")        # francés: è
    assert validar_nombre("Jürgen Müller")             # alemán: ü
    assert validar_nombre("Joan Domènech")             # catalán: è
    assert validar_nombre("Joao Gonçalves")            # portugués: ç
    assert validar_nombre("Renée Gauthier")            # francés: é doble
    assert validar_nombre("José María de la Peña")     # 5 palabras, tildes, ñ
    assert validar_nombre("O'Brien-Smith Núñez")       # apóstrofo + guion juntos
    assert validar_nombre("Bjørn Sørensen")            # noruego: ø


def test_nombre_invalidos_reales():
    assert not validar_nombre("Ana")            # una sola palabra
    assert not validar_nombre("Ana García3")    # con número
    assert not validar_nombre("Ana_García")     # guion bajo
    assert not validar_nombre("Ana García!")    # símbolo
    assert not validar_nombre("123 456")        # solo números
    assert not validar_nombre("")               # vacío


# ---------------------------------------------------------------------------
# DUPLICADOS — el mismo lead disfrazado al extremo
# ---------------------------------------------------------------------------

def test_duplicado_disfraz_extremo():
    """3 entradas que son la MISMA persona con disfraces distintos -> 2 duplicados."""
    contactos = [
        {"nombre": "José Núñez", "email": "jose.nunez@gmail.com",
         "telefono": "612345678", "empresa": "TechCorp"},
        {"nombre": "JOSÉ NÚÑEZ", "email": "  JOSE.NUNEZ@Gmail.Com  ",
         "telefono": "+34 (612) 34-56-78", "empresa": "TechCorp"},
        {"nombre": "jose nuñez", "email": "Jose.Nunez@GMAIL.COM",
         "telefono": "0034-612-345-678", "empresa": "Tech Corp"},
    ]
    assert len(detectar_duplicados(contactos)) == 2  # el 1º es único; 2 repetidos


def test_duplicado_erratas_dominio():
    """Mismo lead con errata de dominio (gmail.con) debe contar como duplicado.

    La clave de comparación corrige el dominio antes, así 'gmail.con' y 'gmail.com'
    se ven iguales.
    """
    contactos = [
        {"nombre": "Ana García", "email": "ana@gmail.com",
         "telefono": "611223344", "empresa": "DataSoft"},
        {"nombre": "Ana García", "email": "ana@gmail.con",  # errata típica
         "telefono": "611223344", "empresa": "DataSoft"},
    ]
    assert len(detectar_duplicados(contactos)) == 1


def test_personas_distintas_no_duplican():
    """Dos personas reales distintas NO deben marcarse como duplicado."""
    contactos = [
        {"nombre": "Ana García", "email": "ana@gmail.com",
         "telefono": "611223344", "empresa": "DataSoft"},
        {"nombre": "Luis Pérez", "email": "luis@outlook.com",
         "telefono": "699887766", "empresa": "RedBricks"},
    ]
    assert detectar_duplicados(contactos) == []
