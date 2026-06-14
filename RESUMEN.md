# 📇 Validador y Enriquecedor de Leads — Ficha resumen
### Script Python para limpieza, puntuación y priorización de bases de datos CRM

> **De días de limpieza manual a segundos.** Convierte una lista de contactos
> "sucia" en una base limpia, puntuada y lista para importar a Salesforce.

*(Documento breve. La explicación completa está en el [README](README.md).)*

---

## ¿Qué es este proyecto?
Un script en Python (sin librerías externas) que lee contactos desde un CSV,
los limpia y normaliza, valida email/teléfono/empresa/nombre, corrige erratas,
detecta duplicados "sucios", **puntúa cada lead de 0 a 100** y genera varios
informes, incluido un CSV listo para Salesforce y un panel HTML.

## Archivos del proyecto
| Archivo | Descripción |
|---------|-------------|
| `contactos.csv` | Datos de entrada (1013 leads de ejemplo) |
| `validador.py` | Script principal con toda la lógica |
| `leads_limpios.csv` | Salida: base depurada y enriquecida |
| `leads_salesforce.csv` | Salida: CSV listo para importar a Salesforce |
| `informe.html` | Salida: panel visual de resultados |
| `validos/invalidos/duplicados.txt` | Salidas de detalle por categoría |

## Conceptos Python aplicados
- **Funciones** con responsabilidad única (normalizar, validar, puntuar, exportar)
- **Diccionarios y `set`** para conteos, claves de duplicados e identidad de filas
- **Condicionales y bucles** para clasificar cada lead
- **Módulos estándar** `csv`, `hashlib` (ID estable) y `html` (escape seguro)
- **Generación de archivos** CSV, HTML y TXT
- **Robustez**: salida UTF-8 en Windows y lectura tolerante a filas mal formadas

## Reglas y puntuación
- **Email:** una `@`, dominio con punto y extensión ≥ 2 (+ corrección de erratas).
- **Teléfono:** 9–15 dígitos tras normalizar (quita espacios, guiones y prefijo +34).
- **Duplicados:** misma persona por clave normalizada (email + teléfono).
- **Nota 0-100:** email 40 · teléfono 30 · empresa 20 · nombre 10 · desechable −30.
- **Categorías:** A (Oro) ≥90 · B ≥70 · C ≥40 · D <40.

## Resultados de la última ejecución
- 📥 Procesados: **1013** · ✅ Válidos: **1004** · ❌ Inválidos: **6** · 🔁 Duplicados: **3**

## Para qué sirve
Equipos comerciales, marketing o RRHH que gestionan bases de leads, clientes o
proveedores: depura miles de contactos en segundos, los prioriza por calidad y
los deja listos para el CRM, evitando duplicados y campañas a datos incorrectos.

## Cómo ejecutarlo
```bash
python validador.py
```

---
*Creado con Claude Code (Anthropic) · Proyecto AI Engineer — Álvaro 2026*
