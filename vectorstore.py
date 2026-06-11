import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

FAISS_PATH = "faiss_index"
# Meertalig model: noodzakelijk omdat de kamerbeschrijvingen en zoekopdrachten
# Nederlands zijn (het Engelstalige all-MiniLM-L6-v2 gaf willekeurige resultaten)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        print("Embeddings model laden (eenmalig ~80MB download)...")
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def build_vectorstore(rooms: list) -> FAISS:
    """Bouw een FAISS vectorstore op basis van de kamerbeschrijvingen."""
    embeddings = get_embeddings()

    docs = []
    for room in rooms:
        tekst = f"{room['naam']} — {room['type']} in {room['locatie']}. {room['beschrijving']}"
        meta = {k: v for k, v in room.items() if k != "beschrijving"}
        docs.append(Document(page_content=tekst, metadata=meta))

    vectorstore = FAISS.from_documents(docs, embeddings)

    # Opslaan zodat het niet elke keer opnieuw gebouwd hoeft te worden
    vectorstore.save_local(FAISS_PATH)
    print(f"Vectorstore opgebouwd met {len(docs)} kamers en opgeslagen in '{FAISS_PATH}/'.")
    return vectorstore


def load_vectorstore() -> FAISS:
    """Laad bestaande vectorstore van schijf (als die er is)."""
    embeddings = get_embeddings()
    return FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)


def get_or_build_vectorstore(rooms: list) -> FAISS:
    """Laad de vectorstore als die al bestaat, anders bouw hem opnieuw op."""
    if os.path.exists(FAISS_PATH):
        print("Bestaande vectorstore gevonden — wordt geladen...")
        return load_vectorstore()
    return build_vectorstore(rooms)


def semantic_search(vectorstore: FAISS, query: str, k: int = 5) -> list[dict]:
    """Voer een semantische zoekopdracht uit en geef de metadata van de resultaten."""
    results = vectorstore.similarity_search(query, k=k)
    return [doc.metadata for doc in results]
