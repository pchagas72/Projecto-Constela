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
import speech_recognition as sr
from pydub import AudioSegment

# Carregar variáveis de ambiente
load_dotenv()
TWILIO_ACCOUNT_SID = 
TWILIO_AUTH_TOKEN = 

# Configurando o modelo e NLP
NLP = NLP()
model = keras.models.load_model('src/models/model.keras')
app = Flask(__name__)

def preprocess_image(file_path):
    try:
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
        return "Poxa, ocorreu um erro… não foi possível processar a imagem."
    prediction = model.predict(img_array)
    return "Bom dia para você também! Gostaria de enviar uma mensagem para o BomDia PE?" if prediction >= 0.5 else "Certo! Recebi a imagem do acidente."

def audio_para_texto(file_path):
    audio = AudioSegment.from_ogg(file_path)
    wav_path = "converted_audio.wav"
    audio.export(wav_path, format="wav")
    
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="pt-BR")
            return text
        except sr.UnknownValueError:
            return "Infelizmente não consegui entender seu áudio…"
        except sr.RequestError as e:
            return f"Erro na requisição ao serviço de reconhecimento: {e}"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    state = session.get('state', '')
    media_url = request.form.get("MediaUrl0")
    incoming_msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()
    texto = False
    mensagem_de_texto = ''

    print(f"Estado atual: {state}")

    if incoming_msg in ['oi', 'olá', 'tudo bom']:
        resp.message("Olá! Sou a Estela, sua assistente do WhatsApp da Globo! Você tem alguma coisa a mandar?")

    elif incoming_msg == 'ADM_finalizar':
        for i in NLP.db:
            NLP.db[i] = []

    elif incoming_msg == 'ADM_database':
        for i in NLP.db:
            resp.message(NLP.db[i])

    elif media_url:
        response = requests.get(media_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            print('CONTENT TYPE:', content_type)
            if "image" in content_type:
                temp_file_path = "temp_image.jpg"
                with open(temp_file_path, "wb") as f:
                    f.write(response.content)

                prediction_result = predict_image(temp_file_path)
                if prediction_result:
                    print("SISTEMA: NENHUM NSFW ENCONTRADO")
                    print("SISTEMA: IMAGEM QUALIFICADA")
                resp.message(prediction_result)
                sleep(3)

                if prediction_result == 'Bom dia para você também! Gostaria de enviar uma mensagem para o BomDia PE?':
                    resp.message('Manda pra gente um texto e enviaremos para o Bom Dia PE!')
                elif prediction_result == 'Certo! Recebi a imagem do acidente.':
                    resp.message('Obrigado pela imagem, nossa equipe já recebeu e estamos investigando a situação.')

                os.remove(temp_file_path)

            elif 'audio' in content_type:
                print("Verificando conteúdo do áudio...")
                response = requests.get(media_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
                with open("audio.ogg", "wb") as fout:
                    fout.write(response.content)
                mensagem_de_texto = audio_para_texto("audio.ogg")
                texto = True
            else:
                resp.message("Poxa, ocorreu um erro… O arquivo enviado não é uma imagem ou houve um problema no download.")
        else:
            resp.message("Poxa, ocorreu um erro… Não foi possível acessar a mídia.")
    else:
        mensagem_de_texto = incoming_msg
        texto = True

    if texto:
        tipo = NLP.detecta_tipo(mensagem_de_texto)
        print(tipo)
        if 'noticia' in tipo[1]:
            resp.message("Obrigada! Recebemos sua notícia. Ela será redirecionada para a nossa equipe imediatamente.")
            if not any(loc in mensagem_de_texto for loc in ['rua', 'avenida', 'br', 'bairro', 'br-101', 'br-232']):
                resp.message("Certo! Mande sua localização para que possamos ajudar melhor!")
            resp.message("Caso você tenha quaisquer imagens, pode enviar por esse canal de comunicação.")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, mensagem_de_texto)

        elif tipo[1] == 'bom dia':
            resp.message("Linda mensagem! Ela foi enviada para nossos repórteres, fique atento na nossa programação!")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, mensagem_de_texto)

        elif tipo[1] == 'reportagem':
            resp.message("Obrigado pela sugestão de reportagem! Enviei ela para o time investigativo.")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, mensagem_de_texto)

        elif tipo[1] == 'odio':
            resp.message("Não toleramos mensagens de ódio nesse canal, seu contato foi bloqueado durante uma semana.")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, mensagem_de_texto)

        elif tipo[1] == 'localizacao':
            resp.message("Obrigado pela localização! É muito importante.")
            if len(NLP.db['noticia quente']) == 0:
                resp.message("O que aconteceu aí?")

        elif tipo[1] == 'faltou sinal':
            resp.message("Entendemos, estamos enviando seu relato para uma equipe que possa resolver!")
            NLP.adicionar_nova_mensagem(NLP.db, 0.14, mensagem_de_texto)
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
