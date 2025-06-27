import re
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

# ------------------------------ CONFIGURAÇÃO DO SELENIUM -----------------------------------------------------

opcoes_edge = webdriver.EdgeOptions() # Cria as opções do navegador Edge
opcoes_edge.add_argument("--start-maximized") # Maximiza a janela do navegador ao iniciar
opcoes_edge.add_argument("--disable-blink-features=AutomationControlled") # Desabilita a detecção de automação (útil para evitar bloqueios ou detecção de bot)

navegador = webdriver.Edge(options=opcoes_edge) # Inicia o navegador Edge com as opções configuradas

# ----------------------------- PARÂMETROS DE BUSCA E FILTRO ---------------------------------------------------
# Lista de tópicos de busca
topicos_busca = [
    "Computação Quântica na Criptografia",
    "Otimização Quântica em Finanças", "Inteligência Artificial e Aprendizado de Máquina Quântico",
    "Computação Quântica e Descoberta de Medicamentos", "Química Quântica Computacional",
    "Perspectivas Futuras da Computação Quântica", "Computação Quântica Pós-Quântica",
    "Desafios e Oportunidades na Era Quântica"
]

ano_inicio = 2024                                   # Ano inicial para o filtro de data
ano_fim = 2025                                      # Ano final para o filtro de data
min_resultados_por_topico = 1000                    # Número mínimo de resultados desejados POR TÓPICO

# -------------------- CONFIGURAR BANCO DE DADOS ------------------------------------------------------------
conexao_db = sqlite3.connect("buscas_completas_CQ.db")
cursor_db = conexao_db.cursor()

cursor_db.execute('''
    CREATE TABLE IF NOT EXISTS resultados_detalhados_CQ (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        termo TEXT NOT NULL,
        titulo TEXT NOT NULL,
        ano_publicacao INTEGER,
        autores TEXT,
        fonte_publicacao TEXT,
        resumo TEXT,
        url_artigo TEXT
    )
''')
conexao_db.commit() # Confirma

# -------------------------------- LOOP PARA CADA TÓPICO DE BUSCA ----------------------------------------------------------------
total_resultados_salvos_geral = 0 # Contador geral de resultados salvos

for termo_busca in topicos_busca:
    print(f"Iniciando busca para o tópico: '{termo_busca}'")

    resultados_extraidos_topico_atual = [] # Lista para armazenar resultados do tópico atual
    numero_pagina = 1                       # Contador de página para o tópico atual

    # Constrói a URL do Google Acadêmico com o termo de busca e o filtro de data.
    url_google_academico = (
        f"https://scholar.google.com.br/scholar?hl=pt-PT&as_sdt=0%2C5&q="
        f"{termo_busca.replace(' ', '+')}&as_ylo={ano_inicio}&as_yhi={ano_fim}"
    )

    # -------------------- ACESSO À PÁGINA PARA O TÓPICO ATUAL ----------------------------------------------------------
    print(f"Acessando: {url_google_academico}")
    navegador.get(url_google_academico)
    time.sleep(4) # Espera para a página carregar

    while len(resultados_extraidos_topico_atual) < min_resultados_por_topico:
        print(f"\n--- Extraindo resultados da Página {numero_pagina} para '{termo_busca}' (Total para tópico: {len(resultados_extraidos_topico_atual)}) ---")

        # Busca todos os blocos de resultados
        try:
            blocos_resultados = navegador.find_elements(By.CSS_SELECTOR, "div.gs_ri")
        except StaleElementReferenceException:
            print("Aviso: Elementos ficaram obsoletos, tentando recarregar.")
            time.sleep(2)
            blocos_resultados = navegador.find_elements(By.CSS_SELECTOR, "div.gs_ri")
        except Exception as e:
            print(f"Erro ao encontrar blocos de resultados: {e}")
            break

        if not blocos_resultados:
            print("Nenhum resultado encontrado nesta página ou fim da busca. Fim da paginação para este tópico.")
            break

        # Extrai os resultados da página atual
        for i, bloco in enumerate(blocos_resultados):
            if len(resultados_extraidos_topico_atual) >= min_resultados_por_topico:
                break

            titulo = "Título não encontrado"
            ano_publicacao = None
            autores = None
            fonte_publicacao = None
            resumo = None
            url_artigo = None

            try:
                # Tenta encontrar o título e a URL
                elemento_titulo = bloco.find_element(By.CSS_SELECTOR, "h3.gs_rt a")
                titulo = elemento_titulo.text
                url_artigo = elemento_titulo.get_attribute("href") # Obtém a URL do link do título
            except NoSuchElementException:
                pass

            try:
                # Tenta encontrar o elemento que contém informações de autor e ano
                elemento_autor_ano = bloco.find_element(By.CSS_SELECTOR, "div.gs_a")
                texto_autor_ano = elemento_autor_ano.text

                # Regex para extrair ano (ex: 2024), autores e fonte (o que vem antes do ano e depois dos autores)
                # Ex: "J. Doe, L. Smith - Journal of Quantum Physics, 2024 - Publisher"
                match_ano = re.search(r'\b(19|20)\d{2}\b', texto_autor_ano)
                if match_ano:
                    ano_publicacao = int(match_ano.group(0))
                    # Dividir a string para tentar pegar autores e fonte antes do ano
                    partes_antes_ano = texto_autor_ano.split(str(ano_publicacao))[0].strip()

                    if ' - ' in partes_antes_ano:
                        partes_separadas = partes_antes_ano.split(' - ', 1)
                        autores = partes_separadas[0].strip()
                        fonte_publicacao = partes_separadas[1].strip()
                    else: # Se não houver ' - ', assumir tudo como autores ou fonte
                        autores = partes_antes_ano.strip()
                        fonte_publicacao = "N/A" # Não conseguiu identificar a fonte claramente
                else: # Se não encontrar o ano, tentamos pegar autores/fonte sem o ano como referência
                    if ' - ' in texto_autor_ano:
                        partes_separadas = texto_autor_ano.split(' - ', 1)
                        autores = partes_separadas[0].strip()
                        fonte_publicacao = partes_separadas[1].strip()
                    else:
                        autores = texto_autor_ano.strip()
                        fonte_publicacao = "N/A"

            except NoSuchElementException:
                pass

            try:
                # Tenta encontrar o snippet/resumo
                elemento_resumo = bloco.find_element(By.CSS_SELECTOR, "div.gs_rs")
                resumo = elemento_resumo.text.strip().replace('...', '') # Remove '...' do final
            except NoSuchElementException:
                pass

            # Adiciona o resultado à lista do tópico atual
            resultados_extraidos_topico_atual.append({
                "termo": termo_busca,
                "titulo": titulo,
                "ano_publicacao": ano_publicacao,
                "autores": autores,
                "fonte_publicacao": fonte_publicacao,
                "resumo": resumo,
                "url_artigo": url_artigo
            })
            # print(f"- {titulo} (Ano: {ano_publicacao if ano_publicacao else 'N/A'}) - Total para tópico: {len(resultados_extraidos_topico_atual)}")

        # -------------------------------- NAVEGAÇÃO PARA A PRÓXIMA PÁGINA ---------------------------------------------
        botao_proxima_pagina_encontrado = False
        try:
            botao_proxima = navegador.find_element(By.ID, "gs_n")
            botao_proxima_pagina_encontrado = True
        except NoSuchElementException:
            try:
                botao_proxima = navegador.find_element(By.LINK_TEXT, "Próxima")
                botao_proxima_pagina_encontrado = True
            except NoSuchElementException:
                print("Não foi possível encontrar o botão 'Próxima'. Fim da paginação para este tópico.")
                break

        if botao_proxima_pagina_encontrado:
            try:
                botao_proxima.click()
                print("Clicou em 'Próxima página'.")
                time.sleep(4) # Espera a próxima página carregar
                numero_pagina += 1
            except Exception as e:
                print(f"Erro ao clicar no botão 'Próxima': {e}. Possível fim da paginação para este tópico.")
                break
        else:
            print("Não há mais páginas ou o botão 'Próxima' não foi encontrado. Fim da paginação para este tópico.")
            break

    # -------------------- INSERIR OS DADOS NA TABELA DO DB PARA O TÓPICO ATUAL --------------------
    print(f"Salvando {len(resultados_extraidos_topico_atual)} resultados para '{termo_busca}' no banco de dados...")
    for dados in resultados_extraidos_topico_atual:
        cursor_db.execute(
            "INSERT INTO resultados_detalhados_CQ (termo, titulo, ano_publicacao, autores, fonte_publicacao, resumo, url_artigo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (dados["termo"], dados["titulo"], dados["ano_publicacao"], dados["autores"], dados["fonte_publicacao"], dados["resumo"], dados["url_artigo"])
        )
    conexao_db.commit()

    total_resultados_salvos_geral += len(resultados_extraidos_topico_atual)
    print(f"Busca para '{termo_busca}' concluída. {len(resultados_extraidos_topico_atual)} resultados salvos.")

print(f"\n----------------------------------------------------------")
print(f"Processo de busca concluído para todos os tópicos.")
print(f"Total geral de resultados salvos: {total_resultados_salvos_geral}")
print(f"-------------------------------------------------------------")

time.sleep(3) # Pequena pausa antes de fechar

# ----------------------------------- FECHAR CONEXÕES -----------------------------------------------------------
navegador.quit()      # Fecha o navegador
conexao_db.close()    # Fecha a conexão db

print("Navegador e conexão com o banco de dados fechados.")