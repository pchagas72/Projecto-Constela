from datasets.noticias import mensagens_bom_dia
from datasets.noticias import mensagens_potencialmente_ofensivas
from datasets.noticias import sugestoes_reportagens
from datasets.noticias import noticias_ultima_hora
from datasets.noticias import noticias_nao_tao_recentes
from datasets.noticias import noticias_teste
from datasets.noticias import falta_sinal_globo
from datasets.noticias_novas import noticias_recentes
from datasets.noticias_novas import sugestoes_reportagens
from datasets.noticias_novas import faltas_de_sinais
from datasets.noticias_novas import mensagens_bom_dia
import string
from collections import Counter

class NLP:
    def __init__(self):
        self.db = {
            'noticia quente' : [],
            'odio' : [],
            'bom dia': [],
            'reportagem' : [],
            'noticia fria' : [],
            'faltou sinal': [],
            'não identificado' : []
        }

    def alimentar_dicionario(self, mensagens, top_n=10, remover_stopwords=False, dicionario_path="dicionario.txt"):
        stopwords = set([
            'a', 'o', 'e', 'de', 'do', 'da', 'em', 'um', 'para', 'com',
            'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as',
            'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem',
            'à', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'há',
            'nos', 'já', 'está', 'eu', 'também', 'só', 'pelo', 'pela',
            'até', 'isso', 'ela', 'entre', 'depois', 'sem', 'mesmo',
            'aos', 'ter', 'seus', 'quem', 'nas', 'me', 'esse', 'eles',
            'estão', 'você', 'tinha', 'foram', 'essa', 'num', 'nem',
            'suas', 'meu', 'às', 'minha', 'têm', 'numa', 'pelos',
            'elas', 'houver', 'isto', 'estive', 'foi', 'será', 'já', 'estava', 
            'que'
        ])

        todas_palavras = []

        for mensagem in mensagens:
            mensagem = mensagem.lower()
            mensagem = mensagem.translate(str.maketrans('', '', string.punctuation))
            palavras = mensagem.split()
            if remover_stopwords:
                palavras = [palavra for palavra in palavras if palavra not in stopwords]
            todas_palavras.extend(palavras)

        contagem = Counter(todas_palavras)
        retorno = contagem.most_common(top_n)

        with open(dicionario_path, 'w', encoding='UTF-8') as f:
            for palavra in retorno:
                f.writelines(f"{palavra[0]},")
        return retorno
    
    def checa_msg_em_dicionario(self, msg: str, dict_path: str) -> int:
        with open(dict_path, 'r', encoding='UTF-8') as f:
            dict = f.read().split(',')
        msg = msg.lower()
        msg = msg.translate(str.maketrans('', '', string.punctuation))
        msg = msg.split()
        credibilidade = 0
        for palavra in msg:
            if palavra in dict:
                credibilidade += 1
        return credibilidade
    
    
    def detecta_tipo(self, mensagem): # Trocar o dicionário para detectar diferentes tipos de mensagem
        credibilidade_bom_dia = (self.checa_msg_em_dicionario(mensagem, dict_path='src/dicts/dicionario_bom_dia.txt'),'bom dia')
        credibilidade_odio = (self.checa_msg_em_dicionario(mensagem, dict_path='src/dicts/dicionario_do_odio.txt'), 'odio')
        credibilidade_reportagem = (self.checa_msg_em_dicionario(mensagem, dict_path='src/dicts/dicionario_reportagens.txt'), 'reportagem')
        credibilidade_noticia_quente = (self.checa_msg_em_dicionario(mensagem, dict_path='src/dicts/dicionario_quente.txt'), 'noticia quente')
        credibilidade_noticia_fria = (self.checa_msg_em_dicionario(mensagem, dict_path='src/dicts/dicionario_frio.txt'), 'noticia fria')
        credibilidade_sinal = (self.checa_msg_em_dicionario(mensagem, dict_path='src/dicts/dicionario_sinal.txt'), 'faltou sinal')
        credibilidades = [credibilidade_bom_dia, credibilidade_noticia_quente, credibilidade_odio, credibilidade_reportagem, credibilidade_noticia_fria, credibilidade_sinal]
        predict = (0,'')
        for cred in credibilidades:
            if cred[0] > predict[0]:
                predict = cred
        return (mensagem, predict[1])

    def mensagens_semelhantes(self, mensagem1: str, mensagem2: str) -> float:
        mensagem1 = mensagem1.lower()
        mensagem2 = mensagem2.lower()
        mensagem1 = mensagem1.translate(str.maketrans('', '', string.punctuation))
        mensagem2 = mensagem2.translate(str.maketrans('', '', string.punctuation))
        conjunto1 = set(mensagem1.split())
        conjunto2 = set(mensagem2.split())
        
        intersecao = conjunto1.intersection(conjunto2)
        uniao = conjunto1.union(conjunto2)
        
        similaridade = len(intersecao) / len(uniao) if uniao else 0.0
        return similaridade
               
    def adicionar_nova_mensagem(self, database,tsh,mensagem):
        content = self.detecta_tipo(mensagem)
        for classe in database:
            if classe == content[1]:
                if classe in ['noticia quente', 'noticia fria', 'reportagem', 'faltou sinal']:
                    for i in range(len(database[classe])):
                        msg = database[classe][i]
                        sim = self.mensagens_semelhantes(mensagem, msg)
                        if sim > tsh:
                            database[classe][i] = msg + '\n' + mensagem
                            return 0
                database[classe].append(mensagem)


    def alimentar_dicionarios(self):
        self.alimentar_dicionario(noticias_recentes, top_n=20, remover_stopwords=True, dicionario_path='src/dicts/dicionario_quente.txt')
        self.alimentar_dicionario(sugestoes_reportagens, top_n=20, remover_stopwords=True, dicionario_path='src/dicts/dicionario_reportagens.txt')
        self.alimentar_dicionario(faltas_de_sinais, top_n=20, remover_stopwords=True, dicionario_path='src/dicts/dicionario_sinal.txt')
        self.alimentar_dicionario(mensagens_bom_dia, top_n=20, remover_stopwords=True, dicionario_path='src/dicts/dicionario_bom_dia.txt')

