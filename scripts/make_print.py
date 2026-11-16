"""Print-ready STLs for the 3D-printed prototype (same geometry as the machined parts,
holes opened up because FDM holes print undersize). Parts are oriented flat, holes vertical."""
import sys
from pathlib import Path

from build123d import Rot, Pos, export_stl, export_step

sys.path.insert(0, str(Path(__file__).parent))
import make_models as mm

HOLE_COMP = 0.2          # mm added to every hole diameter
OUT = Path(__file__).resolve().parent.parent / "print"
OUT.mkdir(exist_ok=True)


def comp(holes):
    return [(x, y, d + HOLE_COMP) for x, y, d in holes]


def drop_to_bed(shape):
    bb = shape.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * shape


parts = {
    "Plate_A_Back_Motor_PRINT": mm._plate(comp(mm.plate_a_holes())),
    "Plate_B_Arm_Side_PRINT": mm._plate(comp(mm.plate_b_holes())),
}
saved_tap = mm.TAP_M5
mm.TAP_M5 = 4.2 + HOLE_COMP        # print 4.4 -> ~4.2 real, then tap M5
parts["Tie_Bar_Middle_PRINT"] = Rot(0, 90, 0) * mm.tie_bar()                       # holes vertical
parts["Tie_Bar_Bottom_PRINT"] = Rot(0, 90, 0) * mm.tie_bar(mm.BAR_HOLES_Z, -1)
parts["Tie_Bar_Top_PRINT"] = Rot(0, 90, 0) * mm.tie_bar(mm.TOP_BAR_HOLES_Z, 1)
mm.TAP_M5 = saved_tap

for name, shape in parts.items():
    s = drop_to_bed(shape)
    export_stl(s, str(OUT / f"{name}.stl"))
    export_step(s, str(OUT / f"{name}.step"))
    bb = s.bounding_box()
    print(f"{name:28s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f} mm")
