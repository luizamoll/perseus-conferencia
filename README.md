# Perseus — conferência e referência de coleta

PDF Perseus → primeiro bloco de coleta → extração → `STATUS_CURSO` → conferência → consolidação da referência → Excel e PDFs.

## Usar neste Mac

Encerre o servidor anterior com Control+C e execute `./iniciar.command`. Selecione o PDF **Alunos Coletados para Fatura** e clique em Processar relatório.

A interface mostra os totais do documento, o quadro colorido da referência, a **Biblioteca de divergências**, as pendências e os downloads.

## Como o STATUS_CURSO é decidido

O sistema preserva duas fontes separadas e auditáveis:

1. `regras_status_curso.json` — transcrição da aba `Legenda_Cursos_Status`;
2. `biblioteca/mapeamentos_operacionais.json` — exceções necessárias para reproduzir os quadros mensais já validados na planilha mestre.

A biblioteca não apaga a legenda. Exemplo importante: a legenda informa `CIB → DI`, mas os quadros operacionais de agosto/setembro usam CIB como **Graduação**. Essa diferença fica explícita na biblioteca, em vez de ser escondida no código.

Regras gerais:

- mesma categoria → mantém a categoria;
- categorias diferentes → `MÚLTIPLAS CATEGORIAS`;
- combinação com exceção operacional confirmada → usa a biblioteca;
- sigla conhecida apenas pela biblioteca → usa a categoria operacional registrada;
- sigla ainda desconhecida → mantém o que puder ser classificado pelas demais siglas e marca o registro como `REVISAR`; se não houver nenhuma categoria conhecida, vira `NÃO LOCALIZADO`.

## Biblioteca de divergências

A pasta `biblioteca/` contém:

- `mapeamentos_operacionais.json` — exceções versionadas e auditáveis;
- `README.md` — explicação da precedência;
- `nao_localizados.json` — criado no computador ao processar os PDFs e ignorado pelo Git. Guarda apenas **siglas, contagens e competências**, nunca nomes/identificadores de alunos.

Cada execução também gera `biblioteca_divergencias.json` dentro do resultado e do ZIP técnico.

## Referências reais validadas

A nova classificação reproduz exatamente os quadros da planilha fornecida.

**Agosto/2026 — total 2.050**

- GRADUAÇÃO 883
- MESTRADO 324
- DI 617
- MBA 10
- POS 13
- CURSO LIVRE 0
- APERFEIÇOAMENTO 15
- NÃO LOCALIZADO 2
- MÚLTIPLAS CATEGORIAS 186

**Setembro/2026 — total 2.211**

- GRADUAÇÃO 945
- MESTRADO 325
- DI 710
- MBA 10
- POS 13
- CURSO LIVRE 0
- APERFEIÇOAMENTO 15
- NÃO LOCALIZADO 4
- MÚLTIPLAS CATEGORIAS 189

A conferência de quantidade do PDF continua independente: agosto permanece 2.050/2.050; setembro permanece 2.213 informados contra 2.211 extraídos, diferença −2. Nenhum registro é criado para fechar o total.

As siglas ainda sem decisão operacional em setembro são `15`, `LPI`, `PCG` e `SETRA`. O código `15` aparece em um registro que também contém cursos DI; por isso a sigla entra na biblioteca de revisão, mas o aluno continua classificado como DI. Assim há cinco ocorrências de siglas pendentes, porém quatro linhas em `NÃO LOCALIZADO`.

## Saídas

O XLSX possui `Resumo`, `Referência`, `Alunos` e `Divergências`. Também são gerados relatório executivo PDF, lista completa em PDF, CSV/JSON, `biblioteca_divergencias.json` e ZIP técnico.

Identificadores permanecem texto, inclusive zeros à esquerda. O motor de extração aprovado não é alterado pela biblioteca.

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
- `biblioteca/`: exceções operacionais e memória local de siglas pendentes.
- `referencia.py`: `COMPETENCIA`, cores e consolidação.
- `exportacao.py`: XLSX e relatório executivo.
- `pdf_alunos.py`: lista completa em PDF.
- `app.py` + `interface/`: servidor local e interface.
- `REGRA_STATUS_CURSO.md`: regra detalhada.

PDFs digitalizados/protegidos ou outros layouts continuam fora do escopo homologado; não há OCR.
