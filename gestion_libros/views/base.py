from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from ..models import Libro, Ejemplar, Socio, Prestamo, Multa
from ..singleton import obtener_configuracion


def index(request):
    """Vista principal del sistema"""
    context = {
        'total_libros': Libro.objects.count(),
        'total_ejemplares': Ejemplar.objects.count(),
        'total_socios': Socio.objects.filter(activo=True).count(),
        'prestamos_activos': Prestamo.objects.filter(fecha_devolucion_real__isnull=True).count(),
        'ejemplares_disponibles': Ejemplar.objects.filter(estado='disponible').count(),
    }
    return render(request, 'gestion_libros/index.html', context)


def listar_libros(request):
    """Lista todos los libros disponibles"""
    libros = Libro.objects.all()
    return render(request, 'gestion_libros/listar_libros.html', {'libros': libros})


def listar_socios(request):
    """Lista todos los socios"""
    socios = Socio.objects.all()
    return render(request, 'gestion_libros/listar_socios.html', {'socios': socios})


def listar_prestamos(request):
    """Lista todos los préstamos"""
    prestamos = Prestamo.objects.all().order_by('-fecha_inicio')
    return render(request, 'gestion_libros/listar_prestamos.html', {'prestamos': prestamos})


# ============================================================
# PROCESO 1: PRÉSTAMO DE UN LIBRO
# ============================================================
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
                messages.error(request, f'El socio {socio.nombre} no está activo.')
                return redirect('realizar_prestamo')
            
            if socio.tiene_multas_pendientes():
                messages.error(request, f'El socio {socio.nombre} tiene multas pendientes por ${socio.monto_total_multas()}.')
                return redirect('realizar_prestamo')
            
            if not ejemplar.esta_disponible():
                messages.error(request, f'El ejemplar {ejemplar.codigo_ejemplar} no está disponible (Estado: {ejemplar.get_estado_display()}).')
                return redirect('realizar_prestamo')
            
            # Obtener configuración
            config = obtener_configuracion()
            
            # Verificar límite de préstamos
            if socio.prestamos_activos().count() >= config.max_prestamos_simultaneos:
                messages.error(request, f'El socio {socio.nombre} ya tiene {config.max_prestamos_simultaneos} préstamos activos.')
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
            
            messages.success(request, f'Préstamo realizado exitosamente. Devolución prevista: {fecha_devolucion.strftime("%d/%m/%Y")}')
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
    ejemplares_disponibles = Ejemplar.objects.filter(estado='disponible')
    
    return render(request, 'gestion_libros/realizar_prestamo.html', {
        'socios': socios_activos,
        'ejemplares': ejemplares_disponibles
    })


# ============================================================
# PROCESO 2: DEVOLUCIÓN DE UN LIBRO
# ============================================================
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
                
                messages.warning(request, f'Libro devuelto. Multa por retraso: ${monto_multa} ({dias_retraso} días)')
            else:
                messages.success(request, 'Libro devuelto exitosamente a tiempo.')
        
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
            
            messages.error(request, f'Libro devuelto con daños. Multa aplicada: ${config.multa_daño_libro}')
        
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
            
            messages.error(request, f'Libro reportado como perdido. Multa aplicada: ${config.multa_perdida_libro}')
        
        return redirect('listar_prestamos')
    
    return render(request, 'gestion_libros/devolver_libro.html', {'prestamo': prestamo})


# ============================================================
# PROCESO 3: ALTA DE UN SOCIO NUEVO
# ============================================================
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
            messages.error(request, f'Ya existe un socio registrado con el DNI {dni}.')
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
            
            messages.success(request, f'Socio registrado exitosamente. Número de socio: {nuevo_numero}')
            return redirect('listar_socios')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el socio: {str(e)}')
            return redirect('registrar_socio')
    
    return render(request, 'gestion_libros/registrar_socio.html')