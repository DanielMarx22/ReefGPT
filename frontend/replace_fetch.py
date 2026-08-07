import os, re

files_to_update = [
    r"c:\Users\Daniel\Desktop\reefGPT\frontend\src\app\page.tsx",
    r"c:\Users\Daniel\Desktop\reefGPT\frontend\src\app\livestock\page.tsx",
    r"c:\Users\Daniel\Desktop\reefGPT\frontend\src\components\Chatbot.tsx",
]

for file_path in files_to_update:
    if not os.path.exists(file_path):
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add import for fetchWithAuth
    if 'import { fetchWithAuth }' not in content:
        # Find last import
        imports_end = content.rfind('import')
        if imports_end != -1:
            line_end = content.find('\n', imports_end)
            content = content[:line_end] + "\nimport { fetchWithAuth } from '@/lib/api';" + content[line_end:]

    # 2. Replace raw fetch with fetchWithAuth
    # fetch(`${API_BASE}/something`) -> fetchWithAuth(`/something`)
    content = re.sub(r'fetch\(`\$\{API_BASE\}([^`]+)`', r'fetchWithAuth(`\1`', content)
    # fetch(`${API_BASE}`) -> fetchWithAuth(`/`)
    content = re.sub(r'fetch\(`\$\{API_BASE\}`', r'fetchWithAuth(`/`', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
