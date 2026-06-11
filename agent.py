from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

import tools as tools_module
from tools import filter_kamers, rangschik_kamers, valideer_aanbeveling
from vectorstore import get_or_build_vectorstore
from rooms_data import ROOMS

SYSTEM_PROMPT = """Je bent een vriendelijke hotelmedewerker die gasten helpt de perfecte kamer te vinden.

Volg altijd deze 6 stappen in volgorde:
1. BEGROETING: Begroet de gast en vraag naar het verblijfsdoel (vakantie, zakenreis, etc.)
2. VRAGEN: Stel beknopte vragen over: budget (max prijs per nacht), ontbijt gewenst, parkeren nodig, huisdieren mee, aantal personen, gewenste locatie.
3. SAMENVATTING: Vat de wensen samen en bevestig ze.
4. ZOEKEN: Gebruik filter_kamers met de criteria als JSON. Voorbeeld: {"max_prijs": 120, "ontbijt": true, "capaciteit": 2}
5. TONEN: Geef de resultaten van filter_kamers door aan rangschik_kamers. Roep daarna valideer_aanbeveling aan op de output. Presenteer vervolgens de top 3.
6. FEEDBACK: Vraag of de gast tevreden is. Als de gast wil verfijnen (bijv. "te duur"), gebruik dan filter_kamers opnieuw met bijgestelde criteria.

Regels:
- Antwoord ALTIJD in het Nederlands.
- Roep valideer_aanbeveling ALTIJD aan voordat je een aanbeveling toont.
- Als filter_kamers geen resultaten geeft, stel voor om de criteria te verruimen.
- Wees vriendelijk en professioneel."""

AGENT_TOOLS = [filter_kamers, rangschik_kamers, valideer_aanbeveling]


def create_hotel_agent():
    """
    Initialiseer de LangChain 1.x hotel agent met:
    - llama3.2:1b via Ollama (lokaal)
    - 3 custom tools voor filteren, rangschikken en valideren
    - MemorySaver voor sessiememorie via thread_id
    - Vectorstore (FAISS) voor semantisch zoeken
    """
    # Vectorstore opbouwen of laden
    vectorstore = get_or_build_vectorstore(ROOMS)
    tools_module.set_vectorstore(vectorstore)

    llm = ChatOllama(model="llama3.2:1b", temperature=0.3)

    # LangChain 1.x create_agent met LangGraph MemorySaver voor sessiememorie
    agent = create_agent(
        model=llm,
        tools=AGENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )

    return agent
