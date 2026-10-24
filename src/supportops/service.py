
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from supportops.config import settings
from supportops.knowledge_base import get_vector_store


SYSTEM_PROMPT = """You are SupportOps Copilot, an IT support knowledge assistant.

Answer in natural, clear Indonesian.

RULES:
1. Use only the supplied evidence for internal procedures.
2. Answer the exact question, using only relevant evidence.
3. Preserve every critical action, escalation rule, severity condition,
   warning, and timing requirement that applies.
4. Do not invent procedures, waiting periods, or facts.
5. Do not add unrelated deployment, rollback, or backup procedures.
6. Do not repeat the same instruction in multiple sections.
7. Do not add meta-statements such as "there are no other instructions"
   when the evidence already provides applicable instructions.
8. If a requested detail is missing from the evidence, state that clearly.
9. Use short, numbered steps for operational procedures and concise
   comparisons for questions about severity levels.
10. Preserve technical meaning. Do not translate technical phrases
    into misleading Indonesian expressions.
11. When a source names a specific technical check, preserve its exact
    technical term. For example, write "health endpoint" explicitly;
    do not replace it only with "kesehatan layanan".
12. Never turn missing information into a prohibition or a definite
    negative claim. Do not say that a severity level has "no escalation"
    unless the source explicitly states this.
13. When comparing severity levels, explain only the procedures documented
    for each level. Distinguish "the document does not specify" from
    "the procedure is prohibited" or "escalation is not required".

Terminology guidance:
- "root-cause analysis" means "analisis akar masalah".
- "deployment history" means "riwayat deployment".
- "user impact" means "dampak terhadap pengguna".
- "incident ticket" means "tiket insiden".
- Keep "incident commander" and "on-call engineer" as role names.

Return only the answer. Do not invent source names or add unnecessary closing remarks.
"""


class RAGService:
    """Retrieval-augmented answering service. Model and vector store load on demand."""


    def retrieve(self, query: str, k: int | None = None) -> list[dict[str, Any]]:
        store = get_vector_store()
        hits = store.similarity_search_with_score(
            query,
            k=k or settings.top_k,
        )

        if not hits:
            return []

        # MVP policy: focus on the source of the highest-ranked result.
        primary_source = str(
            hits[0][0].metadata.get("source", "unknown")
        )

        focused_hits = [
            (document, distance)
            for document, distance in hits
            if str(document.metadata.get("source", "unknown")) == primary_source
        ]

        results: list[dict[str, Any]] = []

        for document, distance in focused_hits:
            results.append(
                {
                    "source": str(document.metadata.get("source", "unknown")),
                    "chunk_id": str(document.metadata.get("chunk_id", "unknown")),
                    "excerpt": document.page_content[:600],
                    "content": document.page_content,
                    "distance": float(distance),
                }
            )

        return results

    def answer(self, query: str) -> dict[str, Any]:
        evidence = self.retrieve(query)

        if not evidence:
            return {
                "answer": (
                    "Saya belum menemukan dokumen yang relevan. Pastikan dokumen "
                    "sudah diindeks atau ajukan pertanyaan yang lebih spesifik."
                ),
                "sources": [],
            }

        evidence_text = "\n\n".join(
            f"[Source: {item['source']} | Chunk: {item['chunk_id']}]\n"
            f"{item['content']}"
            for item in evidence
        )

        user_prompt = f"""PERTANYAAN:
{query}

BUKTI DOKUMEN:
{evidence_text}

INSTRUKSI:
- Jawab langsung sesuai pertanyaan.
- Prioritaskan bukti yang paling relevan.
- Pertahankan istilah teknis sesuai panduan pada system prompt.
- Untuk prosedur, susun langkah penting dalam urutan yang jelas.
- Untuk perbandingan severity, jelaskan kondisi dan tindakan setiap level
  yang ditanyakan.
- Untuk daftar informasi, sebutkan setiap elemen yang diwajibkan sumber.
- Jangan menambahkan langkah yang tidak relevan.
- Jangan menghilangkan eskalasi, larangan, atau tindakan penting.
- Jika informasi tidak tersedia, katakan demikian tanpa menebak.
- Sebutkan istilah "health endpoint" secara eksplisit ketika bukti meminta
  pemeriksaan tersebut.
- Jangan menyimpulkan bahwa suatu tindakan tidak diperlukan hanya karena
  dokumen tidak menyebutkannya.
- Untuk perbandingan severity, jelaskan prosedur yang dinyatakan sumber
  tanpa mengarang larangan atau pengecualian.

Berikan jawaban dalam bahasa Indonesia yang jelas dan ringkas."""

        try:
            llm = ChatOllama(
                model=settings.llm_model,
                base_url=settings.ollama_base_url,
                temperature=0,
            )

            response = llm.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            )

            answer_text = response.content
            if not isinstance(answer_text, str):
                answer_text = str(answer_text)

            answer_text = answer_text.strip()
            if not answer_text:
                raise RuntimeError("The configured LLM returned an empty response.")

        except Exception as exc:
            raise RuntimeError(
                "LLM request failed. Check that Ollama is running and the "
                "configured model is installed "
                f"(model={settings.llm_model}). Details: {exc}"
            ) from exc

        public_sources = [
            {
                "source": item["source"],
                "chunk_id": item["chunk_id"],
                "excerpt": item["excerpt"],
                "distance": round(item["distance"], 4),
            }
            for item in evidence
        ]

        return {
            "answer": answer_text,
            "sources": public_sources,
        }
