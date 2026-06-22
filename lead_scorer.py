# -*- coding: utf-8 -*-
"""
=============================================================================
 LEAD SCORER — Prioriza leads por POTENCIAL DE VENTA (no por calidad del dato)
=============================================================================
Mientras 'validador.py' mide si el DATO está limpio, este módulo mide cuánto
PROMETE un lead como cliente y lo clasifica en una temperatura comercial:

    🔥 Caliente (70-100)  ·  🌡️ Templado (40-69)  ·  ❄️ Frío (0-39)

Combina TRES señales (modelo "fit + intent"):
  - 👔 Cargo            (0-30): ¿esta persona decide la compra?
  - 🏢 Sector/Tamaño    (0-30): ¿la empresa encaja con el cliente ideal?
  - 🎬 Actividad        (0-40): ¿ha mostrado interés? (lo que más predice venta)

Pensado para correr DESPUÉS de validador.py, sobre 'leads_limpios.csv' (u otro
CSV) que puede traer columnas extra: cargo, sector, empleados, actividad.
Si una columna falta, esa señal puntúa 0 y el resto sigue funcionando.
=============================================================================
"""

import csv
import os
import re
import sys
import unicodedata
from html import escape

# Reutilizamos el "núcleo" validador.py para saber si el lead es localizable.
# (Importar es seguro: validador solo ejecuta su main() si se lanza directamente.)
from validador import validar_email, validar_telefono, corregir_dominio_email

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# =============================================================================
# CONFIGURACIÓN — los "mandos" que ajusta el equipo comercial sin tocar el código
# =============================================================================

# Cortes de temperatura (nota mínima para cada categoría).
UMBRAL_CALIENTE = 70   # 70-100 -> llamar hoy
UMBRAL_TEMPLADO = 40   # 40-69  -> nutrir / segunda fila  ( <40 -> Frío )

# Tamaño de empresa ideal (nº de empleados) para el cliente objetivo.
TAMANO_IDEAL_MIN = 50
TAMANO_IDEAL_MAX = 500
TAMANO_ACEPTABLE_MAX = 2000  # por encima de esto, demasiado grande


# =============================================================================
# 0) UTILIDAD: normalizar texto para COMPARAR (minúsculas y sin acentos)
# =============================================================================

def normalizar_texto(texto):
    """Pasa a minúsculas y quita acentos, para comparar sin que estorben.

    'Tecnología' y 'tecnologia' deben tratarse igual al buscar palabras clave.
    unicodedata.normalize('NFKD', ...) separa la letra de su tilde; luego nos
    quedamos solo con lo que no es tilde.
    """
    texto = texto.strip().lower()
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


# =============================================================================
# 1) SEÑAL: CARGO  (0-30)  — ¿decide la compra?
# =============================================================================

# Tres niveles de autoridad. Se comprueban de mayor a menor: el primero que
# encaje manda. Usamos \b SOLO al inicio (frontera de palabra) para que el
# 'tronco' case con sus terminaciones: \bbecari cubre becario/becaria. Si
# pusiéramos \b también al final, 'becari\b' NO casaría con 'becario'.
# Siglas: palabra COMPLETA (\b...\b). Si no, 'coo' colaría dentro de 'coordinadora'
# y 'cto' dentro de otras palabras.
PATRON_CARGO_ALTO_SIGLAS = re.compile(r"\b(ceo|cto|cfo|coo|cmo|vp)\b")
# Cargos en palabra: 'tronco' + terminación (director/directora, jefe/jefa...).
# 'chief' cubre cualquier Chief X Officer; 'country/general manager' son dirección
# (un 'manager' a secas es mando intermedio y lo coge PATRON_CARGO_MEDIO).
PATRON_CARGO_ALTO = re.compile(
    r"\b(chief|founder|cofounder|fundador|propietari|dueñ|owner|"
    r"presidente|vicepresidente|director|gerente|jefe|jefa|"
    r"socio|partner|head|(?:country|general)\s+manager)"
)
PATRON_CARGO_MEDIO = re.compile(
    r"\b(responsable|manag|coordinador|supervisor|encargad|lead|team\s*lead)"
)
PATRON_CARGO_BAJO = re.compile(
    r"\b(analista|tecnic|asistente|ayudante|auxiliar|becari|junior|trainee|"
    r"intern|operari|administrativ|comercial)"
)


def puntuar_cargo(cargo):
    """0-30 según la autoridad del cargo para decidir una compra."""
    c = normalizar_texto(cargo)
    if c == "":
        return 5  # desconocido: ni alto ni cero, prudente
    if PATRON_CARGO_ALTO_SIGLAS.search(c) or PATRON_CARGO_ALTO.search(c):
        return 30
    if PATRON_CARGO_MEDIO.search(c):
        return 18
    if PATRON_CARGO_BAJO.search(c):
        return 8
    return 10  # un cargo que no reconocemos, pero existe


# =============================================================================
# 2) SEÑAL: SECTOR + TAMAÑO  (0-30)  — ¿encaja con el cliente ideal (ICP)?
# =============================================================================

# Perfil de cliente ideal (ICP). AJUSTA estas listas a tu negocio real.
SECTORES_OBJETIVO = {
    "tecnologia", "software", "saas", "fintech", "ecommerce", "e-commerce",
    "marketing", "consultoria", "telecomunicaciones", "ia", "datos",
}
# Sectores que claramente NO compran tu producto (puntúan 0).
SECTORES_DESCARTADOS = {
    "hosteleria", "restauracion", "agricultura", "estudiante", "particular",
}


def _coincide_sector(texto, conjunto):
    """True si algún término del conjunto aparece en 'texto'.

    Los términos de UNA palabra se comparan como palabra COMPLETA (así 'ia' no
    cuela dentro de 'hosteleria'); los de varias palabras, por subcadena.
    """
    palabras = set(re.findall(r"[a-z0-9]+", texto))
    for termino in conjunto:
        if " " in termino or "-" in termino:
            if termino.replace("-", "") in texto.replace("-", ""):
                return True
        elif termino in palabras:
            return True
    return False


def puntuar_sector(sector):
    """0-15: 15 si el sector es objetivo, 0 si está descartado, 5 si es neutro."""
    s = normalizar_texto(sector)
    if s == "":
        return 5
    if _coincide_sector(s, SECTORES_OBJETIVO):
        return 15
    if _coincide_sector(s, SECTORES_DESCARTADOS):
        return 0
    return 5


def _a_entero(valor):
    """Saca el PRIMER número de un campo de empleados, por sucio que venga.

    Maneja rangos ('50-200' -> 50), '100+' -> 100, '~250' -> 250, miles con
    coma/punto ('1,500' -> 1500) y texto ('300 empleados' -> 300).
    """
    texto = str(valor)
    # Primer "número" permitiendo separadores de miles (coma o punto) en medio.
    m = re.search(r"\d[\d.,]*", texto)
    if not m:
        return None
    # Quitamos comas/puntos de millares antes de convertir.
    return int(re.sub(r"[.,]", "", m.group()))


def puntuar_tamano(empleados):
    """0-15 según el nº de empleados. Ideal: pyme/mediana (50-500)."""
    n = _a_entero(empleados)
    if n is None:
        return 5            # desconocido
    if TAMANO_IDEAL_MIN <= n <= TAMANO_IDEAL_MAX:
        return 15           # tamaño ideal
    if 10 <= n < TAMANO_IDEAL_MIN or TAMANO_IDEAL_MAX < n <= TAMANO_ACEPTABLE_MAX:
        return 8            # aceptable
    return 3                # muy pequeña (<10) o muy grande (>2000)


def puntuar_sector_tamano(sector, empleados):
    """Suma de las dos sub-señales de encaje de empresa (0-30)."""
    return puntuar_sector(sector) + puntuar_tamano(empleados)


# =============================================================================
# 3) SEÑAL: ACTIVIDAD  (0-40)  — ¿ha mostrado interés? (la más predictiva)
# =============================================================================

# Niveles de intención según lo que el lead haya hecho. Se toma el MÁS fuerte
# presente (un 'rellenó formulario' pesa más que un simple 'abrió email').
PATRON_ACT_MUY_ALTA = re.compile(
    r"(formulario|demo|reunion|respondi|contacto|presupuesto|llamada)"
)
PATRON_ACT_ALTA = re.compile(r"(descarg|pricing|precios|whitepaper|webinar)")
PATRON_ACT_MEDIA = re.compile(r"(visit|web|pagina|landing)")
PATRON_ACT_BAJA = re.compile(r"(abrio|abri|clic|click|email|correo)")


def puntuar_actividad(actividad):
    """0-40 según la señal de interés más fuerte registrada."""
    a = normalizar_texto(actividad)
    if a == "":
        return 0  # sin interés conocido (frecuente: dato que aún no tienes)
    if PATRON_ACT_MUY_ALTA.search(a):
        return 40
    if PATRON_ACT_ALTA.search(a):
        return 30
    if PATRON_ACT_MEDIA.search(a):
        return 20
    if PATRON_ACT_BAJA.search(a):
        return 10
    return 5  # hay algo escrito, pero no lo reconocemos


# =============================================================================
# 4) NOTA TOTAL + TEMPERATURA
# =============================================================================

def lead_score(lead):
    """Nota 0-100 sumando las tres señales. 'lead' es un dict con las columnas."""
    return (
        puntuar_cargo(lead.get("cargo", ""))
        + puntuar_sector_tamano(lead.get("sector", ""), lead.get("empleados", ""))
        + puntuar_actividad(lead.get("actividad", ""))
    )


def clasificar_temperatura(score):
    """Traduce la nota 0-100 a temperatura comercial."""
    if score >= UMBRAL_CALIENTE:
        return "Caliente"
    if score >= UMBRAL_TEMPLADO:
        return "Templado"
    return "Frío"


def desglose_score(lead):
    """Devuelve un dict con la nota de cada señal (útil para explicar el porqué)."""
    return {
        "cargo": puntuar_cargo(lead.get("cargo", "")),
        "sector_tamano": puntuar_sector_tamano(
            lead.get("sector", ""), lead.get("empleados", "")
        ),
        "actividad": puntuar_actividad(lead.get("actividad", "")),
    }


def es_contactable(lead):
    """True si se puede llegar al lead por AL MENOS un canal (email o teléfono).

    Reutiliza los validadores del núcleo. Un lead muy caliente pero incontactable
    es una venta perdida, así que conviene avisar.
    """
    email_ok = validar_email(corregir_dominio_email(lead.get("email", "")))
    telefono_ok = validar_telefono(lead.get("telefono", ""))
    return email_ok or telefono_ok


def motivo_lead(lead):
    """Frase corta que explica POR QUÉ el lead tiene esa nota (para el comercial)."""
    d = desglose_score(lead)
    partes = []

    if d["cargo"] >= 30:
        partes.append("decisor")
    elif d["cargo"] >= 18:
        partes.append("mando intermedio")
    elif d["cargo"] <= 8 and lead.get("cargo", "").strip():
        partes.append("sin poder de decisión")

    if d["sector_tamano"] >= 24:
        partes.append("encaja con cliente ideal")
    elif d["sector_tamano"] <= 8:
        partes.append("fuera de perfil")

    # "sin actividad" solo se menciona si el lead trae algún otro dato; un lead
    # totalmente vacío debe caer en "datos insuficientes".
    tiene_otros_datos = any(
        lead.get(campo, "").strip() for campo in ("cargo", "sector", "empleados")
    )
    if d["actividad"] >= 40:
        partes.append("alta intención (demo/formulario)")
    elif d["actividad"] >= 20:
        partes.append("interés medio")
    elif d["actividad"] == 0 and tiene_otros_datos:
        partes.append("sin actividad conocida")

    if not partes:
        return "datos insuficientes"
    texto = " · ".join(partes)
    # El aviso solo tiene sentido si hay un lead real que vale la pena rescatar.
    if not es_contactable(lead):
        texto = "⚠ revisar contacto · " + texto
    return texto


# =============================================================================
# 5) PROGRAMA PRINCIPAL: lee CSV, puntúa, ordena y exporta priorizado
# =============================================================================

def cargar_leads(ruta):
    """Lee el CSV de entrada como lista de dicts (una fila = un lead)."""
    leads = []
    with open(ruta, "r", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f):
            leads.append({(k or "").strip(): (v or "") for k, v in fila.items()})
    return leads


def puntuar_todos(leads):
    """Añade 'lead_score' y 'temperatura' a cada lead y los ordena (caliente→frío)."""
    for lead in leads:
        d = desglose_score(lead)
        lead["score_cargo"] = d["cargo"]
        lead["score_sector_tamano"] = d["sector_tamano"]
        lead["score_actividad"] = d["actividad"]
        lead["lead_score"] = d["cargo"] + d["sector_tamano"] + d["actividad"]
        lead["temperatura"] = clasificar_temperatura(lead["lead_score"])
        lead["contactable"] = "Sí" if es_contactable(lead) else "No"
        lead["motivo"] = motivo_lead(lead)
    return sorted(leads, key=lambda l: l["lead_score"], reverse=True)


def exportar_priorizados(leads, ruta="leads_priorizados.csv"):
    """Guarda los leads ya puntuados y ordenados en un CSV listo para vender."""
    if not leads:
        return
    columnas = list(leads[0].keys())
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(leads)


def generar_informe_html(leads, ruta="informe_leads.html"):
    """Panel HTML con el reparto por temperatura y los leads a llamar primero."""
    conteo = {"Caliente": 0, "Templado": 0, "Frío": 0}
    for l in leads:
        conteo[l["temperatura"]] += 1
    total = len(leads)
    top = leads[:15]

    color_temp = {"Caliente": "#f87171", "Templado": "#fbbf24", "Frío": "#38bdf8"}
    filas = "".join(
        f"<tr><td><b>{l['lead_score']}</b></td>"
        f"<td style='color:{color_temp.get(l['temperatura'], '#e2e8f0')}'>"
        f"{escape(l['temperatura'])}</td>"
        f"<td>{escape(l.get('nombre', ''))}</td>"
        f"<td>{escape(l.get('cargo', ''))}</td>"
        f"<td>{escape(l.get('empresa', ''))}</td>"
        f"<td>{'✅' if l.get('contactable') == 'Sí' else '⚠️'}</td>"
        f"<td>{escape(l.get('motivo', ''))}</td></tr>"
        for l in top
    )

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Lead Scorer — Priorización de leads</title>
<style>
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:#0f172a; color:#e2e8f0;
         margin:0; padding:40px; }}
  h1 {{ color:#38bdf8; }} h2 {{ color:#94a3b8; }}
  .cards {{ display:flex; gap:20px; flex-wrap:wrap; margin:30px 0; }}
  .card {{ background:#1e293b; border-radius:14px; padding:24px 30px; min-width:150px;
           box-shadow:0 4px 14px rgba(0,0,0,.3); }}
  .card .num {{ font-size:38px; font-weight:700; }}
  .card .lbl {{ color:#94a3b8; font-size:14px; }}
  .hot {{ color:#f87171; }} .warm {{ color:#fbbf24; }} .cold {{ color:#38bdf8; }}
  table {{ width:100%; border-collapse:collapse; margin:14px 0; }}
  th,td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #334155; }}
  th {{ color:#38bdf8; }} tr:hover {{ background:#1e293b; }}
  footer {{ margin-top:40px; color:#64748b; font-size:13px; }}
</style></head><body>
  <h1>🌡️ Lead Scorer — Priorización por potencial de venta</h1>
  <p>Análisis de <b>{total}</b> leads.</p>
  <div class="cards">
    <div class="card"><div class="num hot">{conteo['Caliente']}</div>
      <div class="lbl">🔥 Calientes (70-100)</div></div>
    <div class="card"><div class="num warm">{conteo['Templado']}</div>
      <div class="lbl">🌡️ Templados (40-69)</div></div>
    <div class="card"><div class="num cold">{conteo['Frío']}</div>
      <div class="lbl">❄️ Fríos (0-39)</div></div>
    <div class="card"><div class="num">{total}</div>
      <div class="lbl">📇 Total leads</div></div>
  </div>
  <h2>📞 A quién llamar primero (top 15)</h2>
  <table>
    <tr><th>Nota</th><th>Temp.</th><th>Nombre</th><th>Cargo</th><th>Empresa</th>
        <th>Contacto</th><th>Motivo</th></tr>
    {filas}
  </table>
  <footer>Generado por lead_scorer.py — reutiliza validador.py para verificar el contacto.</footer>
</body></html>"""

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    # Permite indicar el CSV por línea de comandos; si no, usa leads_limpios.csv.
    ruta_entrada = sys.argv[1] if len(sys.argv) > 1 else "leads_limpios.csv"
    if not os.path.exists(ruta_entrada):
        print(f"❌ No encuentro '{ruta_entrada}'. Ejecuta antes validador.py "
              "o indica otro CSV con columnas cargo/sector/empleados/actividad.")
        return

    print("🚀 Lead Scorer: priorizando leads por potencial de venta...\n")
    leads = cargar_leads(ruta_entrada)
    leads = puntuar_todos(leads)
    exportar_priorizados(leads)
    generar_informe_html(leads)

    # Conteo por temperatura.
    conteo = {"Caliente": 0, "Templado": 0, "Frío": 0}
    for l in leads:
        conteo[l["temperatura"]] += 1

    total = len(leads)
    print("=" * 60)
    print("🌡️  CLASIFICACIÓN POR TEMPERATURA")
    print("=" * 60)
    print(f"🔥 Calientes (70-100): {conteo['Caliente']}")
    print(f"🌡️  Templados (40-69):  {conteo['Templado']}")
    print(f"❄️  Fríos (0-39):       {conteo['Frío']}")
    print(f"📇 Total leads:        {total}")

    # Agenda accionable: a quién llamar primero (ya vienen ordenados).
    print("\n" + "=" * 60)
    print("📞 A QUIÉN LLAMAR HOY (top 5)")
    print("=" * 60)
    for l in leads[:5]:
        nombre = l.get("nombre", "(sin nombre)")
        print(f"  {l['lead_score']:>3} · {l['temperatura']:<8} · {nombre}")
        print(f"        {l['motivo']}")

    # Aviso: leads calientes que no se pueden contactar (oportunidad en riesgo).
    calientes_rotos = [
        l for l in leads
        if l["temperatura"] == "Caliente" and l["contactable"] == "No"
    ]
    if calientes_rotos:
        print("\n⚠ ATENCIÓN: " + str(len(calientes_rotos)) +
              " lead(s) CALIENTE(S) con contacto inválido (revisar email/teléfono):")
        for l in calientes_rotos:
            print(f"   - {l.get('nombre', '(sin nombre)')} "
                  f"({l.get('email', '')} / {l.get('telefono', '')})")

    print("\n" + "=" * 60)
    print("💾 Guardado: leads_priorizados.csv (ordenado de más a menos prometedor)")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# QUÉ HACE: Toma leads ya limpios y los puntúa por su POTENCIAL DE VENTA usando
#           cargo + sector/tamaño + actividad, y los clasifica en Caliente/
#           Templado/Frío para que el comercial sepa a quién llamar primero.
# PARA QUIÉN: Equipos comerciales que reciben más leads de los que pueden atender
#             y necesitan priorizar dónde invertir su tiempo.
# -----------------------------------------------------------------------------
