"""Material layers and a persistent, component-owned Rhino geometry cache."""

import hashlib

import Rhino
from System import Guid
from System.Drawing import Color


def _palette(palette):
    if palette is None:
        from .assignment_01 import PALETTE
        return PALETTE
    return palette


ROOT = "CDF_Composition"
OWNER_KEY = "cdf.composition.owner"
ROOT_KEY = "cdf.cache.root"
STATE_SECTION = "cdf.composition.cache.v1"


def _document(doc):
    doc = Rhino.RhinoDoc.ActiveDoc if doc is None else doc
    if doc is None:
        raise RuntimeError("No active Rhino document is available.")
    return doc


def _root_index(doc, palette, root):
    index = doc.Layers.FindByFullPath(root, -1)
    if index >= 0:
        return index
    if root != ROOT:
        return -1
    # Ownership tags and numeric prefixes identify older names without translating
    # arbitrary user layers or depending on a particular previous display language.
    prefixes = tuple(name[:3] for name, *_ in palette.values())
    parent_ids = set()
    for obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject):
        if (obj.Attributes.GetUserString(OWNER_KEY)
                and obj.Attributes.GetUserString(ROOT_KEY) in (None, "", root)):
            item = doc.Layers[obj.Attributes.LayerIndex]
            if item.Name.startswith(prefixes):
                parent_ids.add(item.ParentLayerId)
    candidates = [item.Index for item in doc.Layers
                  if not item.IsDeleted and item.Id in parent_ids
                  and item.ParentLayerId == Guid.Empty and item.Name.startswith("CDF_")]
    if len(candidates) > 1:
        raise RuntimeError("Multiple cached composition roots found; rename the intended root to " + root)
    return candidates[0] if candidates else -1


def _child_index(doc, parent_id, name, root):
    index = doc.Layers.FindByFullPath(root + "::" + name, -1)
    if index >= 0:
        return index
    candidates = [item.Index for item in doc.Layers
                  if not item.IsDeleted and item.ParentLayerId == parent_id
                  and item.Name.startswith(name[:3])]
    if len(candidates) > 1:
        raise RuntimeError("Multiple composition layers share the prefix " + name[:3])
    return candidates[0] if candidates else -1


def ensure_layers(doc=None, *, palette=None, root=ROOT):
    """Create/update managed layers and materials, reusing older display names.

    A tagged composition root and uniquely numbered child layers are renamed in
    place, preserving layer IDs. Their existing CDF materials are reused when
    their names match the previous child labels. Ownership/cache keys stay stable.
    """
    doc = _document(doc)
    palette = _palette(palette)
    root_index = _root_index(doc, palette, root)
    if root_index < 0:
        parent = Rhino.DocObjects.Layer()
        parent.Name = root
        root_index = doc.Layers.Add(parent)
    if root_index < 0:
        raise RuntimeError("Could not create the CDF root layer.")
    parent = doc.Layers[root_index]
    parent.Name = root
    parent_id = parent.Id
    indices = {}
    for key, (name, rgb, shine, reflection) in palette.items():
        index = _child_index(doc, parent_id, name, root)
        previous_name = None
        previous_material_index = -1
        if index >= 0:
            item = doc.Layers[index]
            previous_name = item.Name
            previous_material_index = item.RenderMaterialIndex
        material_name = root + "_" + name
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
        specular = 0 if shine == 0 else 240
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


def _fingerprint(groups, palette, root):
    digest = hashlib.sha256(repr(palette).encode("utf-8"))
    for key in palette:
        digest.update(key.encode("ascii"))
        digest.update(str(len(groups[key])).encode("ascii"))
        for shape in groups[key]:
            digest.update(str(shape.DataCRC(0)).encode("ascii") + b";")
    return digest.hexdigest()


def cache_geometry(groups, cache_id="default", doc=None, *, force=False, palette=None, root=ROOT,
                   plot_weights=None):
    """Synchronize only owned objects, never every object on a layer.

    Identical geometry and palette inputs preserve manual edits and deletions.
    A changed input or force=True replaces this cache's objects. Palette display
    names are part of the fingerprint, so translating them also refreshes owned
    geometry on the next recompute. Cache state is stored in the Rhino document,
    surviving module reloads and saving/reopening a 3dm file.
    Optional plot_weights maps each group to a positive print width in mm;
    these widths are written to object attributes and included in cache state.
    Omitting widths preserves the existing Assignment 1 fingerprint.
    """
    doc = _document(doc)
    palette = _palette(palette)
    cache_id = str(cache_id)
    if not cache_id.strip():
        raise ValueError("cache_id must not be empty.")
    if set(groups) != set(palette):
        raise ValueError("Geometry groups must match the supplied palette.")
    for shapes in groups.values():
        for shape in shapes:
            if shape is None or not shape.IsValid:
                raise ValueError("Invalid geometry cannot be cached.")
    signature = _fingerprint(groups, palette, root)
    if plot_weights is not None:
        import math
        if set(plot_weights) != set(groups):
            raise ValueError("Plot weights must match geometry groups.")
        plot_weights = {key: float(value) for key, value in plot_weights.items()}
        if any(not math.isfinite(value) or value <= 0 for value in plot_weights.values()):
            raise ValueError("Plot weights must be positive finite millimeter values.")
        signature = hashlib.sha256((signature + repr(sorted(plot_weights.items()))).encode("utf-8")).hexdigest()
    owner_id = cache_id if root == ROOT else root + ":" + cache_id
    owned = [obj for obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject)
             if obj.Attributes.GetUserString(OWNER_KEY) == owner_id]
    if not force and doc.Strings.GetValue(STATE_SECTION, owner_id) == signature:
        return [obj.Id for obj in owned]
    if any(obj.IsLocked or obj.IsReference for obj in owned):
        raise RuntimeError("Owned cache objects are locked or referenced; make them editable before updating.")
    undo = doc.BeginUndoRecord("Update CDF composition")
    added = []
    deleted = []
    try:
        indices = ensure_layers(doc, palette=palette, root=root)
        for key in palette:
            for number, shape in enumerate(groups[key], 1):
                attributes = Rhino.DocObjects.ObjectAttributes()
                attributes.LayerIndex = indices[key]
                if plot_weights is not None:
                    attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
                    attributes.PlotWeight = plot_weights[key]
                attributes.Name = "CDF_{}_{:03d}".format(key, number)
                attributes.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer
                attributes.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
                attributes.SetUserString(OWNER_KEY, owner_id)
                attributes.SetUserString(ROOT_KEY, root)
                object_id = doc.Objects.Add(shape, attributes)
                if object_id == Guid.Empty:
                    raise RuntimeError("Rhino could not add a cache object.")
                added.append(object_id)
        # Remove old objects only after every new object was added successfully.
        for obj in owned:
            if not doc.Objects.Delete(obj.Id, True):
                raise RuntimeError("Could not remove an old cache object.")
            deleted.append(obj.RuntimeSerialNumber)
        doc.Strings.SetString(STATE_SECTION, owner_id, signature)
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

