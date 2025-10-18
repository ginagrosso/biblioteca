from django.db import models


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
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el libro está activo en el sistema (soft delete)"
    )
    
    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ['titulo']
    
    def __str__(self):
        return f"{self.titulo} - {self.autor} (ISBN: {self.isbn})"
    
    def ejemplares_disponibles(self):
        """Retorna la cantidad de ejemplares disponibles para préstamo"""
        return self.ejemplares.filter(estado='disponible', activo=True).count()
    
    def dar_de_baja(self):
        """Marca el libro como inactivo (soft delete)"""
        self.activo = False
        self.save()
        # También damos de baja todos los ejemplares del libro
        self.ejemplares.filter(activo=True).update(activo=False)
    
    def reactivar(self):
        """Reactiva el libro"""
        self.activo = True
        self.save()


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
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el ejemplar está activo en el sistema (soft delete)"
    )
    
    class Meta:
        verbose_name = "Ejemplar"
        verbose_name_plural = "Ejemplares"
        ordering = ['libro', 'codigo_ejemplar']
    
    def __str__(self):
        return f"{self.libro.titulo} - Ejemplar {self.codigo_ejemplar} ({self.get_estado_display()})"
    
    def esta_disponible(self):
        """Verifica si el ejemplar está disponible para préstamo"""
        return self.estado == 'disponible' and self.activo
    
    def dar_de_baja(self):
        """Marca el ejemplar como inactivo (soft delete)"""
        self.activo = False
        self.save()
    
    def reactivar(self):
        """Reactiva el ejemplar"""
        self.activo = True
        self.save()