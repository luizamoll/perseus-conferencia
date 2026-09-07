"""Extrai literais do notebook (sem executá-lo) e evidências da planilha original."""
import argparse
import ast
import collections
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from classificacao import cursos_do_registro

CATEGORIAS = {"Graduação", "Pós", "MBA", "Mestrado", "DI", "Aperfeiçoamento", "Curso livre"}
ABAS = {"agosto": "Fatura_Final_Ref_Agosto_2026", "setembro": "Fatura_Final_Ref_Setembro"}
ALIASES = {"Cursos graduação": "Graduação", "GRAD": "Graduação", "Pos": "Pós", "POS": "Pós", "MESTRADO": "Mestrado", "APERF": "Aperfeiçoamento", "CURSO_LIVRE": "Curso livre", "DI (Disciplinas Isoladas)": "DI"}


def ler_planilha(caminho):
    # Células preenchidas somente; ignora dimensões infladas por formatação.
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(caminho) as z:
        ss = []
        if "xl/sharedStrings.xml" in z.namelist():
            ss = ["".join(e.itertext()) for e in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        rels = {e.get("Id"): e.get("Target") for e in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        abas = {}
        for sheet in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", ns):
            nome = sheet.get("name")
            if nome not in ["Legenda_Cursos_Status", *ABAS.values()]: continue
            rid = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = rels[rid]; path = target.lstrip("/") if target.startswith("/") else "xl/" + target
            rows = collections.defaultdict(dict)
            for _, e in ET.iterparse(z.open(path), events=["end"]):
                if e.tag.endswith("}c"):
                    v = e.find("m:v", ns); inline = e.find("m:is", ns)
                    value = v.text if v is not None else ("".join(inline.itertext()) if inline is not None else None)
                    if value is not None:
                        if e.get("t") == "s": value = ss[int(value)]
                        col, row = re.fullmatch(r"([A-Z]+)([0-9]+)", e.get("r")).groups()
                        rows[int(row)][col] = value
                    e.clear()
                elif e.tag.endswith("}row"): e.clear()
            abas[nome] = dict(rows)
    return abas


def historico(abas, mes):
    rows = abas[ABAS[mes]]
    headers = {v: k for k,v in rows[1].items()}
    for n,row in sorted(rows.items()):
        if n == 1 or not row.get(headers["Aluno"]): continue
        yield {"linha_excel": n, "aba": ABAS[mes], **{k: row.get(c) for k,c in headers.items()}}


def construir(script, planilha, meses=("agosto", "setembro")):
    fontes = [{"arquivo": Path(p).name, "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in [script, planilha]]
    evidence = collections.defaultdict(list)
    def add(sigla, categoria, origem):
        categoria = ALIASES.get(categoria, categoria)
        if categoria in CATEGORIAS:
            evidence[sigla].append({"categoria": categoria, "origem": origem})
    text = Path(script).read_text(encoding="utf-8")
    # Mantém números de linha; comandos do Colab não são executados.
    tree = ast.parse("\n".join("# " + l if l.lstrip().startswith("!") else l for l in text.splitlines()))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict): continue
        try: d = ast.literal_eval(node.value)
        except (ValueError, TypeError): continue
        for k,v in d.items():
            if isinstance(v, str): add(k,v,f"{Path(script).name}:{node.lineno}")
            elif isinstance(v,list):
                for sigla in v: add(sigla,k,f"{Path(script).name}:{node.lineno}")
    abas = ler_planilha(planilha)
    for n,row in abas["Legenda_Cursos_Status"].items():
        if "A" in row and "B" in row: add(row["A"], row["B"], f"Legenda_Cursos_Status!A{n}:B{n}")
    registros = [r for mes in meses for r in historico(abas,mes)]
    for r in registros:
        cs = cursos_do_registro(r["Curso"])
        if cs and all(cs) and len(set(cs)) == 1:
            add(cs[0],r["STATUS_CURSO"],f"{r['aba']}!B{r['linha_excel']}:H{r['linha_excel']}")
    siglas = {}
    for s,ev in sorted(evidence.items()):
        cats = sorted({e["categoria"] for e in ev})
        siglas[s] = {"categoria": cats[0] if len(cats)==1 else None, "conflito": len(cats)>1, "candidatas": cats, "evidencias": ev,
                     "base": "somente histórico" if all("!" in e["origem"] and not e["origem"].startswith("Legenda") for e in ev) else "script/legenda e observações disponíveis"}
    combos = collections.defaultdict(list); multi = collections.defaultdict(list)
    for r in registros:
        cs = cursos_do_registro(r["Curso"])
        cats = sorted({siglas[c]["categoria"] for c in cs if c in siglas and siglas[c]["categoria"]})
        if not cs or not all(c in siglas and siglas[c]["categoria"] for c in cs): continue
        esperado = cats[0] if len(cats)==1 else "Múltiplas categorias"
        ev = {"origem": f"{r['aba']}!B{r['linha_excel']}:H{r['linha_excel']}", "cursos":r["Curso"], "historico":r["STATUS_CURSO"], "categorias":cats}
        if r["STATUS_CURSO"] != esperado: combos["|".join(sorted(set(cs)))].append(ev)
        if len(cats)>1: multi["|".join(cats)].append(ev)
    validas = {k:v for k,v in multi.items() if all(e["historico"]=="Múltiplas categorias" for e in v)}
    return {"versao":"observacional-v1", "meses_evidencia":list(meses), "fontes":fontes, "siglas":siglas,
            "combinacoes_conflitantes":dict(combos), "multiplas_validadas":validas,
            "multiplas_sem_consenso":{k:v for k,v in multi.items() if k not in validas}}


def main():
    p=argparse.ArgumentParser(); p.add_argument("script",type=Path); p.add_argument("planilha",type=Path)
    p.add_argument("--saida",type=Path,required=True); p.add_argument("--meses",nargs="+",choices=list(ABAS),default=list(ABAS))
    a=p.parse_args(); regras=construir(a.script,a.planilha,a.meses)
    with a.saida.open("x",encoding="utf-8") as f: json.dump(regras,f,ensure_ascii=False,indent=2)

if __name__=="__main__": main()
