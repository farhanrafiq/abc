from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import datetime
from flask import current_app
import io
import logging

def generate_invoice_pdf(order):
    """Generate GST invoice PDF for order"""
    buffer = io.BytesIO()
    
    try:
        # Create document
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Build story (content)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#3B2A22')
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#5A4034')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Company header
        story.append(Paragraph("ABC Publishing Kashmir", title_style))
        story.append(Paragraph("GST INVOICE", header_style))
        story.append(Spacer(1, 12))
        
        # Company details
        company_details = [
            "ABC Publishing Kashmir",
            "Srinagar, Jammu & Kashmir, India",
            f"Email: {current_app.config.get('STORE_EMAIL', 'info@abcpublishingkashmir.com')}",
            f"Phone: {current_app.config.get('STORE_PHONE', '+91-194-XXXXXX')}",
            "GSTIN: (If applicable)"
        ]
        
        for detail in company_details:
            story.append(Paragraph(detail, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Invoice details table
        invoice_data = [
            ['Invoice No:', f'INV-{order.id:06d}', 'Date:', order.created_at.strftime('%d/%m/%Y')],
            ['Order No:', f'#{order.id}', 'Payment Method:', order.payment_method.value if order.payment_method else 'N/A']
        ]
        
        invoice_table = Table(invoice_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F2E9E4')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 20))
        
        # Billing address
        story.append(Paragraph("Bill To:", header_style))
        if order.billing_address:
            billing_address = [
                order.billing_address.name,
                order.billing_address.line1,
                order.billing_address.line2 if order.billing_address.line2 else '',
                f"{order.billing_address.city}, {order.billing_address.district}",
                f"{order.billing_address.state} - {order.billing_address.pincode}",
                order.billing_address.country
            ]
            for line in billing_address:
                if line.strip():
                    story.append(Paragraph(line, normal_style))
        else:
            story.append(Paragraph(f"Email: {order.email}", normal_style))
            story.append(Paragraph(f"Phone: {order.phone}", normal_style))
        
        story.append(Spacer(1, 20))
        
        # Order items table
        story.append(Paragraph("Order Details:", header_style))
        
        items_data = [['S.No.', 'Description', 'HSN', 'Qty', 'Rate (₹)', 'Amount (₹)']]
        
        for i, item in enumerate(order.items, 1):
            items_data.append([
                str(i),
                item.title_snapshot,
                '4901',  # HSN code for books
                str(item.quantity),
                f"{item.unit_price_inr / 100:.2f}",
                f"{item.line_total_inr / 100:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 3*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B2A22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Product name left aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals table
        totals_data = [
            ['Subtotal:', f"₹{order.subtotal_inr / 100:.2f}"],
            ['Discount:', f"-₹{order.discount_inr / 100:.2f}"],
            ['Shipping:', f"₹{order.shipping_inr / 100:.2f}"],
            ['Tax (0%):', f"₹{order.tax_inr / 100:.2f}"],
            ['Total Amount:', f"₹{order.grand_total_inr / 100:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E86A17')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        # Payment details
        if order.payment_method and order.payment_method != 'COD':
            story.append(Paragraph("Payment Details:", header_style))
            story.append(Paragraph(f"Payment Method: {order.payment_method.value}", normal_style))
            story.append(Paragraph(f"Payment Status: {order.payment_status.value}", normal_style))
            if order.razorpay_payment_id:
                story.append(Paragraph(f"Transaction ID: {order.razorpay_payment_id}", normal_style))
            story.append(Spacer(1, 20))
        
        # Terms and conditions
        story.append(Paragraph("Terms & Conditions:", header_style))
        terms = [
            "1. All sales are final unless otherwise specified.",
            "2. Books are returnable within 7 days of delivery if in original condition.",
            "3. Shipping charges are non-refundable.",
            "4. For any queries, contact us at the above email/phone number."
        ]
        
        for term in terms:
            story.append(Paragraph(term, normal_style))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        story.append(Paragraph("Thank you for shopping with ABC Publishing Kashmir!", footer_style))
        story.append(Paragraph("This is a computer-generated invoice.", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return io.BytesIO(pdf_data)
    
    except Exception as e:
        logging.error(f"PDF generation failed: {e}")
        buffer.close()
        raise

def generate_packing_slip_pdf(order):
    """Generate packing slip PDF for order"""
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        story.append(Paragraph("PACKING SLIP", title_style))
        
        # Order info
        story.append(Paragraph(f"Order ID: #{order.id}", styles['Heading2']))
        story.append(Paragraph(f"Date: {order.created_at.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Shipping address
        story.append(Paragraph("Ship To:", styles['Heading3']))
        if order.shipping_address:
            address_lines = [
                order.shipping_address.name,
                order.shipping_address.line1,
                order.shipping_address.line2 if order.shipping_address.line2 else '',
                f"{order.shipping_address.city}, {order.shipping_address.district}",
                f"{order.shipping_address.state} - {order.shipping_address.pincode}"
            ]
            for line in address_lines:
                if line.strip():
                    story.append(Paragraph(line, styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Items
        story.append(Paragraph("Items:", styles['Heading3']))
        
        items_data = [['Item', 'SKU', 'Quantity']]
        for item in order.items:
            items_data.append([
                item.title_snapshot,
                item.sku_snapshot,
                str(item.quantity)
            ])
        
        items_table = Table(items_data, colWidths=[4*inch, 1.5*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(items_table)
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return io.BytesIO(pdf_data)
    
    except Exception as e:
        logging.error(f"Packing slip generation failed: {e}")
        buffer.close()
        raise

def generate_shipping_label_pdf(order, shipment):
    """Generate shipping label PDF"""
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("SHIPPING LABEL", styles['Title']))
        story.append(Spacer(1, 30))
        
        # From address
        story.append(Paragraph("FROM:", styles['Heading3']))
        story.append(Paragraph("ABC Publishing Kashmir", styles['Normal']))
        story.append(Paragraph("Srinagar, Jammu & Kashmir", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # To address
        story.append(Paragraph("TO:", styles['Heading3']))
        if order.shipping_address:
            address_lines = [
                order.shipping_address.name,
                order.shipping_address.line1,
                order.shipping_address.line2 if order.shipping_address.line2 else '',
                f"{order.shipping_address.city}, {order.shipping_address.district}",
                f"{order.shipping_address.state} - {order.shipping_address.pincode}"
            ]
            for line in address_lines:
                if line.strip():
                    story.append(Paragraph(line, styles['Normal']))
        
        story.append(Spacer(1, 30))
        
        # Shipment details
        if shipment.tracking_no:
            story.append(Paragraph(f"Tracking No: {shipment.tracking_no}", styles['Heading2']))
        
        story.append(Paragraph(f"Order ID: #{order.id}", styles['Normal']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return io.BytesIO(pdf_data)
    
    except Exception as e:
        logging.error(f"Shipping label generation failed: {e}")
        buffer.close()
        raise
