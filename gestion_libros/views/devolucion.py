"""
Vistas para el proceso de devolución de libros.
PROCESO 2: Devolución de un Libro
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from ..models import Prestamo, Multa
from ..singleton import obtener_configuracion
from django.contrib.auth.decorators import login_required


@login_required
def devolver_libro(request, prestamo_id):
    """
    Proceso de devolución de un libro:
    1. Cerrar el préstamo (registrar fecha_devolucion_real)
    2. Cambiar estado del ejemplar según condición física
    3. Aplicar multas si corresponde (retraso, daño, pérdida)
    """
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    
    # Verificar que el préstamo esté activo
    if not prestamo.esta_activo():
        messages.warning(request, 'Este préstamo ya fue devuelto anteriormente.')
        return redirect('listar_prestamos')
    
    if request.method == 'POST':
        estado_fisico = request.POST.get('estado_fisico')  # 'bueno', 'dañado', 'perdido'
        observaciones = request.POST.get('observaciones', '')
        
        # Registrar fecha de devolución real
        prestamo.fecha_devolucion_real = timezone.now()
        if observaciones:
            prestamo.observaciones = observaciones
        prestamo.save()
        
        # Obtener configuración singleton
        config = obtener_configuracion()
        
        # CASO 1: Libro en buen estado
        if estado_fisico == 'bueno':
            # Cambiar estado del ejemplar a disponible
            prestamo.ejemplar.estado = 'disponible'
            prestamo.ejemplar.save()
            
            # Verificar si hay retraso
            if prestamo.tiene_retraso():
                dias_retraso = prestamo.dias_retraso()
                monto_multa = config.calcular_multa_retraso(dias_retraso)
                
                # Crear multa por retraso
                Multa.objects.create(
                    socio=prestamo.socio,
                    prestamo=prestamo,
                    monto=monto_multa,
                    motivo='retraso',
                    descripcion=f'Retraso de {dias_retraso} días en la devolución del libro "{prestamo.ejemplar.libro.titulo}"'
                )
                
                messages.warning(
                    request, 
                    f'⚠ Libro devuelto con retraso.<br>'
                    f'Días de retraso: {dias_retraso}<br>'
                    f'Multa aplicada: ${monto_multa}'
                )
            else:
                messages.success(request, f'✓ Libro "{prestamo.ejemplar.libro.titulo}" devuelto exitosamente a tiempo.')
        
        # CASO 2: Libro dañado
        elif estado_fisico == 'dañado':
            # Obtener monto de multa por daño del formulario
            monto_daño_str = request.POST.get('monto_daño')
            if not monto_daño_str or float(monto_daño_str) <= 0:
                messages.error(request, 'Debe ingresar un monto válido para la multa por daño.')
                return render(request, 'gestion_libros/devolver_libro.html', {
                    'prestamo': prestamo,
                    'monto_daño': monto_daño_str
                })
            
            monto_daño = Decimal(monto_daño_str)
            
            # Cambiar estado a mantenimiento
            prestamo.ejemplar.estado = 'mantenimiento'
            prestamo.ejemplar.observaciones = f'Dañado en devolución - {timezone.now().date()}'
            prestamo.ejemplar.save()
            
            # Crear multa por daño con el monto ingresado por el bibliotecario
            Multa.objects.create(
                socio=prestamo.socio,
                prestamo=prestamo,
                monto=monto_daño,
                motivo='daño',
                descripcion=f'Libro "{prestamo.ejemplar.libro.titulo}" devuelto con daños. {observaciones}'
            )
            
            # Verificar también retraso
            multa_retraso = 0
            if prestamo.tiene_retraso():
                dias_retraso = prestamo.dias_retraso()
                multa_retraso = config.calcular_multa_retraso(dias_retraso)
                
                Multa.objects.create(
                    socio=prestamo.socio,
                    prestamo=prestamo,
                    monto=multa_retraso,
                    motivo='retraso',
                    descripcion=f'Retraso de {dias_retraso} días'
                )
            
            total_multas = monto_daño + multa_retraso
            messages.error(
                request, 
                f'✗ Libro devuelto con daños.<br>'
                f'Multa por daño: ${monto_daño}<br>'
                f'{"Multa por retraso: $" + str(multa_retraso) + "<br>" if multa_retraso > 0 else ""}'
                f'Total: ${total_multas}'
            )
        
        # CASO 3: Libro perdido
        elif estado_fisico == 'perdido':
            # Obtener monto de multa por pérdida del formulario
            monto_perdida_str = request.POST.get('monto_perdida')
            if not monto_perdida_str or float(monto_perdida_str) <= 0:
                messages.error(request, 'Debe ingresar un monto válido para la multa por pérdida.')
                return render(request, 'gestion_libros/devolver_libro.html', {
                    'prestamo': prestamo,
                    'monto_perdida': monto_perdida_str
                })
            
            monto_perdida = Decimal(monto_perdida_str)
            
            # Cambiar estado a perdido
            prestamo.ejemplar.estado = 'perdido'
            prestamo.ejemplar.observaciones = f'Reportado como perdido - {timezone.now().date()}'
            prestamo.ejemplar.save()
            
            # Crear multa por pérdida con el monto ingresado por el bibliotecario
            Multa.objects.create(
                socio=prestamo.socio,
                prestamo=prestamo,
                monto=monto_perdida,
                motivo='perdida',
                descripcion=f'Libro "{prestamo.ejemplar.libro.titulo}" reportado como perdido. {observaciones}'
            )
            
            messages.error(
                request, 
                f'✗ Libro reportado como perdido.<br>'
                f'Multa aplicada: ${monto_perdida}<br>'
                f'El socio debe pagar esta multa antes de realizar nuevos préstamos.'
            )
        
        return redirect('listar_prestamos')
    
    # Si es GET, redirigir
    return redirect('listar_prestamos')