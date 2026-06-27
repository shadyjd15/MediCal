import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from .. import models, auth
from ..database import get_db

router = APIRouter(prefix="/api/export", tags=["export"])


def _enum_val(v):
    return v.value if hasattr(v, "value") else v


def _scoped_meds(db, user):
    q = db.query(models.Medicine).join(models.Prescription).options(
        joinedload(models.Medicine.tags), joinedload(models.Medicine.prescription)
    )
    if user.role != models.RoleEnum.admin:
        q = q.filter(models.Prescription.user_id == user.id)
    return q.order_by(models.Prescription.visit_date.desc()).all()


def _scoped_prescriptions(db, user):
    q = db.query(models.Prescription).options(
        joinedload(models.Prescription.medicines), joinedload(models.Prescription.cost_items)
    )
    if user.role != models.RoleEnum.admin:
        q = q.filter(models.Prescription.user_id == user.id)
    return q.order_by(models.Prescription.visit_date.desc()).all()


# ---------------- CSV ----------------

@router.get("/medicines.csv")
def export_medicines_csv(db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    meds = _scoped_meds(db, user)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Composition", "Dose", "Frequency", "Status", "Doctor", "Hospital", "Visit Date",
                      "Start Date", "End Date", "Manufacturer", "Quantity Remaining", "Cost", "Payment Method", "Tags"])
    for m in meds:
        writer.writerow([
            m.name, m.composition, m.dose, m.frequency or "", "Active" if m.is_active else "Inactive",
            m.prescription.doctor_name, m.prescription.hospital_name, m.prescription.visit_date,
            m.start_date or "", m.end_date or "", m.manufacturer or "", m.quantity_remaining or "",
            m.cost or "", _enum_val(m.payment_method) or "", ", ".join(t.name for t in m.tags),
        ])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                              headers={"Content-Disposition": "attachment; filename=medicines.csv"})


@router.get("/visits.csv")
def export_visits_csv(db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    visits = _scoped_prescriptions(db, user)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Doctor", "Hospital", "Visit Date", "Next Visit", "Payment Method", "Total Cost",
                      "BP Systolic", "BP Diastolic", "Weight (kg)", "Heart Rate", "Medicines Count", "Notes"])
    for p in visits:
        writer.writerow([
            p.doctor_name, p.hospital_name, p.visit_date, p.next_visit_date or "", _enum_val(p.payment_method) or "",
            sum(c.amount for c in p.cost_items), p.bp_systolic or "", p.bp_diastolic or "", p.weight_kg or "",
            p.heart_rate or "", len(p.medicines), (p.notes or "").replace("\n", " "),
        ])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                              headers={"Content-Disposition": "attachment; filename=visits.csv"})


@router.get("/spending.csv")
def export_spending_csv(year: int = Query(default=None), db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    year = year or date.today().year
    visits = _scoped_prescriptions(db, user)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Visit Date", "Doctor", "Hospital", "Category", "Payment Method", "Amount", "Description"])
    for p in visits:
        if p.visit_date.year != year:
            continue
        for c in p.cost_items:
            writer.writerow([p.visit_date, p.doctor_name, p.hospital_name, _enum_val(c.category),
                              _enum_val(c.payment_method), c.amount, c.description or ""])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                              headers={"Content-Disposition": f"attachment; filename=spending-{year}.csv"})


# ---------------- PDF ----------------

def _build_pdf(title: str, subtitle: str, headers, rows):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    brand = colors.HexColor("#1A56F0")

    elements = [
        Paragraph('<font color="#1A56F0" size=18><b>MediCal</b></font>', styles["Title"]),
        Paragraph(title, styles["Heading2"]),
        Paragraph(subtitle, styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    data = [headers] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E3E8EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFA")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf


@router.get("/medicines.pdf")
def export_medicines_pdf(db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    meds = _scoped_meds(db, user)
    rows = [[m.name, m.composition, m.dose, "Active" if m.is_active else "Inactive",
             m.prescription.doctor_name, str(m.prescription.visit_date)] for m in meds]
    buf = _build_pdf("Medication History", f"{len(meds)} medicines · generated {date.today()}",
                      ["Name", "Composition", "Dose", "Status", "Doctor", "Visit Date"], rows)
    return StreamingResponse(buf, media_type="application/pdf",
                              headers={"Content-Disposition": "attachment; filename=medication-history.pdf"})


@router.get("/visits.pdf")
def export_visits_pdf(db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    visits = _scoped_prescriptions(db, user)
    rows = [[p.doctor_name, p.hospital_name, str(p.visit_date), _enum_val(p.payment_method) or "—",
             f"{sum(c.amount for c in p.cost_items):.2f}", str(len(p.medicines))] for p in visits]
    buf = _build_pdf("Doctor Visit History", f"{len(visits)} visits · generated {date.today()}",
                      ["Doctor", "Hospital", "Date", "Payment", "Total Cost", "Medicines"], rows)
    return StreamingResponse(buf, media_type="application/pdf",
                              headers={"Content-Disposition": "attachment; filename=visit-history.pdf"})


@router.get("/spending.pdf")
def export_spending_pdf(year: int = Query(default=None), db: Session = Depends(get_db), user: models.User = Depends(auth.get_current_user)):
    year = year or date.today().year
    visits = _scoped_prescriptions(db, user)
    rows = []
    for p in visits:
        if p.visit_date.year != year:
            continue
        for c in p.cost_items:
            rows.append([str(p.visit_date), p.doctor_name, _enum_val(c.category), _enum_val(c.payment_method), f"{c.amount:.2f}"])
    buf = _build_pdf(f"Spending Report — {year}", f"{len(rows)} cost entries · generated {date.today()}",
                      ["Visit Date", "Doctor", "Category", "Payment", "Amount"], rows)
    return StreamingResponse(buf, media_type="application/pdf",
                              headers={"Content-Disposition": f"attachment; filename=spending-{year}.pdf"})
