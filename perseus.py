"""Protótipo de extração e conferência. Não modifica o PDF de entrada."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import pdfplumber
from exportacao import salvar_excel, salvar_pdf, nome_excel, nome_pdf
from apresentacao import resumo_resultado

CAMPOS = ["Aluno", "Curso", "Data da Coleta", "Status na Data da Coleta",
          "Status Atual", "Unidade", "Tipo de Curso"]
BLOCO = re.compile(r"(\d{2}/\d{4})\s*\((\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})\)\s*Coletado:\s*(\d+)\s+Calculado:\s*(\d+)")
CABECALHO = re.compile(r"Contrato:\s*(\S+)\s+Competência:\s*(\d{4}/\d{2})\s+Quantidade Faturada:\s*(\d+)")


def limpar(valor):
    return re.sub(r"\s+", " ", valor or "").strip()


def ler_bloco(texto):
    m = BLOCO.search(texto)
    if not m:
        return None
    periodo, inicio, fim, coletado, calculado = m.groups()
    return dict(periodo=periodo, inicio=inicio, fim=fim,
                coletado=int(coletado), calculado=int(calculado))


def validar_linha(valores, inicio, fim):
    """Aponta problemas; jamais elimina uma linha por status, data ou duplicidade."""
    problemas = []
    identificador = re.search(r"\(([^()]*)\)\s*$", valores[0])
    codigo = identificador[1].strip() if identificador else ""
    if not codigo:
        problemas.append("Aluno sem identificador final entre parênteses")
    for campo, valor in zip(CAMPOS, valores):
        if not valor:
            problemas.append(f"Campo vazio: {campo}")
    itens_data = [v.strip() for v in valores[2].split(",")]
    datas = re.findall(r"\d{2}/\d{2}/\d{4}", valores[2])
    if any(not re.fullmatch(r"\d{2}/\d{2}/\d{4}", v) for v in itens_data):
        problemas.append("Data incompleta ou texto inesperado no campo Data da Coleta")
    if not datas:
        problemas.append("Nenhuma data reconhecida")
    for data in datas:
        try:
            dt = datetime.strptime(data, "%d/%m/%Y")
            if not inicio <= dt <= fim:
                problemas.append(f"Data fora do intervalo do bloco: {data}")
        except ValueError:
            problemas.append(f"Data inválida: {data}")
    # As seis listas descrevem vínculos do mesmo registro; não são novos alunos.
    comprimentos = [len(v.split(",")) if v else 0 for v in valores[1:]]
    if len(set(comprimentos)) > 1:
        problemas.append("Quantidades diferentes de cursos/datas/status/unidades/tipos")
    return codigo, problemas


def extrair(pdf_path, periodo=None, progresso=None):
    pdf_path = Path(pdf_path)
    hash_antes = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    registros, revisao, blocos = [], [], {}
    metadados = {"arquivo": pdf_path.name, "sha256": hash_antes}
    metadados["escopo"] = "Primeiro bloco contíguo do relatório" if periodo is None else periodo
    metadados["paginas_lidas"] = 0
    alvo = periodo
    primeiro_bloco = periodo is None
    with pdfplumber.open(pdf_path) as pdf:
        metadados["paginas_pdf"] = len(pdf.pages)
        for pagina_n, pagina in enumerate(pdf.pages, 1):
            if progresso:
                progresso(pagina_n, len(pdf.pages), len(registros))
            texto = pagina.extract_text() or ""
            metadados["paginas_lidas"] = pagina_n
            if pagina_n == 1:
                m = CABECALHO.search(texto)
                if not m:
                    raise ValueError("Cabeçalho Perseus não reconhecido; nenhuma saída foi criada.")
                metadados.update(contrato=m[1], competencia_fatura=m[2], quantidade_faturada=int(m[3]))
                if alvo is None:
                    primeiro = ler_bloco(texto)
                    if not primeiro:
                        raise ValueError("Primeiro período de coleta não reconhecido.")
                    alvo = primeiro["periodo"]
            cabecalhos = list(CABECALHO.finditer(texto))
            for cab in cabecalhos:
                if (cab[1],cab[2],int(cab[3])) != (metadados["contrato"],metadados["competencia_fatura"],metadados["quantidade_faturada"]):
                    raise ValueError(f"Cabeçalhos contraditórios de contrato/competência/quantidade faturada, página {pagina_n}.")
            blocos_pagina = list(BLOCO.finditer(texto))
            periodos_pagina = {m[1] for m in blocos_pagina}
            if not periodos_pagina:
                revisao.append({"pagina": pagina_n, "tabela": "", "linha": "", "periodo": "", "motivo": "Página sem período reconhecido", "dados_originais": texto})
                pagina.close()
                continue
            if alvo != "todos" and alvo not in periodos_pagina:
                pagina.close()
                # No modo padrão, a saída é apenas o primeiro bloco contíguo.
                # Um período explícito ou "todos" percorre o relatório inteiro.
                if primeiro_bloco and blocos:
                    break
                continue
            for encontrado in blocos_pagina:
                declarado = ler_bloco(encontrado[0])
                chave = declarado["periodo"]
                if alvo != "todos" and chave != alvo:
                    continue
                anterior = blocos.get(chave)
                if anterior and any(anterior[k] != declarado[k] for k in declarado):
                    raise ValueError(f"Metadados contraditórios no período {chave}, página {pagina_n}.")
                if not anterior:
                    blocos[chave] = {**declarado, "paginas": []}
            tabelas = pagina.extract_tables()
            linhas_na_pagina = 0
            for tabela_n, tabela in enumerate(tabelas, 1):
                contexto = None
                tabela_alunos = False
                for linha_n, linha in enumerate(tabela, 1):
                    valores = [limpar(v) for v in linha]
                    bloco = ler_bloco(" ".join(valores))
                    if bloco:
                        contexto = bloco
                        continue
                    if len(valores) == 7 and valores == CAMPOS:
                        tabela_alunos = True
                        if contexto is None and len(blocos_pagina) == 1:
                            contexto = ler_bloco(blocos_pagina[0][0])
                        continue
                    if not tabela_alunos or not any(valores):
                        continue
                    if contexto is None:
                        revisao.append({"pagina": pagina_n, "tabela": tabela_n, "linha": linha_n, "periodo": "", "motivo": "Tabela de alunos sem período inequívoco", "dados_originais": linha})
                        continue
                    if alvo != "todos" and contexto["periodo"] != alvo:
                        continue
                    chave = contexto["periodo"]
                    anterior = blocos.get(chave)
                    if anterior and any(anterior[k] != contexto[k] for k in contexto):
                        raise ValueError(f"Metadados contraditórios no período {chave}, página {pagina_n}.")
                    if not anterior:
                        blocos[chave] = {**contexto, "paginas": []}
                    if pagina_n not in blocos[chave]["paginas"]:
                        blocos[chave]["paginas"].append(pagina_n)
                    if len(valores) != 7:
                        revisao.append({"pagina": pagina_n, "tabela": tabela_n, "linha": linha_n, "periodo": chave, "Aluno": valores[0] if valores else "", "motivo": f"Linha com {len(valores)} campos; esperados sete", "dados_originais": linha})
                        continue
                    codigo, problemas = validar_linha(valores, datetime.strptime(contexto["inicio"], "%d/%m/%Y"), datetime.strptime(contexto["fim"], "%d/%m/%Y"))
                    registro = {**dict(zip(CAMPOS, valores)), "Identificador": codigo,
                                "Período de coleta": chave, "Competência da fatura": metadados["competencia_fatura"],
                                "Página": pagina_n, "Tabela": tabela_n, "Linha": linha_n,
                                "Revisar": "; ".join(problemas), "Células originais": linha}
                    registros.append(registro)
                    linhas_na_pagina += 1
                    for problema in problemas:
                        revisao.append({"pagina": pagina_n, "tabela": tabela_n, "linha": linha_n, "periodo": chave, "Aluno": registro["Aluno"], "Identificador": codigo, "Curso": registro["Curso"], "motivo": problema, "dados_originais": linha})
            if not linhas_na_pagina:
                revisao.append({"pagina": pagina_n, "tabela": "", "linha": "", "periodo": alvo, "motivo": "Página do período selecionado sem linhas de alunos extraídas", "dados_originais": texto})
            if pagina_n == 1 or pagina_n % 20 == 0:
                print(f"Página {pagina_n}/{len(pdf.pages)}: {len(registros)} registros extraídos", flush=True)
            pagina.close()
    if not blocos:
        raise ValueError(f"Nenhuma tabela de alunos extraída para {alvo}.")
    contagem_ids = Counter((r["Período de coleta"], r["Identificador"]) for r in registros if r["Identificador"])
    for r in registros:
        if r["Identificador"] and contagem_ids[r["Período de coleta"], r["Identificador"]] > 1:
            motivo = "Identificador repetido no mesmo período; registro preservado"
            r["Revisar"] = "; ".join(filter(None, [r["Revisar"], motivo]))
            revisao.append({"pagina": r["Página"], "tabela": r["Tabela"], "linha": r["Linha"], "periodo": r["Período de coleta"], "Aluno": r["Aluno"], "Identificador": r["Identificador"], "Curso": r["Curso"], "motivo": motivo, "dados_originais": r["Células originais"]})
    conferencia = []
    for chave, bloco in blocos.items():
        linhas = [r for r in registros if r["Período de coleta"] == chave]
        ids = {r["Identificador"] for r in linhas if r["Identificador"]}
        conferencia.append({"Período de coleta": chave, "Início": bloco["inicio"], "Fim": bloco["fim"],
                            "Coletado informado": bloco["coletado"], "Calculado informado": bloco["calculado"],
                            "Linhas extraídas": len(linhas), "Identificadores distintos": len(ids),
                            "Diferença de linhas": len(linhas) - bloco["coletado"],
                            "Diferença de identificadores": len(ids) - bloco["coletado"],
                            "Linhas para revisar": sum(bool(r["Revisar"]) for r in linhas)})
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != hash_antes:
        raise RuntimeError("O arquivo de entrada mudou durante a leitura.")
    return {"metadados": metadados, "registros": registros, "conferencia": conferencia, "revisao": revisao}


def salvar(resultado, pasta):
    """Só aceita pasta nova: uma nova execução nunca sobrescreve resultados."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=False)
    resumo_resultado(resultado)  # valida a consistência antes de escrever os arquivos
    salvar_excel(resultado, pasta / nome_excel(resultado))
    salvar_pdf(resultado, pasta / nome_pdf(resultado))
    (pasta / "resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    for nome, linhas in [("alunos", resultado["registros"]), ("conferencia", resultado["conferencia"]), ("revisao", resultado["revisao"])]:
        if not linhas:
            continue
        campos = list(dict.fromkeys(c for linha in linhas for c in linha if c != "Células originais"))
        with (pasta / f"{nome}.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            for linha in linhas:
                # Neutraliza fórmulas ao abrir CSV no Excel; JSON preserva o original.
                writer.writerow({k: ("'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v) for k,v in linha.items()})


def main():
    parser = argparse.ArgumentParser(description="Extrai alunos do PDF Perseus e confere os totais sem alterar a entrada.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--saida", required=True, type=Path, help="Pasta nova para os resultados")
    parser.add_argument("--periodo", help="MM/AAAA, ou todos. Padrão: primeiro bloco do relatório.")
    args = parser.parse_args()
    if args.saida.exists():
        parser.error("A pasta de saída já existe. Escolha outra para preservar seus arquivos.")
    if args.periodo and args.periodo != "todos" and not re.fullmatch(r"(0[1-9]|1[0-2])/\d{4}", args.periodo):
        parser.error("Use --periodo MM/AAAA ou todos.")
    resultado = extrair(args.pdf, args.periodo)
    from classificacao import classificar_resultado
    resultado["classificacao"] = classificar_resultado(resultado)
    salvar(resultado, args.saida)
    for c in resultado["conferencia"]:
        print(f"{c['Período de coleta']}: {c['Linhas extraídas']} linhas; resumo {c['Coletado informado']}; diferença {c['Diferença de linhas']:+d}.")
    print(f"Resultado salvo em {args.saida}. Alertas para revisão: {len(resultado['revisao'])}.")


if __name__ == "__main__":
    main()
