# Regras verificadas no código, pendentes de homologação no banco

Inspeção em 08/11/2026. Fontes: repositórios `ErisonNeto/Central-de-Indicadores`, `J-T-SLA`, `J-T-T0`, `J-T-Shipping-Time`, `J-T-Capotamento`, `J-T-SemMov-and-Retidos`, `J-T--1BD-5CD-CSAT`, `J-T-AVARIA-EXTRAVIO-PNR`. SHAs no relatório de validação. Código não prova o estado do banco em execução.

| Indicador | Fonte / data | Fórmula implementada | Ressalva |
|---|---|---|---|
| SLA | entregas / data_sla | SUM(no_prazo) / COUNT × 100 | Nulos de no_prazo contam como não cumprido, conforme Central |
| T0 | t0_diario / data | SUM(t0_ok) / SUM(total_pedidos) × 100 | Sem média simples de taxas |
| Shipping | shipping_time_diario / data | SUM((etapa_6_h + etapa_7_h + etapa_8_h) × pacotes) / SUM(pacotes) | Etapas nulas são excluídas, não zero; nesta versão exibe total, detalhamento por etapa pendente |
| Capotamento | capotamento_diario / data | registros ALERTA ou CAPOTADA / registros × 100 | Denominador é base-dia; não base única mensal |
| Sem mov / Retidos | sem_mov_retidos_detalhe / data | SUM(pedidos) para aging_valor > 3 e > 10 | Acumulados são snapshots, não remessas únicas; >10 também está em >3 |
| 1BD | jt_1bd_registros / data_avaliacao | SUM(entregue) / COUNT × 100 | D-2; código via jt_1bd_gestao; gestor por vigência |
| 5CD | jt_5cd_registros / data_relatorio | volume / dias com registros no recorte | D-2; não percentual; sem inferir zero quando não há relatório |
| Avaria / Extravio / PNR | jt_arbitragem_ocorrencias / fechada_em | SUM(valor_centavos) / 100 e quantidade | Somente PROCESSO ENCERRADO e ARBITRAGEM FINALIZADA; nulos de fechamento excluídos |
| CSAT | Não identificada | Não implementada | Não inventar fonte ou fórmula |

Todas as consultas incluem código da base e a vigência da regional. S/C é fornecido pela vigência validada. Bases do Johan podem ser atribuídas no contrato histórico sem duplicar o mesmo registro por coordenador e supervisor.

Diferenças deliberadas a homologar: a Central usa fallback de fechamento para declaração/data em arbitragem; JARVIS exige fechamento. Shipping na Central converte etapas nulas para zero e recorta códigos por SLA; JARVIS exclui etapas incompletas e usa vigência documental. A gestão corrente da Qualidade não comprova histórico. Não se afirmou paridade para esses casos.

Meta: o código atual da Central tem SLA diário 95% e mensal 97%, T0 70%, 1BD 80%. O histórico da conversa menciona SLA 100%. Para não escolher uma regra conflitante, a v0.1 não classifica metas automaticamente. Homologar metas e vigências antes de adicionar tal classificação.

Datas: Brasília. D-1 para operação, D-2 para Qualidade. Arbitragem abre segunda a domingo. Semana anterior completa é a semana anterior à data final selecionada; comparação de mesmos dias subtrai sete dias de ambas as datas. O gráfico mantém valores nulos como sem dados e informa dias presentes; cobertura não comprova carga completa.

Validação: conferir nomes e tipos via CLI discover, cardinalidade dos mapeamentos, amostras de início/fim de vigência, duas bases transferidas, status de arbitragem e cargas com datas ausentes. Só habilitar cada indicador após confronto com uma consulta de referência aprovada.
