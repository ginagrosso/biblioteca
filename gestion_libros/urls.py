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
)

urlpatterns = [
    # Página principal
    path('', index, name='index'),
    
    # Listados
    path('libros/', listar_libros, name='listar_libros'),
    path('socios/', listar_socios, name='listar_socios'),
    path('prestamos/', listar_prestamos, name='listar_prestamos'),
    
    # PROCESO 1: Préstamo de libros
    path('prestamos/nuevo/', realizar_prestamo, name='realizar_prestamo'),
    
    # PROCESO 2: Devolución de libros
    path('prestamos/<int:prestamo_id>/devolver/', devolver_libro, name='devolver_libro'),
    
    # PROCESO 3: Registro de socios
    path('socios/nuevo/', registrar_socio, name='registrar_socio'),
]