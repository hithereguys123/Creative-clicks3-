import re, os

with open("ALL_CODE.md", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"### File: (.+?)\n---\n```[a-z]*\n([\s\S]*?)```"
matches = re.findall(pattern, content)

for path, code in matches:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        out.write(code)
    print(f"Created {path}")
