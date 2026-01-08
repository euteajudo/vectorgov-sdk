"""
Exemplo 10: Integração com LangGraph - ReAct Agent

Este exemplo mostra como usar o VectorGov com LangGraph para criar
um agente ReAct que consulta legislação brasileira.

Requisitos:
    pip install vectorgov langgraph langchain-openai
"""

import os
from vectorgov.integrations.langgraph import create_vectorgov_tool

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def exemplo_react_agent():
    """Exemplo com ReAct Agent pré-construído do LangGraph."""
    print("=" * 60)
    print("EXEMPLO 1: ReAct Agent com VectorGov")
    print("=" * 60)

    try:
        from langgraph.prebuilt import create_react_agent
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("Instale: pip install langgraph langchain-openai")
        return

    # Cria ferramenta VectorGov
    tool = create_vectorgov_tool(api_key=VECTORGOV_KEY, top_k=3)

    # Cria LLM
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_KEY)

    # Cria agente ReAct
    agent = create_react_agent(llm, tools=[tool])

    # Executa pergunta
    query = "Quais são os critérios de julgamento previstos na Lei 14.133?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    result = agent.invoke({"messages": [("user", query)]})

    # Mostra resposta
    print("RESPOSTA:")
    print("-" * 40)
    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(msg.content)
    print()


def exemplo_grafo_customizado():
    """Exemplo com grafo customizado usando retrieval node."""
    print("=" * 60)
    print("EXEMPLO 2: Grafo Customizado com Retrieval Node")
    print("=" * 60)

    try:
        from langgraph.graph import StateGraph, START, END
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("Instale: pip install langgraph langchain-openai")
        return

    from vectorgov.integrations.langgraph import (
        create_retrieval_node,
        VectorGovState,
    )

    # Cria nó de retrieval
    retrieval_node = create_retrieval_node(api_key=VECTORGOV_KEY, top_k=5)

    # Cria LLM
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_KEY)

    # Nó de geração
    def generate(state: VectorGovState) -> dict:
        context = state.get("context", "")
        query = state.get("query", "")

        prompt = f"""Você é um especialista em legislação brasileira.
Responda com base no contexto e cite as fontes.

Contexto:
{context}

Pergunta: {query}

Resposta:"""

        response = llm.invoke(prompt)
        return {"response": response.content}

    # Constrói grafo
    builder = StateGraph(dict)  # Usando dict genérico
    builder.add_node("retrieve", retrieval_node)
    builder.add_node("generate", generate)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)

    graph = builder.compile()

    # Executa
    query = "O que é Estudo Técnico Preliminar (ETP)?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    result = graph.invoke({"query": query})

    print("CONTEXTO RECUPERADO:")
    print("-" * 40)
    print(result.get("context", "")[:500] + "...")
    print()

    print("FONTES:")
    print("-" * 40)
    for source in result.get("sources", []):
        print(f"- {source}")
    print()

    print("RESPOSTA:")
    print("-" * 40)
    print(result.get("response", ""))
    print()


def exemplo_rag_completo():
    """Exemplo com grafo RAG pré-configurado."""
    print("=" * 60)
    print("EXEMPLO 3: Grafo RAG Completo")
    print("=" * 60)

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("Instale: pip install langgraph langchain-openai")
        return

    from vectorgov.integrations.langgraph import create_legal_rag_graph

    # Cria LLM
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_KEY)

    # Cria grafo RAG completo
    graph = create_legal_rag_graph(
        llm=llm,
        api_key=VECTORGOV_KEY,
        top_k=5,
        mode="balanced",
    )

    # Executa
    query = "Quando o ETP pode ser dispensado?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    result = graph.invoke({"query": query})

    print("FONTES UTILIZADAS:")
    print("-" * 40)
    for source in result.get("sources", []):
        print(f"- {source}")
    print()

    print("RESPOSTA:")
    print("-" * 40)
    print(result.get("response", ""))
    print()


def main():
    print("\n" + "=" * 60)
    print("VECTORGOV + LANGGRAPH")
    print("=" * 60 + "\n")

    # Exemplo 1: ReAct Agent
    if OPENAI_KEY:
        exemplo_react_agent()
        print("\n")

        # Exemplo 2: Grafo Customizado
        exemplo_grafo_customizado()
        print("\n")

        # Exemplo 3: RAG Completo
        exemplo_rag_completo()
    else:
        print("Configure OPENAI_API_KEY para executar os exemplos")


if __name__ == "__main__":
    main()
