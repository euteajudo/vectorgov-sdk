"""
Exemplo 11: Integração com Google ADK (Agent Development Kit)

Este exemplo mostra como usar o VectorGov com Google ADK para criar
agentes especializados em legislação brasileira.

Requisitos:
    pip install vectorgov google-adk
"""

import os
from vectorgov.integrations.google_adk import (
    create_search_tool,
    VectorGovToolset,
    create_legal_agent,
)

# Chave de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")


def exemplo_tool_simples():
    """Exemplo básico usando apenas a ferramenta de busca."""
    print("=" * 60)
    print("EXEMPLO 1: Ferramenta de Busca Simples")
    print("=" * 60)

    # Cria ferramenta de busca
    search_tool = create_search_tool(api_key=VECTORGOV_KEY, top_k=3)

    # Testa diretamente (sem agente ADK)
    query = "O que é Estudo Técnico Preliminar?"
    print(f"\nQuery: {query}")
    print("\nResultado:")
    print("-" * 40)

    result = search_tool(query)
    print(result)
    print()


def exemplo_toolset():
    """Exemplo usando o toolset completo."""
    print("=" * 60)
    print("EXEMPLO 2: VectorGov Toolset")
    print("=" * 60)

    # Cria toolset com todas as ferramentas
    toolset = VectorGovToolset(api_key=VECTORGOV_KEY, top_k=5)

    # Lista as ferramentas disponíveis
    tools = toolset.get_tools()
    print("\nFerramentas disponíveis:")
    for tool in tools:
        print(f"- {tool.__name__}")
    print()

    # Testa ferramenta de listagem
    list_tool = toolset.get_list_tool()
    print("Documentos disponíveis:")
    print("-" * 40)
    print(list_tool())
    print()


def exemplo_agente_adk():
    """Exemplo com agente ADK completo."""
    print("=" * 60)
    print("EXEMPLO 3: Agente ADK com VectorGov")
    print("=" * 60)

    try:
        from google.adk.agents import Agent
    except ImportError:
        print("\nGoogle ADK não instalado.")
        print("Para usar este exemplo, instale:")
        print("  pip install google-adk")
        print("\nExibindo código de exemplo:\n")

        code = '''
from google.adk.agents import Agent
from vectorgov.integrations.google_adk import VectorGovToolset

# Cria toolset
toolset = VectorGovToolset(api_key="vg_xxx")

# Cria agente
agent = Agent(
    name="legal_assistant",
    model="gemini-2.0-flash",
    instruction="""Você é um assistente jurídico especializado
    em legislação brasileira. Use as ferramentas disponíveis
    para consultar leis e responder perguntas.""",
    tools=toolset.get_tools(),
)

# Executa
response = agent.run("Quais os critérios de julgamento na licitação?")
print(response)
'''
        print(code)
        return

    # Cria agente usando helper
    agent = create_legal_agent(api_key=VECTORGOV_KEY)

    # Executa pergunta
    query = "Quais os critérios de julgamento previstos na Lei 14.133?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    response = agent.run(query)

    print("RESPOSTA:")
    print("-" * 40)
    print(response)
    print()


def exemplo_agente_customizado():
    """Exemplo com agente ADK customizado."""
    print("=" * 60)
    print("EXEMPLO 4: Agente Customizado")
    print("=" * 60)

    try:
        from google.adk.agents import Agent
    except ImportError:
        print("\nGoogle ADK não instalado. Exibindo código de exemplo:\n")

        code = '''
from google.adk.agents import Agent
from vectorgov.integrations.google_adk import create_search_tool

# Ferramenta customizada
search = create_search_tool(
    api_key="vg_xxx",
    top_k=10,
    mode="precise",
    name="consulta_legislacao",
    description="Busca detalhada em legislação brasileira",
)

# Agente especializado em licitações
agent = Agent(
    name="licitacao_expert",
    model="gemini-2.0-flash",
    instruction="""Você é um especialista em licitações públicas.

    Suas competências:
    - Lei 14.133/2021 (Nova Lei de Licitações)
    - Instruções Normativas SEGES
    - Procedimentos de contratação

    Ao responder:
    1. Consulte sempre a legislação atualizada
    2. Cite artigos, parágrafos e incisos específicos
    3. Explique de forma clara e prática
    """,
    tools=[search],
)

# Pergunta complexa
response = agent.run(
    "Uma empresa foi inabilitada na fase de habilitação. "
    "Quais são os recursos cabíveis e prazos?"
)
print(response)
'''
        print(code)
        return

    from vectorgov.integrations.google_adk import create_search_tool

    # Ferramenta com configuração customizada
    search = create_search_tool(
        api_key=VECTORGOV_KEY,
        top_k=10,
        mode="precise",
    )

    # Agente customizado
    agent = Agent(
        name="licitacao_expert",
        model="gemini-2.0-flash",
        instruction="""Você é um especialista em licitações públicas.
Consulte sempre a legislação antes de responder.
Cite artigos específicos nas suas respostas.""",
        tools=[search],
    )

    query = "Como funciona o sistema de registro de preços?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    response = agent.run(query)

    print("RESPOSTA:")
    print("-" * 40)
    print(response)
    print()


def main():
    print("\n" + "=" * 60)
    print("VECTORGOV + GOOGLE ADK")
    print("=" * 60 + "\n")

    # Exemplo 1: Ferramenta simples (sempre funciona)
    exemplo_tool_simples()
    print("\n")

    # Exemplo 2: Toolset (sempre funciona)
    exemplo_toolset()
    print("\n")

    # Exemplo 3: Agente ADK (requer google-adk)
    exemplo_agente_adk()
    print("\n")

    # Exemplo 4: Agente customizado (requer google-adk)
    exemplo_agente_customizado()


if __name__ == "__main__":
    main()
