"""Shared drawing helpers and part drawings (rail profile, wheel, hardware)."""
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle as MCircle, Rectangle as MRect, Arc


sys.path.insert(0, str(Path(__file__).parent))
import make_models as mm
from build123d import Box, Pos, Rot, Compound

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "build" / "figs"
FIG.mkdir(parents=True, exist_ok=True)


INK = "#1b1b1b"
FILL = "#d9dde3"
FILL2 = "#b9c3cf"
DIM = "#1f5fbf"
NOTE = "#b5531a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})


# ---------------------------------------------------------------- helpers
def wire_pts(wire, n=1600):
    return np.array([[(wire @ t).X, (wire @ t).Y] for t in np.linspace(0, 1, n)])


def draw_sketch(ax, sketch, fill=FILL, offset=(0, 0)):
    for face in sketch.faces():
        outer = wire_pts(face.outer_wire()) + offset
        ax.add_patch(Polygon(outer, closed=True, fc=fill, ec=INK, lw=0.9, zorder=2))
        for w in face.inner_wires():
            ax.add_patch(Polygon(wire_pts(w, 400) + offset, closed=True, fc="white",
                                 ec=INK, lw=0.9, zorder=3))


def dim(ax, p1, p2, off, text, fs=7.5, tpad=0.9, color=DIM, ext=True, rot=None):
    """Linear dimension between p1 and p2, drawn offset `off` along the left normal."""
    p1, p2 = np.array(p1, float), np.array(p2, float)
    d = p2 - p1
    L = np.linalg.norm(d)
    u = d / L
    n = np.array([-u[1], u[0]])
    a, b = p1 + n * off, p2 + n * off
    if ext and abs(off) > 1e-6:
        s = np.sign(off)
        for p, q in ((p1, a), (p2, b)):
            ax.plot(*zip(p + n * s * 0.4, q + n * s * 0.6), color=color, lw=0.5, zorder=5)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.7,
                                                    shrinkA=0, shrinkB=0, mutation_scale=7), zorder=6)
    m = (a + b) / 2 + n * np.sign(off if off else 1) * tpad
    ang = math.degrees(math.atan2(u[1], u[0])) if rot is None else rot
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    ax.text(*m, text, color=color, fontsize=fs, ha="center", va="center", rotation=ang,
            zorder=7, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def leader(ax, p, t, text, color=DIM, fs=7.5, ha="left"):
    ax.annotate(text, xy=p, xytext=t, color=color, fontsize=fs, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0.6, mutation_scale=7,
                                shrinkA=1, shrinkB=0), zorder=8,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def centerline(ax, p1, p2):
    ax.plot(*zip(p1, p2), color="#888", lw=0.5, ls=(0, (8, 2, 1.5, 2)), zorder=1)


def finish(ax, name, title=None):
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9.5, color=INK, loc="left", fontweight="bold")
    fig = ax.figure
    fig.savefig(FIG / f"{name}.png", dpi=260, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- 2020 profile
def fig_2020():
    prof = mm.vslot_profile(20, 20)
    fig, ax = plt.subplots(figsize=(4.0, 4.0))
    draw_sketch(ax, prof)
    centerline(ax, (-13, 0), (13, 0)); centerline(ax, (0, -13), (0, 13))
    dim(ax, (-10, -10), (10, -10), -3.2, "20.00")
    dim(ax, (-10, -10), (-10, 10), 3.2, "20.00")
    dim(ax, (-3.9, -3.9), (3.9, -3.9), -0.0001, "", ext=False)
    ax.text(0, -5.0, "7.80 core", color=DIM, fontsize=6.5, ha="center", zorder=7,
            bbox=dict(fc="white", ec="none", pad=0.3))
    leader(ax, (-1.48, 1.48), (-12, 15.5), "Ø4.20 centre bore\n(tap M5 x 0.8)", ha="right")
    leader(ax, (-9.56, -9.56), (-12, -17), "R1.50 corners (x4)", ha="right")
    ax.add_patch(MCircle((0, 7.0), 5.6, fc="none", ec=NOTE, lw=0.9, ls="--", zorder=9))
    ax.text(6.0, 12.4, "A", color=NOTE, fontsize=11, fontweight="bold")
    ax.set_xlim(-22, 14); ax.set_ylim(-20, 19)
    finish(ax, "p2020", "Cross-section (all 4 faces identical)")

    fig, dx = plt.subplots(figsize=(5.0, 3.6))
    draw_sketch(dx, prof)
    centerline(dx, (0, 2.8), (0, 12.8))
    dim(dx, (-4.58, 10), (4.58, 10), 1.9, "9.16 opening")
    dim(dx, (-3.125, 8.37), (3.125, 8.37), -0.0001, "", ext=False)
    dx.text(0, 9.15, "6.25 neck", color=DIM, fontsize=7, ha="center", va="center", zorder=7,
            bbox=dict(fc="white", ec="none", pad=0.4))
    dim(dx, (-5.5, 7.4), (5.5, 7.4), -0.0001, "", ext=False)
    dx.text(0, 5.4, "11.00 T-slot cavity", color=DIM, fontsize=7, ha="center", va="center", zorder=7,
            bbox=dict(fc="white", ec="none", pad=0.4))
    dim(dx, (4.58, 10), (4.58, 8.545), 6.6, "1.46 V depth", fs=7, tpad=1.0)
    dim(dx, (-3.125, 10), (-3.125, 8.2), -8.6, "1.80 lip", fs=7, tpad=1.0)
    dim(dx, (-5.5, 10), (-5.5, 3.9), -10.0, "6.10 slot depth", fs=7, tpad=1.0)
    leader(dx, (3.85, 9.27), (6.0, 13.6), "45° flanks (90° incl.) = wheel contact faces", color=NOTE)
    dx.set_xlim(-17.5, 14); dx.set_ylim(2.6, 14.4)
    finish(dx, "p2020d", "Detail A — V-groove (~10:1)")


def fig_2040():
    fig, ax = plt.subplots(figsize=(4.4, 6.0))
    draw_sketch(ax, mm.vslot_profile(20, 40))
    centerline(ax, (-13, 10), (13, 10)); centerline(ax, (-13, -10), (13, -10)); centerline(ax, (0, -23), (0, 23))
    dim(ax, (-10, -20), (10, -20), -3.2, "20.00")
    dim(ax, (-10, -20), (-10, 20), 3.6, "40.00")
    dim(ax, (10, -10), (10, 10), -4.0, "20.00 pitch")
    leader(ax, (1.48, 11.48), (14, 25), "Ø4.20 bores (x2)")
    leader(ax, (0, 0), (14, -25), "Centre cavity\n16.4 x 12.2")
    ax.set_xlim(-18, 24); ax.set_ylim(-29, 29)
    finish(ax, "p2040", "V-Slot 20x40 rail (selected)")


# ---------------------------------------------------------------- wheel
def wheel_section_pts():
    ro, ri, hw = mm.W_OD / 2, mm.W_ID / 2, mm.W_WIDTH / 2
    rs, ht, rl, hl = mm.W_SHOULDER_D / 2, mm.W_TIP / 2, mm.W_LIP_D / 2, mm.W_LIP_W / 2
    # (z, r) for the upper half
    return np.array([(-hw, ri), (-hw, rs), (-ht, ro), (ht, ro), (hw, rs), (hw, ri),
                     (hl, ri), (hl, rl), (-hl, rl), (-hl, ri)])


def fig_wheel():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 4.4), gridspec_kw=dict(width_ratios=[1.15, 1]))
    sec = wheel_section_pts()
    for s in (1, -1):
        a1.add_patch(Polygon(sec * [1, s], closed=True, fc=FILL, ec=INK, lw=0.9, hatch="////"))
    centerline(a1, (-9, 0), (9, 0))
    ro, ri, hw = mm.W_OD / 2, mm.W_ID / 2, mm.W_WIDTH / 2
    rs, ht = mm.W_SHOULDER_D / 2, mm.W_TIP / 2
    dim(a1, (-ht, -ro), (-ht, ro), 9.5, "Ø23.90 OD", rot=90)
    dim(a1, (hw, -rs), (hw, rs), -3.4, "Ø18.63", rot=90, fs=7)
    dim(a1, (-hw, -ri), (-hw, ri), 2.4, "Ø15.97 bore", rot=90, fs=7)
    dim(a1, (-hw, -ro), (hw, -ro), -2.2, "10.23")
    dim(a1, (-ht, ro), (ht, ro), 2.0, "4.96 tip")
    leader(a1, (0.5, -6.5), (10.5, -2.5), "Inner lip Ø13.0 x 1.0\n(bearing stop)")
    leader(a1, (3.9, 10.8), (8.5, 14.2), "45° flank\n(90° incl.)")
    a1.set_xlim(-16, 17); a1.set_ylim(-17, 17)
    a1.set_aspect("equal"); a1.axis("off")
    a1.set_title("Section through axle", fontsize=9, loc="left", fontweight="bold")

    for r, fc in ((ro, FILL), (rs, FILL2), (ri, "white")):
        a2.add_patch(MCircle((0, 0), r, fc=fc, ec=INK, lw=0.9))
    a2.add_patch(MCircle((0, 0), 2.5, fc="white", ec=INK, lw=0.6, ls="--"))
    centerline(a2, (-15, 0), (15, 0)); centerline(a2, (0, -15), (0, 15))
    leader(a2, (ro * .707, ro * .707), (12, 15), "V rim (contacts rail)")
    leader(a2, (0, -ri), (6, -16), "625 bearing seat (x2)")
    a2.set_xlim(-16, 22); a2.set_ylim(-18, 18)
    a2.set_aspect("equal"); a2.axis("off")
    a2.set_title("Side view", fontsize=9, loc="left", fontweight="bold")
    fig.savefig(FIG / "wheel.png", dpi=260, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- hardware
def fig_hardware():
    fig, axs = plt.subplots(1, 4, figsize=(8.6, 3.0))
    # bearing section
    a = axs[0]
    for s in (1, -1):
        a.add_patch(MRect((0, s * 6.6 if s > 0 else -8), 5, 1.4, fc=FILL2, ec=INK, lw=0.8))
        a.add_patch(MRect((0, 2.5 if s > 0 else -3.8), 5, 1.3, fc=FILL2, ec=INK, lw=0.8))
        a.add_patch(MCircle((2.5, s * 5.2), 1.3, fc="white", ec=INK, lw=0.7))
    centerline(a, (-2, 0), (7, 0))
    dim(a, (0, -8), (0, 8), 2.2, "Ø16", rot=90)
    dim(a, (5, -2.5), (5, 2.5), -2.0, "Ø5", rot=90, fs=7)
    dim(a, (0, -8), (5, -8), -1.8, "5")
    a.set_title("625-2RS bearing\n5 x 16 x 5", fontsize=8.5, loc="left", fontweight="bold")
    a.set_xlim(-6, 10); a.set_ylim(-12, 11)
    # shim
    a = axs[1]
    a.add_patch(MCircle((0, 0), 5, fc=FILL, ec=INK, lw=0.8)); a.add_patch(MCircle((0, 0), 2.5, fc="white", ec=INK, lw=0.8))
    dim(a, (-5, -5.5), (5, -5.5), -1.4, "Ø10")
    dim(a, (-2.5, 0), (2.5, 0), 0.0001, "", ext=False)
    a.text(0, 1.3, "Ø5", color=DIM, fontsize=7, ha="center")
    a.text(0, 7.5, "thickness 1.0", color=DIM, fontsize=7, ha="center")
    a.set_title("Precision shim\n10 x 5 x 1", fontsize=8.5, loc="left", fontweight="bold")
    a.set_xlim(-8, 8); a.set_ylim(-12, 11)
    # aluminum spacer side
    a = axs[2]
    a.add_patch(MRect((-5, 0), 10, 6, fc=FILL, ec=INK, lw=0.8))
    a.plot([-2.55, -2.55], [0, 6], color=INK, lw=0.6, ls="--"); a.plot([2.55, 2.55], [0, 6], color=INK, lw=0.6, ls="--")
    dim(a, (-5, 0), (5, 0), -1.6, "Ø10")
    dim(a, (5, 0), (5, 6), -1.6, "6.0", rot=90)
    a.text(0, 8.2, "bore Ø5.1", color=DIM, fontsize=7, ha="center")
    a.set_title("Aluminium spacer\n6 mm", fontsize=8.5, loc="left", fontweight="bold")
    a.set_xlim(-8, 9); a.set_ylim(-12, 11)
    # eccentric spacer top view
    a = axs[3]
    R = 10 / math.sqrt(3)
    hexpts = [(R * math.cos(math.radians(30 + 60 * i)), R * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    hexpts = [(y, x) for x, y in hexpts]
    a.add_patch(Polygon(hexpts, closed=True, fc=FILL, ec=INK, lw=0.8))
    a.add_patch(MCircle((0, 0), 7.11 / 2, fc="none", ec=INK, lw=0.6, ls="--"))
    a.add_patch(MCircle((0, 0.79), 2.5, fc="white", ec=INK, lw=0.8))
    a.plot(0, 0, "+", color=NOTE, ms=6); a.plot(0, 0.79, "+", color=INK, ms=5)
    dim(a, (-5, -6.2), (5, -6.2), -1.0, "10 A/F")
    leader(a, (2.5, -2.5), (6.5, -9.5), "Ø7.11 rim, 2.5 long\n(plate hole Ø7.12)")
    leader(a, (0, 0.79), (6.5, 8.5), "Ø5 bore, 0.79 offset\n→ ±0.79 mm preload adj.")
    a.text(0, 8.6, "hex height 6.0", color=DIM, fontsize=7, ha="center")
    a.set_title("Eccentric spacer\n6 mm", fontsize=8.5, loc="left", fontweight="bold")
    a.set_xlim(-8, 14); a.set_ylim(-12, 11)
    for a in axs:
        a.set_aspect("equal"); a.axis("off")
    fig.savefig(FIG / "hardware.png", dpi=260, bbox_inches="tight", facecolor="white")
    plt.close(fig)


