# Segurança da demonstração SolicitaFlow

Esta política descreve o laboratório público entregue em 13/11/2026 e suas
fronteiras. É uma demonstração de portfólio com dados fictícios, sem contas
corporativas reais ou homologação de um SaaS multiempresa. A arquitetura está em
[ARQUITETURA.md](ARQUITETURA.md); os procedimentos operacionais, em
[DEPLOY_PUBLICO.md](DEPLOY_PUBLICO.md).

## Identidade, isolamento e autorização

A entrada sem senha emite uma sessão opaca de laboratório, aleatória, com hash
armazenado no banco. O workspace e os personagens são fictícios. A troca de papel
revoga a sessão anterior e só pode ocorrer nesse contexto isolado. Não permite
impersonar contas reais. IP, nome do workspace e cabeçalho de contexto não
comprovam identidade nem recuperam uma sessão expirada.

O backend confere tipo de sessão, workspace, perfil e propriedade do recurso. O
colaborador consulta seus pedidos; o departamento atua nos casos destinados a ele;
a central consulta seu ambiente. FKs compostas e índices únicos reforçam os vínculos
e impedem encaminhamento duplicado. Esconder uma opção no frontend não substitui
autorização. O isolamento da demonstração é da aplicação; não se afirma que todas
as tabelas tenham políticas RLS de um produto corporativo.

Na publicação, os cookies `__Host-sf_lab` são Secure, HttpOnly, SameSite Strict,
Path `/`, sem Domain. Mutações exigem origem HTTPS exata, JSON, contexto e
Fetch Metadata coerentes. Não há CORS aberto. O login corporativo, a API legada,
Swagger/OpenAPI e a interface técnica local não são expostos ao visitante.

## Fronteira HTTPS e proxy

React compilado e `/api` compartilham a origem pública. O backend aplica Host/Origin
explícitos, CSP, HSTS, bloqueio de frames e nosniff, além de limitar corpo, tempo de
envio e concorrência HTTP. O launcher não confia automaticamente em headers de proxy.

No transporte Render validado, somente o peer `127.0.0.1/32` pode afirmar
CF-Connecting-IP. X-Forwarded-For e X-Forwarded-Proto não alteram a identidade de rede
usada pela aplicação. O smoke real confirmou headers ignorados ou rejeitados na
borda. Essa allowlist deve ser revalidada se a topologia mudar; não usar confiança
irrestrita em proxies. Redes podem compartilhar cotas; não são identidade pessoal.

## IA, validação e proteção de créditos

A DeepSeek recebe somente título/descrição enviados pelo visitante. A interface
orienta usar dados inventados; não há garantia de detecção ou anonimização automática
de todo dado pessoal inserido indevidamente. Não enviar informações confidenciais.

A resposta precisa satisfazer o esquema e os catálogos. A prioridade vem da matriz
Python. O roteamento exige evidência do assunto, suficiência e destino ativo no mesmo
workspace; não depende só de confiança declarada pelo modelo. Falhas, ambiguidade ou
cotas preservam o pedido em exceção, sem sugestão fabricada.

Os [limites públicos ativos](../README.md#limites-ativos-da-demonstração) combinam
orçamento diário global, tokens, cotas por laboratório/rede, timeout e uma única
chamada simultânea. O ledger persiste antes do envio. Idempotência, locks de sessão
em conexão direta e reservas pendentes duráveis evitam repetir pagamentos após
queda de conexão ou reinício. Não há retry pago automático nem devolução automática
de uma reserva desconhecida. Não limpar contadores para contornar limites.

Consumo incerto bloqueia novas chamadas até conferência do operador. Esse envelope
limita a aplicação, não toda a conta do provedor ou outros consumidores da mesma
chave. Mudanças de preço/modelo exigem nova verificação. Não há desafio anti-bot
visual ou promessa de resistência a todo ataque; os limites conservadores podem
reduzir disponibilidade sob abuso.

## Banco, segredos e registros

- Banco público separado dos bancos locais; nenhuma importação automática de dados.
- Conexão Neon direta, TLS `verify-full`, CA confiável; sem locks de sessão em PgBouncer transacional.
- Runtime `ai_classifier_app` sem superusuário, owner, DDL ou TRUNCATE; eventos sem UPDATE/DELETE e ledger sem DELETE.
- Credenciais de migração e limpeza distintas, conforme [privilégios mínimos](DEPLOY_PUBLICO.md#banco-migrações-e-privilégios).
- Segredos exclusivamente no backend e armazenamento operacional privado; nunca em `VITE_*`, commits, argumentos ou capturas.
- Logs da aplicação registram classe/SQLSTATE, sem valores SQL, prompts, resposta bruta ou chaves; acesso HTTP não é logado pelo launcher.

A varredura do deploy examinou 315 blobs contra oito valores privados conhecidos e
padrões comuns, sem achados. Isso não garante ausência de todo segredo histórico
desconhecido. Em incidente, colocar o serviço em manutenção ou suspendê-lo; avaliar
consumidores antes de rotacionar/revogar uma chave compartilhada.

## Expiração, retenção e recuperação

Sessões de laboratório têm validade de até duas horas, limitada pela expiração do
workspace em 24 horas. Retomar uma sessão válida não renova seu prazo. Trocar de
personagem emite nova sessão, também limitada pelo prazo do workspace.

Na próxima atividade, no máximo uma limpeza por hora, laboratórios expirados são
anonimizados. Metadados/consumo mínimos ficam por 32 dias; só depois ocorre expurgo,
sem remover consumo recente ou reservas desconhecidas. Ambientes ativos e locais
não são alvo. Ocioso não significa remoção física imediata. Backups têm retenção
manual própria; detalhes e restauração comprovada estão no guia de deploy.

## Testes e limites de interpretação

O CI exercita autorização, dois visitantes, CSRF, expiração, retomada, idempotência,
concorrência, perda do lock, worker interrompido, cotas e falhas do provedor. IA é
simulada/bloqueada nos testes; dados destrutivos ficam em bancos efêmeros ou no
banco local de testes com preflight. Os testes públicos de rotina devem se limitar
a verificações de leitura, sem criar pedidos pagos para monitorar disponibilidade.

Resultados do marco: [ENCERRAMENTO.md](ENCERRAMENTO.md). Não representam pentest
independente, certificação de conformidade ou garantia de operação empresarial.
