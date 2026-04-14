from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import cv2
import numpy as np
import uuid
from ultralytics import YOLO

app = Flask(__name__)
CORS(app)

PASTA_ENTRADA = "uploads"
PASTA_SAIDA = "processed"
os.makedirs(PASTA_ENTRADA, exist_ok=True)
os.makedirs(PASTA_SAIDA, exist_ok=True)

model = YOLO('yolov8n.pt')

# ================= FILTRO DE CAMPO =================
def filtrar_campo(imagem):
    hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)

    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    mask_not_green = cv2.bitwise_not(mask_green)

    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 60, 255])
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    mask_final = cv2.bitwise_and(mask_white, mask_not_green)

    kernel = np.ones((3,3), np.uint8)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, 2)

    return mask_final

# ================= DETECÇÃO DA LINHA =================
def detectar_linha_estavel(imagem, linha_x):
    mask = filtrar_campo(imagem)
    edges = cv2.Canny(mask, 50, 150)

    linhas = cv2.HoughLinesP(edges, 1, np.pi/180,
                             threshold=80,
                             minLineLength=120,
                             maxLineGap=30)

    if linhas is None:
        return None

    melhores = []

    for linha in linhas:
        x1, y1, x2, y2 = linha[0]

        angulo = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        comprimento = np.hypot(x2 - x1, y2 - y1)

        if abs(angulo) < 60:
            continue

        dist = abs(((x1 + x2) / 2) - linha_x)
        score = comprimento - dist * 0.5

        melhores.append((score, x1, y1, x2, y2))

    if not melhores:
        return None

    melhores.sort(reverse=True)
    _, x1, y1, x2, y2 = melhores[0]

    return (x1, y1, x2, y2)

@app.route('/processed/<filename>')
def buscar_foto_processada(filename):
    return send_from_directory(PASTA_SAIDA, filename)

@app.route("/process-image", methods=["POST"])
def processar_impedimento():

    if "image" not in request.files:
        return jsonify({"error": "Arquivo não encontrado"}), 400
        
    arquivo = request.files["image"]

    nome_base = f"img_{str(uuid.uuid4())[:8]}"
    caminho = os.path.join(PASTA_ENTRADA, nome_base + ".png")
    arquivo.save(caminho)

    imagem = cv2.imread(caminho)
    if imagem is None:
        return jsonify({"error": "Erro ao ler imagem"}), 400

    results = model(imagem)

    jogadores_branco = []
    jogadores_preto = []

    # ================= DETECÇÃO =================
    for result in results:
        for box in result.boxes:
            if int(box.cls) == 0:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                jogador = {
                    "x1": int(x1),
                    "x2": int(x2),
                    "y": int((y1 + y2) / 2)
                }

                crop = imagem[int(y1):int(y2), int(x1):int(x2)]

                if crop.size > 0:
                    if np.mean(crop) > 150:
                        jogadores_branco.append(jogador)
                    else:
                        jogadores_preto.append(jogador)

    # ================= DIREÇÃO DO ATAQUE =================
    if jogadores_preto:
        media = np.mean([(p["x1"] + p["x2"]) / 2 for p in jogadores_preto])
        ataque_direita = media < imagem.shape[1] / 2
    else:
        ataque_direita = True

    # ================= REMOVER GOLEIRO =================
    if len(jogadores_preto) > 1:
        ordenados = sorted(jogadores_preto, key=lambda p: (p["x1"] + p["x2"]) / 2)

        if ataque_direita:
            jogadores_preto_validos = ordenados[:-1]
        else:
            jogadores_preto_validos = ordenados[1:]
    else:
        jogadores_preto_validos = jogadores_preto

    # ================= LINHA DO ÚLTIMO DEFENSOR (CORRIGIDO) =================
    linha_x = None
    impedidos = []

    if jogadores_preto_validos:

        if ataque_direita:
            ultimo = max(jogadores_preto_validos, key=lambda p: p["x2"])
            linha_x = ultimo["x2"]
        else:
            ultimo = min(jogadores_preto_validos, key=lambda p: p["x1"])
            linha_x = ultimo["x1"]

        for j in jogadores_branco:
            if ataque_direita:
                if j["x2"] > linha_x + 5:
                    impedidos.append(j)
            else:
                if j["x1"] < linha_x - 5:
                    impedidos.append(j)

    # ================= PIPELINE =================
    links = {}

    cv2.imwrite(os.path.join(PASTA_SAIDA, f"{nome_base}_original.png"), imagem)
    links["original"] = f"http://localhost:5000/processed/{nome_base}_original.png"

    blur = cv2.GaussianBlur(imagem, (5,5), 0)
    nome = f"{nome_base}_1_gaussian.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome), blur)
    links["gaussian"] = f"http://localhost:5000/processed/{nome}"

    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel = np.uint8(np.absolute(sobel))
    nome = f"{nome_base}_2_sobel.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome), sobel)
    links["sobel"] = f"http://localhost:5000/processed/{nome}"

    _, binaria = cv2.threshold(sobel, 50, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3,3), np.uint8)
    dilatada = cv2.dilate(binaria, kernel, iterations=1)
    nome = f"{nome_base}_3_morph.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome), dilatada)
    links["morphology"] = f"http://localhost:5000/processed/{nome}"

    # ================= RESULTADO FINAL =================
    resultado = imagem.copy()

    if linha_x is not None:
        linha_ref = detectar_linha_estavel(imagem, linha_x)

        if linha_ref is not None:
            x1, y1, x2, y2 = linha_ref

            dx = x2 - x1
            dy = y2 - y1
            tam = np.hypot(dx, dy)

            if tam != 0:
                dx /= tam
                dy /= tam
            else:
                dx, dy = 1, 0

            x0 = linha_x
            y0 = imagem.shape[0] // 2

            L = 2000

            p1 = (int(x0 - dx * L), int(y0 - dy * L))
            p2 = (int(x0 + dx * L), int(y0 + dy * L))

            cv2.line(resultado, p1, p2, (0,0,255), 3)
        else:
            cv2.line(resultado, (linha_x, 0), (linha_x, imagem.shape[0]), (0,0,255), 3)

    # desenhar jogadores
    for p in jogadores_preto:
        cv2.circle(resultado, (int((p["x1"]+p["x2"])/2), p["y"]), 6, (0,0,0), -1)

    for p in jogadores_branco:
        cv2.circle(resultado, (int((p["x1"]+p["x2"])/2), p["y"]), 6, (255,255,255), -1)

    for p in impedidos:
        cv2.circle(resultado, (int((p["x1"]+p["x2"])/2), p["y"]), 10, (0,255,255), 2)

    texto = "ATAQUE ->" if ataque_direita else "<- ATAQUE"
    cv2.putText(resultado, texto, (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    nome_final = f"{nome_base}_4_final.png"
    cv2.imwrite(os.path.join(PASTA_SAIDA, nome_final), resultado)

    links["final"] = f"http://localhost:5000/processed/{nome_final}"
    links["offside"] = "sim" if impedidos else "nao"

    return jsonify(links)

if __name__ == "__main__":
    app.run(port=5000, debug=True)