# 🧠 Web Scraping Acadêmico com Análise de Tópicos e Sentimentos – Foco em Computação Quântica

Este projeto realiza o **web scraping automatizado** de artigos científicos do [Google Acadêmico](https://scholar.google.com.br) com foco em tópicos relacionados à **Computação Quântica**, seguido de um pipeline completo de **tratamento, análise e visualização dos dados** coletados.

---

## 🔍 Objetivo

Extrair, armazenar e analisar publicações recentes (2024–2025) em áreas como:

- Computação Quântica e Criptografia  
- Inteligência Artificial Quântica  
- Química Computacional Quântica  
- Aplicações futuras e desafios da computação quântica

---

## 🧰 Tecnologias Utilizadas

- **Python**
- **Selenium** (automação de navegador)
- **SQLite** (banco de dados local)
- **Pandas / Matplotlib / Seaborn** (análise e visualização de dados)
- **NLTK / WordCloud** (processamento de linguagem natural)
- **Scikit-Learn** (LDA para modelagem de tópicos)

---

## 📦 Estrutura

- `web_scrap_dt.py`: automatiza a navegação no Google Acadêmico, coleta os dados e armazena em um banco SQLite  
- `tratamento.py`: realiza a limpeza dos textos, remoção de stopwords, criação de nuvem de palavras, análise de sentimentos e tópicos com LDA  
- `buscas_completas_CQ.db`: base local onde os dados extraídos são salvos

---

## 📊 Funcionalidades

- Extração de dados bibliográficos de forma robusta e escalável  
- Pré-processamento textual com foco em artigos acadêmicos  
- Geração de **nuvem de palavras-chave**  
- Análise de **sentimentos rudimentar** baseada em palavras positivas/negativas  
- Identificação de **tópicos predominantes com LDA**  
- Visualizações temporais: volume de publicações por ano e tendências de tópicos

---

## ✅ Resultados Esperados

- Identificação de temas emergentes em Computação Quântica  
- Mapeamento das tendências acadêmicas por ano  
- Insights visuais e estruturados para apoiar revisões sistemáticas

---

## 📌 Requisitos

- Python 3.8+  
- Navegador **Microsoft Edge** com **driver compatível**  
- Instalar dependências:  
  ```bash
  pip install -r requirements.txt
