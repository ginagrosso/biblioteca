class ConfiguracionBiblioteca:
    """
    Patrón Singleton para la configuración global de la biblioteca.
    Garantiza que solo exista una instancia de configuración en toda la aplicación.
    """
    _instancia = None
    _inicializado = False
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(ConfiguracionBiblioteca, cls).__new__(cls)
        return cls._instancia
    
    def __init__(self):
        # Solo inicializar una vez
        if not ConfiguracionBiblioteca._inicializado:
            self.tasa_multa_diaria_sugerida = 0.50  # Sugerencia: $0.50 por día de retraso
            self.dias_prestamo_default = 15  # 15 días de préstamo por defecto
            self.max_prestamos_simultaneos = 3  # Máximo de préstamos activos por socio
            # NOTA: Los montos de multas por daño/pérdida los ingresa el bibliotecario dinámicamente
            ConfiguracionBiblioteca._inicializado = True
    
    def calcular_multa_retraso(self, dias_retraso):
        """
        Calcula el monto de multa por días de retraso usando la tasa sugerida.
        """
        return self.tasa_multa_diaria_sugerida * dias_retraso
    
    def __str__(self):
        return f"Configuración Biblioteca - Tasa multa sugerida: ${self.tasa_multa_diaria_sugerida}/día"


# Función auxiliar para obtener la instancia
def obtener_configuracion():
    """
    Retorna la única instancia de ConfiguracionBiblioteca.
    """
    return ConfiguracionBiblioteca()