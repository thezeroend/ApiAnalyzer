# 🚨 Guia de Uso - Sistema de Feedback de Anomalias

## 📋 Visão Geral

O sistema agora possui uma interface melhorada para facilitar o feedback sobre anomalias detectadas. A nova interface permite:

- ✅ Visualizar anomalias detectadas de forma clara
- ✅ Dar feedback com um clique (falso positivo ou verdadeiro positivo)
- ✅ Ver histórico de feedbacks
- ✅ Retreinar o modelo com base no feedback
- ✅ Melhorar a precisão do sistema ao longo do tempo

## 🎯 Como Usar a Interface

### 1. **Acessar a Interface**
- Abra o arquivo `frontend.html` no seu navegador
- Certifique-se de que o backend está rodando (`python main.py`)

### 2. **Seção "Anomalias Detectadas"** (Nova!)
Esta é a seção principal para feedback:

1. **Digite o API ID** no campo (ex: `api_realistic`)
2. **Clique em "🔍 Carregar Anomalias"**
3. **Aguarde** a detecção de anomalias
4. **Visualize** as anomalias em cards organizados

### 3. **Dar Feedback nas Anomalias**

Cada anomalia detectada será exibida em um card com:

- **Informações da anomalia**: Cliente, IP, método, path, status, tempo de resposta
- **Score da anomalia**: Quão anômala o sistema considera
- **Botões de feedback**:
  - ❌ **Falso Positivo**: Clique se esta NÃO é uma anomalia real
  - ✅ **Verdadeiro Positivo**: Clique se esta É uma anomalia real

### 4. **Seção "Feedback de Anomalias"**
Para gerenciar feedbacks:

- **📊 Estatísticas de Feedback**: Ver quantos feedbacks foram dados
- **📋 Histórico de Feedback**: Ver todos os feedbacks anteriores
- **🎯 Retreinar Modelo**: Aplicar feedbacks para melhorar o modelo

## 🔧 Funcionalidades Detalhadas

### **Visualização de Anomalias**
- Cards organizados com informações completas
- Score de anomalia destacado
- Timestamp formatado
- Status colorido (verde para sucesso, vermelho para erro)

### **Sistema de Feedback**
- **Falso Positivo**: Marca que o sistema errou ao detectar como anomalia
- **Verdadeiro Positivo**: Confirma que é realmente uma anomalia
- Feedback é armazenado com score e features da anomalia
- Comentários automáticos para rastreamento

### **Histórico de Feedback**
- Lista todos os feedbacks dados
- Mostra tipo (falso/verdadeiro positivo)
- Status de processamento
- Detalhes da anomalia original

### **Retreinamento Inteligente**
- Usa feedbacks de falsos positivos para melhorar o modelo
- Ajusta pesos para reduzir falsos positivos
- Mantém precisão para verdadeiros positivos

## 📊 Exemplo de Uso

### Cenário 1: Detectar e Dar Feedback
1. Digite `api_realistic` no campo API ID
2. Clique "🔍 Carregar Anomalias"
3. Veja as anomalias detectadas
4. Para cada anomalia:
   - Se for um comportamento normal: clique "❌ Falso Positivo"
   - Se for realmente suspeito: clique "✅ Verdadeiro Positivo"

### Cenário 2: Verificar Histórico
1. Vá para a seção "Feedback de Anomalias"
2. Digite o API ID
3. Clique "📋 Histórico de Feedback"
4. Veja todos os feedbacks anteriores

### Cenário 3: Melhorar o Modelo
1. Após dar vários feedbacks
2. Vá para "Feedback de Anomalias"
3. Clique "🎯 Retreinar Modelo"
4. O sistema usará seus feedbacks para melhorar

## 🎨 Interface Visual

### **Cards de Anomalias**
- Header colorido com score e timestamp
- Botões de feedback bem visíveis
- Informações organizadas em linhas
- Hover effects para melhor UX

### **Instruções Claras**
- Texto explicativo sobre como usar
- Ícones intuitivos
- Cores consistentes (vermelho para falso, verde para verdadeiro)

### **Responsividade**
- Interface funciona em diferentes tamanhos de tela
- Botões se adaptam ao espaço disponível
- Layout flexível

## 🔍 Troubleshooting

### **Problema**: Botões não aparecem
**Solução**: Verifique se o backend está rodando e se há anomalias detectadas

### **Problema**: Erro 500 no histórico
**Solução**: Verifique se o MongoDB está rodando e acessível

### **Problema**: Feedback não é registrado
**Solução**: Verifique o console do navegador para erros de conexão

### **Problema**: Anomalias não são detectadas
**Solução**: 
1. Verifique se há logs no sistema
2. Tente treinar os modelos primeiro
3. Ajuste o parâmetro de horas para trás

## 📈 Benefícios do Sistema

1. **Melhoria Contínua**: O modelo aprende com seus feedbacks
2. **Redução de Falsos Positivos**: Menos alertas desnecessários
3. **Maior Precisão**: Sistema mais confiável ao longo do tempo
4. **Interface Intuitiva**: Fácil de usar mesmo para não técnicos
5. **Rastreabilidade**: Histórico completo de decisões

## 🚀 Próximos Passos

1. **Use a interface** para dar feedback nas anomalias
2. **Monitore o histórico** para ver a evolução
3. **Retreine periodicamente** para melhorar o modelo
4. **Reporte problemas** se encontrar bugs ou melhorias

---

**💡 Dica**: Comece com poucos feedbacks e vá aumentando gradualmente. O sistema funciona melhor com feedback consistente e bem pensado. 