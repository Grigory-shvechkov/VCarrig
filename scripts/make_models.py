"""Generate STEP models for the V-slot linear carriage project.

V-slot profile geometry follows bd_warehouse/open_builds.py (OpenBuilds V-Slot spec).
Wheel V geometry is derived so the 45 deg wheel flanks sit flush on the 45 deg rail
grooves with the wheel axle 9.85 mm from the rail face (OpenBuilds standard).
"""
import math
import sys

import numpy as np
from pathlib import Path
from build123d import *

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "models"

RAIL_LEN = 500.0
CENTER_HOLE_D = 4.2  # M5 tap drill
CORNER_R = 1.5

# ---- V-slot rail -----------------------------------------------------------
GROOVE = [(3.69, 0), (3.9, 0.21), (3.9, 2.8393398282202034), (6.560660171779773, 5.5),
          (8.2, 5.5), (8.2, 3.125), (8.545, 3.125), (10, 4.58), (10, 0)]
CAVITY = [(-8.2, 0), (-8.2, -2.7), (-6.23933983, -2.7), (-2.83933983, -6.1), (0, -6.1)]


def mirrored_face(pts, axes):
    with BuildSketch() as s:
        with BuildLine():
            Polyline(*pts)
            for a in axes:
                mirror(about=a)
        make_face()
    return s.sketch


def vslot_profile(width, height):
    groove = mirrored_face(GROOVE, [Plane.XZ])
    cavity = mirrored_face(CAVITY, [Plane.XZ, Plane.YZ])
    grooves = {
        (20, 20): ([(0, 0)] * 4, [0, 90, 180, 270]),
        (20, 40): ([(0, 10), (0, 10), (0, 10), (0, -10), (0, -10), (0, -10)],
                   [0, 90, 180, 180, 270, 0]),
    }[(width, height)]
    with BuildSketch() as v:
        RectangleRounded(width, height, CORNER_R)
        with GridLocations(20, 20, width // 20, height // 20):
            Circle(CENTER_HOLE_D / 2, mode=Mode.SUBTRACT)
        for pos, ang in zip(*grooves):
            with Locations(pos):
                add(groove.rotate(Axis.Z, ang), mode=Mode.SUBTRACT)
        if height == 40:
            add(cavity, mode=Mode.SUBTRACT)
    return v.sketch


def rail(width, height, length=RAIL_LEN):
    return extrude(vslot_profile(width, height), amount=length)


# ---- Solid V wheel (OpenBuilds style) --------------------------------------
W_OD, W_ID, W_WIDTH = 23.90, 15.97, 10.23
W_TIP = 4.96            # flat land at the OD
W_SHOULDER_D = 18.63    # where the 45 deg flanks meet the side faces
W_LIP_D, W_LIP_W = 13.0, 1.0  # internal lip between the two bearings
AXLE_TO_FACE = 9.85     # wheel axle to rail outer face


def wheel():
    ro, ri, hw = W_OD / 2, W_ID / 2, W_WIDTH / 2
    rs, ht, rl, hl = W_SHOULDER_D / 2, W_TIP / 2, W_LIP_D / 2, W_LIP_W / 2
    pts = [(ri, -hw), (rs, -hw), (ro, -ht), (ro, ht), (rs, hw), (ri, hw),
           (ri, hl), (rl, hl), (rl, -hl), (ri, -hl), (ri, -hw)]
    with BuildPart() as p:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline(*pts)
            make_face()
        revolve(axis=Axis.Z)
    return p.part


def ring(od, id_, h):
    return Cylinder(od / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)) - \
        Cylinder(id_ / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def bearing_625():  # 5 x 16 x 5, simplified outer/inner race + shields
    outer = ring(16, 13.2, 5)
    inner = ring(7.6, 5, 5)
    shield = ring(13.2, 7.6, 4.6).translate((0, 0, 0.2))
    return outer + inner + shield


def precision_shim():
    return ring(10, 5, 1)


def aluminum_spacer(h=6):
    return ring(10, 5.1, h)


def eccentric_spacer(h=6):
    # 10 mm across flats hex body, 7.11 mm rim that drops into the plate hole,
    # 5 mm bore offset 0.79 mm from the rim axis.
    with BuildPart() as p:
        with BuildSketch():
            RegularPolygon(10 / math.sqrt(3), 6, major_radius=True)
        extrude(amount=h)
        Cylinder(7.11 / 2, 2.5, align=(Align.CENTER, Align.CENTER, Align.MAX))
        with Locations((0, 0.79, 0)):
            Cylinder(2.5, 30, mode=Mode.SUBTRACT)
    return p.part


def wheel_assembly(eccentric=False):
    """Stack along +Z starting at the plate face (z=0)."""
    sp = eccentric_spacer() if eccentric else aluminum_spacer()
    if eccentric:
        # bore on the Z axis; rim centre 0.79 to local +x (= back along the rail once the
        # stack is placed), so turning the hex moves the axle +-0.79 up/down for preload
        sp = sp.translate((0, -0.79, 0)).rotate(Axis.Z, 90)
    z = 6  # bearing / shim / bearing stack = 5 + 1 + 5, wheel centred on it
    b1 = bearing_625().translate((0, 0, z))
    sh = precision_shim().translate((0, 0, z + 5))
    b2 = bearing_625().translate((0, 0, z + 6))
    w = wheel().translate((0, 0, z + 5.5))
    for part, lab in ((sp, "spacer"), (b1, "bearing"), (sh, "shim"), (b2, "bearing"), (w, "wheel")):
        part.label = lab
    return Compound(children=[sp, b1, sh, b2, w], label="wheel_assy")


# ---- Rev C: double-plate carriage on a 3.3 m 20x40, GT2 omega drive ----------
# Global frame: rail runs along +Z, rail profile in XY (20 wide in X, 40 tall in Y).
# Plate B (+X side) is the full arm-mount plate. On the -X side the rail is stood off a
# backbone beam by blocks every 400 mm, so plate A is split into an upper strip (motor,
# idlers, fixed wheels) and a lower strip (eccentric wheels) that pass either side of
# the standoffs. Wheels, idlers and tie bars sit between the plates, so every axle is
# still supported at both ends (double shear).
RAIL_H = 40
TRAVEL = 3124.2          # 10 ft 3 in
AXIS_LEN = 3300.0        # rail length: travel + carriage + belt clamps + margin
STANDOFF_T = 14.0        # rail back face -> backbone (clears M5 heads on plate A)
STANDOFF_H = 34.0
STANDOFF_L = 30.0
STANDOFF_PITCH = 400.0
STRIP_EDGE = 19.0        # plate A strips stop 2 mm short of the standoffs
BACKBONE_W, BACKBONE_H = 40.0, 80.0
PLATE_T = 6.0
GAP = 23.0               # plate inner face to inner face (6 spacer + 11 wheel stack + 6 spacer)
PLATE_L = 110.0
WHEELBASE = 70.0
AXLE_Y = RAIL_H / 2 + AXLE_TO_FACE           # 29.85
BAR_H = 12.0
BAR_Y = AXLE_Y + W_OD / 2 + 2.2 + BAR_H / 2   # 50.0 -> bars span 44..56 / -56..-44
BAR_HOLES_Z = (-42.0, 0.0, 42.0)
TOP_BAR_HOLES_Z = (-42.0, 42.0)               # z=0 is under the motor
HOLE_FIXED = 5.1
HOLE_ECC = 7.12
ECC_OFFSET = 0.79       # eccentric spacer bore offset
HOLE_FAR_ECC = 6.8       # plate B clearance for the eccentric axle (2.5 + 0.79 offset + slack)
TAP_M5 = 4.2
BELT_END = 1.0          # belt end inside the clamp, from the rail end

# Drive (GT2 6 mm belt, omega wrap)
BELT_W, BELT_T = 6.0, 1.4
IDLER_D, IDLER_FLANGE_D, IDLER_W = 16.0, 18.0, 10.0   # 2x F625ZZ back to back
IDLER_Y = 68.0
IDLER_Z = 28.0                                        # +/- from carriage centre, clear of motor
BELT_Y = IDLER_Y - IDLER_D / 2 - BELT_T / 2           # 59.3 belt centreline along the rail
PULLEY_PD = 12.73                                     # GT2 20T pitch diameter
PULLEY_Y = 84.0
NEMA = 42.3
NEMA_LEN = 40.0
NEMA_HOLES = 31.0
NEMA_PILOT = 22.5
BELT_X = -GAP / 2 + 12.0     # belt / idler / pulley-teeth centre plane (0.5)
TOP_BAR_Y = PULLEY_Y + NEMA_HOLES / 2 + 3.2 + BAR_H / 2   # 108.7: clears the M3 motor-screw heads
PLATE_Y0, PLATE_Y1 = -(BAR_Y + BAR_H / 2), TOP_BAR_Y + BAR_H / 2   # -56 .. 114.7
PLATE_H = PLATE_Y1 - PLATE_Y0
PLATE_YC = (PLATE_Y0 + PLATE_Y1) / 2


def _plate(holes, y0=None, y1=None):
    """Plate in its own frame: X = along rail, Y = up, Z = thickness."""
    y0 = PLATE_Y0 if y0 is None else y0
    y1 = PLATE_Y1 if y1 is None else y1
    holes = [h for h in holes if y0 < h[1] < y1]
    with BuildPart() as p:
        with BuildSketch():
            with Locations((0, (y0 + y1) / 2)):
                RectangleRounded(PLATE_L, y1 - y0, 4)
            for x, y, d in holes:
                with Locations((x, y)):
                    Circle(d / 2, mode=Mode.SUBTRACT)
        extrude(amount=PLATE_T)
    return p.part


def _common_holes():
    hz = WHEELBASE / 2
    holes = [(s * hz, AXLE_Y, HOLE_FIXED) for s in (-1, 1)]
    holes += [(z, sy * BAR_Y, HOLE_FIXED) for z in BAR_HOLES_Z for sy in (-1, 1)]
    holes += [(z, TOP_BAR_Y, HOLE_FIXED) for z in TOP_BAR_HOLES_Z]
    holes += [(s * IDLER_Z, IDLER_Y, HOLE_FIXED) for s in (-1, 1)]
    return holes


def plate_a_holes():
    holes = _common_holes()
    holes += [(s * WHEELBASE / 2 - ECC_OFFSET, -AXLE_Y, HOLE_ECC) for s in (-1, 1)]   # rim centre
    holes += [(0, PULLEY_Y, NEMA_PILOT)]
    holes += [(sx * NEMA_HOLES / 2, PULLEY_Y + sy * NEMA_HOLES / 2, 3.4) for sx in (-1, 1) for sy in (-1, 1)]
    return holes


def plate_a():
    """Full back plate (motor side). Use the upper/lower strips instead once the rail is
    stood off a backbone."""
    return _plate(plate_a_holes())


def plate_a_upper():
    return _plate(plate_a_holes(), STRIP_EDGE, PLATE_Y1)


def plate_a_lower():
    return _plate(plate_a_holes(), PLATE_Y0, -STRIP_EDGE)


def plate_b_holes():
    holes = _common_holes()
    holes += [(s * WHEELBASE / 2, -AXLE_Y, HOLE_FAR_ECC) for s in (-1, 1)]
    return holes


def plate_b():
    return _plate(plate_b_holes())


PLATE_CORNER_R = 4.0


def tie_bar(holes_z=BAR_HOLES_Z, round_side=0):
    """GAP wide (X) x BAR_H tall (Y) x PLATE_L long (Z); M5 tapped from both ends.
    round_side=+1/-1 rounds the two end corners on the +Y/-Y face to the plate's R4 so a
    bar that sits flush with the plate edge follows the plate outline."""
    with BuildPart() as p:
        Box(GAP, BAR_H, PLATE_L)
        if round_side:
            corners = [e for e in p.edges().filter_by(Axis.X)
                       if abs(e.center().Y - round_side * BAR_H / 2) < 1e-6
                       and abs(abs(e.center().Z) - PLATE_L / 2) < 1e-6]
            fillet(corners, PLATE_CORNER_R)
        for z in holes_z:
            with Locations(Pos(0, 0, z) * Rot(0, 90, 0)):
                Cylinder(TAP_M5 / 2, GAP, mode=Mode.SUBTRACT)
    return p.part


def shcs(d, length):
    """Socket head cap screw along +Z, head below z=0."""
    hd, hh = 1.7 * d, d
    head = Cylinder(hd / 2, hh, align=(Align.CENTER, Align.CENTER, Align.MAX))
    shank = Cylinder(d / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    sock = Pos(0, 0, -hh) * Cylinder(0.4 * d, 0.5 * hh, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return head + shank - sock


def shcs_m5(length):
    return shcs(5, length)


def nyloc_m5():
    with BuildPart() as p:
        with BuildSketch():
            RegularPolygon(8 / math.sqrt(3), 6)
            Circle(2.5, mode=Mode.SUBTRACT)
        extrude(amount=5)
    return p.part


def smooth_idler():
    """Two F625ZZ flanged bearings back to back: 16 running OD, 18 flanges, 10 wide, 5 bore."""
    body = ring(IDLER_D, 5, IDLER_W)
    fl = ring(IDLER_FLANGE_D, 5, 1)
    return body + fl + fl.translate((0, 0, IDLER_W - 1))


def f625zz():
    """Flanged 625ZZ: 5 x 16 x 5, 18 x 1 flange at z=0."""
    return bearing_625() + ring(IDLER_FLANGE_D, 13.2, 1)


def washer_m5():
    return ring(10, 5.3, 1)


def gt2_pulley():
    """GT2 20T, 5 mm bore: hub 7 long, 1 + 7 + 1 belt section. z=0 at hub end."""
    hub = ring(16, 5, 7)
    f1 = ring(16, 5, 1).translate((0, 0, 7))
    teeth = ring(12.2, 5, 7).translate((0, 0, 8))
    f2 = ring(16, 5, 1).translate((0, 0, 15))
    return hub + f1 + teeth + f2


def nema17():
    """Body behind z=0 (mounting face), boss + shaft forward along +Z."""
    with BuildPart() as p:
        with BuildSketch():
            Rectangle(NEMA, NEMA)
            fillet(vertices(), 4)
        extrude(amount=-NEMA_LEN)
        Cylinder(11, 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(2.5, 24, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def wheel_stack(eccentric=False):
    """Local Z = axle; z=0 at plate A inner face, z=GAP at plate B inner face."""
    a = wheel_assembly(eccentric)
    far = aluminum_spacer().translate((0, 0, 17))
    far.label = "spacer"
    out = list(a.children) + [far]
    if eccentric:   # plate B has a 6.8 clearance hole here, so clamp through a washer
        washer = washer_m5().translate((0, 0, GAP + PLATE_T))
        washer.label = "washer"
        out += [washer, _lab(shcs_m5(45).translate((0, 0, -PLATE_T)), "screw"),
                _lab(nyloc_m5().translate((0, 0, GAP + PLATE_T + 1)), "nut")]
    else:
        out += [_lab(shcs_m5(40).translate((0, 0, -PLATE_T)), "screw"),
                _lab(nyloc_m5().translate((0, 0, GAP + PLATE_T)), "nut")]
    return out


def idler_stack():
    """6 spacer + 1 shim + 2x F625ZZ (flanges outward, 10) + 6 spacer = 23."""
    parts = [(aluminum_spacer(), "spacer", 0), (precision_shim(), "shim", 6),
             (f625zz(), "bearing_F625ZZ", 7),                       # flange at z 7..8
             (f625zz().mirror(Plane.XY), "bearing_F625ZZ", 17),     # flange at z 16..17
             (aluminum_spacer(), "spacer", 17),
             (shcs_m5(40), "screw", -PLATE_T), (nyloc_m5(), "nut", GAP + PLATE_T)]
    out = []
    for shp, lab, z in parts:
        s = shp.translate((0, 0, z))
        s.label = lab
        out.append(s)
    return out


def _circle_tangent(c1, r1, ccw1, c2, r2, ccw2):
    """Tangent segment leaving circle 1 and arriving on circle 2 for a belt that wraps
    c1 counter-clockwise (ccw1) / clockwise and c2 likewise. Returns (p1, p2)."""
    c1, c2 = np.array(c1, float), np.array(c2, float)
    s1 = 1 if ccw1 else -1      # centre lies on the left of travel for CCW
    s2 = 1 if ccw2 else -1
    D = c2 - c1
    beta = math.atan2(D[1], D[0])
    k = (s1 * r1 - s2 * r2) / np.linalg.norm(D)
    # D . left(d) = -(s1*r1 - s2*r2)  ->  |D| sin(beta - t) = -k|D|
    t = beta + math.asin(k)
    d = np.array([math.cos(t), math.sin(t)])
    left = np.array([-d[1], d[0]])
    return c1 - s1 * r1 * left, c2 - s2 * r2 * left


def _arc(c, r, p_from, p_to, ccw, n=24):
    a0 = math.atan2(p_from[1] - c[1], p_from[0] - c[0])
    a1 = math.atan2(p_to[1] - c[1], p_to[0] - c[0])
    if ccw and a1 < a0:
        a1 += 2 * math.pi
    if not ccw and a1 > a0:
        a1 -= 2 * math.pi
    return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


def belt_path(z_start, z_end, zc):
    """Belt centreline in the (z, y) plane: straight run, omega wrap at the carriage."""
    ri = IDLER_D / 2 + BELT_T / 2        # belt back rides on the idlers
    rp = PULLEY_PD / 2                   # pitch line on the pulley
    i1, p, i2 = (zc - IDLER_Z, IDLER_Y), (zc, PULLEY_Y), (zc + IDLER_Z, IDLER_Y)
    a1, b1 = _circle_tangent(i1, ri, True, p, rp, False)
    a2, b2 = _circle_tangent(p, rp, False, i2, ri, True)
    pts = [(z_start, BELT_Y), (i1[0], BELT_Y)]
    pts += _arc(i1, ri, (i1[0], BELT_Y), a1, True)[1:]
    pts += _arc(p, rp, b1, a2, False, 40)
    pts += _arc(i2, ri, b2, (i2[0], BELT_Y), True)[:-1]
    pts += [(i2[0], BELT_Y), (z_end, BELT_Y)]
    clean = [pts[0]]
    for q in pts[1:]:
        if math.dist(q, clean[-1]) > 1e-3:
            clean.append(q)
    return clean


def belt(z_start, z_end, zc):
    pts = belt_path(z_start, z_end, zc)
    pl = Plane(origin=(BELT_X + BELT_W / 2, 0, 0), x_dir=(0, 0, 1), z_dir=(-1, 0, 0))
    with BuildPart() as p:
        with BuildSketch(pl):
            with BuildLine():
                Polyline(*pts)
            trace(line_width=BELT_T)
        extrude(amount=BELT_W)
    return p.part


CLAMP_BLOCK_Y1 = BELT_Y - BELT_T / 2          # belt lies on the block top
CLAMP_PLATE_T = 3.0
CLAMP_SCREW_X = 7.0


def belt_from_points(pts):
    pl = Plane(origin=(BELT_X + BELT_W / 2, 0, 0), x_dir=(0, 0, 1), z_dir=(-1, 0, 0))
    with BuildPart() as p:
        with BuildSketch(pl):
            with BuildLine():
                Polyline(*pts)
            trace(line_width=BELT_T)
        extrude(amount=BELT_W)
    return p.part


def belt_omega():
    """The part of the belt lifted off the straight run, relative to the carriage centre."""
    return belt_from_points(belt_path(-IDLER_Z, IDLER_Z, 0))


def belt_straight(rail_len=AXIS_LEN):
    return belt_from_points([(BELT_END, BELT_Y), (rail_len - BELT_END, BELT_Y)])


def belt_end_bracket():
    """Bolts to the rail end (2x M5 into the 2040 centre bores). Local: z=0 at rail end
    face, bracket plate behind it (z<0), belt clamp block in front (z>0, 14 deep).
    The belt lies on the block and is pinched by a clamp plate with 2x M3 (tapped block)."""
    with BuildPart() as p:
        y0, y1 = -RAIL_H / 2, CLAMP_BLOCK_Y1 + BELT_T + CLAMP_PLATE_T
        with Locations((0, (y0 + y1) / 2, -3)):
            Box(20, y1 - y0, 6)
        with Locations((0, CLAMP_BLOCK_Y1 - 5, 7)):
            Box(20, 10, 14)
        for y in (-10, 10):
            with Locations(Pos(0, y, -3)):
                Cylinder(2.75, 6, mode=Mode.SUBTRACT)
        for x in (-CLAMP_SCREW_X, CLAMP_SCREW_X):
            with Locations(Pos(x, CLAMP_BLOCK_Y1 - 4, 7) * Rot(90, 0, 0)):
                Cylinder(1.25, 8, mode=Mode.SUBTRACT)        # M3 tap drill
    return p.part


def belt_clamp_plate():
    with BuildPart() as p:
        with Locations((0, CLAMP_BLOCK_Y1 + BELT_T + CLAMP_PLATE_T / 2, 7)):
            Box(20, CLAMP_PLATE_T, 14)
        for x in (-CLAMP_SCREW_X, CLAMP_SCREW_X):
            with Locations(Pos(x, CLAMP_BLOCK_Y1 + BELT_T + CLAMP_PLATE_T / 2, 7) * Rot(90, 0, 0)):
                Cylinder(1.7, CLAMP_PLATE_T, mode=Mode.SUBTRACT)
    return p.part


def belt_clamp_parts():
    """Bracket, clamp plate, 2x M5x12 into the rail end, 2x M3x10 through the clamp plate."""
    parts = [_lab(belt_end_bracket(), "bracket"), _lab(belt_clamp_plate(), "clamp_plate")]
    for y in (-10, 10):
        parts.append(_lab(Pos(0, y, -6) * shcs_m5(12), "screw"))
    top = CLAMP_BLOCK_Y1 + BELT_T + CLAMP_PLATE_T
    for x in (-CLAMP_SCREW_X, CLAMP_SCREW_X):
        parts.append(_lab(Pos(x, top, 7) * Rot(90, 0, 0) * shcs(3, 10), "screw"))
    return parts


def standoff_block():
    """Rail back face (x=-10) to backbone (x=-10-STANDOFF_T). Global-aligned, centred on z=0.
    Rail side: 2x M5 counterbored from the backbone face into drop-in T-nuts (slots at y=+-10).
    Backbone side: 2x M5 tapped, screws come through the backbone."""
    x0 = -RAIL_H / 4 - STANDOFF_T          # -24
    with BuildPart() as p:
        with Locations((x0 + STANDOFF_T / 2, 0, 0)):
            Box(STANDOFF_T, STANDOFF_H, STANDOFF_L)
        for y in (-10, 10):
            with Locations(Pos(x0, y, -8) * Rot(0, 90, 0)):
                Cylinder(2.75, STANDOFF_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
                Cylinder(4.75, 5.5, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            with Locations(Pos(x0, y, 8) * Rot(0, 90, 0)):
                Cylinder(TAP_M5 / 2, STANDOFF_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def standoff_positions(rail_len):
    n = int((rail_len - 100) // STANDOFF_PITCH) + 1
    first = (rail_len - (n - 1) * STANDOFF_PITCH) / 2
    return [first + i * STANDOFF_PITCH for i in range(n)]


def backbone(length):
    """Placeholder for the support beam / wall (e.g. 40x80 extrusion or steel tube)."""
    x1 = -RAIL_H / 4 - STANDOFF_T
    return Pos(x1 - BACKBONE_W / 2, 0, length / 2) * Box(BACKBONE_W, BACKBONE_H, length)


def _lab(shape, label):
    shape.label = label
    return shape


def carriage(rail_len=AXIS_LEN, zc=None, drive=True, brackets=True, support=False, split_back=False):
    zc = rail_len / 2 if zc is None else zc
    to_x = Rot(0, 90, 0)                        # local +Z -> global +X
    kids = [_lab(rail(20, RAIL_H, rail_len), "rail")]

    def place(parts, loc):
        for part in parts:
            moved = loc * part
            moved.label = part.label
            kids.append(moved)

    for dz in (-WHEELBASE / 2, WHEELBASE / 2):
        for y, ecc in ((AXLE_Y, False), (-AXLE_Y, True)):
            place(wheel_stack(ecc), Pos(-GAP / 2, y, zc + dz) * to_x)
    plate_frame = Rot(0, -90, 0)                 # plate X -> global Z, plate Z -> global X
    backs = (plate_a_upper(), plate_a_lower()) if split_back else (plate_a(),)
    for back in backs:
        kids.append(_lab(Pos(-GAP / 2, 0, zc) * plate_frame * back, "plate_A"))
    kids.append(_lab(Pos(GAP / 2 + PLATE_T, 0, zc) * plate_frame * plate_b(), "plate_B"))
    for y, hz, rs in ((BAR_Y, BAR_HOLES_Z, 0), (-BAR_Y, BAR_HOLES_Z, -1), (TOP_BAR_Y, TOP_BAR_HOLES_Z, 1)):
        kids.append(_lab(Pos(0, y, zc) * tie_bar(hz, rs), "tie_bar"))
        for z in hz:
            kids.append(_lab(Pos(-GAP / 2 - PLATE_T, y, zc + z) * to_x * shcs_m5(16), "screw"))
            kids.append(_lab(Pos(GAP / 2 + PLATE_T, y, zc + z) * Rot(0, -90, 0) * shcs_m5(16), "screw"))
    if drive:
        for s in (-1, 1):
            place(idler_stack(), Pos(-GAP / 2, IDLER_Y, zc + s * IDLER_Z) * to_x)
        kids.append(_lab(Pos(-GAP / 2 - PLATE_T, PULLEY_Y, zc) * to_x * nema17(), "motor"))
        kids.append(_lab(Pos(-GAP / 2 + 0.5, PULLEY_Y, zc) * to_x * gt2_pulley(), "pulley"))
        for sx in (-1, 1):
            for sy in (-1, 1):
                kids.append(_lab(Pos(-GAP / 2, PULLEY_Y + sy * NEMA_HOLES / 2, zc + sx * NEMA_HOLES / 2)
                                 * Rot(0, -90, 0) * shcs(3, 10), "screw"))
        if brackets:
            for part in belt_clamp_parts():
                kids.append(part)
                far = Pos(0, 0, rail_len) * part.mirror(Plane.XY)
                far.label = part.label
                kids.append(far)
        kids.append(_lab(belt(BELT_END, rail_len - BELT_END, zc), "belt"))
    if support:
        for z in standoff_positions(rail_len):
            kids.append(_lab(Pos(0, 0, z) * standoff_block(), "standoff"))
        kids.append(_lab(backbone(rail_len), "backbone"))
    return Compound(children=kids, label="vslot_axis")


def belt_length(rail_len=AXIS_LEN):
    pts = belt_path(BELT_END, rail_len - BELT_END, rail_len / 2)
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    parts = {
        "VSlot_2040_3300mm": rail(20, 40, AXIS_LEN),
        "VSlot_2020_500mm": rail(20, 20),
        "Solid_V_Wheel": wheel(),
        "Bearing_625_2RS_5x16x5": bearing_625(),
        "Precision_Shim_10x5x1": precision_shim(),
        "Aluminum_Spacer_6mm": aluminum_spacer(),
        "Eccentric_Spacer_6mm": eccentric_spacer(),
        "Wheel_Assembly_Fixed": wheel_assembly(False),
        "Wheel_Assembly_Eccentric": wheel_assembly(True),
        "Plate_A_Back_Motor": plate_a(),
        "Plate_B_Arm_Side": plate_b(),
        "Tie_Bar_Middle_23x12x110": tie_bar(),
        "Tie_Bar_Bottom_23x12x110": tie_bar(BAR_HOLES_Z, -1),
        "Tie_Bar_Top_23x12x110": tie_bar(TOP_BAR_HOLES_Z, 1),
        "Smooth_Idler_F625ZZx2": smooth_idler(),
        "GT2_20T_Pulley_5mm": gt2_pulley(),
        "NEMA17_40mm": nema17(),
        "Belt_End_Bracket": belt_end_bracket(),
        "Carriage_Section_600mm": carriage(600),
        "Full_Axis_3300mm": carriage(),
    }
    for name, shape in parts.items():
        export_step(shape, str(OUT / f"{name}.step"))
        export_stl(shape, str(OUT / f"{name}.stl"))
        bb = shape.bounding_box()
        print(f"{name:30s} {bb.size.X:7.2f} x {bb.size.Y:7.2f} x {bb.size.Z:8.2f}  vol={shape.volume:10.1f}")
    print(f"belt length {belt_length():.0f} mm; travel available "
          f"{AXIS_LEN - 2 * (14 + PLATE_L / 2):.0f} mm (need {TRAVEL})")
    print("standoffs at", standoff_positions(AXIS_LEN))
