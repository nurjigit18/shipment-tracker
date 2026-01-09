"""PDF generation service for shipment reports with QR codes."""
import io
from typing import Any
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class PDFService:
    """Service for generating PDF reports with QR codes."""

    # Class variable to track if fonts are registered
    _fonts_registered = False

    @staticmethod
    def _register_fonts():
        """Register fonts that support Cyrillic characters."""
        if PDFService._fonts_registered:
            return

        try:
            # Try to use DejaVu fonts (commonly available)
            # These fonts support Cyrillic and many other character sets
            import os
            from pathlib import Path

            # Try common font locations
            font_locations = [
                # Windows
                r"C:\Windows\Fonts\DejaVuSans.ttf",
                r"C:\Windows\Fonts\dejavu-sans.ttf",
                # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                # Mac
                "/Library/Fonts/DejaVuSans.ttf",
                # Python site-packages (if installed via package)
                str(Path(__file__).parent.parent.parent / "fonts" / "DejaVuSans.ttf"),
            ]

            # Try Arial as fallback (Windows)
            arial_locations = [
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\Arial.ttf",
            ]

            font_registered = False

            # Try DejaVu first
            for font_path in font_locations:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
                        print(f"✓ Registered DejaVuSans from {font_path}")
                        font_registered = True
                        break
                    except Exception as e:
                        print(f"Failed to register font from {font_path}: {e}")
                        continue

            # Try Arial as fallback
            if not font_registered:
                for font_path in arial_locations:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
                            print(f"✓ Registered Arial as DejaVuSans from {font_path}")
                            font_registered = True
                            break
                        except Exception as e:
                            print(f"Failed to register Arial from {font_path}: {e}")
                            continue

            if font_registered:
                PDFService._fonts_registered = True
            else:
                print("⚠ Warning: No Cyrillic-compatible font found. PDF may have display issues with Russian text.")

        except Exception as e:
            print(f"Error registering fonts: {e}")

    @staticmethod
    def generate_shipment_pdf(shipment_data: dict, base_url: str = "") -> bytes:
        """
        Generate a PDF report for a shipment with embedded QR code.

        Args:
            shipment_data: Dictionary containing shipment information
            base_url: Base URL for QR code generation (e.g., https://yourdomain.com)

        Returns:
            PDF file as bytes
        """
        # Register Cyrillic-compatible fonts
        PDFService._register_fonts()

        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # Container for elements
        elements = []

        # Styles
        styles = getSampleStyleSheet()

        # Determine which font to use
        font_name = 'DejaVuSans' if PDFService._fonts_registered else 'Helvetica'

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#00bfff'),
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName=font_name
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0091cc'),
            spaceAfter=10,
            fontName=font_name
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            fontName=font_name
        )

        # Title
        elements.append(Paragraph("Nova Eris Tracking", title_style))
        elements.append(Paragraph("Отчет об отправке", heading_style))
        elements.append(Spacer(1, 10*mm))

        # Generate QR Code
        shipment_id = shipment_data.get('id', '')
        qr_url = f"{base_url}/shipments/{shipment_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Add QR code image
        qr_image = Image(qr_buffer, width=60*mm, height=60*mm)

        # Create a table for QR code and shipment ID
        qr_table_data = [
            [qr_image, [
                Paragraph(f"<b>ID Отправки:</b>", normal_style),
                Paragraph(f"<font size=14><b>{shipment_id}</b></font>", normal_style),
                Spacer(1, 5*mm),
                Paragraph(f"<i>Отсканируйте QR-код для<br/>отслеживания статуса</i>", normal_style)
            ]]
        ]

        qr_table = Table(qr_table_data, colWidths=[70*mm, 100*mm])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#00bfff')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e0f7ff')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(qr_table)
        elements.append(Spacer(1, 10*mm))

        # Shipment Information Section
        elements.append(Paragraph("<b>Информация об отправке</b>", heading_style))

        route_type_label = "Прямой" if shipment_data.get('route_type') == 'DIRECT' else "Через ФФ"

        info_data = [
            ['Поставщик:', shipment_data.get('supplier', '—')],
            ['Склад:', shipment_data.get('warehouse', '—')],
            ['Маршрут:', route_type_label],
            ['Дата отправки:', shipment_data.get('shipment_date', '—')],
            ['Текущий статус:', PDFService._get_status_label(shipment_data.get('current_status'))],
        ]

        info_table = Table(info_data, colWidths=[50*mm, 120*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 10*mm))

        # Totals Section
        totals = shipment_data.get('totals', {})
        elements.append(Paragraph("<b>Сводка</b>", heading_style))

        totals_data = [
            ['Количество мешков:', str(totals.get('bags', 0))],
            ['Общее количество вещей:', str(totals.get('pieces', 0))],
        ]

        totals_table = Table(totals_data, colWidths=[80*mm, 90*mm])
        totals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(totals_table)
        elements.append(Spacer(1, 10*mm))

        # Bags Information
        bags = shipment_data.get('bags', [])
        if bags:
            elements.append(Paragraph("<b>Содержимое мешков</b>", heading_style))

            for bag in bags:
                elements.append(Paragraph(f"<b>{bag.get('bag_id', '')}</b>", normal_style))

                # Items in bag
                items = bag.get('items', [])
                for item in items:
                    model = item.get('model', '')
                    color = item.get('color', '')
                    sizes = item.get('sizes', {})

                    # Create size string
                    size_list = [f"{size}: {qty}" for size, qty in sizes.items() if qty > 0]
                    size_str = ", ".join(size_list) if size_list else "—"

                    item_text = f"• {model} - {color}<br/>&nbsp;&nbsp;&nbsp;&nbsp;Размеры: {size_str}"
                    elements.append(Paragraph(item_text, normal_style))

                elements.append(Spacer(1, 5*mm))

        # Footer
        elements.append(Spacer(1, 15*mm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName=font_name
        )
        elements.append(Paragraph("Сгенерировано системой Nova Eris Tracking", footer_style))
        elements.append(Paragraph(f"URL: {qr_url}", footer_style))

        # Build PDF
        doc.build(elements)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    @staticmethod
    def _get_status_label(status: str | None) -> str:
        """Get Russian label for status."""
        status_labels = {
            'SENT_FROM_FACTORY': 'Отправлено от Поставщика',
            'SHIPPED_FROM_FF': 'Отправлено из Фулфилмента',
            'DELIVERED': 'Доставлено',
        }
        return status_labels.get(status, 'Новая') if status else 'Новая'
