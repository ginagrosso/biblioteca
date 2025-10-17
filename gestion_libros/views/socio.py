"""
Vistas para la gestión de socios.
PROCESO 3: Alta de un Socio Nuevo
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from ..models import Socio
from django.contrib.auth.decorators import login_required


@login_required
def registrar_socio(request):
    """
    Proceso de alta de un nuevo socio:
    1. Validar que el DNI no exista (unique constraint)
    2. Generar número de socio único automáticamente
    3. Registrar el socio en la base de datos
    """
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        
        # Validaciones básicas
        if not dni or not nombre:
            messages.error(request, 'El DNI y el nombre son obligatorios.')
            return redirect('registrar_socio')
        
        # Validar que el DNI no exista
        if Socio.objects.filter(dni=dni).exists():
            messages.error(
                request, 
                f'Ya existe un socio registrado con el DNI {dni}. '
                'No se puede registrar el mismo DNI dos veces.'
            )
            return redirect('registrar_socio')
        
        # Generar número de socio único (formato: SOC-YYYY-NNNN)
        año_actual = timezone.now().year
        ultimo_socio = Socio.objects.filter(
            numero_socio__startswith=f'SOC-{año_actual}'
        ).order_by('-numero_socio').first()
        
        if ultimo_socio:
            # Extraer el número y sumar 1
            ultimo_numero = int(ultimo_socio.numero_socio.split('-')[-1])
            nuevo_numero = f'SOC-{año_actual}-{(ultimo_numero + 1):04d}'
        else:
            # Primer socio del año
            nuevo_numero = f'SOC-{año_actual}-0001'
        
        # Crear el socio
        try:
            socio = Socio.objects.create(
                dni=dni,
                numero_socio=nuevo_numero,
                nombre=nombre,
                email=email if email else None,
                telefono=telefono if telefono else None,
                direccion=direccion if direccion else None,
                activo=True
            )
            
            messages.success(
                request, 
                f'✓ Socio registrado exitosamente.<br>'
                f'Nombre: {socio.nombre}<br>'
                f'DNI: {socio.dni}<br>'
                f'Número de socio: {socio.numero_socio}'
            )
            return redirect('listar_socios')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el socio: {str(e)}')
            return redirect('registrar_socio')
    
    # GET - Mostrar formulario
    return render(request, 'gestion_libros/registrar_socio.html')