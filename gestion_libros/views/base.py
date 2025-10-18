from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import models
from datetime import timedelta
from ..models import Libro, Ejemplar, Socio, Prestamo, Multa
from ..singleton import obtener_configuracion


def index(request):
    """Vista principal del sistema"""
    context = {
        'total_libros': Libro.objects.filter(activo=True).count(),
        'total_ejemplares': Ejemplar.objects.filter(activo=True).count(),
        'total_socios': Socio.objects.filter(activo=True).count(),
        'prestamos_activos': Prestamo.objects.filter(fecha_devolucion_real__isnull=True).count(),
        'ejemplares_disponibles': Ejemplar.objects.filter(estado='disponible', activo=True).count(),
        'multas_pendientes': Multa.objects.filter(pagada=False).count(),
        'monto_multas_pendientes': Multa.objects.filter(pagada=False).aggregate(
            total=models.Sum('monto'))['total'] or 0,
    }
    return render(request, 'gestion_libros/index.html', context)


@login_required
def listar_libros(request):
    """Lista todos los libros activos con funcionalidad de búsqueda"""
    libros_todos = Libro.objects.filter(activo=True)  # Para el select del modal
    libros = libros_todos  # Para la tabla
    query = request.GET.get('q', '').strip()
    filtro_tipo = request.GET.get('filtro', 'todos')
    
    if query:
        if filtro_tipo == 'isbn':
            libros = libros.filter(isbn__icontains=query)
        elif filtro_tipo == 'titulo':
            libros = libros.filter(titulo__icontains=query)
        elif filtro_tipo == 'autor':
            libros = libros.filter(autor__icontains=query)
        elif filtro_tipo == 'editorial':
            libros = libros.filter(editorial__icontains=query)
        else:  # 'todos' - búsqueda general
            libros = libros.filter(
                models.Q(isbn__icontains=query) |
                models.Q(titulo__icontains=query) |
                models.Q(autor__icontains=query) |
                models.Q(editorial__icontains=query)
            )
    
    context = {
        'libros': libros,  # Para la tabla (con filtros)
        'query': query,
        'filtro_tipo': filtro_tipo,
        'total_resultados': libros.count()
    }
    return render(request, 'gestion_libros/listar_libros.html', context)


@login_required
def listar_socios(request):
    """Lista todos los socios con funcionalidad de búsqueda"""
    socios = Socio.objects.all()
    query = request.GET.get('q', '').strip()
    filtro_tipo = request.GET.get('filtro', 'todos')
    estado_filtro = request.GET.get('estado', 'todos')
    
    if query:
        if filtro_tipo == 'dni':
            socios = socios.filter(dni__icontains=query)
        elif filtro_tipo == 'numero_socio':
            socios = socios.filter(numero_socio__icontains=query)
        elif filtro_tipo == 'nombre':
            socios = socios.filter(nombre__icontains=query)
        elif filtro_tipo == 'email':
            socios = socios.filter(email__icontains=query)
        else:  # 'todos' - búsqueda general
            socios = socios.filter(
                models.Q(dni__icontains=query) |
                models.Q(numero_socio__icontains=query) |
                models.Q(nombre__icontains=query) |
                models.Q(email__icontains=query)
            )
    
    if estado_filtro == 'activos':
        socios = socios.filter(activo=True)
    elif estado_filtro == 'inactivos':
        socios = socios.filter(activo=False)
    
    context = {
        'socios': socios,
        'query': query,
        'filtro_tipo': filtro_tipo,
        'estado_filtro': estado_filtro,
        'total_resultados': socios.count()
    }
    return render(request, 'gestion_libros/listar_socios.html', context)


@login_required
def listar_prestamos(request):
    """Lista todos los préstamos con funcionalidad de búsqueda"""
    prestamos = Prestamo.objects.all().order_by('-fecha_inicio')
    query = request.GET.get('q', '').strip()
    filtro_tipo = request.GET.get('filtro', 'todos')
    estado_filtro = request.GET.get('estado', 'todos')
    
    if query:
        if filtro_tipo == 'socio':
            prestamos = prestamos.filter(socio__nombre__icontains=query)
        elif filtro_tipo == 'libro':
            prestamos = prestamos.filter(ejemplar__libro__titulo__icontains=query)
        elif filtro_tipo == 'ejemplar':
            prestamos = prestamos.filter(ejemplar__codigo_ejemplar__icontains=query)
        elif filtro_tipo == 'isbn':
            prestamos = prestamos.filter(ejemplar__libro__isbn__icontains=query)
        else:  # 'todos' - búsqueda general
            prestamos = prestamos.filter(
                models.Q(socio__nombre__icontains=query) |
                models.Q(ejemplar__libro__titulo__icontains=query) |
                models.Q(ejemplar__codigo_ejemplar__icontains=query) |
                models.Q(ejemplar__libro__isbn__icontains=query)
            )
    
    if estado_filtro == 'activos':
        prestamos = prestamos.filter(fecha_devolucion_real__isnull=True)
    elif estado_filtro == 'devueltos':
        prestamos = prestamos.filter(fecha_devolucion_real__isnull=False)
    elif estado_filtro == 'retrasados':
        prestamos = prestamos.filter(
            fecha_devolucion_real__isnull=True,
            fecha_devolucion_prevista__lt=timezone.now().date()
        )
    
    # Datos para modales
    socios_activos = Socio.objects.filter(activo=True)
    ejemplares_disponibles = Ejemplar.objects.filter(estado='disponible', activo=True).select_related('libro')
    
    context = {
        'prestamos': prestamos,
        'query': query,
        'filtro_tipo': filtro_tipo,
        'estado_filtro': estado_filtro,
        'total_resultados': prestamos.count(),
        'socios': socios_activos,
        'ejemplares': ejemplares_disponibles,
    }
    return render(request, 'gestion_libros/listar_prestamos.html', context)


# ============================================================
# PROCESO 1: PRÉSTAMO DE UN LIBRO
# ============================================================
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
            
            # Validaciones
            if not socio.activo:
                messages.error(request, f'❌ Socio {socio.nombre} no está activo.')
                return redirect('listar_prestamos')
            
            if socio.tiene_multas_pendientes():
                messages.error(request, f'❌ {socio.nombre} tiene multas pendientes por ${socio.monto_total_multas()}.')
                return redirect('listar_prestamos')
            
            if not ejemplar.esta_disponible():
                messages.error(request, f'❌ Ejemplar {ejemplar.codigo_ejemplar} no disponible ({ejemplar.get_estado_display()}).')
                return redirect('listar_prestamos')
            
            # Obtener configuración
            config = obtener_configuracion()
            
            # Verificar límite de préstamos
            if socio.prestamos_activos().count() >= config.max_prestamos_simultaneos:
                messages.error(request, f'❌ {socio.nombre} tiene {config.max_prestamos_simultaneos} préstamos activos.')
                return redirect('listar_prestamos')
            
            # Crear el préstamo
            fecha_devolucion = timezone.now().date() + timedelta(days=config.dias_prestamo_default)
            prestamo = Prestamo.objects.create(
                socio=socio,
                ejemplar=ejemplar,
                fecha_devolucion_prevista=fecha_devolucion
            )
            
            # Cambiar estado del ejemplar
            ejemplar.estado = 'prestado'
            ejemplar.save()
            
            messages.success(request, f'✅ Préstamo registrado: {ejemplar.libro.titulo} a {socio.nombre}. Devolución: {fecha_devolucion.strftime("%d/%m/%Y")}')
            return redirect('listar_prestamos')
            
        except Socio.DoesNotExist:
            messages.error(request, f'❌ Socio con DNI {socio_id} no encontrado.')
        except Ejemplar.DoesNotExist:
            messages.error(request, f'❌ Ejemplar {ejemplar_id} no encontrado.')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
        
        return redirect('listar_prestamos')
    
    # Si es GET, redirigir
    return redirect('listar_prestamos')


# ============================================================
# GESTIÓN DE MULTAS
# ============================================================
@login_required
def listar_multas(request):
    """
    Lista todas las multas del sistema con filtros
    """
    multas = Multa.objects.all().order_by('-fecha')
    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', 'todos')
    
    if query:
        multas = multas.filter(
            models.Q(socio__nombre__icontains=query) |
            models.Q(socio__dni__icontains=query) |
            models.Q(socio__numero_socio__icontains=query)
        )
    
    if estado_filtro == 'pendientes':
        multas = multas.filter(pagada=False)
    elif estado_filtro == 'pagadas':
        multas = multas.filter(pagada=True)
    
    context = {
        'multas': multas,
        'query': query,
        'estado_filtro': estado_filtro,
        'total_resultados': multas.count(),
        'total_pendiente': multas.filter(pagada=False).aggregate(
            total=models.Sum('monto'))['total'] or 0
    }
    return render(request, 'gestion_libros/listar_multas.html', context)


@login_required
def pagar_multa(request, multa_id):
    """Marca una multa como pagada (solo POST)"""
    multa = get_object_or_404(Multa, id=multa_id)
    
    if request.method != 'POST':
        return redirect('listar_multas')
    
    if multa.pagada:
        messages.warning(request, f'⚠️ Esta multa ya fue pagada el {multa.fecha_pago.strftime("%d/%m/%Y")}.')
    else:
        multa.marcar_como_pagada()
        messages.success(request, f'✅ Multa de ${multa.monto} pagada. {multa.socio.nombre} puede hacer préstamos.')
    
    return redirect('listar_multas')