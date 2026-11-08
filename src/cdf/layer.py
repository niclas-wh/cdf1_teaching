"""Material layers and a persistent, component-owned Rhino geometry cache."""

import hashlib

import Rhino
from System import Guid
from System.Drawing import Color


# RGB, shine (0-255), reflectivity (0-1): warm ivory and matte primary colors.
PALETTE = {
    "white": ("01_Ivory", (226, 212, 192), 22.0, 0.02),
    "black": ("02_Anthracite", (37, 38, 36), 18.0, 0.01),
    "blue": ("03_Ultramarine", (6, 38, 145), 0.0, 0.0),
    "red": ("04_Vermilion", (228, 12, 18), 0.0, 0.0),
    "yellow": ("05_SunYellow", (255, 190, 5), 0.0, 0.0),
}
ROOT = "CDF_Composition"
OWNER_KEY = "cdf.composition.owner"
STATE_SECTION = "cdf.composition.cache.v1"


def _document(doc):
    doc = Rhino.RhinoDoc.ActiveDoc if doc is None else doc
    if doc is None:
        raise RuntimeError("No active Rhino document is available.")
    return doc


def _root_index(doc):
    index = doc.Layers.FindByFullPath(ROOT, -1)
    if index >= 0:
        return index
    # Ownership tags and numeric prefixes identify older names without translating
    # arbitrary user layers or depending on a particular previous display language.
    prefixes = tuple(name[:3] for name, *_ in PALETTE.values())
    parent_ids = set()
    for obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject):
        if obj.Attributes.GetUserString(OWNER_KEY):
            item = doc.Layers[obj.Attributes.LayerIndex]
            if item.Name.startswith(prefixes):
                parent_ids.add(item.ParentLayerId)
    candidates = [item.Index for item in doc.Layers
                  if not item.IsDeleted and item.Id in parent_ids
                  and item.ParentLayerId == Guid.Empty and item.Name.startswith("CDF_")]
    if len(candidates) > 1:
        raise RuntimeError("Multiple cached composition roots found; rename the intended root to " + ROOT)
    return candidates[0] if candidates else -1


def _child_index(doc, parent_id, name):
    index = doc.Layers.FindByFullPath(ROOT + "::" + name, -1)
    if index >= 0:
        return index
    candidates = [item.Index for item in doc.Layers
                  if not item.IsDeleted and item.ParentLayerId == parent_id
                  and item.Name.startswith(name[:3])]
    if len(candidates) > 1:
        raise RuntimeError("Multiple composition layers share the prefix " + name[:3])
    return candidates[0] if candidates else -1


def ensure_layers(doc=None):
    """Create/update managed layers and materials, reusing older display names.

    A tagged composition root and uniquely numbered child layers are renamed in
    place, preserving layer IDs. Their existing CDF materials are reused when
    their names match the previous child labels. Ownership/cache keys stay stable.
    """
    doc = _document(doc)
    root_index = _root_index(doc)
    if root_index < 0:
        parent = Rhino.DocObjects.Layer()
        parent.Name = ROOT
        root_index = doc.Layers.Add(parent)
    if root_index < 0:
        raise RuntimeError("Could not create the CDF root layer.")
    parent = doc.Layers[root_index]
    parent.Name = ROOT
    parent_id = parent.Id
    indices = {}
    for key, (name, rgb, shine, reflection) in PALETTE.items():
        index = _child_index(doc, parent_id, name)
        previous_name = None
        previous_material_index = -1
        if index >= 0:
            item = doc.Layers[index]
            previous_name = item.Name
            previous_material_index = item.RenderMaterialIndex
        material_name = ROOT + "_" + name
        material_index = doc.Materials.Find(material_name, True)
        if material_index < 0 and 0 <= previous_material_index < doc.Materials.Count:
            previous_material = doc.Materials[previous_material_index]
            if (previous_material.Name.startswith("CDF_")
                    and previous_material.Name.endswith("_" + previous_name)):
                material_index = previous_material_index
        if material_index < 0:
            material_index = doc.Materials.Add()
        if material_index < 0:
            raise RuntimeError("Could not create material: " + name)
        material = doc.Materials[material_index]
        material.Name = material_name
        material.DiffuseColor = Color.FromArgb(*rgb)
        specular = 0 if key in ("blue", "red", "yellow") else 240
        material.SpecularColor = Color.FromArgb(specular, specular, specular)
        material.Shine = shine
        material.Reflectivity = reflection
        material.Transparency = 0.0
        if not material.CommitChanges():
            raise RuntimeError("Could not save material: " + name)
        if index < 0:
            item = Rhino.DocObjects.Layer()
            item.Name = name
            item.ParentLayerId = parent_id
            index = doc.Layers.Add(item)
        if index < 0:
            raise RuntimeError("Could not create material layer: " + name)
        item = doc.Layers[index]
        # Document-controlled layer setters apply immediately; no CommitChanges().
        item.Name = name
        item.Color = Color.FromArgb(*rgb)
        item.RenderMaterialIndex = material_index
        indices[key] = index
    return indices


def _fingerprint(groups):
    digest = hashlib.sha256(repr(PALETTE).encode("utf-8"))
    for key in PALETTE:
        digest.update(key.encode("ascii"))
        digest.update(str(len(groups[key])).encode("ascii"))
        for shape in groups[key]:
            digest.update(str(shape.DataCRC(0)).encode("ascii") + b";")
    return digest.hexdigest()


def cache_geometry(groups, cache_id="default", doc=None, *, force=False):
    """Synchronize only owned objects, never every object on a layer.

    Identical geometry and palette inputs preserve manual edits and deletions.
    A changed input or force=True replaces this cache's objects. Palette display
    names are part of the fingerprint, so translating them also refreshes owned
    geometry on the next recompute. Cache state is stored in the Rhino document,
    surviving module reloads and saving/reopening a 3dm file.
    """
    doc = _document(doc)
    cache_id = str(cache_id)
    if not cache_id.strip():
        raise ValueError("cache_id must not be empty.")
    if set(groups) != set(PALETTE):
        raise ValueError("Exactly the five defined color groups are required.")
    for shapes in groups.values():
        for shape in shapes:
            if shape is None or not shape.IsValid:
                raise ValueError("Invalid geometry cannot be cached.")
    signature = _fingerprint(groups)
    owned = [obj for obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject)
             if obj.Attributes.GetUserString(OWNER_KEY) == cache_id]
    if not force and doc.Strings.GetValue(STATE_SECTION, cache_id) == signature:
        return [obj.Id for obj in owned]
    if any(obj.IsLocked or obj.IsReference for obj in owned):
        raise RuntimeError("Owned cache objects are locked or referenced; make them editable before updating.")
    undo = doc.BeginUndoRecord("Update CDF composition")
    added = []
    deleted = []
    try:
        indices = ensure_layers(doc)
        for key in PALETTE:
            for number, shape in enumerate(groups[key], 1):
                attributes = Rhino.DocObjects.ObjectAttributes()
                attributes.LayerIndex = indices[key]
                attributes.Name = "CDF_{}_{:03d}".format(key, number)
                attributes.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer
                attributes.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
                attributes.SetUserString(OWNER_KEY, cache_id)
                object_id = doc.Objects.Add(shape, attributes)
                if object_id == Guid.Empty:
                    raise RuntimeError("Rhino could not add a cache object.")
                added.append(object_id)
        # Remove old objects only after every new object was added successfully.
        for obj in owned:
            if not doc.Objects.Delete(obj.Id, True):
                raise RuntimeError("Could not remove an old cache object.")
            deleted.append(obj.RuntimeSerialNumber)
        doc.Strings.SetString(STATE_SECTION, cache_id, signature)
    except Exception:
        for object_id in added:
            doc.Objects.Delete(object_id, True)
        for object_id in deleted:
            doc.Objects.Undelete(object_id)
        raise
    finally:
        if undo:
            doc.EndUndoRecord(undo)
        doc.Views.Redraw()
    return added
