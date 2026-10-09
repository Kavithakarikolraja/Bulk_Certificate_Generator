import io
import os
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.config import settings

THEME_PALETTES = {
    "gold": {
        "name": "Gold Classic",
        "primary": colors.HexColor("#1E3A8A"),      # Navy Blue
        "secondary": colors.HexColor("#D4AF37"),    # Gold
        "dark": colors.HexColor("#0F172A"),         # Slate Dark
        "accent": colors.HexColor("#B45309"),       # Amber
        "border": colors.HexColor("#D4AF37"),       # Gold Border
        "bg_tint": colors.HexColor("#FFFDF7"),
        "rgb_primary": (30, 58, 138),
        "rgb_secondary": (212, 175, 55),
        "rgb_dark": (15, 23, 42),
        "rgb_accent": (180, 83, 9),
        "rgb_border": (212, 175, 55),
        "rgb_bg": (255, 253, 247)
    },
    "indigo": {
        "name": "Indigo Modern",
        "primary": colors.HexColor("#4338CA"),
        "secondary": colors.HexColor("#6366F1"),
        "dark": colors.HexColor("#1E1B4B"),
        "accent": colors.HexColor("#06B6D4"),
        "border": colors.HexColor("#4338CA"),
        "bg_tint": colors.HexColor("#F8FAFC"),
        "rgb_primary": (67, 56, 202),
        "rgb_secondary": (99, 102, 241),
        "rgb_dark": (30, 27, 75),
        "rgb_accent": (6, 182, 212),
        "rgb_border": (67, 56, 202),
        "rgb_bg": (248, 250, 252)
    },
    "emerald": {
        "name": "Emerald Honor",
        "primary": colors.HexColor("#065F46"),
        "secondary": colors.HexColor("#10B981"),
        "dark": colors.HexColor("#022C22"),
        "accent": colors.HexColor("#F59E0B"),
        "border": colors.HexColor("#059669"),
        "bg_tint": colors.HexColor("#F0FDF4"),
        "rgb_primary": (6, 95, 70),
        "rgb_secondary": (16, 185, 129),
        "rgb_dark": (2, 44, 34),
        "rgb_accent": (245, 158, 11),
        "rgb_border": (5, 150, 105),
        "rgb_bg": (240, 253, 244)
    },
    "crimson": {
        "name": "Crimson Elite",
        "primary": colors.HexColor("#991B1B"),
        "secondary": colors.HexColor("#EF4444"),
        "dark": colors.HexColor("#450A0A"),
        "accent": colors.HexColor("#D97706"),
        "border": colors.HexColor("#991B1B"),
        "bg_tint": colors.HexColor("#FEF2F2"),
        "rgb_primary": (153, 27, 27),
        "rgb_secondary": (239, 68, 68),
        "rgb_dark": (69, 10, 10),
        "rgb_accent": (217, 119, 6),
        "rgb_border": (153, 27, 27),
        "rgb_bg": (254, 242, 242)
    },
    "platinum": {
        "name": "Platinum Executive",
        "primary": colors.HexColor("#0F172A"),
        "secondary": colors.HexColor("#64748B"),
        "dark": colors.HexColor("#020617"),
        "accent": colors.HexColor("#38BDF8"),
        "border": colors.HexColor("#475569"),
        "bg_tint": colors.HexColor("#F8FAFC"),
        "rgb_primary": (15, 23, 42),
        "rgb_secondary": (100, 116, 139),
        "rgb_dark": (2, 6, 23),
        "rgb_accent": (56, 189, 248),
        "rgb_border": (71, 85, 105),
        "rgb_bg": (248, 250, 252)
    },
    "cyberpunk": {
        "name": "Cyberpunk Tech",
        "primary": colors.HexColor("#6D28D9"),
        "secondary": colors.HexColor("#06B6D4"),
        "dark": colors.HexColor("#18181B"),
        "accent": colors.HexColor("#F43F5E"),
        "border": colors.HexColor("#8B5CF6"),
        "bg_tint": colors.HexColor("#FAF5FF"),
        "rgb_primary": (109, 40, 217),
        "rgb_secondary": (6, 182, 212),
        "rgb_dark": (24, 24, 27),
        "rgb_accent": (244, 63, 94),
        "rgb_border": (139, 92, 246),
        "rgb_bg": (250, 245, 255)
    },
    "minimalist": {
        "name": "Minimalist Luxe",
        "primary": colors.HexColor("#27272A"),
        "secondary": colors.HexColor("#E11D48"),
        "dark": colors.HexColor("#18181B"),
        "accent": colors.HexColor("#D97706"),
        "border": colors.HexColor("#A1A1AA"),
        "bg_tint": colors.HexColor("#FAFAFA"),
        "rgb_primary": (39, 39, 42),
        "rgb_secondary": (225, 29, 72),
        "rgb_dark": (24, 24, 27),
        "rgb_accent": (217, 119, 6),
        "rgb_border": (161, 161, 170),
        "rgb_bg": (250, 250, 250)
    },
    "sunset": {
        "name": "Sunset Warmth",
        "primary": colors.HexColor("#C2410C"),
        "secondary": colors.HexColor("#F59E0B"),
        "dark": colors.HexColor("#431407"),
        "accent": colors.HexColor("#EA580C"),
        "border": colors.HexColor("#EA580C"),
        "bg_tint": colors.HexColor("#FFF7ED"),
        "rgb_primary": (194, 65, 12),
        "rgb_secondary": (245, 158, 11),
        "rgb_dark": (67, 20, 7),
        "rgb_accent": (234, 88, 12),
        "rgb_border": (234, 88, 12),
        "rgb_bg": (255, 247, 237)
    }
}


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for rendering Canva-style vector graphics, decorative frames, corner accents, and seals."""
    
    def __init__(self, *args, theme="gold", cert_code="", verify_url="", **kwargs):
        super().__init__(*args, **kwargs)
        self.theme_name = theme.lower()
        self.theme_colors = THEME_PALETTES.get(self.theme_name, THEME_PALETTES["gold"])
        self.cert_code = cert_code
        self.verify_url = verify_url

    def draw_decorations(self):
        self.saveState()
        width, height = self._pagesize

        # Background Subtle Tint Fill
        self.setFillColor(self.theme_colors["bg_tint"])
        self.rect(0, 0, width, height, fill=1, stroke=0)

        # Outer Frame
        self.setStrokeColor(self.theme_colors["border"])
        self.setLineWidth(3.5)
        self.rect(0.35 * inch, 0.35 * inch, width - 0.7 * inch, height - 0.7 * inch)

        # Inner Thin Frame
        self.setLineWidth(1)
        self.rect(0.43 * inch, 0.43 * inch, width - 0.86 * inch, height - 0.86 * inch)

        # Corner Vector Ornaments
        c_size = 0.4 * inch
        
        # Top-Left Ornament
        p1 = self.beginPath()
        p1.moveTo(0.43 * inch, height - 0.43 * inch - c_size)
        p1.lineTo(0.43 * inch, height - 0.43 * inch)
        p1.lineTo(0.43 * inch + c_size, height - 0.43 * inch)
        p1.close()
        self.setFillColor(self.theme_colors["primary"])
        self.drawPath(p1, fill=1, stroke=0)

        # Top-Right Ornament
        p2 = self.beginPath()
        p2.moveTo(width - 0.43 * inch - c_size, height - 0.43 * inch)
        p2.lineTo(width - 0.43 * inch, height - 0.43 * inch)
        p2.lineTo(width - 0.43 * inch, height - 0.43 * inch - c_size)
        p2.close()
        self.drawPath(p2, fill=1, stroke=0)

        # Bottom-Left Ornament
        p3 = self.beginPath()
        p3.moveTo(0.43 * inch, 0.43 * inch + c_size)
        p3.lineTo(0.43 * inch, 0.43 * inch)
        p3.lineTo(0.43 * inch + c_size, 0.43 * inch)
        p3.close()
        self.drawPath(p3, fill=1, stroke=0)

        # Bottom-Right Ornament
        p4 = self.beginPath()
        p4.moveTo(width - 0.43 * inch - c_size, 0.43 * inch)
        p4.lineTo(width - 0.43 * inch, 0.43 * inch)
        p4.lineTo(width - 0.43 * inch, 0.43 * inch + c_size)
        p4.close()
        self.drawPath(p4, fill=1, stroke=0)

        # Gold Ribbon & Rosette Seal
        seal_x = 1.25 * inch
        seal_y = 1.25 * inch
        
        self.setFillColor(self.theme_colors["secondary"])
        self.circle(seal_x, seal_y, 0.38 * inch, fill=1, stroke=0)
        
        self.setFillColor(self.theme_colors["primary"])
        self.circle(seal_x, seal_y, 0.30 * inch, fill=1, stroke=0)
        
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 7)
        self.drawCentredString(seal_x, seal_y + 2, "OFFICIAL")
        self.setFont("Helvetica-Bold", 6)
        self.drawCentredString(seal_x, seal_y - 6, "VERIFIED")

        # Certificate Code Details
        self.setFillColor(self.theme_colors["dark"])
        self.setFont("Helvetica-Bold", 8)
        self.drawString(1.75 * inch, 1.2 * inch, f"CERTIFICATE ID: {self.cert_code}")
        self.setFont("Helvetica", 7)
        self.drawString(1.75 * inch, 1.05 * inch, "Authentic Digital Verification Record")

        self.restoreState()


def generate_qr_code_image(url: str) -> Image.Image:
    """Generates a PIL Image QR code for verification."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=3,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGB")


def generate_qr_code_buffer(url: str) -> io.BytesIO:
    """Generates a high-contrast QR code buffer for reportlab."""
    qr_img = generate_qr_code_image(url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_certificate_pdf(
    recipient_name: str,
    course_title: str,
    issuer_name: str,
    issue_date: str,
    certificate_code: str,
    output_path: str,
    template_theme: str = "gold",
    cert_heading: str = "CERTIFICATE OF ACHIEVEMENT"
) -> str:
    """
    Generates a Canva-grade vector PDF certificate using ReportLab.
    """
    theme = template_theme.lower()
    palette = THEME_PALETTES.get(theme, THEME_PALETTES["gold"])

    page_width, page_height = landscape(letter)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
        textColor=palette["primary"],
        spaceAfter=14
    )

    subtitle_style = ParagraphStyle(
        'CertSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=palette["accent"],
        spaceAfter=14
    )

    recipient_style = ParagraphStyle(
        'CertRecipient',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        textColor=palette["dark"],
        spaceAfter=14
    )

    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        textColor=palette["dark"],
        spaceAfter=10
    )

    course_style = ParagraphStyle(
        'CertCourse',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        textColor=palette["primary"],
        spaceAfter=18
    )

    meta_style = ParagraphStyle(
        'CertMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )

    elements = []
    elements.append(Spacer(1, 0.4 * inch))

    # Issuer Header
    elements.append(Paragraph(f"<b>{issuer_name.upper()}</b>", subtitle_style))
    elements.append(Spacer(1, 0.08 * inch))

    # Main Certificate Title (Customizable heading)
    heading_text = cert_heading.strip().upper() if cert_heading else "CERTIFICATE OF ACHIEVEMENT"
    elements.append(Paragraph(heading_text, title_style))
    elements.append(Spacer(1, 0.05 * inch))

    # Subtitle
    elements.append(Paragraph("THIS CERTIFICATE IS PROUDLY PRESENTED TO", subtitle_style))
    elements.append(Spacer(1, 0.1 * inch))

    # Recipient Name
    elements.append(Paragraph(f"<u>{recipient_name}</u>", recipient_style))
    elements.append(Spacer(1, 0.1 * inch))

    # Body statement
    elements.append(Paragraph("for outstanding performance and successful completion of the specialized training program", body_style))
    elements.append(Spacer(1, 0.05 * inch))

    # Course Title
    elements.append(Paragraph(f"“{course_title}”", course_style))
    elements.append(Spacer(1, 0.1 * inch))

    # Verification QR Code
    verify_url = f"{settings.BASE_VERIFY_URL}/{certificate_code}"
    qr_buf = generate_qr_code_buffer(verify_url)
    qr_img = RLImage(qr_buf, width=0.85 * inch, height=0.85 * inch)

    # Footer Table
    footer_data = [
        [
            Paragraph(f"<b>{issue_date}</b><br/><font color='#64748B'>Date of Issuance</font>", meta_style),
            Paragraph(f"<b>{issuer_name}</b><br/><font color='#64748B'>Authorized Signature</font>", meta_style),
            qr_img
        ]
    ]

    footer_table = Table(footer_data, colWidths=[2.5 * inch, 3.5 * inch, 1.5 * inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, 0), (0, 0), 1, palette["secondary"]),
        ('LINEABOVE', (1, 0), (1, 0), 1, palette["secondary"]),
    ]))

    elements.append(footer_table)

    def on_page(canvas_obj, doc_obj):
        nc = NumberedCanvas(canvas_obj._filename, theme=theme, cert_code=certificate_code, verify_url=verify_url)
        nc._pagesize = (page_width, page_height)
        nc.draw_decorations()

    doc.build(elements, onFirstPage=on_page)
    return output_path


def generate_certificate_image_bytes(
    recipient_name: str,
    course_title: str,
    issuer_name: str,
    issue_date: str,
    certificate_code: str = "CERT-PREVIEW-001",
    template_theme: str = "gold",
    cert_heading: str = "CERTIFICATE OF ACHIEVEMENT"
) -> bytes:
    """
    Renders a crisp, high-resolution PNG image (image/png) of the certificate design.
    This guarantees that clicking 'See Certificate Design' displays an inline visual image
    WITHOUT ANY PDF DOWNLOAD POPUP OR PROMPT IN ANY BROWSER.
    """
    theme = template_theme.lower()
    palette = THEME_PALETTES.get(theme, THEME_PALETTES["gold"])

    # High definition landscape dimensions
    W, H = 1200, 850
    img = Image.new("RGB", (W, H), palette["rgb_bg"])
    draw = ImageDraw.Draw(img)

    # 1. Outer Border
    border_col = palette["rgb_border"]
    draw.rectangle([30, 30, W - 30, H - 30], outline=border_col, width=8)
    draw.rectangle([45, 45, W - 45, H - 45], outline=border_col, width=2)

    # 2. Corner Vector Triangles
    c_len = 45
    primary_col = palette["rgb_primary"]
    draw.polygon([(45, 45 + c_len), (45, 45), (45 + c_len, 45)], fill=primary_col)
    draw.polygon([(W - 45 - c_len, 45), (W - 45, 45), (W - 45, 45 + c_len)], fill=primary_col)
    draw.polygon([(45, H - 45 - c_len), (45, H - 45), (45 + c_len, H - 45)], fill=primary_col)
    draw.polygon([(W - 45 - c_len, H - 45), (W - 45, H - 45), (W - 45, H - 45 - c_len)], fill=primary_col)

    # 3. Text Layout (Centered)
    dark_col = palette["rgb_dark"]
    accent_col = palette["rgb_accent"]

    # Fonts fallback to default PIL font
    try:
        font_issuer = ImageFont.truetype("arial.ttf", 22)
        font_heading = ImageFont.truetype("arialbd.ttf", 38)
        font_sub = ImageFont.truetype("arialbd.ttf", 18)
        font_name = ImageFont.truetype("arialbd.ttf", 44)
        font_body = ImageFont.truetype("arial.ttf", 18)
        font_course = ImageFont.truetype("arialbd.ttf", 30)
        font_meta = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 13)
    except IOError:
        font_issuer = font_heading = font_sub = font_name = font_body = font_course = font_meta = font_small = ImageFont.load_default()

    # Issuer
    draw.text((W // 2, 100), issuer_name.upper(), fill=accent_col, font=font_issuer, anchor="mm")
    
    # Heading
    heading_txt = cert_heading.strip().upper() if cert_heading else "CERTIFICATE OF ACHIEVEMENT"
    draw.text((W // 2, 160), heading_txt, fill=primary_col, font=font_heading, anchor="mm")

    # Subtitle
    draw.text((W // 2, 220), "THIS CERTIFICATE IS PROUDLY PRESENTED TO", fill=accent_col, font=font_sub, anchor="mm")

    # Recipient Name
    draw.text((W // 2, 300), recipient_name, fill=dark_col, font=font_name, anchor="mm")
    # Underline
    name_bbox = draw.textbbox((W // 2, 300), recipient_name, font=font_name, anchor="mm")
    draw.line([name_bbox[0], name_bbox[3] + 8, name_bbox[2], name_bbox[3] + 8], fill=palette["rgb_secondary"], width=3)

    # Body
    draw.text((W // 2, 380), "for outstanding performance and successful completion of the specialized training program", fill=dark_col, font=font_body, anchor="mm")

    # Course Title
    draw.text((W // 2, 450), f"“{course_title}”", fill=primary_col, font=font_course, anchor="mm")

    # Footer Divider Line
    draw.line([120, 680, W - 120, 680], fill=palette["rgb_secondary"], width=2)

    # Date
    draw.text((250, 710), issue_date, fill=dark_col, font=font_meta, anchor="mm")
    draw.text((250, 735), "Date of Issuance", fill=(100, 116, 139), font=font_small, anchor="mm")

    # Signature
    draw.text((W // 2, 710), issuer_name, fill=dark_col, font=font_meta, anchor="mm")
    draw.text((W // 2, 735), "Authorized Signature", fill=(100, 116, 139), font=font_small, anchor="mm")

    # Seal at bottom left
    seal_cx, seal_cy = 130, 720
    draw.ellipse([seal_cx - 40, seal_cy - 40, seal_cx + 40, seal_cy + 40], fill=palette["rgb_secondary"])
    draw.ellipse([seal_cx - 32, seal_cy - 32, seal_cx + 32, seal_cy + 32], fill=primary_col)
    draw.text((seal_cx, seal_cy - 5), "OFFICIAL", fill=(255, 255, 255), font=font_small, anchor="mm")
    draw.text((seal_cx, seal_cy + 10), "VERIFIED", fill=(255, 255, 255), font=font_small, anchor="mm")

    # Verification QR Code at bottom right
    verify_url = f"{settings.BASE_VERIFY_URL}/{certificate_code}"
    qr_img = generate_qr_code_image(verify_url)
    qr_img = qr_img.resize((90, 90))
    img.paste(qr_img, (W - 200, 690))

    # Certificate ID text
    draw.text((W - 155, 795), f"ID: {certificate_code}", fill=dark_col, font=font_small, anchor="mm")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
