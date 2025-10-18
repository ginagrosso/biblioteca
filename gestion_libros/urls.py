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
    editar_libro,
    editar_ejemplar,
    dar_baja_libro,
    dar_baja_ejemplar,
    listar_multas,
    pagar_multa,
)

urlpatterns = [
    # Página principal
    path('', index, name='index'),
    
    # Listados
    path('libros/', listar_libros, name='listar_libros'),
    path('socios/', listar_socios, name='listar_socios'),
    path('prestamos/', listar_prestamos, name='listar_prestamos'),
    path('multas/', listar_multas, name='listar_multas'),
    
    # Gestión de libros y ejemplares
    path('libros/nuevo/', registrar_libro, name='registrar_libro'),
    path('libros/<str:isbn>/editar/', editar_libro, name='editar_libro'),
    path('libros/<str:isbn>/baja/', dar_baja_libro, name='dar_baja_libro'),
    path('ejemplares/nuevo/', registrar_ejemplar, name='registrar_ejemplar'),
    path('ejemplares/<str:codigo_ejemplar>/editar/', editar_ejemplar, name='editar_ejemplar'),
    path('ejemplares/<str:codigo_ejemplar>/baja/', dar_baja_ejemplar, name='dar_baja_ejemplar'),
    
    # PROCESO 1: Préstamo de libros
    path('prestamos/nuevo/', realizar_prestamo, name='realizar_prestamo'),
    
    # PROCESO 2: Devolución de libros
    path('prestamos/<int:prestamo_id>/devolver/', devolver_libro, name='devolver_libro'),
    
    # PROCESO 3: Registro de socios
    path('socios/nuevo/', registrar_socio, name='registrar_socio'),
    
    # PROCESO 4: Gestión de multas
    path('multas/<int:multa_id>/pagar/', pagar_multa, name='pagar_multa'),
]