from typing import Dict, List, Optional

# Données statiques génériques (non exhaustives, non sensibles aux mises à jour)
BAC_TRACKS = [
    "Sciences Math A", "Sciences Math B", "Sciences Physiques",
    "Sciences de la Vie et de la Terre", "Sciences et Technologies",
    "Économie et Gestion", "Lettres et Sciences Humaines", "Arts Appliqués"
]

FIELDS = [
    "Ingénierie & Informatique", "Commerce & Gestion", "Médecine & Santé",
    "Sciences Fondamentales", "Droit & Sciences Politiques",
    "Langues, Communication & Journalisme", "Design & Arts",
    "Agronomie & Environnement", "Technologie (EST/DUT)", "Formation Professionnelle"
]

# Mapping heuristique filière bac -> domaines probables
TRACK_TO_FIELDS = {
    "Sciences Math A": ["Ingénierie & Informatique", "Sciences Fondamentales", "Technologie (EST/DUT)"],
    "Sciences Math B": ["Ingénierie & Informatique", "Sciences Fondamentales", "Technologie (EST/DUT)"],
    "Sciences Physiques": ["Ingénierie & Informatique", "Médecine & Santé", "Sciences Fondamentales", "Technologie (EST/DUT)"],
    "Sciences de la Vie et de la Terre": ["Médecine & Santé", "Agronomie & Environnement", "Sciences Fondamentales"],
    "Sciences et Technologies": ["Technologie (EST/DUT)", "Ingénierie & Informatique", "Commerce & Gestion"],
    "Économie et Gestion": ["Commerce & Gestion", "Droit & Sciences Politiques", "Technologie (EST/DUT)"],
    "Lettres et Sciences Humaines": ["Droit & Sciences Politiques", "Langues, Communication & Journalisme", "Design & Arts"],
    "Arts Appliqués": ["Design & Arts", "Langues, Communication & Journalisme"]
}

# Exemples d'établissements (catégories génériques)
CATEGORIES_ECOLES = {
    "Ingénierie & Informatique": ["ENSA", "ENSAM", "EMI", "ENSIAS", "INPT", "EHTP", "FST (licence sciences et techniques)"],
    "Commerce & Gestion": ["ENCG", "ISCAE", "Facultés Éco/Gestion"],
    "Médecine & Santé": ["FMP (Facultés de Médecine et de Pharmacie)", "IFCS (Instituts de formation en soins)"],
    "Sciences Fondamentales": ["Facultés des Sciences", "FST"],
    "Droit & Sciences Politiques": ["Facultés de Droit", "Instituts d'études politiques (équivalents locaux si applicable)"],
    "Langues, Communication & Journalisme": ["Facultés Lettres/Langues", "Instituts de Communication/Journalisme"],
    "Design & Arts": ["Écoles d’arts/design", "Facultés Arts"],
    "Agronomie & Environnement": ["IAV Hassan II", "ENA/ENAM (selon filières)"],
    "Technologie (EST/DUT)": ["EST (Écoles Supérieures de Technologie)"],
    "Formation Professionnelle": ["OFPPT (Technicien/TS), Instituts spécialisés"]
}

def grade_band(avg: float) -> str:
    if avg >= 16: return "Excellent"
    if avg >= 14: return "Très Bien"
    if avg >= 12: return "Bien"
    if avg >= 10: return "Passable"
    return "À renforcer"

def build_profile_summary(profile: Dict) -> str:
    p = profile or {}
    parts = []
    if p.get("name"):
        parts.append(f"Nom: {p['name']}")
    if p.get("track"):
        parts.append(f"Filière: {p['track']}")
    if p.get("city"):
        parts.append(f"Ville: {p['city']}")
    if p.get("avg"):
        parts.append(f"Moyenne: {p['avg']} ({grade_band(float(p['avg']))})")
    subj = p.get("subjects", {})
    if subj:
        subparts = []
        for k,v in subj.items():
            if v:
                subparts.append(f"{k}: {v}")
        if subparts:
            parts.append("Notes matières: " + ", ".join(subparts))
    prefs = p.get("interests", [])
    if prefs:
        parts.append("Intérêts: " + ", ".join(prefs))
    langs = p.get("languages", [])
    if langs:
        parts.append("Langues: " + ", ".join(langs))
    budget = p.get("budget")
    if budget:
        parts.append(f"Budget: {budget}")
    mobility = p.get("mobility")
    if mobility:
        parts.append(f"Mobilité: {mobility}")
    constraints = p.get("constraints")
    if constraints:
        parts.append(f"Contraintes: {constraints}")
    return " | ".join(parts)

def suggested_fields_for_track(track: str) -> List[str]:
    return TRACK_TO_FIELDS.get(track, [])

def month_timeline_generic() -> List[str]:
    # Timeline générique Maroc (indicative, à vérifier chaque année)
    return [
        "Avril-Mai: Préparation aux examens, affiner le projet d'orientation.",
        "Juin: Épreuves du bac, veille sur préinscriptions/concours.",
        "Juin-Juillet: Préinscriptions en ligne / dépôts de dossiers (selon établissements).",
        "Juillet: Concours/entretiens pour écoles sélectives.",
        "Fin Juillet-Août: Résultats d’admission, choix définitifs.",
        "Septembre: Inscriptions administratives et rentrée."
    ]