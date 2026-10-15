# API Perseus interna — primeiro passo para uso compartilhado

**Estado:** protótipo backend-to-backend **não publicado na rede**. A versão local `app.py` em :8878 continua funcionando como antes. O novo `servico_interno.py` é separado e abre **somente 127.0.0.1:8879**.

## Objetivo

Permitir que, no futuro, um gateway autenticado do Portal UNH execute tarefas de conferência com motor Python sem expor relatórios de alunos nem segredos a navegadores ou outros setores.

```text
Navegador (autenticação institucional)
    ↓
Backend do Portal UNH / gateway (ainda NÃO implementado)
    ↓ chave de serviço mantida somente no servidor + identidade validada
servico_interno.py (Python em loopback, :8879)
    ↓
app.processar(…, registrar_biblioteca=False)
    ↓
arquivos temporários privados por tarefa → downloads autorizados
```

A chave de serviço **não autentica usuários**. O gateway futuro deve validar sessões, autorizações e setor, sobrescrever qualquer cabeçalho de identidade fornecido pelo cliente e transmitir apenas o ID autorizado. **Não disponibilizar este serviço por URL pública, LAN, Portainer ou proxy direto.**

## Iniciar para desenvolvimento local

No repositório privado Perseus, instale as dependências como habitualmente. Defina em variável de ambiente `PERSEUS_SERVICE_KEY` uma chave forte de pelo menos 32 caracteres aleatórios **nunca copiada para o GitHub**. Inicie:

```powershell
$env:PERSEUS_SERVICE_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
python servico_interno.py
```

Em outro terminal, teste o endpoint de saúde enviando o cabeçalho `X-Perseus-Service-Key`. A resposta será `{"estado":"operacional","modo":"somente-loopback"}`. O cabeçalho `X-UNH-Actor` identifica o usuário já validado pelo gateway futuro. **Não usar o endpoint diretamente no navegador**, e não colocar a chave em HTML, JavaScript ou URL.

## Contrato do protótipo (backend-to-backend)

- `GET /v1/saude`: exige chave de serviço; não exige usuário.
- `POST /v1/trabalhos`: exige chave e `X-UNH-Actor`; recebe bytes PDF com `Content-Type: application/pdf`, até 80 MB, e `X-Filename` opcional; responde HTTP 202 com identificador da tarefa.
- `GET /v1/trabalhos/{id}`: exige chave/usuário; retorna status, progresso, contagens e nomes dos arquivos autorizados; não expõe amostra dos registros, classificação individual ou metadados do PDF.
- `GET /v1/trabalhos/{id}/download/{nome}`: exige chave/usuário; apenas dono da tarefa pode obter ZIP, Excel e PDFs gerados. Entrada original e arquivos de outros trabalhos são bloqueados.
- HTTP 401 sem chave válida, 400 sem identidade, 404 para tarefa de outro usuário, 409 se houver processamento concorrente. `Origin` é recusado e não há CORS.

## Limites da versão de desenvolvimento

- Processa uma tarefa por vez; armazena estado em memória, sem fila persistente.
- Usa pasta temporária do sistema fora do repositório; apaga ao encerrar normalmente e expira trabalhos concluídos após 1h quando chegam novas requisições. Em caso de interrupção abrupta, restos precisam ser limpos operacionalmente.
- Não compartilha escrita em `biblioteca/nao_localizados.json` entre usuários; o resultado gerado para a tarefa continua contendo suas divergências.
- Sem login/LDAP, rate limiting distribuído, antivírus, limites por setor, TLS no gateway, auditoria persistente, política aprovada de retenção, backups, recuperação de jobs ou isolamento por processo/container.
- A chave de serviço permite representar uma identidade **somente porque o gateway confiável deverá preenchê-la**. Sem gateway autenticado não há proteção suficiente para uso multiusuário real.
- Nem o Portal UNH nem o serviço Python são publicados no servidor da instituição por esta entrega.

## Testes e próximos incrementos

```sh
python -m unittest test_servico_interno -v
python -m unittest discover -v
```

1. Conferir CI Linux/Windows e confirmar saídas do Perseus local existentes.
2. Desenhar e aprovar SSO/LDAP + autorização no backend do Portal UNH.
3. Implementar gateway que **não exponha** a chave ao cliente e associe job ao usuário autenticado.
4. Criar fila de processamento, isolamento, registros de auditoria sem PII e limpeza com SLA.
5. Homologar com TI e dados sintéticos antes de disponibilizar a colaboradores.
