"""
Vistas para el proceso de préstamo de libros.
PROCESO 1: Préstamo de un Libro
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from ..models import Socio, Ejemplar, Prestamo
from ..singleton import obtener_configuracion
from django.contrib.auth.decorators import login_required


@login_required
def realizar_prestamo(request):
    """
    PROCESO 1: Préstamo de un Libro (según diagrama de actividad)
    
    Pasos del proceso:
    1. Validar que el socio esté activo
    2. Verificar que no tenga multas pendientes
    3. Verificar que el ejemplar esté disponible
    4. Verificar que el socio no exceda el límite de préstamos simultáneos
    5. Crear el préstamo con fecha de devolución calculada
    6. Cambiar el estado del ejemplar a 'prestado'
    """
    if request.method == 'POST':
        socio_id = request.POST.get('socio_id')
        ejemplar_id = request.POST.get('ejemplar_id')
        
        try:
            # Buscar el socio y ejemplar en la base de datos
            socio = Socio.objects.get(dni=socio_id)
            ejemplar = Ejemplar.objects.get(codigo_ejemplar=ejemplar_id)
            
            # === VALIDACIONES ANTES DE PRESTAR ===
            
            # Validación 1: Socio activo (no dado de baja)
            if not socio.activo:
                messages.error(request, f'El socio {socio.nombre} no está activo.')
                return redirect('realizar_prestamo')
            
            # Validación 2: Multas pendientes (regla de negocio importante)
            if socio.tiene_multas_pendientes():
                messages.error(
                    request, 
                    f'El socio {socio.nombre} tiene multas pendientes por ${socio.monto_total_multas()}. '
                    'Debe saldarlas antes de realizar un nuevo préstamo.'
                )
                return redirect('realizar_prestamo')
            
            # Validación 3: Ejemplar disponible (puede estar prestado, en mantenimiento, etc)
            if not ejemplar.esta_disponible():
                messages.error(
                    request, 
                    f'El ejemplar {ejemplar.codigo_ejemplar} no está disponible. '
                    f'Estado actual: {ejemplar.get_estado_display()}.'
                )
                return redirect('realizar_prestamo')
            
            # Obtener configuración global (Singleton) para las reglas de negocio
            config = obtener_configuracion()
            
            # Validación 4: Límite de préstamos simultáneos (ej: máximo 3 a la vez)
            prestamos_activos = socio.prestamos_activos().count()
            if prestamos_activos >= config.max_prestamos_simultaneos:
                messages.error(
                    request, 
                    f'El socio {socio.nombre} ya tiene {config.max_prestamos_simultaneos} préstamos activos. '
                    'Debe devolver al menos uno antes de realizar un nuevo préstamo.'
                )
                return redirect('realizar_prestamo')
            
            # === REGISTRAR EL PRÉSTAMO ===
            
            # Obtener los días de préstamo del formulario (por defecto 15 si no viene o es inválido)
            try:
                dias_prestamo = int(request.POST.get('dias_prestamo', config.dias_prestamo_default))
                # Validar que esté en un rango razonable (1 a 90 días)
                if dias_prestamo < 1 or dias_prestamo > 90:
                    dias_prestamo = config.dias_prestamo_default
            except (ValueError, TypeError):
                dias_prestamo = config.dias_prestamo_default
            
            # Calcular fecha de devolución (hoy + días indicados por el bibliotecario)
            fecha_devolucion = timezone.now().date() + timedelta(days=dias_prestamo)
            
            # Crear el registro del préstamo en la base de datos
            prestamo = Prestamo.objects.create(
                socio=socio,
                ejemplar=ejemplar,
                fecha_devolucion_prevista=fecha_devolucion
            )
            
            # Cambiar el estado del ejemplar a 'prestado' (ya no está disponible)
            ejemplar.estado = 'prestado'
            ejemplar.save()
            
            messages.success(
                request, 
                f'✓ Préstamo realizado exitosamente.<br>'
                f'Libro: {ejemplar.libro.titulo}<br>'
                f'Socio: {socio.nombre}<br>'
                f'Días de préstamo: {dias_prestamo}<br>'
                f'Devolución prevista: {fecha_devolucion.strftime("%d/%m/%Y")}'
            )
            return redirect('listar_prestamos')
            
        except Socio.DoesNotExist:
            messages.error(request, f'No existe un socio con DNI {socio_id}.')
        except Ejemplar.DoesNotExist:
            messages.error(request, f'No existe un ejemplar con código {ejemplar_id}.')
        except Exception as e:
            messages.error(request, f'Error al realizar el préstamo: {str(e)}')
        
        return redirect('realizar_prestamo')
    
    # Si es GET, redirigir a listar
    return redirect('listar_prestamos')