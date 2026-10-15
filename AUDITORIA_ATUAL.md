# Perseus — auditoria atual

Atualização concluída em 08/09/2026. O escopo operacional continua sendo o primeiro bloco contíguo de coleta de cada PDF, sem somar os períodos históricos do restante do documento.

## Estado atual

Fluxo validado:

PDF Perseus → extração → conferência de quantidade → `STATUS_CURSO` pela legenda oficial → `COMPETENCIA` → consolidação da referência → XLSX + relatório PDF + lista completa em PDF + saídas técnicas.

O motor de extração aprovado não foi alterado nesta rodada.

## Fonte oficial de classificação

A regra agora usa exclusivamente a aba `Legenda_Cursos_Status` da planilha **Fatura Perseus - SET 1.xlsx** como fonte empresarial para Curso → categoria.

A legenda versionada foi comparada com a planilha fonte:

- 58 siglas na planilha;
- 58 siglas em `regras_status_curso.json`;
- nenhuma sigla faltante;
- nenhuma sigla extra;
- nenhuma categoria divergente.

O histórico mensal deixa de decidir a categoria. Ele pode ser usado apenas para comparação/diagnóstico.

Regras operacionais:

- todas as siglas do registro na mesma categoria → mantém essa categoria;
- categorias diferentes → `MÚLTIPLAS CATEGORIAS`;
- qualquer sigla ausente da legenda → `NÃO LOCALIZADO` e `REVISAR`;
- `CIB` → `DI`;
- `EVE` → `CURSO LIVRE`.

## Cores de referência

As cores efetivas foram extraídas da aba `Licenças Base`, considerando tema e tonalidade aplicados pelo Excel:

| Referência | Cor |
|---|---|
| Fevereiro | `#C2F1C8` |
| Março | `#FBE3D6` |
| Abril | `#F9F9F9` |
| Maio | `#C2F1C8` |
| Junho | `#F2AA84` |
| Julho | `#F9F9F9` |
| Agosto | `#C04F15` |
| Setembro | `#E59EDD` |

Esses valores estão versionados em `referencia.py` e cobertos por teste.

## Resultado real — agosto

- Documento: fatura agosto/2026; 521 páginas.
- Competência da fatura: **2026/08**.
- Coleta: **07/2026**, de **26/06/2026 a 25/07/2026**.
- Informados: **2.050**.
- Extraídos: **2.050**.
- Diferença: **0**.
- Identificadores distintos: **2.050**.
- Classificados automaticamente pela legenda oficial: **1.978**.
- `NÃO LOCALIZADO` / revisão: **72**.
- Consolidação: **2.050** registros no total.

Distribuição:

| STATUS_CURSO | Quantidade |
|---|---:|
| GRADUAÇÃO | 804 |
| MESTRADO | 324 |
| DI | 633 |
| MBA | 10 |
| POS | 11 |
| CURSO LIVRE | 0 |
| APERFEIÇOAMENTO | 15 |
| NÃO LOCALIZADO | 72 |
| MÚLTIPLAS CATEGORIAS | 181 |
| **Total** | **2.050** |

## Resultado real — setembro

- Documento: fatura setembro/2026; 537 páginas.
- Competência da fatura: **2026/09**.
- Coleta: **08/2026**, de **26/07/2026 a 25/08/2026**.
- Informados: **2.213**.
- Extraídos: **2.211**.
- Diferença: **−2**, preservada sem criação de registros.
- Identificadores distintos: **2.211**.
- Classificados automaticamente pela legenda oficial: **2.133**.
- `NÃO LOCALIZADO` / revisão: **78**.
- Consolidação: **2.211** registros no total.

Distribuição:

| STATUS_CURSO | Quantidade |
|---|---:|
| GRADUAÇÃO | 860 |
| MESTRADO | 325 |
| DI | 728 |
| MBA | 10 |
| POS | 11 |
| CURSO LIVRE | 0 |
| APERFEIÇOAMENTO | 15 |
| NÃO LOCALIZADO | 78 |
| MÚLTIPLAS CATEGORIAS | 184 |
| **Total** | **2.211** |

A diferença de dois registros de setembro continua sendo uma divergência do próprio relatório: 2.213 informados contra 2.211 identificadores/linhas encontrados. Nenhum aluno foi inventado para fechar o total.

## Siglas ausentes da legenda oficial

Estas siglas explicam os novos casos de `NÃO LOCALIZADO`.

### Agosto

- `TEOC`: 48 ocorrências
- `EFB`: 6
- `GECOO`: 3
- `GEQUA`: 3
- `LPI`: 2
- `CBIOL`: 2
- `ARTVI`: 2
- `LEPOL`: 2
- `EFL`: 1
- `GESSP`: 1
- `15`: 1
- `QUIM`: 1

### Setembro

- `TEOC`: 49 ocorrências
- `EFB`: 9
- `GEQUA`: 3
- `GECOO`: 2
- `LPI`: 2
- `CBIOL`: 2
- `GESSP`: 2
- `ARTVI`: 2
- `LEPOL`: 2
- `SETRA`: 1
- `EFL`: 1
- `15`: 1
- `QUIM`: 1
- `PCG`: 1

Essas siglas não foram classificadas pelo histórico. Permanecem visíveis para decisão empresarial sobre inclusão ou não na legenda oficial.

## Saídas validadas

O XLSX agora contém quatro abas:

1. `Resumo`
2. `Referência`
3. `Alunos`
4. `Divergências`

A aba `Referência` soma exatamente o total extraído e usa a cor correta da competência.

Nos arquivos finais reabertos:

- Agosto: `Referência Agosto`, total 2.050, cor `#C04F15`.
- Setembro: `Referência Setembro`, total 2.211, cor `#E59EDD`.

O relatório PDF executivo contém a consolidação da referência. O PDF de lista completa contém `STATUS_CURSO` e `COMPETENCIA`.

## Testes

GitHub Actions na branch `feat/nova-interface`:

- instalação das dependências em Python 3.12: aprovada;
- suíte Python: aprovada;
- teste real condicionado a variáveis de ambiente: ignorado no CI por não versionarmos PDFs com dados;
- testes JavaScript da interface: aprovados;
- empacotamento da versão validada: aprovado.

Os PDFs reais foram processados separadamente, sem colocá-los no repositório. A leitura independente confirmou novamente 2.050 identificadores em agosto e 2.211 em setembro.

## Segurança e preservação

- PDFs reais, planilhas de dados e resultados continuam fora do Git.
- Identificadores permanecem texto, inclusive zeros à esquerda.
- O sistema continua local (`127.0.0.1`).
- Nenhum cálculo de faturamento/licença foi acrescentado.
- A planilha histórica original não é alterada.

## Pendências antes de merge

1. Inspeção visual final da interface no navegador local.
2. Decisão empresarial sobre as siglas ausentes da legenda oficial, principalmente `TEOC` e `EFB`.
3. A diferença de −2 em setembro permanece registrada e não deve ser compensada artificialmente.
4. Outros layouts de PDF e PDFs digitalizados continuam fora do escopo homologado.

A branch está tecnicamente consistente para teste local; o PR permanece em rascunho até a inspeção visual e a confirmação das siglas não mapeadas.
