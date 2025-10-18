"""
Vistas para la gestión de libros y ejemplares.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Libro, Ejemplar
from django.contrib.auth.decorators import login_required


@login_required
def registrar_libro(request):
    """Vista unificada para crear/editar libro (solo POST)"""
    if request.method != 'POST':
        return redirect('listar_libros')
    
    isbn = request.POST.get('isbn', '').strip()
    titulo = request.POST.get('titulo', '').strip()
    autor = request.POST.get('autor', '').strip()
    editorial = request.POST.get('editorial', '').strip()
    año_publicacion = request.POST.get('año_publicacion', '').strip()
    
    if not isbn or not titulo or not autor:
        messages.error(request, '❌ ISBN, título y autor son obligatorios.')
        return redirect('listar_libros')
    
    # Validar que el ISBN no exista (solo al crear)
    if Libro.objects.filter(isbn=isbn).exists():
        messages.error(request, f'❌ El ISBN {isbn} ya está registrado.')
        return redirect('listar_libros')
    
    try:
        libro = Libro.objects.create(
            isbn=isbn,
            titulo=titulo,
            autor=autor,
            editorial=editorial if editorial else None,
            año_publicacion=int(año_publicacion) if año_publicacion else None
        )
        messages.success(request, f'✅ Libro "{libro.titulo}" registrado.')
    except Exception as e:
        messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('listar_libros')

@login_required
def registrar_ejemplar(request):
    """Vista unificada para crear ejemplar (solo POST)"""
    if request.method != 'POST':
        return redirect('listar_libros')
    
    libro_isbn = request.POST.get('libro_isbn', '').strip()
    observaciones = request.POST.get('observaciones', '').strip()
    
    if not libro_isbn:
        messages.error(request, '❌ Debes seleccionar un libro.')
        return redirect('listar_libros')
    
    try:
        libro = Libro.objects.get(isbn=libro_isbn, activo=True)
    except Libro.DoesNotExist:
        messages.error(request, f'❌ Libro con ISBN {libro_isbn} no encontrado.')
        return redirect('listar_libros')
    
    # Generar código automático
    ultimo_ejemplar = Ejemplar.objects.filter(
        libro=libro,
        codigo_ejemplar__startswith=f'EJ-{libro.isbn}-'
    ).order_by('-codigo_ejemplar').first()
    
    if ultimo_ejemplar:
        try:
            partes = ultimo_ejemplar.codigo_ejemplar.split('-')
            nuevo_numero = int(partes[-1]) + 1
        except (ValueError, IndexError):
            nuevo_numero = 1
    else:
        nuevo_numero = 1
    
    codigo_ejemplar = f'EJ-{libro.isbn}-{nuevo_numero:03d}'
    
    try:
        ejemplar = Ejemplar.objects.create(
            libro=libro,
            codigo_ejemplar=codigo_ejemplar,
            estado='disponible',
            observaciones=observaciones if observaciones else None
        )
        messages.success(request, f'✅ Ejemplar {ejemplar.codigo_ejemplar} registrado.')
    except Exception as e:
        messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('listar_libros')


@login_required
def editar_libro(request, isbn):
    """Vista simple para editar un libro (solo POST)"""
    libro = get_object_or_404(Libro, isbn=isbn)
    
    if request.method != 'POST':
        return redirect('listar_libros')
    
    titulo = request.POST.get('titulo', '').strip()
    autor = request.POST.get('autor', '').strip()
    editorial = request.POST.get('editorial', '').strip()
    año_publicacion = request.POST.get('año_publicacion', '').strip()
    
    if not titulo or not autor:
        messages.error(request, '❌ El título y autor son obligatorios.')
        return redirect('listar_libros')
    
    try:
        libro.titulo = titulo
        libro.autor = autor
        libro.editorial = editorial if editorial else None
        libro.año_publicacion = int(año_publicacion) if año_publicacion else None
        libro.save()
        messages.success(request, f'✅ Libro "{libro.titulo}" actualizado exitosamente.')
    except Exception as e:
        messages.error(request, f'❌ Error al actualizar: {str(e)}')
    
    return redirect('listar_libros')


@login_required
def dar_baja_libro(request, isbn):
    """Vista simple para dar de baja un libro (solo POST)"""
    libro = get_object_or_404(Libro, isbn=isbn)
    
    if request.method != 'POST':
        return redirect('listar_libros')
    
    if not libro.activo:
        messages.warning(request, f'⚠️ El libro "{libro.titulo}" ya fue dado de baja.')
        return redirect('listar_libros')
    
    # Verificar si tiene préstamos activos
    prestamos_activos = libro.ejemplares.filter(prestamos__fecha_devolucion_real__isnull=True).count()
    if prestamos_activos > 0:
        messages.error(request, f'❌ No se puede dar de baja. Tiene {prestamos_activos} préstamo(s) activo(s).')
        return redirect('listar_libros')
    
    libro.dar_de_baja()
    messages.success(request, f'✅ Libro "{libro.titulo}" y sus ejemplares dados de baja.')
    return redirect('listar_libros')


@login_required
def editar_ejemplar(request, codigo_ejemplar):
    """Vista simple para editar un ejemplar (solo POST)"""
    ejemplar = get_object_or_404(Ejemplar, codigo_ejemplar=codigo_ejemplar)
    
    if request.method != 'POST':
        return redirect('listar_libros')
    
    estado = request.POST.get('estado', '').strip()
    observaciones = request.POST.get('observaciones', '').strip()
    
    if not estado:
        messages.error(request, '❌ El estado es obligatorio.')
        return redirect('listar_libros')
    
    # Validar que no se cambie a disponible si tiene préstamo activo
    if estado == 'disponible':
        prestamo_activo = ejemplar.prestamos.filter(fecha_devolucion_real__isnull=True).exists()
        if prestamo_activo:
            messages.error(request, '❌ No se puede cambiar a disponible. Tiene un préstamo activo.')
            return redirect('listar_libros')
    
    try:
        ejemplar.estado = estado
        ejemplar.observaciones = observaciones if observaciones else None
        ejemplar.save()
        messages.success(request, f'✅ Ejemplar {ejemplar.codigo_ejemplar} actualizado.')
    except Exception as e:
        messages.error(request, f'❌ Error al actualizar: {str(e)}')
    
    return redirect('listar_libros')


@login_required
def dar_baja_ejemplar(request, codigo_ejemplar):
    """Vista simple para dar de baja un ejemplar (solo POST)"""
    ejemplar = get_object_or_404(Ejemplar, codigo_ejemplar=codigo_ejemplar)
    
    if request.method != 'POST':
        return redirect('listar_libros')
    
    if not ejemplar.activo:
        messages.warning(request, f'⚠️ El ejemplar {ejemplar.codigo_ejemplar} ya fue dado de baja.')
        return redirect('listar_libros')
    
    # Verificar si tiene préstamo activo
    prestamo_activo = ejemplar.prestamos.filter(fecha_devolucion_real__isnull=True).exists()
    if prestamo_activo:
        messages.error(request, f'❌ No se puede dar de baja. Tiene un préstamo activo.')
        return redirect('listar_libros')
    
    ejemplar.dar_de_baja()
    messages.success(request, f'✅ Ejemplar {ejemplar.codigo_ejemplar} dado de baja.')
    return redirect('listar_libros')