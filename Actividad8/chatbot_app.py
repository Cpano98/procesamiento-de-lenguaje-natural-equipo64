# -*- coding: utf-8 -*-
# stori_runbook_chatbot_poc.py

# --- Import Libraries ---
import os
import shutil
import logging
import re
import subprocess
from github import Github, UnknownObjectException
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
from langchain.schema.output_parser import StrOutputParser
import gradio as gr
from dotenv import load_dotenv

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

# --- Global Variables ---
vectorstore = None
llm = None
LOCAL_DOCS_DIR = "./downloaded_runbooks"
PERSIST_DIRECTORY = "./chroma_db"
PDF_DOCS_DIR = "./pdf_docs"
CLONED_REPOS_DIR = "./cloned_repos"

def parse_github_url(url):
    """Parses a GitHub URL to extract organization, repository, branch and file path."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
    if match:
        return match.groups()
    return None, None, None, None

def download_docs_from_github(github_token, urls_text):
    """Downloads documents from a list of GitHub URLs."""
    if not urls_text.strip():
        return []

    g = Github(github_token)
    os.makedirs(LOCAL_DOCS_DIR, exist_ok=True)
    downloaded_files = []
    
    urls = [url.strip() for url in urls_text.strip().split('\n') if url.strip()]
    
    for url in urls:
        org, repo_name, branch, path = parse_github_url(url)
        if not all([org, repo_name, branch, path]):
            logging.warning(f"Invalid GitHub URL or incorrect format: {url}")
            continue

        try:
            repo = g.get_repo(f"{org}/{repo_name}")
            logging.info(f"Accessing: {org}/{repo_name}")
            
            file_content = repo.get_contents(path, ref=branch)
            
            # Clean filename for local storage
            local_filename = f"{repo_name}_{path.replace('/', '_')}"
            local_filepath = os.path.join(LOCAL_DOCS_DIR, local_filename)

            with open(local_filepath, "w", encoding="utf-8") as f:
                f.write(file_content.decoded_content.decode('utf-8'))
            
            logging.info(f"✅ Downloaded '{path}' to '{local_filepath}'")
            downloaded_files.append(local_filepath)

        except UnknownObjectException:
            logging.error(f"❌ File not found at '{url}'. Verify URL, branch and path.")
        except Exception as e:
            logging.error(f"Error downloading from {url}: {e}", exc_info=True)
            
    return downloaded_files

def load_pdf_docs(category):
    """Loads PDF documents from the category-specific directory."""
    category_dir = os.path.join(PDF_DOCS_DIR, category)
    if not os.path.exists(category_dir):
        return []
        
    pdf_files = []
    for file in os.listdir(category_dir):
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(category_dir, file))
    return pdf_files

def clone_github_repo(repo_url, category):
    """Clones a GitHub repository into a category-specific directory."""
    if not repo_url.strip().endswith(".git"):
        repo_url += ".git"
    
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    clone_dir = os.path.join(CLONED_REPOS_DIR, category, repo_name)
    
    if os.path.exists(clone_dir):
        logging.info(f"Repository '{repo_name}' already exists in '{clone_dir}'. Skipping clone.")
        return clone_dir

    logging.info(f"Cloning '{repo_url}' into '{clone_dir}'...")
    try:
        subprocess.run(
            ["git", "clone", repo_url, clone_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(f"✅ Successfully cloned repository: {repo_name}")
        return clone_dir
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to clone repository: {repo_url}")
        logging.error(f"Git Error: {e.stderr}")
        return None

def setup_rag(sources: dict):
    """Creates the Vector Store from a dictionary of categorized sources."""
    global vectorstore, llm
    
    # Load environment variables
    load_dotenv('.env')
    GITHUB_TOKEN = os.getenv('CPANO_GITHUB_TOKEN')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    if not GOOGLE_API_KEY:
        logging.error("Error: GOOGLE_API_KEY is not configured.")
        raise ValueError("Error: GOOGLE_API_KEY is not configured. Please set it in your .env file.")

    # --- 1. Get and load documents ---
    logging.info("--- 1. Getting and loading documents ---")
    
    all_documents = []
    
    has_urls = any(sources.values())
    if has_urls and not GITHUB_TOKEN:
        logging.error("Error: CPANO_GITHUB_TOKEN is not configured for GitHub downloads.")
        raise ValueError("Error: GitHub URLs were provided but CPANO_GITHUB_TOKEN is not configured.")

    # Create directory structures
    os.makedirs(PDF_DOCS_DIR, exist_ok=True)
    os.makedirs(CLONED_REPOS_DIR, exist_ok=True)
    for category in sources.keys():
        os.makedirs(os.path.join(PDF_DOCS_DIR, category), exist_ok=True)
        os.makedirs(os.path.join(CLONED_REPOS_DIR, category), exist_ok=True)

    for category, source_details in sources.items():
        logging.info(f"Processing category: '{category}'")
        
        # Process GitHub URLs
        urls = source_details.get("urls", [])
        urls_text = "\n".join(urls)
        if urls_text.strip():
            github_files = download_docs_from_github(GITHUB_TOKEN, urls_text)
            
            # Load GitHub documents
            for file_path in github_files:
                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata["category"] = category
                        doc.metadata["source_type"] = "github"
                    
                    all_documents.extend(docs)
                    logging.info(f"Loaded {len(docs)} segments from GitHub file '{file_path}' for category '{category}'")
                except Exception as e:
                    logging.error(f"Error loading GitHub file {file_path}: {e}")

        # Process PDF documents
        pdf_files = load_pdf_docs(category)
        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(pdf_path)
                docs = loader.load()
                for doc in docs:
                    doc.metadata["category"] = category
                    doc.metadata["source_type"] = "pdf"
                
                all_documents.extend(docs)
                logging.info(f"Loaded {len(docs)} segments from PDF '{pdf_path}' for category '{category}'")
            except Exception as e:
                logging.error(f"Error loading PDF {pdf_path}: {e}")

        # Process and load from GitHub Repositories
        repos_to_clone = source_details.get("repos", [])
        for repo_url in repos_to_clone:
            cloned_repo_path = clone_github_repo(repo_url, category)
            if cloned_repo_path:
                # Define files/extensions to include and directories to ignore
                allowed_extensions = {'.py', '.md', '.js', '.ts', '.java', '.go', '.html', '.css', '.txt', '.sh', '.yml', '.yaml', '.json'}
                ignored_dirs = {'.git', 'node_modules', '__pycache__', 'build', 'dist', 'target'}

                for root, dirs, files in os.walk(cloned_repo_path):
                    # Remove ignored directories from traversal
                    dirs[:] = [d for d in dirs if d not in ignored_dirs]
                    
                    for file in files:
                        if any(file.endswith(ext) for ext in allowed_extensions):
                            file_path = os.path.join(root, file)
                            try:
                                loader = TextLoader(file_path, encoding="utf-8")
                                docs = loader.load()
                                for doc in docs:
                                    doc.metadata["category"] = category
                                    doc.metadata["source_type"] = "repository"
                                all_documents.extend(docs)
                                logging.info(f"Loaded {len(docs)} segments from repo file '{file_path}'")
                            except Exception as e:
                                logging.warning(f"Could not load repo file {file_path}: {e}")
                                
    if not all_documents:
        logging.error("No documents were found or downloaded from the provided sources.")
        raise ValueError("No documents were found or downloaded. Check your source configuration.")

    logging.info(f"Loaded a total of {len(all_documents)} document segments from all categories.")
    
    # --- 2. Split and create embeddings ---
    logging.info("--- 2. Splitting documents and creating embeddings ---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(all_documents)
    logging.info(f"Documents split into {len(texts)} chunks.")

    # Clean vector DB directory if it exists
    if os.path.exists(PERSIST_DIRECTORY):
        logging.info(f"Removing existing ChromaDB directory: {PERSIST_DIRECTORY}")
        shutil.rmtree(PERSIST_DIRECTORY)

    # --- 3. Create Vector Store and RAG Chain ---
    logging.info("--- 3. Creating Vector Store and initializing LLM ---")
    
    # Initialize embeddings model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_query")

    # Create Chroma vector store
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3)
    
    logging.info("✅ RAG setup complete. Vector store and LLM are ready.")


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
Ensure the Mermaid syntax is correct. Use this to visualize relationships, data flow, or component interactions from the context provided.

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
    load_dotenv('.env')
    
    initial_sources = {
        "finclip-miniprogram-boilerplate": {
            "urls": [
                "https://github.com/credifranco/finclip-miniprogram-boilerplate/blob/main/docs/api-services.md",
                "https://github.com/credifranco/finclip-miniprogram-boilerplate/blob/main/docs/build-deploy.md",
                "https://github.com/credifranco/finclip-miniprogram-boilerplate/blob/main/docs/extension-apis.md",
                "https://github.com/credifranco/finclip-miniprogram-boilerplate/blob/main/docs/project-structure.md",
                "https://github.com/credifranco/finclip-miniprogram-boilerplate/blob/main/docs/state-management.md",
                "https://github.com/credifranco/finclip-miniprogram-boilerplate/blob/main/docs/tracking.md"
            ],
            "repos": [
                "https://github.com/credifranco/finclip-miniprogram-boilerplate",
                "https://github.com/credifranco/deposits-jars-ui",
            ]
        },
        "deposits-secured-card": {
            "urls": [
                "https://github.com/credifranco/deposits-transactions-securedcard/blob/dev/README.md",
                "https://github.com/credifranco/deposits-transactions-securedcard/blob/dev/TROUBLESHOOTING_RUNBOOK.md"
            ],
            "repos": [
                "https://github.com/credifranco/deposits-transactions-securedcard",
                "https://github.com/credifranco/deposits-transactions-securedcard-integrations",
            ]
        },
        "hyperlane-tooling": {
            "urls": [
                "https://github.com/credifranco/hyperlane-authorization/blob/main/README.md",
                "https://github.com/credifranco/wl-internal-gateway-routing-rules/blob/main/README.md"
            ],
            "repos": [
                "https://github.com/credifranco/backend-service-template",
            ]
        }
    }

    try:
        logging.info("--- Creating RAG on application startup ---")
        setup_rag(initial_sources)
        logging.info("--- ✅ RAG created successfully. ---")
    except Exception as e:
        logging.critical(f"--- ❌ CRITICAL ERROR CREATING RAG ❌ ---")
        logging.critical(f"Application cannot start without RAG: {e}", exc_info=True)
        return # End execution if RAG cannot be created

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
        with gr.Row():
            with gr.Column(scale=4):
                # --- Chatbot Interface ---
                chatbot_interface = gr.ChatInterface(
                    fn=None, # Will be set later to include category
                    chatbot=gr.Chatbot(
                        height=850,
                        bubble_full_width=False,
                        avatar_images=(None, None),
                        label="Stori Runbooks Chatbot"
                    ),
                    textbox=gr.Textbox(placeholder="First, select a category. Then, write your question here...", container=False, scale=7),
                    examples=[
                        ["How is state managed in the application?"],
                        ["Summarize the build and deploy process"],
                        ["What are the extension APIs?"]
                    ],
                    cache_examples=False,
                )
            with gr.Column(scale=1):
                gr.Markdown(source_files_markdown)
                category_dropdown = gr.Dropdown(
                    label="Select a Document Category",
                    choices=["All"] + list(initial_sources.keys()),
                    value="All"
                )

        # Link the chat function with the category dropdown
        chatbot_interface.fn = lambda message, history: chat_with_rag(message, history, category_dropdown.value)

    logging.info("Launching Gradio interface at http://127.0.0.1:7862")
    demo.launch(server_name="0.0.0.0", server_port=7862)


if __name__ == "__main__":
    main()