import json
from langchain_core.tools import tool
from rooms_data import ROOMS

# Wordt ingesteld vanuit agent.py nadat de vectorstore is opgebouwd
_vectorstore = None


def set_vectorstore(vs) -> None:
    global _vectorstore
    _vectorstore = vs


def _parse_criteria(criteria: str) -> dict:
    """Probeer criteria als JSON te parsen; geef een leeg dict terug bij mislukking."""
    criteria = criteria.strip()
    try:
        return json.loads(criteria)
    except (json.JSONDecodeError, ValueError):
        return {}


@tool
def filter_kamers(criteria: str) -> str:
    """
    Filter hotelkamers op basis van criteria.

    Verwacht een JSON-string met één of meer van de volgende optionele velden:
      - max_prijs (int): maximale prijs per nacht in euro
      - min_prijs (int): minimale prijs per nacht
      - ontbijt (bool): ontbijt inbegrepen?
      - parkeren (bool): parkeren beschikbaar?
      - huisdieren (bool): huisdieren toegestaan?
      - capaciteit (int): minimaal aantal personen
      - locatie (str): gewenste stad of wijk (bijv. "Den Haag" of "Amsterdam")
      - type (str): kamertype (standard / deluxe / suite / family / business / romantisch)
      - query (str): vrije tekstzoekopdracht voor semantisch zoeken

    Voorbeeld: {"max_prijs": 120, "ontbijt": true, "capaciteit": 2}

    Geeft een JSON-lijst van passende kamers terug.
    """
    criteria_dict = _parse_criteria(criteria)
    # Verwijder null-waarden (kleine modellen geven die soms mee)
    criteria_dict = {k: v for k, v in criteria_dict.items() if v is not None}

    # Semantische zoekopdracht via vectorstore (als query meegegeven is)
    if _vectorstore is not None and "query" in criteria_dict:
        from vectorstore import semantic_search
        semantic_ids = {r["id"] for r in semantic_search(_vectorstore, criteria_dict["query"], k=8)}
    else:
        semantic_ids = None

    gefilterd = list(ROOMS)

    if "max_prijs" in criteria_dict:
        gefilterd = [r for r in gefilterd if r["prijs_per_nacht"] <= int(criteria_dict["max_prijs"])]
    if "min_prijs" in criteria_dict:
        gefilterd = [r for r in gefilterd if r["prijs_per_nacht"] >= int(criteria_dict["min_prijs"])]
    # Bool-criteria werken als harde eis bij 'true' en als 'geen voorkeur' bij 'false'
    # (een gast die geen ontbijt hoeft, vindt een kamer mét ontbijt ook prima)
    if criteria_dict.get("ontbijt"):
        gefilterd = [r for r in gefilterd if r["ontbijt"]]
    if criteria_dict.get("parkeren"):
        gefilterd = [r for r in gefilterd if r["parkeren"]]
    if criteria_dict.get("huisdieren"):
        gefilterd = [r for r in gefilterd if r["huisdieren"]]
    if "capaciteit" in criteria_dict:
        gewenst = int(criteria_dict["capaciteit"])
        gefilterd = [r for r in gefilterd if r["capaciteit"] >= gewenst]
    if "locatie" in criteria_dict:
        zoekterm = criteria_dict["locatie"].lower()
        gefilterd = [r for r in gefilterd if zoekterm in r["locatie"].lower()]
    if "type" in criteria_dict:
        zoekterm = criteria_dict["type"].lower()
        gefilterd = [r for r in gefilterd if zoekterm in r["type"].lower()]

    # Pas semantische filtering toe als query was opgegeven
    if semantic_ids is not None:
        semantisch_gefilterd = [r for r in gefilterd if r["id"] in semantic_ids]
        # Gebruik semantisch resultaat als het niet leeg is; anders fallback op structureel gefilterd
        gefilterd = semantisch_gefilterd if semantisch_gefilterd else gefilterd

    if not gefilterd:
        return (
            "Geen kamers gevonden met deze criteria. "
            "Overweeg het budget te verhogen of andere filters te verruimen."
        )

    return json.dumps(gefilterd[:10], ensure_ascii=False, indent=2)


@tool
def rangschik_kamers(kamers_json: str) -> str:
    """
    Rangschik een lijst kamers op prijs (laag naar hoog) en geef de top 3 terug
    als een leesbaar overzicht.

    Verwacht een JSON-array van kamers (output van filter_kamers).
    Geeft een geformatteerde tekst terug met de top 3 aanbevelingen.
    """
    try:
        kamers = json.loads(kamers_json)
    except (json.JSONDecodeError, TypeError, ValueError):
        return "Fout: kon de kamerlijst niet verwerken. Zorg voor een geldige JSON-array."

    if not kamers:
        return "Geen kamers beschikbaar om te rangschikken."

    # Sorteer op prijs (laag naar hoog), dan op capaciteit (hoog naar laag)
    gesorteerd = sorted(kamers, key=lambda k: (k.get("prijs_per_nacht", 9999), -k.get("capaciteit", 0)))
    top3 = gesorteerd[:3]

    regels = ["Top 3 aanbevolen kamers:\n"]
    for i, kamer in enumerate(top3, 1):
        regels.append("-" * 42)
        regels.append(f"{i}. {kamer['naam']}")
        regels.append(f"   Locatie   : {kamer['locatie']}")
        regels.append(f"   Prijs     : EUR {kamer['prijs_per_nacht']}/nacht")
        regels.append(f"   Capaciteit: {kamer['capaciteit']} persoon/personen")
        regels.append(f"   Ontbijt   : {'Inbegrepen' if kamer['ontbijt'] else 'Niet inbegrepen'}")
        regels.append(f"   Parkeren  : {'Beschikbaar' if kamer['parkeren'] else 'Niet beschikbaar'}")
        regels.append(f"   Huisdieren: {'Welkom' if kamer['huisdieren'] else 'Niet toegestaan'}")
        regels.append(f"   Info      : {kamer.get('beschrijving', '')[:120]}...")
        regels.append("")

    return "\n".join(regels)


@tool
def valideer_aanbeveling(aanbeveling: str) -> str:
    """
    Valideer of een kameraanbeveling volledig en logisch is voordat die aan de gast getoond wordt.

    Accepteert een JSON-string van één kamer of de ruwe output van rangschik_kamers.
    Controleert op verplichte velden en logische consistentie.

    Geeft '✓ Geldig' terug als de aanbeveling correct is, anders een foutmelding.
    """
    # Probeer als JSON te parsen
    aanbeveling = aanbeveling.strip()
    try:
        if aanbeveling.startswith("["):
            kamers = json.loads(aanbeveling)
            kamer = kamers[0] if kamers else {}
        elif aanbeveling.startswith("{"):
            kamer = json.loads(aanbeveling)
        else:
            # Tekst-output (bijv. van rangschik_kamers) — basiscontrole
            if "EUR" in aanbeveling and any(t in aanbeveling for t in ["kamer", "suite", "Kamer", "Suite"]):
                return "[OK] Aanbeveling bevat prijs en kamertype — tekst-output goedgekeurd voor presentatie."
            return "[LET OP] Aanbeveling is in tekstformaat maar mist prijs of kamertype. Controleer de output."
    except (json.JSONDecodeError, ValueError, IndexError):
        return "[LET OP] Kon aanbeveling niet verwerken als JSON. Controleer het formaat."

    verplichte_velden = ["naam", "prijs_per_nacht", "type", "locatie", "capaciteit"]
    ontbrekend = [v for v in verplichte_velden if v not in kamer]

    if ontbrekend:
        return f"[FOUT] Onvolledige aanbeveling. Ontbrekende velden: {', '.join(ontbrekend)}"

    # Logische controles
    waarschuwingen = []
    if kamer.get("prijs_per_nacht", 0) <= 0:
        waarschuwingen.append("prijs is nul of negatief")
    if kamer.get("capaciteit", 0) <= 0:
        waarschuwingen.append("capaciteit is nul of negatief")

    if waarschuwingen:
        return f"[LET OP] Aanbeveling deels ongeldig: {'; '.join(waarschuwingen)}"

    return (
        f"[OK] Aanbeveling geldig: '{kamer['naam']}' "
        f"(EUR {kamer['prijs_per_nacht']}/nacht, {kamer['capaciteit']} pers.) "
        f"in {kamer['locatie']}."
    )
