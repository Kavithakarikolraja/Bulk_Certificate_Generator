import os
from pathlib import Path
from fastapi import APIRouter, Query, Response
from fastapi.responses import FileResponse

from app.config import settings
from app.services.generator import generate_certificate_pdf, generate_certificate_image_bytes, THEME_PALETTES

router = APIRouter(prefix="/templates", tags=["Certificate Templates"])


@router.get("/preview-image")
def preview_template_image(
    theme: str = Query("gold", description="Template theme: gold, indigo, emerald, crimson, platinum, cyberpunk, minimalist, sunset"),
    recipient_name: str = Query("Jane Doe", description="Sample recipient name"),
    course_title: str = Query("Advanced Python & Cloud Architecture Masterclass", description="Sample course title"),
    issuer_name: str = Query("Global Tech Institute", description="Sample issuer"),
    issue_date: str = Query("2026-10-09", description="Sample issue date"),
    cert_heading: str = Query("CERTIFICATE OF ACHIEVEMENT", description="Custom certificate heading")
):
    """
    Renders and returns a high-resolution PNG image (image/png) of the certificate.
    Used by the Web Studio to display design samples 100% inline without triggering any PDF download dialogs in any browser.
    """
    selected_theme = theme.lower() if theme.lower() in THEME_PALETTES else "gold"

    img_bytes = generate_certificate_image_bytes(
        recipient_name=recipient_name,
        course_title=course_title,
        issuer_name=issuer_name,
        issue_date=issue_date,
        certificate_code="CERT-PREVIEW-001",
        template_theme=selected_theme,
        cert_heading=cert_heading
    )

    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@router.get("/preview")
def preview_template(
    theme: str = Query("gold", description="Template theme: gold, indigo, emerald, crimson, platinum, cyberpunk, minimalist, sunset"),
    recipient_name: str = Query("Jane Doe", description="Sample recipient name"),
    course_title: str = Query("Advanced Python & Cloud Architecture Masterclass", description="Sample course title"),
    issuer_name: str = Query("Global Tech Institute", description="Sample issuer"),
    issue_date: str = Query("2026-10-09", description="Sample issue date"),
    cert_heading: str = Query("CERTIFICATE OF ACHIEVEMENT", description="Custom certificate heading")
):
    """
    Generates and returns a preview PDF certificate for design inspection.
    """
    selected_theme = theme.lower() if theme.lower() in THEME_PALETTES else "gold"
    preview_filename = f"Preview_{selected_theme}.pdf"
    preview_path = str(settings.TEMP_DIR / preview_filename)

    generate_certificate_pdf(
        recipient_name=recipient_name,
        course_title=course_title,
        issuer_name=issuer_name,
        issue_date=issue_date,
        certificate_code="CERT-PREVIEW-001",
        output_path=preview_path,
        template_theme=selected_theme,
        cert_heading=cert_heading
    )

    return FileResponse(
        path=preview_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=preview.pdf"}
    )


@router.get("/themes")
def list_template_themes():
    """
    Returns all available Canva-style certificate design themes.
    """
    themes_list = []
    for key, data in THEME_PALETTES.items():
        themes_list.append({
            "id": key,
            "name": data["name"],
            "primary": data["primary"].hexval(),
            "secondary": data["secondary"].hexval(),
            "accent": data["accent"].hexval()
        })
    return {"themes": themes_list}
