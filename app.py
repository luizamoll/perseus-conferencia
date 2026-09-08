"""Interface local. Execute: python app.py. Processamento separado em perseus.py."""
from __future__ import annotations

import argparse
import json
import secrets
import threading
import uuid
from datetime import datetime, timezone
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from perseus import extrair, salvar
from classificacao import classificar_resultado
from exportacao import nome_excel, nome_pdf
from pdf_alunos import nome_pdf_alunos, salvar_pdf_alunos
from apresentacao import divergencias, resumo_resultado
from biblioteca import registrar_nao_localizados

BASE = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
TRABALHOS = {}
TRAVA = threading.Lock()
MAX_UPLOAD = 80 * 1024 * 1024


def processar(job, arquivo, pasta):
    def progresso(pagina, total, registros):
        with TRAVA:
            job.update(pagina=pagina, paginas_pdf=total, registros=registros, etapa="Lendo e conferindo tabelas")
    try:
        resultado = extrair(arquivo, progresso=progresso)
        resultado["metadados"]["arquivo"] = job["arquivo"]
        resultado["metadados"].update(execucao=job.get("id") or uuid.uuid4().hex, processado_em=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        resultado["classificacao"] = classificar_resultado(resultado)
        biblioteca_resumo = resultado["classificacao"].get("biblioteca", {})
        registrar_nao_localizados(
            biblioteca_resumo,
            resultado["classificacao"].get("competencia_operacional", resultado["metadados"].get("competencia_fatura", "")),
        )
        resumo = resumo_resultado(resultado)
        pendencias = divergencias(resultado)
        revisoes_classificacao = sum(a["status_final"] == "REVISAR" for a in resultado["classificacao"]["auditoria"])
        destino = pasta / "resultado"
        with TRAVA:
            job.update(etapa="Preparando Excel e relatórios PDF", registros=len(resultado["registros"]))
        salvar(resultado, destino)
        (destino / "biblioteca_divergencias.json").write_text(
            json.dumps(biblioteca_resumo, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        pdf = nome_pdf(resultado)
        excel = nome_excel(resultado)
        pdf_alunos = nome_pdf_alunos(resultado)
        salvar_pdf_alunos(resultado, destino / pdf_alunos)
        with zipfile.ZipFile(pasta / "resultado.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in destino.iterdir():
                z.write(p, p.name)
        classificacao = resultado["classificacao"]
        with TRAVA:
            job.update(
                estado="concluido",
                registros=len(resultado["registros"]),
                conferencia=resultado["conferencia"],
                metadados=resultado["metadados"],
                excel=excel,
                pdf=pdf,
                pdf_alunos=pdf_alunos,
                resumo=resumo,
                divergencias=pendencias,
                casos_revisao=sum(r["Registros para revisão"] for r in resumo),
                total_pendencias=len(pendencias),
                alertas=len(resultado["revisao"]),
                revisoes_classificacao=revisoes_classificacao,
                referencia=classificacao.get("referencia", {}),
                consolidacao=classificacao.get("consolidacao", []),
                competencia_operacional=classificacao.get("competencia_operacional", ""),
                biblioteca=classificacao.get("biblioteca", {}),
                amostra=[{k:v for k,v in r.items() if k != "Células originais"} for r in resultado["registros"][:10]],
            )
    except Exception as exc:
        with TRAVA:
            job.update(estado="erro", erro=(str(exc) if isinstance(exc, ValueError) else "Não foi possível concluir a leitura ou salvar os resultados. Verifique se o PDF abre sem senha e se há espaço na pasta de resultados. Tente novamente."), detalhe=f"{type(exc).__name__}: {exc}")


class Servidor(ThreadingHTTPServer):
    daemon_threads = True


class Pagina(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def responder(self, status, dados, tipo="application/json; charset=utf-8", nome=None):
        if not isinstance(dados, bytes):
            dados = json.dumps(dados, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        if nome:
            self.send_header("Content-Disposition", f'attachment; filename="{nome}"')
        self.end_headers()
        self.wfile.write(dados)

    def host_valido(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self.host_valido():
            return self.responder(403, {"erro": "Acesse pelo endereço local informado pelo programa."})
        path = urlparse(self.path).path
        if path in ("/", "/app.js", "/style.css"):
            nome, tipo = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}[path]
            return self.responder(200, (BASE / "interface" / nome).read_bytes(), tipo)
        if path == "/api/sessao":
            return self.responder(200, {"token": TOKEN})
        if path.startswith("/api/trabalho/"):
            with TRAVA:
                job = TRABALHOS.get(path.split("/")[-1])
                copia = dict(job) if job else None
            return self.responder(200 if copia else 404, copia or {"erro": "Processamento não encontrado nesta sessão."})
        partes = path.strip("/").split("/")
        if len(partes) == 3 and partes[0] == "download":
            id_job, nome = partes[1:]
            with TRAVA:
                job = TRABALHOS.get(id_job)
            permitidos = {"alunos.xlsx", "alunos.csv", "conferencia.csv", "revisao.csv", "resultado.json", "biblioteca_divergencias.json", "resultado.zip"}
            if job and job.get("excel"):
                permitidos.add(job["excel"])
            if job and job.get("pdf"):
                permitidos.add(job["pdf"])
            if job and job.get("pdf_alunos"):
                permitidos.add(job["pdf_alunos"])
            if not job or job["estado"] != "concluido" or nome not in permitidos:
                return self.responder(404, {"erro": "Resultado indisponível."})
            arquivo = self.server.destino / id_job / (nome if nome.endswith(".zip") else "resultado/" + nome)
            if not arquivo.is_file():
                return self.responder(404, {"erro": "Arquivo indisponível."})
            tipo = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if nome.endswith(".xlsx") else "application/pdf" if nome.endswith(".pdf") else "application/zip" if nome.endswith(".zip") else "text/csv; charset=utf-8" if nome.endswith(".csv") else "application/json"
            return self.responder(200, arquivo.read_bytes(), tipo, nome)
        return self.responder(404, {"erro": "Página não encontrada."})

    def do_POST(self):
        origem = self.headers.get("Origin")
        if (not self.host_valido() or self.headers.get("X-Local-Token") != TOKEN
                or (origem and origem != f"http://127.0.0.1:{self.server.server_port}")):
            return self.responder(403, {"erro": "Sessão inválida. Atualize a página."})
        if self.path != "/api/processar":
            return self.responder(404, {"erro": "Operação não encontrada."})
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tamanho = 0
        if not 0 < tamanho <= MAX_UPLOAD:
            return self.responder(413, {"erro": "Selecione um PDF com até 80 MB."})
        with TRAVA:
            if any(j["estado"] in ("recebendo", "processando") for j in TRABALHOS.values()):
                return self.responder(409, {"erro": "Há um PDF sendo processado. Aguarde a conclusão."})
            id_job = uuid.uuid4().hex
            nome = Path(unquote(self.headers.get("X-Filename", "relatorio.pdf")).replace("\\", "/")).name[:180]
            job = {"id": id_job, "estado": "recebendo", "arquivo": nome, "pagina": 0, "paginas_pdf": 0, "registros": 0}
            TRABALHOS[id_job] = job
        try:
            dados = self.rfile.read(tamanho)
            if len(dados) != tamanho or not dados.startswith(b"%PDF-"):
                raise ValueError("O arquivo selecionado não é um PDF válido.")
            pasta = self.server.destino / id_job
            pasta.mkdir(parents=True, exist_ok=False)
            arquivo = pasta / "entrada.pdf"
            arquivo.write_bytes(dados)
            with TRAVA:
                job["estado"] = "processando"
            threading.Thread(target=processar, args=(job, arquivo, pasta), daemon=True).start()
            self.responder(202, {"id": id_job})
        except Exception as exc:
            with TRAVA:
                job.update(estado="erro", erro=str(exc))
            self.responder(400, {"erro": str(exc)})


def main():
    parser = argparse.ArgumentParser(description="Abre a interface local de conferência Perseus.")
    parser.add_argument("--porta", type=int, default=8878)
    parser.add_argument("--sem-abrir", action="store_true")
    parser.add_argument("--resultados", type=Path, default=BASE / "resultados")
    args = parser.parse_args()
    servidor = Servidor(("127.0.0.1", args.porta), Pagina)
    servidor.destino = args.resultados.resolve()
    url = f"http://127.0.0.1:{servidor.server_port}"
    print(f"Conferência Perseus: {url}\nMantenha esta janela aberta enquanto usa o sistema. Ctrl+C encerra.", flush=True)
    if not args.sem_abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
