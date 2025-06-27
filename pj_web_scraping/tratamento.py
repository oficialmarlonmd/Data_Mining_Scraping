import re
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
import sys # <-- Adicione esta importação para 'sys'
import os  # <-- Adicione esta importação para 'os'

# --- Verifica e baixa pacotes NLTK ---
# O 'punkt' é essencial para nltk.tokenize
# O 'stopwords' é essencial para nltk.corpus.stopwords
required_nltk_data = ['stopwords', 'punkt']

print("Verificando e baixando recursos NLTK necessários...")

# O NLTK_DATA pode ser definido como uma variável de ambiente para um local específico
# Caso contrário, ele tentará baixar para um local padrão (AppData/Roaming/nltk_data no Windows)
# Ou no diretório do script se não tiver permissão para os locais padrão.
# Você pode tentar forçar um local se tiver problemas de permissão, por exemplo:
# nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))
# Mas primeiro, tente sem isso e confie no download padrão.

for recurso in required_nltk_data:
    try:
        nltk.data.find(f'corpora/{recurso}.zip') # Tenta encontrar o arquivo .zip primeiro
        print(f"Recurso '{recurso}' já baixado.")
    except LookupError:
        print(f"Baixando recurso '{recurso}'...")
        try:
            nltk.download(recurso)
            print(f"Download de '{recurso}' concluído com sucesso.")
        except Exception as e:
            print(f"ERRO: Falha ao baixar o recurso '{recurso}'.")
            print(f"Por favor, verifique sua conexão com a internet e as permissões de escrita em seu diretório de dados NLTK (geralmente em C:\\Users\\SeuUsuario\\AppData\\Roaming\\nltk_data).")
            print(f"Detalhes do erro: {e}")
            print("Não é possível prosseguir sem este recurso NLTK.")
            sys.exit(1) # Sai do script com um código de erro

# Importe 'stopwords' APENAS DEPOIS que você tiver certeza que 'nltk.download' foi executado com sucesso
from nltk.corpus import stopwords

# --- Conexão e leitura do banco ---
try:
    conn = sqlite3.connect("buscas_completas_CQ.db")
    df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
    conn.close()
    print("Dados carregados com sucesso do banco de dados.")
except Exception as e:
    print(f"Erro ao carregar dados do banco de dados: {e}")
    print(f"Certifique-se de que 'buscas_completas_CQ.db' está no mesmo diretório do script ou o caminho está correto.")
    sys.exit(1) # Sai se houver erro no carregamento do BD

# Se o DataFrame estiver vazio, não podemos prosseguir com as análises
if df.empty:
    print("DataFrame está vazio. Não foi possível carregar dados do banco de dados. As análises não podem ser realizadas.")
    sys.exit(1)

# --- Pré-processamento ---
print("Iniciando pré-processamento de texto...")
df['texto_completo'] = df['titulo'].fillna('') + ' ' + df['resumo'].fillna('')
df['texto_limpo'] = df['texto_completo'].str.lower().apply(lambda x: re.sub(r'[^a-z\s]', '', x))

stopwords_custom = set(stopwords.words('portuguese')).union({
    'computacao', 'quantica', 'quântico', 'quantum', 'trabalho', 'estudo', 'pesquisa',
    'neste', 'este', 'para', 'com', 'que', 'uma', 'como', 'sobre', 'dados', 'resultados',
    'computação', 'quântico', 'quantica', 'quantico', 'quantum',
    'artigo', 'trabalho', 'estudo', 'pesquisa', 'analise', 'revisao', 'apresenta',
    'neste', 'este', 'para', 'com', 'da', 'do', 'das', 'dos', 'em', 'um', 'uma',
    'que', 'e', 'o', 'a', 'os', 'as', 'se', 'no', 'na', 'nos', 'nas', 'de', 'sobre',
    'como', 'por', 'discutir', 'propor', 'desenvolver', 'mostrar', 'impacto', 'foco',
    'abordagem', 'baseado', 'partir', 'novo', 'novos', 'novas', 'nova', 'futuro',
    'futura', 'apresentamos', 'tecnico', 'desenvolvimento', 'complexas', 'destacando',
    'revisão', 'sistemática', 'literatura', 'ensino', 'dados', 'utiliza', 'proposto',
    'presente', 'desenvolvido', 'baseada', 'proposta', 'pode', 'ser', 'são', 'muito',
    'mais', 'ainda', 'assim', 'apenas', 'tambem', 'apresenta', 'resultados', 'diferentes',
    'utilizados', 'através', 'diferentes', 'processo', 'informações', 'possível', 'metodo',
    'teorico', 'potenciais', 'referencial', 'crescimento', 'transcrita', 'seguira',
    'suficiente', 'instrumentar', 'notar', 'projeto', 'outro', 'fator', 'taxas', 'retencao',
    'discutem', 'criação', 'novo', 'visão', 'busca', 'física', 'ciência', 'computadores',
    'área', 'aplicações', 'tecnologia', 'sistema', 'sistemas', 'partir'
})

df['texto_filtrado'] = df['texto_limpo'].apply(lambda x: ' '.join([w for w in x.split() if w not in stopwords_custom]))
print("Pré-processamento de texto concluído.")

# --- WordCloud ---
print("\nGerando Nuvem de Palavras...")
texto = ' '.join(df['texto_filtrado'].dropna())
if texto:
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(texto)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Nuvem de Palavras-Chave')
    plt.show()
    print("\nTop 20 palavras mais frequentes:")
    for p, f in Counter(texto.split()).most_common(20):
        print(f"{p}: {f}")
else:
    print("Texto insuficiente para gerar Nuvem de Palavras.")

# --- LDA: Modelagem de Tópicos ---
print("\nIniciando Modelagem de Tópicos (LDA)...")
df_lda = df[df['texto_filtrado'].str.strip() != ''].copy() # Usar .copy() para evitar SettingWithCopyWarning
if not df_lda.empty:
    try:
        vec = TfidfVectorizer(max_df=0.95, min_df=2, stop_words=list(stopwords_custom))
        dtm = vec.fit_transform(df_lda['texto_filtrado'])
        lda = LatentDirichletAllocation(n_components=5, random_state=42)
        lda.fit(dtm)
        terms = vec.get_feature_names_out()
        for i, topico in enumerate(lda.components_):
            print(f"\nTópico {i + 1}:", [terms[j] for j in topico.argsort()[-10:]])
        df_lda['topico'] = lda.transform(dtm).argmax(axis=1)
        print("\nDocumentos por tópico:")
        print(df_lda['topico'].value_counts())
    except Exception as e:
        print(f"ERRO: LDA falhou: {e}")
        print("Verifique se 'min_df' no TfidfVectorizer não é muito alto para o seu volume de dados.")
else:
    print("Dados insuficientes para Modelagem de Tópicos (LDA).")


# --- Sentimento Básico ---
print("\nIniciando Análise de Sentimento Básica...")
positivas = {'inovação', 'oportunidades', 'avanços', 'eficiente', 'sucesso'}
negativas = {'desafios', 'problemas', 'riscos', 'limitações', 'ameaça'}

def sentimento(texto):
    if not isinstance(texto, str): return 'Neutro'
    texto = texto.lower()
    p = sum(1 for w in positivas if w in texto)
    n = sum(1 for w in negativas if w in texto)
    return 'Positivo' if p > n else 'Negativo' if n > p else 'Neutro'

df['sentimento'] = df['resumo'].apply(sentimento)
sns.countplot(x='sentimento', data=df, palette='viridis')
plt.title('Sentimento dos Resumos')
plt.show()
print("Análise de sentimento concluída.")

# --- Análise Temporal ---
print("\nIniciando Análise Temporal...")
df['ano_publicacao'] = pd.to_numeric(df['ano_publicacao'], errors='coerce')
# Filtrar anos válidos e dentro de um intervalo razoável
ano_atual = pd.Timestamp.now().year
df_anos = df.dropna(subset=['ano_publicacao']).copy() # Usar .copy()
df_anos = df_anos[(df_anos['ano_publicacao'] >= 1900) & (df_anos['ano_publicacao'] <= (ano_atual + 1))]
df_anos['ano_publicacao'] = df_anos['ano_publicacao'].astype(int)

if not df_anos.empty:
    print("\nGerando gráfico de Publicações por Ano...")
    publicacoes_por_ano = df_anos['ano_publicacao'].value_counts().sort_index()
    if not publicacoes_por_ano.empty:
        publicacoes_por_ano.plot(kind='bar', color='skyblue')
        plt.title('Publicações por Ano')
        plt.xlabel('Ano')
        plt.ylabel('Número de Artigos')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    else:
        print("Nenhuma publicação válida encontrada para plotar o gráfico de anos.")

    if 'termo' in df.columns:
        print("\nGerando gráfico de Tendência de Tópicos por Ano...")
        tendencias = df_anos.groupby(['ano_publicacao', 'termo']).size().unstack(fill_value=0)
        if not tendencias.empty:
            tendencias.plot(marker='o', figsize=(12, 6))
            plt.title('Tendência de Tópicos por Ano')
            plt.xlabel('Ano')
            plt.ylabel('Qtd Artigos')
            plt.legend(title='Tópico', bbox_to_anchor=(1.05, 1))
            plt.tight_layout()
            plt.show()
        else:
            print("Dados insuficientes para plotar tendências de tópicos ao longo do tempo.")
    else:
        print("Coluna 'termo' não encontrada para análise de tendência de tópicos.")
else:
    print("Não há dados de anos válidos para análise temporal.")


print("\n✔️ Análise concluída com sucesso.")
