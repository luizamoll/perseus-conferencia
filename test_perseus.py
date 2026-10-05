import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from perseus import ler_bloco, validar_linha, salvar


class RegrasDeExtracao(unittest.TestCase):
    def test_periodo_de_coleta_nao_e_competencia_da_fatura(self):
        bloco = ler_bloco("08/2026 (26/07/2026 até 25/08/2026) Coletado: 2213 Calculado: 2213")
        self.assertEqual(bloco["periodo"], "08/2026")
        self.assertEqual(bloco["coletado"], 2213)

    def test_varios_cursos_preservam_um_identificador(self):
        linha = ["Aluno Exemplo(0000123)", "DIR, EVE", "26/06/2026, 25/07/2026", "MAT, MAT", "MAT, CCL", "1, 3", "S, S"]
        codigo, problemas = validar_linha(linha, datetime(2026, 6, 26), datetime(2026, 7, 25))
        self.assertEqual(codigo, "0000123")
        self.assertEqual(problemas, [])
        self.assertEqual(linha[1], "DIR, EVE")

    def test_datas_incorretas_geram_alertas(self):
        linha = ["Exemplo(DIs0001)", "DIR, EVE", "31/02/2026, 26/07/2026", "MAT", "MAT, MAT", "1, 1", "S, S"]
        _, problemas = validar_linha(linha, datetime(2026, 6, 26), datetime(2026, 7, 25))
        self.assertTrue(any("inválida" in p for p in problemas))
        self.assertTrue(any("fora do intervalo" in p for p in problemas))
        self.assertTrue(any("Quantidades diferentes" in p for p in problemas))

    def test_sem_identificador_nao_e_descartado(self):
        linha = ["Exemplo", "DIR", "26/06/2026", "MAT", "CCL", "1", "S"]
        codigo, problemas = validar_linha(linha, datetime(2026, 6, 26), datetime(2026, 7, 25))
        self.assertEqual(codigo, "")
        self.assertTrue(any("sem identificador" in p for p in problemas))

    def test_saida_existente_nao_e_sobrescrita(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "original.txt"
            arquivo.write_text("preservado")
            with self.assertRaises(FileExistsError):
                salvar({}, pasta)
            self.assertEqual(arquivo.read_text(), "preservado")


if __name__ == "__main__":
    unittest.main()
