# Checklist de Homologação (Release Interna)

## 1) Fluxo operacional diário
- Abrir `Nova Ordem` e selecionar cliente existente.
- Definir/alterar profissional responsável.
- Adicionar ao menos 1 serviço e 1 peça.
- Salvar e imprimir OS.
- Em `Consultar OS`, buscar por nome e por CPF.
- Alterar profissional diretamente na tabela e salvar.
- Mudar status: `Aguardando` -> `Em andamento` -> `Concluído` -> `Garantia`.
- Validar contador de 90 dias na lógica de garantia.

## 2) Relatórios
- Abrir `Relatórios > Produção por Profissional`.
- Buscar profissional por período (máx. 31 dias).
- Validar resumo e tabela.
- Baixar Excel de profissional.
- Baixar Excel mensal contábil.
- Baixar Excel operacional (serviços, peças e saídas).

## 3) Configurações
- Cadastrar e remover profissional.
- Definir profissional no campo "Profissional para envio automático ao contador".
- Salvar configuração de e-mail.
- Confirmar persistência após recarregar a página.

## 4) Critérios de aceite
- Nenhum erro em console durante os fluxos acima.
- Nenhum endpoint principal retorna erro 500.
- Exportações baixam arquivo e abrem no Excel/LibreOffice.
- Status e profissional da OS persistem corretamente após atualizar página.
