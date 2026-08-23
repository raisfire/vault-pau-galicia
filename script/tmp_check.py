import re
RUN_RE = re.compile(r"([\U0001D400-\U0001D7FF])\1+")
t = open("vault/matematicas_ii/2020/ordinaria/pregunta-1.md", encoding="utf-8").read()
for m in RUN_RE.finditer(t):
    print(len(m.group(0)), repr(m.group(0)))
