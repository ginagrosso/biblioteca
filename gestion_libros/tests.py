"""
Tests para el sistema de gestión de biblioteca.
Se implementa TDD (Test-Driven Development) para garantizar la calidad del código.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta, date
from decimal import Decimal

from .models import Libro, Ejemplar, Socio, Prestamo, Multa


# ============================================
# TESTS DE MODELOS
# ============================================

class LibroModelTest(TestCase):
    """Tests representativos para el modelo Libro"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.libro = Libro.objects.create(
            isbn='9780132350884',
            titulo='Clean Code',
            autor='Robert C. Martin',
            editorial='Prentice Hall',
            año_publicacion=2008
        )
    
    def test_libro_creacion_y_str(self):
        """Test: Crear un libro correctamente y verificar su representación"""
        self.assertEqual(self.libro.isbn, '9780132350884')
        self.assertEqual(self.libro.titulo, 'Clean Code')
        self.assertTrue(self.libro.activo)
        self.assertIn('Clean Code', str(self.libro))
    
    def test_ejemplares_disponibles(self):
        """Test: Contar ejemplares disponibles correctamente"""
        # Crear 2 ejemplares disponibles y 1 prestado
        Ejemplar.objects.create(libro=self.libro, codigo_ejemplar='EJ-1', estado='disponible')
        Ejemplar.objects.create(libro=self.libro, codigo_ejemplar='EJ-2', estado='disponible')
        Ejemplar.objects.create(libro=self.libro, codigo_ejemplar='EJ-3', estado='prestado')
        
        self.assertEqual(self.libro.ejemplares_disponibles(), 2)


class SocioModelTest(TestCase):
    """Tests representativos para el modelo Socio"""
    
    def setUp(self):
        self.socio = Socio.objects.create(
            dni='12345678',
            numero_socio='SOC-001',
            nombre='Juan Pérez'
        )
    
    def test_socio_con_multas_pendientes(self):
        """Test: Verificar multas pendientes y cálculo de montos"""
        # Sin multas
        self.assertFalse(self.socio.tiene_multas_pendientes())
        
        # Crear multas
        Multa.objects.create(socio=self.socio, monto=Decimal('100.00'), motivo='retraso', pagada=False)
        Multa.objects.create(socio=self.socio, monto=Decimal('50.00'), motivo='daño', pagada=False)
        
        # Verificar
        self.assertTrue(self.socio.tiene_multas_pendientes())
        self.assertEqual(self.socio.monto_total_multas(), Decimal('150.00'))


class PrestamoModelTest(TestCase):
    """Tests representativos para el modelo Prestamo"""
    
    def setUp(self):
        self.socio = Socio.objects.create(dni='12345678', numero_socio='SOC-001', nombre='Juan Pérez')
        libro = Libro.objects.create(isbn='9780132350884', titulo='Clean Code', autor='Robert C. Martin')
        self.ejemplar = Ejemplar.objects.create(libro=libro, codigo_ejemplar='EJ-001')
        self.prestamo = Prestamo.objects.create(
            socio=self.socio,
            ejemplar=self.ejemplar,
            fecha_devolucion_prevista=date.today() + timedelta(days=15)
        )
    
    def test_prestamo_ciclo_vida(self):
        """Test: Ciclo completo de préstamo (activo -> devuelto)"""
        # Inicialmente activo
        self.assertTrue(self.prestamo.esta_activo())
        
        # Devolver
        self.prestamo.fecha_devolucion_real = timezone.now()
        self.prestamo.save()
        
        # Ya no está activo
        self.assertFalse(self.prestamo.esta_activo())
    
    def test_calculo_dias_retraso(self):
        """Test: Calcular días de retraso correctamente"""
        # Sin retraso
        self.assertEqual(self.prestamo.dias_retraso(), 0)
        self.assertFalse(self.prestamo.tiene_retraso())
        
        # Con retraso de 5 días
        self.prestamo.fecha_devolucion_prevista = date.today() - timedelta(days=5)
        self.prestamo.save()
        
        # Verificar que tiene retraso (al menos 5 días, puede variar por hora)
        self.assertGreaterEqual(self.prestamo.dias_retraso(), 5)
        self.assertTrue(self.prestamo.tiene_retraso())


# ============================================
# TESTS DE INTEGRACIÓN
# ============================================

class IntegracionViewsTest(TestCase):
    """Tests de integración para vistas principales"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        self.socio = Socio.objects.create(dni='12345678', numero_socio='SOC-001', nombre='Juan Pérez')
        libro = Libro.objects.create(isbn='9780132350884', titulo='Clean Code', autor='Robert C. Martin')
        self.ejemplar = Ejemplar.objects.create(libro=libro, codigo_ejemplar='EJ-001', estado='disponible')
    
    def test_listar_libros_y_socios(self):
        """Test: Acceso a vistas de listado principales"""
        response_libros = self.client.get(reverse('listar_libros'))
        response_socios = self.client.get(reverse('listar_socios'))
        
        self.assertEqual(response_libros.status_code, 200)
        self.assertEqual(response_socios.status_code, 200)
        self.assertContains(response_libros, 'Clean Code')
        self.assertContains(response_socios, 'Juan Pérez')
    
    def test_proceso_prestamo_completo(self):
        """Test: Proceso completo de préstamo y devolución"""
        # Crear préstamo
        prestamo = Prestamo.objects.create(
            socio=self.socio,
            ejemplar=self.ejemplar,
            fecha_devolucion_prevista=date.today() + timedelta(days=15)
        )
        self.ejemplar.estado = 'prestado'
        self.ejemplar.save()
        
        # Verificar que existe y está activo
        self.assertTrue(Prestamo.objects.filter(socio=self.socio).exists())
        self.assertTrue(prestamo.esta_activo())
        
        # Devolver
        response = self.client.post(reverse('devolver_libro', args=[prestamo.id]))
        prestamo.refresh_from_db()
        
        # Verificar devolución (puede tener redirect)
        self.assertIsNotNone(prestamo.fecha_devolucion_real)


# ============================================
# TESTS DE REGLAS DE NEGOCIO
# ============================================

class ReglasNegocioTest(TestCase):
    """Tests para validar reglas de negocio críticas"""
    
    def setUp(self):
        self.socio = Socio.objects.create(dni='12345678', numero_socio='SOC-001', nombre='Juan Pérez')
        libro = Libro.objects.create(isbn='9780132350884', titulo='Clean Code', autor='Robert C. Martin')
        self.ejemplar = Ejemplar.objects.create(libro=libro, codigo_ejemplar='EJ-001', estado='disponible')
    
    def test_ejemplar_estados_prestamo_devolucion(self):
        """Test: Cambios de estado en ciclo préstamo-devolución"""
        # Inicialmente disponible
        self.assertTrue(self.ejemplar.esta_disponible())
        
        # Prestar
        prestamo = Prestamo.objects.create(
            socio=self.socio,
            ejemplar=self.ejemplar,
            fecha_devolucion_prevista=date.today() + timedelta(days=15)
        )
        self.ejemplar.estado = 'prestado'
        self.ejemplar.save()
        
        self.assertFalse(self.ejemplar.esta_disponible())
        
        # Devolver
        prestamo.fecha_devolucion_real = timezone.now()
        prestamo.save()
        self.ejemplar.estado = 'disponible'
        self.ejemplar.save()
        
        self.assertTrue(self.ejemplar.esta_disponible())
    
    def test_multa_por_retraso(self):
        """Test: Generación de multa por retraso en devolución"""
        from .singleton import obtener_configuracion
        
        # Crear préstamo con retraso de 5 días
        prestamo = Prestamo.objects.create(
            socio=self.socio,
            ejemplar=self.ejemplar,
            fecha_devolucion_prevista=date.today() - timedelta(days=5)
        )
        
        # Verificar retraso
        self.assertTrue(prestamo.tiene_retraso())
        dias_retraso = prestamo.dias_retraso()
        
        # Calcular y crear multa
        config = obtener_configuracion()
        monto_multa = config.calcular_multa_retraso(dias_retraso)
        
        multa = Multa.objects.create(
            socio=self.socio,
            prestamo=prestamo,
            monto=monto_multa,
            motivo='retraso'
        )
        
        # Verificar multa creada
        self.assertTrue(self.socio.tiene_multas_pendientes())
    
    def test_validacion_montos_multas(self):
        """Test: Validar montos de multas dinámicas (daño/pérdida)"""
        from .singleton import obtener_configuracion
        
        config = obtener_configuracion()
        
        # Test 1: Monto válido
        es_valido, monto, error = config.validar_monto_multa('100.50')
        self.assertTrue(es_valido)
        self.assertEqual(monto, Decimal('100.50'))
        self.assertIsNone(error)
        
        # Test 2: Monto vacío
        es_valido, monto, error = config.validar_monto_multa('')
        self.assertFalse(es_valido)
        self.assertIsNone(monto)
        self.assertIn('vacío', error)
        
        # Test 3: Monto negativo o cero
        es_valido, monto, error = config.validar_monto_multa('0')
        self.assertFalse(es_valido)
        
        # Test 4: Monto demasiado grande
        es_valido, monto, error = config.validar_monto_multa('10000000')
        self.assertFalse(es_valido)
        self.assertIn('grande', error)
        
        # Test 5: Formato inválido
        es_valido, monto, error = config.validar_monto_multa('abc123')
        self.assertFalse(es_valido)
        self.assertIn('inválido', error)
