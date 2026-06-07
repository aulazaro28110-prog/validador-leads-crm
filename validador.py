# -*- coding: utf-8 -*-
"""
Validador de Contactos Empresariales
Lee contactos.csv, valida emails y teléfonos, detecta duplicados
y genera informes en validos.txt e invalidos.txt
"""

import csv
import sys

# En Windows la consola usa cp1252 y no puede mostrar emojis.
# Forzamos la salida a UTF-8 para que los prints con emojis se vean bien.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def validar_email(email):
    """Devuelve True si el email tiene @ y un punto DESPUÉS del @, False si no."""
    if "@" not in email:
        return False
    # Separamos en la parte de antes y después del @
    partes = email.split("@")
    # Debe haber exactamente una @ (dos partes) y ninguna parte vacía
    if len(partes) != 2:
        return False
    usuario, dominio = partes
    if usuario == "" or dominio == "":
        return False
    # El punto debe estar en el dominio (después del @)
    if "." not in dominio:
        return False
    return True


def validar_telefono(telefono):
    """Devuelve True si solo tiene números y tiene entre 9 y 15 dígitos, False si no."""
    # Quitamos espacios por si acaso
    telefono = telefono.strip()
    if not telefono.isdigit():
        return False
    if 9 <= len(telefono) <= 15:
        return True
    return False


def detectar_duplicados(lista_contactos):
    """Recibe la lista completa y devuelve los nombres de los contactos duplicados."""
    vistos = []
    duplicados = []
    for contacto in lista_contactos:
        # Clave única: combinamos todos los campos para detectar duplicados EXACTOS
        clave = (
            contacto["nombre"],
            contacto["email"],
            contacto["telefono"],
            contacto["empresa"],
        )
        if clave in vistos:
            if contacto["nombre"] not in duplicados:
                duplicados.append(contacto["nombre"])
        else:
            vistos.append(clave)
    return duplicados


def generar_informe(validos, invalidos, duplicados):
    """Imprime un resumen final con el conteo de cada categoría."""
    print("\n" + "=" * 45)
    print("📊 INFORME FINAL DE VALIDACIÓN")
    print("=" * 45)
    print(f"✅ Contactos válidos:     {len(validos)}")
    print(f"❌ Contactos inválidos:   {len(invalidos)}")
    print(f"🔁 Contactos duplicados:  {len(duplicados)}")
    if duplicados:
        print(f"   👉 Nombres duplicados: {', '.join(duplicados)}")
    total = len(validos) + len(invalidos) + len(duplicados)
    print(f"📇 Total procesados:      {total}")
    print("=" * 45)
    print("📄 Revisa 'validos.txt', 'invalidos.txt' y 'duplicados.txt' para el detalle.")
    print("=" * 45 + "\n")


def main():
    print("🚀 Iniciando validador de contactos empresariales...\n")

    contactos = []
    # Leemos el CSV con el módulo csv (incluido en Python, no hace falta instalar nada)
    with open("contactos.csv", "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            contactos.append(fila)

    print(f"📥 Se han leído {len(contactos)} contactos del archivo.\n")

    validos = []
    invalidos = []
    duplicados_contactos = []
    vistos = []  # claves de contactos ya procesados, para detectar repetidos

    # Recorremos cada contacto con un bucle for
    for contacto in contactos:
        nombre = contacto["nombre"]
        email = contacto["email"]
        telefono = contacto["telefono"]

        # Clave única con todos los campos: si ya la hemos visto, es un duplicado exacto
        clave = (nombre, email, telefono, contacto["empresa"])
        if clave in vistos:
            contacto["motivo"] = "Contacto duplicado"
            duplicados_contactos.append(contacto)
            print(f"🔁 {nombre}: contacto duplicado (omitido de válidos)")
            continue
        vistos.append(clave)

        email_ok = validar_email(email)
        telefono_ok = validar_telefono(telefono)

        # Clasificamos con if / elif / else
        if email_ok and telefono_ok:
            validos.append(contacto)
            print(f"✅ {nombre}: contacto válido")
        elif not email_ok and not telefono_ok:
            contacto["motivo"] = "Email y teléfono incorrectos"
            invalidos.append(contacto)
            print(f"❌ {nombre}: email y teléfono incorrectos")
        elif not email_ok:
            contacto["motivo"] = "Email incorrecto"
            invalidos.append(contacto)
            print(f"❌ {nombre}: email incorrecto")
        else:
            contacto["motivo"] = "Teléfono incorrecto"
            invalidos.append(contacto)
            print(f"❌ {nombre}: teléfono incorrecto")

    # Detectamos duplicados sobre la lista completa
    duplicados = detectar_duplicados(contactos)

    # Guardamos los contactos válidos en validos.txt
    with open("validos.txt", "w", encoding="utf-8") as f:
        f.write("CONTACTOS VÁLIDOS\n")
        f.write("=" * 40 + "\n")
        for c in validos:
            f.write(
                f"{c['nombre']} | {c['email']} | {c['telefono']} | {c['empresa']}\n"
            )

    # Guardamos los contactos inválidos con su motivo en invalidos.txt
    with open("invalidos.txt", "w", encoding="utf-8") as f:
        f.write("CONTACTOS INVÁLIDOS\n")
        f.write("=" * 40 + "\n")
        for c in invalidos:
            f.write(
                f"{c['nombre']} | {c['email']} | {c['telefono']} | "
                f"{c['empresa']} -> MOTIVO: {c['motivo']}\n"
            )

    # Guardamos los contactos duplicados en duplicados.txt
    with open("duplicados.txt", "w", encoding="utf-8") as f:
        f.write("CONTACTOS DUPLICADOS\n")
        f.write("=" * 40 + "\n")
        for c in duplicados_contactos:
            f.write(
                f"{c['nombre']} | {c['email']} | {c['telefono']} | {c['empresa']}\n"
            )

    print("\n💾 Archivos 'validos.txt', 'invalidos.txt' y 'duplicados.txt' guardados.")

    # Mostramos el resumen final
    generar_informe(validos, invalidos, duplicados)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# QUÉ HACE: Lee una lista de contactos desde un CSV, valida que el email y el
#           teléfono tengan un formato correcto, detecta contactos duplicados y
#           genera dos archivos de salida (válidos e inválidos con su motivo).
# PARA QUIÉN: Útil para cualquier empresa con departamento comercial o de RRHH
#             que gestione bases de datos de clientes, leads o proveedores.
# TIEMPO QUE AHORRA: Revisar 1.000 contactos a mano lleva horas; este script lo
#                    hace en segundos, evitando errores de envío y datos sucios.
# -----------------------------------------------------------------------------
