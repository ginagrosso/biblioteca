"""
Módulo de vistas para el sistema de gestión de biblioteca.
Organizado por funcionalidad.
"""

from .base import index, listar_libros, listar_socios, listar_prestamos, listar_multas, pagar_multa
from .prestamo import realizar_prestamo
from .devolucion import devolver_libro
from .socio import registrar_socio
from .libro import (
    registrar_libro, 
    registrar_ejemplar, 
    editar_libro, 
    editar_ejemplar,
    dar_baja_libro,
    dar_baja_ejemplar
)
from .pdf import generar_comprobante_multa, generar_comprobante_prestamo

__all__ = [
    'index',
    'listar_libros',
    'listar_socios',
    'listar_prestamos',
    'realizar_prestamo',
    'devolver_libro',
    'registrar_socio',
    'registrar_libro',
    'registrar_ejemplar',
    'editar_libro',
    'editar_ejemplar',
    'dar_baja_libro',
    'dar_baja_ejemplar',
    'listar_multas',
    'pagar_multa',
    'generar_comprobante_multa',
    'generar_comprobante_prestamo',
]