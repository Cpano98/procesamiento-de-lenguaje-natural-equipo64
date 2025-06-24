# -*- coding: utf-8 -*-
# stori_runbook_chatbot_poc.py

# --- Import Libraries ---
import os
import logging
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
from langchain.schema.output_parser import StrOutputParser
import gradio as gr
from dotenv import load_dotenv

# --- Local Imports ---
from rag_builder import load_latest_rag_version, initial_sources, PDF_DOCS_DIR

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

# --- Global Variables ---
vectorstore = None
llm = None
rag_version = "N/A"

def chat_with_rag(question, history, category):
    """Chat function that interacts with the RAG using Gemini, with category filtering."""
    logging.info(f"Question received: '{question}' in category: '{category}'")
    
    if not vectorstore or not llm:
        return "RAG is not available. The application could not start correctly."
    if not question.strip():
        return "Please enter a valid question."

    # Create retriever with or without category filtering
    if not category or category == "All":
        retriever = vectorstore.as_retriever(search_kwargs={'k': 5})
        logging.info("Searching across all categories.")
    else:
        retriever = vectorstore.as_retriever(search_kwargs={'k': 5, 'filter': {'category': category}})
        logging.info(f"Searching within category: '{category}'")

    # Define prompt template
    template = """You are a helpful assistant for Stori developers.
Answer the question based only on the following context. Do not use external knowledge.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

If the user asks for a diagram, a flowchart, a sequence diagram, or any kind of visual representation of the code, architecture, or logic, you MUST generate a Mermaid diagram to explain it.
When generating a diagram, enclose the entire Mermaid code in a markdown block like this:
```mermaid
graph TD;
    A-->B;
```
Ensure the Mermaid syntax is correct and that the diagram code is complete and not truncated. Use this to visualize relationships, data flow, or component interactions from the context provided.

Context:
{context}

Question: {question}

Helpful Answer:"""
    prompt = PromptTemplate.from_template(template)

    # Define RAG chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain_from_docs = (
        {"context": lambda x: format_docs(x["context"]), "question": lambda x: x["question"]}
        | prompt
        | llm
        | StrOutputParser()
    )

    rag_chain_with_source = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)

    try:
        result = rag_chain_with_source.invoke(question)
        answer = result['answer']

        sources_info = "\n\n--- \n*Consulted Sources:*"
        seen_sources = set()
        for doc in result['context']:
            source_name = os.path.basename(doc.metadata.get('source', 'Unknown'))
            source_type = doc.metadata.get('source_type', 'Unknown')
            if source_name not in seen_sources:
                seen_sources.add(source_name)
                sources_info += f"\n- `{source_name}` (Category: `{doc.metadata.get('category', 'Unknown')}`, Type: `{source_type}`)"

        return f"{answer}{sources_info}"

    except Exception as e:
        logging.error(f"Error processing question '{question}': {e}", exc_info=True)
        return "Sorry, an error occurred while processing your question."

def main():
    """Main function that creates the RAG and launches the Gradio interface."""
    global vectorstore, llm, rag_version
    load_dotenv('.env')
    
    try:
        logging.info("--- Loading latest RAG version on application startup ---")
        vectorstore, llm, rag_version = load_latest_rag_version()
        llm.max_output_tokens = 8192 # Ensure long diagrams are not truncated
        logging.info(f"--- ✅ RAG version '{rag_version}' loaded successfully. ---")
    except Exception as e:
        logging.critical(f"--- ❌ CRITICAL ERROR LOADING RAG ❌ ---")
        logging.critical(f"Application cannot start without RAG: {e}", exc_info=True)
        # Display error in Gradio UI
        with gr.Blocks() as demo:
            gr.Markdown(f"# ❌ Error starting application\nCould not load the RAG vector store. Please check the logs.\n\n**Error:**\n```\n{e}\n```")
        demo.launch(server_name="0.0.0.0", server_port=7862)
        return

    # Format source URLs and PDF info to display in interface
    source_files_markdown = "#### This RAG was trained with the following documents:\n"
    for category, source_details in initial_sources.items():
        source_files_markdown += f"\n**Category: {category}**\n"
        
        # List GitHub URLs
        urls = source_details.get("urls", [])
        if urls:
            source_files_markdown += "\n*GitHub Documents:*\n"
            for url in urls:
                file_name = url.split('/')[-1]
                source_files_markdown += f"- [{file_name}]({url})\n"
        
        # List PDF files
        pdf_dir = os.path.join(PDF_DOCS_DIR, category)
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
            if pdf_files:
                source_files_markdown += "\n*PDF Documents:*\n"
                for pdf in pdf_files:
                    source_files_markdown += f"- {pdf}\n"
        
        # List cloned repositories
        repos = source_details.get("repos", [])
        if repos:
            source_files_markdown += "\n*Cloned Repositories:*\n"
            for repo_url in repos:
                repo_name = repo_url.split('/')[-1]
                source_files_markdown += f"- {repo_name}\n"

    with gr.Blocks(
        theme=gr.themes.Soft(
            primary_hue="emerald", 
            secondary_hue="emerald"
        )
    ) as demo:
        gr.Markdown(f"## Stori Runbooks Chatbot\n*Currently using documentation version: `{rag_version}`*")
        # --- Chatbot Interface ---
        chatbot_interface = gr.ChatInterface(
            fn=lambda message, history: chat_with_rag(message, history, "All"),
            chatbot=gr.Chatbot(
                height=850,
                bubble_full_width=False,
                avatar_images=(None, None),
                label="Stori Runbooks Chatbot"
            ),
            textbox=gr.Textbox(placeholder="Ask me anything about the documentation...", container=False, scale=7),
            examples=[
                ["How is state managed in the application?"],
                ["Summarize the build and deploy process"],
                ["What are the extension APIs?"]
            ],
            cache_examples=False,
        )

    logging.info("Launching Gradio interface at http://127.0.0.1:7862")
    demo.launch(server_name="0.0.0.0", server_port=7862)


if __name__ == "__main__":
    main()