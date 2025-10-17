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
            messages.error(request, 'El ISBN, título y autor son obligatorios.')
            return redirect('registrar_libro')
        
        # Validar que el ISBN no exista
        if Libro.objects.filter(isbn=isbn).exists():
            messages.error(
                request, 
                f'Ya existe un libro registrado con el ISBN {isbn}.'
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
                f'✓ Libro registrado exitosamente.<br>'
                f'Título: {libro.titulo}<br>'
                f'ISBN: {libro.isbn}<br>'
                f'Ahora puedes agregar ejemplares de este libro.'
            )
            return redirect('listar_libros')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el libro: {str(e)}')
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
            messages.error(request, 'Debe seleccionar un libro.')
            return redirect('registrar_ejemplar')
        
        try:
            libro = Libro.objects.get(isbn=libro_isbn)
        except Libro.DoesNotExist:
            messages.error(request, f'No existe un libro con ISBN {libro_isbn}.')
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
                f'✓ Ejemplar registrado exitosamente.<br>'
                f'Libro: {libro.titulo}<br>'
                f'Código generado: <strong>{ejemplar.codigo_ejemplar}</strong><br>'
                f'Estado: Disponible'
            )
            return redirect('listar_libros')
            
        except Exception as e:
            messages.error(request, f'Error al registrar el ejemplar: {str(e)}')
            return redirect('registrar_ejemplar')
    
    # GET - Mostrar formulario
    libros = Libro.objects.all()
    return render(request, 'gestion_libros/registrar_ejemplar.html', {'libros': libros})