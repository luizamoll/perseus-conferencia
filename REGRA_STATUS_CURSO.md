# Regra — STATUS_CURSO, biblioteca e Referência

Este documento registra a regra empresarial usada pelo Perseus sem alterar o motor de extração do PDF.

## Duas fontes, sem misturar evidência

### 1. Legenda oficial

`regras_status_curso.json` é a transcrição da aba `Legenda_Cursos_Status` de **Fatura Perseus - SET 1.xlsx**.

### 2. Biblioteca operacional

`biblioteca/mapeamentos_operacionais.json` guarda exceções observadas e confirmadas pelos quadros mensais da própria planilha mestre. Ela existe porque a legenda e o processo operacional não são idênticos em todos os casos.

Exemplo central: a legenda traz `CIB → DI`, porém agosto e setembro classificam operacionalmente CIB como **Graduação**. O sistema preserva as duas informações e usa a biblioteca para reproduzir a Referência operacional.

## Precedência

1. combinação exata registrada na biblioteca;
2. mapeamento de sigla registrado na biblioteca;
3. legenda oficial;
4. sigla ausente nas duas fontes → pendência.

A biblioteca não modifica `regras_status_curso.json`.

## Regras de um registro

- O campo `Curso` é separado somente por vírgula.
- Repetições são preservadas.
- Se todas as categorias conhecidas forem iguais, o aluno recebe essa categoria.
- Se houver categorias conhecidas diferentes, recebe `MÚLTIPLAS CATEGORIAS`.
- Se uma sigla desconhecida aparecer junto com siglas conhecidas, a categoria conhecida é preservada, mas o registro fica `REVISAR` e a sigla desconhecida entra na biblioteca local.
- Se nenhuma sigla tiver categoria conhecida, recebe `NÃO LOCALIZADO` e `REVISAR`.
- Nenhum aluno é criado, removido ou duplicado para fechar totais.

## Exceções operacionais que reproduzem agosto/setembro

Siglas:

- CIB → GRADUAÇÃO
- TEOC → GRADUAÇÃO
- EFB → GRADUAÇÃO
- GECOO → GRADUAÇÃO
- GEQUA → POS
- EFL → GRADUAÇÃO
- CBIOL → GRADUAÇÃO
- GESSP → GRADUAÇÃO
- ARTVI → GRADUAÇÃO
- LEPOL → GRADUAÇÃO
- QUIM → GRADUAÇÃO

Combinações exatas:

- ESGSC + PSO → GRADUAÇÃO
- DIREM + MBAAD → GRADUAÇÃO
- DA + DIR → GRADUAÇÃO

Exemplos:

- `CIB` → GRADUAÇÃO pela biblioteca, mantendo DI como `categoria_legenda` na auditoria.
- `CEXT, CIB` → MÚLTIPLAS CATEGORIAS.
- `ESGSC, PSO` → GRADUAÇÃO pela exceção de combinação.
- `15, CEXT, CSAP, GN` → DI + REVISAR; `15` entra na biblioteca de pendências.
- `LPI` → NÃO LOCALIZADO + REVISAR.

## Biblioteca persistente

`biblioteca/nao_localizados.json` é criado durante o uso e não vai para o Git. Ele armazena somente sigla, quantidade acumulada, primeira/última competência e data de atualização. Não armazena nome nem identificador de aluno.

Cada execução exporta também `biblioteca_divergencias.json` para permitir auditoria daquele processamento.

## COMPETENCIA

Para 2026, a nomenclatura observada segue `Fatura_Final_Ref_<Mês>_2026`, com setembro registrado na fonte como `Fatura_Final_Ref_Setembro`. Meses futuros usam o padrão com mês e ano enquanto não houver outra fonte.

## Cores de Referência

- Fevereiro `#C2F1C8`
- Março `#FBE3D6`
- Abril `#F9F9F9`
- Maio `#C2F1C8`
- Junho `#F2AA84`
- Julho `#F9F9F9`
- Agosto `#C04F15`
- Setembro `#E59EDD`

## Totais de controle

A consolidação validada reproduz a planilha:

- Agosto: 883 GRADUAÇÃO, 324 MESTRADO, 617 DI, 10 MBA, 13 POS, 0 CURSO LIVRE, 15 APERFEIÇOAMENTO, 2 NÃO LOCALIZADO, 186 MÚLTIPLAS CATEGORIAS = **2.050**.
- Setembro: 945 GRADUAÇÃO, 325 MESTRADO, 710 DI, 10 MBA, 13 POS, 0 CURSO LIVRE, 15 APERFEIÇOAMENTO, 4 NÃO LOCALIZADO, 189 MÚLTIPLAS CATEGORIAS = **2.211**.

Esses totais de classificação não alteram a conferência do PDF. Setembro continua com 2.213 informados e 2.211 extraídos.
