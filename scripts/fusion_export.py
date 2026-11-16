"""Export unique parts + a placement layout (JSON) for building the assembly in Fusion 360.

Model frame (make_models): rail along +Z, Y up, plate B on +X.
Fusion frame (Z-up):       rail along +X, Z up, plate B on +Y.   F = R . m
Each unique part is exported once in its own local frame; the layout lists every
instance as a 4x4 matrix (Fusion frame, cm) relative to its parent component.
"""
import json
import sys
from pathlib import Path

import numpy as np
from build123d import Color, Compound, Location, Pos, Rot, Plane, export_step

sys.path.insert(0, str(Path(__file__).parent))
import make_models as mm

OUT = Path(__file__).resolve().parent.parent / "models" / "fusion"
OUT.mkdir(parents=True, exist_ok=True)

R = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)

COL = {
    "rail": (0.74, 0.76, 0.79), "plate": (0.33, 0.47, 0.66), "bar": (0.27, 0.38, 0.54),
    "wheel": (0.93, 0.88, 0.74), "steel": (0.62, 0.64, 0.67), "black": (0.12, 0.12, 0.13),
    "brass": (0.78, 0.62, 0.29), "bracket": (0.33, 0.47, 0.66),
}
LABEL_COL = {"wheel": "wheel", "bearing": "steel", "shim": "steel", "spacer": "steel",
             "screw": "black", "nut": "black", "idler": "steel", "washer": "steel",
             "bearing_F625ZZ": "steel", "bracket": "bracket", "clamp_plate": "bracket"}


def mirrored(parts):
    out = []
    for p in parts:
        m = p.mirror(Plane.XY)
        m.label = p.label
        out.append(m)
    return out


def _loc_matrix(loc: Location):
    t = loc.wrapped.Transformation()
    m = np.eye(4)
    for i in range(3):
        for j in range(4):
            m[i, j] = t.Value(i + 1, j + 1)
    return m


def fusion_matrix(m_model, conj=False):
    """Model placement -> Fusion matrix (translation converted to cm)."""
    f = R @ m_model @ (np.linalg.inv(R) if conj else np.eye(4))
    f = f.copy()
    f[:3, 3] /= 10.0
    return f.tolist()


def colored(shape, key):
    shape.color = Color(*COL[key])
    return shape


def stack(parts, name):
    kids = []
    for p in parts:
        p.color = Color(*COL[LABEL_COL.get(p.label, "steel")])
        kids.append(p)
    return Compound(children=kids, label=name)


UNIQUE = {
    "Rail_VSlot_2040_3300": lambda: colored(mm.rail(20, 40, mm.AXIS_LEN), "rail"),
    "Belt_Clamp_Assembly": lambda: stack(mm.belt_clamp_parts(), "Belt_Clamp_Assembly"),
    "Belt_Clamp_Assembly_Mirrored": lambda: stack(mirrored(mm.belt_clamp_parts()), "Belt_Clamp_Assembly_Mirrored"),
    "GT2_Belt_Straight": lambda: colored(mm.belt_straight(), "black"),
    "GT2_Belt_Omega": lambda: colored(mm.belt_omega(), "black"),
    "Plate_B_Arm_Side": lambda: colored(mm.plate_b(), "plate"),
    "Plate_A_Back_Motor": lambda: colored(mm.plate_a(), "plate"),
    "Tie_Bar": lambda: colored(mm.tie_bar(), "bar"),
    "Tie_Bar_Bottom": lambda: colored(mm.tie_bar(mm.BAR_HOLES_Z, -1), "bar"),
    "Tie_Bar_Top": lambda: colored(mm.tie_bar(mm.TOP_BAR_HOLES_Z, 1), "bar"),
    "Wheel_Stack_Fixed": lambda: stack(mm.wheel_stack(False), "Wheel_Stack_Fixed"),
    "Wheel_Stack_Eccentric": lambda: stack(mm.wheel_stack(True), "Wheel_Stack_Eccentric"),
    "Idler_Stack": lambda: stack(mm.idler_stack(), "Idler_Stack"),
    "NEMA17_Motor": lambda: colored(mm.nema17(), "black"),
    "GT2_20T_Pulley": lambda: colored(mm.gt2_pulley(), "brass"),
    "SHCS_M5x16": lambda: colored(mm.shcs_m5(16), "black"),
    "SHCS_M3x10": lambda: colored(mm.shcs(3, 10), "black"),
}


def carriage_instances():
    """(part, name, Location) relative to the carriage centre (model frame)."""
    to_x = Rot(0, 90, 0)
    plate_frame = Rot(0, -90, 0)
    g, hz = mm.GAP, mm.WHEELBASE / 2
    out = [("Plate_B_Arm_Side", "Plate B (arm side)", Pos(g / 2 + mm.PLATE_T, 0, 0) * plate_frame),
           ("Plate_A_Back_Motor", "Plate A back (motor)", Pos(-g / 2, 0, 0) * plate_frame)]
    for i, dz in enumerate((-hz, hz)):
        out.append(("Wheel_Stack_Fixed", f"Wheel top {i + 1}", Pos(-g / 2, mm.AXLE_Y, dz) * to_x))
        out.append(("Wheel_Stack_Eccentric", f"Wheel bottom {i + 1} (eccentric)", Pos(-g / 2, -mm.AXLE_Y, dz) * to_x))
    for name, y, holes, part in (("Tie bar upper", mm.BAR_Y, mm.BAR_HOLES_Z, "Tie_Bar"),
                                 ("Tie bar lower", -mm.BAR_Y, mm.BAR_HOLES_Z, "Tie_Bar_Bottom"),
                                 ("Tie bar top", mm.TOP_BAR_Y, mm.TOP_BAR_HOLES_Z, "Tie_Bar_Top")):
        out.append((part, name, Pos(0, y, 0)))
        for z in holes:
            out.append(("SHCS_M5x16", "M5x16", Pos(-g / 2 - mm.PLATE_T, y, z) * to_x))
            out.append(("SHCS_M5x16", "M5x16", Pos(g / 2 + mm.PLATE_T, y, z) * Rot(0, -90, 0)))
    for i, s in enumerate((-1, 1)):
        out.append(("Idler_Stack", f"Idler {i + 1}", Pos(-g / 2, mm.IDLER_Y, s * mm.IDLER_Z) * to_x))
    out.append(("NEMA17_Motor", "NEMA17 motor", Pos(-g / 2 - mm.PLATE_T, mm.PULLEY_Y, 0) * to_x))
    out.append(("GT2_20T_Pulley", "GT2 20T pulley", Pos(-g / 2 + 0.5, mm.PULLEY_Y, 0) * to_x))
    out.append(("GT2_Belt_Omega", "GT2 belt, omega loop", Pos(0, 0, 0)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(("SHCS_M3x10", "M3x10", Pos(-g / 2, mm.PULLEY_Y + sy * mm.NEMA_HOLES / 2,
                                                   sx * mm.NEMA_HOLES / 2) * Rot(0, -90, 0)))
    return out


def export_only(names):
    for name in names:
        export_step(UNIQUE[name](), str(OUT / f"{name}.step"))


def main():
    for name, make in UNIQUE.items():
        export_step(make(), str(OUT / f"{name}.step"))
        print("exported", name)
    L = mm.AXIS_LEN
    zc_min, zc_max = 14 + mm.PLATE_L / 2, L - 14 - mm.PLATE_L / 2
    layout = {
        "fixed": [
            {"part": "Rail_VSlot_2040_3300", "name": "Rail 2040 x 3300", "m": fusion_matrix(np.eye(4))},
            {"part": "Belt_Clamp_Assembly", "name": "Belt clamp start", "m": fusion_matrix(np.eye(4))},
            {"part": "Belt_Clamp_Assembly_Mirrored", "name": "Belt clamp end",
             "m": fusion_matrix(_loc_matrix(Pos(0, 0, L)))},
            {"part": "GT2_Belt_Straight", "name": "GT2 belt, straight run", "m": fusion_matrix(np.eye(4))},
        ],
        "carriage_home": fusion_matrix(_loc_matrix(Pos(0, 0, L / 2)), conj=True),
        "carriage": [{"part": p, "name": n, "m": fusion_matrix(_loc_matrix(loc))}
                     for p, n, loc in carriage_instances()],
        "slide_min_cm": (zc_min - L / 2) / 10, "slide_max_cm": (zc_max - L / 2) / 10,
        "step_dir": str(OUT).replace("\\", "/"),
    }
    (OUT / "layout.json").write_text(json.dumps(layout, indent=1))
    print("instances:", len(layout["carriage"]), "slide", layout["slide_min_cm"], layout["slide_max_cm"])


if __name__ == "__main__":
    main()
