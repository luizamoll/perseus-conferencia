"""Testes isolados da API interna: nenhum arquivo real de aluno."""
import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import servico_interno as api

KEY = "a" * 48
ACTOR = "ti.colaborador"


class ApiInternaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = api.criar_servidor(0, KEY, Path(self.temp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.finalizar)

    def finalizar(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def pedir(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        base = {"X-Perseus-Service-Key": KEY, "X-UNH-Actor": ACTOR}
        if headers is not None:
            base.update(headers)
        conn.request(method, path, body=body, headers=base)
        res = conn.getresponse()
        payload = res.read()
        result = (res.status, json.loads(payload) if res.getheader("Content-Type", "").startswith("application/json") else payload)
        conn.close()
        return result

    def test_credenciais_obrigatorias_e_rejeicao_de_origin(self):
        self.assertEqual(self.pedir("GET", "/v1/saude", headers={"X-Perseus-Service-Key": ""})[0], 401)
        self.assertEqual(self.pedir("GET", "/v1/saude", headers={"Origin": "http://evil.local"})[0], 403)
        self.assertEqual(self.pedir("GET", "/v1/saude", headers={"Host": "exemplo.local"})[0], 403)
        self.assertEqual(self.pedir("GET", "/v1/saude")[0], 200)
        self.assertEqual(self.pedir("GET", "/v1/trabalhos/" + "0"*32, headers={"X-UNH-Actor": ""})[0], 400)

    def test_limites_de_entrada(self):
        self.assertEqual(self.pedir("POST", "/v1/trabalhos", b"ola", {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.pedir("POST", "/v1/trabalhos", b"ola", {"Content-Type": "application/pdf"})[0], 400)
        self.assertEqual(self.pedir("POST", "/v1/trabalhos", b"", {"Content-Type": "application/pdf"})[0], 413)
        self.assertEqual(self.pedir("POST", "/v1/trabalhos", b"abc", {"Content-Type": "application/pdf", "Content-Length": str(api.MAX_UPLOAD+1)})[0], 413)

    def test_isolamento_entre_atores_e_download(self):
        def fake_processar(job, origem, pasta, *, registrar_biblioteca=True):
            self.assertFalse(registrar_biblioteca)
            pasta_resultado = pasta / "resultado"
            pasta_resultado.mkdir()
            (pasta / "resultado.zip").write_bytes(b"ZIP-ficticio")
            (pasta_resultado / "exemplo.xlsx").write_bytes(b"xlsx-sintetico")
            job.update(estado="concluido", registros=2, excel="exemplo.xlsx", total_pendencias=1,
                       alertas=1, amostra=[{"Aluno": "DADO_SIGILOSO"}],
                       metadados={"nome": "DADO_SIGILOSO"})

        with patch("servico_interno.processar", side_effect=fake_processar):
            status, response = self.pedir("POST", "/v1/trabalhos", b"%PDF-ficticio",
                                          {"Content-Type": "application/pdf", "X-Filename": "teste.pdf"})
            self.assertEqual(status, 202)
            job_id = response["id"]
            for _ in range(100):
                s, data = self.pedir("GET", f"/v1/trabalhos/{job_id}")
                if data["estado"] == "concluido":
                    break
                time.sleep(.01)
            self.assertEqual(s, 200)
            self.assertEqual(data["registros"], 2)
            self.assertIn("exemplo.xlsx", data["arquivos"])
            self.assertNotIn("DADO_SIGILOSO", json.dumps(data))
            self.assertNotIn("metadados", data)
            self.assertEqual(self.pedir("GET", f"/v1/trabalhos/{job_id}", headers={"X-UNH-Actor": "outro.usuario"})[0], 404)
            self.assertEqual(self.pedir("GET", f"/v1/trabalhos/{job_id}/download/exemplo.xlsx", headers={"X-UNH-Actor": "outro.usuario"})[0], 404)
            self.assertEqual(self.pedir("GET", f"/v1/trabalhos/{job_id}/download/entrada.pdf")[0], 404)
            self.assertEqual(self.pedir("GET", f"/v1/trabalhos/{job_id}/download/exemplo.xlsx"), (200, b"xlsx-sintetico"))
            self.assertEqual(self.pedir("GET", f"/v1/trabalhos/{job_id}/download/resultado.zip"), (200, b"ZIP-ficticio"))

    def test_rejeita_trabalho_concorrente(self):
        iniciado = threading.Event()
        liberar = threading.Event()
        def fake_processar(job, arquivo, pasta, *, registrar_biblioteca=True):
            iniciado.set()
            liberar.wait(3)
            job["estado"] = "concluido"
        try:
            with patch("servico_interno.processar", side_effect=fake_processar):
                first = self.pedir("POST", "/v1/trabalhos", b"%PDF-test", {"Content-Type": "application/pdf"})
                self.assertEqual(first[0], 202)
                self.assertTrue(iniciado.wait(2))
                second = self.pedir("POST", "/v1/trabalhos", b"%PDF-test", {"Content-Type": "application/pdf"})
                self.assertEqual(second[0], 409)
        finally:
            liberar.set()

    def test_chave_curta_e_expiracao(self):
        with self.assertRaises(ValueError):
            extra = api.criar_servidor(0, "curta", Path(self.temp.name))
        clock = [1000]
        store = api.Trabalhos(Path(self.temp.name), ttl=30, relogio=lambda:clock[0])
        sample = "f"*32
        pasta = Path(self.temp.name) / sample
        pasta.mkdir()
        (pasta/"entrada.pdf").write_bytes(b"%PDF-")
        store.trabalhos[sample] = {"id":sample, "_ator":ACTOR,"estado":"concluido","_finalizado_em":1000}
        clock[0] = 1031
        self.assertIsNone(store.consultar(ACTOR, sample))
        self.assertFalse(pasta.exists())


if __name__ == "__main__":
    unittest.main()
