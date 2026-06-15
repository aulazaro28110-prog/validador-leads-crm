# -*- coding: utf-8 -*-
"""
=============================================================================
 GENERADOR DE PRIMER CONTACTO
=============================================================================
Crea un mensaje personalizado para cada lead NUEVO del CRM (seguimiento.csv),
rellenando la plantilla 'plantilla.txt' con los datos de cada contacto.

El texto lo editas tú en plantilla.txt (sin tocar el código), usando huecos:
  {nombre}  {nombre_pila}  {empresa}  {email}  {telefono}

Reutiliza separar_nombre() del validador para sacar el nombre de pila, así que
el validador sigue siendo el "núcleo" del que tiran todas las herramientas.

Salida: mensajes.csv  (columnas: email, asunto, mensaje), listo para mail-merge.

Uso:
  python mensajes.py
=============================================================================
"""

import csv
import sys
import os

# Reutilizamos el núcleo del validador (mismo criterio para partir el nombre).
from validador import separar_nombre

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

CRM = "seguimiento.csv"
PLANTILLA = "plantilla.txt"
SALIDA = "mensajes.csv"
ESTADO_OBJETIVO = "nuevo"  # primer contacto = leads que aún no se han contactado


def cargar_plantilla(ruta=PLANTILLA):
    """Lee la plantilla y la separa en (asunto, cuerpo).

    Si la primera línea empieza por 'Asunto:', se usa como asunto del email.
    """
    with open(ruta, "r", encoding="utf-8-sig") as f:
        lineas = f.read().split("\n")

    asunto = "Hola"
    cuerpo_lineas = lineas
    if lineas and lineas[0].lower().startswith("asunto:"):
        asunto = lineas[0].split(":", 1)[1].strip()
        cuerpo_lineas = lineas[1:]
    cuerpo = "\n".join(cuerpo_lineas).strip("\n")
    return asunto, cuerpo


def personalizar(texto, lead):
    """Sustituye los huecos {campo} por los datos reales del lead."""
    # .get evita un KeyError si una fila del CRM viene con alguna columna de menos.
    nombre = lead.get("nombre", "")
    nombre_pila, _ = separar_nombre(nombre)
    reemplazos = {
        "{nombre}": nombre,
        "{nombre_pila}": nombre_pila or nombre,
        "{empresa}": lead.get("empresa", ""),
        "{email}": lead.get("email", ""),
        "{telefono}": lead.get("telefono", ""),
    }
    for hueco, valor in reemplazos.items():
        texto = texto.replace(hueco, valor)
    return texto


def main():
    if not os.path.exists(CRM):
        print(f"❌ No encuentro '{CRM}'. Ejecuta antes:  python crm.py importar")
        return
    if not os.path.exists(PLANTILLA):
        print(f"❌ No encuentro '{PLANTILLA}'. Crea la plantilla del mensaje primero.")
        return

    asunto_plantilla, cuerpo_plantilla = cargar_plantilla()

    with open(CRM, "r", encoding="utf-8-sig") as f:
        leads = list(csv.DictReader(f))

    # Solo generamos mensajes para los leads que aún no se han contactado.
    objetivo = [l for l in leads if l.get("estado") == ESTADO_OBJETIVO]

    mensajes = []
    for lead in objetivo:
        asunto = personalizar(asunto_plantilla, lead)
        cuerpo = personalizar(cuerpo_plantilla, lead)
        mensajes.append({"email": lead["email"], "asunto": asunto, "mensaje": cuerpo})

    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=["email", "asunto", "mensaje"])
        escritor.writeheader()
        escritor.writerows(mensajes)

    print(f"✉️  Generados {len(mensajes)} mensajes de primer contacto en '{SALIDA}'.")
    if not mensajes:
        print("   (No hay leads 'nuevo'. Importa o revisa el estado en el CRM.)")
        return

    # Mostramos el primer mensaje como ejemplo para que veas el resultado.
    ejemplo = mensajes[0]
    print("\n--- EJEMPLO (primer lead) ---")
    print(f"Para:    {ejemplo['email']}")
    print(f"Asunto:  {ejemplo['asunto']}")
    print(f"{ejemplo['mensaje']}")
    print("-----------------------------")


if __name__ == "__main__":
    main()
