"""Material-Layer und persistenter, komponentenbezogener Rhino-Geometriecache."""

import hashlib

import Rhino
from System import Guid
from System.Drawing import Color


# RGB, Glanz (0–255), Reflexion (0–1): warmes Elfenbein und matte Primärfarben.
PALETTE = {
    "white": ("01_Elfenbein", (226, 212, 192), 22.0, 0.02),
    "black": ("02_Anthrazit", (37, 38, 36), 18.0, 0.01),
    "blue": ("03_Ultramarin", (6, 38, 145), 0.0, 0.0),
    "red": ("04_Zinnoberrot", (228, 12, 18), 0.0, 0.0),
    "yellow": ("05_Sonnengelb", (255, 190, 5), 0.0, 0.0),
}
ROOT = "CDF_Bildkomposition"
OWNER_KEY = "cdf.composition.owner"
STATE_SECTION = "cdf.composition.cache.v1"


def _document(doc):
    doc = Rhino.RhinoDoc.ActiveDoc if doc is None else doc
    if doc is None:
        raise RuntimeError("Kein aktives Rhino-Dokument vorhanden.")
    return doc


def ensure_layers(doc=None):
    """Erzeuge eigene Layer/Materialien; fremde Layer werden nicht verändert."""
    doc = _document(doc)
    root_index = doc.Layers.FindByFullPath(ROOT, -1)
    if root_index < 0:
        parent = Rhino.DocObjects.Layer()
        parent.Name = ROOT
        root_index = doc.Layers.Add(parent)
    if root_index < 0:
        raise RuntimeError("CDF-Hauptlayer konnte nicht angelegt werden.")
    parent_id = doc.Layers[root_index].Id
    indices = {}
    for key, (name, rgb, shine, reflection) in PALETTE.items():
        material_name = ROOT + "_" + name
        material_index = doc.Materials.Find(material_name, True)
        if material_index < 0:
            material_index = doc.Materials.Add()
        if material_index < 0:
            raise RuntimeError("Material konnte nicht angelegt werden: " + name)
        material = doc.Materials[material_index]
        material.Name = material_name
        material.DiffuseColor = Color.FromArgb(*rgb)
        specular = 0 if key in ("blue", "red", "yellow") else 240
        material.SpecularColor = Color.FromArgb(specular, specular, specular)
        material.Shine = shine
        material.Reflectivity = reflection
        material.Transparency = 0.0
        if not material.CommitChanges():
            raise RuntimeError("Material konnte nicht gespeichert werden: " + name)
        index = doc.Layers.FindByFullPath(ROOT + "::" + name, -1)
        if index < 0:
            item = Rhino.DocObjects.Layer()
            item.Name = name
            item.ParentLayerId = parent_id
            index = doc.Layers.Add(item)
        if index < 0:
            raise RuntimeError("Materiallayer konnte nicht angelegt werden: " + name)
        item = doc.Layers[index]
        # Rhino 6+: Layeränderungen sind sofort wirksam; CommitChanges() liefert False.
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
    """Synchronisiere nur eigene Objekte, nie alle Objekte auf einem Layer.

    Identische Eingabe lässt manuelle Änderungen und Löschungen bestehen.
    Neue Eingabe ersetzt die eigenen Objekte. force=True setzt Bearbeitungen
    ausdrücklich zurück. Der Zustand liegt im Rhino-Dokument, nicht im Modul,
    und übersteht daher Reloads und das Speichern/Öffnen einer 3dm-Datei.
    """
    doc = _document(doc)
    cache_id = str(cache_id)
    if not cache_id.strip():
        raise ValueError("cache_id darf nicht leer sein.")
    if set(groups) != set(PALETTE):
        raise ValueError("Es werden genau die fünf definierten Farbgruppen benötigt.")
    for shapes in groups.values():
        for shape in shapes:
            if shape is None or not shape.IsValid:
                raise ValueError("Ungültige Geometrie kann nicht gecached werden.")
    signature = _fingerprint(groups)
    owned = [obj for obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject)
             if obj.Attributes.GetUserString(OWNER_KEY) == cache_id]
    if not force and doc.Strings.GetValue(STATE_SECTION, cache_id) == signature:
        return [obj.Id for obj in owned]
    if any(obj.IsLocked or obj.IsReference for obj in owned):
        raise RuntimeError("Eigene Cache-Objekte sind gesperrt/referenziert; vor Aktualisierung entsperren.")
    undo = doc.BeginUndoRecord("CDF Bildkomposition aktualisieren")
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
                    raise RuntimeError("Rhino konnte ein Cache-Objekt nicht hinzufügen.")
                added.append(object_id)
        # Erst nach erfolgreichem Hinzufügen aller neuen Objekte alte entfernen.
        for obj in owned:
            if not doc.Objects.Delete(obj.Id, True):
                raise RuntimeError("Altes Cache-Objekt konnte nicht entfernt werden.")
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
