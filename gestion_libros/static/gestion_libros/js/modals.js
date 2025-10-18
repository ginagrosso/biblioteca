/**
 * Funciones para gestionar los modales de la biblioteca
 * Estas funciones se usan en varios templates para crear/editar libros, ejemplares y socios
 * sin tener que duplicar el código en cada página
 */

// ============================================================
// MODALES DE LIBROS
// ============================================================

/**
 * Limpia el modal de libro para crear uno nuevo
 * Resetea todos los campos y configura la acción del form
 */
function limpiarModalLibro() {
    // Cambiar título del modal
    document.getElementById('modalLibroTitulo').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Nuevo Libro';
    
    // Apuntar el form a la URL de creación
    document.getElementById('formLibro').action = '/libros/nuevo/';
    
    // Limpiar todos los campos
    document.getElementById('libro_isbn').value = '';
    document.getElementById('libro_isbn').readOnly = false;  // El ISBN se puede editar al crear
    document.getElementById('libro_titulo').value = '';
    document.getElementById('libro_autor').value = '';
    document.getElementById('libro_editorial').value = '';
    document.getElementById('libro_año').value = '';
}

/**
 * Carga los datos de un libro existente en el modal para editarlo
 * @param {string} isbn - ISBN del libro (identificador único)
 * @param {string} titulo - Título del libro
 * @param {string} autor - Autor del libro
 * @param {string} editorial - Editorial (puede ser null)
 * @param {number} año - Año de publicación (puede ser null)
 */
function cargarLibroEnModal(isbn, titulo, autor, editorial, año) {
    // Cambiar título del modal a "Editar"
    document.getElementById('modalLibroTitulo').innerHTML = '<i class="bi bi-pencil me-2"></i>Editar Libro';
    
    // Apuntar el form a la URL de edición (con el ISBN en la URL)
    document.getElementById('formLibro').action = '/libros/' + encodeURIComponent(isbn) + '/editar/';
    
    // Cargar los valores actuales en los campos
    document.getElementById('libro_isbn').value = isbn;
    document.getElementById('libro_isbn').readOnly = true;  // No se puede cambiar el ISBN al editar
    document.getElementById('libro_titulo').value = titulo;
    document.getElementById('libro_autor').value = autor;
    document.getElementById('libro_editorial').value = editorial || '';  // Si es null, usar string vacío
    document.getElementById('libro_año').value = año || '';
}

// ============================================================
// MODALES DE EJEMPLARES
// ============================================================

/**
 * Limpia el modal de ejemplar para crear uno nuevo
 * @param {string} isbnPreselect - ISBN del libro para preseleccionar (opcional)
 */
function limpiarModalEjemplar(isbnPreselect = '') {
    // Cambiar título del modal
    document.getElementById('modalEjemplarTitulo').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Nuevo Ejemplar';
    
    // Apuntar el form a la URL de creación
    document.getElementById('formEjemplar').action = '/ejemplares/nuevo/';
    
    // Mostrar el selector de libro (porque estamos creando, hay que elegir a qué libro pertenece)
    document.getElementById('ejemplar_libro_select_container').style.display = 'block';
    
    // Ocultar los campos que solo se usan al editar (código y estado)
    document.getElementById('ejemplar_codigo_container').style.display = 'none';
    document.getElementById('ejemplar_estado_container').style.display = 'none';
    
    // Hacer el selector de libro obligatorio
    document.getElementById('ejemplar_libro_select').required = true;
    
    // Si se pasó un ISBN, preseleccionarlo (útil cuando hacés clic en "Nuevo ejemplar" desde un libro específico)
    document.getElementById('ejemplar_libro_select').value = isbnPreselect;
    document.getElementById('ejemplar_libro_select').disabled = false;
    
    // Limpiar observaciones
    document.getElementById('ejemplar_obs').value = '';
}

/**
 * Carga los datos de un ejemplar existente en el modal para editarlo
 * @param {string} codigo - Código único del ejemplar
 * @param {string} libroIsbn - ISBN del libro al que pertenece
 * @param {string} estado - Estado actual (disponible/prestado/mantenimiento/perdido/dañado)
 * @param {string} obs - Observaciones
 */
function cargarEjemplarEnModal(codigo, libroIsbn, estado, obs) {
    // Cambiar título del modal
    document.getElementById('modalEjemplarTitulo').innerHTML = '<i class="bi bi-pencil me-2"></i>Editar Ejemplar';
    
    // Construir la URL de edición con el código del ejemplar
    // Uso window.location.origin para obtener la URL base del sitio
    const baseUrl = window.location.origin;
    document.getElementById('formEjemplar').action = baseUrl + '/ejemplares/' + encodeURIComponent(codigo) + '/editar/';
    
    // Ocultar el selector de libro (no se puede cambiar el libro de un ejemplar existente)
    document.getElementById('ejemplar_libro_select_container').style.display = 'none';
    
    // Mostrar los campos de código y estado (que estaban ocultos en modo crear)
    document.getElementById('ejemplar_codigo_container').style.display = 'block';
    document.getElementById('ejemplar_estado_container').style.display = 'block';
    
    // Quitar el required del selector de libro (porque está oculto)
    // Esto evita errores de validación del form
    document.getElementById('ejemplar_libro_select').required = false;
    
    // Cargar los valores actuales
    document.getElementById('ejemplar_codigo_display').value = codigo;
    document.getElementById('ejemplar_estado').value = estado;
    document.getElementById('ejemplar_obs').value = obs || '';
}

// ============================================================
// MODALES DE SOCIOS
// ============================================================

/**
 * Limpia el modal de socio para crear uno nuevo
 * Simplemente resetea todos los campos del formulario
 */
function limpiarModalSocio() {
    // Reset hace que todos los campos vuelvan a sus valores por defecto (vacíos)
    document.getElementById('formSocio').reset();
}

// ============================================================
// FUNCIONES AUXILIARES
// ============================================================

/**
 * Muestra/oculta los ejemplares de un libro en la tabla
 * Se usa en listar_libros para expandir/contraer las filas de ejemplares
 * @param {string} isbn - ISBN del libro
 */
function toggleEjemplares(isbn) {
    const row = document.getElementById('ejemplares-' + isbn);
    if (row) {
        // Si está oculto, mostrarlo. Si está visible, ocultarlo.
        row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
    }
}

