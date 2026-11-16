"""Regressoes anonimizadas para o formato de novembro/2026.

Os dados reais de alunos permanecem fora do Git. A lista de siglas e os
totais sao apenas metadados de controle do relatorio recebido.
"""
import unittest
from datetime import datetime

from perseus import BLOCO, CABECALHO, validar_linha
from classificacao import carregar_regras, classificar_registro
from biblioteca import carregar_biblioteca

# Siglas/codigos observados no primeiro bloco de coleta do PDF de novembro.
# Nao contem nomes nem identificadores de pessoas.
CODIGOS_NOVEMBRO = (
    "15 ADM ADS AOP ARQ ARTVI BIOM CBIOL CEXT CHU CIB CONT COPIP "
    "CSA CSAP DA DCC DEPP DIR DIREM DPC DPPP DTPT DTT EFB EFL "
    "ENF ENGC ENGPR ENGST ESGSC EVE FISIO FTC GDP GECOM GECOO "
    "GEFIN GEPDO GEQUA GERH GESSP GETI GN LEPOL LOG LPI MAT MBA "
    "MBAAD MBAAF MBAGC MBAGE MBAGP MEST MKT P-DEP PC PCG "
    "PEDAG PRGER PSO QUIM SESOC TA TEOC"
).split()


class ConferenciaNovembro(unittest.TestCase):
    def test_fatura_novembro_e_primeira_coleta_outubro_sao_distintas(self):
        cab = CABECALHO.search(
            "Contrato: 2023-0901 Competência: 2026/11 Quantidade Faturada: 2119"
        )
        bloco = BLOCO.search(
            "10/2026 (26/09/2026 até 25/10/2026) Coletado: 2310 Calculado: 2310"
        )
        self.assertIsNotNone(cab)
        self.assertIsNotNone(bloco)
        self.assertEqual((cab[2], int(cab[3])), ("2026/11", 2119))
        self.assertEqual((bloco[1], int(bloco[4]), int(bloco[5])),
                         ("10/2026", 2310, 2310))
        self.assertNotEqual(int(cab[3]), int(bloco[4]))

    def test_pdf_financeiro_nao_e_pdf_de_alunos(self):
        texto_financeiro = (
            "Detalhamento de Faturamento\n"
            "Competência: 2026/11\nTotal na Competência: R$ 15.875,15"
        )
        self.assertIsNone(CABECALHO.search(texto_financeiro))

    def test_nome_com_acentos_e_quebra_de_linha_preservado(self):
        # Exemplo ficticio, sem dados pessoais do PDF original.
        linha = [
            "ALUNA FICTÍCIA DA\nCONCEIÇÃO(0000123)",
            "DIR, EVE", "26/09/2026, 14/10/2026", "MAT, MAT",
            "MAT, MAT", "1, 1", "S, S",
        ]
        codigo, problemas = validar_linha(
            linha, datetime(2026, 9, 26), datetime(2026, 10, 25)
        )
        self.assertEqual(codigo, "0000123")
        self.assertEqual(problemas, [])
        self.assertIn("CONCEIÇÃO", linha[0])

    def test_identificador_sem_nome_gera_revisao(self):
        linha = ["(0000123)", "DIR", "26/09/2026", "MAT", "MAT", "1", "S"]
        codigo, problemas = validar_linha(
            linha, datetime(2026, 9, 26), datetime(2026, 10, 25)
        )
        self.assertEqual(codigo, "0000123")
        self.assertTrue(any("sem nome legível" in p for p in problemas))

    def test_nome_com_caractere_ilegivel_gera_revisao(self):
        linha = ["PESSOA FICTÍCIA \ufffd TESTE(0000123)", "DIR",
                 "26/09/2026", "MAT", "MAT", "1", "S"]
        _, problemas = validar_linha(
            linha, datetime(2026, 9, 26), datetime(2026, 10, 25)
        )
        self.assertTrue(any("caracteres ilegíveis" in p for p in problemas))

    def test_siglas_do_relatorio_reconhecidas_sem_herdar_excecoes_historicas(self):
        regras, biblioteca = carregar_regras(), carregar_biblioteca()
        self.assertEqual(len(CODIGOS_NOVEMBRO), 66)
        self.assertEqual(len(set(CODIGOS_NOVEMBRO)), 66)
        for codigo in CODIGOS_NOVEMBRO:
            with self.subTest(codigo=codigo):
                classificacao = classificar_registro(
                    {"Curso": codigo}, regras, biblioteca, permitir_historico=False
                )
                # O codigo 15 e legitimo, mas isolado nao determina STATUS_CURSO.
                if codigo == "15":
                    self.assertEqual(classificacao["siglas_nao_localizadas"], [])
                    self.assertIn("15", classificacao["cursos_sem_regra_status"])
                else:
                    self.assertEqual(classificacao["siglas_nao_localizadas"], [])
                    self.assertEqual(classificacao["status_final"], "CLASSIFICADO")


if __name__ == "__main__":
    unittest.main()
