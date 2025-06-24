# -*- coding: utf-8 -*-
# generate_docs.py

import os
import logging
from bs4 import BeautifulSoup
import markdown
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
import re
import datetime

from rag_builder import create_new_rag_version, initial_sources

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

def generate_sidebar_nav(html_content):
    """Parses the generated HTML and creates sidebar navigation links."""
    soup = BeautifulSoup(html_content, 'html.parser')
    sidebar_links = []
    
    headings = soup.find_all(['h2', 'h3'])
    used_ids = set()

    for heading in headings:
        heading_text = heading.get_text(strip=True)
        slug_base = re.sub(r'\s+', '-', heading_text.lower())
        slug_base = re.sub(r'[^a-z0-9\-]', '', slug_base)
        
        slug = slug_base
        count = 1
        while slug in used_ids:
            slug = f"{slug_base}-{count}"
            count += 1
        
        heading['id'] = slug
        used_ids.add(slug)
        
        sidebar_links.append({
            'id': slug,
            'text': heading_text,
            'level': int(heading.name[1:])
        })

    nav_html = '<ul class="nav flex-column">'
    for link in sidebar_links:
        if link['level'] == 2:
            nav_html += f'<li class="nav-item"><a class="nav-link" href="#{link["id"]}">{link["text"]}</a></li>'
    nav_html += '</ul>'
    
    return nav_html, str(soup)

def generate_documentation_for_category(category_name, vectorstore, llm, version_id):
    """Generates an HTML documentation page for a specific category."""
    logging.info(f"Generating documentation for category: {category_name} (Version: {version_id})")

    try:
        results = vectorstore.get(where={"category": category_name}, include=["documents"])
        documents = results.get("documents", [])
        if not documents:
            logging.warning(f"No documents found for category: {category_name}")
            return None, None
    except Exception as e:
        logging.error(f"Could not retrieve documents for category '{category_name}': {e}", exc_info=True)
        return None, None

    chunk_size = 5
    all_generated_content = []

    for i in range(0, len(documents), chunk_size):
        chunk = documents[i:i + chunk_size]
        documents_content = "\n\n---\n\n".join(chunk)

        category_title = category_name.replace('-', ' ').title()
        prompt_template = PromptTemplate(
            input_variables=["context", "category_name", "category_title"],
            template=(
                "Task: Create a comprehensive, non-redundant technical documentation page for the '{category_title}' category.\n\n"
                "Audience: The documentation will be used by both technical (frontend/backend developers) and product stakeholders.\n\n"
                "Instructions:\n"
                "1. Deduplicate and synthesize: If content or headers repeat, merge and summarize them. Avoid boilerplate.\n"
                "2. Use ONLY the information provided in the context for this category. Do NOT combine or invent information from other categories or external sources.\n"
                "3. Structure the documentation as follows:\n"
                "   - Abstract: A concise summary of the project/repo.\n"
                "   - What is it?: Briefly explain the purpose and main functionality.\n"
                "   - Available APIs/Modules: List and describe all public APIs or modules, with concise, meaningful section titles. Only include endpoints that are present in the provided context. Do not invent or assume endpoints.\n"
                "   - Entry Payloads & Responses: For each API, describe the expected input and output, with examples.\n"
                "   - Error Handling: Explain how errors are managed and reported.\n"
                "   - Metrics/Monitoring: Describe any available metrics or monitoring features.\n"
                "   - Troubleshooting/FAQ: Common problems and their solutions.\n"
                "   - Examples: Provide usage examples.\n"
                "   - Diagrams: Where helpful, include a Mermaid diagram (in <pre class=\"mermaid\">...</pre> tags) to illustrate architecture, flow, or relationships.\n"
                "   - If the repository does not contain APIs, explain the content in an ordered way, summarizing its content so the reader can quickly and clearly understand it.\n"
                "4. Formatting: Use well-structured Markdown (headings, lists, code blocks). Do NOT include any HTML except for Mermaid blocks.\n"
                "5. Section Titles: Make all section and subsection titles as short, unique, and meaningful as possible.\n"
                "6. Clarity: Write for both technical and product audiences—be clear, concise, and avoid jargon where possible.\n"
                "7. Accuracy: Do NOT invent endpoints, APIs, or features. Only document what is present in the provided context.\n\n"
                "Content to Analyze:\n---\n{context}\n---"
            )
        )

        chain = prompt_template | llm | StrOutputParser()

        try:
            logging.info(f"Invoking LLM for chunk {i // chunk_size + 1} of '{category_name}'...")
            generated_content = chain.invoke({
                "context": documents_content,
                "category_name": category_name,
                "category_title": category_title
            })
            all_generated_content.append(generated_content)
        except Exception as e:
            logging.error(f"Error invoking LLM for category '{category_name}', chunk {i // chunk_size + 1}: {e}", exc_info=True)
            continue

    if not all_generated_content:
        logging.error(f"Failed to generate any content for category '{category_name}'.")
        return None, None

    final_markdown_content = "\n".join(all_generated_content)

    versioned_front_dir = os.path.join("front", version_id)
    os.makedirs(versioned_front_dir, exist_ok=True)
    with open(os.path.join(versioned_front_dir, f"{category_name}.md"), "w", encoding="utf-8") as f:
        f.write(final_markdown_content)

    final_html_content = markdown.markdown(
        final_markdown_content,
        extensions=['fenced_code', 'tables', 'codehilite', 'extra'],
        output_format='html5'
    )

    final_html_content = re.sub(
        r'&lt;pre class="mermaid"&gt;(.*?)&lt;/pre&gt;',
        r'<pre class="mermaid">\1</pre>',
        final_html_content,
        flags=re.DOTALL
    )

    sidebar_nav, final_html_content = generate_sidebar_nav(final_html_content)

    page_title = f"Documentation: {category_title}"
    
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1.0, shrink-to-fit=no">
  <link href="../assets/images/favicon.png" rel="icon" />
  <title>{page_title}</title>
  <meta name="description" content="Stori Technical Documentation">
  <meta name="author" content="Stori">

  <!-- Stori Design System -->
  <link rel="stylesheet" type="text/css" href="../assets/css/stori-style.css" />
  
  <!-- Vendor CSS -->
  <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
</head>

<body data-spy="scroll" data-target=".docs-sidebar" data-offset="125">

<header class="stori-header">
  <a class="logo" href="../index.html" title="Stori Docs">
    <img src="https://www.storicard.com/_next/static/media/storis_savvi_color.7e286ddd.svg" alt="Stori Logo">
  </a>
  <nav>
    <a href="../index.html#project-overview">About</a>
    <a href="../index.html#sitemap-list">Sitemap</a>
    <a href="../index.html" class="stori-btn">Back to Home</a>
  </nav>
</header>
  
<div id="content" role="main" class="container docs-wrapper">
  <nav class="docs-sidebar">
    {sidebar_nav}
  </nav>
  
  <div class="docs-content stori-card">
    <section>
      <h1>{category_title}</h1>
      <p class="lead">This document provides a detailed overview of the {category_title} module.</p>
      <hr style="margin: 2rem 0;">
      {final_html_content}
    </section>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({{ startOnLoad: true }});
</script>

</body>
</html>
""".format(
        page_title=page_title,
        category_title=category_title,
        sidebar_nav=sidebar_nav,
        final_html_content=final_html_content
    )

    file_name = f"{category_name}.html"
    output_path = os.path.join(versioned_front_dir, file_name)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        logging.info(f"✅ Successfully generated documentation for '{category_name}' at '{output_path}'")
        return file_name, category_title
    except IOError as e:
        logging.error(f"Could not write to file '{output_path}': {e}")
        return None, None

def update_index_html():
    index_path = os.path.join(os.path.dirname(__file__), 'front', 'index.html')
    if not os.path.exists(index_path):
        logging.error("front/index.html not found. Cannot update navigation.")
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # --- Ensure Bootstrap CSS is present for the dropdown ---
    head = soup.find('head')
    if head and not head.find('link', href=lambda x: x and 'bootstrap.min.css' in x):
        bootstrap_css = soup.new_tag(
            'link',
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
        )
        head.append(bootstrap_css)

    front_dir = os.path.join(os.path.dirname(__file__), 'front')
    version_dirs = sorted(
        [d for d in os.listdir(front_dir) if os.path.isdir(os.path.join(front_dir, d)) and d.isdigit()],
        reverse=True
    )
    
    # --- 1. Update Header Dropdown with latest version docs ---
    header_nav_container = soup.select_one('header nav .hidden.md\\:flex')
    if header_nav_container:
        for child in header_nav_container.find_all(recursive=False):
            child.decompose()

        if version_dirs:
            latest_version = version_dirs[0]
            latest_version_path = os.path.join(front_dir, latest_version)
            doc_files = sorted([f for f in os.listdir(latest_version_path) if f.endswith('.html')])

            if doc_files:
                # Use Tailwind classes for the button, and Bootstrap for the dropdown functionality
                dropdown_html = """
                <div class="dropdown">
                  <button class="py-2 px-4 rounded-full bg-stori-green text-white font-semibold hover:bg-stori-primary-green-dark transition-colors duration-300 dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    Latest Docs
                  </button>
                  <ul class="dropdown-menu">
                """
                for doc_file in doc_files:
                    doc_title = doc_file.replace('.html', '').replace('-', ' ').title()
                    dropdown_html += f'<li><a class="dropdown-item" href="./{latest_version}/{doc_file}">{doc_title}</a></li>'
                
                dropdown_html += "</ul></div>"
                header_nav_container.append(BeautifulSoup(dropdown_html, 'html.parser'))

    # --- 2. Update Documentation Versions List ---
    versions_container = soup.find('div', id='documentation-versions')
    if versions_container:
        versions_container.clear()
        
        if not version_dirs:
            versions_container.append(BeautifulSoup("<p>No documentation versions found.</p>", 'html.parser'))
        else:
            list_wrapper = soup.new_tag('div', attrs={'class': 'space-y-4 w-full text-left'})
            for version_id in version_dirs:
                version_path = os.path.join(front_dir, version_id)
                doc_files = sorted([f for f in os.listdir(version_path) if f.endswith('.html')])
                
                if not doc_files:
                    continue

                try:
                    dt_object = datetime.datetime.strptime(version_id, "%Y%m%d%H%M%S")
                    formatted_date = dt_object.strftime("%B %d, %Y - %H:%M:%S")
                except ValueError:
                    formatted_date = version_id
                
                version_block_html = f"""
                <div class="p-4 border rounded-lg bg-gray-50">
                    <h3 class="text-md font-semibold text-stori-dark-blue">{formatted_date}</h3>
                    <ul class="mt-2 list-disc list-inside pl-2">
                        {''.join([f'<li><a href="./{version_id}/{doc}" class="text-stori-green hover:underline">{doc.replace(".html", "").replace("-", " ").title()}</a></li>' for doc in doc_files])}
                    </ul>
                </div>
                """
                list_wrapper.append(BeautifulSoup(version_block_html, 'html.parser'))
            versions_container.append(list_wrapper)

    # --- 3. Update Sitemap with all files for quick access ---
    sitemap_ul = soup.find('ul', id='sitemap-list')
    if sitemap_ul:
        sitemap_ul.clear()
        if not version_dirs:
            sitemap_ul.append(BeautifulSoup("<li>No documentation found.</li>", 'html.parser'))
        else:
            all_docs = []
            for version_id in version_dirs:
                version_path = os.path.join(front_dir, version_id)
                doc_files = sorted([f for f in os.listdir(version_path) if f.endswith('.html')])
                for doc_file in doc_files:
                    all_docs.append({'version': version_id, 'file': doc_file})
            
            all_docs.sort(key=lambda x: x['file'])
            
            for doc_info in all_docs:
                version_id = doc_info['version']
                doc_file = doc_info['file']
                doc_title = doc_file.replace('.html', '').replace('-', ' ').title()
                
                try:
                    dt_object = datetime.datetime.strptime(version_id, "%Y%m%d%H%M%S")
                    formatted_date = dt_object.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = version_id

                li_html = f'<li><a href="./{version_id}/{doc_file}" class="text-stori-green hover:underline">{doc_title}</a> <span class="text-stori-gray text-sm">({formatted_date})</span></li>'
                sitemap_ul.append(BeautifulSoup(li_html, 'html.parser'))

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))

    logging.info("✅ Updated front/index.html with header dropdown, version list, and sitemap.")

def main():
    logging.info("--- Starting Documentation Generation Process ---")

    try:
        vectorstore, llm, version_id = create_new_rag_version()
        llm.max_output_tokens = 8192 # Ensure long diagrams are not truncated
    except Exception as e:
        logging.critical(f"Failed to set up RAG: {e}", exc_info=True)
        return

    generated_files = []
    for category in initial_sources.keys():
        file_name, category_title = generate_documentation_for_category(category, vectorstore, llm, version_id)
        if file_name and category_title:
            generated_files.append((file_name, category_title))

    if generated_files:
        update_index_html()

    logging.info("--- Documentation Generation Process Finished ---")

if __name__ == "__main__":
    main()
