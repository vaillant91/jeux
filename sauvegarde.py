"""Lecture et ecriture des sauvegardes du jeu."""

import json
from pathlib import Path


VERSION_SAUVEGARDE = 1


def _encoder(valeur):
    if isinstance(valeur, tuple):
        return {"__type__": "tuple", "elements": [_encoder(element) for element in valeur]}
    if isinstance(valeur, set):
        return {"__type__": "set", "elements": [_encoder(element) for element in valeur]}
    if isinstance(valeur, dict):
        if any(not isinstance(cle, str) for cle in valeur):
            return {
                "__type__": "dict",
                "elements": [
                    [_encoder(cle), _encoder(element)]
                    for cle, element in valeur.items()
                ],
            }
        return {cle: _encoder(element) for cle, element in valeur.items()}
    if isinstance(valeur, list):
        return [_encoder(element) for element in valeur]
    return valeur


def _decoder(valeur):
    if isinstance(valeur, dict):
        if valeur.get("__type__") == "tuple":
            return tuple(_decoder(element) for element in valeur["elements"])
        if valeur.get("__type__") == "set":
            return set(_decoder(element) for element in valeur["elements"])
        if valeur.get("__type__") == "dict":
            return {
                _decoder(cle): _decoder(element)
                for cle, element in valeur["elements"]
            }
        return {cle: _decoder(element) for cle, element in valeur.items()}
    if isinstance(valeur, list):
        return [_decoder(element) for element in valeur]
    return valeur


def sauvegarder(etat, chemin):
    """Ecrit une sauvegarde complete, en remplacant le fichier atomiquement."""
    chemin = Path(chemin)
    temporaire = chemin.with_suffix(chemin.suffix + ".tmp")
    with temporaire.open("w", encoding="utf-8") as fichier:
        json.dump(
            {"version": VERSION_SAUVEGARDE, "etat": _encoder(etat)},
            fichier,
            ensure_ascii=False,
            indent=2,
        )
    temporaire.replace(chemin)


def charger(chemin):
    """Charge une sauvegarde et refuse les formats inconnus ou incomplets."""
    with Path(chemin).open("r", encoding="utf-8") as fichier:
        donnees = json.load(fichier)
    if not isinstance(donnees, dict) or donnees.get("version") != VERSION_SAUVEGARDE:
        raise ValueError("version de sauvegarde inconnue")
    if "etat" not in donnees or not isinstance(donnees["etat"], dict):
        raise ValueError("fichier de sauvegarde incomplet")
    return _decoder(donnees["etat"])
