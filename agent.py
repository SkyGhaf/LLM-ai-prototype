"""
Hotel Kamer Aanbeveling Agent — kern van de workflow.

Architectuur: Python orkestreert de vaste 6-staps workflow (state machine),
het LLM (llama3.2:1b via Ollama) interpreteert vrije tekst van de gast en
de LangChain tools voeren het filteren, rangschikken en valideren uit.

Deze opzet is bewust gekozen: kleine lokale modellen (1B) zijn onbetrouwbaar
in een vrije tool-calling loop, maar uitstekend in tekstbegrip. De orchestratie
(meetcriterium C2) ligt daarom in Python, de taalvaardigheid bij het LLM.
"""

import json
import logging
import re

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

import tools as tools_module
from tools import filter_kamers, rangschik_kamers, valideer_aanbeveling
from vectorstore import get_or_build_vectorstore
from rooms_data import ROOMS

logger = logging.getLogger("hotel_agent")

EXTRACT_PROMPT = """Je leest een bericht van een hotelgast. Haal de zoekcriteria eruit.
Antwoord ALLEEN met een JSON-object, geen andere tekst. Mogelijke velden:
- max_prijs (getal, euro per nacht)
- ontbijt (true/false)
- parkeren (true/false)
- huisdieren (true/false)
- capaciteit (getal, aantal personen)
- locatie (string, stad)

Alleen velden opnemen die de gast echt noemt. Niets genoemd? Antwoord: {}

Voorbeelden:
Bericht: "ik zoek iets voor 2 personen onder de 100 euro" -> {"capaciteit": 2, "max_prijs": 100}
Bericht: "met ontbijt graag, in Den Haag" -> {"ontbijt": true, "locatie": "Den Haag"}
Bericht: "hallo" -> {}"""

# Vaste vragen voor stap 2 — telkens één veld dat nog onbekend is
VRAGEN = [
    ("capaciteit", "Voor hoeveel personen zoekt u een kamer?"),
    ("max_prijs", "Wat is uw maximale budget per nacht (in euro)?"),
    ("ontbijt", "Wilt u ontbijt inbegrepen? (ja/nee)"),
    ("parkeren", "Heeft u een parkeerplaats nodig? (ja/nee)"),
    ("locatie", "Heeft u een voorkeurslocatie? (bijv. Den Haag, Amsterdam, of 'geen voorkeur')"),
]

JA_WOORDEN = ("ja", "j", "yes", "graag", "zeker", "jazeker", "jawel", "yep")
NEE_WOORDEN = ("nee", "n", "no", "niet", "nope", "geen")

# Geschreven getallen, zodat "voor vier personen" ook begrepen wordt
WOORD_GETALLEN = {
    "één": 1, "een persoon": 1, "twee": 2, "drie": 3, "vier": 4,
    "vijf": 5, "zes": 6, "zeven": 7, "acht": 8, "negen": 9, "tien": 10,
}

# Signalen dat de gast een vrije vraag stelt i.p.v. een antwoord geeft
VRAAG_SIGNALEN = (
    "kan ik", "kunnen we", "kunnen wij", "kun je", "kunt u", "mag ik",
    "mogen we", "mogen wij", "is er", "zijn er", "hebben jullie",
    "heeft het hotel", "is het mogelijk", "hoe laat", "hoe werkt",
    "wat kost", "wat is er", "waar is", "waar ligt", "welke",
)

# Systeem-prompt voor vrije vragen: het LLM antwoordt op basis van
# hotelcontext (RAG) en algemene Van der Valk-informatie
ANTWOORD_PROMPT = """Je bent de digitale kamerassistent van Van der Valk Hotels.
Beantwoord de vraag van de gast kort, vriendelijk en in het Nederlands (maximaal 4 zinnen).
Gebruik alleen de informatie hieronder; verzin geen prijzen of faciliteiten die er niet staan.

Algemene informatie Van der Valk:
- Gasten kunnen meerdere kamers tegelijk boeken, bijvoorbeeld 2 kamers om een groep of gezin te splitsen.
- Inchecken kan vanaf 15:00 uur, uitchecken tot 12:00 uur.
- Het ontbijt is een uitgebreid Live Cooking buffet.
- Alle hotels hebben een restaurant; veel locaties hebben wellness, zwembad en fitness.
- Parkeren is bij vrijwel alle hotels gratis.
- Reserveren kan via deze chat, telefonisch of aan de balie.

{context}"""

# Bekende plaatsnamen, automatisch afgeleid uit de kamerdataset zodat
# nieuwe hotels direct herkend worden. Langste namen eerst, zodat
# "den haag" matcht vóór een kortere deelnaam.
def _afgeleide_locaties() -> tuple:
    locaties = set()
    for room in ROOMS:
        loc = room["locatie"].lower()
        locaties.add(loc)
        for deel in re.split(r"[-/]| bij | op de ", loc):
            deel = deel.strip()
            if len(deel) >= 4:
                locaties.add(deel)
    return tuple(sorted(locaties, key=len, reverse=True))


BEKENDE_LOCATIES = _afgeleide_locaties()

# Wens-signalen: bij deze woorden wordt het hele bericht als semantische
# zoekopdracht (query) meegegeven aan filter_kamers, zodat de vectorstore
# kamers kan aanbevelen op sfeer/kenmerken i.p.v. alleen harde filters
WENS_WOORDEN = (
    "uitzicht", "romantisch", "luxe", "rustig", "rust", "natuur", "strand",
    "zee", "water", "bos", "sauna", "zwembad", "wellness", "spa",
    "skybar", "kasteel", "centrum", "modern", "sfeervol", "polder",
    "dierentuin", "pretpark", "efteling", "gezellig", "bijzonder", "mooi",
)


class HotelAgent:
    """Doorloopt de 6-staps workflow: begroeting -> vragen -> samenvatting ->
    zoeken -> tonen -> feedbackloop."""

    def __init__(self):
        self.vectorstore = get_or_build_vectorstore(ROOMS)
        tools_module.set_vectorstore(self.vectorstore)
        self.llm = ChatOllama(model="llama3.2:1b", temperature=0.1)

        # Sessiememorie (meetcriterium C3): criteria en fase blijven bewaard
        self.criteria: dict = {}
        self.fase = "begroeting"
        self.vraag_index = 0
        self.laatste_resultaat: str | None = None

    # ---------- LLM-hulpfuncties ----------

    def _extraheer_criteria(self, tekst: str) -> dict:
        """Laat het LLM zoekcriteria uit vrije tekst halen (stap 2/6)."""
        logger.info(f"LLM-extractie gestart voor: {tekst!r}")
        try:
            response = self.llm.invoke([
                SystemMessage(content=EXTRACT_PROMPT),
                HumanMessage(content=f'Bericht: "{tekst}"'),
            ])
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            criteria = json.loads(match.group()) if match else {}
            if not isinstance(criteria, dict):
                return {}
            criteria = self._valideer_extractie(criteria, tekst)
            logger.info(f"LLM-extractie resultaat (gevalideerd): {criteria}")
            return criteria
        except Exception as exc:
            logger.warning(f"LLM-extractie mislukt ({exc}), fallback op regelparser")
            return {}

    @staticmethod
    def _valideer_extractie(criteria: dict, tekst: str) -> dict:
        """Kleine modellen verzinnen soms velden — accepteer alleen velden
        waarvoor daadwerkelijk een aanwijzing in de gasttekst staat."""
        lower = tekst.lower()
        bewijs = {
            "ontbijt": ("ontbijt",),
            "parkeren": ("parkeer", "parking", "auto"),
            "huisdieren": ("huisdier", "hond", "kat", "dier"),
            "max_prijs": ("euro", "budget", "prijs", "eur", "goedkoop", "duur") ,
            "capaciteit": ("persoon", "personen", "mensen", "man", "z'n", "alleen"),
            "locatie": (),  # aparte controle hieronder
        }
        gevalideerd = {}
        for veld, waarde in criteria.items():
            if waarde is None or veld not in bewijs:
                continue
            if veld == "locatie":
                # Locatie alleen accepteren als het een bekende plaats is
                # die ook echt in de gasttekst voorkomt
                if isinstance(waarde, str) and len(waarde) >= 3 and waarde.lower() in lower:
                    loc = HotelAgent._herken_locatie(waarde)
                    if loc:
                        gevalideerd[veld] = loc
                continue
            if veld in ("max_prijs", "capaciteit"):
                # Getalwaarde moet letterlijk in de tekst staan (1B modellen
                # lezen getallen soms verkeerd) en binnen logische grenzen vallen
                try:
                    getal = int(waarde)
                    ondergrens, bovengrens = (1, 10) if veld == "capaciteit" else (20, 2000)
                    if HotelAgent._getal_in_tekst(getal, tekst) and ondergrens <= getal <= bovengrens:
                        gevalideerd[veld] = getal
                except (ValueError, TypeError):
                    pass
                continue
            if any(w in lower for w in bewijs[veld]):
                gevalideerd[veld] = waarde
        return gevalideerd

    def _vang_wensen(self, tekst: str) -> bool:
        """Herken sfeer-/kenmerkwensen ('mooi uitzicht', 'romantisch') en sla
        alleen de wenswoorden op als semantische zoekopdracht — de hele zin
        meegeven verwatert de zoekresultaten. Wensen stapelen over beurten."""
        lower = tekst.lower()
        gevonden = [w for w in WENS_WOORDEN if re.search(rf"\b{w}", lower)]
        if not gevonden:
            return False
        bestaand = self.criteria.get("query", "").split()
        woorden = bestaand + [w for w in gevonden if w not in bestaand]
        self.criteria["query"] = " ".join(woorden)
        logger.info(f"Wens vastgelegd als semantische query: {self.criteria['query']!r}")
        return True

    # ---------- Vrije vragen (LLM + RAG) ----------

    @staticmethod
    def _is_vraag(tekst: str) -> bool:
        """Herken of de gast een vrije vraag stelt in plaats van een antwoord geeft."""
        lower = tekst.lower()
        if "?" in tekst:
            return True
        return any(signaal in lower for signaal in VRAAG_SIGNALEN)

    def _beantwoord_vraag(self, tekst: str) -> str:
        """Beantwoord een vrije vraag van de gast via het LLM, met relevante
        kamerinformatie uit de vectorstore als context (RAG)."""
        logger.info(f"Vrije vraag gedetecteerd: {tekst!r}")
        try:
            from vectorstore import semantic_search
            relevant = semantic_search(self.vectorstore, tekst, k=3)
            regels = []
            for kamer in relevant:
                regels.append(
                    f"- {kamer['naam']} ({kamer['locatie']}): EUR {kamer['prijs_per_nacht']}/nacht, "
                    f"max {kamer['capaciteit']} pers., "
                    f"ontbijt {'inbegrepen' if kamer['ontbijt'] else 'niet inbegrepen'}, "
                    f"parkeren {'gratis' if kamer['parkeren'] else 'niet beschikbaar'}, "
                    f"huisdieren {'welkom' if kamer['huisdieren'] else 'niet toegestaan'}"
                )
            context = "Relevante kamers uit ons aanbod:\n" + "\n".join(regels)
            if self.criteria:
                context += f"\n\nReeds genoteerde wensen van deze gast: {self._samenvatting()}."

            response = self.llm.invoke([
                SystemMessage(content=ANTWOORD_PROMPT.format(context=context)),
                HumanMessage(content=tekst),
            ])
            antwoord = response.content.strip()
            logger.info(f"LLM-antwoord op vrije vraag: {antwoord[:120]}")
            return antwoord
        except Exception as exc:
            logger.warning(f"Vrije-vraagbeantwoording mislukt: {exc}")
            return (
                "Dat kan ik zo niet beantwoorden, maar onze receptie helpt u graag verder. "
            )

    # ---------- Regelgebaseerde parsers (fallback + ja/nee) ----------

    @staticmethod
    def _parse_ja_nee(tekst: str) -> bool | None:
        woorden = tekst.lower().split()
        if any(w.strip(",.!?") in JA_WOORDEN for w in woorden):
            return True
        if any(w.strip(",.!?") in NEE_WOORDEN for w in woorden):
            return False
        return None

    @staticmethod
    def _parse_getal(tekst: str) -> int | None:
        match = re.search(r"\d+", tekst)
        if match:
            return int(match.group())
        # Geschreven getallen ("voor vier personen")
        lower = tekst.lower()
        for woord, getal in WOORD_GETALLEN.items():
            if woord in lower:
                return getal
        return None

    @staticmethod
    def _getal_in_tekst(getal: int, tekst: str) -> bool:
        """Controleer of een getal letterlijk (als cijfer of woord) in de tekst staat."""
        if re.search(rf"\b{getal}\b", tekst):
            return True
        lower = tekst.lower()
        return any(w in lower for w, g in WOORD_GETALLEN.items() if g == getal)

    @staticmethod
    def _herken_locatie(tekst: str) -> str | None:
        """Herken een plaatsnaam uit de dataset in de tekst."""
        lower = tekst.lower()
        for loc in BEKENDE_LOCATIES:
            if loc in lower:
                return loc.title()
        return None

    def _verwerk_antwoord(self, veld: str, tekst: str) -> None:
        """Sla het antwoord op de huidige vraag op in de sessiememorie."""
        lower = tekst.lower()
        if veld in ("ontbijt", "parkeren", "huisdieren"):
            waarde = self._parse_ja_nee(tekst)
            if waarde is not None:
                self.criteria[veld] = waarde
            else:
                # Gast noemt een bedrag bij een ja/nee-vraag? Bewaar het als budget.
                getal = self._parse_getal(tekst)
                if getal and 20 <= getal <= 2000 and ("euro" in lower or "eur" in lower):
                    self.criteria.setdefault("max_prijs", getal)
        elif veld == "capaciteit":
            waarde = self._parse_getal(tekst)
            # Gast noemt een bedrag bij de personenvraag? Sla het op als budget.
            if waarde is not None and ("euro" in lower or "eur" in lower or waarde > 10):
                if 20 <= waarde <= 2000:
                    self.criteria.setdefault("max_prijs", waarde)
            elif waarde is not None and 1 <= waarde <= 10:
                self.criteria["capaciteit"] = waarde
        elif veld == "max_prijs":
            waarde = self._parse_getal(tekst)
            if waarde is not None and 20 <= waarde <= 2000:
                self.criteria["max_prijs"] = waarde
        elif veld == "locatie":
            # Alleen bekende plaatsnamen accepteren — voorkomt dat 'ja' of
            # ander los antwoord als locatie wordt opgeslagen
            loc = self._herken_locatie(tekst)
            if loc:
                self.criteria["locatie"] = loc
        # Veld blijft leeg bij onduidelijk antwoord; gast kan het later alsnog noemen

    # ---------- Workflowstappen ----------

    def _volgende_vraag(self) -> str | None:
        """Zoek de eerstvolgende vraag waarvan het veld nog onbekend is."""
        while self.vraag_index < len(VRAGEN):
            veld, vraag = VRAGEN[self.vraag_index]
            if veld not in self.criteria:
                return vraag
            self.vraag_index += 1
        return None

    def _samenvatting(self) -> str:
        delen = []
        if "capaciteit" in self.criteria:
            delen.append(f"{self.criteria['capaciteit']} persoon/personen")
        if "max_prijs" in self.criteria:
            delen.append(f"max EUR {self.criteria['max_prijs']}/nacht")
        if "ontbijt" in self.criteria:
            delen.append("met ontbijt" if self.criteria["ontbijt"] else "zonder ontbijt")
        if "parkeren" in self.criteria:
            delen.append("met parkeerplaats" if self.criteria["parkeren"] else "geen parkeerplaats nodig")
        if "huisdieren" in self.criteria:
            delen.append("huisdieren mee" if self.criteria["huisdieren"] else "geen huisdieren")
        if "locatie" in self.criteria:
            delen.append(f"in {self.criteria['locatie']}")
        if "query" in self.criteria:
            delen.append(f"speciale wens: '{self.criteria['query']}'")
        return ", ".join(delen) if delen else "geen specifieke wensen"

    def _zoek_en_toon(self) -> str:
        """Stappen 4 en 5: filter_kamers -> rangschik_kamers -> valideer_aanbeveling."""
        criteria_json = json.dumps(self.criteria, ensure_ascii=False)
        logger.info(f"TOOL filter_kamers aangeroepen met: {criteria_json}")
        gevonden = filter_kamers.invoke(criteria_json)

        if gevonden.startswith("Geen kamers"):
            logger.info("filter_kamers: geen resultaten")
            return (
                f"{gevonden}\n\n"
                "U kunt bijvoorbeeld zeggen: 'verhoog mijn budget naar 150' of 'ontbijt hoeft niet'."
            )

        logger.info("TOOL rangschik_kamers aangeroepen")
        top3 = rangschik_kamers.invoke(gevonden)

        logger.info("TOOL valideer_aanbeveling aangeroepen")
        validatie = valideer_aanbeveling.invoke(gevonden)
        logger.info(f"Validatie-uitkomst: {validatie}")

        if validatie.startswith("[FOUT]"):
            return f"Er ging iets mis bij het valideren van de aanbeveling: {validatie}"

        self.laatste_resultaat = top3
        return (
            f"Op basis van uw wensen ({self._samenvatting()}):\n\n{top3}\n"
            f"Validatie: {validatie}\n\n"
            "Bent u tevreden met deze aanbevelingen? "
            "Of wilt u iets aanpassen (bijv. 'te duur', 'liever met ontbijt')?"
        )

    # ---------- Hoofdverwerking per gespreksbeurt ----------

    def reageer(self, tekst: str) -> str:
        logger.info(f"Fase: {self.fase} | Criteria: {self.criteria}")

        # Sfeerwensen ('mooi uitzicht') in elke fase opvangen voor semantisch zoeken
        wens_gevonden = self._vang_wensen(tekst)

        # Stap 1 — Begroeting: pak meteen criteria mee die de gast al noemt
        if self.fase == "begroeting":
            self.criteria.update(self._extraheer_criteria(tekst))
            self.fase = "vragen"
            vraag = self._volgende_vraag()
            begroeting = "Welkom bij Van der Valk! Wat fijn dat u bij ons een kamer zoekt. "
            # Stelt de gast meteen een vraag? Beantwoord die eerst.
            if self._is_vraag(tekst):
                begroeting = self._beantwoord_vraag(tekst) + "\n\n"
            elif self.criteria:
                begroeting += f"Ik heb genoteerd: {self._samenvatting()}. "
            if vraag:
                return begroeting + vraag
            self.fase = "zoeken"
            return begroeting + self._zoek_en_toon_overgang()

        # Stap 2 — Vragenronde: huidige vraag verwerken, volgende stellen
        if self.fase == "vragen":
            veld, _ = VRAGEN[self.vraag_index]
            # Vrije vraag van de gast? Beantwoord die en herhaal daarna onze vraag.
            if self._is_vraag(tekst):
                antwoord = self._beantwoord_vraag(tekst)
                # Criteria die de gast in de vraag noemt wel meenemen
                self.criteria.update({
                    k: v for k, v in self._extraheer_criteria(tekst).items()
                    if k not in self.criteria
                })
                vervolg = self._volgende_vraag()
                if vervolg:
                    return f"{antwoord}\n\nOm verder te zoeken: {vervolg}"
                return antwoord + "\n\n" + self._zoek_en_toon_overgang()
            self._verwerk_antwoord(veld, tekst)
            # LLM-extractie als de gast meer noemt dan alleen het antwoord
            if len(tekst.split()) > 3:
                extra = self._extraheer_criteria(tekst)
                extra.pop(veld, None) if veld in self.criteria else None
                self.criteria.update({k: v for k, v in extra.items() if k not in self.criteria})
            self.vraag_index += 1
            vraag = self._volgende_vraag()
            if vraag:
                return vraag
            return self._zoek_en_toon_overgang()

        # Stap 6 — Feedbackloop: wensen bijstellen en opnieuw zoeken
        if self.fase == "feedback":
            lower = tekst.lower()
            # Vrije vraag over de aanbevelingen of het hotel? Beantwoord die.
            if self._is_vraag(tekst):
                antwoord = self._beantwoord_vraag(tekst)
                return (
                    f"{antwoord}\n\n"
                    "Wilt u verder nog iets aanpassen aan uw zoekopdracht, of bent u tevreden?"
                )
            if any(w in lower for w in ("tevreden", "prima", "goed zo", "perfect", "top", "bedankt", "boek")):
                logger.info("Gast tevreden — workflow afgerond")
                return (
                    "Wat fijn! U kunt de kamer aan de balie of telefonisch reserveren. "
                    "Nog een prettige dag en graag tot ziens!"
                )

            aanpassing = self._extraheer_criteria(tekst)
            filter_verwijderd = False

            # 'Geen voorkeur' / 'maakt niet uit' → laat het locatiefilter los
            if any(w in lower for w in ("geen voorkeur", "maakt niet uit", "overal", "alle locaties")):
                if "locatie" in self.criteria:
                    del self.criteria["locatie"]
                    filter_verwijderd = True
                    logger.info("FEEDBACKLOOP: locatiefilter verwijderd")

            # Noemt de gast een andere plaats? Pas de locatie aan.
            loc = self._herken_locatie(tekst)
            if loc:
                aanpassing["locatie"] = loc

            # Regelgebaseerde aanvulling voor veelvoorkomende feedback
            # Noemt de gast een concreet bedrag? Gebruik dat dan letterlijk.
            getal = self._parse_getal(tekst)
            if getal and 20 <= getal <= 2000 and any(
                w in lower for w in ("duur", "goedkoper", "onder", "max", "budget", "euro", "prijs")
            ):
                aanpassing["max_prijs"] = getal
            elif "te duur" in lower or "goedkoper" in lower:
                huidig = self.criteria.get("max_prijs", 200)
                aanpassing.setdefault("max_prijs", int(huidig * 0.8))
            if "ontbijt" in lower and "max_prijs" not in aanpassing:
                ja_nee = self._parse_ja_nee(lower)
                if ja_nee is not None:
                    aanpassing.setdefault("ontbijt", ja_nee)

            if aanpassing or filter_verwijderd or wens_gevonden:
                if aanpassing:
                    logger.info(f"FEEDBACKLOOP: criteria bijgesteld met {aanpassing}")
                    self.criteria.update(aanpassing)
                return "Ik pas uw wensen aan en zoek opnieuw...\n\n" + self._zoek_en_toon()

            # Geen herkenbare aanpassing — laat het LLM vrij reageren
            antwoord = self._beantwoord_vraag(tekst)
            return (
                f"{antwoord}\n\n"
                "U kunt uw zoekopdracht ook aanpassen, bijvoorbeeld: "
                "'maximaal 100 euro' of 'liever in Amsterdam'."
            )

        # Vangnet — zou niet moeten gebeuren
        return "Kunt u dat anders formuleren?"

    def _zoek_en_toon_overgang(self) -> str:
        """Stap 3 (samenvatting) + 4/5, daarna door naar de feedbackfase."""
        self.fase = "feedback"
        intro = f"Dank u wel! Samengevat zoekt u: {self._samenvatting()}.\n\n"
        return intro + self._zoek_en_toon()


def create_hotel_agent() -> HotelAgent:
    return HotelAgent()
