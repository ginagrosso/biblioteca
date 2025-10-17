"""
Modelos del sistema de gestión de biblioteca.
Modularizado para mejor mantenibilidad.
"""
from .libro import Libro, Ejemplar
from .socio import Socio
from .prestamo import Prestamo
from .multa import Multa

__all__ = ['Libro', 'Ejemplar', 'Socio', 'Prestamo', 'Multa']