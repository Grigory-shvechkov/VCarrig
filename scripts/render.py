"""Z-buffered renders of the carriage (PyVista / VTK) — no painter's-algorithm clipping."""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).parent))
import make_models as mm

COLORS = {
    "rail": "#b8bec7", "wheel": "#efe2bf", "bearing": "#8d949c", "shim": "#c9ccd0",
    "spacer": "#d3d7dc", "screw": "#3e434a", "nut": "#3e434a",
    "plate_A": "#5b7fae", "plate_B": "#6f93c2", "tie_bar": "#47658c",
    "motor": "#2b2f35", "pulley": "#c7a24a", "idler": "#9aa1a9", "belt": "#1d1d1d",
    "bracket": "#5b7fae", "standoff": "#c98b3a", "backbone": "#d9d4c7",
}


def leaves(shape, inherited=None):
    kids = list(getattr(shape, "children", ()) or ())
    lab = shape.label or inherited
    if not kids:
        yield shape, lab
    for k in kids:
        yield from leaves(k, lab)


def to_pv(shape, tol=0.04):
    v, t = shape.tessellate(tol, 0.25)
    pts = np.array([[p.X, p.Y, p.Z] for p in v])
    faces = np.hstack([np.full((len(t), 1), 3), np.array(t)]).ravel()
    return pv.PolyData(pts, faces)


def render(assy, out, camera, size=(1800, 1150), hide=()):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for shp, lab in leaves(assy):
        if lab in hide:
            continue
        mesh = to_pv(shp).compute_normals(split_vertices=True, feature_angle=35)
        pl.add_mesh(mesh, color=COLORS.get(lab, "#aaaaaa"), smooth_shading=True,
                    specular=0.25, specular_power=20, ambient=0.18, diffuse=0.85)
        edges = mesh.extract_feature_edges(feature_angle=35, boundary_edges=False,
                                           non_manifold_edges=False, manifold_edges=False)
        if edges.n_points:
            pl.add_mesh(edges, color="#2a2f36", line_width=1.0, opacity=0.55)
    pl.enable_anti_aliasing("ssaa")
    pl.camera_position = camera
    pl.screenshot(str(out))
    pl.close()


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "build" / "figs"
    out.mkdir(parents=True, exist_ok=True)
    c = mm.carriage(700, zc=450)
    focus = (0, 30, 450)
    render(c, out / "rc_front.png", [(380, 230, 180), focus, (0, 1, 0)])
    render(c, out / "rc_back.png", [(-420, 260, 260), focus, (0, 1, 0)])
    render(c, out / "rc_open.png", [(380, 160, 200), focus, (0, 1, 0)], hide=("plate_B",))
    print("rendered")
