import cv2
from PIL import Image, ExifTags

class fatofake(): # RECEBE: IMAGEM, MENSAGENS
    def __init__(self, mensagens: list[str], image_path: list[str]):
        self.imagens = [(cv2.imread(i),Image.open(i)) for i in image_path]
        self.mensagens = mensagens
        self.resultados = []

    def verificar_metadados(self):
        for i in self.imagens:
            imagem = self.imagens[1]
            
            try:
                # Extrair os metadados EXIF
                metadados = imagem._getexif()
                if metadados:
                    for tag, valor in metadados.items():
                        tag_nome = ExifTags.TAGS.get(tag, tag)
                        print(f"{tag_nome}: {valor}")
                        self.resultados.append(f"{tag_nome}: {valor}")
                else:
                    print("Nenhum metadado EXIF encontrado.")
            except Exception as e:
                print("Erro ao acessar metadados:", e)


    def verificar_inconsistencias(self):
        for i in self.imagens:
            imagem = self.imagens[0]
            cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
            
            # Aplicar detecção de bordas para verificar áreas editadas
            bordas = cv2.Canny(cinza, 100, 200)
            
            # Detectar contornos e inconsistências
            contornos, _ = cv2.findContours(bordas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Avaliar se há contornos suspeitos
            for contorno in contornos:
                area = cv2.contourArea(contorno)
                if area > 1000:  # Define um limite para áreas suspeitas
                    print("Possível edição detectada em uma área:", area)

    def check_imagem(self):
        self.verificar_metadados()
        self.verificar_inconsistencias()