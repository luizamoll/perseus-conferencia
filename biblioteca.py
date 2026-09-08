"""Biblioteca persistente de regras confirmadas, compatibilidade histórica e siglas não localizadas."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PASTA = BASE / "biblioteca"
MAPA = PASTA / "mapeamentos_operacionais.json"
REGISTRO_LOCAL = PASTA / "nao_localizados.json"


def carregar_biblioteca(caminho=None):
    caminho = Path(caminho or MAPA)
    return json.loads(caminho.read_text(encoding="utf-8"))


def chave_combinacao(cursos):
    return "|".join(sorted(set(cursos)))


def categoria_biblioteca(curso, biblioteca=None):
    """Retorna primeiro regra confirmada; depois compatibilidade histórica.

    Mantém leitura compatível com a versão antiga da biblioteca enquanto os
    arquivos locais ainda não forem atualizados.
    """
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    confirmados = biblioteca.get("confirmados_negocio", {})
    if curso in confirmados:
        return confirmados[curso]
    historicos = biblioteca.get("mapeamentos_historicos_compatibilidade", {})
    if curso in historicos:
        return historicos[curso]
    return biblioteca.get("mapeamentos_siglas", {}).get(curso)


def origem_biblioteca(curso, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    if curso in biblioteca.get("confirmados_negocio", {}):
        return "negocio_confirmado"
    if curso in biblioteca.get("mapeamentos_historicos_compatibilidade", {}):
        return "compatibilidade_historica"
    if curso in biblioteca.get("mapeamentos_siglas", {}):
        return "biblioteca_legada"
    return None


def combinacao_biblioteca(cursos, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    chave = chave_combinacao(cursos)
    historicas = biblioteca.get("combinacoes_historicas_compatibilidade", {})
    if chave in historicas:
        return historicas[chave]
    return biblioteca.get("combinacoes_exatas", {}).get(chave)


def resumo_execucao(auditoria, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    desconhecidas = Counter()
    confirmadas = Counter()
    historicas = Counter()
    combinacoes = Counter()
    for item in auditoria:
        for curso in item.get("cursos_mapeados", []):
            sigla = curso.get("curso", "")
            origem = origem_biblioteca(sigla, biblioteca)
            if origem == "negocio_confirmado":
                confirmadas[sigla] += 1
            elif origem in {"compatibilidade_historica", "biblioteca_legada"}:
                historicas[sigla] += 1
            if curso.get("categoria") is None and sigla:
                desconhecidas[sigla] += 1
        if item.get("fonte_categoria_final") == "biblioteca_combinacao":
            combinacoes[chave_combinacao(item.get("cursos_lista", []))] += 1
    return {
        "versao": biblioteca.get("versao", ""),
        "arquivo": "biblioteca/mapeamentos_operacionais.json",
        "regras_negocio_usadas": [
            {"sigla": sigla, "ocorrencias": qtd} for sigla, qtd in sorted(confirmadas.items())
        ],
        "excecoes_historicas_usadas": [
            {"sigla": sigla, "ocorrencias": qtd} for sigla, qtd in sorted(historicas.items())
        ],
        "siglas_operacionais_usadas": [
            {"sigla": sigla, "ocorrencias": qtd}
            for sigla, qtd in sorted((confirmadas + historicas).items())
        ],
        "combinacoes_operacionais_usadas": [
            {"combinacao": chave, "ocorrencias": qtd} for chave, qtd in sorted(combinacoes.items())
        ],
        "siglas_nao_localizadas": [
            {"sigla": sigla, "ocorrencias": qtd} for sigla, qtd in sorted(desconhecidas.items())
        ],
        "pendencias_conhecidas": biblioteca.get("pendencias_conhecidas", {}),
    }


def registrar_nao_localizados(resumo, competencia, caminho=None):
    """Acumula somente siglas/contagens; nunca grava nomes ou identificadores de alunos."""
    caminho = Path(caminho or REGISTRO_LOCAL)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists():
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            dados = {"siglas": {}}
    else:
        dados = {"siglas": {}}
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    siglas = dados.setdefault("siglas", {})
    for item in resumo.get("siglas_nao_localizadas", []):
        sigla = item["sigla"]
        qtd = int(item.get("ocorrencias", 0))
        registro = siglas.setdefault(sigla, {
            "ocorrencias_acumuladas": 0,
            "primeira_competencia": competencia,
            "ultima_competencia": competencia,
            "ultima_atualizacao_utc": agora,
        })
        registro["ocorrencias_acumuladas"] = int(registro.get("ocorrencias_acumuladas", 0)) + qtd
        registro["ultima_competencia"] = competencia
        registro["ultima_atualizacao_utc"] = agora
    dados["ultima_atualizacao_utc"] = agora
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(caminho)
    return caminho
