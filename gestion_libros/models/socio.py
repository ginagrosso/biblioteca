from django.db import models


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