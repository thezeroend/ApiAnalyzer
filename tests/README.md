# 🧪 Scripts de Teste - API Log Analyzer

Esta pasta contém todos os scripts de teste para validar e demonstrar as funcionalidades do sistema de análise de anomalias em logs de API.

## 📋 Índice

- [Scripts Básicos](#scripts-básicos)
- [Scripts de Machine Learning](#scripts-de-machine-learning)
- [Scripts de Feedback](#scripts-de-feedback)
- [Scripts de Configuração](#scripts-de-configuração)
- [Scripts Específicos](#scripts-específicos)
- [Como Executar](#como-executar)

## 🚀 Scripts Básicos

### `test_simple.py`
**Descrição:** Teste básico para verificar se o backend está funcionando e enviar alguns logs simples.

**Funcionalidades:**
- Verifica se o backend está rodando
- Envia logs básicos para a API
- Testa endpoints fundamentais

**Uso:**
```bash
python test_simple.py
```

### `quick_test.py`
**Descrição:** Teste rápido para verificar funcionalidades básicas do sistema.

**Funcionalidades:**
- Teste de conectividade
- Envio de logs de teste
- Verificação de endpoints

**Uso:**
```bash
python quick_test.py
```

## 🤖 Scripts de Machine Learning

### `test_ml.py`
**Descrição:** Teste completo do sistema de Machine Learning com dados realistas.

**Funcionalidades:**
- Gera logs com padrões normais e anômalos
- Treina modelos de ML
- Detecta anomalias
- Mostra estatísticas de detecção

**Uso:**
```bash
python test_ml.py
```

### `test_ml_simple.py`
**Descrição:** Versão simplificada do teste de ML para testes rápidos.

**Funcionalidades:**
- Teste básico de treinamento e detecção
- Menos dados, execução mais rápida

**Uso:**
```bash
python test_ml_simple.py
```

### `test_ml_detailed.py`
**Descrição:** Teste detalhado que mostra informações completas sobre as anomalias detectadas.

**Funcionalidades:**
- Exibe detalhes completos de cada anomalia
- Mostra scores de diferentes modelos
- Compara resultados entre algoritmos

**Uso:**
```bash
python test_ml_detailed.py
```

### `test_realistic.py`
**Descrição:** Gera dados mais realistas com menor proporção de anomalias.

**Funcionalidades:**
- Simula cenários mais próximos da realidade
- Proporção controlada de anomalias
- Padrões de tráfego realistas

**Uso:**
```bash
python test_realistic.py
```

### `test_network_anomaly.py`
**Descrição:** Teste específico para detecção de anomalias de rede.

**Funcionalidades:**
- Gera logs com IPs em faixas específicas
- Testa detecção de anomalias baseadas em IP
- Avalia precisão do sistema

**Uso:**
```bash
python test_network_anomaly.py
```

## 🏷️ Scripts de Feedback

### `test_feedback.py`
**Descrição:** Teste básico do sistema de feedback.

**Funcionalidades:**
- Marca falsos positivos
- Marca verdadeiros positivos
- Testa endpoints de feedback

**Uso:**
```bash
python test_feedback.py
```

### `test_feedback_interface.py`
**Descrição:** Teste da interface de feedback.

**Funcionalidades:**
- Simula interações com a interface web
- Testa funcionalidades de feedback via frontend

**Uso:**
```bash
python test_feedback_interface.py
```

### `test_feedback_fix.py`
**Descrição:** Teste para corrigir problemas específicos do sistema de feedback.

**Funcionalidades:**
- Corrige erros de serialização
- Testa campos específicos do feedback

**Uso:**
```bash
python test_feedback_fix.py
```

### `test_feedback_filter.py`
**Descrição:** Testa o filtro de logs já marcados com feedback.

**Funcionalidades:**
- Verifica se logs com feedback são filtrados
- Testa a funcionalidade de não mostrar anomalias já marcadas

**Uso:**
```bash
python test_feedback_filter.py
```

### `test_retrain_effectiveness.py`
**Descrição:** Testa a eficácia do retreinamento com feedback.

**Funcionalidades:**
- Compara performance antes e depois do retreinamento
- Avalia redução de falsos positivos
- Mede melhoria na precisão

**Uso:**
```bash
python test_retrain_effectiveness.py
```

### `test_retrain_effectiveness_v2.py`
**Descrição:** Versão melhorada do teste de eficácia de retreinamento.

**Funcionalidades:**
- Teste mais robusto e detalhado
- Métricas mais precisas
- Melhor análise de resultados

**Uso:**
```bash
python test_retrain_effectiveness_v2.py
```

### `test_retrain_effectiveness_v3.py`
**Descrição:** Versão final e otimizada do teste de retreinamento.

**Funcionalidades:**
- Teste completo e otimizado
- Análise estatística detalhada
- Relatórios de performance

**Uso:**
```bash
python test_retrain_effectiveness_v3.py
```

## ⚙️ Scripts de Configuração

### `test_config.py`
**Descrição:** Teste básico do sistema de configurações.

**Funcionalidades:**
- Testa leitura de configurações
- Testa atualização de parâmetros
- Verifica persistência de configurações

**Uso:**
```bash
python test_config.py
```

### `test_config_complete.py`
**Descrição:** Teste completo do sistema de configurações.

**Funcionalidades:**
- Testa todas as funcionalidades de configuração
- Valida diferentes tipos de parâmetros
- Testa restauração de padrões

**Uso:**
```bash
python test_config_complete.py
```

## 🎯 Scripts Específicos

### `test_anomalies.py`
**Descrição:** Teste específico para detecção de anomalias.

**Funcionalidades:**
- Foca apenas na detecção
- Análise detalhada de anomalias
- Comparação de algoritmos

**Uso:**
```bash
python test_anomalies.py
```

### `test_model_storage.py`
**Descrição:** Testa o armazenamento e carregamento de modelos.

**Funcionalidades:**
- Verifica persistência de modelos
- Testa carregamento de modelos salvos
- Valida integridade dos dados

**Uso:**
```bash
python test_model_storage.py
```

### `test_anomaly_description.py`
**Descrição:** Teste para verificar se as descrições de anomalias estão sendo geradas corretamente.

**Funcionalidades:**
- Verifica se as descrições explicativas das anomalias são geradas
- Testa diferentes tipos de anomalias (horário, erro, admin, etc.)
- Avalia a qualidade das descrições geradas

**Uso:**
```bash
python test_anomaly_description.py
```

### `test_ip_changes.py`
**Descrição:** Teste específico para verificar a detecção de mudanças de IP nas descrições de anomalias.

**Funcionalidades:**
- Testa detecção de mudanças de IP privado para público
- Verifica múltiplos IPs usados pelo mesmo cliente
- Analisa novos IPs nunca vistos antes
- Avalia mudanças frequentes de IP em pouco tempo

**Cenários testados:**
- Cliente que muda de IP privado (192.168.1.100) para público (203.45.67.89)
- Cliente que usa múltiplos IPs em sequência rápida
- Cliente que aparece com IP completamente novo
- Cliente normal como controle

**Uso:**
```bash
python test_ip_changes.py
```

### `test_true_positives.py`
**Descrição:** Teste específico para verdadeiros positivos.

**Funcionalidades:**
- Gera cenários com anomalias conhecidas
- Avalia taxa de detecção de verdadeiros positivos
- Mede precisão do sistema

**Uso:**
```bash
python test_true_positives.py
```

### `test_false_positive_filter.py`
**Descrição:** Testa o filtro de falsos positivos.

**Funcionalidades:**
- Verifica se falsos positivos são filtrados corretamente
- Testa a lógica de filtragem
- Avalia performance do filtro

**Uso:**
```bash
python test_false_positive_filter.py
```

## 🚀 Como Executar

### Pré-requisitos

1. **Backend rodando:**
   ```bash
   python main.py
   ```

2. **Dependências instaladas:**
   ```bash
   pip install -r requirements.txt
   ```

3. **MongoDB configurado:**
   - Certifique-se de que o MongoDB está rodando
   - Verifique as configurações de conexão

### Execução Básica

**⚠️ IMPORTANTE:** Use o terminal WSL para executar os testes, pois o Python do Windows pode não funcionar corretamente.

1. **Navegue para a pasta de testes:**
   ```bash
   cd tests
   ```

2. **Execute um teste específico:**
   ```bash
   wsl python3 nome_do_teste.py
   ```

3. **Execute todos os testes básicos:**
   ```bash
   wsl python3 test_simple.py
   wsl python3 test_ml.py
   wsl python3 test_feedback.py
   ```

### Execução no WSL (Recomendado)

Para executar os testes no ambiente WSL:

```bash
# No terminal WSL
cd /c/Users/mathe/workspace/api-log-analyzer/tests
python3 test_ml.py
```

### Execução Alternativa (se WSL não estiver disponível)

Se você não puder usar o WSL, execute os testes a partir do diretório raiz:

```bash
# No diretório raiz do projeto
python tests/test_ml.py
```

### Interpretação dos Resultados

- **✅ Sucesso:** Teste executado sem erros
- **❌ Erro:** Verifique logs e configurações
- **⚠️ Aviso:** Problemas menores que não impedem execução

### Logs e Debug

Para ver logs detalhados, execute com verbose:

```bash
wsl python3 -u test_ml.py 2>&1 | tee test_output.log
```

## 📊 Métricas de Teste

### Performance Esperada

- **Taxa de Detecção:** > 90% para anomalias reais
- **Falsos Positivos:** < 10% em cenários normais
- **Tempo de Execução:** < 30 segundos para testes básicos

### Configurações Recomendadas

- **Threshold:** 0.12 (padrão)
- **Horas para trás:** 24 (padrão)
- **Mínimo de logs:** 100 para treinamento

## 🔧 Troubleshooting

### Problemas Comuns

1. **Backend não responde:**
   - Verifique se `main.py` está rodando
   - Confirme porta 8000 está livre

2. **Erro de conexão MongoDB:**
   - Verifique se MongoDB está rodando
   - Confirme configurações de conexão

3. **Erro de importação:**
   - Instale dependências: `pip install -r requirements.txt`
   - Verifique versões das bibliotecas

### Logs de Debug

Para habilitar logs detalhados, adicione no início dos scripts:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Contribuindo

Para adicionar novos testes:

1. Crie o arquivo na pasta `tests/`
2. Use o padrão de nomenclatura `test_*.py`
3. Adicione documentação no README
4. Teste em diferentes cenários

## 📞 Suporte

Para problemas com os testes:

1. Verifique os logs de erro
2. Confirme configurações do sistema
3. Teste com dados menores primeiro
4. Consulte a documentação principal

---

**Última atualização:** Dezembro 2024  
**Versão:** 1.0.0

# 📊 Testes do API Log Analyzer

Este diretório contém scripts de teste para validar as funcionalidades do sistema de detecção de anomalias.

## 🧪 Scripts de Teste

### 1. `test_network_anomaly.py`
**Objetivo:** Testa detecção de anomalias baseadas em padrões de rede
- Gera 10.000 logs normais de uma faixa de IP específica
- Gera 100 logs anômalos de outra faixa de IP
- Testa diferentes thresholds de detecção
- Valida redução de falsos positivos

**Uso:**
```bash
python tests/test_network_anomaly.py
```

**Métricas Esperadas:**
- Precisão: >95%
- Falsos positivos: <5%
- Verdadeiros positivos: >90%

### 2. `test_timeline.py`
**Objetivo:** Testa a funcionalidade de timeline temporal de anomalias
- Gera dados de teste com padrões temporais específicos
- Testa agrupamento por diferentes intervalos (15min, 30min, 1h)
- Valida geração de dados para gráficos
- Testa exportação de dados temporais

**Uso:**
```bash
python tests/test_timeline.py
```

**Funcionalidades Testadas:**
- Endpoint `/ml/anomalies-timeline`
- Agrupamento temporal de anomalias
- Geração de dados para Chart.js
- Exportação de dados JSON
- Diferentes modelos ML (iforest, lof)

**Métricas Esperadas:**
- Dados temporais gerados corretamente
- Gráficos com múltiplos datasets
- Exportação funcional
- Performance adequada

### 3. `test_ip_changes.py`
**Objetivo:** Testa detecção de mudanças de endereços IP
- Simula clientes acessando de múltiplos IPs
- Testa detecção de comportamento suspeito
- Valida descrições de anomalias

**Uso:**
```bash
python tests/test_ip_changes.py
```

### 4. `test_config.py`
**Objetivo:** Testa o sistema de configurações
- Valida leitura/escrita de configurações
- Testa diferentes seções (ml_detection, feedback, etc.)
- Verifica persistência de configurações

**Uso:**
```bash
python tests/test_config.py
```

### 5. `test_config_complete.py`
**Objetivo:** Teste completo do sistema de configurações
- Testa todas as funcionalidades de configuração
- Valida integração com detecção ML
- Testa reset e histórico

**Uso:**
```bash
python tests/test_config_complete.py
```

### 6. `test_retrain_effectiveness.py`
**Objetivo:** Testa eficácia do retreinamento com feedback
- Simula feedback de falsos positivos
- Valida melhoria na precisão após retreinamento
- Testa redução de falsos positivos

**Uso:**
```bash
python tests/test_retrain_effectiveness.py
```

### 7. `test_ml_detailed.py`
**Objetivo:** Teste detalhado de detecção ML
- Testa todos os modelos disponíveis
- Compara performance entre modelos
- Valida scores de anomalia

**Uso:**
```bash
python tests/test_ml_detailed.py
```

### 8. `test_feedback.py`
**Objetivo:** Testa sistema de feedback
- Testa marcação de falsos/verdadeiros positivos
- Valida armazenamento de feedback
- Testa histórico e estatísticas

**Uso:**
```bash
python tests/test_feedback.py
```

## 🚀 Como Executar os Testes

### Pré-requisitos
1. Backend rodando: `python main.py`
2. Dependências instaladas: `pip install -r requirements.txt`

### Execução Individual
```bash
# Executar teste específico
python tests/test_timeline.py

# Executar com output detalhado
python -u tests/test_timeline.py
```

### Execução em Lote
```bash
# Executar todos os testes
python tests/test_all_scripts.py
```

## 📊 Interpretação dos Resultados

### Métricas de Performance
- **Precisão:** Porcentagem de detecções corretas
- **Falsos Positivos:** Anomalias detectadas incorretamente
- **Verdadeiros Positivos:** Anomalias reais detectadas
- **Tempo de Processamento:** Performance do sistema

### Indicadores de Sucesso
- ✅ Precisão > 90%
- ✅ Falsos positivos < 10%
- ✅ Tempo de resposta < 5s
- ✅ Dados exportados corretamente

### Troubleshooting

#### Erro de Conexão
```
❌ Erro ao conectar com o backend
```
**Solução:** Verifique se o backend está rodando em `http://localhost:8000`

#### Erro de Modelo Não Encontrado
```
❌ Modelo iforest não encontrado
```
**Solução:** Execute o treinamento primeiro ou use outro modelo

#### Erro de Dados Insuficientes
```
❌ Nenhum log encontrado
```
**Solução:** Gere mais dados de teste ou ajuste o período

#### Performance Lenta
```
⏳ Processamento demorado
```
**Solução:** 
- Reduza o número de logs de teste
- Ajuste o período de análise
- Verifique recursos do sistema

## 🔧 Configuração de Testes

### Variáveis de Ambiente
```bash
export API_BASE="http://localhost:8000"
export TEST_API_ID="api_test"
export TEST_HOURS_BACK=24
```

### Parâmetros de Teste
- **API_ID:** Identificador da API para teste
- **Hours_Back:** Período de análise em horas
- **Model_Name:** Modelo ML a ser testado
- **Threshold:** Sensibilidade da detecção

## 📈 Melhorias Contínuas

### Novos Testes
Para adicionar novos testes:
1. Crie script seguindo o padrão `test_*.py`
2. Implemente função `main()` com validações
3. Adicione documentação no README
4. Inclua no `test_all_scripts.py`

### Padrões de Teste
- Use nomes descritivos para logs de teste
- Implemente validação de resultados
- Inclua métricas de performance
- Documente casos de erro

### Integração
- Testes são executados automaticamente
- Resultados são logados para análise
- Falhas são reportadas com contexto
- Performance é monitorada continuamente 