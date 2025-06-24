# boost_docs.py
# Script to post-process and enhance generated documentation in the latest /front/<timestamp>/ directory

import os
import re
import glob
from bs4 import BeautifulSoup

# --- Utility Functions ---
def get_latest_version_dir(front_dir):
    version_dirs = [d for d in os.listdir(front_dir) if os.path.isdir(os.path.join(front_dir, d)) and d.isdigit()]
    if not version_dirs:
        return None
    latest = sorted(version_dirs, reverse=True)[0]
    return os.path.join(front_dir, latest)

def condense_markdown(md_content):
    # Simple deduplication and structuring logic (can be replaced with LLM for smarter processing)
    lines = md_content.splitlines()
    seen = set()
    new_lines = []
    for line in lines:
        if line.strip() in seen and line.strip().startswith('#'):
            continue  # Remove duplicate headers
        seen.add(line.strip())
        new_lines.append(line)
    # Remove consecutive blank lines
    condensed = re.sub(r'\n{3,}', '\n\n', '\n'.join(new_lines))
    return condensed

def condense_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove duplicate h2/h3 headers
    seen = set()
    for tag in soup.find_all(['h2', 'h3']):
        text = tag.get_text(strip=True)
        if text in seen:
            tag.decompose()
        else:
            seen.add(text)
    # Optionally, further summarization/structuring can be added here
    return str(soup)

def process_files_in_dir(version_dir):
    for file in glob.glob(os.path.join(version_dir, '*.md')):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        improved = condense_markdown(content)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(improved)
    for file in glob.glob(os.path.join(version_dir, '*.html')):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        improved = condense_html(content)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(improved)

def main():
    front_dir = os.path.join(os.path.dirname(__file__), 'front')
    latest_dir = get_latest_version_dir(front_dir)
    if not latest_dir:
        print('No versioned documentation directories found.')
        return
    print(f'Boosting documentation in: {latest_dir}')
    process_files_in_dir(latest_dir)
    print('Documentation boosting complete.')

if __name__ == '__main__':
    main() 