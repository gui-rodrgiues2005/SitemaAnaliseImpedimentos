from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import numpy as np
import os
import uuid

app = Flask(__name__)
CORS(app)

PASTA_ENTRADA = "uploads"
PASTA_SAIDA = "processed"

os.makedirs(PASTA_ENTRADA, exist_ok=True)
os.makedirs(PASTA_SAIDA, exist_ok=True)

def salvar(nome_base, sufixo, img):
    nome = f"{nome_base}_{sufixo}.png"
    caminho = os.path.join(PASTA_SAIDA, nome)
    cv2.imwrite(caminho, img)
    return f"http://localhost:5000/processed/{nome}"


def aplicar_filtros(img):
    gaussian = cv2.GaussianBlur(img, (5,5), 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3)
    sobel = cv2.convertScaleAbs(sobel)
    return gaussian, sobel

def operacao_realce(img1, img2):
    g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(g1, g2)
    diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    _, diff = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    return diff

def morfologia(img):
    kernel = np.ones((3,3), np.uint8)
    return cv2.dilate(img, kernel, iterations=1)

def segmentar_times(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    cores = {
        "branco": ([0, 0, 140], [180, 60, 255]),
        "azul": ([100, 80, 50], [140, 255, 255]),
        "amarelo": ([20, 100, 100], [35, 255, 255]),
        "verde": ([35, 40, 40], [85, 255, 255])
    }
    masks = {}
    kernel = np.ones((3,3), np.uint8)
    for nome, (lower, upper) in cores.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        masks[nome] = mask
    
    l1, u1 = np.array([0, 80, 80]), np.array([10, 255, 255])
    l2, u2 = np.array([170, 80, 80]), np.array([180, 255, 255])
    masks["vermelho"] = cv2.bitwise_or(cv2.inRange(hsv, l1, u1), cv2.inRange(hsv, l2, u2))
    return masks

def aplicar_bordas(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 50, 120)
    return edges

# imagem final
def gerar_visual_final(img):
    masks = segmentar_times(img)
    gaussian, sobel_filter = aplicar_filtros(img)
    realce = operacao_realce(img, gaussian)
    edges = aplicar_bordas(img)
    morph = morfologia(edges)

    base = (img * 0.2).astype(np.uint8)
    resultado = base.copy()
    cores_visuais = {
        "branco": (255, 255, 255), "azul": (255, 0, 0),
        "vermelho": (0, 0, 255), "amarelo": (0, 255, 255), "verde": (0, 255, 0)
    }

    for nome, mask in masks.items():
        highlight = cv2.bitwise_and(morph, morph, mask=mask)
        if nome in cores_visuais:
            resultado[highlight > 0] = cores_visuais[nome]

    return gaussian, sobel_filter, realce, edges, morph, resultado

@app.route("/process-image", methods=["POST"])
def processar():
    if "image" not in request.files: return jsonify({"error": "sem imagem"}), 400
    file = request.files["image"]
    nome = f"img_{uuid.uuid4().hex[:6]}"
    caminho = os.path.join(PASTA_ENTRADA, nome + ".png")
    file.save(caminho)
    img = cv2.imread(caminho)
    if img is None: return jsonify({"error": "erro ao carregar"}), 500

    gauss, sob_f, real, edg, morph, final = gerar_visual_final(img)

    return jsonify({
        "original": salvar(nome, "original", img),
        "gaussian": salvar(nome, "gaussian", gauss),
        "sobel": salvar(nome, "sobel", sob_f),
        "realce": salvar(nome, "realce", real),
        "edges": salvar(nome, "edges", edg),
        "morph": salvar(nome, "morph", morph),
        "final": salvar(nome, "final", final),
    })

@app.route('/processed/<filename>')
def get_img(filename):
    return send_from_directory(PASTA_SAIDA, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)