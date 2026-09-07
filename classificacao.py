"""Classificação observacional independente da extração e do STATUS_CURSO alvo."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path


def carregar_regras(caminho=None):
    return json.loads(Path(caminho or Path(__file__).with_name("regras_classificacao.json")).read_text(encoding="utf-8"))


def cursos_do_registro(valor):
    # Somente a vírgula está sustentada pelo formato observado. Não divide espaços/substrings.
    if not isinstance(valor, str):
        return []
    return [parte.strip().upper() for parte in valor.split(",")]


def classificar_registro(registro, regras=None):
    regras = carregar_regras() if regras is None else regras
    original = registro.get("Curso")
    cursos = cursos_do_registro(original)
    motivos, mapeados = [], []
    if not cursos or any(not c for c in cursos):
        motivos.append("Curso ausente, inválido ou item vazio")
    for curso in cursos:
        regra = regras["siglas"].get(curso)
        categoria = regra.get("categoria") if regra else None
        if curso and not categoria:
            motivos.append(("Conflito de fontes: " if regra and regra["conflito"] else "Sigla sem mapa suficiente: ") + curso)
        mapeados.append({"curso": curso, "categoria": categoria,
                         "referencia_regra": "siglas." + curso if regra else None,
                         "base": regra.get("base") if regra else None})
    categorias = sorted({m["categoria"] for m in mapeados if m["categoria"]})
    chave_cursos = "|".join(sorted(set(cursos)))
    if chave_cursos in regras["combinacoes_conflitantes"]:
        motivos.append("Combinação contradiz mapa no histórico: " + chave_cursos)
    if len(categorias) > 1 and "|".join(categorias) not in regras["multiplas_validadas"]:
        motivos.append("Conjunto de categorias sem validação histórica de múltiplas")
    categoria_proposta = categorias[0] if len(categorias) == 1 else None
    if len(categorias) > 1 and not motivos:
        categoria_proposta = "Múltiplas categorias"
    return {"registro_original": copy.deepcopy(registro), "cursos_originais": original,
            "cursos_mapeados": mapeados, "categorias_mapeadas": categorias,
            "categoria_final": categoria_proposta if not motivos else None,
            "status_final": "REVISAR" if motivos else "CLASSIFICADO",
            "motivos_revisao": list(dict.fromkeys(motivos))}


def classificar_resultado(resultado, regras=None):
    regras = carregar_regras() if regras is None else regras
    return {"versao_regras": regras["versao"], "fontes": regras["fontes"],
            "sha256_regras": hashlib.sha256(json.dumps(regras, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
            "metadados_extracao": copy.deepcopy(resultado.get("metadados", {})),
            "conferencia_extracao": copy.deepcopy(resultado.get("conferencia", [])),
            "auditoria": [classificar_registro(r, regras) for r in resultado["registros"]]}


def salvar_auditoria(resultado, pasta):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=False)
    (pasta / "auditoria.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    campos = ["registro", "identificador", "pagina", "linha", "cursos_originais", "cursos_mapeados", "categorias_mapeadas", "categoria_final", "status_final", "motivos_revisao", "status_historico", "comparacao", "celula_historica"]
    with (pasta / "auditoria.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";"); w.writeheader()
        for i, a in enumerate(resultado["auditoria"], 1):
            r = a["registro_original"]
            row = {k: a.get(k) for k in campos}
            row.update(registro=i, identificador=r.get("Identificador"), pagina=r.get("Página"), linha=r.get("Linha"))
            h = a.get("historico", {})
            row.update(status_historico=h.get("STATUS_CURSO"), comparacao=a.get("comparacao"),
                       celula_historica=(str(h.get("aba")) + "!H" + str(h.get("linha_excel"))) if h else None)
            for k,v in row.items():
                if isinstance(v, (list, dict)): v = json.dumps(v, ensure_ascii=False)
                if isinstance(v, str) and v.startswith(("=", "+", "-", "@")): v = "'" + v
                row[k] = v
            w.writerow(row)


def main():
    p = argparse.ArgumentParser(description="Classifica resultado.json do módulo 1 sem modificar a entrada")
    p.add_argument("resultado", type=Path); p.add_argument("--saida", required=True, type=Path)
    p.add_argument("--regras", type=Path)
    args = p.parse_args()
    resultado = json.loads(args.resultado.read_text(encoding="utf-8"))
    regras = carregar_regras(args.regras)
    saida = classificar_resultado(resultado, regras)
    saida["sha256_entrada"] = hashlib.sha256(args.resultado.read_bytes()).hexdigest()
    salvar_auditoria(saida, args.saida)
    print(f"{len(saida['auditoria'])} registros auditados em {args.saida}")

if __name__ == "__main__":
    main()
