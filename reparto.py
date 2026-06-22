# -*- coding: utf-8 -*-
"""
=============================================================================
 REPARTO DE LEADS EN EQUIPO — divide los leads priorizados entre comerciales
=============================================================================
Tercera fase del pipeline (validador -> lead_scorer -> REPARTO -> crm).
Pensado para el ritmo semanal de un equipo de ventas:

    🟢 LUNES: repartir los leads de la semana de forma justa.
    🔴 VIERNES: revisar qué trabajó cada uno (fase 2, futura).

Criterio de reparto (lo que importa de verdad en un equipo generalista):
  1) EQUILIBRIO POR TEMPERATURA: que nadie acapare los leads calientes.
  2) CARGA EQUITATIVA: todos con un nº parecido de leads (según su capacidad).
La "especialidad por sector" se deja fuera a propósito: en la mayoría de equipos
los comerciales son generalistas y añadiría complejidad que no se usa.
=============================================================================
"""

import csv
import os
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# Orden en que se reparten los leads: primero los calientes (los más valiosos).
ORDEN_TEMP = {"Caliente": 0, "Templado": 1, "Frío": 2}
TEMPERATURAS = ("Caliente", "Templado", "Frío")
SIN_CAPACIDAD = 10_000  # capacidad "infinita" si no se indica una


# =============================================================================
# 1) EQUIPO
# =============================================================================

def cargar_equipo(ruta):
    """Lee 'equipo.csv' (columnas: nombre, capacidad) como lista de comerciales."""
    equipo = []
    with open(ruta, "r", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f):
            nombre = (fila.get("nombre") or "").strip()
            if not nombre:
                continue
            bruto = fila.get("capacidad") or ""
            digitos = re.sub(r"[^\d]", "", bruto)
            equipo.append({
                "nombre": nombre,
                "capacidad": int(digitos) if digitos else SIN_CAPACIDAD,
            })
    return equipo


# =============================================================================
# 2) REPARTO (núcleo)
# =============================================================================

def _estado_inicial(equipo):
    """Contadores por comercial: cuántos lleva de cada temperatura y en total."""
    return {
        c["nombre"]: {"temp": {t: 0 for t in TEMPERATURAS}, "total": 0}
        for c in equipo
    }


def mejor_comercial(temperatura, equipo, estado):
    """Elige el comercial para un lead de esa temperatura, o None si nadie tiene hueco.

    Regla: menos leads de ESA temperatura (equilibrio); empate -> menos leads totales.
    """
    candidatos = [c for c in equipo if estado[c["nombre"]]["total"] < c["capacidad"]]
    if not candidatos:
        return None

    def clave(c):
        e = estado[c["nombre"]]
        return (e["temp"][temperatura], e["total"])

    return min(candidatos, key=clave)


def repartir(leads, equipo):
    """Asigna a cada lead un 'comercial' equilibrando temperatura y carga.

    Devuelve la lista de leads (con la clave 'comercial' añadida), ordenada de
    más caliente a más frío. Lo que no cabe queda como '(sin asignar)'.
    """
    estado = _estado_inicial(equipo)
    ordenados = sorted(
        leads,
        key=lambda l: (ORDEN_TEMP.get(l.get("temperatura", "Frío"), 2),
                       -int(l.get("lead_score", 0) or 0)),
    )
    for lead in ordenados:
        temp = lead.get("temperatura", "Frío")
        elegido = mejor_comercial(temp, equipo, estado)
        if elegido is None:
            lead["comercial"] = "(sin asignar)"
        else:
            lead["comercial"] = elegido["nombre"]
            estado[elegido["nombre"]]["temp"][temp] += 1
            estado[elegido["nombre"]]["total"] += 1
    return ordenados


def resumen_reparto(leads, equipo):
    """Cuántos leads de cada temperatura ha recibido cada comercial (+ sin asignar)."""
    resumen = {c["nombre"]: {t: 0 for t in TEMPERATURAS} for c in equipo}
    resumen["(sin asignar)"] = {t: 0 for t in TEMPERATURAS}
    for lead in leads:
        quien = lead.get("comercial", "(sin asignar)")
        temp = lead.get("temperatura", "Frío")
        if quien not in resumen:
            resumen[quien] = {t: 0 for t in TEMPERATURAS}
        resumen[quien][temp] += 1
    return resumen


# =============================================================================
# 3) SALIDAS (se completan en el siguiente paso)
# =============================================================================

def _slug(nombre):
    """Convierte 'Ana García' en 'ana_garcia' para usarlo en un nombre de archivo."""
    t = unicodedata.normalize("NFKD", nombre.strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "comercial"


def exportar_por_comercial(leads, equipo):
    """Genera un CSV por comercial (su lista de la semana) ordenado por nota."""
    rutas = []
    for c in equipo:
        suyos = [l for l in leads if l.get("comercial") == c["nombre"]]
        suyos.sort(key=lambda l: -int(l.get("lead_score", 0) or 0))
        ruta = f"leads_{_slug(c['nombre'])}.csv"
        if suyos:
            columnas = list(suyos[0].keys())
            with open(ruta, "w", encoding="utf-8", newline="") as f:
                escritor = csv.DictWriter(f, fieldnames=columnas)
                escritor.writeheader()
                escritor.writerows(suyos)
            rutas.append(ruta)
    return rutas


def exportar_reparto(leads, ruta="reparto_equipo.csv"):
    """Guarda todos los leads con su columna 'comercial' en un único CSV."""
    if not leads:
        return
    columnas = list(leads[0].keys())
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(leads)


def generar_informe_equipo_html(leads, equipo, ruta="informe_equipo.html"):
    """Panel del lunes: cuántos leads (y de qué temperatura) lleva cada comercial."""
    from html import escape
    res = resumen_reparto(leads, equipo)
    orden = [c["nombre"] for c in equipo] + ["(sin asignar)"]
    filas = ""
    for nombre in orden:
        r = res.get(nombre, {t: 0 for t in TEMPERATURAS})
        total = sum(r.values())
        if total == 0 and nombre == "(sin asignar)":
            continue
        filas += (
            f"<tr><td>{escape(nombre)}</td>"
            f"<td class='hot'>{r['Caliente']}</td>"
            f"<td class='warm'>{r['Templado']}</td>"
            f"<td class='cold'>{r['Frío']}</td>"
            f"<td><b>{total}</b></td></tr>"
        )
    total_leads = len(leads)
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Reparto semanal del equipo</title>
<style>
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:#0f172a; color:#e2e8f0;
         margin:0; padding:40px; }}
  h1 {{ color:#38bdf8; }} p {{ color:#94a3b8; }}
  table {{ width:100%; border-collapse:collapse; margin:18px 0; background:#1e293b;
           border-radius:10px; overflow:hidden; }}
  th,td {{ text-align:left; padding:11px 14px; border-bottom:1px solid #334155; }}
  th {{ color:#38bdf8; text-transform:uppercase; font-size:13px; }}
  tr:hover {{ background:#243044; }}
  .hot {{ color:#f87171; }} .warm {{ color:#fbbf24; }} .cold {{ color:#38bdf8; }}
  footer {{ margin-top:34px; color:#64748b; font-size:13px; }}
</style></head><body>
  <h1>🗓️ Reparto semanal del equipo</h1>
  <p>{total_leads} leads repartidos entre {len(equipo)} comerciales (equilibrado por temperatura).</p>
  <table>
    <tr><th>Comercial</th><th>🔥 Calientes</th><th>🌡️ Templados</th>
        <th>❄️ Fríos</th><th>Total</th></tr>
    {filas}
  </table>
  <footer>Generado por reparto.py — fase 3 del pipeline (validador → lead_scorer → reparto).</footer>
</body></html>"""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    ruta_leads = sys.argv[1] if len(sys.argv) > 1 else "leads_priorizados.csv"
    ruta_equipo = sys.argv[2] if len(sys.argv) > 2 else "equipo.csv"

    if not os.path.exists(ruta_leads):
        print(f"❌ No encuentro '{ruta_leads}'. Ejecuta antes lead_scorer.py.")
        return
    if not os.path.exists(ruta_equipo):
        print(f"❌ No encuentro '{ruta_equipo}'. Crea un CSV con columnas: nombre,capacidad")
        return

    with open(ruta_leads, "r", encoding="utf-8-sig") as f:
        leads = [dict(fila) for fila in csv.DictReader(f)]
    equipo = cargar_equipo(ruta_equipo)

    leads = repartir(leads, equipo)
    exportar_reparto(leads)
    exportar_por_comercial(leads, equipo)
    generar_informe_equipo_html(leads, equipo)

    res = resumen_reparto(leads, equipo)
    print("=" * 56)
    print("🗓️  REPARTO SEMANAL DEL EQUIPO")
    print("=" * 56)
    for c in equipo:
        r = res[c["nombre"]]
        total = sum(r.values())
        print(f"  {c['nombre']:<14} 🔥{r['Caliente']:<3} 🌡️{r['Templado']:<3} "
              f"❄️{r['Frío']:<3} → {total} leads")
    sin = sum(res["(sin asignar)"].values())
    if sin:
        print(f"  {'(sin asignar)':<14} → {sin} leads (sin capacidad)")
    print("=" * 56)
    print("💾 Guardado: reparto_equipo.csv, leads_<comercial>.csv e informe_equipo.html")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# QUÉ HACE: Reparte los leads ya priorizados entre los comerciales del equipo,
#           equilibrando calientes/templados/fríos y respetando la capacidad de
#           cada uno. Genera la lista semanal de cada comercial y un panel.
# PARA QUIÉN: Responsables de equipos de ventas que cada lunes deben repartir
#             los leads de la semana de forma justa entre su gente.
# -----------------------------------------------------------------------------
