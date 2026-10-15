"""Biblioteca persistente de regras confirmadas, compatibilidade histórica e cursos sem regra final."""
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


def usar_compatibilidade_historica(competencia, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    return competencia in set(biblioteca.get("competencias_historicas_compatibilidade", []))


def curso_reconhecido_sem_regra_status(curso, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    return curso in biblioteca.get("codigos_curso_confirmados_sem_regra_status", {})


def origem_biblioteca(curso, biblioteca=None, permitir_historico=False):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    if curso in biblioteca.get("confirmados_negocio", {}):
        return "negocio_confirmado"
    if permitir_historico and curso in biblioteca.get("mapeamentos_historicos_compatibilidade", {}):
        return "compatibilidade_historica"
    if permitir_historico and curso in biblioteca.get("mapeamentos_siglas", {}):
        return "biblioteca_legada"
    if curso_reconhecido_sem_regra_status(curso, biblioteca):
        return "curso_confirmado_sem_regra_status"
    return None


def categoria_biblioteca(curso, biblioteca=None, permitir_historico=False):
    """Regras confirmadas valem sempre; histórico só nas competências autorizadas."""
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    confirmados = biblioteca.get("confirmados_negocio", {})
    if curso in confirmados:
        return confirmados[curso]
    if permitir_historico:
        historicos = biblioteca.get("mapeamentos_historicos_compatibilidade", {})
        if curso in historicos:
            return historicos[curso]
        return biblioteca.get("mapeamentos_siglas", {}).get(curso)
    return None


def combinacao_biblioteca(cursos, biblioteca=None, permitir_historico=False):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    if not permitir_historico:
        return None
    chave = chave_combinacao(cursos)
    historicas = biblioteca.get("combinacoes_historicas_compatibilidade", {})
    if chave in historicas:
        return historicas[chave]
    return biblioteca.get("combinacoes_exatas", {}).get(chave)


def resumo_execucao(auditoria, biblioteca=None):
    biblioteca = carregar_biblioteca() if biblioteca is None else biblioteca
    desconhecidas = Counter()
    sem_regra_status = Counter()
    confirmadas = Counter()
    historicas = Counter()
    combinacoes = Counter()
    for item in auditoria:
        for curso in item.get("cursos_mapeados", []):
            sigla = curso.get("curso", "")
            origem = curso.get("origem_biblioteca")
            if origem == "negocio_confirmado":
                confirmadas[sigla] += 1
            elif origem in {"compatibilidade_historica", "biblioteca_legada"}:
                historicas[sigla] += 1
            elif origem == "curso_confirmado_sem_regra_status":
                sem_regra_status[sigla] += 1
            if curso.get("categoria") is None and sigla and origem != "curso_confirmado_sem_regra_status":
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
        "cursos_confirmados_sem_regra_status": [
            {"sigla": sigla, "ocorrencias": qtd} for sigla, qtd in sorted(sem_regra_status.items())
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
