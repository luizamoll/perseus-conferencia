# Perseus — conferência e referência de coleta

PDF Perseus → primeiro bloco de coleta → extração → `STATUS_CURSO` → conferência → consolidação da referência → Excel e PDFs.

## Usar neste Mac

Encerre o servidor anterior com Control+C e execute `./iniciar.command`. Selecione o PDF **Alunos Coletados para Fatura** e clique em Processar relatório.

A interface mostra os totais do documento, o quadro colorido da referência, a **Biblioteca de divergências**, as pendências e os downloads.

## Como o STATUS_CURSO é decidido

O sistema separa três camadas:

1. **regra de negócio confirmada** — fatos esclarecidos pela área;
2. `regras_status_curso.json` — transcrição da aba `Legenda_Cursos_Status`;
3. **compatibilidade histórica** — exceções necessárias para explicar/reproduzir quadros mensais antigos.

Regras de negócio confirmadas em 08/09/2026:

- `LPI` = Licenciatura → **GRADUAÇÃO**;
- `TEOC` = Graduação → **GRADUAÇÃO**;
- `EFB` = Bacharelado → **GRADUAÇÃO**;
- `PCG` = Pós → **POS**;
- `DI` significa compra de **disciplina isolada**, por exemplo uma matéria como Lógica de Programação.

A biblioteca não apaga a legenda. Exemplo importante: a legenda informa `CIB → DI`, mas os quadros históricos de agosto/setembro usam CIB como **Graduação**. Como a regra específica de CIB ainda não foi esclarecida, isso permanece marcado como compatibilidade histórica, não como verdade empresarial.

A compatibilidade histórica está limitada às competências de agosto e setembro já validadas. Uma competência futura não herda automaticamente `CIB → Graduação` nem as combinações históricas; nela o Perseus volta à regra confirmada/legenda até existir nova confirmação empresarial.

Regras gerais:

- mesma categoria → mantém a categoria;
- categorias diferentes → `MÚLTIPLAS CATEGORIAS`;
- sigla desconhecida junto de siglas conhecidas → preserva a categoria sustentada e marca `REVISAR`;
- nenhuma categoria conhecida → `NÃO LOCALIZADO`.

## Biblioteca de divergências

A pasta `biblioteca/` contém:

- `mapeamentos_operacionais.json` — regras confirmadas, compatibilidades históricas e pendências conhecidas;
- `README.md` — explicação da precedência;
- `nao_localizados.json` — criado no computador ao processar os PDFs e ignorado pelo Git. Guarda apenas **siglas, contagens e competências**, nunca nomes/identificadores de alunos.

Cada execução também gera `biblioteca_divergencias.json` dentro do resultado e do ZIP técnico.

As pendências empresariais conhecidas agora são:

- `SETRA` — significado/categoria ainda desconhecidos;
- `15` — valor confirmado como realmente presente na coluna Curso, mas significado/categoria ainda não esclarecidos; deve ser confirmado com a pessoa responsável pela lista.

`LPI` e `PCG` deixaram de ser pendências.

## Referência histórica x regra atual

A planilha histórica de setembro possui total 2.211 e distribui:

- GRADUAÇÃO 945
- MESTRADO 325
- DI 710
- MBA 10
- POS 13
- CURSO LIVRE 0
- APERFEIÇOAMENTO 15
- NÃO LOCALIZADO 4
- MÚLTIPLAS CATEGORIAS 189

Com os novos esclarecimentos de negócio, mantendo as demais compatibilidades históricas apenas para explicar/reproduzir setembro, a classificação atual passa a:

- **GRADUAÇÃO 947**
- MESTRADO 325
- DI 710
- MBA 10
- **POS 14**
- CURSO LIVRE 0
- APERFEIÇOAMENTO 15
- **NÃO LOCALIZADO 1** (`SETRA`)
- MÚLTIPLAS CATEGORIAS 189
- total **2.211**

A diferença é explicada por dois alunos `LPI` que saem de NÃO LOCALIZADO para GRADUAÇÃO e um aluno `PCG` que sai de NÃO LOCALIZADO para POS.

O valor `15` aparece junto de cursos já sustentados como DI; por isso o registro continua classificado como DI, mas permanece marcado `REVISAR` até seu significado ser confirmado.

A conferência de quantidade do PDF continua independente: agosto permanece 2.050/2.050; setembro permanece 2.213 informados contra 2.211 extraídos, diferença −2. Nenhum registro é criado para fechar o total.

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
- `biblioteca/`: regras de negócio, compatibilidade histórica e memória local de pendências.
- `referencia.py`: `COMPETENCIA`, cores e consolidação.
- `exportacao.py`: XLSX e relatório executivo.
- `pdf_alunos.py`: lista completa em PDF.
- `app.py` + `interface/`: servidor local e interface.
- `REGRA_STATUS_CURSO.md`: regra detalhada.

PDFs digitalizados/protegidos ou outros layouts continuam fora do escopo homologado; não há OCR.
