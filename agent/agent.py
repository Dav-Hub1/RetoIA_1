from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from config import settings
from agent.rag import rag_service


# ========== DEPENDENCIAS ==========
class ManagerDeps(BaseModel):
    """Dependencies for the agent."""
    session_id: str


# ========== MODELO ==========
model = OpenAIChatModel(
    model_name=settings.model_name,
)

# ========== AGENTE ==========
manager_agent = Agent[ManagerDeps, str](
    model=model,
    deps_type=ManagerDeps,
    output_type=str,
    system_prompt=(
    """
    # Context
    You are David de la Cruz's personal career assistant. You help recruiters, supervisors, and colleagues learn about David's professional background, skills, research experience, and achievements.

    # Behavior
    - Be conversational, professional, and concise.
    - Answer ONLY based on the context retrieved from David's CV.
    - If the context doesn't contain the answer, say so honestly.

    # Capabilities and Limitations
    - You can search David's CV using the `retrieve_cv_context` tool.
    - You can summarize, compare, and explain David's experience.
    - You cannot access external information or the internet.
    - You cannot make up information not present in the CV.

    # Tools
    - `retrieve_cv_context`: Searches David's CV.

    # Rules
    1. ALWAYS call `retrieve_cv_context` with the user's query before answering.
    2. If the tool returns no results, try again with broader keywords.
    3. Never say "I don't have information" without first calling the tool.
    4. Use the context to formulate a specific, detailed answer.

    # Instructions
    1. Receive the user's question.
    2. Call `retrieve_cv_context` with the full question.
    3. If no results, call again with simplified keywords.
    4. Summarize the relevant context into a clear, conversational response.
    5. Answer as if you know David personally from his CV.

    # Additional Context
    - David's CV contains sections: Profile Summary, Education, Research Experience, Publications, Technical Skills, Soft Skills, Professional Experience, International Mobility, Languages.
    - Common queries: educational background, PhD research, key strengths, technical skills, work experience, languages, publications.

    # Fallback Rules
    - If after two tool calls there's still no relevant information, respond with:
      "I couldn't find specific information about that in David's CV. Is there anything else you'd like to know about his background, skills, or experience?"
    """
),
    retries=2
)


# ========== HERRAMIENTA ==========
@manager_agent.tool()
async def retrieve_cv_context(ctx: RunContext[ManagerDeps], query: str) -> str:
    """Retrieve relevant chunks from David's CV to answer the query."""
    retrieved = rag_service.retrieve(query)
    if not retrieved:
        return "No relevant information found in the CV."
    
    context = rag_service.format_context(retrieved)
    return context


# ========== FUNCIÓN PARA GENERAR RESPUESTA ==========
async def generate_response(user_input: str, session_id: str) -> str:
    """Generate a response using the agent with RAG."""
    deps = ManagerDeps(session_id=session_id)
    # Añadir instrucción explícita en el prompt del usuario
    prompt_with_instruction = f"Use the retrieve_cv_context tool to answer: {user_input}"
    
    result = await manager_agent.run(
        instructions=prompt_with_instruction,
        deps=deps,
    )
    return result.output