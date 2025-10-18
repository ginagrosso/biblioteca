"""
Vistas para generación de PDFs (comprobantes de pago y préstamos)
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from ..models import Multa, Prestamo


@login_required
def generar_comprobante_multa(request, multa_id):
    """Genera un PDF con el comprobante de pago de multa"""
    multa = get_object_or_404(Multa, id=multa_id)
    
    # Crear respuesta HTTP con tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="comprobante_multa_{multa_id}.pdf"'
    
    # Crear documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#3E2723'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#6B8E7F'),
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # Título
    elements.append(Paragraph("COMPROBANTE DE MULTA", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Estado de la multa
    estado_text = "PAGADA" if multa.pagada else "PENDIENTE"
    estado_color = colors.HexColor('#5A9E8B') if multa.pagada else colors.HexColor('#E06055')
    estado_style = ParagraphStyle(
        'Estado',
        parent=styles['Normal'],
        fontSize=16,
        textColor=estado_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(f"Estado: {estado_text}", estado_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Información de la multa en tabla
    data = [
        ['Nº de Comprobante:', f'#{multa.id}'],
        ['Fecha de Emisión:', multa.fecha.strftime('%d/%m/%Y %H:%M')],
        ['Socio:', multa.socio.nombre],
        ['DNI:', multa.socio.dni],
        ['Nº Socio:', multa.socio.numero_socio],
        ['', ''],
        ['Motivo:', multa.get_motivo_display()],
        ['Descripción:', multa.descripcion or 'N/A'],
        ['', ''],
        ['MONTO:', f'$ {multa.monto}'],
    ]
    
    if multa.pagada:
        data.append(['Fecha de Pago:', multa.fecha_pago.strftime('%d/%m/%Y %H:%M')])
    
    table = Table(data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
        ('FONT', (0, 9), (-1, 9), 'Helvetica-Bold', 14),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B5B4D')),
        ('TEXTCOLOR', (0, 9), (-1, 9), colors.HexColor('#3E2723')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 8), (-1, 8), 1, colors.HexColor('#E5DDD1')),
        ('LINEABOVE', (0, 9), (-1, 9), 2, colors.HexColor('#3E2723')),
        ('BACKGROUND', (0, 9), (-1, 9), colors.HexColor('#FAF8F5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Nota al pie
    if multa.pagada:
        nota = "Este comprobante certifica que la multa ha sido pagada en su totalidad."
    else:
        nota = "Este comprobante debe ser presentado al momento del pago de la multa."
    
    nota_style = ParagraphStyle(
        'Nota',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6B5B4D'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    elements.append(Paragraph(nota, nota_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Fecha de emisión del comprobante
    fecha_emision = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    fecha_style = ParagraphStyle(
        'Fecha',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_RIGHT
    )
    elements.append(Paragraph(f"Comprobante generado el {fecha_emision}", fecha_style))
    
    # Construir PDF
    doc.build(elements)
    return response


@login_required
def generar_comprobante_prestamo(request, prestamo_id):
    """Genera un PDF con el comprobante de préstamo"""
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    
    # Crear respuesta HTTP con tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="comprobante_prestamo_{prestamo_id}.pdf"'
    
    # Crear documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#3E2723'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Título
    elements.append(Paragraph("COMPROBANTE DE PRÉSTAMO", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Estado del préstamo
    estado_text = "DEVUELTO" if not prestamo.esta_activo() else "ACTIVO"
    if prestamo.esta_activo() and prestamo.tiene_retraso():
        estado_text = "RETRASADO"
        estado_color = colors.HexColor('#F0AD4E')
    elif prestamo.esta_activo():
        estado_color = colors.HexColor('#5A9E8B')
    else:
        estado_color = colors.HexColor('#6B5B4D')
    
    estado_style = ParagraphStyle(
        'Estado',
        parent=styles['Normal'],
        fontSize=16,
        textColor=estado_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(f"Estado: {estado_text}", estado_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Información del préstamo en tabla
    data = [
        ['Nº de Préstamo:', f'#{prestamo.id}'],
        ['Fecha de Préstamo:', prestamo.fecha_inicio.strftime('%d/%m/%Y')],
        ['', ''],
        ['Socio:', prestamo.socio.nombre],
        ['DNI:', prestamo.socio.dni],
        ['Nº Socio:', prestamo.socio.numero_socio],
        ['', ''],
        ['Libro:', prestamo.ejemplar.libro.titulo],
        ['Autor:', prestamo.ejemplar.libro.autor],
        ['Editorial:', prestamo.ejemplar.libro.editorial or 'N/A'],
        ['ISBN:', prestamo.ejemplar.libro.isbn],
        ['Código Ejemplar:', prestamo.ejemplar.codigo_ejemplar],
        ['', ''],
        ['FECHA DE DEVOLUCIÓN:', prestamo.fecha_devolucion_prevista.strftime('%d/%m/%Y')],
    ]
    
    if not prestamo.esta_activo():
        data.append(['Devuelto el:', prestamo.fecha_devolucion_real.strftime('%d/%m/%Y')])
    
    table = Table(data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
        ('FONT', (0, 13), (-1, 13), 'Helvetica-Bold', 14),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B5B4D')),
        ('TEXTCOLOR', (0, 13), (-1, 13), colors.HexColor('#3E2723')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 12), (-1, 12), 1, colors.HexColor('#E5DDD1')),
        ('LINEABOVE', (0, 13), (-1, 13), 2, colors.HexColor('#3E2723')),
        ('BACKGROUND', (0, 13), (-1, 13), colors.HexColor('#FAF8F5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Nota al pie
    if prestamo.esta_activo():
        if prestamo.tiene_retraso():
            nota = f"ATENCIÓN: Este préstamo está vencido. Por favor devolver el ejemplar a la brevedad para evitar multas adicionales."
        else:
            nota = f"Este préstamo es válido hasta el {prestamo.fecha_devolucion_prevista.strftime('%d/%m/%Y')}. Por favor devolver antes de esa fecha."
    else:
        nota = "Este préstamo ha sido devuelto satisfactoriamente."
    
    nota_style = ParagraphStyle(
        'Nota',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#E06055') if (prestamo.esta_activo() and prestamo.tiene_retraso()) else colors.HexColor('#6B5B4D'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold' if (prestamo.esta_activo() and prestamo.tiene_retraso()) else 'Helvetica-Oblique'
    )
    elements.append(Paragraph(nota, nota_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Fecha de emisión del comprobante
    fecha_emision = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    fecha_style = ParagraphStyle(
        'Fecha',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_RIGHT
    )
    elements.append(Paragraph(f"Comprobante generado el {fecha_emision}", fecha_style))
    
    # Construir PDF
    doc.build(elements)
    return response

