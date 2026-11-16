# Executed inside Fusion (after fusion_build_lib.py). Poses the carriage + spinning parts
# for frame i of the animation plan and saves viewport frames.
import math, os

FRAMES_DIR = r"C:\Users\gregory\Desktop\VSlot_Carriage\build\anim"
HOME_X = 165.0                 # carriage centre at mid-rail (cm)
TRAVEL = 158.1                 # +- slide limit (cm)
R_WHEEL, R_IDLER, R_PULLEY = 1.06, 0.87, 0.6365   # rolling radii (cm)
SEG_A, SEG_B, SEG_C = 80, 170, 70                  # frames per segment (20 fps)
W, H = 1280, 720


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def plan(i):
    """-> (slide offset cm, shot name, segment progress)."""
    if i < SEG_A:
        return 25.0 * ease(i / (SEG_A - 1)), "close_open", i / (SEG_A - 1)
    i -= SEG_A
    if i < SEG_B:
        t = i / (SEG_B - 1)
        keys = [(0.0, 25.0), (0.36, TRAVEL), (0.86, -TRAVEL), (1.0, -100.0)]
        for (t0, d0), (t1, d1) in zip(keys, keys[1:]):
            if t <= t1:
                return d0 + (d1 - d0) * ease((t - t0) / (t1 - t0)), "wide", t
    i -= SEG_B
    t = i / (SEG_C - 1)
    return -100.0 + 100.0 * ease(t), "close_front", t


def total_frames():
    return SEG_A + SEG_B + SEG_C


def spinners(root):
    """[(occ, W0 world matrix at home, axis origin, axis dir, radius, sign)]"""
    out = []
    for o in root.allOccurrences:
        n = o.component.name
        if n.startswith("Solid V Wheel") or n.startswith("Bearing 625") or n.startswith("Bearing F625"):
            ctx = o.assemblyContext
            S = ctx.transform2
            org = S.translation.asPoint()
            ax = adsk.core.Vector3D.create(S.getCell(0, 2), S.getCell(1, 2), S.getCell(2, 2))
            if n.startswith("Bearing F625"):
                r, sign = R_IDLER, 1.0
            else:
                r, sign = R_WHEEL, (1.0 if org.z > 0 else -1.0)
            out.append((o, o.transform2.copy(), org, ax, r, sign))
        elif n == "GT2_20T_Pulley":
            S = o.transform2
            org = S.translation.asPoint()
            ax = adsk.core.Vector3D.create(S.getCell(0, 2), S.getCell(1, 2), S.getCell(2, 2))
            out.append((o, S.copy(), org, ax, R_PULLEY, -1.0))
    return out


def pose(car, spin, d):
    T = car.transform2
    T.translation = adsk.core.Vector3D.create(HOME_X + d, 0, 0)
    car.transform2 = T
    shift = adsk.core.Matrix3D.create()
    shift.translation = adsk.core.Vector3D.create(d, 0, 0)
    for occ, W0, org, ax, r, sign in spin:
        R = adsk.core.Matrix3D.create()
        # rolling without slip; axis dir is +Y for every spinner in this layout
        R.setToRotation(sign * d / r * (1.0 if ax.y >= 0 else -1.0), ax, org)
        M = W0.copy()
        M.transformBy(R)
        M.transformBy(shift)
        occ.transform2 = M


def set_camera(vp, shot, d, t):
    cam = vp.camera
    cam.isFitView = False
    cam.isSmoothTransition = False
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    cx = HOME_X + d
    cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    if shot == "close_open":          # plate B hidden, orbit slightly while following
        a = math.radians(55 - 25 * t)
        cam.target = adsk.core.Point3D.create(cx, 0, 3.0)
        cam.eye = adsk.core.Point3D.create(cx + 45 * math.cos(a), 45 * math.sin(a) + 8, 20)
        cam.viewExtents = 17
    elif shot == "wide":
        # fitted once in Fusion at the export aspect (vp.fit() then pulled back 1.38x)
        cam.target = adsk.core.Point3D.create(165.0, -1.5, 2.9)
        cam.eye = adsk.core.Point3D.create(239.8, 522.3, 202.5)
        cam.viewExtents = 0.4
    else:                              # front, plate B shown, following
        cam.target = adsk.core.Point3D.create(cx, 0, 3.0)
        cam.eye = adsk.core.Point3D.create(cx - 30, 50, 22)
        cam.viewExtents = 24
    vp.camera = cam


def render_frames(i0, i1):
    des = target_design()
    root = des.rootComponent
    car = find_occ(root, "Carriage")
    plate_b = [o for o in root.allOccurrences if o.component.name == "Plate_B_Arm_Side"][0]
    # home pose first so the spinner base matrices are captured consistently
    T = car.transform2; T.translation = adsk.core.Vector3D.create(HOME_X, 0, 0); car.transform2 = T
    spin = spinners(root)      # valid only at home pose with zero spin (restored below)
    for j in root.allAsBuiltJoints:
        j.isLightBulbOn = False
    os.makedirs(FRAMES_DIR, exist_ok=True)
    vp = app.activeViewport
    for i in range(i0, min(i1, total_frames())):
        d, shot, t = plan(i)
        plate_b.isLightBulbOn = (shot != "close_open")
        pose(car, spin, d)
        set_camera(vp, shot, d, t)
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(FRAMES_DIR, f"f{i:04d}.png"), W, H)
    pose(car, spin, 0.0)       # back to home with no spin so the next batch starts clean
    plate_b.isLightBulbOn = True
    return len(spin)
