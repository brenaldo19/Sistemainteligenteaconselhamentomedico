# fix_dicionario.py
import re, sys, shutil, io, tokenize, pathlib, difflib

PATH = pathlib.Path("dicionario.py")
orig = PATH.read_text(encoding="utf-8")

# 1) trocar chaves top-level do tipo  "Nome" = {  ->  "Nome": {
def replace_equals_for_colon(src: str) -> str:
    # só quando logo depois vem { e a chave começa na coluna 0/indent típica de topo
    pat = re.compile(r'(?m)^(?P<indent>\s*)"(?P<key>[^"\n]+)"\s*=\s*\{')
    return pat.sub(r'\g<indent>"\g<key>": {', src)

# 2) consertar caso específico: "Sangramento gastrointestinal",  -> ": {"
def fix_sangramento_block(src: str) -> str:
    pat = re.compile(r'(?m)^(?P<indent>\s*)"Sangramento gastrointestinal"\s*,\s*$')
    return pat.sub(r'\g<indent>"Sangramento gastrointestinal": {', src)

# 3) inserir vírgula após fechamento de item top-level se a linha seguinte começa com "..."
# (evita mexer em dicionários internos por exigir início de linha)
def add_commas_between_top_items(src: str) -> str:
    lines = src.splitlines()
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        if line.rstrip().endswith("}"):
            # olha próxima linha "crua" ignorando vazias/comentários
            j = i + 1
            while j < len(lines) and lines[j].strip() in ("",):
                j += 1
            if j < len(lines) and re.match(r'^\s*"', lines[j]):  # próxima começa com aspas
                # só adiciona vírgula se a linha atual não terminar com , já
                if not line.rstrip().endswith(","):
                    out[-1] = line + ","
    return "\n".join(out)

# 4) rodar as correções
fixed = orig
fixed = replace_equals_for_colon(fixed)
fixed = fix_sangramento_block(fixed)
fixed = add_commas_between_top_items(fixed)

# 5) mostrar diff
diff = difflib.unified_diff(
    orig.splitlines(keepends=True),
    fixed.splitlines(keepends=True),
    fromfile="dicionario.py (orig)",
    tofile="dicionario.py (fixed)",
)
print("".join(diff))

# 6) checar pares de (), [], {} ignorando strings/comentários
def brackets_ok(code: str) -> tuple[bool, str]:
    pairs = {"{": "}", "[": "]", "(": ")"}
    opens = set(pairs)
    closes = {v: k for k, v in pairs.items()}
    stack = []
    for tok in tokenize.tokenize(io.BytesIO(code.encode()).readline):
        if tok.type == tokenize.OP and tok.string in opens | set(closes):
            if tok.string in opens:
                stack.append((tok.string, tok.start))
            else:
                if not stack or stack[-1][0] != closes[tok.string]:
                    return False, f"Incompatível: abriu '{stack[-1][0] if stack else '?'}' mas fechou '{tok.string}' em linha {tok.start[0]}"
                stack.pop()
    if stack:
        return False, f"Aberturas sem fechamento: {stack}"
    return True, "Brackets ok."

ok, msg = brackets_ok(fixed)
print("Bracket check:", msg)

# 7) tentar compilar
try:
    compile(fixed, "dicionario.py", "exec")
    print("✅ Compilação OK")
    # backup e salvar
    shutil.copy2(PATH, PATH.with_suffix(".py.bak"))
    PATH.write_text(fixed, encoding="utf-8")
    print("Backup em:", PATH.with_suffix(".py.bak"))
    print("Arquivo sobrescrito com correções.")
except SyntaxError as e:
    print("❌ Ainda tem SyntaxError:", e)
    print("Arquivo original NÃO foi sobrescrito.")
    sys.exit(1)
