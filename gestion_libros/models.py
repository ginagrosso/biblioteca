from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta


class Libro(models.Model):
    """
    Representa un libro en el catálogo de la biblioteca.
    El ISBN es único y sirve como identificador principal.
    """
    isbn = models.CharField(
        max_length=13, 
        unique=True, 
        primary_key=True,
        verbose_name="ISBN",
        help_text="Código ISBN único del libro (10 o 13 dígitos)"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    autor = models.CharField(max_length=100, verbose_name="Autor")
    editorial = models.CharField(max_length=100, blank=True, null=True)
    año_publicacion = models.IntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ['titulo']
    
    def __str__(self):
        return f"{self.titulo} - {self.autor} (ISBN: {self.isbn})"
    
    def ejemplares_disponibles(self):
        """Retorna la cantidad de ejemplares disponibles para préstamo"""
        return self.ejemplares.filter(estado='disponible').count()


class Ejemplar(models.Model):
    """
    Representa una copia física de un libro.
    Un libro puede tener múltiples ejemplares.
    """
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('mantenimiento', 'En Mantenimiento'),
        ('perdido', 'Perdido'),
    ]
    
    libro = models.ForeignKey(
        Libro, 
        on_delete=models.CASCADE, 
        related_name='ejemplares',
        verbose_name="Libro"
    )
    codigo_ejemplar = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Código de Ejemplar",
        help_text="Código único para identificar este ejemplar específico"
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS, 
        default='disponible',
        verbose_name="Estado"
    )
    fecha_adquisicion = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Adquisición"
    )
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Ejemplar"
        verbose_name_plural = "Ejemplares"
        ordering = ['libro', 'codigo_ejemplar']
    
    def __str__(self):
        return f"{self.libro.titulo} - Ejemplar {self.codigo_ejemplar} ({self.get_estado_display()})"
    
    def esta_disponible(self):
        """Verifica si el ejemplar está disponible para préstamo"""
        return self.estado == 'disponible'


class Socio(models.Model):
    """
    Representa un socio/miembro de la biblioteca.
    El DNI es único y sirve como identificador principal.
    """
    dni = models.CharField(
        max_length=10, 
        unique=True,
        verbose_name="DNI",
        help_text="Documento Nacional de Identidad del socio"
    )
    numero_socio = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Número de Socio",
        help_text="Número único asignado al socio"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre Completo")
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    fecha_registro = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el socio puede realizar préstamos"
    )
    
    class Meta:
        verbose_name = "Socio"
        verbose_name_plural = "Socios"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} (DNI: {self.dni} - Socio: {self.numero_socio})"
    
    def tiene_multas_pendientes(self):
        """Verifica si el socio tiene multas sin pagar"""
        return self.multas.filter(pagada=False).exists()
    
    def monto_total_multas(self):
        """Calcula el monto total de multas pendientes"""
        return sum(multa.monto for multa in self.multas.filter(pagada=False))
    
    def prestamos_activos(self):
        """Retorna los préstamos activos (sin devolver) del socio"""
        return self.prestamos.filter(fecha_devolucion_real__isnull=True)


class Prestamo(models.Model):
    """
    Representa un préstamo de un ejemplar a un socio.
    """
    socio = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        related_name='prestamos',
        verbose_name="Socio"
    )
    ejemplar = models.ForeignKey(
        Ejemplar, 
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
            # Ya fue devuelto
            fecha_comparacion = self.fecha_devolucion_real.date()
        else:
            # Aún no fue devuelto, comparar con hoy
            fecha_comparacion = timezone.now().date()
        
        if fecha_comparacion > self.fecha_devolucion_prevista:
            return (fecha_comparacion - self.fecha_devolucion_prevista).days
        return 0
    
    def tiene_retraso(self):
        """Verifica si el préstamo tiene retraso"""
        return self.dias_retraso() > 0
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para establecer fecha_devolucion_prevista automáticamente
        si no se proporciona (15 días por defecto)
        """
        if not self.fecha_devolucion_prevista:
            self.fecha_devolucion_prevista = (timezone.now() + timedelta(days=15)).date()
        super().save(*args, **kwargs)


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
        Socio, 
        on_delete=models.CASCADE, 
        related_name='multas',
        verbose_name="Socio"
    )
    prestamo = models.ForeignKey(
        Prestamo, 
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
