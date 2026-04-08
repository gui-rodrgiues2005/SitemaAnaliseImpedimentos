#Sistema de Análise de Impedimento (VAR)

Projeto de Visão Computacional desenvolvido para a disciplina de Processamento de Imagens.

##Tecnologias
- **Backend:** Python, Flask, OpenCV, NumPy
- **Frontend:** React.js

##Como rodar
1. Instale as dependências: `pip install flask flask-cors opencv-python numpy`
2. Rode o servidor: `python app.py`
3. Em outra aba, rode o React: `npm start`

##Processamento de Imagem
O sistema utiliza um pipeline de 5 etapas:
1. Suavização Gaussiana
2. Detecção de Bordas (Sobel)
3. Morfologia Matemática (Dilação)
4. Transformada de Hough (Detecção de Retas)
5. Sobreposição de Imagens (VAR Final)
