from django.contrib import admin
from .models import Libro, Ejemplar, Socio, Prestamo, Multa


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ['isbn', 'titulo', 'autor', 'editorial', 'año_publicacion', 'ejemplares_disponibles']
    search_fields = ['isbn', 'titulo', 'autor']
    list_filter = ['editorial', 'año_publicacion']


@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display = ['codigo_ejemplar', 'libro', 'estado', 'fecha_adquisicion']
    list_filter = ['estado', 'fecha_adquisicion']
    search_fields = ['codigo_ejemplar', 'libro__titulo', 'libro__isbn']
    list_editable = ['estado']


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ['numero_socio', 'nombre', 'dni', 'email', 'telefono', 'activo', 'fecha_registro']
    search_fields = ['dni', 'numero_socio', 'nombre', 'email']
    list_filter = ['activo', 'fecha_registro']
    list_editable = ['activo']


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ['id', 'socio', 'ejemplar', 'fecha_inicio', 'fecha_devolucion_prevista', 'fecha_devolucion_real', 'esta_activo']
    list_filter = ['fecha_inicio', 'fecha_devolucion_prevista', 'fecha_devolucion_real']
    search_fields = ['socio__nombre', 'socio__dni', 'ejemplar__codigo_ejemplar', 'ejemplar__libro__titulo']
    date_hierarchy = 'fecha_inicio'
    
    def esta_activo(self, obj):
        return obj.esta_activo()
    esta_activo.boolean = True
    esta_activo.short_description = 'Activo'


@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ['id', 'socio', 'monto', 'motivo', 'fecha', 'pagada', 'fecha_pago']
    list_filter = ['motivo', 'pagada', 'fecha']
    search_fields = ['socio__nombre', 'socio__dni', 'descripcion']
    list_editable = ['pagada']
    date_hierarchy = 'fecha'
