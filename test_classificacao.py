import copy
import json
import tempfile
import unittest
from pathlib import Path

from classificacao import carregar_regras, classificar_registro, classificar_resultado, salvar_auditoria
from referencia import CORES_REFERENCIA
from biblioteca import carregar_biblioteca, registrar_nao_localizados


class ClassificacaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regras=carregar_regras()
        cls.biblioteca=carregar_biblioteca()

    def classify(self,curso):
        return classificar_registro({"Curso":curso},self.regras,self.biblioteca)

    def test_legenda_e_biblioteca_operacional(self):
        esperados={
            "DIR":"GRADUAÇÃO","CIB":"GRADUAÇÃO","CEXT":"DI","EVE":"CURSO LIVRE",
            "TA":"APERFEIÇOAMENTO","MEST":"MESTRADO","MBAAD":"MBA","PSO":"POS",
            "TEOC":"GRADUAÇÃO","EFB":"GRADUAÇÃO","GEQUA":"POS",
        }
        for curso,categoria in esperados.items():
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],categoria)
                self.assertEqual(a["status_final"],"CLASSIFICADO")

    def test_biblioteca_nao_apaga_legenda_oficial(self):
        self.assertEqual(self.regras["siglas"]["CIB"],"DI")
        self.assertEqual(self.biblioteca["mapeamentos_siglas"]["CIB"],"GRADUAÇÃO")
        a=self.classify("CIB")
        self.assertEqual(a["categoria_final"],"GRADUAÇÃO")
        self.assertEqual(a["cursos_mapeados"][0]["categoria_legenda"],"DI")
        self.assertEqual(a["cursos_mapeados"][0]["fonte"],"biblioteca")

    def test_mesma_categoria_e_repetidos(self):
        casos={"CEXT, CHU, GN":"DI","CEXT, CEXT":"DI","CONT, DIR":"GRADUAÇÃO","MEST, MEST":"MESTRADO"}
        for curso,categoria in casos.items():
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],categoria)
                self.assertEqual(a["status_final"],"CLASSIFICADO")
                self.assertEqual(len(a["cursos_mapeados"]),len(curso.split(",")))

    def test_combinacoes_operacionais_reproduzem_referencia(self):
        casos={"ESGSC, PSO":"GRADUAÇÃO","DIREM, MBAAD":"GRADUAÇÃO","DA, DIR":"GRADUAÇÃO"}
        for curso,categoria in casos.items():
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],categoria)
                self.assertEqual(a["fonte_categoria_final"],"biblioteca_combinacao")
                self.assertEqual(a["status_final"],"CLASSIFICADO")

    def test_multiplas_categorias_genericas(self):
        for curso in ["DIR, EVE","DIR, CSAP","MBA, MEST"]:
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],"MÚLTIPLAS CATEGORIAS")
                self.assertEqual(a["status_final"],"CLASSIFICADO")

    def test_desconhecido_sozinho_e_misturado(self):
        for curso in ["LPI","PCG","SETRA"]:
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["categoria_final"],"NÃO LOCALIZADO")
                self.assertEqual(a["status_final"],"REVISAR")
                self.assertTrue(any("biblioteca" in m for m in a["motivos_revisao"]))
        a=self.classify("15, CEXT, CSAP, GN")
        self.assertEqual(a["categoria_final"],"DI")
        self.assertEqual(a["status_final"],"REVISAR")
        self.assertEqual(a["siglas_nao_localizadas"],["15"])

    def test_sem_substring_ou_delimitador_inventado(self):
        for curso in ["XXDIR","DIR EVE","DIR/EVE","DIR;EVE"]:
            self.assertEqual(self.classify(curso)["status_final"],"REVISAR")
        self.assertEqual(self.classify("DIREM")["categoria_final"],"POS")

    def test_vazio_e_delimitador(self):
        for curso in [None,"",",","DIR,","DIR,,EVE",15]:
            with self.subTest(curso=curso):
                a=self.classify(curso)
                self.assertEqual(a["status_final"],"REVISAR")

    def test_original_nao_e_modificado(self):
        r={"Curso":" dir,\n DIR ","STATUS_CURSO":"MBA","Células originais":["raw"]}
        old=copy.deepcopy(r);a=classificar_registro(r,self.regras,self.biblioteca)
        self.assertEqual(r,old);self.assertEqual(a["categoria_final"],"GRADUAÇÃO")
        a["registro_original"]["Células originais"].append("x");self.assertEqual(r,old)

    def test_nao_agrupa_pessoas(self):
        rows=[{"Identificador":"01","Curso":"DIR"},{"Identificador":"01","Curso":"MEST"}]
        a=classificar_resultado({"registros":rows,"metadados":{}},self.regras,self.biblioteca)
        self.assertEqual([r["categoria_final"] for r in a["auditoria"]],["GRADUAÇÃO","MESTRADO"])

    def test_competencia_referencia_consolidacao_e_biblioteca(self):
        resultado={
            "metadados":{"competencia_fatura":"2026/09"},
            "registros":[{"Curso":"CIB"},{"Curso":"DIR, EVE"},{"Curso":"LPI"},{"Curso":"15, CEXT"}],
        }
        a=classificar_resultado(resultado,self.regras,self.biblioteca)
        self.assertEqual(a["competencia_operacional"],"Fatura_Final_Ref_Setembro")
        self.assertEqual(a["referencia"]["titulo"],"Referência Setembro")
        self.assertEqual(a["referencia"]["cor"],"E59EDD")
        contagem={i["categoria"]:i["quantidade"] for i in a["consolidacao"]}
        self.assertEqual(contagem["GRADUAÇÃO"],1)
        self.assertEqual(contagem["DI"],1)
        self.assertEqual(contagem["MÚLTIPLAS CATEGORIAS"],1)
        self.assertEqual(contagem["NÃO LOCALIZADO"],1)
        self.assertEqual(sum(contagem.values()),4)
        nao={i["sigla"]:i["ocorrencias"] for i in a["biblioteca"]["siglas_nao_localizadas"]}
        self.assertEqual(nao,{"15":1,"LPI":1})

    def test_cores_referencia_iguais_a_planilha(self):
        self.assertEqual(CORES_REFERENCIA,{2:"C2F1C8",3:"FBE3D6",4:"F9F9F9",5:"C2F1C8",6:"F2AA84",7:"F9F9F9",8:"C04F15",9:"E59EDD"})

    def test_registro_local_da_biblioteca_acumula_so_siglas(self):
        resumo={"siglas_nao_localizadas":[{"sigla":"LPI","ocorrencias":2},{"sigla":"15","ocorrencias":1}]}
        with tempfile.TemporaryDirectory() as d:
            caminho=Path(d)/"nao_localizados.json"
            registrar_nao_localizados(resumo,"Fatura_Final_Ref_Setembro",caminho)
            registrar_nao_localizados({"siglas_nao_localizadas":[{"sigla":"LPI","ocorrencias":1}]},"Fatura_Final_Ref_Outubro_2026",caminho)
            dados=json.loads(caminho.read_text())
            self.assertEqual(dados["siglas"]["LPI"]["ocorrencias_acumuladas"],3)
            self.assertEqual(dados["siglas"]["LPI"]["ultima_competencia"],"Fatura_Final_Ref_Outubro_2026")
            self.assertNotIn("Aluno",caminho.read_text())

    def test_auditoria_roundtrip(self):
        a=classificar_resultado({"registros":[{"Curso":"=X"}],"metadados":{}},self.regras,self.biblioteca)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"audit";salvar_auditoria(a,p)
            self.assertEqual(json.loads((p/"auditoria.json").read_text()),a)
            self.assertIn("'=X",(p/"auditoria.csv").read_text(encoding="utf-8-sig"))
            with self.assertRaises(FileExistsError):salvar_auditoria(a,p)


if __name__=="__main__":
    unittest.main()
