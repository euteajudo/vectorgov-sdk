"""
Exemplo 9: Integração com LangChain

Este exemplo mostra como usar o VectorGov com LangChain.
O VectorGovRetriever é compatível com todas as chains do LangChain.

Requisitos:
    pip install vectorgov langchain langchain-openai
"""

import os
from vectorgov.integrations.langchain import VectorGovRetriever

# Chaves de API
VECTORGOV_KEY = os.getenv("VECTORGOV_API_KEY", "vg_xxx")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def exemplo_basico():
    """Exemplo básico: usar o retriever diretamente."""
    print("=" * 60)
    print("EXEMPLO 1: Retriever Básico")
    print("=" * 60)

    retriever = VectorGovRetriever(api_key=VECTORGOV_KEY, top_k=3)

    # Busca documentos
    docs = retriever.invoke("O que é Estudo Técnico Preliminar?")

    print(f"\nEncontrados {len(docs)} documentos:\n")
    for i, doc in enumerate(docs, 1):
        print(f"[{i}] {doc.metadata['source']}")
        print(f"    Score: {doc.metadata['score']:.2%}")
        print(f"    {doc.page_content[:150]}...")
        print()


def exemplo_retrieval_qa():
    """Exemplo com RetrievalQA chain."""
    print("=" * 60)
    print("EXEMPLO 2: RetrievalQA Chain")
    print("=" * 60)

    try:
        from langchain.chains import RetrievalQA
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("Instale: pip install langchain langchain-openai")
        return

    # Cria retriever e LLM
    retriever = VectorGovRetriever(api_key=VECTORGOV_KEY, top_k=5)
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_KEY)

    # Cria chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
    )

    # Faz pergunta
    query = "Quando o ETP pode ser dispensado?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    result = qa.invoke(query)

    print("RESPOSTA:")
    print("-" * 40)
    print(result["result"])
    print("\nFONTES:")
    print("-" * 40)
    for doc in result["source_documents"]:
        print(f"- {doc.metadata['source']}")


def exemplo_lcel():
    """Exemplo com LCEL (LangChain Expression Language)."""
    print("=" * 60)
    print("EXEMPLO 3: LCEL (Moderno)")
    print("=" * 60)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("Instale: pip install langchain-core langchain-openai")
        return

    # Componentes
    retriever = VectorGovRetriever(api_key=VECTORGOV_KEY, top_k=5)
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_KEY)

    # Prompt
    prompt = ChatPromptTemplate.from_template("""
Você é um especialista em legislação brasileira.
Responda com base no contexto fornecido e cite as fontes.

Contexto:
{context}

Pergunta: {question}

Resposta:""")

    # Função para formatar documentos
    def format_docs(docs):
        return "\n\n".join(
            f"[{doc.metadata['source']}]\n{doc.page_content}"
            for doc in docs
        )

    # Chain LCEL
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Executa
    query = "Quais são os modos de disputa na licitação?"
    print(f"\nPergunta: {query}")
    print("\nProcessando...\n")

    answer = chain.invoke(query)

    print("RESPOSTA:")
    print("-" * 40)
    print(answer)


def main():
    print("\n" + "=" * 60)
    print("VECTORGOV + LANGCHAIN")
    print("=" * 60 + "\n")

    # Executa exemplos
    exemplo_basico()
    print("\n")

    if OPENAI_KEY:
        exemplo_retrieval_qa()
        print("\n")
        exemplo_lcel()
    else:
        print("Configure OPENAI_API_KEY para exemplos com LLM")


if __name__ == "__main__":
    main()
