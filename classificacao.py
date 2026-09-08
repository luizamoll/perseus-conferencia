"""Classificação operacional de STATUS_CURSO com legenda + biblioteca de divergências."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

from biblioteca import (
    carregar_biblioteca,
    categoria_biblioteca,
    combinacao_biblioteca,
    resumo_execucao,
)
from referencia import competencia_operacional, consolidar_classificacao, referencia_visual


def carregar_regras(caminho=None):
    caminho = Path(caminho or Path(__file__).with_name("regras_status_curso.json"))
    return json.loads(caminho.read_text(encoding="utf-8"))


def cursos_do_registro(valor):
    # O relatório observado separa cursos por vírgula. Não inferimos outros delimitadores.
    if not isinstance(valor, str):
        return []
    return [parte.strip().upper() for parte in valor.split(",")]


def normalizar_categoria(valor, regras=None):
    regras = carregar_regras() if regras is None else regras
    if valor is None:
        return None
    texto = str(valor).strip().upper().replace("_", " ")
    aliases = {
        "GRAD": "GRADUAÇÃO", "GRADUAÇÃO": "GRADUAÇÃO", "GRADUACAO": "GRADUAÇÃO",
        "DI": "DI", "POS": "POS", "PÓS": "POS",
        "MBA": "MBA", "MESTRADO": "MESTRADO",
        "APERF": "APERFEIÇOAMENTO", "APERFEIÇOAMENTO": "APERFEIÇOAMENTO",
        "APERFEICOAMENTO": "APERFEIÇOAMENTO",
        "CURSO LIVRE": "CURSO LIVRE", "CURSO_LIVRE": "CURSO LIVRE",
        "NÃO LOCALIZADO": "NÃO LOCALIZADO", "NAO LOCALIZADO": "NÃO LOCALIZADO",
        "NÃO MAPEADO": "NÃO LOCALIZADO", "NAO MAPEADO": "NÃO LOCALIZADO",
        "NÃO LOCALIZADO/NÃO MAPEADO": "NÃO LOCALIZADO",
        "MÚLTIPLAS CATEGORIAS": "MÚLTIPLAS CATEGORIAS",
        "MULTIPLAS CATEGORIAS": "MÚLTIPLAS CATEGORIAS",
    }
    if texto in aliases:
        return aliases[texto]
    codigos = regras.get("categorias", {})
    if texto in codigos:
        return normalizar_categoria(codigos[texto], regras)
    return texto


def classificar_registro(registro, regras=None, biblioteca=None):
    regras = carregar_regras() if regras is None else regras
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    original = registro.get("Curso")
    cursos = cursos_do_registro(original)
    motivos, mapeados, desconhecidos = [], [], []

    if not cursos or any(not curso for curso in cursos):
        motivos.append("Curso ausente, inválido ou item vazio")

    for curso in cursos:
        if not curso:
            continue
        codigo_legenda = regras.get("siglas", {}).get(curso)
        categoria_legenda = normalizar_categoria(codigo_legenda, regras) if codigo_legenda else None
        categoria_excecao = categoria_biblioteca(curso, biblioteca)
        if categoria_excecao:
            categoria = normalizar_categoria(categoria_excecao, regras)
            fonte = "biblioteca"
        else:
            categoria = categoria_legenda
            fonte = "legenda" if categoria_legenda else None
        if categoria is None:
            desconhecidos.append(curso)
            motivos.append("Curso não localizado na legenda nem na biblioteca: " + curso)
        mapeados.append({
            "curso": curso,
            "categoria": categoria,
            "categoria_legenda": categoria_legenda,
            "fonte": fonte,
            "referencia_regra": (
                "biblioteca.mapeamentos_siglas." + curso if fonte == "biblioteca" else
                "Legenda_Cursos_Status." + curso if fonte == "legenda" else None
            ),
        })

    categorias = sorted({m["categoria"] for m in mapeados if m["categoria"]})
    cursos_validos = [curso for curso in cursos if curso]
    override_combinacao = combinacao_biblioteca(cursos_validos, biblioteca) if cursos_validos else None

    if override_combinacao and not any(not curso for curso in cursos):
        categoria_final = normalizar_categoria(override_combinacao, regras)
        fonte_final = "biblioteca_combinacao"
    elif len(categorias) == 1:
        categoria_final = categorias[0]
        fonte_final = "categorias_mapeadas"
    elif len(categorias) > 1:
        categoria_final = "MÚLTIPLAS CATEGORIAS"
        fonte_final = "categorias_mapeadas"
    else:
        categoria_final = "NÃO LOCALIZADO"
        fonte_final = "sem_mapeamento"

    # Uma sigla desconhecida não apaga a categoria sustentada pelas demais siglas,
    # mas continua visível para revisão e entra na biblioteca local de divergências.
    status_final = "REVISAR" if motivos else "CLASSIFICADO"
    if not cursos_validos:
        categoria_final = "NÃO LOCALIZADO"
        status_final = "REVISAR"

    return {
        "registro_original": copy.deepcopy(registro),
        "cursos_originais": original,
        "cursos_lista": cursos_validos,
        "cursos_mapeados": mapeados,
        "categorias_mapeadas": categorias,
        "categoria_final": categoria_final,
        "fonte_categoria_final": fonte_final,
        "status_final": status_final,
        "motivos_revisao": list(dict.fromkeys(motivos)),
        "siglas_nao_localizadas": list(dict.fromkeys(desconhecidos)),
    }


def classificar_resultado(resultado, regras=None, biblioteca=None):
    regras = carregar_regras() if regras is None else regras
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    auditoria = [classificar_registro(r, regras, biblioteca) for r in resultado["registros"]]
    competencia_fatura = resultado.get("metadados", {}).get("competencia_fatura", "")
    competencia = competencia_operacional(competencia_fatura)
    referencia = referencia_visual(competencia_fatura)
    consolidacao = consolidar_classificacao(auditoria)
    biblioteca_resumo = resumo_execucao(auditoria, biblioteca)
    return {
        "versao_regras": regras["versao"],
        "versao_biblioteca": biblioteca.get("versao", ""),
        "fontes": [regras.get("fonte", "Legenda_Cursos_Status"), biblioteca.get("fonte", "Biblioteca operacional")],
        "sha256_regras": hashlib.sha256(
            json.dumps(regras, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "sha256_biblioteca": hashlib.sha256(
            json.dumps(biblioteca, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "metadados_extracao": copy.deepcopy(resultado.get("metadados", {})),
        "conferencia_extracao": copy.deepcopy(resultado.get("conferencia", [])),
        "competencia_operacional": competencia,
        "referencia": referencia,
        "consolidacao": consolidacao,
        "biblioteca": biblioteca_resumo,
        "auditoria": auditoria,
    }


def salvar_auditoria(resultado, pasta):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=False)
    (pasta / "auditoria.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    campos = [
        "registro", "identificador", "pagina", "linha", "cursos_originais",
        "cursos_mapeados", "categorias_mapeadas", "categoria_final", "status_final",
        "motivos_revisao", "status_historico", "comparacao", "celula_historica",
    ]
    with (pasta / "auditoria.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        for i, a in enumerate(resultado["auditoria"], 1):
            r = a["registro_original"]
            row = {k: a.get(k) for k in campos}
            row.update(
                registro=i,
                identificador=r.get("Identificador"),
                pagina=r.get("Página"),
                linha=r.get("Linha"),
            )
            h = a.get("historico", {})
            row.update(
                status_historico=h.get("STATUS_CURSO"),
                comparacao=a.get("comparacao"),
                celula_historica=(str(h.get("aba")) + "!H" + str(h.get("linha_excel"))) if h else None,
            )
            for k, v in row.items():
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, ensure_ascii=False)
                if isinstance(v, str) and v.startswith(("=", "+", "-", "@")):
                    v = "'" + v
                row[k] = v
            w.writerow(row)


def main():
    p = argparse.ArgumentParser(description="Classifica resultado.json pela legenda e biblioteca operacional")
    p.add_argument("resultado", type=Path)
    p.add_argument("--saida", required=True, type=Path)
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
