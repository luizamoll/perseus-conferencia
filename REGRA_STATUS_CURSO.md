# Regra — STATUS_CURSO, biblioteca e Referência

Este documento registra a regra empresarial usada pelo Perseus sem alterar o motor de extração do PDF.

## Três camadas, sem misturar evidência

### 1. Regra de negócio confirmada

Fatos confirmados diretamente pela área têm prioridade e ficam em `biblioteca/mapeamentos_operacionais.json` dentro de `confirmados_negocio`.

Confirmados em 08/09/2026:

- `LPI` = Licenciatura → **GRADUAÇÃO**
- `TEOC` = Graduação → **GRADUAÇÃO**
- `EFB` = Bacharelado → **GRADUAÇÃO**
- `PCG` = Pós → **POS**
- `DI` significa vínculo de compra de **disciplina isolada**, por exemplo uma matéria como Lógica de Programação. DI não deve ser interpretado apenas como uma sigla genérica de nível acadêmico.

### 2. Legenda oficial

`regras_status_curso.json` é a transcrição da aba `Legenda_Cursos_Status` de **Fatura Perseus - SET 1.xlsx**. Ela continua preservada como fonte documental.

### 3. Compatibilidade histórica

A própria planilha mestre usa classificações que nem sempre coincidem com a legenda. Essas regras ficam isoladas em `mapeamentos_historicos_compatibilidade` e `combinacoes_historicas_compatibilidade`.

Exemplo central: a legenda traz `CIB → DI`, porém os quadros históricos de agosto e setembro classificam operacionalmente CIB como **Graduação**. Como o significado empresarial de DI foi esclarecido, CIB não é tratado como verdade empresarial: permanece uma exceção histórica até a regra específica de CIB ser confirmada.

A compatibilidade histórica está autorizada somente para `Fatura_Final_Ref_Agosto_2026` e `Fatura_Final_Ref_Setembro`. Uma competência futura **não herda automaticamente** CIB → Graduação nem as combinações históricas. Nela, o sistema volta à regra confirmada/legenda até existir nova confirmação empresarial.

## Precedência

1. regra de negócio confirmada;
2. legenda oficial;
3. compatibilidade histórica somente nas competências explicitamente autorizadas;
4. sem base segura → pendência explícita.

Combinações históricas exatas continuam registradas separadamente para explicar como os quadros antigos foram obtidos, mas não devem ser confundidas com regra empresarial confirmada.

## Regras de um registro

- O campo `Curso` é separado somente por vírgula.
- Repetições são preservadas.
- Se todas as categorias conhecidas forem iguais, o aluno recebe essa categoria.
- Se houver categorias conhecidas diferentes, recebe `MÚLTIPLAS CATEGORIAS`.
- Se uma sigla desconhecida aparecer junto com siglas conhecidas, a categoria conhecida é preservada, mas o registro fica `REVISAR` e a sigla desconhecida entra na biblioteca local.
- Se nenhuma sigla tiver categoria conhecida, recebe `NÃO LOCALIZADO` e `REVISAR`.
- Nenhum aluno é criado, removido ou duplicado para fechar totais.

## Pendências reais conhecidas

- `SETRA` → significado e categoria ainda não confirmados.
- `15` → foi confirmado que o valor está realmente na coluna **Curso** da fonte. Seu significado e sua categoria continuam desconhecidos e devem ser confirmados com a pessoa responsável pela lista. O Perseus não presume que seja erro nem curso válido.

`LPI` e `PCG` não são mais pendências: agora possuem regra de negócio confirmada.

## Compatibilidade histórica que reproduz agosto/setembro

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

Esses itens servem para explicar/reproduzir referências antigas. Eles não têm o mesmo grau de autoridade das regras confirmadas pela área.

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

## Referência histórica x regra atual

A planilha histórica de setembro fecha em:

- 945 GRADUAÇÃO
- 325 MESTRADO
- 710 DI
- 10 MBA
- 13 POS
- 0 CURSO LIVRE
- 15 APERFEIÇOAMENTO
- 4 NÃO LOCALIZADO
- 189 MÚLTIPLAS CATEGORIAS
- total **2.211**

Depois dos novos esclarecimentos empresariais, `LPI` passa de NÃO LOCALIZADO para GRADUAÇÃO (2 alunos) e `PCG` passa de NÃO LOCALIZADO para POS (1 aluno). Portanto, mantendo as compatibilidades históricas apenas para explicar/reproduzir setembro, a classificação atual esperada passa a:

- **947 GRADUAÇÃO**
- 325 MESTRADO
- 710 DI
- 10 MBA
- **14 POS**
- 0 CURSO LIVRE
- 15 APERFEIÇOAMENTO
- **1 NÃO LOCALIZADO** (`SETRA`)
- 189 MÚLTIPLAS CATEGORIAS
- total **2.211**

O valor `15` continua sendo uma pendência de significado. No registro em que aparece junto de `CEXT, CSAP, GN`, as siglas já conhecidas sustentam DI, então ele não aumenta o total de NÃO LOCALIZADO; ainda assim, permanece marcado para revisão até a confirmação da fonte.

Esses totais de classificação não alteram a conferência do PDF. Setembro continua com 2.213 informados e 2.211 extraídos.
