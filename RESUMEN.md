# 📇 Sistema Comercial de Leads — Ficha resumen
### Python para limpiar, priorizar, repartir y dar seguimiento a bases de leads

> **De días de trabajo manual a segundos.** Convierte una lista de contactos "sucia"
> en una operación de ventas organizada para todo un equipo.

*(Documento breve. La explicación completa está en el [README](README.md).)*

---

## ¿Qué es este proyecto?
Un sistema en Python (sin librerías externas) que encadena **4 fases**:

```
validador.py  →  lead_scorer.py  →  reparto.py            →  crm.py
  (limpia)        (prioriza)        (reparte + balance)       (seguimiento)
```

1. **Validador** — valida email/teléfono/nombre con **regex**, corrige erratas y
   detecta duplicados "sucios" (mayúsculas, espacios, `+34`, `gmail.con`).
2. **Lead Scorer** — puntúa cada lead 0-100 por **potencial de venta** (cargo +
   sector/tamaño + actividad) y lo clasifica en 🔥 Caliente / 🌡️ Templado / ❄️ Frío.
3. **Reparto** — reparte los leads entre los comerciales equilibrando temperatura y
   carga (🟢 lunes) y hace el **balance** de lo trabajado (🔴 viernes).
4. **CRM** — agenda diaria de contactos y estados (nuevo → seguimiento → cerrado).

## Calidad
- ✅ **57 tests automáticos (pytest)** — `python -m pytest -v`
- 📦 **Cero dependencias de ejecución** (solo biblioteca estándar de Python 3)
- ♻️ **Código reutilizable**: scorer, reparto y CRM importan el núcleo del validador

## Conceptos Python aplicados
- **Expresiones regulares** (`re`) para validar formatos
- **Funciones** con responsabilidad única · **diccionarios y `set`** (conteos, duplicados)
- **Tests con pytest** (fixtures, casos límite) como red de seguridad
- **Generación de archivos** CSV y HTML · **CLI** por argumentos
- **Robustez**: salida UTF-8 en Windows, tolerancia a datos sucios y columnas faltantes

## Resultados de ejemplo
- Validador: **1013** procesados · ✅ **1004** válidos · 🔁 **3** duplicados · ~135 min de limpieza evitados
- Lead Scorer (1.000 leads): 🔥 **319** calientes · 🌡️ **480** templados · ❄️ **201** fríos

## Para quién
Responsables de equipos comerciales que cada semana reciben más leads de los que
pueden atender y necesitan **limpiarlos, priorizarlos y repartirlos** de forma justa.

## Cómo ejecutarlo
```bash
python validador.py            # limpia contactos.csv
python lead_scorer.py          # prioriza
python reparto.py              # reparte (lunes) · "balance" para el viernes
```

---
© 2026 Álvaro Utazu Lázaro · Código *source-available* (ver [LICENSE](LICENSE))
