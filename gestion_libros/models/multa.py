from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Multa(models.Model):
    """
    Representa una multa aplicada a un socio.
    Puede estar asociada a un préstamo específico.
    """
    MOTIVOS = [
        ('retraso', 'Retraso en Devolución'),
        ('daño', 'Daño al Libro'),
        ('perdida', 'Pérdida del Libro'),
        ('otro', 'Otro Motivo'),
    ]
    
    socio = models.ForeignKey(
        'Socio',  # String reference
        on_delete=models.CASCADE, 
        related_name='multas',
        verbose_name="Socio"
    )
    prestamo = models.ForeignKey(
        'Prestamo',  # String reference
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='multas',
        verbose_name="Préstamo Asociado",
        help_text="Préstamo que originó la multa (si aplica)"
    )
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Monto"
    )
    motivo = models.CharField(
        max_length=20, 
        choices=MOTIVOS,
        verbose_name="Motivo"
    )
    descripcion = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Descripción Detallada"
    )
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de la Multa"
    )
    pagada = models.BooleanField(
        default=False,
        verbose_name="Pagada"
    )
    fecha_pago = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Fecha de Pago"
    )
    
    class Meta:
        verbose_name = "Multa"
        verbose_name_plural = "Multas"
        ordering = ['-fecha']
    
    def __str__(self):
        estado = "Pagada" if self.pagada else "Pendiente"
        return f"Multa de ${self.monto} a {self.socio.nombre} - {estado}"
    
    def marcar_como_pagada(self):
        """Marca la multa como pagada y registra la fecha de pago"""
        self.pagada = True
        self.fecha_pago = timezone.now()
        self.save()