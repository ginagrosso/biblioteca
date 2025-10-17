"""
Vistas para la gestión de libros y ejemplares.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Libro, Ejemplar
from django.contrib.auth.decorators import login_required


@login_required
def registrar_libro(request):
    """
    Vista para registrar un nuevo libro en el catálogo.
    """
    if request.method == 'POST':
        isbn = request.POST.get('isbn', '').strip()
        titulo = request.POST.get('titulo', '').strip()
        autor = request.POST.get('autor', '').strip()
        editorial = request.POST.get('editorial', '').strip()
        año_publicacion = request.POST.get('año_publicacion', '').strip()
        
        # Validaciones básicas
        if not isbn or not titulo or not autor:
            messages.error(request, 
                f'❌ <strong>Campos obligatorios faltantes</strong><br>'
                f'Debes completar todos los campos obligatorios:<br>'
                f'• <strong>ISBN:</strong> {"✓" if isbn else "❌"}<br>'
                f'• <strong>Título:</strong> {"✓" if titulo else "❌"}<br>'
                f'• <strong>Autor:</strong> {"✓" if autor else "❌"}<br>'
                f'<small>Completa los campos marcados con ❌ para continuar.</small>'
            )
            return redirect('registrar_libro')
        
        # Validar que el ISBN no exista
        if Libro.objects.filter(isbn=isbn).exists():
            messages.error(request, 
                f'❌ <strong>ISBN ya registrado</strong><br>'
                f'Ya existe un libro registrado con el ISBN <strong>{isbn}</strong>.<br>'
                f'<small>Verifica el número de ISBN o busca el libro existente en el catálogo.</small>'
            )
            return redirect('registrar_libro')
        
        try:
            # Crear el libro
            libro = Libro.objects.create(
                isbn=isbn,
                titulo=titulo,
                autor=autor,
                editorial=editorial if editorial else None,
                año_publicacion=int(año_publicacion) if año_publicacion else None
            )
            
            messages.success(
                request, 
                f'✅ <strong>¡Libro registrado exitosamente!</strong><br>'
                f'<strong>Título:</strong> {libro.titulo}<br>'
                f'<strong>Autor:</strong> {libro.autor}<br>'
                f'<strong>ISBN:</strong> <code>{libro.isbn}</code><br>'
                f'<strong>Editorial:</strong> {libro.editorial or "No especificada"}<br>'
                f'<strong>Año:</strong> {libro.año_publicacion or "No especificado"}<br>'
                f'<small>El libro ha sido agregado al catálogo. Ahora puedes registrar ejemplares de este libro.</small>'
            )
            return redirect('listar_libros')
            
        except Exception as e:
            messages.error(request, 
                f'❌ <strong>Error al registrar el libro</strong><br>'
                f'No se pudo completar el registro: <strong>{str(e)}</strong><br>'
                f'<small>Verifica los datos ingresados y contacta al administrador si el problema persiste.</small>'
            )
            return redirect('registrar_libro')
    
    # GET - Mostrar formulario
    return render(request, 'gestion_libros/registrar_libro.html')

@login_required
def registrar_ejemplar(request):
    """
    Vista para registrar un nuevo ejemplar de un libro existente.
    El código de ejemplar se genera automáticamente usando el ISBN completo.
    """
    if request.method == 'POST':
        libro_isbn = request.POST.get('libro_isbn', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        
        # Validación básica
        if not libro_isbn:
            messages.error(request, 
                f'❌ <strong>Libro no seleccionado</strong><br>'
                f'Debes seleccionar un libro para registrar un ejemplar.<br>'
                f'<small>Elige un libro de la lista desplegable para continuar.</small>'
            )
            return redirect('registrar_ejemplar')
        
        try:
            libro = Libro.objects.get(isbn=libro_isbn)
        except Libro.DoesNotExist:
            messages.error(request, 
                f'❌ <strong>Libro no encontrado</strong><br>'
                f'No existe un libro con ISBN <strong>{libro_isbn}</strong>.<br>'
                f'<small>Verifica el ISBN o registra el libro primero en el catálogo.</small>'
            )
            return redirect('registrar_ejemplar')
        
        # GENERAR CÓDIGO AUTOMÁTICAMENTE CON ISBN COMPLETO
        # Formato: EJ-[ISBN_COMPLETO]-[NÚMERO]
        # Ejemplo: EJ-9788478887644-001, EJ-9788478887644-002, etc.
        # Esto garantiza unicidad absoluta porque el ISBN es único
        
        # Buscar el último ejemplar de este libro específico
        ultimo_ejemplar = Ejemplar.objects.filter(
            libro=libro,
            codigo_ejemplar__startswith=f'EJ-{libro.isbn}-'
        ).order_by('-codigo_ejemplar').first()
        
        if ultimo_ejemplar:
            # Extraer el número del último código
            try:
                partes = ultimo_ejemplar.codigo_ejemplar.split('-')
                ultimo_numero = int(partes[-1])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                # Si no se puede extraer, empezar desde 1
                nuevo_numero = 1
        else:
            # Primer ejemplar de este libro
            nuevo_numero = 1
        
        # Generar código: EJ-[ISBN_COMPLETO]-[NÚMERO_SECUENCIAL]
        codigo_ejemplar = f'EJ-{libro.isbn}-{nuevo_numero:03d}'
        
        try:
            # Crear el ejemplar
            ejemplar = Ejemplar.objects.create(
                libro=libro,
                codigo_ejemplar=codigo_ejemplar,
                estado='disponible',
                observaciones=observaciones if observaciones else None
            )
            
            messages.success(
                request, 
                f'✅ <strong>¡Ejemplar registrado exitosamente!</strong><br>'
                f'<strong>Libro:</strong> {libro.titulo}<br>'
                f'<strong>Autor:</strong> {libro.autor}<br>'
                f'<strong>Código generado:</strong> <code>{ejemplar.codigo_ejemplar}</code><br>'
                f'<strong>Estado:</strong> Disponible<br>'
                f'<strong>Observaciones:</strong> {ejemplar.observaciones or "Ninguna"}<br>'
                f'<small>El ejemplar está listo para ser prestado a los socios.</small>'
            )
            return redirect('listar_libros')
            
        except Exception as e:
            messages.error(request, 
                f'❌ <strong>Error al registrar el ejemplar</strong><br>'
                f'No se pudo completar el registro: <strong>{str(e)}</strong><br>'
                f'<small>Verifica los datos ingresados y contacta al administrador si el problema persiste.</small>'
            )
            return redirect('registrar_ejemplar')
    
    # GET - Mostrar formulario
    libros = Libro.objects.all()
    return render(request, 'gestion_libros/registrar_ejemplar.html', {'libros': libros})