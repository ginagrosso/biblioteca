from decimal import Decimal, InvalidOperation


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
            self.monto_multa_maximo = Decimal('999999.99')  # Monto máximo permitido para multas
            self.monto_multa_minimo = Decimal('0.01')  # Monto mínimo permitido para multas
            # NOTA: Los montos de multas por daño/pérdida los ingresa el bibliotecario dinámicamente
            ConfiguracionBiblioteca._inicializado = True
    
    def calcular_multa_retraso(self, dias_retraso):
        """
        Calcula el monto de multa por días de retraso usando la tasa sugerida.
        """
        return self.tasa_multa_diaria_sugerida * dias_retraso
    
    def validar_monto_multa(self, monto_str):
        """
        Valida que un monto de multa sea válido.
        Centraliza la lógica de validación de montos para evitar duplicación (DRY).
        
        Args:
            monto_str: String con el monto a validar (viene del formulario)
            
        Returns:
            tuple (es_valido: bool, monto: Decimal o None, mensaje_error: str o None)
        """
        try:
            # Validar que no esté vacío
            if not monto_str or str(monto_str).strip() == '':
                return False, None, "El monto no puede estar vacío"
            
            # Convertir a Decimal
            monto = Decimal(str(monto_str))
            
            # Validar rango mínimo
            if monto < self.monto_multa_minimo:
                return False, None, f"El monto debe ser mayor a ${self.monto_multa_minimo}"
            
            # Validar rango máximo
            if monto > self.monto_multa_maximo:
                return False, None, f"El monto es demasiado grande (máximo: ${self.monto_multa_maximo})"
            
            return True, monto, None
            
        except (ValueError, InvalidOperation):
            return False, None, "El formato del monto es inválido"
    
    def __str__(self):
        return f"Configuración Biblioteca - Tasa multa sugerida: ${self.tasa_multa_diaria_sugerida}/día"


# Función auxiliar para obtener la instancia
def obtener_configuracion():
    """
    Retorna la única instancia de ConfiguracionBiblioteca.
    """
    return ConfiguracionBiblioteca()