# -*- coding: utf-8 -*-
"""
Tests del Lead Scorer (pytest -v).
Comprueban cada señal por separado, la nota total, la temperatura y el orden.
"""

from lead_scorer import (
    puntuar_cargo,
    puntuar_sector,
    puntuar_tamano,
    puntuar_actividad,
    lead_score,
    clasificar_temperatura,
    puntuar_todos,
    desglose_score,
    motivo_lead,
    es_contactable,
    generar_informe_html,
)


# ---------------------------------------------------------------------------
# CARGO (0-30)
# ---------------------------------------------------------------------------

def test_cargo_alto():
    assert puntuar_cargo("CEO") == 30
    assert puntuar_cargo("Directora de Compras") == 30
    assert puntuar_cargo("Gerente") == 30
    assert puntuar_cargo("Founder & Owner") == 30


def test_cargo_medio():
    assert puntuar_cargo("Responsable de Marketing") == 18
    assert puntuar_cargo("Project Manager") == 18
    assert puntuar_cargo("Coordinadora de Ventas") == 18


def test_cargo_bajo():
    assert puntuar_cargo("Analista junior") == 8
    assert puntuar_cargo("Becario") == 8
    assert puntuar_cargo("Asistente administrativo") == 8


def test_cargo_desconocido_o_vacio():
    assert puntuar_cargo("") == 5
    assert puntuar_cargo("   ") == 5
    assert puntuar_cargo("Astronauta") == 10  # existe pero no lo clasificamos


def test_cargo_reales_ingles_y_compuestos():
    """Títulos reales en inglés y compuestos típicos de un CRM."""
    # Decisores (alto, 30):
    assert puntuar_cargo("VP of Sales") == 30
    assert puntuar_cargo("Head of Marketing") == 30
    assert puntuar_cargo("Chief Revenue Officer") == 30
    assert puntuar_cargo("Sales Director") == 30
    assert puntuar_cargo("Country Manager") == 30       # dirige un país: decisor
    assert puntuar_cargo("General Manager") == 30
    # Mandos intermedios (medio, 18): 'manager' genérico
    assert puntuar_cargo("Marketing Manager") == 18
    assert puntuar_cargo("Team Lead") == 18


# ---------------------------------------------------------------------------
# SECTOR + TAMAÑO (0-30)
# ---------------------------------------------------------------------------

def test_sector():
    assert puntuar_sector("Tecnología") == 15        # objetivo (con tilde)
    assert puntuar_sector("software") == 15
    assert puntuar_sector("Hostelería") == 0          # descartado
    assert puntuar_sector("") == 5                     # desconocido
    assert puntuar_sector("Banca") == 5                # neutro


def test_tamano():
    assert puntuar_tamano("250") == 15                 # ideal (50-500)
    assert puntuar_tamano("1.500") == 8                # grande aceptable
    assert puntuar_tamano("30") == 8                   # pequeña aceptable
    assert puntuar_tamano("5") == 3                    # micro
    assert puntuar_tamano("9000") == 3                 # gigante
    assert puntuar_tamano("N/A") == 5                  # desconocido


def test_tamano_formatos_sucios():
    """Datos reales de empresa: rangos, '+', separadores de miles, texto."""
    assert puntuar_tamano("50-200") == 15      # rango -> toma el primero (50)
    assert puntuar_tamano("100+") == 15        # '100 o más' -> 100
    assert puntuar_tamano("~250") == 15        # aproximado
    assert puntuar_tamano("1,500") == 8        # miles con coma -> 1500
    assert puntuar_tamano("300 empleados") == 15  # número con texto detrás
    assert puntuar_tamano("De 50 a 200") == 15    # rango en texto


# ---------------------------------------------------------------------------
# ACTIVIDAD (0-40)
# ---------------------------------------------------------------------------

def test_actividad():
    assert puntuar_actividad("Rellenó formulario de demo") == 40
    assert puntuar_actividad("Descargó whitepaper") == 30
    assert puntuar_actividad("Visitó la web 3 veces") == 20
    assert puntuar_actividad("Abrió email") == 10
    assert puntuar_actividad("") == 0                  # sin actividad conocida


def test_actividad_toma_la_senal_mas_fuerte():
    # Si hay varias acciones, vale la de mayor intención (formulario > email).
    assert puntuar_actividad("Abrió email y luego rellenó formulario") == 40


# ---------------------------------------------------------------------------
# NOTA TOTAL Y TEMPERATURA
# ---------------------------------------------------------------------------

def test_lead_score_completo():
    lead_top = {"cargo": "CEO", "sector": "SaaS",
                "empleados": "200", "actividad": "pidió demo"}
    # 30 (cargo) + 15+15 (sector+tamaño) + 40 (actividad) = 100
    assert lead_score(lead_top) == 100


def test_lead_score_con_columnas_faltantes():
    # Si solo viene el cargo, las demás señales puntúan 0 (o su valor por defecto).
    lead = {"cargo": "Director"}
    # 30 (cargo) + (5 sector vacío + 5 tamaño vacío) + 0 (actividad) = 40
    assert lead_score(lead) == 40


def test_clasificar_temperatura_cortes():
    # Bordes exactos de cada categoría.
    assert clasificar_temperatura(100) == "Caliente"
    assert clasificar_temperatura(70) == "Caliente"
    assert clasificar_temperatura(69) == "Templado"
    assert clasificar_temperatura(40) == "Templado"
    assert clasificar_temperatura(39) == "Frío"
    assert clasificar_temperatura(0) == "Frío"


# ---------------------------------------------------------------------------
# ORDEN: los más prometedores arriba
# ---------------------------------------------------------------------------

def test_desglose_suma_igual_que_score():
    """El desglose por señales debe sumar exactamente la nota total."""
    lead = {"cargo": "Responsable", "sector": "Banca",
            "empleados": "300", "actividad": "visitó web"}
    d = desglose_score(lead)
    assert d["cargo"] + d["sector_tamano"] + d["actividad"] == lead_score(lead)


# ---------------------------------------------------------------------------
# MOTIVO (explicación legible)
# ---------------------------------------------------------------------------

def test_motivo_lead_caliente():
    lead = {"cargo": "CEO", "sector": "SaaS",
            "empleados": "200", "actividad": "pidió demo"}
    motivo = motivo_lead(lead)
    assert "decisor" in motivo
    assert "encaja con cliente ideal" in motivo
    assert "alta intención" in motivo


def test_motivo_lead_frio():
    lead = {"cargo": "Becario", "sector": "Hostelería",
            "empleados": "4", "actividad": ""}
    motivo = motivo_lead(lead)
    assert "sin poder de decisión" in motivo
    assert "fuera de perfil" in motivo
    assert "sin actividad conocida" in motivo


def test_motivo_datos_insuficientes():
    # Lead totalmente vacío: no hay nada que destacar.
    assert motivo_lead({}) == "datos insuficientes"


# ---------------------------------------------------------------------------
# CONTACTABLE (reutiliza el validador)
# ---------------------------------------------------------------------------

def test_contactable_email_valido():
    assert es_contactable({"email": "ana@gmail.com", "telefono": "no-vale"})


def test_contactable_solo_telefono():
    assert es_contactable({"email": "roto@@mal", "telefono": "+34 612 345 678"})


def test_no_contactable():
    assert not es_contactable({"email": "roto@@mal", "telefono": "123"})


def test_motivo_avisa_si_no_contactable():
    """Un lead caliente pero incontactable debe llevar el aviso por delante."""
    lead = {"cargo": "CEO", "sector": "SaaS", "empleados": "200",
            "actividad": "pidió demo", "email": "roto@@mal", "telefono": "123"}
    assert motivo_lead(lead).startswith("⚠ revisar contacto")


def test_puntuar_todos_lista_vacia():
    """Un CSV sin filas no debe romper nada."""
    assert puntuar_todos([]) == []


def test_puntuar_todos_sin_columnas_esperadas():
    """Filas con solo 'nombre' (sin cargo/sector/...) deben puntuarse sin error."""
    leads = [{"nombre": "Solo Nombre"}, {"nombre": "Otro Mas"}]
    ordenados = puntuar_todos(leads)
    assert len(ordenados) == 2
    for l in ordenados:
        assert "lead_score" in l and "temperatura" in l and "motivo" in l
        assert 0 <= l["lead_score"] <= 100


def test_genera_informe_html(tmp_path):
    """El panel HTML se crea y contiene el reparto y un lead esperado."""
    leads = puntuar_todos([
        {"nombre": "Ana García", "cargo": "CEO", "sector": "SaaS",
         "empleados": "200", "actividad": "pidió demo",
         "email": "ana@gmail.com", "telefono": "612345678"},
    ])
    ruta = tmp_path / "informe_leads.html"
    generar_informe_html(leads, ruta=str(ruta))
    contenido = ruta.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in contenido
    assert "Ana García" in contenido
    assert "Calientes" in contenido


def test_puntuar_todos_ordena_caliente_primero():
    leads = [
        {"nombre": "Frío", "cargo": "Becario", "sector": "Hostelería",
         "empleados": "3", "actividad": ""},
        {"nombre": "Caliente", "cargo": "CEO", "sector": "Tecnología",
         "empleados": "150", "actividad": "pidió demo"},
        {"nombre": "Templado", "cargo": "Responsable", "sector": "Banca",
         "empleados": "300", "actividad": "visitó web"},
    ]
    ordenados = puntuar_todos(leads)
    # Deben quedar de mayor a menor puntuación.
    assert [l["nombre"] for l in ordenados] == ["Caliente", "Templado", "Frío"]
    assert ordenados[0]["temperatura"] == "Caliente"
    assert ordenados[-1]["temperatura"] == "Frío"
