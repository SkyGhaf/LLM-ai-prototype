"""
Hotel Kamer Aanbeveling Agent
Sprint 3 - LangChain + Ollama (llama3.2:1b) + FAISS

Start: python main.py
Vereiste: Ollama actief met llama3.2:1b (`ollama pull llama3.2:1b`)
"""

import sys
from logging_config import setup_logging

BANNER = """
================================================
  Hotel Kamer Aanbeveling Agent -- Sprint 3
  LangChain + Ollama (llama3.2:1b) + FAISS
================================================
Typ 'stop' of 'quit' om de sessie te beeindigen.
"""


def main() -> None:
    logger = setup_logging("agent_log.txt")
    logger.info("Sessie gestart")

    print(BANNER)
    print("Agent wordt geladen (vectorstore + embeddings + model)...\n")

    try:
        from agent import create_hotel_agent
        agent = create_hotel_agent()
    except Exception as exc:
        print(f"\n[FOUT] Kon de agent niet starten: {exc}")
        print("Controleer of Ollama actief is en llama3.2:1b geladen is (ollama pull llama3.2:1b).")
        logger.error(f"Opstartfout: {exc}")
        sys.exit(1)

    print("Agent klaar! Begin het gesprek (bijv. 'Hallo, ik zoek een kamer').\n")

    while True:
        try:
            user_input = input("Gast: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAgent: Sessie onderbroken. Tot ziens!")
            logger.info("Sessie onderbroken (Ctrl+C / EOF)")
            break

        if not user_input:
            continue

        if user_input.lower() in ("stop", "quit", "exit", "bye"):
            print("\nAgent: Bedankt voor uw bezoek! Tot ziens en een prettig verblijf.")
            logger.info("Sessie beeindigd door gebruiker")
            break

        logger.info(f"GAST: {user_input}")

        try:
            output = agent.reageer(user_input)
        except Exception as exc:
            output = f"Er is een fout opgetreden: {exc}. Kunt u uw vraag anders formuleren?"
            logger.error(f"Agent fout: {exc}")

        print(f"\nAgent: {output}\n")
        logger.info(f"AGENT: {output}")


if __name__ == "__main__":
    main()
