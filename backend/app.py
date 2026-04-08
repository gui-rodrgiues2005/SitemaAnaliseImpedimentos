from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import cv2
import numpy as np
import uuid
import time

app = Flask(__name__)
CORS(app)

#Configuração de pastas
PASTA_ENTRADA = "uploads"
PASTA_SAIDA = "processed"
os.makedirs(PASTA_ENTRADA, exist_ok=True)
os.makedirs(PASTA_SAIDA, exist_ok=True)

@app.route('/processed/<filename>')
def buscar_foto_processada(filename):
    return send_from_directory(PASTA_SAIDA, filename)

@app.route("/process-image", methods=["POST"])
def processar_impedimento():
    if "image" not in request.files:
        return jsonify({"error": "Arquivo não encontrado"}), 400
        
    arquivo = request.files["image"]
    
    # Gerando um nome único para não misturar os testes da turma
    identificador = str(uuid.uuid4())[:8]
    nome_base = f"projeto_{identificador}"
    caminho_original = os.path.join(PASTA_ENTRADA, f"{nome_base}_original.png")
    arquivo.save(caminho_original)

    # Carrega a imagem para o OpenCV
    imagem = cv2.imread(caminho_original)
    if imagem is None:
        return jsonify({"error": "Não foi possível ler a imagem"}), 400

    # Dicionário que o React vai ler para mostrar o "passo a passo"
    links_resultado = {
        "original": f"http://localhost:5000/processed/{nome_base}_original.png"
    }
    cv2.imwrite(os.path.join(PASTA_SAIDA, f"{nome_base}_original.png"), imagem)

    #1 - FILTRO GAUSSIANO: Suaviza a imagem(tira o ruído da grama)
    imagem_suave = cv2.GaussianBlur(imagem, (5, 5), 0)
    nome_gauss = f"{nome_base}_1_suave.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome_gauss), imagem_suave)
    links_resultado["gaussian"] = f"http://localhost:5000/processed/{nome_gauss}"

    #2 - FILTRO SOBEL: Detecta onde estão as bordas (as linhas brancas)
    imagem_cinza = cv2.cvtColor(imagem_suave, cv2.COLOR_BGR2GRAY)
    bordas_x = cv2.Sobel(imagem_cinza, cv2.CV_64F, 1, 0, ksize=3)
    bordas_reais = np.uint8(np.absolute(bordas_x))
    nome_sobel = f"{nome_base}_2_bordas.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome_sobel), bordas_reais)
    links_resultado["sobel"] = f"http://localhost:5000/processed/{nome_sobel}"

    #3 - MORFOLOGIA: Binariza (preto e branco puro) e engrossa as linhas
    _, imagem_binaria = cv2.threshold(bordas_reais, 50, 255, cv2.THRESH_BINARY)
    elemento_estruturante = np.ones((3,3), np.uint8)
    imagem_dilatada = cv2.dilate(imagem_binaria, elemento_estruturante, iterations=1)
    nome_morfologia = f"{nome_base}_3_morfologia.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome_morfologia), imagem_dilatada)
    links_resultado["morphology"] = f"http://localhost:5000/processed/{nome_morfologia}"

    #4 - FUNÇÃO EXTRA (HoughLinesP): Identifica as retas matemáticas do campo
    linhas_detectadas = cv2.HoughLinesP(imagem_dilatada, 1, np.pi/180, threshold=80, minLineLength=80, maxLineGap=15)
    
    mascara_linhas = np.zeros_like(imagem)
    if linhas_detectadas is not None:
        for linha in linhas_detectadas:
            x1, y1, x2, y2 = linha[0]
            # Desenha as linhas em Ciano (azul claro) para destacar bem
            cv2.line(mascara_linhas, (x1, y1), (x2, y2), (255, 255, 0), 2)

    #5 - OPERAÇÃO ENTRE IMAGENS: Sobrepõe as linhas na foto original
    resultado_final = cv2.addWeighted(imagem, 0.9, mascara_linhas, 1.0, 0)
    nome_final = f"{nome_base}_4_resultado.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome_final), resultado_final)
    links_resultado["final"] = f"http://localhost:5000/processed/{nome_final}"

    # Retorna o pacote de URLs para o Frontend
    return jsonify(links_resultado)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
    
# testando backend