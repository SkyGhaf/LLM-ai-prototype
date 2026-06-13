# Kamerdata van alle (open) Valk Exclusief hotels — gescraped van valkexclusief.nl/hotels
# De site toont 43 hotels; 'De Gouden Leeuw' (gesloten tot eind 2027) en
# 'Maastricht-Maas' (in aanbouw) zijn weggelaten. Prijzen zijn indicatief.
#
# Per hotel: (naam, provincie, vanaf-prijs, huisdieren welkom, kenmerken, extra kamertypes)
HOTELS = [
    ("Akersloot", "Noord-Holland", 109, True,
     "Gelegen aan het Alkmaardermeer met binnenzwembad, sauna en fitness; veel kamers met prachtig uitzicht over het water.", "suite"),
    ("Almere", "Flevoland", 99, False,
     "Modern hotel met wellness en uitzicht over het Weerwater, dichtbij het centrum van Almere.", ""),
    ("Avifauna", "Zuid-Holland", 119, False,
     "Uniek hotel direct aan vogelpark Avifauna in Alphen aan den Rijn, met exotische tuinen en rondvaarten.", "familie"),
    ("Amsterdam Zuidas", "Noord-Holland", 159, False,
     "Stijlvol stadshotel op de Amsterdamse Zuidas met wellness; de hoogste etages bieden een indrukwekkend uitzicht over de skyline van Amsterdam.", "suite"),
    ("Apeldoorn", "Gelderland", 105, True,
     "Aan de rand van de Veluwe met bosrijk uitzicht, dichtbij Paleis Het Loo en de Apenheul.", "familie"),
    ("Assen", "Drenthe", 105, True,
     "Met wellness en gezellige hotelbar; ideale uitvalsbasis voor het TT Circuit en de Drentse natuur.", ""),
    ("Rotterdam-Blijdorp", "Zuid-Holland", 119, False,
     "Naast Diergaarde Blijdorp met wellness; binnen enkele minuten in het bruisende centrum van Rotterdam.", "familie"),
    ("Bloemendal", "Limburg", 129, False,
     "Sfeervol hotel in Vaals met gloednieuwe wellness en prachtig uitzicht over het Limburgse heuvelland, vlakbij het Drielandenpunt.", "suite"),
    ("Den Haag-Nootdorp", "Zuid-Holland", 115, True,
     "Met binnenzwembad, op korte afstand van Den Haag, het strand van Scheveningen en historisch Delft.", "familie"),
    ("Deventer", "Overijssel", 105, False,
     "Met wellness, aan de rand van de historische Hanzestad Deventer aan de IJssel.", ""),
    ("Dordrecht", "Zuid-Holland", 109, True,
     "Wellnesscenter met zwembad, dichtbij Nationaal Park de Biesbosch en het oudste stadscentrum van Holland.", ""),
    ("Düsseldorf", "Duitsland", 119, False,
     "Stadshotel in Düsseldorf, perfect voor winkelen aan de Königsallee en een avond in de Altstadt.", ""),
    ("Duiven bij Arnhem", "Gelderland", 99, True,
     "Met moderne wellness, dichtbij Arnhem, Burgers' Zoo en de natuur van de Veluwezoom.", "familie"),
    ("Eindhoven-Best", "Noord-Brabant", 119, False,
     "Met wellness en skybar met spectaculair uitzicht over de hele regio Eindhoven; 200 kamers en 22 suites.", "suite"),
    ("Emmeloord", "Flevoland", 95, True,
     "In de Noordoostpolder met weids polderuitzicht, dichtbij Nationaal Park Weerribben-Wieden en Giethoorn.", ""),
    ("Emmen", "Drenthe", 99, True,
     "Met zwembad, op korte afstand van Wildlands Adventure Zoo; ideaal voor gezinnen.", "familie"),
    ("Enschede", "Overijssel", 105, False,
     "Met wellness en zwembad, dichtbij het centrum van Enschede en het Twentse coulisselandschap.", ""),
    ("Groningen-Westerbroek", "Groningen", 105, True,
     "Landelijk gelegen tussen Groningen en Hoogezand, met rustgevend uitzicht over de weilanden.", "suite"),
    ("Haarlem", "Noord-Holland", 129, False,
     "Groot hotel met wellness, dichtbij het centrum van Haarlem, de duinen en het strand van Zandvoort.", "familie"),
    ("Harderwijk op de Veluwe", "Gelderland", 115, True,
     "Midden in de Veluwse bossen: heerlijk rustig met bosuitzicht, dichtbij het Dolfinarium.", "familie"),
    ("Heerlen", "Limburg", 105, False,
     "Wellnesscenter met zwembad in het Limburgse heuvelland, op korte afstand van Maastricht en Aken.", ""),
    ("Hengelo", "Overijssel", 99, True,
     "Met wellness; comfortabele uitvalsbasis voor Twente en het Duitse grensgebied.", ""),
    ("Hollands Kroon", "Noord-Holland", 99, True,
     "Moderne kamers in de kop van Noord-Holland, dichtbij het IJsselmeer, de Waddenzee en Den Helder.", ""),
    ("Houten-Utrecht", "Utrecht", 109, False,
     "Modern hotel onder de rook van Utrecht, met nieuwe wellness in aantocht.", ""),
    ("Leeuwarden", "Friesland", 109, True,
     "Met luxe boerderijwoningen, dichtbij het historische centrum van Leeuwarden en het Werelderfgoed Waddenzee.", "suite"),
    ("Leiden", "Zuid-Holland", 125, False,
     "Met terras direct aan het water en prachtig uitzicht over de Oude Rijn, dichtbij historisch Leiden.", "suite"),
    ("Maastricht", "Limburg", 135, False,
     "Met wellness en binnenzwembad; kamers met uitzicht over de Maas en het Limburgse heuvelland.", "suite"),
    ("Middelburg", "Zeeland", 109, True,
     "Met wellness en zwembad, dichtbij de Zeeuwse stranden en het monumentale centrum van Middelburg.", "familie"),
    ("Rotterdam-Nieuwerkerk", "Zuid-Holland", 105, True,
     "Met wellness, gunstig gelegen tussen Rotterdam en Gouda in het Groene Hart.", ""),
    ("Oostzaan-Amsterdam", "Noord-Holland", 115, False,
     "Aan de rand van Amsterdam, dichtbij de Zaanse Schans en op 15 minuten van het centrum.", ""),
    ("Schiedam", "Zuid-Holland", 109, False,
     "Met 5 suites, dichtbij de historische jeneverstad Schiedam en het centrum van Rotterdam.", "suite"),
    ("Schiphol", "Noord-Holland", 139, False,
     "Met zwembad, wellness en gratis shuttleservice naar luchthaven Schiphol; ideaal voor en na een vliegreis.", ""),
    ("Sneek", "Friesland", 105, True,
     "Aan de rand van de Friese meren met uitzicht over het water; perfect voor watersporters.", "familie"),
    ("Spier-Dwingeloo", "Drenthe", 119, True,
     "Met wellnesscenter midden in Nationaal Park Dwingelderveld: volledige rust, natuur en sterrenhemels.", "suite"),
    ("Kasteel TerWorm", "Limburg", 189, False,
     "Romantisch kasteelhotel op eigen landgoed bij Heerlen, met vorstelijke suites, kasteeltuinen en adembenemend uitzicht over het groen.", "suite"),
    ("Tilburg", "Noord-Brabant", 105, True,
     "Dichtbij de Efteling en Safaripark Beekse Bergen; ideaal voor een dagje uit met het gezin.", "familie"),
    ("Utrecht", "Utrecht", 129, False,
     "Stadshotel met uitzicht over Utrecht, dichtbij de Jaarbeurs en het gezellige centrum.", "suite"),
    ("Vianen-Utrecht", "Utrecht", 99, True,
     "Direct aan de A2 onder Utrecht; praktische en comfortabele uitvalsbasis.", ""),
    ("Woerden", "Utrecht", 99, True,
     "In het Groene Hart tussen Utrecht en Gouda, met landelijk uitzicht over de polders.", ""),
    ("Wolvega-Heerenveen", "Friesland", 95, True,
     "Tussen Wolvega en Heerenveen, dichtbij Thialf en de Friese natuur; voordelig en comfortabel.", ""),
    ("Zwolle", "Overijssel", 109, False,
     "Modern hotel dichtbij het historische centrum van de Hanzestad Zwolle.", "familie"),
]

# Hotels zonder gratis parkeren (stadslocaties met betaalde garage)
_BETAALD_PARKEREN = {"Amsterdam Zuidas", "Utrecht"}

ROOMS = []
for _i, (_naam, _prov, _vanaf, _huisdieren, _kenmerken, _extra) in enumerate(HOTELS, 1):
    _parkeren = _naam not in _BETAALD_PARKEREN

    ROOMS.append({
        "id": f"VE{_i:03d}A",
        "naam": f"Comfort Kamer — Hotel {_naam}",
        "type": "standard",
        "prijs_per_nacht": _vanaf,
        "locatie": _naam,
        "capaciteit": 2,
        "ontbijt": False,
        "parkeren": _parkeren,
        "huisdieren": _huisdieren,
        "beschrijving": (
            f"Comfortabele tweepersoonskamer in Van der Valk Hotel {_naam} ({_prov}). "
            f"{_kenmerken} Gratis wifi en het vertrouwde Valk-comfort."
        ),
    })

    ROOMS.append({
        "id": f"VE{_i:03d}B",
        "naam": f"Deluxe Kamer — Hotel {_naam}",
        "type": "deluxe",
        "prijs_per_nacht": _vanaf + 45,
        "locatie": _naam,
        "capaciteit": 2,
        "ontbijt": True,
        "parkeren": _parkeren,
        "huisdieren": False,
        "beschrijving": (
            f"Ruime deluxe kamer met luxe badkamer en regendouche in Van der Valk Hotel {_naam} ({_prov}). "
            f"Inclusief uitgebreid Live Cooking ontbijtbuffet. {_kenmerken}"
        ),
    })

    if "suite" in _extra:
        ROOMS.append({
            "id": f"VE{_i:03d}C",
            "naam": f"Suite — Hotel {_naam}",
            "type": "suite",
            "prijs_per_nacht": _vanaf + 115,
            "locatie": _naam,
            "capaciteit": 2,
            "ontbijt": True,
            "parkeren": _parkeren,
            "huisdieren": False,
            "beschrijving": (
                f"Luxe suite met aparte zithoek, kingsize boxspring en ligbad in Van der Valk Hotel {_naam} ({_prov}). "
                f"Romantisch en ruim, inclusief ontbijtbuffet. {_kenmerken}"
            ),
        })

    if "familie" in _extra:
        ROOMS.append({
            "id": f"VE{_i:03d}D",
            "naam": f"Familiekamer — Hotel {_naam}",
            "type": "family",
            "prijs_per_nacht": _vanaf + 60,
            "locatie": _naam,
            "capaciteit": 4,
            "ontbijt": True,
            "parkeren": _parkeren,
            "huisdieren": _huisdieren,
            "beschrijving": (
                f"Ruime familiekamer voor vier personen in Van der Valk Hotel {_naam} ({_prov}). "
                f"Kindvriendelijk ontbijtbuffet inbegrepen. {_kenmerken}"
            ),
        })
