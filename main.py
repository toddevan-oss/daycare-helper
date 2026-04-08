#!/usr/bin/env python3
"""
Daycare Instruction Sheet Generator
Generates a printable PDF with nap schedule, feeding times, and instructions.
"""

import json
import os
from datetime import datetime, date
from fpdf import FPDF, XPos, YPos

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "baby_name": "Baby",
    "parent_contact": "",
    "feeding_instructions": [
        "Warm breast milk bottles in warm water for 2 minutes — do not microwave",
        "Shake gently before feeding",
        "Discard any unused milk after 1 hour of feeding"
    ]
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    print("No config.json found — creating one with defaults. Edit it to customize.")
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def prompt(question, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{question}{suffix}: ").strip()
    return val if val else (default or "")


def collect_naps():
    naps = []
    print("\n--- NAP SCHEDULE ---")
    print("Enter each nap (leave start time blank when done):\n")
    i = 1
    while True:
        start = input(f"  Nap {i} start time (e.g. 10:00am, leave blank to finish): ").strip()
        if not start:
            break
        duration = prompt(f"  Nap {i} target duration (e.g. 1h 30min)", "-")
        naps.append({"num": i, "start": start, "duration": duration})
        i += 1
    return naps


def collect_feedings():
    feedings = []
    print("\n--- FEEDING SCHEDULE ---")
    print("Enter each feeding (leave time blank when done):\n")
    i = 1
    while True:
        time = input(f"  Feeding {i} time (e.g. 8:00am, leave blank to finish): ").strip()
        if not time:
            break
        amount = prompt(f"  Feeding {i} amount (e.g. 4oz or 10 min)", "-")
        ftype = prompt(f"  Feeding {i} type", "breast milk")
        feedings.append({"time": time, "amount": amount, "type": ftype})
        i += 1
    return feedings


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

BLUE_FILL = (224, 236, 255)
GRAY_FILL = (242, 242, 242)
BORDER_COLOR = (180, 180, 180)


def safe(text):
    """Strip characters unsupported by Helvetica (latin-1 only)."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def section_header(pdf, title):
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(*BLUE_FILL)
    pdf.set_draw_color(*BORDER_COLOR)
    pdf.cell(0, 9, safe(f"  {title}"), border=1, fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)


def table_header(pdf, headers, widths):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*GRAY_FILL)
    pdf.set_draw_color(*BORDER_COLOR)
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, safe(f"  {header}"), border=1, fill=True,
                 new_x=XPos.RIGHT, new_y=YPos.LAST)
    pdf.ln()


def table_row(pdf, values, widths, shade=False):
    pdf.set_font("Helvetica", "", 10)
    if shade:
        pdf.set_fill_color(250, 250, 250)
    else:
        pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(*BORDER_COLOR)
    for value, width in zip(values, widths):
        pdf.cell(width, 7, safe(f"  {value}"), border=1, fill=True,
                 new_x=XPos.RIGHT, new_y=YPos.LAST)
    pdf.ln()


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def generate_pdf(config, sheet_date, naps, feedings, notes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)

    # ---- Header ----
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(40, 60, 120)
    pdf.cell(0, 12, "Daycare Instructions", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, f"{config['baby_name']}  |  {sheet_date}", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if config.get("parent_contact"):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"Parent contact: {config['parent_contact']}", align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)
    pdf.set_draw_color(*BORDER_COLOR)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())

    # ---- Nap Schedule ----
    section_header(pdf, "Nap Schedule")
    if naps:
        widths = [20, 60, 60, 40]
        table_header(pdf, ["#", "Start Time", "Target Duration", "Wake Window Note"], widths)
        for idx, nap in enumerate(naps):
                table_row(pdf, [str(nap["num"]), nap["start"], nap["duration"], nap.get("wake_note", "")], widths, shade=idx % 2 == 1)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 7, "  No naps scheduled", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    # ---- Feeding Schedule ----
    section_header(pdf, "Feeding Schedule")
    if feedings:
        widths = [45, 40, 55, 40]
        table_header(pdf, ["Time", "Amount", "Type", "Notes"], widths)
        for idx, f in enumerate(feedings):
            table_row(pdf, [f["time"], f["amount"], f["type"], f.get("note", "")], widths, shade=idx % 2 == 1)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 7, "  No feedings scheduled", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    # ---- Feeding Instructions ----
    section_header(pdf, "Feeding Instructions")
    instructions = config.get("feeding_instructions", [])
    if instructions:
        pdf.set_font("Helvetica", "", 10)
        for i, instruction in enumerate(instructions, 1):
            pdf.set_x(15)
            pdf.cell(8, 6, f"{i}.", new_x=XPos.RIGHT, new_y=YPos.LAST)
            pdf.multi_cell(0, 6, safe(instruction), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

    # ---- Notes ----
    section_header(pdf, "Notes for Today")
    if notes:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, safe(notes), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        # blank ruled lines for handwriting
        for _ in range(4):
            pdf.ln(9)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())

    # ---- Footer ----
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(170, 170, 170)
    pdf.cell(0, 5, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 45)
    print("   Daycare Instruction Sheet Generator")
    print("=" * 45)

    config = load_config()
    print(f"\nLoaded config for: {config['baby_name']}")

    today_str = date.today().strftime("%B %d, %Y")
    sheet_date = prompt("\nDate for the sheet", today_str)

    naps = collect_naps()
    feedings = collect_feedings()

    print("\n--- NOTES ---")
    notes = input("Any notes for today (press Enter to leave blank): ").strip()

    pdf = generate_pdf(config, sheet_date, naps, feedings, notes)

    safe_date = datetime.now().strftime("%Y-%m-%d")
    out_path = os.path.join(os.path.dirname(__file__), f"daycare_{safe_date}.pdf")
    pdf.output(out_path)

    print(f"\nDone! Saved to: {out_path}")


if __name__ == "__main__":
    main()
