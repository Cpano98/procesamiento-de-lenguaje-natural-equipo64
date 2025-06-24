# -*- coding: utf-8 -*-
# rag_builder.py

# --- Import Libraries ---
import os
import shutil
import logging
import re
import subprocess
import datetime
from github import Github, Auth, UnknownObjectException
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

# --- Global Variables & Directories ---
PARENT_PERSIST_DIRECTORY = "./chroma_db"
PDF_DOCS_DIR = "./pdf_docs"
CLONED_REPOS_DIR = "./cloned_repos"
DOWNLOADED_RUNBOOKS_DIR = "./downloaded_runbooks"

# --- Source Configuration ---
initial_sources = {
    "finclip-miniprogram-boilerplate": {
        "pdf_docs": False,
        "repos": [
        ],
         "urls": [
        ],
    },
    "deposits-secured-card": {
        "pdf_docs": True,
        "urls": [
        ],
        "repo_dirs": [
        ],
        "repos": [
        ]
    },
    "hyperlane-tooling": {
        "pdf_docs": False,
        "repos": [
        ]
    },
}

# --- Helper Functions ---

def parse_github_url(url):
    """Parses a GitHub URL to extract org, repo, branch, and path."""
    # Match blob (file) URLs
    file_match = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
    if file_match:
        return {'type': 'file', 'org': file_match.group(1), 'repo': file_match.group(2), 'branch': file_match.group(3), 'path': file_match.group(4)}

    # Match tree (directory) URLs
    dir_match = re.match(r"https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/?(.*)", url)
    if dir_match:
        return {'type': 'tree', 'org': dir_match.group(1), 'repo': dir_match.group(2), 'branch': dir_match.group(3), 'path': dir_match.group(4) or '.'}

    # Match base repo URLs
    repo_match = re.match(r"https://github\.com/([^/]+)/([^/]+)/?", url)
    if repo_match:
        return {'type': 'repo', 'org': repo_match.group(1), 'repo': repo_match.group(2)}
        
    return None

def download_github_file(g, org, repo_name, branch, file_path):
    """Downloads a single file from a GitHub repository."""
    try:
        repo = g.get_repo(f"{org}/{repo_name}")
        content_obj = repo.get_contents(file_path, ref=branch)
        
        # Sanitize filename and create local path
        local_filename = f"{repo_name}_{file_path.replace('/', '_')}"
        local_filepath = os.path.join(DOWNLOADED_RUNBOOKS_DIR, local_filename)

        with open(local_filepath, "wb") as f:
            f.write(content_obj.decoded_content)
        
        logging.info(f"✅ Downloaded '{file_path}' to '{local_filepath}'")
        return [local_filepath]
    except UnknownObjectException:
        logging.error(f"❌ File not found at '{file_path}' in {org}/{repo_name}. Verify URL, branch and path.")
    except Exception as e:
        logging.error(f"Error downloading file {file_path}: {e}")
    return []

def download_github_directory(g, org, repo_name, branch, dir_path):
    """Recursively downloads files from a directory in a GitHub repository."""
    downloaded_files = []
    try:
        repo = g.get_repo(f"{org}/{repo_name}")
        contents = repo.get_contents(dir_path, ref=branch)
        
        queue = list(contents)
        while queue:
            content_file = queue.pop(0)
            if content_file.type == 'dir':
                queue.extend(repo.get_contents(content_file.path, ref=branch))
            else:
                downloaded_files.extend(download_github_file(g, org, repo_name, branch, content_file.path))
    except Exception as e:
        logging.error(f"Error downloading from directory {dir_path}: {e}")
    return downloaded_files

def clone_github_repo(g, repo_url):
    """Clones a GitHub repository."""
    parsed_url = parse_github_url(repo_url)
    if not parsed_url or parsed_url['type'] != 'repo':
        logging.warning(f"Invalid GitHub repo URL, skipping: {repo_url}")
        return None

    repo_name = parsed_url['repo']
    clone_dir = os.path.join(CLONED_REPOS_DIR, repo_name)

    if os.path.exists(clone_dir) and os.listdir(clone_dir):
        logging.info(f"Repository '{repo_name}' already cloned. Skipping.")
        return clone_dir

    logging.info(f"Cloning '{repo_name}'...")
    try:
        repo = g.get_repo(f"{parsed_url['org']}/{repo_name}")
        subprocess.run(
            ["git", "clone", repo.clone_url, clone_dir],
            check=True, capture_output=True, text=True
        )
        logging.info(f"✅ Successfully cloned '{repo_name}'")
        return clone_dir
    except Exception as e:
        logging.error(f"❌ Failed to clone repository '{repo_name}': {e}")
        return None

def load_documents_from_path(path, category, source_type, allowed_extensions=None):
    """Loads all supported documents from a given directory path."""
    all_documents = []
    if allowed_extensions is None:
        allowed_extensions = {'.py', '.md', '.js', '.ts', '.java', '.go', '.html', '.css', '.txt', '.sh', '.yml', '.yaml', '.json'}
    
    ignored_dirs = {'.git', 'node_modules', '__pycache__', 'build', 'dist', 'target', 'test', 'tests', 'mock', 'mocks', 'vendor'}

    for root, dirs, files in os.walk(path):
        # Exclude ignored directories from recursion
        dirs[:] = [d for d in dirs if d.lower() not in ignored_dirs]
        
        for file in files:
            file_lower = file.lower()
            
            # Skip files with test/mock patterns in their names
            if '_test.' in file_lower or '_mock.' in file_lower or file_lower.startswith('test_') or file_lower.startswith('mock_'):
                continue

            if any(file.endswith(ext) for ext in allowed_extensions):
                file_path = os.path.join(root, file)
                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata["category"] = category
                        doc.metadata["source_type"] = source_type
                    all_documents.extend(docs)
                except Exception as e:
                    logging.warning(f"Could not load repo file {file_path}: {e}")
    return all_documents


# --- Main RAG Setup Function ---

def create_new_rag_version():
    """Initializes and sets up a new version of the RAG pipeline."""
    load_dotenv('.env')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("Error: GOOGLE_API_KEY is not configured.")

    # Initialize GitHub client
    g = None
    github_token = os.getenv("CPANO_GITHUB_TOKEN")
    if github_token:
        try:
            auth = Auth.Token(github_token)
            g = Github(auth=auth)
        except Exception as e:
            logging.error(f"Failed to initialize GitHub client: {e}")
    else:
        logging.warning("GITHUB_TOKEN not set. Skipping GitHub-related processing.")
    
    # --- 1. Load Documents ---
    logging.info("--- 1. Loading documents from all sources ---")
    all_documents = []

    # Create directories
    for path in [PDF_DOCS_DIR, CLONED_REPOS_DIR, DOWNLOADED_RUNBOOKS_DIR]:
        os.makedirs(path, exist_ok=True)

    for category, sources in initial_sources.items():
        logging.info(f"Processing category: '{category}'")

        # Load from local PDF directory if specified
        if sources.get("pdf_docs"):
            category_pdf_dir = os.path.join(PDF_DOCS_DIR, category)
            if os.path.exists(category_pdf_dir):
                for filename in os.listdir(category_pdf_dir):
                    if filename.lower().endswith('.pdf'):
                        pdf_path = os.path.join(category_pdf_dir, filename)
                        try:
                            loader = PyPDFLoader(pdf_path)
                            docs = loader.load()
                            for doc in docs:
                                doc.metadata["category"] = category
                                doc.metadata["source_type"] = "pdf"
                            all_documents.extend(docs)
                            logging.info(f"Loaded {len(docs)} segments from PDF '{pdf_path}'")
                        except Exception as e:
                            logging.error(f"Error loading PDF {pdf_path}: {e}")

        if g:
            # Process individual file URLs
            for url in sources.get("urls", []):
                parsed = parse_github_url(url)
                if parsed and parsed['type'] == 'file':
                    files = download_github_file(g, parsed['org'], parsed['repo'], parsed['branch'], parsed['path'])
                    for file_path in files:
                        all_documents.extend(load_documents_from_path(os.path.dirname(file_path), category, "github_file"))

            # Process directory URLs
            for url in sources.get("repo_dirs", []):
                parsed = parse_github_url(url)
                if parsed and parsed['type'] == 'tree':
                    files = download_github_directory(g, parsed['org'], parsed['repo'], parsed['branch'], parsed['path'])
                    for file_path in files:
                        all_documents.extend(load_documents_from_path(os.path.dirname(file_path), category, "github_dir"))

            # Process full repositories
            for url in sources.get("repos", []):
                clone_path = clone_github_repo(g, url)
                if clone_path:
                    all_documents.extend(load_documents_from_path(clone_path, category, "repository", allowed_extensions={'.go'}))

    if not all_documents:
        raise ValueError("No documents were loaded. Check source configuration and paths.")

    logging.info(f"Loaded a total of {len(all_documents)} document segments.")

    # --- 2. Split Documents ---
    logging.info("--- 2. Splitting documents ---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(all_documents)
    logging.info(f"Documents split into {len(texts)} chunks.")

    # --- 3. Create Vector Store ---
    logging.info("--- 3. Creating Vector Store and initializing LLM ---")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    persist_directory = os.path.join(PARENT_PERSIST_DIRECTORY, timestamp)
    os.makedirs(persist_directory, exist_ok=True)
    logging.info(f"Creating new RAG version in: {persist_directory}")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_query")
    
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3)
    
    logging.info(f"✅ RAG version '{timestamp}' created successfully.")
    return vectorstore, llm, timestamp

def load_latest_rag_version():
    """Loads the latest available RAG version."""
    load_dotenv('.env')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("Error: GOOGLE_API_KEY is not configured.")

    if not os.path.exists(PARENT_PERSIST_DIRECTORY):
        raise FileNotFoundError("Chroma DB directory not found. Please create a version first.")
    
    version_dirs = [d for d in os.listdir(PARENT_PERSIST_DIRECTORY) if os.path.isdir(os.path.join(PARENT_PERSIST_DIRECTORY, d))]
    if not version_dirs:
        raise FileNotFoundError("No RAG versions found in the Chroma DB directory.")
        
    latest_version = sorted(version_dirs, reverse=True)[0]
    persist_directory = os.path.join(PARENT_PERSIST_DIRECTORY, latest_version)
    logging.info(f"Loading latest RAG version: '{latest_version}' from '{persist_directory}'")
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_query")
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3)

    return vectorstore, llm, latest_version 