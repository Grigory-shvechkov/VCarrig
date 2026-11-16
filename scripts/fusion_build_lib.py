# Executed inside Fusion via the MCP bridge (exec'd with app/design/adsk in scope).
# Imports each unique STEP into a throw-away document, copies its bodies into a new
# component of the target design, then places every instance from layout.json.
import json, os
import adsk.core, adsk.fusion

LAYOUT_PATH = r"C:\Users\gregory\Desktop\VSlot_Carriage\models\fusion\layout.json"
TARGET_DOC = "Print_Bed_Scanner"


def target_design():
    for d in app.documents:
        if d.name == TARGET_DOC:
            d.activate()
            return adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
    raise RuntimeError("target document not open")


def matrix(rows):
    m = adsk.core.Matrix3D.create()
    m.setWithArray([v for row in rows for v in row])
    return m


def read_bodies(step_path):
    """Return [(name, transient body)] from a STEP file via importToNewDocument."""
    im = app.importManager
    doc = im.importToNewDocument(im.createSTEPImportOptions(step_path))
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    tbm = adsk.fusion.TemporaryBRepManager.get()
    out = []
    root = des.rootComponent
    for b in root.bRepBodies:
        out.append((b.name, tbm.copy(b)))
    for occ in root.allOccurrences:
        for b in occ.bRepBodies:          # proxies -> geometry in assembly context
            out.append((occ.component.name, tbm.copy(b)))
    doc.close(False)
    return out


def find_occ(parent_comp, name):
    for o in parent_comp.occurrences:
        if o.name.split(":")[0] == name:
            return o
    return None


def make_component(parent_comp, comp_name, bodies, m):
    occ = parent_comp.occurrences.addNewComponent(m)
    comp = occ.component
    comp.name = comp_name
    bf = comp.features.baseFeatures.add()
    bf.startEdit()
    try:
        for name, body in bodies:
            nb = comp.bRepBodies.add(body, bf)
            nb.name = name
    finally:
        bf.finishEdit()
    return occ


def place(parent_comp, part, instances, step_dir):
    """Import `part` once into parent_comp (first instance), then add placed copies."""
    n0 = parent_comp.occurrences.count
    im = app.importManager
    if not im.importToTarget(im.createSTEPImportOptions(os.path.join(step_dir, part + ".step")), parent_comp):
        raise RuntimeError("import failed: " + part)
    first = parent_comp.occurrences.item(parent_comp.occurrences.count - 1)
    assert parent_comp.occurrences.count == n0 + 1
    comp = first.component
    comp.name = part
    # Nested occurrences can't take a transform override, so add every placed instance
    # as a copy and then drop the identity-placed import.
    occs = [parent_comp.occurrences.addExistingComponent(comp, matrix(inst["m"])) for inst in instances]
    first.deleteMe()
    return occs


def layout():
    with open(LAYOUT_PATH) as f:
        return json.load(f)


def rail_edge(rail_occ):
    for e in rail_occ.bRepBodies.item(0).edges:
        g = e.geometry
        if isinstance(g, adsk.core.Line3D):
            v = g.startPoint.vectorTo(g.endPoint)
            if v.length > 300 and abs(v.x) > 0.999 * v.length:
                return e
    raise RuntimeError("no rail edge along X")


def build_all():
    """Wipe the design and rebuild Rail Assembly + Carriage + slider joint from layout.json."""
    L = layout()
    des = target_design()
    root = des.rootComponent
    for j in list(root.asBuiltJoints):
        j.deleteMe()
    for o in list(root.occurrences):
        o.deleteMe()
    car = root.occurrences.addNewComponent(matrix(L["carriage_home"]))
    car.component.name = "Carriage"
    groups = {}
    for inst in L["carriage"]:
        groups.setdefault(inst["part"], []).append(inst)
    for part, insts in groups.items():
        place(car.component, part, insts, L["step_dir"])
    grp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    grp.component.name = "Rail Assembly"
    for inst in L["fixed"]:
        place(grp.component, inst["part"], [inst], L["step_dir"])
    grp.isGrounded = True
    rail = [o for o in grp.childOccurrences if o.component.name.startswith("Rail_VSlot")][0]
    geo = adsk.fusion.JointGeometry.createByCurve(rail_edge(rail), adsk.fusion.JointKeyPointTypes.StartKeyPoint)
    ji = root.asBuiltJoints.createInput(car, grp, geo)
    ji.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    j = root.asBuiltJoints.add(ji)
    j.name = "Carriage travel"
    lim = j.jointMotion.slideLimits
    lim.isMinimumValueEnabled = True; lim.minimumValue = L["slide_min_cm"]
    lim.isMaximumValueEnabled = True; lim.maximumValue = L["slide_max_cm"]
    return car, grp, j
