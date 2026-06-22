# -*- coding: utf-8 -*-
"""
=============================================================================
 VALIDADOR Y ENRIQUECEDOR DE LEADS COMERCIALES
=============================================================================
Lee 'contactos.csv', limpia y normaliza los datos, valida emails y teléfonos,
corrige erratas típicas, detecta duplicados (aunque estén "sucios"), puntúa la
calidad de cada lead (0-100) y genera varios informes:

  - validos.txt / invalidos.txt / duplicados.txt   (detalle por categoría)
  - leads_limpios.csv                              (base lista para el CRM)
  - informe.html                                   (panel visual de resultados)

Pensado para departamentos comerciales: convierte una lista de contactos
"sucia" en una base de datos limpia, priorizada y lista para vender.
=============================================================================
"""

import csv
import sys
import os
import re
import hashlib
from html import escape

# En Windows la consola usa cp1252 y no puede mostrar emojis.
# Forzamos la salida a UTF-8 para que los prints con emojis se vean bien.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# =============================================================================
# 1) NORMALIZACIÓN  (solo para COMPARAR; el dato original nunca se altera)
# =============================================================================

def normalizar_email(email):
    """Email en minúsculas y sin espacios en los extremos. Solo para comparar."""
    return email.strip().lower()


def normalizar_telefono(telefono):
    """Deja el teléfono solo con dígitos relevantes (quita adornos y prefijo +34)."""
    t = telefono.strip()
    t = t.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if t.startswith("+34"):
        t = t[3:]
    elif t.startswith("0034"):
        t = t[4:]
    return t


def clave_contacto(contacto):
    """Clave única (email + teléfono NORMALIZADOS) que identifica a la persona."""
    return (
        normalizar_email(corregir_dominio_email(contacto["email"])),
        normalizar_telefono(contacto["telefono"]),
    )


# =============================================================================
# 2) VALIDACIÓN
# =============================================================================

# Patrón de un email válido: usuario@dominio.ext.
#   usuario  -> [^@\s.]+(?:\.[^@\s.]+)*  : trozos sin puntos, unidos por UN punto
#               (prohíbe ana..perez, .ana o ana.)
#   dominio  -> (?:[^@\s.]+\.)+           : uno o más "etiqueta." (sub.dominio.)
#   tld      -> [^@\s.]{2,}               : extensión final de 2+ caracteres
# Así caen los puntos dobles (gmail..com) y los dominios sin punto.
PATRON_EMAIL = re.compile(
    r"^[^@\s.]+(?:\.[^@\s.]+)*@(?:[^@\s.]+\.)+[^@\s.]{2,}$"
)


def validar_email(email):
    """True si el email tiene formato válido (una @, dominio con punto, TLD>=2)."""
    return PATRON_EMAIL.match(email.strip()) is not None


# Patrón de un teléfono ya normalizado: solo dígitos, longitud de 9 a 15.
PATRON_TELEFONO = re.compile(r"^\d{9,15}$")


def validar_telefono(telefono):
    """True si, una vez normalizado, son solo dígitos y mide entre 9 y 15."""
    t = normalizar_telefono(telefono)
    return PATRON_TELEFONO.match(t) is not None


def validar_empresa(empresa):
    """True si el campo empresa no está vacío."""
    return empresa.strip() != ""


# Una palabra de un nombre: letras (de cualquier idioma), pudiendo unir bloques con
# guion o apóstrofo (José-María, O'Connor, Lefèvre, Müller, Gonçalves).
#   [^\W\d_] = "carácter de palabra que NO sea dígito ni guion bajo" = cualquier
#   LETRA Unicode (incluye á, è, ñ, ü, ö, ç...). Más robusto que listar tildes a mano.
PATRON_PALABRA_NOMBRE = re.compile(r"^[^\W\d_]+(?:[-'][^\W\d_]+)*$")


def validar_nombre(nombre):
    """True si hay al menos nombre y apellido, formados por letras.

    Se permiten guiones y apóstrofos dentro de una palabra para aceptar nombres
    como 'José-María' u 'O'Connor'.
    """
    partes = nombre.strip().split()
    if len(partes) < 2:
        return False
    return all(PATRON_PALABRA_NOMBRE.match(parte) for parte in partes)


# =============================================================================
# 3) LIMPIEZA Y CORRECCIÓN  (mejora el dato para la base final)
# =============================================================================

# Erratas de dominio más frecuentes al teclear un correo.
ERRATAS_DOMINIO = {
    "gmail.con": "gmail.com",
    "gmail.co": "gmail.com",
    "gmial.com": "gmail.com",
    "gmai.com": "gmail.com",
    "hotmial.com": "hotmail.com",
    "hotmai.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "outlok.com": "outlook.com",
    "outloo.com": "outlook.com",
    "yaho.com": "yahoo.com",
    "yahooo.com": "yahoo.com",
}


def corregir_dominio_email(email):
    """Corrige erratas típicas del dominio. Si no hay errata, lo deja igual."""
    email = email.strip()
    if "@" not in email:
        return email
    usuario, dominio = email.rsplit("@", 1)
    dominio_corregido = ERRATAS_DOMINIO.get(dominio.lower(), dominio)
    return f"{usuario}@{dominio_corregido}"


def formatear_telefono(telefono):
    """Deja el móvil con formato presentable: '+34 612 34 56 78'."""
    t = normalizar_telefono(telefono)
    if len(t) == 9 and t.isdigit():
        return f"+34 {t[0:3]} {t[3:5]} {t[5:7]} {t[7:9]}"
    return telefono.strip()


def extraer_dominio(email):
    """Devuelve el dominio del email (lo que va tras la @) en minúsculas."""
    email = email.strip().lower()
    if "@" in email:
        return email.rsplit("@", 1)[1]
    return ""


# Dominios de correo temporal / desechable (señal de lead poco fiable).
DOMINIOS_DESECHABLES = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "throwaway.email", "yopmail.com", "trashmail.com", "getnada.com",
}


def es_email_desechable(email):
    """True si el dominio del email es de los típicos 'usar y tirar'."""
    return extraer_dominio(email) in DOMINIOS_DESECHABLES


# =============================================================================
# 4) PUNTUACIÓN DE CALIDAD DEL LEAD
# =============================================================================

def puntuar_lead(contacto):
    """Da una nota 0-100 según lo completo y fiable que es el lead.

    Email válido: 40 · Teléfono válido: 30 · Empresa: 20 · Nombre completo: 10.
    Un email desechable resta 30 puntos (no llegará nunca el correo comercial).
    """
    puntos = 0
    if validar_email(corregir_dominio_email(contacto["email"])):
        puntos += 40
    if validar_telefono(contacto["telefono"]):
        puntos += 30
    if validar_empresa(contacto["empresa"]):
        puntos += 20
    if validar_nombre(contacto["nombre"]):
        puntos += 10
    if es_email_desechable(contacto["email"]):
        puntos -= 30
    # Nos aseguramos de no devolver una nota negativa.
    return max(0, puntos)


def clasificar_lead(puntuacion):
    """Convierte la nota numérica en una categoría comercial."""
    if puntuacion >= 90:
        return "A (Oro)"
    if puntuacion >= 70:
        return "B (Bueno)"
    if puntuacion >= 40:
        return "C (Mejorable)"
    return "D (Descartar)"


# =============================================================================
# 5) DUPLICADOS
# =============================================================================

def detectar_duplicados(lista_contactos):
    """Devuelve los CONTACTOS duplicados, conservando su dato ORIGINAL.

    Compara con la clave normalizada (email + teléfono), así caen también los
    casi-duplicados (mayúsculas, espacios, prefijo +34...), no solo los exactos.
    El primero de cada persona se considera único; las repeticiones se devuelven.
    """
    # 'vistos' es un set: comprobar 'clave in vistos' es instantáneo (O(1)),
    # así el total es O(n). Con una lista sería O(n²) y se arrastraría con miles.
    vistos = set()
    duplicados = []
    for contacto in lista_contactos:
        clave = clave_contacto(contacto)
        if clave in vistos:
            duplicados.append(contacto)
        else:
            vistos.add(clave)
    return duplicados


# =============================================================================
# 6) ESTADÍSTICAS
# =============================================================================

def estadisticas_por_empresa(contactos, top=5):
    """Devuelve las 'top' empresas con más leads, como lista de (empresa, nº)."""
    conteo = {}
    for c in contactos:
        empresa = c["empresa"].strip() or "(sin empresa)"
        conteo[empresa] = conteo.get(empresa, 0) + 1
    return sorted(conteo.items(), key=lambda par: par[1], reverse=True)[:top]


def estadisticas_por_dominio(contactos, top=5):
    """Devuelve los 'top' dominios de email más frecuentes, como (dominio, nº)."""
    conteo = {}
    for c in contactos:
        dominio = extraer_dominio(c["email"]) or "(sin dominio)"
        conteo[dominio] = conteo.get(dominio, 0) + 1
    return sorted(conteo.items(), key=lambda par: par[1], reverse=True)[:top]


# =============================================================================
# 7) INFORMES Y EXPORTACIÓN
# =============================================================================

def generar_informe(validos, invalidos, duplicados):
    """Imprime en consola el resumen final con conteos y porcentaje."""
    print("\n" + "=" * 50)
    print("📊 INFORME FINAL DE VALIDACIÓN")
    print("=" * 50)
    print(f"✅ Contactos válidos:     {len(validos)}")
    print(f"❌ Contactos inválidos:   {len(invalidos)}")
    print(f"🔁 Contactos duplicados:  {len(duplicados)}")
    if duplicados:
        # 'duplicados' es una lista de contactos; sacamos nombres únicos de ejemplo.
        nombres = []
        for c in duplicados:
            if c["nombre"] not in nombres:
                nombres.append(c["nombre"])
        muestra = ", ".join(nombres[:5])
        extra = "..." if len(nombres) > 5 else ""
        print(f"   👉 Ejemplos duplicados: {muestra}{extra}")
    total = len(validos) + len(invalidos) + len(duplicados)
    print(f"📇 Total procesados:      {total}")
    if total > 0:
        porcentaje = round(len(duplicados) / total * 100, 1)
    else:
        porcentaje = 0
    print(f"🧹 % duplicados eliminados: {porcentaje}%")
    print("=" * 50)


def exportar_csv_limpio(validos, ruta="leads_limpios.csv"):
    """Genera un CSV depurado y enriquecido, listo para importar al CRM."""
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(
            ["nombre", "email", "telefono", "empresa", "dominio",
             "puntuacion", "categoria"]
        )
        for c in validos:
            email_corregido = corregir_dominio_email(c["email"])
            escritor.writerow([
                c["nombre"].strip(),
                email_corregido,
                formatear_telefono(c["telefono"]),
                c["empresa"].strip(),
                extraer_dominio(email_corregido),
                c["puntuacion"],
                c["categoria"],
            ])


def separar_nombre(nombre):
    """Parte 'Ana García' en (FirstName, LastName) que es lo que pide Salesforce.

    LastName es obligatorio en Salesforce; si solo hay una palabra la usamos como
    apellido para no dejar vacío el campo requerido.
    """
    partes = nombre.strip().split()
    if len(partes) == 0:
        return ("", "")
    if len(partes) == 1:
        return ("", partes[0])
    return (partes[0], " ".join(partes[1:]))


def telefono_e164(telefono):
    """Formato internacional sin espacios '+34612345678' (ideal para CRM/CTI)."""
    t = normalizar_telefono(telefono)
    if len(t) == 9 and t.isdigit():
        return "+34" + t
    return telefono.strip()


def rating_salesforce(puntuacion):
    """Traduce la nota 0-100 al picklist estándar de Salesforce (Hot/Warm/Cold)."""
    if puntuacion >= 90:
        return "Hot"
    if puntuacion >= 70:
        return "Warm"
    return "Cold"


def id_externo(contacto):
    """ID externo ESTABLE (mismo lead -> mismo ID) para hacer 'upsert' sin duplicar.

    Usamos un hash de la clave normalizada (email+teléfono). hashlib da un valor
    reproducible entre ejecuciones, justo lo que Salesforce necesita como
    External Id para reimportar sin crear copias.
    """
    email_norm, tlf_norm = clave_contacto(contacto)
    base = f"{email_norm}|{tlf_norm}"
    return "LD-" + hashlib.md5(base.encode("utf-8")).hexdigest()[:12]


def exportar_salesforce(validos, ruta="leads_salesforce.csv"):
    """Genera un CSV listo para el Asistente de Importación de Salesforce (objeto Lead).

    Cabeceras con los nombres de campo de Salesforce -> se auto-mapean solas.
    Incluye External_Id__c para que reimportar haga 'upsert' (actualiza, no duplica).
    """
    columnas = [
        "External_Id__c", "FirstName", "LastName", "Company", "Email", "Phone",
        "LeadSource", "Rating", "Lead_Score__c", "Status",
    ]
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(columnas)
        for c in validos:
            nombre_pila, apellidos = separar_nombre(c["nombre"])
            email = corregir_dominio_email(c["email"])
            empresa = c["empresa"].strip() or "(Desconocida)"  # Company es obligatorio
            escritor.writerow([
                id_externo(c),
                nombre_pila,
                apellidos,
                empresa,
                email,
                telefono_e164(c["telefono"]),
                "Validador Python",
                rating_salesforce(c["puntuacion"]),
                c["puntuacion"],
                "Open - Not Contacted",
            ])


def generar_informe_html(validos, invalidos, duplicados, contactos,
                         ruta="informe.html"):
    """Crea un panel HTML visual con las métricas clave y los mejores leads."""
    total = len(contactos)
    n_val, n_inv, n_dup = len(validos), len(invalidos), len(duplicados)
    pct_val = round(n_val / total * 100) if total else 0
    # Mejores leads: ordenados por puntuación de mayor a menor.
    mejores = sorted(validos, key=lambda c: c["puntuacion"], reverse=True)[:10]
    top_empresas = estadisticas_por_empresa(contactos)
    top_dominios = estadisticas_por_dominio(contactos)

    # escape() evita que un nombre con < o & rompa el HTML del informe.
    filas_leads = "".join(
        f"<tr><td>{escape(c['nombre'])}</td>"
        f"<td>{escape(corregir_dominio_email(c['email']))}</td>"
        f"<td>{escape(formatear_telefono(c['telefono']))}</td>"
        f"<td>{escape(c['empresa'])}</td>"
        f"<td><b>{c['puntuacion']}</b></td><td>{escape(c['categoria'])}</td></tr>"
        for c in mejores
    )
    filas_empresas = "".join(
        f"<tr><td>{escape(nombre)}</td><td>{n}</td></tr>" for nombre, n in top_empresas
    )
    filas_dominios = "".join(
        f"<tr><td>{escape(nombre)}</td><td>{n}</td></tr>" for nombre, n in top_dominios
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe de Validación de Leads</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#0f172a;
         color:#e2e8f0; margin:0; padding:40px; }}
  h1 {{ color:#38bdf8; }}
  h2 {{ color:#94a3b8; border-bottom:1px solid #334155; padding-bottom:6px; }}
  .cards {{ display:flex; gap:20px; flex-wrap:wrap; margin:30px 0; }}
  .card {{ background:#1e293b; border-radius:14px; padding:24px 30px;
           min-width:160px; box-shadow:0 4px 14px rgba(0,0,0,.3); }}
  .card .num {{ font-size:38px; font-weight:700; }}
  .card .lbl {{ color:#94a3b8; font-size:14px; }}
  .ok {{ color:#4ade80; }} .bad {{ color:#f87171; }} .dup {{ color:#fbbf24; }}
  table {{ width:100%; border-collapse:collapse; margin:14px 0 34px; }}
  th,td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #334155; }}
  th {{ color:#38bdf8; }}
  tr:hover {{ background:#1e293b; }}
  .tablas {{ display:flex; gap:40px; flex-wrap:wrap; }}
  .tablas > div {{ flex:1; min-width:280px; }}
  footer {{ margin-top:40px; color:#64748b; font-size:13px; }}
</style>
</head>
<body>
  <h1>📊 Informe de Validación de Leads</h1>
  <p>Análisis automático de <b>{total}</b> contactos importados.</p>
  <div class="cards">
    <div class="card"><div class="num ok">{n_val}</div>
      <div class="lbl">✅ Válidos ({pct_val}%)</div></div>
    <div class="card"><div class="num bad">{n_inv}</div>
      <div class="lbl">❌ Inválidos</div></div>
    <div class="card"><div class="num dup">{n_dup}</div>
      <div class="lbl">🔁 Duplicados</div></div>
    <div class="card"><div class="num">{total}</div>
      <div class="lbl">📇 Total procesados</div></div>
  </div>

  <h2>🏆 Mejores 10 leads (por puntuación)</h2>
  <table>
    <tr><th>Nombre</th><th>Email</th><th>Teléfono</th><th>Empresa</th>
        <th>Nota</th><th>Categoría</th></tr>
    {filas_leads}
  </table>

  <div class="tablas">
    <div>
      <h2>🏢 Top empresas</h2>
      <table><tr><th>Empresa</th><th>Leads</th></tr>{filas_empresas}</table>
    </div>
    <div>
      <h2>📧 Top dominios de email</h2>
      <table><tr><th>Dominio</th><th>Leads</th></tr>{filas_dominios}</table>
    </div>
  </div>

  <footer>Generado automáticamente por validador.py — sin librerías externas.</footer>
</body>
</html>"""

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)


# =============================================================================
# 8) PROGRAMA PRINCIPAL
# =============================================================================

def main():
    print("🚀 Iniciando validador y enriquecedor de leads...\n")

    if not os.path.exists("contactos.csv"):
        print("❌ No encuentro 'contactos.csv' en esta carpeta. "
              "Crea el archivo con las columnas: nombre,email,telefono,empresa")
        return

    campos = ["nombre", "email", "telefono", "empresa"]
    contactos = []
    # utf-8-sig se "come" el BOM que añade Excel al guardar como 'CSV UTF-8'.
    with open("contactos.csv", "r", encoding="utf-8-sig") as archivo:
        for fila in csv.DictReader(archivo):
            # Robustez: si a una fila le falta un campo, lo dejamos en "" en vez
            # de None (así .strip() nunca falla con una fila mal formada).
            contactos.append({campo: (fila.get(campo) or "") for campo in campos})

    print(f"📥 Se han leído {len(contactos)} contactos del archivo.\n")

    # Paso A: separar los duplicados (conservan su dato original). Una sola pasada.
    duplicados_contactos = detectar_duplicados(contactos)
    filas_duplicadas = {id(c) for c in duplicados_contactos}  # identidad de cada fila
    for c in duplicados_contactos:
        c["motivo"] = "Contacto duplicado"

    # Paso B: clasificar el resto (los únicos) en válidos o inválidos.
    validos = []
    invalidos = []
    for contacto in contactos:
        if id(contacto) in filas_duplicadas:
            continue  # ya está contado como duplicado, no se reprocesa

        # Puntuamos y clasificamos el lead.
        contacto["puntuacion"] = puntuar_lead(contacto)
        contacto["categoria"] = clasificar_lead(contacto["puntuacion"])

        # Recogemos los motivos de error (si los hay).
        errores = []
        if not validar_email(corregir_dominio_email(contacto["email"])):
            errores.append("email incorrecto")
        if not validar_telefono(contacto["telefono"]):
            errores.append("teléfono incorrecto")
        if not validar_empresa(contacto["empresa"]):
            errores.append("empresa vacía")
        if es_email_desechable(contacto["email"]):
            errores.append("email desechable")

        if not errores:
            validos.append(contacto)
        else:
            contacto["motivo"] = " y ".join(errores).capitalize()
            invalidos.append(contacto)

    # --- Archivos de detalle (dato ORIGINAL, no normalizado) ---
    with open("validos.txt", "w", encoding="utf-8") as f:
        f.write("CONTACTOS VÁLIDOS\n" + "=" * 40 + "\n")
        for c in validos:
            f.write(f"{c['nombre']} | {c['email']} | {c['telefono']} | "
                    f"{c['empresa']} | nota {c['puntuacion']} | {c['categoria']}\n")

    with open("invalidos.txt", "w", encoding="utf-8") as f:
        f.write("CONTACTOS INVÁLIDOS\n" + "=" * 40 + "\n")
        for c in invalidos:
            f.write(f"{c['nombre']} | {c['email']} | {c['telefono']} | "
                    f"{c['empresa']} -> MOTIVO: {c['motivo']}\n")

    with open("duplicados.txt", "w", encoding="utf-8") as f:
        f.write("CONTACTOS DUPLICADOS\n" + "=" * 40 + "\n")
        for c in duplicados_contactos:
            f.write(f"{c['nombre']} | {c['email']} | {c['telefono']} | "
                    f"{c['empresa']}\n")

    # --- Salidas "premium": CSV limpio + Salesforce-ready + panel HTML ---
    exportar_csv_limpio(validos)
    exportar_salesforce(validos)
    generar_informe_html(validos, invalidos, duplicados_contactos, contactos)

    print("💾 Guardados: validos.txt, invalidos.txt, duplicados.txt,")
    print("            leads_limpios.csv, leads_salesforce.csv e informe.html\n")

    # Pequeño ranking en consola para ver el valor de un vistazo.
    print("🏢 Top empresas por nº de leads:")
    for nombre, n in estadisticas_por_empresa(contactos):
        print(f"   - {nombre}: {n}")

    generar_informe(validos, invalidos, duplicados_contactos)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# QUÉ HACE: Toma una lista de contactos "sucia" (CSV), la limpia, corrige
#           erratas, valida email y teléfono, elimina duplicados aunque vengan
#           con mayúsculas/espacios/prefijos, puntúa cada lead de 0 a 100 y
#           genera una base limpia para el CRM más un panel visual en HTML.
# PARA QUIÉN: Equipos comerciales / RRHH que gestionan bases de leads, clientes
#             o proveedores y necesitan datos fiables y priorizados.
# TIEMPO QUE AHORRA: Depurar y priorizar miles de contactos a mano lleva días;
#                    este script lo hace en segundos y sin errores humanos.
# -----------------------------------------------------------------------------
