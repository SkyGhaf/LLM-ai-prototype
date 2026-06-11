# Hotel Kamer Aanbeveling Agent — Sprint 3

**Vak:** AI Agents (DEAI) — De Haagse Hogeschool
**Team:** Rames Saljuqi · Sky Ghafoerkhan · Anson Mok · Omar Moussaten
**Framework:** LangChain (gekozen in Sprint 2) + Ollama (lokaal LLM) + FAISS (vectordatabase)

## Wat doet het prototype?

Een AI-agent die hotelgasten via een gesprek helpt de perfecte kamer te vinden. De agent doorloopt de 6-staps workflow uit Sprint 1:

1. **Begroeting** — gast wordt verwelkomd; criteria die de gast al noemt worden direct herkend (LLM-extractie)
2. **Ja/nee-vragen** — agent vraagt budget, ontbijt, parkeren, aantal personen en locatie (antwoorden bewaard in sessiememorie)
3. **Samenvatting** — wensen worden samengevat en bevestigd
4. **Kamers ophalen** — `filter_kamers` tool doorzoekt de kamerdatabase (FAISS vectorstore met embeddings)
5. **Rangschikken & tonen** — `rangschik_kamers` sorteert, `valideer_aanbeveling` controleert de output, daarna toont de agent de top 3
6. **Feedbackloop** — gast kan verfijnen ("te duur", "liever onder de 100", "geen voorkeur") en de agent filtert opnieuw zonder herstart

## Installatie

1. Installeer [Ollama](https://ollama.com) en haal het model op:
   ```
   ollama pull llama3.2:1b
   ```
2. Installeer de Python-dependencies:
   ```
   pip install -r requirements.txt
   ```

## Starten

```
python main.py
```

Eerste keer duurt iets langer (embeddings model ~80MB wordt gedownload en de FAISS-index wordt opgebouwd). Typ `stop` om te stoppen.

## Voorbeeldgesprek voor de demo

```
Gast: Hallo, ik zoek een kamer voor 2 personen in Den Haag
Gast: 2 personen
Gast: 120 euro
Gast: ja graag          (ontbijt)
Gast: nee               (parkeren)
→ agent toont top 3 met validatie
Gast: te duur, liever onder de 100
→ feedbackloop: agent filtert opnieuw
Gast: perfect, bedankt!
```

## Architectuur

| Bestand | Rol |
|---|---|
| `main.py` | Entry point, conversatieloop |
| `agent.py` | Workflow-orchestratie (6 stappen), LLM-extractie van criteria, sessiememorie |
| `tools.py` | LangChain `@tool`s: `filter_kamers`, `rangschik_kamers`, `valideer_aanbeveling` |
| `vectorstore.py` | FAISS vectordatabase met HuggingFace embeddings (all-MiniLM-L6-v2) |
| `rooms_data.py` | Kamerdataset (18 kamers) |
| `logging_config.py` | Logging naar `agent_log.txt` (volledige sessie) en `session.log` (events) |

**Ontwerpkeuze:** de orchestratie van de 6 stappen ligt in Python (state machine), het LLM (`llama3.2:1b`, lokaal via Ollama) interpreteert de vrije tekst van de gast. Dit is bewust: kleine lokale modellen zijn onbetrouwbaar in een vrije tool-calling loop (hangen/loopen), maar sterk in tekstbegrip. Elke LLM-extractie wordt bovendien gevalideerd tegen de letterlijke gasttekst, omdat 1B-modellen soms velden verzinnen.

## Koppeling met de meetcriteria uit Sprint 2

| Criterium | Hoe aangetoond |
|---|---|
| C2 Orchestratie | Vaste 6-staps workflow in `agent.py` (fases: begroeting → vragen → feedback) |
| C3 Sessiememorie | `self.criteria` dict bewaart alle gastwensen over de hele sessie |
| C4 Feedbackloop | Feedbackfase past criteria aan en roept `filter_kamers` opnieuw aan |
| C5 RAG/retrieval | FAISS vectorstore met embeddings; semantisch zoeken via `query`-criterium |
| C6 Tool calling | Drie LangChain `@tool`s worden in de workflow aangeroepen |
| C7 Validatie | `valideer_aanbeveling` controleert elke aanbeveling vóór presentatie |
| Logging | `agent_log.txt` + `session.log`: alle prompts, tool calls, extracties en fouten traceerbaar |

## Logging & traceerbaarheid

Na elke sessie staan in `session.log` regels als:

```
14:35:19 [INFO] LLM-extractie resultaat (gevalideerd): {'locatie': 'Rotterdam'}
14:35:19 [INFO] FEEDBACKLOOP: criteria bijgesteld met {'locatie': 'Rotterdam'}
14:35:19 [INFO] TOOL filter_kamers aangeroepen met: {"capaciteit": 2, ...}
14:35:19 [INFO] Validatie-uitkomst: [OK] Aanbeveling geldig: ...
```

Hiermee is elke stap van de agent controleerbaar (vereiste uit de opdracht).
