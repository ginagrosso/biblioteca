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
    Proceso de préstamo de un libro:
    1. Verificar si el libro está disponible
    2. Registrar el préstamo
    3. Cambiar el estado del ejemplar a 'prestado'
    """
    if request.method == 'POST':
        socio_id = request.POST.get('socio_id')
        ejemplar_id = request.POST.get('ejemplar_id')
        
        try:
            socio = Socio.objects.get(dni=socio_id)
            ejemplar = Ejemplar.objects.get(codigo_ejemplar=ejemplar_id)
            
            # Validación 1: Socio activo
            if not socio.activo:
                messages.error(request, f'El socio {socio.nombre} no está activo.')
                return redirect('realizar_prestamo')
            
            # Validación 2: Multas pendientes
            if socio.tiene_multas_pendientes():
                messages.error(
                    request, 
                    f'El socio {socio.nombre} tiene multas pendientes por ${socio.monto_total_multas()}. '
                    'Debe saldarlas antes de realizar un nuevo préstamo.'
                )
                return redirect('realizar_prestamo')
            
            # Validación 3: Ejemplar disponible
            if not ejemplar.esta_disponible():
                messages.error(
                    request, 
                    f'El ejemplar {ejemplar.codigo_ejemplar} no está disponible. '
                    f'Estado actual: {ejemplar.get_estado_display()}.'
                )
                return redirect('realizar_prestamo')
            
            # Obtener configuración singleton
            config = obtener_configuracion()
            
            # Validación 4: Límite de préstamos simultáneos
            prestamos_activos = socio.prestamos_activos().count()
            if prestamos_activos >= config.max_prestamos_simultaneos:
                messages.error(
                    request, 
                    f'El socio {socio.nombre} ya tiene {config.max_prestamos_simultaneos} préstamos activos. '
                    'Debe devolver al menos uno antes de realizar un nuevo préstamo.'
                )
                return redirect('realizar_prestamo')
            
            # Crear el préstamo
            fecha_devolucion = timezone.now().date() + timedelta(days=config.dias_prestamo_default)
            prestamo = Prestamo.objects.create(
                socio=socio,
                ejemplar=ejemplar,
                fecha_devolucion_prevista=fecha_devolucion
            )
            
            # Cambiar estado del ejemplar a 'prestado'
            ejemplar.estado = 'prestado'
            ejemplar.save()
            
            messages.success(
                request, 
                f'✓ Préstamo realizado exitosamente.<br>'
                f'Libro: {ejemplar.libro.titulo}<br>'
                f'Socio: {socio.nombre}<br>'
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
    
    # GET - Mostrar formulario
    socios_activos = Socio.objects.filter(activo=True)
    ejemplares_disponibles = Ejemplar.objects.filter(estado='disponible').select_related('libro')
    
    return render(request, 'gestion_libros/realizar_prestamo.html', {
        'socios': socios_activos,
        'ejemplares': ejemplares_disponibles
    })