# Regra — STATUS_CURSO, biblioteca e Referência

Este documento registra a regra empresarial usada pelo Perseus sem alterar o motor de extração do PDF.

## Três camadas, sem misturar evidência

### 1. Regra de negócio confirmada

Fatos confirmados diretamente pela área têm prioridade e ficam em `biblioteca/mapeamentos_operacionais.json` dentro de `confirmados_negocio`.

Confirmados:

- `LPI` = Licenciatura → **GRADUAÇÃO**
- `TEOC` = Graduação → **GRADUAÇÃO**
- `EFB` = Bacharelado → **GRADUAÇÃO**
- `PCG` = Pós → **POS**
- `SETRA` = Graduação em Segurança do Trabalho → **GRADUAÇÃO**
- `DI` significa vínculo de compra de **disciplina isolada**, por exemplo uma matéria como Lógica de Programação.

O valor `15` **não foi promovido a MBA**. Sabe-se apenas que o aluno do registro em que ele aparece cursa MBA Gestão de trans; isso não prova que `15` seja o código desse MBA. O significado de `15` continua pendente.

### 2. Legenda oficial

`regras_status_curso.json` é a transcrição da aba `Legenda_Cursos_Status` da planilha mestre. Ela continua preservada como fonte documental.

### 3. Compatibilidade histórica

A planilha mestre usa algumas classificações que não coincidem com a legenda. Essas regras ficam isoladas em `mapeamentos_historicos_compatibilidade` e `combinacoes_historicas_compatibilidade`.

Exemplo central: a legenda traz `CIB → DI`, porém a referência histórica de agosto/setembro classifica operacionalmente CIB como **Graduação**. Isso permanece compatibilidade histórica, não verdade empresarial confirmada.

A compatibilidade histórica está autorizada somente para `Fatura_Final_Ref_Agosto_2026` e `Fatura_Final_Ref_Setembro`. Uma competência futura não herda automaticamente essas exceções.

## Precedência

1. regra de negócio confirmada;
2. legenda oficial;
3. compatibilidade histórica somente nas competências explicitamente autorizadas;
4. sem base segura → pendência explícita.

## Regras de um registro

- O campo `Curso` é separado somente por vírgula.
- Repetições são preservadas.
- Se todas as categorias conhecidas forem iguais, mantém a categoria.
- Se houver categorias conhecidas diferentes, recebe `MÚLTIPLAS CATEGORIAS`.
- Sigla desconhecida junto de siglas conhecidas não apaga a classificação sustentada pelas siglas conhecidas; o registro fica `REVISAR`.
- Se nenhuma sigla tiver categoria conhecida, recebe `NÃO LOCALIZADO` e `REVISAR`.
- Nenhum aluno é criado, removido ou duplicado para fechar totais.

## Pendência conhecida

- `15` → existe realmente na coluna Curso. O significado do código continua sem confirmação. No registro observado, `CEXT`, `CSAP` e `GN` sustentam **DI**, e a planilha rosa original de setembro também classificou esse registro como **DI**.

`SETRA` deixou de ser pendência e agora é **GRADUAÇÃO**.

## Compatibilidade histórica que reproduz a planilha rosa original

Siglas históricas:

- CIB → GRADUAÇÃO
- GECOO → GRADUAÇÃO
- GEQUA → POS
- EFL → GRADUAÇÃO
- CBIOL → GRADUAÇÃO
- GESSP → GRADUAÇÃO
- ARTVI → GRADUAÇÃO
- LEPOL → GRADUAÇÃO
- QUIM → GRADUAÇÃO

Combinações históricas exatas:

- ESGSC + PSO → GRADUAÇÃO
- DIREM + MBAAD → GRADUAÇÃO
- DA + DIR → GRADUAÇÃO

## Referência histórica x regra atual

A planilha rosa original de setembro possui 2.211 registros e fecha em:

- 945 GRADUAÇÃO
- 325 MESTRADO
- 710 DI
- 10 MBA
- 13 POS
- 0 CURSO LIVRE
- 15 APERFEIÇOAMENTO
- 4 NÃO LOCALIZADO
- 189 MÚLTIPLAS CATEGORIAS

Na planilha `alunos (5).xlsx`, gerada por uma versão anterior do software, os 2.211 registros eram os mesmos, mas 24 deles estavam classificados diferente da referência original: 20 conflitos ligados a `CIB`, 3 combinações históricas e o registro com `15`. Por isso o consolidado gerado ficou 928 GRADUAÇÃO, 709 DI, 183 MÚLTIPLAS e 28 NÃO LOCALIZADO, mantendo iguais MESTRADO, MBA, POS e APERFEIÇOAMENTO.

Com a compatibilidade histórica aplicada, esses 24 casos voltam a reproduzir a referência original. Depois das confirmações empresariais posteriores, porém, a **regra atual corrigida** deixa de ser idêntica à planilha histórica: os dois `LPI`, `SETRA` e `PCG` saem de NÃO LOCALIZADO. Assim, mantendo os demais registros conforme a referência histórica, setembro passa a:

- **948 GRADUAÇÃO**
- 325 MESTRADO
- 710 DI
- 10 MBA
- **14 POS**
- 0 CURSO LIVRE
- 15 APERFEIÇOAMENTO
- **0 NÃO LOCALIZADO**
- 189 MÚLTIPLAS CATEGORIAS
- total **2.211**

O `15` permanece pendente de significado e não altera esse total: seu registro continua DI com revisão, porque as outras siglas do mesmo registro sustentam DI e essa também é a classificação da referência original.

A conferência de quantidade do PDF continua independente: setembro permanece com 2.213 informados e 2.211 extraídos.
