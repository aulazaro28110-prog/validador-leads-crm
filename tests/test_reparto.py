# -*- coding: utf-8 -*-
"""
Tests del reparto de leads en equipo (pytest -v).
Comprueban el equilibrio por temperatura, el respeto de capacidad y la equidad.
"""

from reparto import (
    cargar_equipo,
    mejor_comercial,
    repartir,
    resumen_reparto,
    _estado_inicial,
    exportar_por_comercial,
    generar_informe_equipo_html,
    balance_semanal,
    generar_informe_balance_html,
)


def _leads(temperaturas):
    """Crea leads de prueba a partir de una lista de temperaturas."""
    return [
        {"nombre": f"Lead{i}", "temperatura": t, "lead_score": 100 - i}
        for i, t in enumerate(temperaturas)
    ]


def _equipo(*pares):
    """Crea un equipo a partir de pares (nombre, capacidad)."""
    return [{"nombre": n, "capacidad": cap} for n, cap in pares]


# ---------------------------------------------------------------------------
# EQUILIBRIO POR TEMPERATURA
# ---------------------------------------------------------------------------

def test_reparto_equilibra_calientes():
    """4 calientes y 2 comerciales -> 2 calientes cada uno."""
    leads = _leads(["Caliente"] * 4)
    equipo = _equipo(("Ana", 100), ("Luis", 100))
    repartidos = repartir(leads, equipo)
    res = resumen_reparto(repartidos, equipo)
    assert res["Ana"]["Caliente"] == 2
    assert res["Luis"]["Caliente"] == 2


def test_reparto_equilibra_cada_temperatura():
    """Mezcla de temperaturas: cada comercial recibe mitad de cada tipo."""
    leads = _leads(["Caliente", "Caliente", "Templado", "Templado",
                    "Frío", "Frío"])
    equipo = _equipo(("Ana", 100), ("Luis", 100))
    res = resumen_reparto(repartir(leads, equipo), equipo)
    for t in ("Caliente", "Templado", "Frío"):
        assert res["Ana"][t] == 1
        assert res["Luis"][t] == 1


# ---------------------------------------------------------------------------
# CAPACIDAD
# ---------------------------------------------------------------------------

def test_reparto_respeta_capacidad():
    """Si la capacidad total no llega, sobran leads como '(sin asignar)'."""
    leads = _leads(["Caliente", "Caliente", "Caliente"])
    equipo = _equipo(("Ana", 1), ("Luis", 1))
    repartidos = repartir(leads, equipo)
    sin_asignar = [l for l in repartidos if l["comercial"] == "(sin asignar)"]
    assert len(sin_asignar) == 1
    assert sum(1 for l in repartidos if l["comercial"] in ("Ana", "Luis")) == 2


def test_capacidad_distinta_reparte_proporcional():
    """Con capacidades 1 y 3, el de más capacidad recibe más."""
    leads = _leads(["Templado"] * 4)
    equipo = _equipo(("Ana", 1), ("Luis", 3))
    res = resumen_reparto(repartir(leads, equipo), equipo)
    assert res["Ana"]["Templado"] == 1
    assert res["Luis"]["Templado"] == 3


# ---------------------------------------------------------------------------
# EQUIDAD / CASOS LÍMITE
# ---------------------------------------------------------------------------

def test_reparto_equitativo_impar():
    """5 leads entre 2 comerciales -> 3 y 2 (no se pierde ninguno)."""
    leads = _leads(["Caliente"] * 5)
    equipo = _equipo(("Ana", 100), ("Luis", 100))
    repartidos = repartir(leads, equipo)
    totales = sorted(
        sum(1 for l in repartidos if l["comercial"] == n) for n in ("Ana", "Luis")
    )
    assert totales == [2, 3]


def test_sin_equipo_todo_sin_asignar():
    """Sin comerciales, todos los leads quedan sin asignar (no peta)."""
    leads = _leads(["Caliente", "Frío"])
    repartidos = repartir(leads, [])
    assert all(l["comercial"] == "(sin asignar)" for l in repartidos)


def test_mejor_comercial_sin_hueco_devuelve_none():
    equipo = _equipo(("Ana", 1))
    estado = _estado_inicial(equipo)
    estado["Ana"]["total"] = 1  # ya llena
    assert mejor_comercial("Caliente", equipo, estado) is None


def test_exporta_un_csv_por_comercial(tmp_path, monkeypatch):
    """Cada comercial con leads debe tener su archivo leads_<nombre>.csv."""
    monkeypatch.chdir(tmp_path)
    equipo = _equipo(("Ana García", 100), ("Luis", 100))
    leads = repartir(_leads(["Caliente"] * 4), equipo)
    rutas = exportar_por_comercial(leads, equipo)
    assert (tmp_path / "leads_ana_garcia.csv").exists()
    assert (tmp_path / "leads_luis.csv").exists()
    assert len(rutas) == 2


def test_genera_informe_equipo_html(tmp_path):
    equipo = _equipo(("Ana", 100), ("Luis", 100))
    leads = repartir(_leads(["Caliente", "Templado", "Frío"]), equipo)
    ruta = tmp_path / "informe_equipo.html"
    generar_informe_equipo_html(leads, equipo, ruta=str(ruta))
    html = ruta.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "Ana" in html and "Luis" in html


# ---------------------------------------------------------------------------
# BALANCE DEL VIERNES (cruce con el CRM)
# ---------------------------------------------------------------------------

def test_balance_cuenta_trabajados_y_cerrados():
    reparto = [
        {"email": "a@x.com", "comercial": "Ana", "temperatura": "Caliente"},
        {"email": "b@x.com", "comercial": "Ana", "temperatura": "Templado"},
        {"email": "c@x.com", "comercial": "Luis", "temperatura": "Frío"},
    ]
    crm = [
        {"email": "a@x.com", "estado": "cerrado", "ultimo_contacto": "2026-06-22"},
        {"email": "b@x.com", "estado": "seguimiento", "ultimo_contacto": "2026-06-22"},
        # c@x.com no aparece en el CRM -> no trabajado
    ]
    stats = balance_semanal(reparto, crm)
    assert stats["Ana"]["asignados"] == 2
    assert stats["Ana"]["trabajados"] == 2
    assert stats["Ana"]["cerrados"] == 1
    assert stats["Luis"]["asignados"] == 1
    assert stats["Luis"]["trabajados"] == 0


def test_balance_detecta_calientes_sin_tocar():
    """Un caliente asignado pero no contactado debe aparecer como sin tocar."""
    reparto = [
        {"email": "hot@x.com", "comercial": "Ana", "temperatura": "Caliente"},
        {"email": "hot2@x.com", "comercial": "Ana", "temperatura": "Caliente"},
    ]
    crm = [
        {"email": "hot@x.com", "estado": "seguimiento", "ultimo_contacto": "2026-06-22"},
        {"email": "hot2@x.com", "estado": "nuevo", "ultimo_contacto": ""},  # sin tocar
    ]
    stats = balance_semanal(reparto, crm)
    assert stats["Ana"]["calientes_sin_tocar"] == 1


def test_balance_cruza_email_normalizado():
    """El cruce ignora mayúsculas/espacios en el email (igual que el CRM)."""
    reparto = [{"email": "Ana@X.COM ", "comercial": "Ana", "temperatura": "Templado"}]
    crm = [{"email": "ana@x.com", "estado": "seguimiento", "ultimo_contacto": "2026-06-22"}]
    stats = balance_semanal(reparto, crm)
    assert stats["Ana"]["trabajados"] == 1


def test_balance_ignora_sin_asignar():
    reparto = [{"email": "a@x.com", "comercial": "(sin asignar)", "temperatura": "Caliente"}]
    stats = balance_semanal(reparto, [])
    assert "(sin asignar)" not in stats


def test_genera_informe_balance_html(tmp_path):
    stats = {"Ana": {"asignados": 5, "trabajados": 4, "cerrados": 1,
                     "calientes_sin_tocar": 1}}
    ruta = tmp_path / "informe_balance.html"
    generar_informe_balance_html(stats, ruta=str(ruta))
    html = ruta.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "Ana" in html


def test_cargar_equipo(tmp_path):
    """Lee equipo.csv y convierte la capacidad a número."""
    csv_equipo = tmp_path / "equipo.csv"
    csv_equipo.write_text(
        "nombre,capacidad\nAna,40\nLuis,35\nSofía,\n", encoding="utf-8"
    )
    equipo = cargar_equipo(str(csv_equipo))
    assert len(equipo) == 3
    assert equipo[0] == {"nombre": "Ana", "capacidad": 40}
    assert equipo[2]["nombre"] == "Sofía"        # capacidad vacía -> "infinita"
    assert equipo[2]["capacidad"] >= 10000
