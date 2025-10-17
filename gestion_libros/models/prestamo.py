from django.db import models
from django.utils import timezone
from datetime import timedelta


class Prestamo(models.Model):
    """
    Representa un préstamo de un ejemplar a un socio.
    """
    socio = models.ForeignKey(
        'Socio',  # String reference para evitar imports circulares
        on_delete=models.CASCADE, 
        related_name='prestamos',
        verbose_name="Socio"
    )
    ejemplar = models.ForeignKey(
        'Ejemplar',  # String reference
        on_delete=models.CASCADE, 
        related_name='prestamos',
        verbose_name="Ejemplar"
    )
    fecha_inicio = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Préstamo"
    )
    fecha_devolucion_prevista = models.DateField(
        verbose_name="Fecha de Devolución Prevista",
        help_text="Fecha límite para devolver el libro"
    )
    fecha_devolucion_real = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Fecha de Devolución Real"
    )
    observaciones = models.TextField(
        blank=True, 
        null=True,
        help_text="Observaciones sobre el préstamo o devolución"
    )
    
    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        estado = "Devuelto" if self.fecha_devolucion_real else "Activo"
        return f"Préstamo de {self.ejemplar.libro.titulo} a {self.socio.nombre} - {estado}"
    
    def esta_activo(self):
        """Verifica si el préstamo está activo (no devuelto)"""
        return self.fecha_devolucion_real is None
    
    def dias_retraso(self):
        """Calcula los días de retraso en la devolución"""
        if self.fecha_devolucion_real:
            fecha_comparacion = self.fecha_devolucion_real.date()
        else:
            fecha_comparacion = timezone.now().date()
        
        if fecha_comparacion > self.fecha_devolucion_prevista:
            return (fecha_comparacion - self.fecha_devolucion_prevista).days
        return 0
    
    def tiene_retraso(self):
        """Verifica si el préstamo tiene retraso"""
        return self.dias_retraso() > 0
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para establecer fecha_devolucion_prevista
        automáticamente si no se proporciona (15 días por defecto)
        """
        if not self.fecha_devolucion_prevista:
            self.fecha_devolucion_prevista = (timezone.now() + timedelta(days=15)).date()
        super().save(*args, **kwargs)