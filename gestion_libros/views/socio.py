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
    """Vista unificada para crear socio (solo POST)"""
    if request.method != 'POST':
        return redirect('listar_socios')
    
    dni = request.POST.get('dni', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    email = request.POST.get('email', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    direccion = request.POST.get('direccion', '').strip()
    
    if not dni or not nombre:
        messages.error(request, '❌ DNI y nombre son obligatorios.')
        return redirect('listar_socios')
    
    if Socio.objects.filter(dni=dni).exists():
        messages.error(request, f'❌ El DNI {dni} ya está registrado.')
        return redirect('listar_socios')
    
    # Generar número de socio único
    año_actual = timezone.now().year
    ultimo_socio = Socio.objects.filter(
        numero_socio__startswith=f'SOC-{año_actual}'
    ).order_by('-numero_socio').first()
    
    if ultimo_socio:
        ultimo_numero = int(ultimo_socio.numero_socio.split('-')[-1])
        nuevo_numero = f'SOC-{año_actual}-{(ultimo_numero + 1):04d}'
    else:
        nuevo_numero = f'SOC-{año_actual}-0001'
    
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
        messages.success(request, f'✅ Socio "{socio.nombre}" registrado ({socio.numero_socio}).')
    except Exception as e:
        messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('listar_socios')