# Proyecto: Sistema de Gestión de Biblioteca (2do Parcial)

Este proyecto implementa un sistema básico de gestión para una biblioteca utilizando **Django** y sigue un enfoque de diseño centrado en patrones de arquitectura y buenas prácticas.

## 1. Contexto y Requisitos Funcionales

El objetivo es gestionar libros, ejemplares, socios, préstamos y multas, implementando la lógica de los tres procesos principales definidos en la actividad.

### Entidades Clave (Modelo de Datos)

| Entidad | Atributos Clave | Relaciones |
| :--- | :--- | :--- |
| **Libro** | `titulo`, `autor`, **`ISBN` (Unique)** | 1:N con Ejemplar |
| **Ejemplar** | `libro_isbn`, `estado` (disponible/prestado) | 0..1 con Préstamo |
| **Socio** | **`dni` (Unique)**, `nombre`, `numero_socio` | 1:N con Préstamo, 1:N con Multa |
| **Prestamo** | `fechalnicio`, `fechaDevolucionPrevista`, `fechaDevolucionReal` | N:1 con Socio, N:1 con Ejemplar, 0..1 con Multa |
| **Multa** | `monto`, `motivo`, `fecha` | N:1 con Socio, N:1 con Préstamo |

### Procesos Implementados (Vistas - Controlador)

1.  **Préstamo de un Libro:**
    * Verificar si el libro está disponible (Ejemplar en estado 'disponible').
    * Registrar el `Prestamo` con `fechaDevolucionPrevista` (ej. 15 días).
    * Cambiar el estado del `Ejemplar` a 'prestado'.
2.  **Devolución de un Libro:**
    * Cerrar el `Prestamo` (asignar `fechaDevolucionReal`).
    * Cambiar el estado del `Ejemplar` a 'disponible'.
    * **Verificar estado físico:** Si el libro está dañado, se registra una `Multa` al `Socio`.
3.  **Alta de un Socio Nuevo:**
    * Validar que el `DNI` no exista (garantizado por `unique=True` en el modelo).
    * Registrar el nuevo `Socio` y asignar un `numero_socio`.

---

## 2. Arquitectura y Patrones de Diseño (Parte 1)

### Patrón de Arquitectura
* **Modelo-Vista-Controlador (MVC):** Utilizamos la implementación de Django (Modelo-Template-Vista o MTV), que separa la lógica del negocio (`views.py`) de los datos (`models.py`) y la presentación (`templates/`).

### Patrones de Diseño Aplicados (Requisito Académico)

| Tipo | Patrón | Justificación y Aplicación en el Proyecto |
| :--- | :--- | :--- |
| **Creacional** | **Singleton** | Se utiliza para la clase `ConfiguracionBiblioteca` (`singleton.py`) para asegurar que solo exista **una instancia** que gestione los parámetros globales (como la `tasa_multa_diaria = 0.50`). |
| **Estructural** | **Adapter** | *Propuesto:* Se podría usar para integrar una futura API externa de libros (ej. Google Books) con la interfaz interna del modelo `Libro`. |
| **Comportamiento** | **Observer** | *Propuesto:* Se podría usar para notificar automáticamente al `Socio` (Observer) cuando el estado de un `Libro` que solicitó cambia a 'disponible' (Subject). |

---

## 3. Stack Tecnológico y Configuración

### Stack
| Componente | Nombre | Versión |
| :--- | :--- | :--- |
| Backend | Python + Django | Python 3.x, Django 4.2 LTS |
| Frontend (Prototipo) | HTML + Bootstrap | Bootstrap 5.3 |
| **Base de Datos** | **SQLite3** | *¡Selección final por simplicidad!* |
| Control de Versiones | Git | 2.x |

## **4. Seguridad Adicional: Autenticación (Login/Logout)**

Aunque no fue un requisito funcional explícito, la aplicación debe garantizar que solo usuarios autorizados (el bibliotecario) puedan realizar transacciones críticas.

### Patrón y Lógica Implementada
* **Mecanismo:** Se utiliza el sistema de autenticación por defecto de Django (`django.contrib.auth`).
* **Controlador Protegido:** Todas las vistas de transacción (Préstamo, Devolución, Alta de Socio) deben estar protegidas usando el decorador **`@login_required`** de Django.

### Requerimientos de Código

| Componente | Archivo | Acción Necesaria |
| :--- | :--- | :--- |
| **URLs de Auth** | `biblioteca_project/urls.py` | Incluir las rutas de Django Auth: `path('accounts/', include('django.contrib.auth.urls'))`. |
| **Configuración** | `settings.py` | Definir las redirecciones: `LOGIN_REDIRECT_URL = '/'` y `LOGOUT_REDIRECT_URL = '/'`. |
| **Vistas Protegidas** | `gestion_libros/views.py` | Aplicar `@login_required` a las funciones `registrar_socio`, `registrar_prestamo`, y `procesar_devolucion`. |
| **Superusuario** | `Terminal` | Recordar usar `python manage.py createsuperuser` para poder iniciar sesión y probar la aplicación. |

### Requerimientos (`requirements.txt`)

El proyecto solo requiere dependencias mínimas para funcionar con SQLite:

Django~=4.2.0
requests.

### **Actualización de Dependencias**

Para actualizar las dependencias:
```bash
pip list --outdated
pip install --upgrade Django reportlab
pip freeze > requirements.txt