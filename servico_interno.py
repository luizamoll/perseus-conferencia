"""Protótipo da API interna Perseus, destinado EXCLUSIVAMENTE a gateway autenticado.

Não é endpoint para o navegador. A chave de serviço vive no backend, nunca no JS.
Escuta apenas 127.0.0.1. Não habilitar acesso à rede institucional sem homologação.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from app import MAX_UPLOAD, TRAVA, processar

ACTOR = re.compile(r"[A-Za-z0-9_.@-]{3,128}\Z")
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
DEFAULT_TTL = 60 * 60


class Ocupado(Exception):
    """O protótipo aceita apenas um trabalho em andamento."""


class Trabalhos:
    def __init__(self, destino: Path, *, ttl: int = DEFAULT_TTL, relogio=time.monotonic):
        self.destino = Path(destino)
        self.destino.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.trabalhos = {}
        self.trava = threading.RLock()
        self.ttl = ttl
        self.relogio = relogio

    def _expirar(self):
        agora = self.relogio()
        for job_id, job in list(self.trabalhos.items()):
            final = job.get("_finalizado_em")
            if final is not None and agora - final >= self.ttl:
                shutil.rmtree(self.destino / job_id, ignore_errors=True)
                del self.trabalhos[job_id]

    def _executar(self, job: dict, origem: Path, pasta: Path):
        try:
            # A biblioteca de divergências local NÃO deve ser compartilhada entre equipes.
            processar(job, origem, pasta, registrar_biblioteca=False)
        except Exception:
            # Não devolver detalhes internos/nomes de alunos pela API.
            with TRAVA:
                job["estado"] = "erro"
        finally:
            with self.trava:
                job["_finalizado_em"] = self.relogio()

    def criar(self, ator: str, dados: bytes, nome: str):
        with self.trava:
            self._expirar()
            if any(j.get("_finalizado_em") is None for j in self.trabalhos.values()):
                raise Ocupado()
            if len(self.trabalhos) >= 30:
                raise Ocupado()
            job_id = secrets.token_hex(16)
            pasta = self.destino / job_id
            pasta.mkdir(mode=0o700)
            origem = pasta / "entrada.pdf"
            origem.write_bytes(dados)
            job = {
                "id": job_id, "arquivo": nome, "estado": "processando",
                "pagina": 0, "paginas_pdf": 0, "registros": 0,
                "etapa": "Iniciando processamento",
                "_ator": ator, "_finalizado_em": None,
            }
            self.trabalhos[job_id] = job
            worker = threading.Thread(target=self._executar, args=(job, origem, pasta), daemon=True)
            worker.start()
            return job_id

    def consultar(self, ator: str, job_id: str):
        with self.trava:
            self._expirar()
            job = self.trabalhos.get(job_id)
            if not job or job["_ator"] != ator:
                return None
            with TRAVA:
                response = {
                    "id": job["id"], "estado": job["estado"],
                    "etapa": job.get("etapa", ""),
                    "progresso": {
                        "pagina": job.get("pagina", 0),
                        "paginas_pdf": job.get("paginas_pdf", 0),
                        "registros_extraidos": job.get("registros", 0),
                    },
                }
                if job["estado"] == "concluido":
                    response["registros"] = job.get("registros", 0)
                    response["total_pendencias"] = job.get("total_pendencias", 0)
                    response["alertas"] = job.get("alertas", 0)
                    response["arquivos"] = sorted(self._arquivos_permitidos(job))
                elif job["estado"] == "erro":
                    response["mensagem"] = "Processamento não concluído. Confira o PDF e procure o suporte."
                return response

    @staticmethod
    def _arquivos_permitidos(job: dict):
        if job.get("estado") != "concluido":
            return set()
        nomes = {"resultado.zip"}
        for campo in ("excel", "excel_mestre", "pdf", "pdf_alunos"):
            nome = job.get(campo)
            if isinstance(nome, str) and nome and nome not in (".", ".."):
                if Path(nome).name == nome and "/" not in nome and "\\" not in nome:
                    nomes.add(nome)
        return nomes

    def arquivo(self, ator: str, job_id: str, nome: str):
        with self.trava:
            self._expirar()
            job = self.trabalhos.get(job_id)
            if not job or job["_ator"] != ator:
                return None
            if nome not in self._arquivos_permitidos(job):
                return None
            caminho = self.destino / job_id / ("resultado.zip" if nome == "resultado.zip" else "resultado") / nome if nome != "resultado.zip" else self.destino / job_id / "resultado.zip"
            return caminho if caminho.is_file() else None


class Servidor(ThreadingHTTPServer):
    daemon_threads = True


class API(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        # Não logar arquivos, tokens, identificadores ou dados de alunos.
        pass

    def resposta(self, status: int, objeto: dict):
        dados = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(dados)

    def autorizar(self, *, precisa_ator=True):
        if (self.headers.get("Origin") or
                self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}"):
            self.resposta(403, {"erro": "Acesso não permitido."})
            return None
        recebido = self.headers.get("X-Perseus-Service-Key", "")
        if not hmac.compare_digest(recebido.encode("utf-8"), self.server.chave.encode("utf-8")):
            self.resposta(401, {"erro": "Serviço não autorizado."})
            return None
        if not precisa_ator:
            return ""
        ator = self.headers.get("X-UNH-Actor", "")
        if not ACTOR.fullmatch(ator):
            self.resposta(400, {"erro": "Identidade do usuário autenticado é obrigatória."})
            return None
        return ator

    def do_GET(self):
        ator = self.autorizar(precisa_ator=self.path != "/v1/saude")
        if ator is None:
            return
        rota = urlparse(self.path).path
        if rota == "/v1/saude":
            return self.resposta(200, {"estado": "operacional", "modo": "somente-loopback"})
        status = re.fullmatch(r"/v1/trabalhos/([0-9a-f]{32})", rota)
        if status:
            resultado = self.server.trabalhos.consultar(ator, status.group(1))
            return self.resposta(200, resultado) if resultado else self.resposta(404, {"erro": "Trabalho indisponível."})
        download = re.fullmatch(r"/v1/trabalhos/([0-9a-f]{32})/download/([^/]+)", rota)
        if download:
            nome = unquote(download.group(2))
            caminho = self.server.trabalhos.arquivo(ator, download.group(1), nome)
            if not caminho:
                return self.resposta(404, {"erro": "Arquivo indisponível."})
            tipo = ("application/zip" if nome.endswith(".zip")
                    else "application/pdf" if nome.endswith(".pdf")
                    else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(caminho.stat().st_size))
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(nome, safe=""))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            with caminho.open("rb") as origem:
                shutil.copyfileobj(origem, self.wfile, length=64 * 1024)
            return
        return self.resposta(404, {"erro": "Rota não encontrada."})

    def do_POST(self):
        ator = self.autorizar()
        if ator is None:
            return
        if urlparse(self.path).path != "/v1/trabalhos":
            return self.resposta(404, {"erro": "Rota não encontrada."})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/pdf":
            return self.resposta(415, {"erro": "Somente arquivos PDF são aceitos."})
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tamanho = 0
        if tamanho <= 0 or tamanho > MAX_UPLOAD:
            return self.resposta(413, {"erro": "O PDF deve ter no máximo 80 MB."})
        self.connection.settimeout(120)
        try:
            dados = self.rfile.read(tamanho)
        except (TimeoutError, OSError):
            return self.resposta(408, {"erro": "Tempo de envio excedido."})
        if len(dados) != tamanho or not dados.startswith(b"%PDF-"):
            return self.resposta(400, {"erro": "Arquivo PDF inválido."})
        nome = Path(unquote(self.headers.get("X-Filename", "relatorio.pdf")).replace("\\", "/")).name[:120]
        if not nome.lower().endswith(".pdf"):
            nome = "relatorio.pdf"
        try:
            trabalho_id = self.server.trabalhos.criar(ator, dados, nome)
        except Ocupado:
            return self.resposta(409, {"erro": "Serviço ocupado. Aguarde ou tente novamente."})
        return self.resposta(202, {"id": trabalho_id, "estado": "processando"})

def criar_servidor(porta: int, chave: str, destino: Path):
    if not chave or len(chave) < 32:
        raise ValueError("Defina PERSEUS_SERVICE_KEY com ao menos 32 caracteres aleatórios.")
    servidor = Servidor(("127.0.0.1", porta), API)
    servidor.chave = chave
    servidor.trabalhos = Trabalhos(destino)
    return servidor


def main():
    parser = argparse.ArgumentParser(description="API Perseus privada para integração backend a backend.")
    parser.add_argument("--porta", type=int, default=8879)
    args = parser.parse_args()
    chave = os.environ.get("PERSEUS_SERVICE_KEY", "")
    if not chave or len(chave) < 32:
        parser.error("PERSEUS_SERVICE_KEY não configurada (mínimo de 32 caracteres).")
    # Temporários fora do repositório; removidos após encerramento normal da API.
    with tempfile.TemporaryDirectory(prefix="perseus-interno-") as pasta:
        servidor = criar_servidor(args.porta, chave, Path(pasta))
        print(f"API Perseus interna: http://127.0.0.1:{servidor.server_port}", flush=True)
        print("Somente para backend autenticado. Ctrl+C encerra.", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            servidor.server_close()

if __name__ == "__main__":
    main()
