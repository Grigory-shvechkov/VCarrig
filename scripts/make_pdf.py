"""Build the materials PDF (Rev C): 20x40 rail, double-plate carriage, GT2 omega drive."""
import math
from collections import OrderedDict

from drawing import *          # helpers, part figures, mm, FIG, plt, patches, np
from drawing import Polygon, MCircle, MRect

PDF = ROOT / "VSlot_Carriage_Materials.pdf"
REV = "Rev C"
DATE = "28 Oct 2026"

G, T = mm.GAP, mm.PLATE_T
AY, BY, BH, TBY = mm.AXLE_Y, mm.BAR_Y, mm.BAR_H, mm.TOP_BAR_Y
PY0, PY1 = mm.PLATE_Y0, mm.PLATE_Y1
WHEEL = "#f3e7c9"
STEEL = "#aab2bb"
DARK = "#4a5058"
PLATE = "#cfd8e3"


def rect(ax, x0, x1, y0, y1, fc, z=4, lw=0.6, **kw):
    ax.add_patch(MRect((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=INK, lw=lw, zorder=z, **kw))


def ring_section(ax, x0, x1, r_in, r_out, yc, fc, z=4):
    rect(ax, x0, x1, yc + r_in, yc + r_out, fc, z)
    rect(ax, x0, x1, yc - r_out, yc - r_in, fc, z)


def axle(ax, yc):
    rect(ax, -G / 2 - T, G / 2 + T + 5, yc - 2.5, yc + 2.5, "#9aa3ad", z=3, lw=0.4)   # M5x40 shank
    rect(ax, -G / 2 - T - 5, -G / 2 - T, yc - 4.25, yc + 4.25, DARK, z=5)            # head
    rect(ax, G / 2 + T, G / 2 + T + 5, yc - 4.0, yc + 4.0, DARK, z=5)                # nyloc
    centerline(ax, (-G / 2 - T - 8, yc), (G / 2 + T + 8, yc))


def wheel_stack_section(ax, yc, eccentric):
    sec = wheel_section_pts()
    for s in (1, -1):
        ax.add_patch(Polygon(np.column_stack([sec[:, 0], yc + s * sec[:, 1]]), closed=True,
                             fc=WHEEL, ec=INK, lw=0.7, zorder=4))
    for x0 in (-5.5, 0.5):
        ring_section(ax, x0, x0 + 5, 2.5, 8, yc, STEEL)
    ring_section(ax, -0.5, 0.5, 2.5, 5, yc, FILL)
    ring_section(ax, -G / 2, -5.5, 2.5, 5.77 if eccentric else 5, yc, "#e9d7f0" if eccentric else FILL)
    ring_section(ax, 5.5, G / 2, 2.5, 5, yc, FILL)
    axle(ax, yc)


def idler_stack_section(ax, yc):
    ring_section(ax, -G / 2, -5.5, 2.5, 5, yc, FILL)
    ring_section(ax, -5.5, -4.5, 2.5, 5, yc, FILL)
    ring_section(ax, -4.5, 5.5, 2.5, 8, yc, STEEL)
    for x0 in (-4.5, 4.5):
        ring_section(ax, x0, x0 + 1, 8, 9, yc, STEEL)
    ring_section(ax, 5.5, G / 2, 2.5, 5, yc, FILL)
    axle(ax, yc)


def fig_section():
    fig, ax = plt.subplots(figsize=(7.4, 8.6))
    draw_sketch(ax, mm.vslot_profile(20, 40))
    rect(ax, -G / 2 - T, -G / 2, PY0, PY1, PLATE, z=2, lw=0.9, hatch="\\\\\\")
    rect(ax, G / 2, G / 2 + T, PY0, PY1, PLATE, z=2, lw=0.9, hatch="///")
    for y in (BY, -BY, TBY):
        rect(ax, -G / 2, G / 2, y - BH / 2, y + BH / 2, "#b4c2d4", z=2, lw=0.8)
    wheel_stack_section(ax, AY, False)
    wheel_stack_section(ax, -AY, True)
    idler_stack_section(ax, mm.IDLER_Y)
    # motor, shaft, pulley
    py = mm.PULLEY_Y
    rect(ax, -G / 2 - T - mm.NEMA_LEN, -G / 2 - T, py - mm.NEMA / 2, py + mm.NEMA / 2, "#3a3f46", z=4)
    rect(ax, -G / 2 - T, -G / 2 - T + 2, py - 11, py + 11, "#3a3f46", z=4)
    rect(ax, -G / 2 - T, -G / 2 + 18, py - 2.5, py + 2.5, "#9aa3ad", z=3)
    px = -G / 2 + 0.5
    for a, b, r in ((0, 7, 8), (7, 8, 8), (8, 15, 6.1), (15, 16, 8)):
        ring_section(ax, px + a, px + b, 2.5, r, py, "#d8b25a")
    # belt (straight run in this section plane)
    rect(ax, mm.BELT_X - 3, mm.BELT_X + 3, mm.BELT_Y - 0.7, mm.BELT_Y + 0.7, "#111111", z=6)

    xr = G / 2 + T + 12
    dim(ax, (xr, -AY), (xr, AY), -14, "59.70", rot=90)
    dim(ax, (xr, 20), (xr, AY), -5, "9.85", rot=90, fs=7)
    dim(ax, (xr, 0), (xr, mm.BELT_Y), -22, "59.3 belt line", rot=90, fs=7)
    dim(ax, (xr, 0), (xr, mm.IDLER_Y), -30, "68.0 idlers", rot=90, fs=7)
    dim(ax, (xr, 0), (xr, py), -38, "84.0 motor shaft", rot=90, fs=7)
    dim(ax, (-G / 2 - T - mm.NEMA_LEN - 6, PY0), (-G / 2 - T - mm.NEMA_LEN - 6, PY1), 0.001, "", ext=False)
    ax.text(-G / 2 - T - mm.NEMA_LEN - 9, (PY0 + PY1) / 2, f"{PY1 - PY0:.1f} plate height", rotation=90,
            color=DIM, fontsize=7.5, ha="center", va="center")
    dim(ax, (-G / 2, PY0 - 4), (G / 2, PY0 - 4), -3, "23.0 between plates", fs=7)
    dim(ax, (-G / 2 - T, PY1 + 3), (-G / 2, PY1 + 3), 3, "6", fs=7)
    dim(ax, (G / 2, PY1 + 3), (G / 2 + T, PY1 + 3), 3, "6", fs=7)
    dim(ax, (-G / 2 - T - mm.NEMA_LEN, PY0 - 13), (G / 2 + T + 5, PY0 - 13), -3,
        f"{G / 2 + T + 5 + G / 2 + T + mm.NEMA_LEN:.1f} overall depth (motor to nuts)", fs=7)
    dim(ax, (-G / 2, 0), (-10, 0), 0.001, "", ext=False)
    ax.text(-10.75, -3, "1.5", color=DIM, fontsize=6.5, ha="center")
    leader(ax, (-G / 2 - T / 2, 10), (-75, 14), "Plate A — back plate\n(motor, eccentric holes)", ha="right")
    leader(ax, (G / 2 + T / 2, 10), (40, 14), "Plate B — arm plate")
    leader(ax, (0, BY), (40, BY + 10), "tie bars 23 x 12 x 110\n(close the box)")
    leader(ax, (-8, -AY + 4), (-75, -AY + 12), "eccentric spacer\n(preload bottom wheels)", ha="right")
    leader(ax, (-3, AY + 5), (-75, AY + 18), "fixed wheel stack:\n6 spacer · 625 bearing x2\n+ 1 shim · 6 spacer", ha="right")
    leader(ax, (0, mm.IDLER_Y + 6), (40, mm.IDLER_Y + 4), "smooth idler (2x F625ZZ)")
    leader(ax, (1, py + 6), (40, py + 22), "GT2 20T pulley")
    leader(ax, (-50, py), (-75, py + 30), "NEMA17 (42 x 40)", ha="right")
    leader(ax, (3.4, mm.BELT_Y), (40, mm.BELT_Y - 8), "GT2 6 mm belt")
    leader(ax, (-25, -AY), (-75, -AY - 20), "M5 x 40 axle, both\nends supported", ha="right")
    ax.set_xlim(-112, 80); ax.set_ylim(PY0 - 24, PY1 + 12)
    finish(ax, "section", "Carriage cross-section, looking along the rail (wheel, idler and motor axes drawn in one view)")


def fig_layout():
    S = 4.0      # vertical exaggeration
    fig, ax = plt.subplots(figsize=(7.6, 2.9))
    L = mm.AXIS_LEN
    zmin, zmax = 14 + mm.PLATE_L / 2, L - 14 - mm.PLATE_L / 2
    rect(ax, 0, L, -20 * S, 20 * S, FILL, z=2)
    ax.plot([14, L - 14], [mm.BELT_Y * S] * 2, color="#111", lw=1.2, zorder=3)
    for z0 in (-6, L):
        rect(ax, z0, z0 + 6, -20 * S, (mm.BELT_Y + 7) * S, PLATE, z=3)
    for zc, ls, a in ((zmin, "--", 0.35), (L / 2, "-", 0.95), (zmax, "--", 0.35)):
        ax.add_patch(MRect((zc - mm.PLATE_L / 2, PY0 * S), mm.PLATE_L, (PY1 - PY0) * S, fc=PLATE if ls == "-" else "none",
                           ec="#1f3b63", lw=0.9, ls=ls, alpha=a if ls == "-" else 1, zorder=4))
        centerline(ax, (zc, PY0 * S - 30), (zc, PY1 * S + 30))
    dim(ax, (0, -20 * S), (L, -20 * S), -170, "3300 rail (20x40 V-slot)")
    dim(ax, (zmin, PY1 * S), (zmax, PY1 * S), 120, f"{zmax - zmin:.0f} usable travel (needed 3124 = 10 ft 3 in)")
    ax.text(L / 2, -20 * S - 330, "vertical scale x4  ·  carriage shown at both ends of travel and at mid-travel",
            ha="center", fontsize=7, color="#666")
    ax.text(30, (mm.BELT_Y + 18) * S, "belt clamp", fontsize=7, color=INK)
    ax.text(L - 30, (mm.BELT_Y + 18) * S, "belt clamp", fontsize=7, color=INK, ha="right")
    ax.set_xlim(-60, L + 60); ax.set_ylim(-20 * S - 380, PY1 * S + 320)
    ax.axis("off")
    ax.set_title("Full axis — side elevation", fontsize=9.5, loc="left", fontweight="bold")
    fig.savefig(FIG / "layout.png", dpi=230, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def hole_purpose(y, d):
    if d == mm.NEMA_PILOT: return "NEMA17 pilot"
    if d == 3.4: return "NEMA17 mount, M3 clearance"
    if abs(abs(y) - AY) < 0.01:
        if d == mm.HOLE_ECC: return "Eccentric spacer rim"
        if d == mm.HOLE_FAR_ECC: return "Eccentric axle clearance (+ M5 washer)"
        return "Wheel axle, M5 clearance"
    if abs(y - mm.IDLER_Y) < 0.01: return "Idler axle, M5 clearance"
    return "Tie-bar screw, M5 clearance"


def hole_groups(holes):
    g = OrderedDict()
    for x, y, d in sorted(holes, key=lambda h: (-h[1], h[0])):
        g.setdefault((d, hole_purpose(y, d)), []).append((x, y))
    return [(chr(65 + i), d, p, pts) for i, ((d, p), pts) in enumerate(g.items())]


def fig_plates():
    fig, axs = plt.subplots(1, 2, figsize=(8.0, 6.8))
    tables = {}
    for ax, name, holes in ((axs[0], "Plate A — back (motor side)", mm.plate_a_holes()),
                            (axs[1], "Plate B — front (arm side)", mm.plate_b_holes())):
        ax.add_patch(matplotlib.patches.FancyBboxPatch((-mm.PLATE_L / 2 + 4, PY0 + 4), mm.PLATE_L - 8, PY1 - PY0 - 8,
                                                       boxstyle="round,pad=4", fc=PLATE, ec=INK, lw=0.9))
        groups = hole_groups(holes)
        for letter, d, p, pts in groups:
            for x, y in pts:
                ax.add_patch(MCircle((x, y), d / 2, fc="white", ec=INK, lw=0.7, zorder=3))
                ax.text(x + d / 2 + 0.8, y + d / 2 + 0.5, letter, fontsize=6.5, color=NOTE, zorder=5)
        ax.plot(0, 0, "+", color=NOTE, ms=12, mew=1.0, zorder=6)
        ax.text(1.5, -6, "datum (0,0)\nrail centre", fontsize=6, color=NOTE)
        centerline(ax, (-mm.PLATE_L / 2 - 6, 0), (mm.PLATE_L / 2 + 6, 0))
        dim(ax, (-mm.PLATE_L / 2, PY0), (mm.PLATE_L / 2, PY0), -7, "110.0")
        dim(ax, (mm.PLATE_L / 2, PY0), (mm.PLATE_L / 2, PY1), -7, f"{PY1 - PY0:.1f}", rot=90)
        dim(ax, (-mm.PLATE_L / 2, 0), (-mm.PLATE_L / 2, PY1), 7, f"{PY1:.1f}", rot=90, fs=7)
        dim(ax, (-mm.PLATE_L / 2, PY0), (-mm.PLATE_L / 2, 0), 7, f"{-PY0:.1f}", rot=90, fs=7)
        ax.text(0, PY0 - 22, "6 mm aluminium (6061-T6), corners R4", ha="center", fontsize=7, color="#555")
        ax.set_xlim(-75, 75); ax.set_ylim(PY0 - 28, PY1 + 8)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(name + "\n(viewed from outside)" if "B" in name else name + "\n(viewed from inside)",
                     fontsize=9, loc="left", fontweight="bold")
        tables[name] = groups
    fig.savefig(FIG / "plates.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return tables


def fig_drive():
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    hz = mm.WHEELBASE / 2
    rect(ax, -95, 95, -20, 20, FILL, z=1, lw=0.6)
    ax.text(-92, 0, "20x40 rail", fontsize=7, va="center")
    ax.add_patch(matplotlib.patches.FancyBboxPatch((-mm.PLATE_L / 2 + 4, PY0 + 4), mm.PLATE_L - 8, PY1 - PY0 - 8,
                                                   boxstyle="round,pad=4", fc="none", ec="#7a8ea8", lw=0.8, ls="--"))
    for y in (BY, -BY, TBY):
        rect(ax, -mm.PLATE_L / 2, mm.PLATE_L / 2, y - BH / 2, y + BH / 2, "#dfe6ef", z=2, lw=0.5)
    for z in (-hz, hz):
        for y in (AY, -AY):
            ax.add_patch(MCircle((z, y), mm.W_OD / 2, fc=WHEEL, ec=INK, lw=0.6, zorder=3))
    for s in (-1, 1):
        ax.add_patch(MCircle((s * mm.IDLER_Z, mm.IDLER_Y), mm.IDLER_FLANGE_D / 2, fc="#e8ebee", ec=INK, lw=0.5, zorder=3))
        ax.add_patch(MCircle((s * mm.IDLER_Z, mm.IDLER_Y), mm.IDLER_D / 2, fc=STEEL, ec=INK, lw=0.6, zorder=3))
    ax.add_patch(MRect((-mm.NEMA / 2, mm.PULLEY_Y - mm.NEMA / 2), mm.NEMA, mm.NEMA, fc="none", ec="#555", lw=0.7, ls=":", zorder=2))
    ax.add_patch(MCircle((0, mm.PULLEY_Y), 8, fc="#f1dfaa", ec=INK, lw=0.5, zorder=3))
    ax.add_patch(MCircle((0, mm.PULLEY_Y), mm.PULLEY_PD / 2, fc="#d8b25a", ec=INK, lw=0.6, zorder=3))
    pts = np.array(mm.belt_path(-95, 95, 0))
    ax.plot(pts[:, 0], pts[:, 1], color="#111", lw=2.2, zorder=5, solid_capstyle="butt")
    dim(ax, (-mm.IDLER_Z, mm.IDLER_Y), (mm.IDLER_Z, mm.IDLER_Y), -17, f"{2 * mm.IDLER_Z:.0f} idler centres")
    dim(ax, (-hz, -AY), (hz, -AY), -20, f"{mm.WHEELBASE:.0f} wheelbase")
    leader(ax, (60, mm.BELT_Y - 1.5), (62, 40), f"{mm.BELT_Y - 0.7 - BY - BH / 2:.1f} clearance belt ↔ tie bar", fs=7)
    c1, p = (-mm.IDLER_Z, mm.IDLER_Y), (0, mm.PULLEY_Y)
    a1, b1 = mm._circle_tangent(c1, mm.IDLER_D / 2 + mm.BELT_T / 2, True, p, mm.PULLEY_PD / 2, False)
    ang = math.degrees(math.atan2(b1[1] - p[1], b1[0] - p[0]))   # belt wraps from ang to 180-ang
    leader(ax, (0, mm.PULLEY_Y + 6.4), (25, 128), f"pulley wrap ≈ {2 * ang - 180:.0f}° (≈ {round((2 * ang - 180) / 18)} teeth engaged)")
    leader(ax, (mm.IDLER_Z, mm.IDLER_Y + 8), (50, 95), "smooth idlers on M5 axles\n(through both plates)")
    leader(ax, (-80, mm.BELT_Y), (-90, 82), "belt fixed at both rail ends", ha="left")
    ax.set_xlim(-100, 100); ax.set_ylim(-60, 135)
    finish(ax, "drive", "Omega drive — side view (plate B removed)")
    return 2 * ang - 180


def fig_small_parts():
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw=dict(width_ratios=[1.6, 1]))
    a = axs[0]
    rect(a, -55, 55, -6, 6, "#b4c2d4", z=2, lw=0.8)
    for z in mm.BAR_HOLES_Z:
        a.add_patch(MCircle((z, 0), 2.1, fc="white", ec=INK, lw=0.6, zorder=3))
    dim(a, (-55, -6), (55, -6), -6, "110")
    dim(a, (55, -6), (55, 6), -5, "12", rot=90, fs=7)
    dim(a, (-42, 6), (0, 6), 5, "42", fs=7); dim(a, (0, 6), (42, 6), 5, "42", fs=7)
    a.text(0, -22, "Tie bar, Al, 23 thick (plate gap). M5 tapped 12 deep from both 23-wide faces\n"
           "at 3 positions (top bar: 2 positions, ±42 only). Top and bottom bars: R4 on the 2 outer\n"
           "corners to match the plate outline", ha="center", fontsize=6.8, color="#444")
    a.set_xlim(-65, 65); a.set_ylim(-30, 18); a.set_aspect("equal"); a.axis("off")
    a.set_title("Tie bar (x3)", fontsize=9, loc="left", fontweight="bold")
    b = axs[1]
    y0, y1 = -20, mm.CLAMP_BLOCK_Y1 + mm.BELT_T + mm.CLAMP_PLATE_T
    rect(b, -10, 10, y0, y1, PLATE, z=2)
    for y in (-10, 10):
        b.add_patch(MCircle((0, y), 2.75, fc="white", ec=INK, lw=0.6, zorder=3))
    rect(b, -10, 10, mm.CLAMP_BLOCK_Y1 - 10, mm.CLAMP_BLOCK_Y1, "#b4c2d4", z=3)
    rect(b, -10, 10, mm.CLAMP_BLOCK_Y1, mm.CLAMP_BLOCK_Y1 + mm.BELT_T, "#111111", z=3)
    rect(b, -10, 10, mm.CLAMP_BLOCK_Y1 + mm.BELT_T, y1, "#8fa5c2", z=3)
    dim(b, (-10, y0), (10, y0), -5, "20", fs=7)
    dim(b, (10, y0), (10, y1), -5, f"{y1 - y0:.1f}", rot=90, fs=7)
    leader(b, (0, 10), (18, 20), "2x M5 into rail\nend bores")
    leader(b, (3, mm.BELT_Y), (18, mm.BELT_Y + 6), "belt pinched between block\nand clamp plate (2x M3)")
    b.set_xlim(-18, 45); b.set_ylim(-30, 75); b.set_aspect("equal"); b.axis("off")
    b.set_title("Belt clamp (x2)", fontsize=9, loc="left", fontweight="bold")
    fig.savefig(FIG / "smallparts.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def crop(name):
    from PIL import Image as PImg, ImageChops
    im = PImg.open(FIG / name).convert("RGB")
    bb = ImageChops.difference(im, PImg.new("RGB", im.size, "white")).getbbox()
    im.crop((max(bb[0] - 15, 0), max(bb[1] - 15, 0), min(bb[2] + 15, im.width), min(bb[3] + 15, im.height))).save(FIG / ("c_" + name))


# ---------------------------------------------------------------- PDF
def build_pdf(plate_tables, wrap_deg):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                    Image, PageBreak, KeepTogether)
    from PIL import Image as PImg

    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=19, leading=23, alignment=0, spaceAfter=2)
    H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=4,
                        textColor=colors.HexColor("#1f3b63"))
    B = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9, leading=12.2)
    S = ParagraphStyle("s", parent=B, fontSize=7.8, leading=9.8)
    SM = ParagraphStyle("sm", parent=B, fontSize=8, leading=10, textColor=colors.HexColor("#555555"))
    NAVY, ALT = colors.HexColor("#1f3b63"), colors.HexColor("#eef2f7")

    def img(name, w):
        p = FIG / name
        iw, ih = PImg.open(p).size
        return Image(str(p), width=w, height=w * ih / iw)

    def table(rows, widths, sect_rows=()):
        rows = [list(r) for r in rows]
        for r in sect_rows:   # spanned rows only show cell 0, so move the label there
            rows[r] = [next((c for c in rows[r] if c), "")] + [""] * (len(rows[r]) - 1)
        data =[[Paragraph(f"<font color='white'><b>{c}</b></font>", S) for c in rows[0]]]
        data += [[Paragraph(str(c), S) for c in r] for r in rows[1:]]
        t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1)
        st = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT]),
              ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cf")),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
        for r in sect_rows:
            st += [("BACKGROUND", (0, r), (-1, r), colors.HexColor("#dfe7f1")), ("SPAN", (0, r), (-1, r))]
        t.setStyle(TableStyle(st))
        return t

    belt_len = mm.belt_length()
    travel = mm.AXIS_LEN - 2 * (14 + mm.PLATE_L / 2)
    story = []
    story.append(Paragraph("V-Slot Linear Carriage — Materials &amp; Part Drawings", H1))
    story.append(Paragraph(f"Print Bed Scanner axis · {REV} · {DATE} · all dimensions in mm", SM))
    story.append(Spacer(1, 4))
    story.append(img("c_rc_front.png", 5.6 * inch))
    story.append(Paragraph(
        "A rigid double-plate carriage on a 20x40 V-slot rail. Plate A (back) carries the NEMA17 motor. "
        "Plate B (front) is left clear for the arm. Four Solid V wheels ride the top and bottom grooves. "
        "Every wheel and idler axle is an M5 bolt through <b>both</b> plates, clamped tight, so it is supported at "
        "both ends and never turns. Only the bearing outer races and wheels spin, so the plate holes do not wear. "
        "Three tie bars close the two plates into a box. A GT2 belt is fixed at both rail ends and wraps the "
        "motor pulley between two idlers (omega drive), so the motor rides on the carriage.", B))
    story.append(Spacer(1, 4))
    spec = [["Item", "Value"],
            ["Required travel", "3124 mm (10 ft 3 in)"],
            ["Rail", f"V-slot 20x40 x {mm.AXIS_LEN:.0f} mm → {travel:.0f} mm usable travel"],
            ["Carriage", f"110 long x {PY1 - PY0:.1f} tall x 80 deep (incl. motor), 4 wheels, 70 wheelbase"],
            ["Wheel axles", "59.70 apart (top ↔ bottom), 9.85 from rail faces"],
            ["Drive", f"NEMA17 + GT2 20T pulley, omega wrap ≈ {wrap_deg:.0f}°, 40 mm of travel per motor rev"],
            ["Belt", f"GT2 6 mm, {belt_len:.0f} mm path → buy ≥ 3.5 m (steel-core recommended)"],
            ["Payload", "arm + payload < 2 kg, horizontal axis"]]
    story.append(table(spec, [1.6, 5.7]))
    story.append(PageBreak())

    story.append(Paragraph("Bill of materials (as of now)", H2))
    bom = [["#", "Part", "Size / spec", "Qty", "Model file (models/)"],
           ["", "<b>Rail &amp; drive (fixed)</b>", "", "", ""],
           ["1", "V-slot 20x40 linear rail", f"{mm.AXIS_LEN:.0f} long (one piece preferred)", "1", "VSlot_2040_3300mm.step"],
           ["2", "Belt clamp: bracket + clamp plate, Al (to make)", "20 x 83 x 6, 14 block, 20x14x3 plate", "2", "Belt_End_Bracket.step"],
           ["3", "GT2 belt, 6 mm (steel-core recommended)", f"≥ 3.5 m ({belt_len:.0f} path)", "1", "—"],
           ["4", "M5 x 12 SHCS (clamp → rail end bores, tap M5)", "M5 x 12", "4", "—"],
           ["5", "M3 x 10 SHCS (clamp plate → tapped block)", "M3 x 10", "4", "—"],
           ["", "<b>Carriage structure</b>", "", "", ""],
           ["6", "Plate A — back, 6061 Al (to make)", f"110 x {PY1 - PY0:.1f} x 6", "1", "Plate_A_Back_Motor.step"],
           ["7", "Plate B — front / arm, 6061 Al (to make)", f"110 x {PY1 - PY0:.1f} x 6", "1", "Plate_B_Arm_Side.step"],
           ["8", "Middle tie bar, Al (to make), 3x M5 tapped each end", "23 x 12 x 110", "1", "Tie_Bar_Middle_23x12x110.step"],
           ["8b", "Bottom tie bar, R4 outer corners, 3x M5 each end", "23 x 12 x 110", "1", "Tie_Bar_Bottom_23x12x110.step"],
           ["9", "Top tie bar, R4 outer corners, 2x M5 each end", "23 x 12 x 110", "1", "Tie_Bar_Top_23x12x110.step"],
           ["10", "M5 x 16 SHCS (plates → tie bars)", "M5 x 16", "16", "—"],
           ["", "<b>Wheels &amp; idlers</b>", "", "", ""],
           ["11", "Solid V wheel (Delrin)", "Ø23.90 x 10.23", "4", "Solid_V_Wheel.step"],
           ["12", "625-2RS bearing", "5 x 16 x 5", "8", "Bearing_625_2RS_5x16x5.step"],
           ["13", "Precision shim", "10 x 5 x 1", "6", "Precision_Shim_10x5x1.step"],
           ["14", "Aluminium spacer", "Ø10 x 6, bore 5.1", "10", "Aluminum_Spacer_6mm.step"],
           ["15", "Eccentric spacer", "6 mm, 10 A/F", "2", "Eccentric_Spacer_6mm.step"],
           ["16", "F625ZZ flanged bearing (idlers, 2 per idler)", "5 x 16 x 5, 18 flange", "4", "Smooth_Idler_F625ZZx2.step"],
           ["17", "M5 x 40 SHCS (fixed wheel &amp; idler axles)", "M5 x 40", "4", "—"],
           ["17b", "M5 x 45 SHCS (eccentric wheel axles, + washer)", "M5 x 45", "2", "—"],
           ["18", "M5 nylon lock nut", "M5", "6", "—"],
           ["19", "M5 washer (plate B eccentric holes)", "M5", "2", "—"],
           ["", "<b>Motor</b>", "", "", ""],
           ["20", "NEMA17 stepper, ≥ 0.4 N·m", "42.3 sq x 40, 5 mm shaft", "1", "NEMA17_40mm.step"],
           ["21", "GT2 20T pulley, 5 mm bore, 6 mm belt", "Ø16 flange x 16", "1", "GT2_20T_Pulley_5mm.step"],
           ["22", "M3 x 10 SHCS (motor)", "M3 x 10", "4", "—"],
           ["23", "Driver / controller, 2 limit switches, drag chain", "TBD", "—", "—"]]
    story.append(table(bom, [0.38, 2.82, 1.75, 0.4, 1.95], sect_rows=(1, 7, 14, 25)))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Assembly sub-sets:</b> wheel stack (fixed) = spacer · 625 · shim · 625 · spacer on an M5 x 40. "
        "Eccentric stack = eccentric spacer (rim in plate A) · 625 · shim · 625 · spacer. "
        "Idler stack = spacer · shim · 2x F625ZZ · spacer. Each stack is exactly 23 mm, the gap between the plates.", S))
    story.append(PageBreak())

    story.append(Paragraph("Carriage materials", H2))
    story.append(Paragraph(
        "Everything that rides on the rail: one complete carriage, including the motor. The rail, belt and belt "
        "clamps are not included (see the full bill of materials).", B))
    story.append(Spacer(1, 4))
    car_bom = [["#", "Part", "Size / spec", "Qty", "Used in"],
               ["", "<b>Machined parts (6061 aluminium)</b>", "", "", ""],
               ["C1", "Plate A — back plate (motor side)", f"110 x {PY1 - PY0:.1f} x 6", "1", "frame"],
               ["C2", "Plate B — front plate (arm side)", f"110 x {PY1 - PY0:.1f} x 6", "1", "frame"],
               ["C3", "Middle + bottom tie bar, 3x M5 tapped each end", "23 x 12 x 110", "2", "frame (bottom bar: R4 corners)"],
               ["C4", "Top tie bar, 2x M5 tapped each end, R4 corners", "23 x 12 x 110", "1", "frame"],
               ["", "<b>Rolling parts</b>", "", "", ""],
               ["C5", "Solid V wheel (Delrin)", "Ø23.90 x 10.23", "4", "1 per wheel stack"],
               ["C6", "625-2RS ball bearing", "5 x 16 x 5", "8", "2 per wheel, included with wheel kit"],
               ["C7", "F625ZZ flanged ball bearing", "5 x 16 x 5, 18 flange", "4", "2 per idler"],
               ["", "<b>Spacers &amp; shims</b>", "", "", ""],
               ["C8", "Aluminium spacer", "Ø10 x 6, bore 5.1", "10", "fixed stack 2 · eccentric 1 · idler 2"],
               ["C9", "Eccentric spacer", "6 mm, 10 A/F", "2", "bottom wheels"],
               ["C10", "Precision shim", "10 x 5 x 1", "6", "1 per wheel (in kit), 1 per idler"],
               ["", "<b>Fasteners</b>", "", "", ""],
               ["C11", "M5 x 40 socket head cap screw", "M5 x 40", "4", "top wheel + idler axles"],
               ["C12", "M5 x 45 socket head cap screw", "M5 x 45", "2", "eccentric wheel axles"],
               ["C13", "M5 nylon lock nut", "M5", "6", "all axles"],
               ["C14", "M5 washer", "Ø10 x 1", "2", "eccentric axles at plate B"],
               ["C15", "M5 x 16 socket head cap screw", "M5 x 16", "16", "plates → tie bars"],
               ["C16", "M3 x 10 socket head cap screw", "M3 x 10", "4", "motor → plate A"],
               ["", "<b>Drive (on the carriage)</b>", "", "", ""],
               ["C17", "NEMA17 stepper motor, ≥ 0.4 N·m", "42.3 sq x 40, 5 mm shaft", "1", "plate A"],
               ["C18", "GT2 20T pulley, 5 mm bore", "6 mm belt, Ø16 flange", "1", "motor shaft"]]
    story.append(table(car_bom, [0.4, 2.75, 1.7, 0.4, 2.05], sect_rows=(1, 6, 10, 14, 21)))
    story.append(Spacer(1, 6))
    sub = [["Sub-assembly", "Qty", "Stack (plate A → plate B), 23 mm total", "Axle"],
           ["Fixed wheel (top)", "2", "spacer 6 · 625 · shim 1 · 625 (inside V wheel) · spacer 6", "M5 x 40 + nyloc"],
           ["Eccentric wheel (bottom)", "2", "eccentric 6 · 625 · shim 1 · 625 (inside V wheel) · spacer 6",
            "M5 x 45 + washer + nyloc"],
           ["Idler", "2", "spacer 6 · shim 1 · F625ZZ · F625ZZ · spacer 6", "M5 x 40 + nyloc"],
           ["Frame", "1", "plate A + plate B + 3 tie bars (16x M5 x 16)", "—"],
           ["Motor", "1", "NEMA17 on plate A (4x M3 x 10), GT2 pulley inside the box", "—"]]
    story.append(table(sub, [1.55, 0.4, 3.85, 1.5]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Tighten every axle nut firmly. The bolts, spacers and bearing inner races are clamped solid between the "
        "plates, and only the wheels and bearing outer races turn, so no bearings are needed in the plate holes.", S))
    story.append(PageBreak())

    # ---------------------------------------------------------------- shopping list
    from urllib.parse import quote_plus
    LINK = ParagraphStyle("lnk", parent=S, textColor=colors.HexColor("#1f5fbf"))

    def amz(q):
        return Paragraph(f'<a href="https://www.amazon.com/s?k={quote_plus(q)}" color="#1f5fbf"><u>{q}</u></a>', LINK)

    story.append(Paragraph("Shopping list — Amazon", H2))
    story.append(Paragraph(
        "Each search phrase is a clickable Amazon search link, worded the way sellers name these parts. Quantities "
        "cover one carriage plus the rail and drive. Screws and nuts come in packs, so buy the pack size shown. "
        "Check the spec notes on each listing before ordering.", B))
    story.append(Spacer(1, 4))
    shop = [
        ("<b>Rail &amp; motion</b>",),
        ("1", "2040 V-slot aluminum extrusion 500mm",
         "1 (prototype)", "1", "20x40 mm V-slot (not T-slot). Amazon tops out around 1.5 m; get the 3.3 m length "
         "from an extrusion supplier (OpenBuilds, Misumi, 8020) later."),
        ("2", "solid V wheel kit 625 bearing delrin V-slot", "4", "pack of 10",
         "Delrin/POM 'solid' V wheel, sold with 2x 625-2RS bearings + 1 shim per wheel. Check that the listing "
         "says bearings are included."),
        ("3", "F625ZZ flanged bearing 5x16x5mm", "4", "pack of 10", "Flanged, 18 mm flange. For the 2 belt idlers."),
        ("4", "aluminum spacer 6mm V-slot M5", "10", "pack of 10–20", "10 mm OD, 6 mm long, ~5.1 mm bore."),
        ("5", "precision shim 10x5x1mm", "2", "pack of 20+", "For the 2 idlers (the wheel shims come in the wheel kits)."),
        ("6", "eccentric spacer 6mm V-slot", "2", "pack of 5–10", "6 mm cam height, 7.1 mm rim. For the bottom wheels."),
        ("<b>Drive</b>",),
        ("7", "NEMA 17 stepper motor 40mm 0.45Nm", "1", "1", "42x42 mm body, 5 mm D-shaft, ≥ 0.4 N·m."),
        ("8", "GT2 20 tooth pulley 5mm bore 6mm belt", "1", "pack of 2–5", "5 mm bore, for 6 mm wide belt."),
        ("9", "GT2 timing belt 6mm steel core 5 meters", "3.5 m", "5 m roll",
         "Steel or fiberglass reinforced. 5 m covers the 3.3 m axis; 1 m is enough for the prototype."),
        ("10", "TMC2209 stepper driver", "1", "1–4", "Plus a controller board (TBD), 12–24 V supply and 2 limit switches."),
        ("<b>Fasteners (metric, black-oxide 12.9 or stainless)</b>",),
        ("11", "M5 x 40mm socket head cap screw", "4", "pack of 10–25", "Top wheel + idler axles (6 mm plates)."),
        ("12", "M5 x 45mm socket head cap screw", "2", "pack of 10", "Eccentric wheel axles."),
        ("13", "M5 x 16mm socket head cap screw", "16", "pack of 25–50", "Plates to tie bars."),
        ("14", "M5 x 12mm socket head cap screw", "4", "pack of 25", "Belt clamps into the rail ends."),
        ("15", "M3 x 10mm socket head cap screw", "8", "pack of 50", "4 motor + 4 belt clamp plate."),
        ("16", "M5 nylon insert lock nut", "6", "pack of 50", "Axle nuts."),
        ("17", "M5 flat washer 10mm OD", "2", "pack of 50+", "Under the eccentric axle nuts at plate B."),
        ("—", "M5 socket head cap screw assortment kit", "—", "1 kit", "Alternative to items 11–17. Check that it includes 40/45 mm lengths."),
        ("<b>Materials &amp; tools</b>",),
        ("18", "6061 aluminum plate 1/4 inch 6 x 12", "2 plates", "1 sheet",
         "For the final plates. US stock is 1/4\" (6.35 mm): then use M5 x 45 on all axles."),
        ("19", "6061 aluminum flat bar 1 inch x 1/2 inch 12 inch", "3 bars", "1 bar",
         "Tie bars. Face down to exactly 23.0 mm (see machining notes)."),
        ("20", "M5 tap and 4.2mm drill bit set", "1", "1", "Tie bars and rail end bores. An M3 tap + 2.5 mm drill is needed for the belt clamp."),
        ("21", "PLA filament 1kg", "1", "1 kg", "Prototype plates + tie bars use about 350 g."),
    ]
    rows = [["#", "Amazon search (click)", "Need", "Buy", "Check on the listing"]]
    sect = []
    for r in shop:
        if len(r) == 1:
            sect.append(len(rows))
            rows.append([r[0], "", "", "", ""])
        else:
            rows.append(list(r))
    data = [[Paragraph(f"<font color='white'><b>{c}</b></font>", S) for c in rows[0]]]
    for i, r in enumerate(rows[1:], 1):
        if i in sect:
            data.append([Paragraph(r[0], S), "", "", "", ""])
        else:
            data.append([Paragraph(r[0], S), amz(r[1]), Paragraph(r[2], S), Paragraph(r[3], S), Paragraph(r[4], S)])
    t = Table(data, colWidths=[0.3 * inch, 2.35 * inch, 0.75 * inch, 0.8 * inch, 3.1 * inch], repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT]),
          ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cf")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    for r in sect:
        st += [("BACKGROUND", (0, r), (-1, r), colors.HexColor("#dfe7f1")), ("SPAN", (0, r), (-1, r))]
    t.setStyle(TableStyle(st))
    story.append(t)
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Tip: \"OpenBuilds\"-style kits on Amazon (V wheels, spacers, eccentrics) are interchangeable with the "
        "OpenBuilds parts these drawings are based on. Machined parts (plates, tie bars, belt clamps) are made, "
        "not bought.", S))
    story.append(PageBreak())

    story.append(Paragraph("1 · Carriage section", H2))
    story.append(img("section.png", 6.4 * inch))
    story.append(PageBreak())
    story.append(Paragraph("2 · Axis layout", H2))
    story.append(img("layout.png", 7.3 * inch))
    story.append(Paragraph(
        f"The rail is {mm.AXIS_LEN:.0f} mm long. Carriage travel is {travel:.0f} mm between the belt clamps "
        f"(3124 mm needed). Rail mounting is not designed yet: supported only at its ends, a 20x40 sags about 9 mm "
        "at mid-span under a 3 kg carriage. Supported every 400 mm, it sags about 0.01 mm. See open items on the last page.", B))
    story.append(Spacer(1, 6))
    story.append(KeepTogether([Paragraph("3 · Omega belt drive", H2), img("drive.png", 4.6 * inch)]))
    story.append(PageBreak())

    story.append(Paragraph("4 · Plates — hole layout", H2))
    story.append(img("plates.png", 7.2 * inch))
    rows = [["Plate", "Hole", "Ø", "Purpose", "Positions (x along rail, y from rail centre)"]]
    for pname, groups in plate_tables.items():
        for code, d, p, pts in groups:
            pos = "  ".join(f"({x:+.1f}, {y:+.2f})" for x, y in pts)
            rows.append(["A" if "A" in pname.split("—")[0] else "B", code, f"{d:g}", p, pos])
    story.append(table(rows, [0.45, 0.45, 0.45, 2.2, 3.75]))
    story.append(PageBreak())

    story.append(Paragraph("5 · V-slot 20x40 rail", H2))
    t = Table([[img("p2040.png", 2.2 * inch), img("p2020d.png", 4.8 * inch)]], colWidths=[2.45 * inch, 4.9 * inch])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(t)
    story.append(Paragraph(
        "Groove detail A is the same on every face. The wheels ride the two 45° flanks. Per metre the profile "
        "weighs 0.80 kg, with a cross-section area of 298 mm². Second moment of area: I = 4.75 cm<super>4</super> for vertical "
        "loads, 1.21 cm<super>4</super> for sideways loads (computed from the model).", B))
    story.append(Paragraph("6 · Solid V wheel", H2))
    story.append(img("wheel.png", 6.6 * inch))
    story.append(PageBreak())
    story.append(Paragraph("7 · Bearing, shim and spacers", H2))
    story.append(img("hardware.png", 7.3 * inch))
    story.append(Paragraph("8 · Tie bar and belt clamp", H2))
    story.append(img("smallparts.png", 7.0 * inch))
    story.append(Paragraph("9 · Inside the carriage", H2))
    story.append(img("c_rc_open.png", 4.6 * inch))
    story.append(PageBreak())

    story.append(Paragraph("10 · Fusion 360 model", H2))
    story.append(Paragraph(
        "<b>Print_Bed_Scanner</b> (set to an Assembly design) contains:<br/>"
        "• <b>Rail Assembly</b> (grounded): 3300 mm rail, both belt clamps, and the belt shown at mid-travel.<br/>"
        "• <b>Carriage</b>: both plates, 3 tie bars, 4 wheel stacks, 2 idler stacks, the motor, the pulley and all "
        "screws. Repeated parts share one component.<br/>"
        f"• Joint <b>Carriage travel</b>: an as-built slider along the rail with limits ±{travel / 2:.0f} mm from "
        "mid-rail. Drag the carriage, or right-click the joint and use Drive Joints. The belt is a fixed reference "
        "and does not follow the carriage.<br/><br/>"
        "<b>Next in Fusion:</b> add revolute joints for the wheels, linked to the slider with Motion Link, then run a "
        "Motion Study. A Static Stress study of the carriage (fix the wheel axles, load plate B with the arm "
        "moment) will show plate deflection.<br/>"
        "All STEP files are regenerated by scripts/make_models.py and scripts/fusion_export.py, and Fusion is built "
        "by scripts/fusion_build_lib.py.", B))
    story.append(Paragraph("Open items", H2))
    story.append(Paragraph(
        "• <b>Rail mounting (deferred):</b> the closed box covers all four rail faces, so the rail can only be held "
        "at its ends. To support the rail along its length, split plate A into upper and lower strips and stand the "
        "rail off a backbone on 14 mm blocks every 400 mm. That variant is already in the model script "
        "(split_back=True).<br/>"
        "• <b>One-piece 3.3 m rail:</b> OpenBuilds sells up to 1.5 m. Find a supplier that cuts 20x40 V-slot to "
        "3.3 m, or splice two lengths over a support with dowels in the centre bores so the wheels cross the joint "
        "smoothly.<br/>"
        "• <b>Belt tensioner:</b> one clamp needs an adjustment slot or a tensioner. It is not modelled yet.<br/>"
        "• <b>Arm mounting pattern on plate B:</b> TBD. Keep screws from protruding more than 1 mm into the 1.5 mm "
        "rail clearance.<br/>"
        "• <b>Wheel flank geometry:</b> derived from the groove fit. Check it against the OpenBuilds STEP library "
        "before ordering plates.", B))
    story.append(Paragraph("Sources", H2))
    story.append(Paragraph(
        "OpenBuilds V-slot and Solid V wheel specs (openbuilds.com, STEP Parts Library 1.5). The V-slot profile "
        "geometry comes from the open-source bd_warehouse OpenBuilds library (Apache-2.0).", S))

    def on_page(c, d):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#888888"))
        c.drawString(0.6 * inch, 0.45 * inch, f"V-Slot Linear Carriage · materials {REV}")
        c.drawRightString(7.9 * inch, 0.45 * inch, f"page {d.page}")
        c.restoreState()

    doc = SimpleDocTemplate(str(PDF), pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.7 * inch,
                            title="V-Slot Linear Carriage — Materials")
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("wrote", PDF)


if __name__ == "__main__":
    for f in (fig_2020, fig_2040, fig_wheel, fig_hardware, fig_section, fig_layout, fig_small_parts):
        f()
    tables = fig_plates()
    wrap = fig_drive()
    crop("rc_front.png"); crop("rc_open.png")
    build_pdf(tables, wrap)
