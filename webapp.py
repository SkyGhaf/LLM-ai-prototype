"""
Van der Valk Hotel Website met chatbot-widget (Flask)

Start: python webapp.py
Daarna: open http://localhost:5000
Vereiste: Ollama actief met llama3.2:1b
"""

import logging
import uuid

from flask import Flask, jsonify, render_template, request, session

from agent import create_hotel_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hotel_agent")

app = Flask(__name__)
app.secret_key = "vdv-prototype-demo"  # alleen voor sessiecookies in dit schoolprototype

# Eén HotelAgent per browsersessie: de agent bewaart zelf fase + criteria
_agents: dict[str, object] = {}


def _get_agent():
    sid = session.get("sid")
    if sid is None or sid not in _agents:
        sid = uuid.uuid4().hex
        session["sid"] = sid
        _agents[sid] = create_hotel_agent()
        logger.info(f"Nieuwe chatsessie gestart: {sid[:8]}")
    return _agents[sid]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    bericht = (request.json or {}).get("message", "").strip()
    if not bericht:
        return jsonify({"reply": "Ik heb geen bericht ontvangen. Probeer het opnieuw."})

    agent = _get_agent()
    try:
        antwoord = agent.reageer(bericht)
    except Exception as exc:
        logger.error(f"Agent fout: {exc}")
        antwoord = "Er ging iets mis. Kunt u uw vraag anders formuleren?"

    return jsonify({"reply": antwoord})


@app.route("/reset", methods=["POST"])
def reset():
    sid = session.get("sid")
    if sid in _agents:
        del _agents[sid]
    session.pop("sid", None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Agent wordt voorgeladen (vectorstore + embeddings)...")
    # Vectorstore/embeddings één keer opwarmen zodat de eerste chat snel is
    _agents["warmup"] = create_hotel_agent()
    del _agents["warmup"]
    print("Klaar! Open http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
