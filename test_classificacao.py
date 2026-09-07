import copy
import json
import tempfile
import unittest
from pathlib import Path
from classificacao import carregar_regras,classificar_registro,classificar_resultado,salvar_auditoria
from validar_classificacao import comparar

class ClassificacaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.regras=carregar_regras()
    def classify(self,curso): return classificar_registro({"Curso":curso},self.regras)
    def test_unico(self):
        self.assertEqual(self.classify("DIR")["categoria_final"],"Graduação")
    def test_mesma_categoria_e_repetidos(self):
        for c in ["CEXT, CHU, GN", "CEXT, CEXT", "CONT, DIR", "MEST, MEST"]:
            with self.subTest(c=c):
                a=self.classify(c);self.assertEqual(a["status_final"],"CLASSIFICADO")
                self.assertNotEqual(a["categoria_final"],"Múltiplas categorias")
                self.assertEqual(len(a["cursos_mapeados"]),len(c.split(",")))
    def test_multiplas_validada(self):
        for c in ["DIR, EVE", "DIR, CSAP", "CSAP, CSAP, DIR"]:
            self.assertEqual(self.classify(c)["categoria_final"],"Múltiplas categorias")
    def test_multiplas_nao_observada(self):
        self.assertEqual(self.classify("MBA, MEST")["status_final"],"REVISAR")
    def test_cib_e_desconhecidos(self):
        for c in ["CIB","CIB, CEXT", "LPI", "15, CEXT, CSAP, GN", "PCG", "SETRA"]:
            self.assertEqual(self.classify(c)["status_final"],"REVISAR")
    def test_combinacoes_conflitantes(self):
        for c in ["ESGSC, PSO", "DIREM, MBAAD", "DA, DIR", "PSO, ESGSC"]:
            self.assertEqual(self.classify(c)["status_final"],"REVISAR")
    def test_sem_substring(self):
        for c in ["XXDIR", "DIR EVE", "DIR/EVE", "DIR;EVE"]:
            self.assertEqual(self.classify(c)["status_final"],"REVISAR")
        self.assertEqual(self.classify("DIREM")["categoria_final"],"Pós")
        self.assertEqual(self.classify("MBAAD")["categoria_final"],"MBA")
    def test_vazio_e_delimitador(self):
        for c in [None,"",",", "DIR,", "DIR,,EVE", 15]:
            self.assertEqual(self.classify(c)["status_final"],"REVISAR")
    def test_original_e_historico_nao_influencia(self):
        r={"Curso":" dir,\n DIR ","STATUS_CURSO":"MBA","Células originais":["raw"]}
        old=copy.deepcopy(r);a=classificar_registro(r,self.regras)
        self.assertEqual(r,old); self.assertEqual(a["categoria_final"],"Graduação")
        a["registro_original"]["Células originais"].append("x");self.assertEqual(r,old)
    def test_nao_agrupa_pessoas(self):
        rows=[{"Identificador":"01","Curso":"DIR"},{"Identificador":"01","Curso":"MEST"}]
        a=classificar_resultado({"registros":rows},self.regras)
        self.assertEqual([r["categoria_final"] for r in a["auditoria"]],["Graduação","Mestrado"])
    def test_auditoria_roundtrip(self):
        a=classificar_resultado({"registros":[{"Curso":"=X"}]},self.regras)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"audit";salvar_auditoria(a,p)
            self.assertEqual(json.loads((p/"auditoria.json").read_text()),a)
            self.assertIn("'=X",(p/"auditoria.csv").read_text(encoding="utf-8-sig"))
            with self.assertRaises(FileExistsError):salvar_auditoria(a,p)
    def test_pareamento_duplicado_nao_sobrescreve(self):
        r={"registros":[{"Identificador":"01","Curso":"DIR"}]}
        h={"Aluno":"Exemplo(01)","Curso":"DIR","STATUS_CURSO":"Graduação"}
        a,s=comparar(r,[h,h],self.regras)
        self.assertEqual(s["comparacao"]["SEM_PAREAMENTO_UNIVOCO"],1)
    def test_mapa_observado_e_conflito(self):
        self.assertTrue(self.regras["siglas"]["CIB"]["conflito"])
        self.assertEqual(self.regras["siglas"]["GEQUA"]["base"],"somente histórico")
        self.assertEqual(self.classify("GEQUA")["categoria_final"],"Pós")
        self.assertEqual(self.classify("GECOO")["categoria_final"],"Graduação")

if __name__=="__main__": unittest.main()
