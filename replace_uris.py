import os
import glob

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False
        
    original = content
    content = content.replace("http://purl.org/dido#", "http://purl.org/dido#")
    content = content.replace("http://purl.org/dido#", "http://purl.org/dido#")
    
    if original != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    root_dir = '/home/kelseyrook/Documents/GitHub/dialogueOnt'
    extensions = ['.ttl', '.owl', '.py', '.sparql', '.md', '.ru', '.jsonl', '.html', '.nt', '.jsonld']
    changed_files = []
    
    for subdir, _, files in os.walk(root_dir):
        if '.git' in subdir or '.gemini' in subdir:
            continue
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                filepath = os.path.join(subdir, file)
                if replace_in_file(filepath):
                    changed_files.append(filepath)
                    
    for f in changed_files:
        print(f"Updated: {f}")
    print(f"Total files updated: {len(changed_files)}")

if __name__ == '__main__':
    main()
