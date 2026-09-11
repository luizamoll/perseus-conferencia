# Perseus — conferência e referência de coleta

PDF Perseus → primeiro bloco de coleta → extração → `STATUS_CURSO` → conferência → consolidação da referência → Excel e PDFs.

## Usar neste Mac

Encerre o servidor anterior com Control+C e execute `./iniciar.command`. Selecione o PDF **Alunos Coletados para Fatura** e clique em Processar relatório.

A interface mostra os totais do documento, o quadro colorido da referência, a **Biblioteca de divergências**, as pendências e os downloads.

## Como o STATUS_CURSO é decidido

O sistema separa três camadas:

1. **regra de negócio confirmada**;
2. `regras_status_curso.json` — legenda oficial;
3. **compatibilidade histórica** — exceções usadas para reproduzir referências antigas específicas.

Regras confirmadas:

- `LPI` → **GRADUAÇÃO**;
- `TEOC` → **GRADUAÇÃO**;
- `EFB` → **GRADUAÇÃO**;
- `PCG` → **POS**;
- `SETRA` = Graduação em Segurança do Trabalho → **GRADUAÇÃO**;
- `DI` representa compra de **disciplina isolada**.

O valor `15` continua pendente. Sabe-se que o aluno do registro cursa MBA Gestão de trans, mas isso não permite concluir que `15` seja o código do MBA. No registro `15, CEXT, CSAP, GN`, as siglas conhecidas sustentam **DI**, e a referência histórica de setembro também classifica esse registro como DI. Portanto o Perseus preserva DI e mantém `15` em revisão.

A compatibilidade histórica está limitada às competências de agosto e setembro já validadas. Uma competência futura não herda automaticamente `CIB → Graduação` nem as combinações históricas.

## Por que a planilha rosa antiga não batia

A planilha rosa original de setembro e a antiga `alunos (5).xlsx` possuem os mesmos **2.211 registros**, mas uma versão anterior do classificador marcou 24 registros de forma diferente da referência: 20 casos ligados a `CIB`, 3 combinações históricas e o registro com `15`.

Isso produzia na planilha gerada:

- GRADUAÇÃO 928 em vez de 945;
- DI 709 em vez de 710;
- MÚLTIPLAS CATEGORIAS 183 em vez de 189;
- NÃO LOCALIZADO 28 em vez de 4.

MESTRADO 325, MBA 10, POS 13 e APERFEIÇOAMENTO 15 já coincidiam.

A compatibilidade histórica corrige esses 24 casos para reproduzir a referência antiga. Depois das confirmações empresariais posteriores, a regra atual corrigida passa a **948 GRADUAÇÃO, 325 MESTRADO, 710 DI, 10 MBA, 14 POS, 0 CURSO LIVRE, 15 APERFEIÇOAMENTO, 0 NÃO LOCALIZADO e 189 MÚLTIPLAS CATEGORIAS = 2.211**. A diferença em relação à planilha histórica é intencional: dois `LPI`, `SETRA` e `PCG` foram posteriormente esclarecidos.

A conferência do PDF continua independente: setembro possui 2.213 informados e 2.211 extraídos, diferença −2. Nenhum registro é criado para fechar o total.

## Biblioteca de divergências

A pasta `biblioteca/` contém:

- `mapeamentos_operacionais.json` — regras confirmadas, compatibilidades históricas e pendências;
- `README.md` — explicação das camadas;
- `nao_localizados.json` — criado localmente e ignorado pelo Git; guarda somente siglas, contagens e competências.

## Saídas

O XLSX possui `Resumo`, `Referência`, `Alunos` e `Divergências`. Também são gerados relatório executivo PDF, lista completa em PDF, CSV/JSON, `biblioteca_divergencias.json` e ZIP técnico.

Identificadores permanecem texto, inclusive zeros à esquerda.

## Testes

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -v
node --test test_interface.cjs
```

A branch `feat/nova-interface` executa esses testes automaticamente no GitHub Actions.

## Organização

- `perseus.py`: extração e conferência do PDF.
- `classificacao.py`: classificação e rastreabilidade das fontes.
- `regras_status_curso.json`: legenda oficial.
- `biblioteca/`: regras de negócio, compatibilidade histórica e memória local de pendências.
- `referencia.py`: `COMPETENCIA`, cores e consolidação.
- `exportacao.py`: XLSX e relatório executivo.
- `pdf_alunos.py`: lista completa em PDF.
- `app.py` + `interface/`: servidor local e interface.
- `REGRA_STATUS_CURSO.md`: regra detalhada.
