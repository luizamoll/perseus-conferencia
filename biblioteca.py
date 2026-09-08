"""Biblioteca persistente de exceções e siglas não localizadas do Perseus."""
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
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    return biblioteca.get("mapeamentos_siglas", {}).get(curso)


def combinacao_biblioteca(cursos, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    return biblioteca.get("combinacoes_exatas", {}).get(chave_combinacao(cursos))


def resumo_execucao(auditoria, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    desconhecidas = Counter()
    overrides = Counter()
    combinacoes = Counter()
    for item in auditoria:
        for curso in item.get("cursos_mapeados", []):
            if curso.get("fonte") == "biblioteca":
                overrides[curso.get("curso", "")] += 1
            if curso.get("categoria") is None and curso.get("curso"):
                desconhecidas[curso["curso"]] += 1
        if item.get("fonte_categoria_final") == "biblioteca_combinacao":
            combinacoes[chave_combinacao(item.get("cursos_lista", []))] += 1
    return {
        "versao": biblioteca.get("versao", ""),
        "arquivo": "biblioteca/mapeamentos_operacionais.json",
        "siglas_operacionais_usadas": [
            {"sigla": sigla, "ocorrencias": qtd} for sigla, qtd in sorted(overrides.items())
        ],
        "combinacoes_operacionais_usadas": [
            {"combinacao": chave, "ocorrencias": qtd} for chave, qtd in sorted(combinacoes.items())
        ],
        "siglas_nao_localizadas": [
            {"sigla": sigla, "ocorrencias": qtd} for sigla, qtd in sorted(desconhecidas.items())
        ],
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
