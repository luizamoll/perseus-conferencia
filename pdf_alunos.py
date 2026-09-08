"""PDF complementar com a lista completa de registros extraídos."""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from exportacao import nome_excel


def nome_pdf_alunos(resultado):
    return nome_excel(resultado).replace("Resultado_Perseus_", "Lista_Alunos_Perseus_").replace(".xlsx", ".pdf")


def salvar_pdf_alunos(resultado, caminho):
    meta = resultado["metadados"]
    registros = resultado["registros"]
    classificacao = resultado.get("classificacao", {})
    auditoria = classificacao.get("auditoria") or []
    competencia_operacional = classificacao.get("competencia_operacional", "")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="AlunoCell",fontName="Helvetica",fontSize=7.2,leading=9.2,textColor=colors.HexColor("#243D55")))
    styles.add(ParagraphStyle(name="AlunoHead",parent=styles["AlunoCell"],fontName="Helvetica-Bold",textColor=colors.white))
    styles.add(ParagraphStyle(name="AlunoMeta",fontName="Helvetica",fontSize=9,leading=12,textColor=colors.HexColor("#526577")))

    def para(valor, cabecalho=False):
        texto = escape(str(valor if valor is not None else "")).replace("\n", "<br/>")
        return Paragraph(texto, styles["AlunoHead" if cabecalho else "AlunoCell"])

    campos = ["Aluno","Identificador","Curso","STATUS_CURSO","COMPETENCIA","Classificação","Status Atual","Período de coleta","Página"]
    dados = [[para(campo, True) for campo in campos]]
    for indice, registro in enumerate(registros):
        audit = auditoria[indice] if indice < len(auditoria) else {}
        linha = {
            **registro,
            "STATUS_CURSO": audit.get("categoria_final") or "NÃO LOCALIZADO",
            "COMPETENCIA": competencia_operacional,
            "Classificação": audit.get("status_final") or "Não executada",
        }
        dados.append([para(linha.get(campo, "")) for campo in campos])

    doc = SimpleDocTemplate(str(caminho),pagesize=landscape(A3),leftMargin=28,rightMargin=28,topMargin=28,bottomMargin=34,title="Perseus - Lista completa de alunos",author="Perseus")
    tabela = LongTable(dados,colWidths=[210,82,170,120,170,90,105,90,42],repeatRows=1,hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243D55")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F0F4F7"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#243D55")),
    ]))

    competencia = meta.get("competencia_fatura", "—")
    periodo = registros[0].get("Período de coleta", "—") if registros else "—"
    story = [
        Paragraph("Lista completa de alunos", styles["Title"]),
        Paragraph(f"Fatura {escape(str(competencia))} · Coleta {escape(str(periodo))} · {len(registros):,} registros".replace(",", "."),styles["AlunoMeta"]),
        Paragraph(f"COMPETENCIA: {escape(str(competencia_operacional))}", styles["AlunoMeta"]),
        Paragraph(f"Documento: {escape(str(meta.get('arquivo', '')))}", styles["AlunoMeta"]),
        Spacer(1, 10),tabela,
    ]

    def rodape(canvas, documento):
        canvas.setFont("Helvetica", 8);canvas.setFillColor(colors.HexColor("#526577"))
        canvas.drawString(28, 18, f"Perseus | Fatura {competencia} | Lista completa")
        canvas.drawRightString(1160, 18, f"Página {documento.page}")

    doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
