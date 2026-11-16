"""Regras de competência e consolidação por STATUS_CURSO.

As categorias e cores reproduzem a estrutura operacional observada na planilha
"Fatura Perseus - SET 1.xlsx". O motor de extração não depende deste módulo.
"""
from collections import Counter
import re

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

CATEGORIAS_REFERENCIA = [
    "GRADUAÇÃO",
    "MESTRADO",
    "DI",
    "MBA",
    "POS",
    "CURSO LIVRE",
    "APERFEIÇOAMENTO",
    "NÃO LOCALIZADO",
    "MÚLTIPLAS CATEGORIAS",
]

# Cores efetivas dos cabeçalhos/totais dos quadros de referência na planilha fonte.
# Os valores abaixo já consideram as cores de tema + tint aplicadas pelo Excel.
# Para meses ainda não observados, usa-se um neutro institucional.
CORES_REFERENCIA = {
    2: "C2F1C8",  # Fevereiro
    3: "FBE3D6",  # Março
    4: "F9F9F9",  # Abril
    5: "C2F1C8",  # Maio
    6: "F2AA84",  # Junho
    7: "F9F9F9",  # Julho
    8: "C04F15",  # Agosto
    9: "E59EDD",  # Setembro
}
COR_REFERENCIA_PADRAO = "E7EFEA"

# A planilha histórica usa estes nomes de COMPETENCIA em 2026.
COMPETENCIAS_2026 = {
    2: "Fatura_Final_Ref_Fevereiro_2026",
    3: "Fatura_Final_Ref_Março_2026",
    4: "Fatura_Final_Ref_Abril_2026",
    5: "Fatura_Final_Ref_Maio_2026",
    6: "Fatura_Final_Ref_Junho_2026",
    7: "Fatura_Final_Ref_Julho_2026",
    8: "Fatura_Final_Ref_Agosto_2026",
    9: "Fatura_Final_Ref_Setembro",
}


def dados_competencia(valor):
    m = re.fullmatch(r"(\d{4})/(0[1-9]|1[0-2])", str(valor or ""))
    if not m:
        return None
    return int(m[1]), int(m[2])


def competencia_operacional(valor):
    dados = dados_competencia(valor)
    if not dados:
        return ""
    ano, mes = dados
    if ano == 2026 and mes in COMPETENCIAS_2026:
        return COMPETENCIAS_2026[mes]
    return f"Fatura_Final_Ref_{MESES[mes-1]}_{ano}"


def referencia_visual(valor):
    dados = dados_competencia(valor)
    if not dados:
        return {"titulo": "Referência", "mes": "", "ano": "", "cor": COR_REFERENCIA_PADRAO}
    ano, mes = dados
    return {
        "titulo": f"Referência {MESES[mes-1]}",
        "mes": MESES[mes-1],
        "ano": ano,
        "cor": CORES_REFERENCIA.get(mes, COR_REFERENCIA_PADRAO),
    }


def consolidar_classificacao(auditoria):
    contagem = Counter((a.get("categoria_final") or "NÃO LOCALIZADO") for a in auditoria)
    linhas = [{"categoria": categoria, "quantidade": contagem.get(categoria, 0)}
              for categoria in CATEGORIAS_REFERENCIA]
    return linhas


def total_consolidado(consolidacao):
    return sum(int(item.get("quantidade", 0)) for item in consolidacao)
