"""Classificação operacional de STATUS_CURSO com legenda + biblioteca de divergências.

A classificação por legenda/biblioteca é provisória enquanto o cálculo empresarial
completo da situação do aluno não estiver reconstruído.
"""
import argparse
import copy
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from biblioteca import (
    carregar_biblioteca,
    categoria_biblioteca,
    combinacao_biblioteca,
    curso_reconhecido_sem_regra_status,
    origem_biblioteca,
    resumo_execucao,
    usar_compatibilidade_historica,
)
from referencia import competencia_operacional, consolidar_classificacao, referencia_visual


def carregar_regras(caminho=None):
    caminho = Path(caminho or Path(__file__).with_name("regras_status_curso.json"))
    return json.loads(caminho.read_text(encoding="utf-8"))


def normalizar_chave_curso(valor):
    """Chave de comparação tolerante a acentos, caixa e espaços.

    A escrita original do curso continua preservada no registro/exportação.
    """
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().upper()


def _chave_equivalente(mapa, valor):
    if valor in mapa:
        return valor
    alvo = normalizar_chave_curso(valor)
    for chave in mapa:
        if normalizar_chave_curso(chave) == alvo:
            return chave
    return None


def _chave_biblioteca_equivalente(curso, biblioteca, permitir_historico=False):
    nomes = ["confirmados_negocio", "codigos_curso_confirmados_sem_regra_status"]
    if permitir_historico:
        nomes.extend(["mapeamentos_historicos_compatibilidade", "mapeamentos_siglas"])
    for nome in nomes:
        chave = _chave_equivalente(biblioteca.get(nome, {}), curso)
        if chave is not None:
            return chave
    return curso


def cursos_do_registro(valor):
    # O relatório observado separa cursos por vírgula. Não inferimos outros delimitadores.
    if not isinstance(valor, str):
        return []
    return [unicodedata.normalize("NFC", parte.strip()).upper() for parte in valor.split(",")]


def normalizar_categoria(valor, regras=None):
    regras = carregar_regras() if regras is None else regras
    if valor is None:
        return None
    texto = normalizar_chave_curso(valor).replace("_", " ")
    aliases = {
        "GRAD": "GRADUAÇÃO", "GRADUACAO": "GRADUAÇÃO",
        "DI": "DI",
        "POS": "POS", "POS GRAD": "POS", "POS-GRAD": "POS",
        "POS GRADUACAO": "POS", "POS-GRADUACAO": "POS",
        "MBA": "MBA", "MESTRADO": "MESTRADO",
        "APERF": "APERFEIÇOAMENTO", "APERFEICOAMENTO": "APERFEIÇOAMENTO",
        "CURSO LIVRE": "CURSO LIVRE",
        "NAO LOCALIZADO": "NÃO LOCALIZADO",
        "NAO MAPEADO": "NÃO LOCALIZADO",
        "NAO LOCALIZADO/NAO MAPEADO": "NÃO LOCALIZADO",
        "MULTIPLAS CATEGORIAS": "MÚLTIPLAS CATEGORIAS",
    }
    if texto in aliases:
        return aliases[texto]
    codigos = regras.get("categorias", {})
    chave = _chave_equivalente(codigos, str(valor).strip().upper())
    if chave is not None:
        return normalizar_categoria(codigos[chave], regras)
    return unicodedata.normalize("NFC", str(valor).strip().upper())


def classificar_registro(registro, regras=None, biblioteca=None, permitir_historico=False):
    regras = carregar_regras() if regras is None else regras
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    original = registro.get("Curso")
    cursos = cursos_do_registro(original)
    motivos, mapeados, desconhecidos, sem_regra_status = [], [], [], []

    if not cursos or any(not curso for curso in cursos):
        motivos.append("Curso ausente, inválido ou item vazio")

    for curso in cursos:
        if not curso:
            continue
        chave_legenda = _chave_equivalente(regras.get("siglas", {}), curso)
        codigo_legenda = regras.get("siglas", {}).get(chave_legenda) if chave_legenda is not None else None
        categoria_direta = normalizar_categoria(curso, regras)
        categorias_diretas = {
            "GRADUAÇÃO", "DI", "POS", "MBA", "MESTRADO",
            "APERFEIÇOAMENTO", "CURSO LIVRE",
        }
        if categoria_direta not in categorias_diretas:
            categoria_direta = None
        categoria_legenda = (
            normalizar_categoria(codigo_legenda, regras)
            if codigo_legenda else categoria_direta
        )
        curso_biblioteca = _chave_biblioteca_equivalente(curso, biblioteca, permitir_historico)
        categoria_excecao = categoria_biblioteca(curso_biblioteca, biblioteca, permitir_historico)
        origem_excecao = origem_biblioteca(curso_biblioteca, biblioteca, permitir_historico)
        if categoria_excecao:
            categoria = normalizar_categoria(categoria_excecao, regras)
            fonte = "biblioteca"
        else:
            categoria = categoria_legenda
            fonte = "legenda" if codigo_legenda else "alias_categoria" if categoria_direta else None
        if categoria is None:
            if curso_reconhecido_sem_regra_status(curso_biblioteca, biblioteca):
                # É um código real conhecido. Ele só vira divergência se, sozinho,
                # não houver nenhuma categoria sustentada pelos demais códigos do registro.
                sem_regra_status.append(curso)
            else:
                desconhecidos.append(curso)
                motivos.append("Curso não localizado na legenda nem nas regras confirmadas: " + curso)
        mapeados.append({
            "curso": curso,
            "categoria": categoria,
            "categoria_legenda": categoria_legenda,
            "fonte": fonte,
            "origem_biblioteca": origem_excecao,
            "referencia_regra": (
                "biblioteca.confirmados_negocio." + curso if origem_excecao == "negocio_confirmado" else
                "biblioteca.compatibilidade_historica." + curso if origem_excecao in {"compatibilidade_historica", "biblioteca_legada"} else
                "biblioteca.codigos_curso_confirmados_sem_regra_status." + curso if origem_excecao == "curso_confirmado_sem_regra_status" else
                "Legenda_Cursos_Status." + (chave_legenda or curso) if fonte == "legenda" else
                "Alias_Categoria." + normalizar_chave_curso(curso) if fonte == "alias_categoria" else None
            ),
        })

    categorias = sorted({m["categoria"] for m in mapeados if m["categoria"]})
    cursos_validos = [curso for curso in cursos if curso]
    override_combinacao = (
        combinacao_biblioteca(cursos_validos, biblioteca, permitir_historico)
        if cursos_validos else None
    )

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

    if sem_regra_status and not categorias and not override_combinacao:
        motivos.append(
            "Código de curso reconhecido, mas sem categoria STATUS_CURSO determinada: "
            + ", ".join(sem_regra_status)
        )

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
        "cursos_sem_regra_status": list(dict.fromkeys(sem_regra_status)),
    }


def classificar_resultado(resultado, regras=None, biblioteca=None):
    regras = carregar_regras() if regras is None else regras
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    competencia_fatura = resultado.get("metadados", {}).get("competencia_fatura", "")
    competencia = competencia_operacional(competencia_fatura)
    permitir_historico = usar_compatibilidade_historica(competencia, biblioteca)
    auditoria = [
        classificar_registro(r, regras, biblioteca, permitir_historico)
        for r in resultado["registros"]
    ]
    referencia = referencia_visual(competencia_fatura)
    consolidacao = consolidar_classificacao(auditoria)
    biblioteca_resumo = resumo_execucao(auditoria, biblioteca)
    return {
        "versao_regras": regras["versao"],
        "versao_biblioteca": biblioteca.get("versao", ""),
        "fontes": [regras.get("fonte", "Legenda_Cursos_Status"), biblioteca.get("fonte", "Biblioteca operacional")],
        "status_classificacao": "PROVISORIA_ENQUANTO_CALCULO_EMPRESARIAL_PENDENTE",
        "sha256_regras": hashlib.sha256(
            json.dumps(regras, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "sha256_biblioteca": hashlib.sha256(
            json.dumps(biblioteca, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "metadados_extracao": copy.deepcopy(resultado.get("metadados", {})),
        "conferencia_extracao": copy.deepcopy(resultado.get("conferencia", [])),
        "competencia_operacional": competencia,
        "modo_compatibilidade_historica": permitir_historico,
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
