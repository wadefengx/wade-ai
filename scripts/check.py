#!/usr/bin/env python3
"""Check wade-ai docs: relative links and anchors resolve, entry files stay short."""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
limits = {"AGENTS.md": 80, "playbooks/complex-work.md": 120}
errors = []

def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")

def anchors(path):
    text = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
    return {slug(h) for h in re.findall(r"^#+ (.+)$", text, flags=re.M)}

for md in sorted(root.rglob("*.md")):
    if ".git" in md.parts:
        continue
    rel = md.relative_to(root).as_posix()
    text = md.read_text()
    if rel in limits and text.count("\n") > limits[rel]:
        errors.append(f"{rel}: {text.count(chr(10))} lines > {limits[rel]}")
    for target in re.findall(r"\]\(([^)\s]+)\)", re.sub(r"```.*?```|`[^`]*`", "", text, flags=re.S)):
        if re.match(r"[a-z]+:", target):
            continue
        file, _, anchor = target.partition("#")
        dest = (md.parent / file).resolve() if file else md
        if not dest.exists():
            errors.append(f"{rel}: missing {target}")
        elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
            errors.append(f"{rel}: missing anchor {target}")

print("\n".join(errors) or "docs ok")
sys.exit(1 if errors else 0)
