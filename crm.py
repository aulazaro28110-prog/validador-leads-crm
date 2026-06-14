# -*- coding: utf-8 -*-
"""
=============================================================================
 MINI-CRM "LEADS DE HOY"
=============================================================================
Gestiona el seguimiento diario de los leads ya limpios por validador.py.

Reutiliza el "núcleo" del validador (normalizar_email) para identificar a cada
persona, de modo que el validador deja de ser una herramienta de un solo uso y
pasa a ser la base de la que tira este CRM.

Base de datos: seguimiento.csv  (se crea solo la primera vez)

Comandos:
  python crm.py importar            -> añade leads nuevos desde leads_limpios.csv
  python crm.py hoy                 -> a quién toca contactar hoy
  python crm.py contactado <email>  -> marca contactado hoy y agenda el siguiente
  python crm.py cerrar <email>      -> venta hecha: sale de la agenda
  python crm.py descartar <email>   -> no interesa: sale de la agenda
  python crm.py nota <email> "..."  -> apunta un detalle (con fecha) al lead
  python crm.py listar              -> muestra todo el CRM
=============================================================================
"""

import csv
import sys
import os
from datetime import date, timedelta

# Reutilizamos el motor del validador (mismo criterio para identificar emails).
from validador import normalizar_email

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

DB = "seguimiento.csv"
ENTRADA = "leads_limpios.csv"
DIAS_SEGUIMIENTO = 3  # cada cuántos días se reagenda un lead tras contactarlo

COLUMNAS = [
    "email", "nombre", "telefono", "empresa", "estado",
    "alta", "ultimo_contacto", "proximo_contacto", "notas",
]

# Estados que siguen "vivos" (aparecen en la agenda); el resto se ignora.
ESTADOS_ACTIVOS = {"nuevo", "seguimiento"}


def hoy_iso():
    """Devuelve la fecha de hoy como texto 'AAAA-MM-DD'."""
    return date.today().isoformat()


def cargar_db():
    """Lee seguimiento.csv y devuelve la lista de leads (vacía si no existe)."""
    if not os.path.exists(DB):
        return []
    with open(DB, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def guardar_db(leads):
    """Escribe la lista de leads de vuelta a seguimiento.csv."""
    with open(DB, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(leads)


def buscar(leads, email):
    """Devuelve el lead cuyo email coincide (normalizado), o None."""
    clave = normalizar_email(email)
    for lead in leads:
        if normalizar_email(lead["email"]) == clave:
            return lead
    return None


def comando_importar():
    """Añade al CRM los leads de leads_limpios.csv que aún no estén dentro."""
    if not os.path.exists(ENTRADA):
        print(f"❌ No encuentro '{ENTRADA}'. Ejecuta antes:  python validador.py")
        return

    leads = cargar_db()
    with open(ENTRADA, "r", encoding="utf-8") as f:
        nuevos_origen = list(csv.DictReader(f))

    añadidos = 0
    for fila in nuevos_origen:
        if buscar(leads, fila["email"]) is not None:
            continue  # ya está en el CRM, no lo duplicamos
        leads.append({
            "email": fila["email"],
            "nombre": fila["nombre"],
            "telefono": fila["telefono"],
            "empresa": fila["empresa"],
            "estado": "nuevo",
            "alta": hoy_iso(),
            "ultimo_contacto": "",
            "proximo_contacto": hoy_iso(),  # los nuevos tocan desde hoy
            "notas": "",
        })
        añadidos += 1

    guardar_db(leads)
    print(f"📥 Importados {añadidos} leads nuevos. CRM total: {len(leads)}.")


def comando_hoy():
    """Lista los leads activos cuyo próximo contacto es hoy o ya pasó."""
    leads = cargar_db()
    hoy = date.today()
    pendientes = []
    for lead in leads:
        if lead["estado"] not in ESTADOS_ACTIVOS:
            continue
        try:
            proximo = date.fromisoformat(lead["proximo_contacto"])
        except ValueError:
            proximo = hoy  # si la fecha está mal, lo mostramos por si acaso
        if proximo <= hoy:
            pendientes.append((proximo, lead))

    # Primero los más atrasados.
    pendientes.sort(key=lambda par: par[0])

    print(f"\n== 📅 LEADS PARA HOY ({len(pendientes)}) ==")
    if not pendientes:
        print("   🎉 ¡Nada pendiente! Estás al día.")
    for proximo, lead in pendientes:
        dias_atraso = (hoy - proximo).days
        if lead["estado"] == "nuevo":
            etiqueta = "nuevo"
        elif dias_atraso > 0:
            etiqueta = f"seguimiento (atrasado {dias_atraso}d)"
        else:
            etiqueta = "seguimiento"
        print(f"   [ ] {lead['nombre']:<22} | {lead['empresa']:<16} | {etiqueta}")
        print(f"       {lead['email']} · {lead['telefono']}")
    print()


def comando_contactado(email):
    """Marca un lead como contactado hoy y reagenda el siguiente toque."""
    leads = cargar_db()
    lead = buscar(leads, email)
    if lead is None:
        print(f"❌ No encuentro ningún lead con el email '{email}'.")
        return
    lead["estado"] = "seguimiento"
    lead["ultimo_contacto"] = hoy_iso()
    lead["proximo_contacto"] = (date.today() + timedelta(days=DIAS_SEGUIMIENTO)).isoformat()
    guardar_db(leads)
    print(f"✅ {lead['nombre']} marcado como contactado. "
          f"Siguiente toque: {lead['proximo_contacto']}.")


def comando_estado_final(email, nuevo_estado):
    """Cierra (venta) o descarta (no interesa) un lead: sale de la agenda diaria."""
    leads = cargar_db()
    lead = buscar(leads, email)
    if lead is None:
        print(f"❌ No encuentro ningún lead con el email '{email}'.")
        return
    lead["estado"] = nuevo_estado
    lead["ultimo_contacto"] = hoy_iso()
    lead["proximo_contacto"] = ""  # ya no se reagenda
    guardar_db(leads)
    print(f"🏁 {lead['nombre']} marcado como '{nuevo_estado}'. Ya no aparecerá en 'hoy'.")


def comando_nota(email, texto):
    """Añade una nota fechada al lead, sin borrar las anteriores."""
    leads = cargar_db()
    lead = buscar(leads, email)
    if lead is None:
        print(f"❌ No encuentro ningún lead con el email '{email}'.")
        return
    apunte = f"[{hoy_iso()}] {texto}"
    # Si ya había notas, las separamos con ' | ' para conservar el historial.
    lead["notas"] = f"{lead['notas']} | {apunte}" if lead["notas"] else apunte
    guardar_db(leads)
    print(f"📝 Nota añadida a {lead['nombre']}: {apunte}")


def comando_listar():
    """Muestra todos los leads del CRM con su estado y fechas."""
    leads = cargar_db()
    print(f"\n== 📇 CRM COMPLETO ({len(leads)} leads) ==")
    if not leads:
        print("   (vacío) Usa:  python crm.py importar")
    for lead in leads:
        print(f"   {lead['nombre']:<22} | {lead['empresa']:<16} | "
              f"{lead['estado']:<12} | próx: {lead['proximo_contacto']}")
    print()


def main():
    # sys.argv son las palabras que escribes tras 'python crm.py'.
    args = sys.argv[1:]
    comando = args[0] if args else "hoy"  # sin argumentos, mostramos la agenda

    if comando == "importar":
        comando_importar()
    elif comando == "hoy":
        comando_hoy()
    elif comando == "contactado":
        if len(args) < 2:
            print("Uso: python crm.py contactado <email>")
        else:
            comando_contactado(args[1])
    elif comando == "listar":
        comando_listar()
    elif comando == "cerrar":
        if len(args) < 2:
            print("Uso: python crm.py cerrar <email>")
        else:
            comando_estado_final(args[1], "cerrado")
    elif comando == "descartar":
        if len(args) < 2:
            print("Uso: python crm.py descartar <email>")
        else:
            comando_estado_final(args[1], "descartado")
    elif comando == "nota":
        if len(args) < 3:
            print('Uso: python crm.py nota <email> "texto de la nota"')
        else:
            # Unimos todo lo que venga tras el email por si la nota lleva espacios.
            comando_nota(args[1], " ".join(args[2:]))
    else:
        print("Comandos: importar | hoy | contactado <email> | "
              "cerrar <email> | descartar <email> | nota <email> \"texto\" | listar")


if __name__ == "__main__":
    main()
