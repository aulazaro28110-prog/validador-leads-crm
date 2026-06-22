# 🎯 Sistema Comercial de Leads (Validador · Lead Scorer · Reparto · CRM)

> Sistema en Python que convierte una lista de contactos **"sucia"** en una operación de
> ventas organizada: la **limpia**, **prioriza los mejores leads**, los **reparte entre el
> equipo** y hace **seguimiento** — en segundos y sin librerías externas (solo Python estándar).

---

## 🧭 El proyecto de un vistazo

Lo que empezó como un validador es hoy un **sistema comercial completo de 4 fases** que
organiza el trabajo de un equipo de ventas durante toda la semana:

```
validador.py  →  lead_scorer.py  →  reparto.py             →  crm.py
  (limpia)        (prioriza)        (reparte + balance)        (seguimiento)
```

| Fase | Módulo | Qué hace |
|------|--------|----------|
| 1. Limpieza | `validador.py` | Valida con **regex**, corrige erratas y elimina duplicados "sucios" |
| 2. Priorización | `lead_scorer.py` | Puntúa cada lead por potencial de venta → 🔥 Caliente / 🌡️ Templado / ❄️ Frío |
| 3. Reparto (equipo) | `reparto.py` | 🟢 **Lunes** reparte los leads entre comerciales; 🔴 **viernes** balancea qué trabajó cada uno |
| 4. Seguimiento | `crm.py` | Agenda diaria de contactos y estados |

✅ **57 pruebas automáticas (pytest)** cubren los validadores, el scorer y el reparto.

### 🖼️ Presentación visual

[`presentacion.html`](presentacion.html) es un panel con métricas reales (1.000 leads),
gráficas y tablas. ⚠️ **GitHub no renderiza los HTML**, así que para verlo:
- **Descárgalo** y ábrelo en tu navegador (doble clic), **o**
- publícalo como web con **GitHub Pages** (*Settings → Pages → Branch `main` → carpeta `/root`*).

### 📁 Estructura del proyecto

| Archivo(s) | Rol |
|------------|-----|
| `validador.py` · `lead_scorer.py` · `reparto.py` · `crm.py` · `mensajes.py` | Módulos del pipeline |
| `test_*.py` | Pruebas automáticas (pytest) |
| `presentacion.html` | Presentación visual del proyecto |
| `contactos.csv` · `leads_demo.csv` · `equipo.csv` | Datos de ejemplo |
| `README.md` · `RESUMEN.md` | Documentación |

---

## 🚀 Demo rápida

```
🚀 Iniciando validador y enriquecedor de leads...

📥 Se han leído 1013 contactos del archivo.

💾 Guardados: validos.txt, invalidos.txt, duplicados.txt,
            leads_limpios.csv, leads_salesforce.csv e informe.html

🏢 Top empresas por nº de leads:
   - DataSoft: 35
   - RedBricks: 34
   - DataMine: 33

==================================================
📊 INFORME FINAL DE VALIDACIÓN
==================================================
✅ Contactos válidos:     1004
❌ Contactos inválidos:   6
🔁 Contactos duplicados:  3
🧹 % duplicados eliminados: 0%
==================================================
```

---

## ❗ El problema que resuelve

Cualquier empresa con **ventas, marketing o RRHH** acumula bases de contactos con errores:

| Problema habitual | Consecuencia real |
|---|---|
| Emails sin `@`, con erratas (`gmail.con`) | Campañas que fallan al enviarse |
| Teléfonos con letras, cortos o con formatos distintos | Llamadas y SMS que no llegan |
| Duplicados "sucios" (mayúsculas, espacios, `+34`) | El cliente recibe el mismo mensaje dos veces |
| Leads sin priorizar | El comercial pierde el tiempo en contactos malos |
| Revisión manual de miles de filas | Días de trabajo repetitivo |

**Este script convierte esos días en segundos — y además prioriza los mejores leads.**

---

## ⚙️ Qué hace, paso a paso

1. **Lee** `contactos.csv` (`nombre, email, telefono, empresa`).
2. **Normaliza** los datos *solo para comparar* — el dato original **nunca** se altera.
3. **Corrige erratas** de dominio (`gmail.con` → `gmail.com`).
4. **Valida** email, teléfono, empresa y nombre.
5. **Detecta duplicados** aunque vengan sucios: `Juan@Empresa.com ` y `juan@empresa.com`
   se reconocen como la misma persona (clave normalizada email + teléfono).
6. **Descarta** correos desechables (`@mailinator.com`, etc.).
7. **Puntúa** cada lead de **0 a 100** y lo clasifica en **A / B / C / D**.
8. **Exporta** los resultados en 6 formatos.

---

## 📂 Archivos que genera

| Archivo | Para qué sirve |
|---|---|
| `validos.txt` | Válidos con su nota y categoría |
| `invalidos.txt` | Inválidos **con el motivo** del rechazo |
| `duplicados.txt` | Duplicados detectados (con el dato original) |
| `leads_limpios.csv` | Base depurada y enriquecida (uso general) |
| **`leads_salesforce.csv`** | **CSV listo para el Asistente de Importación de Salesforce** |
| `informe.html` | 📊 Panel visual con métricas y rankings (ábrelo en el navegador) |

---

## 🧮 Cómo se puntúa un lead

| Criterio | Puntos |
|---|---|
| Email válido | +40 |
| Teléfono válido | +30 |
| Empresa presente | +20 |
| Nombre y apellido | +10 |
| Email desechable | −30 |

**Categorías:** `A (Oro)` ≥90 · `B (Bueno)` ≥70 · `C (Mejorable)` ≥40 · `D (Descartar)` <40.

---

## 🔗 Integración con Salesforce

`leads_salesforce.csv` se importa **de un tirón** en el objeto **Lead**:

- Cabeceras con los nombres de campo reales (`FirstName`, `LastName`, `Company`,
  `Email`, `Phone`, `Rating`, `Status`) → **auto-mapeo**, sin trabajo manual.
- Nombre partido en `FirstName` / `LastName` (Salesforce exige `LastName`).
- Teléfono en formato internacional **E.164** (`+34612345678`), listo para CTI.
- `Rating` traducido al picklist estándar (**Hot / Warm / Cold**).
- **`External_Id__c` estable** (mismo lead → mismo ID): reimportar hace **upsert**
  (actualiza), **no crea duplicados**.

**Setup único (admin, ~5 min):** crear los campos personalizados `External_Id__c`
(External Id, único) y `Lead_Score__c` (número) en el objeto Lead.

---

## 🧩 Funciones principales

| Función | Responsabilidad |
|---|---|
| `normalizar_email/telefono` | Limpian el dato *solo para comparar* |
| `corregir_dominio_email` | Arregla erratas típicas de dominio |
| `validar_email/telefono/empresa/nombre` | Reglas de validación |
| `es_email_desechable` | Detecta correos temporales |
| `detectar_duplicados` | Encuentra duplicados con clave normalizada |
| `puntuar_lead` / `clasificar_lead` | Nota 0-100 y categoría A/B/C/D |
| `estadisticas_por_empresa/dominio` | Rankings para el informe |
| `formatear_telefono` / `telefono_e164` | Formato presentable / internacional |
| `separar_nombre` / `id_externo` | Preparación para Salesforce (FirstName/LastName, upsert) |
| `exportar_csv_limpio` / `exportar_salesforce` / `generar_informe_html` | Salidas |

---

## 🔁 Uso diario: Mini-CRM (`crm.py`)

El validador limpia los datos una vez; el **Mini-CRM los convierte en una rutina
diaria de seguimiento comercial**. `crm.py` **reutiliza el núcleo del validador**
(`from validador import normalizar_email`), así que el validador deja de ser una
herramienta de un solo uso y pasa a ser la base de la que tira el CRM.

Base de datos local: `seguimiento.csv` (se crea sola la primera vez).
Estados de un lead: `nuevo` → `seguimiento` → `cerrado` / `descartado`.

```bash
python validador.py                      # 1. limpia la lista nueva de leads
python crm.py importar                   # 2. mete los nuevos en el CRM (sin duplicar)
python mensajes.py                       # 3. genera el primer contacto de los nuevos
python crm.py hoy                        # 4. ¿a quién toca contactar hoy?
python crm.py contactado juan@x.com      # 5. tras llamar: reagenda +3 días
python crm.py nota juan@x.com "Pide oferta"   # apunta detalles (con fecha)
python crm.py cerrar juan@x.com          # venta hecha -> sale de la agenda
python crm.py descartar juan@x.com       # no interesa -> sale de la agenda
python crm.py listar                     # ver todo el CRM
```

### ✉️ Generador de primer contacto (`mensajes.py`)

Crea un mensaje **personalizado por cada lead nuevo** del CRM rellenando la
plantilla `plantilla.txt` (que editas tú, sin tocar el código) con huecos como
`{nombre_pila}` y `{empresa}`. Genera `mensajes.csv` (`email · asunto · mensaje`),
listo para mail-merge. Solo escribe a los leads en estado `nuevo`, así que un lead
ya contactado no recibe dos veces el primer contacto.

```
Asunto: Una idea para {empresa}

Hola {nombre_pila}:
Soy [TU NOMBRE], de [TU EMPRESA]...
```

Ejemplo de `python crm.py hoy`:

```
== 📅 LEADS PARA HOY (12) ==
   [ ] Ana García            | TechCorp         | nuevo
       ana.garcia@empresa.com · +34 612 34 56 78
   [ ] Luis Martínez         | Innova SL        | seguimiento (atrasado 2d)
       luis.martinez@gmail.com · +34 698 76 54 32
```

---

## 🌡️ Lead Scorer (`lead_scorer.py`) — prioriza por potencial de venta

Mientras el validador mide si el **dato** está limpio, el Lead Scorer mide cuánto
**promete** un lead como cliente y lo clasifica en una temperatura comercial.

| Señal | Qué mide | Puntos |
|-------|----------|:------:|
| 👔 Cargo | ¿Decide la compra? (CEO/Director… vs becario) | 0-30 |
| 🏢 Sector + Tamaño | ¿Encaja con el cliente ideal? | 0-30 |
| 🎬 Actividad | ¿Ha mostrado interés? (demo > descarga > visita > email) | 0-40 |

**Temperatura:** 🔥 Caliente (70-100) · 🌡️ Templado (40-69) · ❄️ Frío (0-39).
Además **reutiliza el validador** para avisar si un lead caliente **no es contactable**.

```bash
python lead_scorer.py leads_limpios.csv   # genera leads_priorizados.csv + informe_leads.html
```

---

## 🗓️ Reparto en equipo (`reparto.py`) — el ritmo semanal

Organiza a un equipo de ventas durante la semana, en dos modos:

```bash
python reparto.py                          # 🟢 LUNES: reparte los leads entre el equipo
python reparto.py balance                  # 🔴 VIERNES: balance de lo que trabajó cada uno
```

- **Lunes:** reparte equilibrando **temperatura** (nadie acapara los calientes) y **carga**
  (según la capacidad de cada comercial, definida en `equipo.csv`). Genera la lista de cada uno.
- **Viernes:** cruza el reparto con el CRM y muestra por comercial cuántos leads **trabajó**,
  cuántos **cerró** y —lo más importante— cuántos **🔥 calientes quedaron sin tocar**.

---

## 🛣️ Roadmap (evolución a proceso productivo)

- [ ] **Origen automático de datos** (formulario web / API en vez de CSV manual).
- [ ] **Empuje directo vía Salesforce Bulk API** (sin subir el CSV a mano).
- [ ] **Ejecución programada** (diaria) para mantener el CRM siempre limpio.

---

## ▶️ Cómo usarlo

```bash
python validador.py
```

Requisitos: **Python 3** (no necesita instalar nada más). Edita `contactos.csv`
con tus datos (`nombre,email,telefono,empresa`) y ejecuta.

---

## 🛠️ Tecnologías y conceptos

- **Python 3** — sin dependencias externas
- Módulos estándar `csv`, `hashlib`, `html`, `datetime`, `os`, `sys`
- **Código reutilizable**: `crm.py` importa el núcleo de `validador.py`
- Funciones con responsabilidad única · condicionales · bucles · gestión de archivos
- Generación de **CSV, HTML y reportes de texto** · mini-CRM por línea de comandos

---

## ⚠️ Limitaciones conocidas

- La validación de email comprueba el **formato**, no que el buzón o el dominio existan
  realmente (eso requeriría verificación SMTP / API externa).

---

## 👤 Autor

**Álvaro Utazu Lázaro** · En formación como AI Engineer
Proyecto desarrollado con [Claude Code](https://claude.ai) (Anthropic) como parte del
programa de aprendizaje práctico de IA.

---

*De una lista de contactos sucia a una base de leads priorizada y lista para vender.*
