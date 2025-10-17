"""
URLs para la aplicación gestion_libros
"""

from django.urls import path
from .views import (
    index,
    listar_libros,
    listar_socios,
    listar_prestamos,
    realizar_prestamo,
    devolver_libro,
    registrar_socio,
    registrar_libro,
    registrar_ejemplar,
)

urlpatterns = [
    # Página principal
    path('', index, name='index'),
    
    # Listados
    path('libros/', listar_libros, name='listar_libros'),
    path('socios/', listar_socios, name='listar_socios'),
    path('prestamos/', listar_prestamos, name='listar_prestamos'),
    
    # Gestión de libros y ejemplares
    path('libros/nuevo/', registrar_libro, name='registrar_libro'),
    path('ejemplares/nuevo/', registrar_ejemplar, name='registrar_ejemplar'),
    
    # PROCESO 1: Préstamo de libros
    path('prestamos/nuevo/', realizar_prestamo, name='realizar_prestamo'),
    
    # PROCESO 2: Devolución de libros
    path('prestamos/<int:prestamo_id>/devolver/', devolver_libro, name='devolver_libro'),
    
    # PROCESO 3: Registro de socios
    path('socios/nuevo/', registrar_socio, name='registrar_socio'),
]