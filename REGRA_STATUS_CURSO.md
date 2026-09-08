# Regra oficial — STATUS_CURSO e Referência

Este documento é a fonte de contexto da etapa de classificação/consolidação do Perseus. Ele não altera as regras de extração do PDF.

## Fonte de negócio

A fonte oficial para classificar cursos é a aba `Legenda_Cursos_Status` da planilha **Fatura Perseus - SET 1.xlsx** fornecida para o processo.

O histórico das abas mensais pode ser comparado para diagnóstico, mas **não pode sobrescrever a legenda oficial**. Isso evita que classificações manuais antigas incorretas sejam transformadas em regra.

## Saída operacional

Cada registro extraído recebe:

- `STATUS_CURSO`
- `COMPETENCIA`

Categorias usadas na consolidação:

1. GRADUAÇÃO
2. MESTRADO
3. DI
4. MBA
5. POS
6. CURSO LIVRE
7. APERFEIÇOAMENTO
8. NÃO LOCALIZADO
9. MÚLTIPLAS CATEGORIAS

## Como classificar

1. Separe o campo `Curso` somente por vírgula, preservando o conteúdo original do registro.
2. Consulte cada sigla na legenda oficial.
3. Se todas as siglas encontradas pertencem à mesma categoria, o registro recebe essa categoria, mesmo que a sigla se repita.
4. Se as siglas encontradas pertencem a categorias diferentes, o registro recebe `MÚLTIPLAS CATEGORIAS`.
5. Se qualquer sigla não existir na legenda oficial, o registro recebe `NÃO LOCALIZADO` e permanece como `REVISAR`.
6. O sistema nunca cria, remove ou duplica alunos para fechar totais.

Exemplos importantes:

- `CIB` → `DI`
- `CEXT, CIB` → `DI`
- `ESGSC, PSO` → `POS`
- `DIREM, MBAAD` → `MÚLTIPLAS CATEGORIAS`
- `DA, DIR` → `MÚLTIPLAS CATEGORIAS`
- `EVE` → `CURSO LIVRE`
- `LPI` (enquanto não estiver na legenda) → `NÃO LOCALIZADO` + revisão

## COMPETENCIA

O campo segue a nomenclatura operacional observada na planilha. Para 2026:

- Fevereiro → `Fatura_Final_Ref_Fevereiro_2026`
- Março → `Fatura_Final_Ref_Março_2026`
- Abril → `Fatura_Final_Ref_Abril_2026`
- Maio → `Fatura_Final_Ref_Maio_2026`
- Junho → `Fatura_Final_Ref_Junho_2026`
- Julho → `Fatura_Final_Ref_Julho_2026`
- Agosto → `Fatura_Final_Ref_Agosto_2026`
- Setembro → `Fatura_Final_Ref_Setembro`

Para competências futuras ainda não observadas na fonte, o fallback é `Fatura_Final_Ref_<Mês>_<Ano>`.

## Cores de Referência

As cores abaixo são as cores efetivas dos cabeçalhos/totais da aba `Licenças Base`, já considerando tema e tonalidade aplicados pelo Excel:

- Fevereiro: `#C2F1C8`
- Março: `#FBE3D6`
- Abril: `#F9F9F9`
- Maio: `#C2F1C8`
- Junho: `#F2AA84`
- Julho: `#F9F9F9`
- Agosto: `#C04F15`
- Setembro: `#E59EDD`

Meses sem cor observada usam um neutro institucional até que uma fonte oficial seja fornecida.

## Consolidação

A consolidação conta **um registro por aluno/linha extraída**, usando o `STATUS_CURSO` final daquele registro. A soma das nove categorias precisa ser igual ao total de registros extraídos. A consolidação não altera a conferência de quantidade do PDF.

## Limites

- Não calcula faturamento ou quantidade de licenças.
- Não corrige automaticamente a planilha mestre histórica.
- Não usa o histórico manual como regra oficial.
- Não altera o motor de leitura do PDF aprovado.
