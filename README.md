# 🎯 Validador y Enriquecedor de Leads Comerciales

> Script Python que convierte una lista de contactos **"sucia"** en una base de datos
> **limpia, puntuada y lista para importar a Salesforce** — en segundos y sin librerías
> externas (solo Python estándar).

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
| `normalizar_email/telefono/texto` | Limpian el dato *solo para comparar* |
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
- Módulos estándar `csv` y `hashlib`
- Funciones con responsabilidad única · condicionales · bucles · gestión de archivos
- Generación de **CSV, HTML y reportes de texto**

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
