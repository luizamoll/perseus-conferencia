"""Comparação por registro e identificador; nunca altera as regras para fechar totais."""
import argparse
import collections
import json
import re
from pathlib import Path
from classificacao import carregar_regras, classificar_resultado, salvar_auditoria
from evidencia_classificacao import ler_planilha, historico


def comparar(resultado, historicos, regras):
    saida = classificar_resultado(resultado,regras)
    index = collections.defaultdict(list)
    for h in historicos:
        m = re.search(r"\(([^()]*)\)\s*$",h["Aluno"] or "")
        index[m[1].strip() if m else ""].append(h)
    ids = collections.Counter(r.get("Identificador", "") for r in resultado["registros"])
    cont = collections.Counter(); motivos=collections.Counter(); padroes=collections.Counter()
    for a in saida["auditoria"]:
        r=a["registro_original"]; ident=r.get("Identificador", ""); hs=index.get(ident,[])
        if not ident or len(hs)!=1 or ids[ident]!=1:
            a["comparacao"]="SEM_PAREAMENTO_UNIVOCO"; cont[a["comparacao"]]+=1; continue
        h=hs[0]; a["historico"] = h
        cursos_iguais = r["Curso"] == h["Curso"]
        a["cursos_iguais_historico"] = cursos_iguais
        a["comparacao"] = "COINCIDE" if a["categoria_final"] == h["STATUS_CURSO"] else ("REVISAO" if a["status_final"]=="REVISAR" else "DIVERGE")
        cont[a["comparacao"]]+=1
        if not cursos_iguais: cont["CURSOS_DIFERENTES"]+=1
        for motivo in a["motivos_revisao"]: motivos[motivo]+=1
        if a["comparacao"] != "COINCIDE": padroes[r["Curso"]+" → "+str(h["STATUS_CURSO"])]+=1
    resumo = {"total_pdf":len(saida["auditoria"]), "total_historico":sum(len(v) for v in index.values()),
              "historicos_sem_pdf":sum(len(v) for k,v in index.items() if k not in ids),
              "comparacao":dict(cont), "coincidencias":cont["COINCIDE"], "divergencias_classificadas":cont["DIVERGE"],
              "casos_revisao":cont["REVISAO"], "diferencas_status_incluindo_revisao":cont["DIVERGE"]+cont["REVISAO"],
              "motivos_revisao":dict(motivos), "padroes_diferentes":dict(padroes),
              "categorias_historicas":dict(collections.Counter(h["STATUS_CURSO"] for v in index.values() for h in v)),
              "categorias_novas":dict(collections.Counter(a["categoria_final"] or "REVISAR" for a in saida["auditoria"]))}
    return saida,resumo


def main():
    p=argparse.ArgumentParser();p.add_argument("planilha",type=Path);p.add_argument("extracoes",type=Path)
    p.add_argument("--regras",type=Path);p.add_argument("--saida",type=Path,required=True)
    a=p.parse_args();a.saida.mkdir(parents=True,exist_ok=False)
    abas=ler_planilha(a.planilha);regras=carregar_regras(a.regras); res={}
    for mes in ("agosto","setembro"):
        resultado=json.loads((a.extracoes/mes/"resultado.json").read_text(encoding="utf-8"))
        audit,res[mes]=comparar(resultado,list(historico(abas,mes)),regras)
        salvar_auditoria(audit,a.saida/mes)
    (a.saida/"resumo.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(res,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
