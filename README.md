# 📇 Validador de Contactos Empresariales

> Script Python que **limpia y valida bases de datos de contactos** en segundos — eliminando emails inválidos, teléfonos incorrectos y registros duplicados de forma automática.

---

## 🚀 Demo rápida

```
🚀 Iniciando validador de contactos empresariales...

📥 Se han leído 10 contactos del archivo.

✅ Ana García: contacto válido
✅ Luis Martínez: contacto válido
❌ María López: email incorrecto
❌ Carlos Ruiz: email incorrecto
❌ Elena Sánchez: teléfono incorrecto
❌ Javier Moreno: teléfono incorrecto

📊 INFORME FINAL
✅ Válidos: 6  |  ❌ Inválidos: 4  |  🔁 Duplicados: 1
```

---

## ❗ El problema que resuelve

Cualquier empresa que tenga un **departamento de ventas, marketing o RRHH** acumula bases de datos de contactos con errores:

| Problema habitual | Consecuencia real |
|---|---|
| Emails sin `@` o mal formateados | Campañas de email que fallan al enviarse |
| Teléfonos con letras o demasiado cortos | Llamadas y SMS que no llegan |
| Contactos duplicados en el CRM | Clientes que reciben el mismo mensaje dos veces |
| Revisión manual de miles de filas | 3–4 horas de trabajo repetitivo cada semana |

**Este script convierte esas horas en segundos.**

---

## ⚙️ Funciones del script

### `validar_email(email)`
Comprueba que el email tenga el formato correcto: debe contener `@` y un punto después del `@`.
```python
validar_email("usuario@empresa.com")  # True
validar_email("usuarioempresa.com")   # False — falta @
validar_email("usuario@correo")       # False — falta punto en dominio
```

### `validar_telefono(telefono)`
Verifica que el teléfono solo contenga dígitos y tenga entre 9 y 15 caracteres.
```python
validar_telefono("612345678")   # True
validar_telefono("6123ABC78")   # False — contiene letras
validar_telefono("12345")       # False — demasiado corto
```

### `detectar_duplicados(lista_contactos)`
Recorre la lista completa y devuelve los nombres de contactos que aparecen más de una vez con los mismos datos.
```python
detectar_duplicados(contactos)  # ['Ana García']
```

### `generar_informe(validos, invalidos, duplicados)`
Imprime un resumen visual al final con el conteo de cada categoría y guarda los resultados en archivos de texto.

---

## 📂 Estructura del proyecto

```
validador-contactos/
│
├── validador.py       # Script principal
├── contactos.csv      # Datos de entrada (tu lista de contactos)
├── validos.txt        # Salida generada automáticamente (no versionada)
├── invalidos.txt      # Salida generada automáticamente (no versionada)
├── duplicados.txt     # Salida generada automáticamente (no versionada)
└── README.md          # Este documento
```

---

## ▶️ Cómo usarlo

**1. Clona el repositorio**
```bash
git clone https://github.com/tu-usuario/validador-contactos.git
cd validador-contactos
```

**2. Prepara tu archivo de contactos**

Edita `contactos.csv` con tus propios datos. El formato es:
```
nombre,email,telefono,empresa
Juan Pérez,juan@empresa.com,612345678,Mi Empresa SL
```

**3. Ejecuta el script**
```bash
python validador.py
```

**4. Revisa los resultados**

Los archivos `validos.txt` e `invalidos.txt` se generan automáticamente con el resultado de la validación.

---

## 🏢 Casos de uso reales

- **Equipo de ventas**: limpia los leads exportados del CRM antes de una campaña de email marketing
- **Departamento de RRHH**: valida la base de datos de candidatos antes de enviar comunicaciones masivas
- **Marketing**: sanea la lista de contactos antes de importarla a Mailchimp, HubSpot o Salesforce
- **Administración**: audita periódicamente la base de datos de proveedores o clientes

---

## 🛠️ Tecnologías y conceptos

- **Python 3** — sin dependencias externas
- **Módulo `csv`** — lectura de datos reales desde archivo
- **Funciones** (`def`) — lógica separada por responsabilidad
- **Condicionales** (`if/elif/else`) — clasificación de cada contacto
- **Bucles** (`for`) — procesamiento automático de toda la lista
- **Gestión de archivos** (`open`, `write`) — generación de informes

---

## 📈 Escalabilidad

Este script está diseñado como punto de partida. Se puede extender fácilmente para:

- Validar también el campo `empresa` (que no esté vacío)
- Exportar los resultados en CSV en lugar de TXT
- Conectarse directamente a un CRM vía API
- Procesar archivos con miles o decenas de miles de contactos
- Añadir validación de formato de DNI o código postal

---

## ⚠️ Limitaciones conocidas

- La validación de email es **básica** (comprueba `@` y un punto en el dominio); no verifica que el dominio exista realmente.
- El campo `empresa` no se valida todavía.

---

## 👤 Autor

**Álvaro Utazu Lázaro** · En formación como AI Engineer  
Proyecto desarrollado con [Claude Code](https://claude.ai) (Anthropic) como parte del programa de aprendizaje práctico de IA.

---

*¿Tienes una base de datos que necesita limpiarse? Este script es el punto de partida.*
