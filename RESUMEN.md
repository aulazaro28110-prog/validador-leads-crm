# 📇 Validador de Contactos Empresariales
### Script Python para limpieza automática de bases de datos CRM

> **Reduce de 3 horas a 10 segundos** la limpieza manual de una base de datos de contactos empresariales.

---

## ¿Qué es este proyecto?
Un script en Python que lee una base de datos de contactos desde un archivo CSV,
valida que cada email y teléfono tengan un formato correcto, detecta contactos
duplicados y genera informes separados de contactos válidos e inválidos.

## Archivos del proyecto
| Archivo | Descripción |
|---------|-------------|
| `contactos.csv` | Datos de entrada (10 contactos de ejemplo) |
| `validador.py` | Script principal con la lógica de validación |
| `validos.txt` | Salida: contactos correctos |
| `invalidos.txt` | Salida: contactos con errores y su motivo |
| `RESUMEN.md` | Este documento |

## Conceptos Python aplicados
- **Funciones** (`def`) para separar responsabilidades: validar email, validar teléfono, detectar duplicados, generar informe
- **Condicionales** (`if/elif/else`) para clasificar cada contacto como válido o inválido
- **Bucles** (`for`) para procesar automáticamente toda la lista de contactos
- **Módulo `csv`** nativo de Python para leer datos reales sin instalar librerías externas
- **Escritura de archivos** con `open()` y `write()` para generar los informes de salida
- **Debugging real**: reconfiguración de salida a UTF-8 (`sys.stdout.reconfigure`) para compatibilidad con Windows

## Reglas de validación
- **Email:** debe contener `@` y un punto `.` *después* del `@`.
- **Teléfono:** solo dígitos, con una longitud de entre 9 y 15 caracteres.
- **Duplicados:** se marca como duplicado un contacto idéntico en todos sus campos.

## Resultados de la última ejecución
- 📥 Contactos procesados: **10**
- ✅ Válidos: **6**
- ❌ Inválidos: **4**
- 🔁 Duplicados detectados: **1** (Ana García)

### Detalle de inválidos
| Nombre | Motivo |
|--------|--------|
| María López | Email sin `@` |
| Carlos Ruiz | Email sin punto tras la `@` |
| Elena Sánchez | Teléfono con letras |
| Javier Moreno | Teléfono demasiado corto (5 dígitos) |

## Para qué sirve
Útil para empresas con departamentos comerciales, marketing o RRHH que gestionan
bases de datos de clientes, leads o proveedores. Revisar miles de contactos a mano
lleva horas y genera errores; este script lo hace en segundos, evitando envíos
fallidos, campañas a emails incorrectos y datos sucios en el CRM.

## Nota técnica
> En Windows la consola usa la codificación `cp1252`, que no muestra emojis.
> El script reconfigura la salida a UTF-8 (`sys.stdout.reconfigure`) para que
> los prints con emojis se vean correctamente.

## Cómo ejecutarlo
```bash
python validador.py
```

---
*Creado con Claude Code (Anthropic) · Proyecto AI Engineer — Álvaro 2026*
