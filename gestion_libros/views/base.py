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
    
    context = {
        'prestamos': prestamos,
        'query': query,
        'filtro_tipo': filtro_tipo,
        'estado_filtro': estado_filtro,
        'total_resultados': prestamos.count()
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
                messages.error(request, 
                    f'❌ <strong>No se puede realizar el préstamo</strong><br>'
                    f'El socio <strong>{socio.nombre}</strong> (Nº {socio.numero_socio}) no está activo.<br>'
                    f'<small>Contacta al administrador para reactivar la cuenta del socio.</small>'
                )
                return redirect('realizar_prestamo')
            
            if socio.tiene_multas_pendientes():
                messages.error(request, 
                    f'❌ <strong>No se puede realizar el préstamo</strong><br>'
                    f'El socio <strong>{socio.nombre}</strong> tiene multas pendientes por <strong>${socio.monto_total_multas()}</strong>.<br>'
                    f'<small>El socio debe pagar las multas antes de poder realizar nuevos préstamos.</small>'
                )
                return redirect('realizar_prestamo')
            
            if not ejemplar.esta_disponible():
                messages.error(request, 
                    f'❌ <strong>No se puede realizar el préstamo</strong><br>'
                    f'El ejemplar <strong>{ejemplar.codigo_ejemplar}</strong> no está disponible.<br>'
                    f'<small>Estado actual: <strong>{ejemplar.get_estado_display()}</strong></small>'
                )
                return redirect('realizar_prestamo')
            
            # Obtener configuración
            config = obtener_configuracion()
            
            # Verificar límite de préstamos
            if socio.prestamos_activos().count() >= config.max_prestamos_simultaneos:
                messages.error(request, 
                    f'❌ <strong>Límite de préstamos alcanzado</strong><br>'
                    f'El socio <strong>{socio.nombre}</strong> ya tiene <strong>{config.max_prestamos_simultaneos} préstamos activos</strong>.<br>'
                    f'<small>Debe devolver algún libro antes de poder realizar un nuevo préstamo.</small>'
                )
                return redirect('realizar_prestamo')
            
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
            
            messages.success(request, 
                f'✅ <strong>¡Préstamo realizado exitosamente!</strong><br>'
                f'<strong>Socio:</strong> {socio.nombre} (Nº {socio.numero_socio})<br>'
                f'<strong>Libro:</strong> {ejemplar.libro.titulo}<br>'
                f'<strong>Ejemplar:</strong> {ejemplar.codigo_ejemplar}<br>'
                f'<strong>Fecha de devolución:</strong> {fecha_devolucion.strftime("%d/%m/%Y")}<br>'
                f'<small>El ejemplar ha sido marcado como prestado y está disponible para consulta.</small>'
            )
            return redirect('listar_prestamos')
            
        except Socio.DoesNotExist:
            messages.error(request, 
                f'❌ <strong>Socio no encontrado</strong><br>'
                f'No existe un socio registrado con el DNI <strong>{socio_id}</strong>.<br>'
                f'<small>Verifica el número de DNI o registra un nuevo socio.</small>'
            )
        except Ejemplar.DoesNotExist:
            messages.error(request, 
                f'❌ <strong>Ejemplar no encontrado</strong><br>'
                f'No existe un ejemplar con el código <strong>{ejemplar_id}</strong>.<br>'
                f'<small>Verifica el código del ejemplar o registra un nuevo ejemplar.</small>'
            )
        except Exception as e:
            messages.error(request, 
                f'❌ <strong>Error inesperado</strong><br>'
                f'No se pudo realizar el préstamo: <strong>{str(e)}</strong><br>'
                f'<small>Contacta al administrador del sistema.</small>'
            )
        
        return redirect('realizar_prestamo')
    
    # GET - Mostrar formulario
    socios_activos = Socio.objects.filter(activo=True)
    ejemplares_disponibles = Ejemplar.objects.filter(estado='disponible')
    
    return render(request, 'gestion_libros/realizar_prestamo.html', {
        'socios': socios_activos,
        'ejemplares': ejemplares_disponibles
    })


# ============================================================
# PROCESO 2: DEVOLUCIÓN DE UN LIBRO
# ============================================================
@login_required
def devolver_libro(request, prestamo_id):
    """
    Proceso de devolución de un libro:
    1. Cerrar el préstamo
    2. Cambiar estado del ejemplar a 'disponible'
    3. Verificar estado físico (si hay daño, crear multa)
    """
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    
    if request.method == 'POST':
        estado_fisico = request.POST.get('estado_fisico')  # 'bueno', 'dañado', 'perdido'
        
        # Registrar fecha de devolución
        prestamo.fecha_devolucion_real = timezone.now()
        prestamo.save()
        
        config = obtener_configuracion()
        
        # Procesar según estado físico
        if estado_fisico == 'bueno':
            # Cambiar estado del ejemplar a disponible
            prestamo.ejemplar.estado = 'disponible'
            prestamo.ejemplar.save()
            
            # Verificar si hay retraso
            if prestamo.tiene_retraso():
                dias_retraso = prestamo.dias_retraso()
                monto_multa = config.calcular_multa_retraso(dias_retraso)
                
                Multa.objects.create(
                    socio=prestamo.socio,
                    prestamo=prestamo,
                    monto=monto_multa,
                    motivo='retraso',
                    descripcion=f'Retraso de {dias_retraso} días en la devolución'
                )
                
                messages.warning(request, 
                    f'⚠️ <strong>Libro devuelto con retraso</strong><br>'
                    f'<strong>Multa aplicada:</strong> ${monto_multa}<br>'
                    f'<strong>Días de retraso:</strong> {dias_retraso} día{dias_retraso|pluralize}<br>'
                    f'<small>La multa ha sido registrada en el sistema. El socio debe pagarla antes de realizar nuevos préstamos.</small>'
                )
            else:
                messages.success(request, 
                    f'✅ <strong>¡Libro devuelto exitosamente!</strong><br>'
                    f'<strong>Socio:</strong> {prestamo.socio.nombre}<br>'
                    f'<strong>Libro:</strong> {prestamo.ejemplar.libro.titulo}<br>'
                    f'<strong>Ejemplar:</strong> {prestamo.ejemplar.codigo_ejemplar}<br>'
                    f'<small>El ejemplar ha sido marcado como disponible y está listo para nuevos préstamos.</small>'
                )
        
        elif estado_fisico == 'dañado':
            # Cambiar estado a mantenimiento
            prestamo.ejemplar.estado = 'mantenimiento'
            prestamo.ejemplar.save()
            
            # Crear multa por daño
            Multa.objects.create(
                socio=prestamo.socio,
                prestamo=prestamo,
                monto=config.multa_daño_libro,
                motivo='daño',
                descripcion='Libro devuelto con daños'
            )
            
            messages.error(request, 
                f'❌ <strong>Libro devuelto con daños</strong><br>'
                f'<strong>Multa aplicada:</strong> ${config.multa_daño_libro}<br>'
                f'<strong>Estado del ejemplar:</strong> En mantenimiento<br>'
                f'<small>El ejemplar ha sido enviado a mantenimiento. La multa ha sido registrada en el sistema.</small>'
            )
        
        elif estado_fisico == 'perdido':
            # Cambiar estado a perdido
            prestamo.ejemplar.estado = 'perdido'
            prestamo.ejemplar.save()
            
            # Crear multa por pérdida
            Multa.objects.create(
                socio=prestamo.socio,
                prestamo=prestamo,
                monto=config.multa_perdida_libro,
                motivo='perdida',
                descripcion='Libro perdido'
            )
            
            messages.error(request, 
                f'❌ <strong>Libro reportado como perdido</strong><br>'
                f'<strong>Multa aplicada:</strong> ${config.multa_perdida_libro}<br>'
                f'<strong>Estado del ejemplar:</strong> Perdido<br>'
                f'<small>El ejemplar ha sido marcado como perdido. La multa ha sido registrada en el sistema.</small>'
            )
        
        return redirect('listar_prestamos')
    
    return render(request, 'gestion_libros/devolver_libro.html', {'prestamo': prestamo})


# ============================================================
# PROCESO 3: ALTA DE UN SOCIO NUEVO
# ============================================================
@login_required
def registrar_socio(request):
    """
    Proceso de alta de un nuevo socio:
    1. Validar que el DNI no exista
    2. Generar número de socio único
    3. Registrar el socio
    """
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        
        # Validar que el DNI no exista
        if Socio.objects.filter(dni=dni).exists():
            messages.error(request, 
                f'❌ <strong>DNI ya registrado</strong><br>'
                f'Ya existe un socio registrado con el DNI <strong>{dni}</strong>.<br>'
                f'<small>Verifica el número de DNI o busca el socio existente en la lista.</small>'
            )
            return redirect('registrar_socio')
        
        # Generar número de socio (formato: SOC-YYYY-NNNN)
        año_actual = timezone.now().year
        ultimo_socio = Socio.objects.filter(
            numero_socio__startswith=f'SOC-{año_actual}'
        ).order_by('-numero_socio').first()
        
        if ultimo_socio:
            ultimo_numero = int(ultimo_socio.numero_socio.split('-')[-1])
            nuevo_numero = f'SOC-{año_actual}-{(ultimo_numero + 1):04d}'
        else:
            nuevo_numero = f'SOC-{año_actual}-0001'
        
        # Crear el socio
        try:
            socio = Socio.objects.create(
                dni=dni,
                numero_socio=nuevo_numero,
                nombre=nombre,
                email=email,
                telefono=telefono,
                direccion=direccion
            )
            
            messages.success(request, 
                f'✅ <strong>¡Socio registrado exitosamente!</strong><br>'
                f'<strong>Nombre:</strong> {socio.nombre}<br>'
                f'<strong>DNI:</strong> {socio.dni}<br>'
                f'<strong>Número de socio:</strong> <code>{nuevo_numero}</code><br>'
                f'<strong>Email:</strong> {socio.email or "No proporcionado"}<br>'
                f'<strong>Teléfono:</strong> {socio.telefono or "No proporcionado"}<br>'
                f'<small>El socio ya puede realizar préstamos en la biblioteca.</small>'
            )
            return redirect('listar_socios')
            
        except Exception as e:
            messages.error(request, 
                f'❌ <strong>Error al registrar el socio</strong><br>'
                f'No se pudo completar el registro: <strong>{str(e)}</strong><br>'
                f'<small>Verifica los datos ingresados y contacta al administrador si el problema persiste.</small>'
            )
            return redirect('registrar_socio')
    
    return render(request, 'gestion_libros/registrar_socio.html')


# ============================================================
# PROCESO 4: GESTIÓN DE MULTAS
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
    """
    Marca una multa como pagada
    """
    multa = get_object_or_404(Multa, id=multa_id)
    
    if request.method == 'POST':
        if multa.pagada:
            messages.warning(request, 
                f'⚠️ <strong>Multa ya pagada</strong><br>'
                f'Esta multa ya fue marcada como pagada el {multa.fecha_pago.strftime("%d/%m/%Y")}.<br>'
                f'<small>No se requiere ninguna acción adicional.</small>'
            )
        else:
            multa.marcar_como_pagada()
            messages.success(request, 
                f'✅ <strong>¡Multa pagada exitosamente!</strong><br>'
                f'<strong>Socio:</strong> {multa.socio.nombre}<br>'
                f'<strong>Monto:</strong> ${multa.monto}<br>'
                f'<strong>Motivo:</strong> {multa.get_motivo_display()}<br>'
                f'<small>El socio ahora puede realizar nuevos préstamos si no tiene otras multas pendientes.</small>'
            )
        
        return redirect('listar_multas')
    
    return render(request, 'gestion_libros/pagar_multa.html', {'multa': multa})