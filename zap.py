from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from NLP_GROBO import NLP
from tensorflow import keras
import numpy as np
from PIL import Image
import requests
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import pandas as pd
from time import sleep

# Carregar variáveis de ambiente
load_dotenv()
TWILIO_ACCOUNT_SID = 'AC80ca4525936c35fa79c4a0d224ec2d8f'
TWILIO_AUTH_TOKEN = 'e4c12bfaa0e6b4517994a9c51efb4e90'

# Configurando o modelo e NLP
NLP = NLP()
model = keras.models.load_model('src/models/model.keras')
app = Flask(__name__)

# Definindo uma chave secreta para a sessão
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'secret_key')

def preprocess_image(file_path):
    try:
        # Abrir e processar a imagem
        img = Image.open(file_path).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        return img_array
    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")
        return None

def predict_image(file_path):
    img_array = preprocess_image(file_path)
    if img_array is None:
        return "Erro: não foi possível processar a imagem."
    prediction = model.predict(img_array)
    return "Que linda imagem de bom dia!" if prediction >= 0.5 else "Recebemos a imagem do acidente."

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    # Recuperar o estado da sessão ou inicializar como vazio
    state = session.get('state', '')
    media_url = request.form.get("MediaUrl0")
    incoming_msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()

    print(f"Estado atual: {state}")

    if incoming_msg == 'ADM_finalizar':
        for i in NLP.db:
            NLP.db[i] = []


    if incoming_msg == 'ADM_database':
        for i in NLP.db:
            resp.message(NLP.db[i])

    if media_url:
        response = requests.get(media_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "image" in content_type:
                temp_file_path = "temp_image.jpg"
                with open(temp_file_path, "wb") as f:
                    f.write(response.content)

                # Previsão com o modelo
                prediction_result = predict_image(temp_file_path)
                if prediction_result:
                    print("SISTEMA: NENHUM NSFW ENCONTRADO")
                    print("SISTEMA: IMAGEM QUALIFICADA")
                resp.message(prediction_result)
                sleep(3)

                # Atualizando o estado corretamente na sessão
                if prediction_result == 'Que linda imagem de bom dia!':
                    resp.message('Manda pra gente um texto e enviaremos para o bom dia PE!')
                elif prediction_result == 'Recebemos a imagem do acidente.':
                    resp.message('Obrigado pela imagem, nossa equipe já recebeu e estamos investigando a situação.')

                # Remover arquivo temporário
                os.remove(temp_file_path)
            else:
                resp.message("Erro: O arquivo enviado não é uma imagem ou houve um problema no download.")
        else:
            resp.message(f"Erro {response.status_code}: Não foi possível acessar a mídia.")
    else:
        tipo = NLP.detecta_tipo(incoming_msg)
        print(tipo)
        if 'noticia' in tipo[1]:
            resp.message(f"Recebemos sua notícia. Ela será redirecionada para a nossa equipe imediatamante.")
            sleep(1)
            resp.message(f"Caso você tenha quaisquer imagens, pode enviar por esse canal de comunicação.")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, incoming_msg)
            df=pd.DataFrame.from_dict(NLP.db,orient='index').transpose()
            df.to_csv('adicionar.csv', sep='\t', encoding='utf-8')
            print(df)
        elif tipo[1] == 'bom dia':
            resp.message(f"Linda mensagem! Ela foi enviada para nossos repórteres, fique atento na nossa programação!")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, incoming_msg)
            df=pd.DataFrame.from_dict(NLP.db,orient='index').transpose()
            df.to_csv('adicionar.csv', sep='\t', encoding='utf-8')
            print(df)
        elif tipo[1] == 'reportagem':
            resp.message('Obrigado pela sugestão de reportagem! Enviei ela para o time investigativo.')
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, incoming_msg)
        elif tipo[1] == 'odio':
            resp.message('Não toleramos mensagens de ódio nesse canal, seu contato foi bloqueado durante uma semana.')
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, incoming_msg)     
        elif tipo[1] == 'faltou sinal':
            resp.message('Entendemos, estamos enviando seu relato para uma equipe que possa resolver!')
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, incoming_msg)
            df=pd.DataFrame.from_dict(NLP.db,orient='index').transpose()
            df.to_csv('adicionar.csv', sep='\t', encoding='utf-8')
            print(df)
            sleep(1)
            resp.message("""
Olá!

Lamentamos que esteja enfrentando problemas com o sinal da Globo. Siga estes passos para resolver a questão:

Verifique se todos os cabos estão corretamente conectados, especialmente o cabo da antena.
Certifique-se de que a TV esteja ligada e configurada para o modo de recepção correto.
Já enviamos seu pedido de verificação!

Obrigado!
""")
            
    print(NLP.db)


    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
