# -*- coding: utf-8 -*-
"""
=============================================================================
 REPARTO DE LEADS EN EQUIPO — divide los leads priorizados entre comerciales
=============================================================================
Tercera fase del pipeline (validador -> lead_scorer -> REPARTO -> crm).
Pensado para el ritmo semanal de un equipo de ventas:

    🟢 LUNES: repartir los leads de la semana de forma justa.
    🔴 VIERNES: balance — qué trabajó cada uno y qué calientes quedaron sin tocar.

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

# Reutilizamos el normalizador del núcleo para cruzar leads por email igual que
# lo hace el CRM (mismo criterio: minúsculas y sin espacios).
from validador import normalizar_email

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
# 3) BALANCE DEL VIERNES — cruza el reparto con el seguimiento del CRM
# =============================================================================

def _trabajado(lead_crm):
    """True si el lead se contactó al menos una vez (tiene fecha de último contacto)."""
    return bool(lead_crm and (lead_crm.get("ultimo_contacto") or "").strip())


def balance_semanal(reparto, crm):
    """Por comercial: asignados, trabajados, cerrados y calientes SIN tocar.

    'reparto' = filas con 'comercial', 'email' y 'temperatura'.
    'crm'     = filas de seguimiento.csv con 'email', 'estado', 'ultimo_contacto'.
    Se cruzan por email normalizado (mismo criterio que el CRM).
    """
    indice_crm = {normalizar_email(c.get("email", "")): c for c in crm}
    stats = {}
    for lead in reparto:
        comercial = lead.get("comercial", "(sin asignar)")
        if comercial == "(sin asignar)":
            continue
        s = stats.setdefault(comercial, {
            "asignados": 0, "trabajados": 0, "cerrados": 0, "calientes_sin_tocar": 0,
        })
        s["asignados"] += 1
        lead_crm = indice_crm.get(normalizar_email(lead.get("email", "")))
        trabajado = _trabajado(lead_crm)
        if trabajado:
            s["trabajados"] += 1
        if lead_crm and (lead_crm.get("estado") or "") == "cerrado":
            s["cerrados"] += 1
        if lead.get("temperatura") == "Caliente" and not trabajado:
            s["calientes_sin_tocar"] += 1
    return stats


def generar_informe_balance_html(stats, ruta="informe_balance.html"):
    """Panel del viernes: rendimiento de cada comercial en la semana."""
    from html import escape
    filas = ""
    for comercial in sorted(stats):
        s = stats[comercial]
        pct = round(s["trabajados"] / s["asignados"] * 100) if s["asignados"] else 0
        alerta = "⚠️" if s["calientes_sin_tocar"] else "✅"
        filas += (
            f"<tr><td>{escape(comercial)}</td>"
            f"<td>{s['asignados']}</td>"
            f"<td>{s['trabajados']} ({pct}%)</td>"
            f"<td class='ok'>{s['cerrados']}</td>"
            f"<td class='warn'>{alerta} {s['calientes_sin_tocar']}</td></tr>"
        )
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Balance semanal del equipo</title>
<style>
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:#0f172a; color:#e2e8f0;
         margin:0; padding:40px; }}
  h1 {{ color:#38bdf8; }} p {{ color:#94a3b8; }}
  table {{ width:100%; border-collapse:collapse; margin:18px 0; background:#1e293b;
           border-radius:10px; overflow:hidden; }}
  th,td {{ text-align:left; padding:11px 14px; border-bottom:1px solid #334155; }}
  th {{ color:#38bdf8; text-transform:uppercase; font-size:13px; }}
  .ok {{ color:#4ade80; }} .warn {{ color:#fbbf24; }}
  footer {{ margin-top:34px; color:#64748b; font-size:13px; }}
</style></head><body>
  <h1>📊 Balance semanal del equipo (viernes)</h1>
  <p>Qué trabajó cada comercial y qué oportunidades calientes quedaron sin tocar.</p>
  <table>
    <tr><th>Comercial</th><th>Asignados</th><th>Trabajados</th>
        <th>Cerrados</th><th>🔥 Calientes sin tocar</th></tr>
    {filas}
  </table>
  <footer>Generado por reparto.py (balance) — cruza reparto_equipo.csv con seguimiento.csv del CRM.</footer>
</body></html>"""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)


# =============================================================================
# 4) SALIDAS DEL REPARTO
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


def _leer_csv(ruta):
    """Lee un CSV como lista de dicts (tolera el BOM de Excel)."""
    with open(ruta, "r", encoding="utf-8-sig") as f:
        return [dict(fila) for fila in csv.DictReader(f)]


def main_reparto(ruta_leads, ruta_equipo):
    """🟢 LUNES: reparte los leads de la semana entre el equipo."""
    if not os.path.exists(ruta_leads):
        print(f"❌ No encuentro '{ruta_leads}'. Ejecuta antes lead_scorer.py.")
        return
    if not os.path.exists(ruta_equipo):
        print(f"❌ No encuentro '{ruta_equipo}'. Crea un CSV con columnas: nombre,capacidad")
        return

    leads = repartir(_leer_csv(ruta_leads), cargar_equipo(ruta_equipo))
    equipo = cargar_equipo(ruta_equipo)
    exportar_reparto(leads)
    exportar_por_comercial(leads, equipo)
    generar_informe_equipo_html(leads, equipo)

    res = resumen_reparto(leads, equipo)
    print("=" * 56)
    print("🗓️  REPARTO SEMANAL DEL EQUIPO (lunes)")
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


def main_balance(ruta_reparto, ruta_crm):
    """🔴 VIERNES: balance de lo que trabajó cada comercial."""
    if not os.path.exists(ruta_reparto):
        print(f"❌ No encuentro '{ruta_reparto}'. Haz antes el reparto del lunes.")
        return
    if not os.path.exists(ruta_crm):
        print(f"❌ No encuentro '{ruta_crm}'. Es la base del CRM (crm.py).")
        return

    stats = balance_semanal(_leer_csv(ruta_reparto), _leer_csv(ruta_crm))
    generar_informe_balance_html(stats)

    print("=" * 64)
    print("📊  BALANCE SEMANAL DEL EQUIPO (viernes)")
    print("=" * 64)
    for comercial in sorted(stats):
        s = stats[comercial]
        pct = round(s["trabajados"] / s["asignados"] * 100) if s["asignados"] else 0
        alerta = "⚠️ " if s["calientes_sin_tocar"] else "✅ "
        print(f"  {comercial:<14} asignados {s['asignados']:<3} · "
              f"trabajados {s['trabajados']:<3} ({pct}%) · cerrados {s['cerrados']:<3} · "
              f"{alerta}{s['calientes_sin_tocar']} calientes sin tocar")
    print("=" * 64)
    print("💾 Guardado: informe_balance.html")


def main():
    args = sys.argv[1:]
    if args and args[0] == "balance":
        ruta_reparto = args[1] if len(args) > 1 else "reparto_equipo.csv"
        ruta_crm = args[2] if len(args) > 2 else "seguimiento.csv"
        main_balance(ruta_reparto, ruta_crm)
    else:
        ruta_leads = args[0] if args else "leads_priorizados.csv"
        ruta_equipo = args[1] if len(args) > 1 else "equipo.csv"
        main_reparto(ruta_leads, ruta_equipo)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# QUÉ HACE: Reparte los leads ya priorizados entre los comerciales del equipo,
#           equilibrando calientes/templados/fríos y respetando la capacidad de
#           cada uno. Genera la lista semanal de cada comercial y un panel.
# PARA QUIÉN: Responsables de equipos de ventas que cada lunes deben repartir
#             los leads de la semana de forma justa entre su gente.
# -----------------------------------------------------------------------------
