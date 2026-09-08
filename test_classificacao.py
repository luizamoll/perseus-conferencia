import copy
import json
import tempfile
import unittest
from pathlib import Path

from classificacao import carregar_regras, classificar_registro, classificar_resultado, salvar_auditoria
from referencia import CORES_REFERENCIA


class ClassificacaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regras=carregar_regras()

    def classify(self,curso):
        return classificar_registro({"Curso":curso},self.regras)

    def test_legenda_oficial_principal(self):
        esperados={
            "DIR":"GRADUAÇÃO","CIB":"DI","CEXT":"DI","EVE":"CURSO LIVRE",
            "TA":"APERFEIÇOAMENTO","MEST":"MESTRADO","MBAAD":"MBA","PSO":"POS",
        }
        for curso,categoria in esperados.items():
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],categoria)
                self.assertEqual(a["status_final"],"CLASSIFICADO")

    def test_mesma_categoria_e_repetidos(self):
        casos={"CEXT, CHU, GN":"DI","CEXT, CEXT":"DI","CONT, DIR":"GRADUAÇÃO","MEST, MEST":"MESTRADO","ESGSC, PSO":"POS"}
        for curso,categoria in casos.items():
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],categoria)
                self.assertEqual(a["status_final"],"CLASSIFICADO")
                self.assertEqual(len(a["cursos_mapeados"]),len(curso.split(",")))

    def test_multiplas_categorias_e_regra_operacional(self):
        for curso in ["DIR, EVE","DIR, CSAP","DIREM, MBAAD","DA, DIR","MBA, MEST"]:
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],"MÚLTIPLAS CATEGORIAS")
                self.assertEqual(a["status_final"],"CLASSIFICADO")
                self.assertEqual(a["motivos_revisao"],[])

    def test_desconhecido_vai_para_nao_localizado_e_revisao(self):
        for curso in ["LPI","PCG","SETRA","GEQUA","DIR, LPI"]:
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],"NÃO LOCALIZADO")
                self.assertEqual(a["status_final"],"REVISAR")
                self.assertTrue(any("legenda oficial" in m for m in a["motivos_revisao"]))

    def test_sem_substring_ou_delimitador_inventado(self):
        for curso in ["XXDIR","DIR EVE","DIR/EVE","DIR;EVE"]:
            self.assertEqual(self.classify(curso)["status_final"],"REVISAR")
        self.assertEqual(self.classify("DIREM")["categoria_final"],"POS")

    def test_vazio_e_delimitador(self):
        for curso in [None,"",",","DIR,","DIR,,EVE",15]:
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],"NÃO LOCALIZADO")
                self.assertEqual(a["status_final"],"REVISAR")

    def test_original_nao_e_modificado(self):
        r={"Curso":" dir,\n DIR ","STATUS_CURSO":"MBA","Células originais":["raw"]}
        old=copy.deepcopy(r);a=classificar_registro(r,self.regras)
        self.assertEqual(r,old);self.assertEqual(a["categoria_final"],"GRADUAÇÃO")
        a["registro_original"]["Células originais"].append("x");self.assertEqual(r,old)

    def test_nao_agrupa_pessoas(self):
        rows=[{"Identificador":"01","Curso":"DIR"},{"Identificador":"01","Curso":"MEST"}]
        a=classificar_resultado({"registros":rows,"metadados":{}},self.regras)
        self.assertEqual([r["categoria_final"] for r in a["auditoria"]],["GRADUAÇÃO","MESTRADO"])

    def test_competencia_referencia_e_consolidacao(self):
        resultado={
            "metadados":{"competencia_fatura":"2026/09"},
            "registros":[{"Curso":"CIB"},{"Curso":"DIR, EVE"},{"Curso":"LPI"}],
        }
        a=classificar_resultado(resultado,self.regras)
        self.assertEqual(a["competencia_operacional"],"Fatura_Final_Ref_Setembro")
        self.assertEqual(a["referencia"]["titulo"],"Referência Setembro")
        self.assertEqual(a["referencia"]["cor"],"E59EDD")
        contagem={i["categoria"]:i["quantidade"] for i in a["consolidacao"]}
        self.assertEqual(contagem["DI"],1)
        self.assertEqual(contagem["MÚLTIPLAS CATEGORIAS"],1)
        self.assertEqual(contagem["NÃO LOCALIZADO"],1)
        self.assertEqual(sum(contagem.values()),3)

    def test_cores_referencia_iguais_a_planilha(self):
        self.assertEqual(CORES_REFERENCIA,{2:"C2F1C8",3:"FBE3D6",4:"F9F9F9",5:"C2F1C8",6:"F2AA84",7:"F9F9F9",8:"C04F15",9:"E59EDD"})

    def test_auditoria_roundtrip(self):
        a=classificar_resultado({"registros":[{"Curso":"=X"}],"metadados":{}},self.regras)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"audit";salvar_auditoria(a,p)
            self.assertEqual(json.loads((p/"auditoria.json").read_text()),a)
            self.assertIn("'=X",(p/"auditoria.csv").read_text(encoding="utf-8-sig"))
            with self.assertRaises(FileExistsError):salvar_auditoria(a,p)

    def test_mapa_oficial_nao_usa_historico_para_decidir(self):
        self.assertEqual(self.regras["siglas"]["CIB"],"DI")
        self.assertEqual(self.regras["siglas"]["EVE"],"CURSO_LIVRE")
        self.assertNotIn("GEQUA",self.regras["siglas"])
        self.assertEqual(self.classify("GEQUA")["categoria_final"],"NÃO LOCALIZADO")


if __name__=="__main__":
    unittest.main()
