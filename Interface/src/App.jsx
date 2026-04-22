import React, { useState } from "react";
import "./estilo.css";

function App() {
  const [file, setFile] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [zoomImage, setZoomImage] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  // PIPELINE REAL (AJUSTADO COM O BACKEND)
  const steps = [
    {
      key: "gaussian",
      title: "Filtro Gaussiano",
      description: "Usado para suavizar a imagem e reduzir ruídos do campo"
    },
    {
      key: "sobel",
      title: "Sobel (Bordas)",
      description: "Usado para detectar os contornos dos jogadores"
    },
    {
      key: "realce",
      title: "Operação entre imagens (AbsDiff)",
      description: "Ajuda a recuperar e evidenciar detalhes importantes que foram reduzidos pelo filtro Gaussiano"
    },
    {
      key: "edges",
      title: "Canny",
      description: "Usado para manter apenas bordas mais fortes e claras"
    },
    {
      key: "morph",
      title: "Dilatação",
      description: "Usada para reforçar e conectar regiões dos jogadores"
    },
    {
      key: "final",
      title: "Resultado Final",
      description: "Jogadores segmentados e destacados no campo"
    }
  ];

  const validateFile = (file) => {
    const acceptedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
    const maxSize = 10 * 1024 * 1024;

    if (!file) return 'Nenhum arquivo selecionado';

    if (!acceptedTypes.includes(file.type)) {
      return `Formato não suportado. Use: ${acceptedTypes.map(t => t.split('/')[1]).join(', ')}`;
    }

    if (file.size > maxSize) {
      return `Arquivo muito grande. Máximo: ${maxSize / (1024 * 1024)}MB`;
    }

    return null;
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadError("Selecione um arquivo primeiro");
      return;
    }

    setIsLoading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setPipelineData(null);
    setCurrentStep(0);

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("http://localhost:5000/process-image", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);

      const data = await res.json();
      setPipelineData(data);
      setUploadSuccess("Imagem processada com sucesso!");
    } catch (err) {
      setUploadError(err.message || "Erro ao processar imagem");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">

      {/* HEADER */}
      <div className="header">
        <h1 className="title">⚽ VAR Analyzer</h1>
        <p className="subtitle">
          Pipeline de visão computacional para análise de impedimento
        </p>
      </div>

      {/* UPLOAD */}
      <div className="upload-container">

        <div className="upload-input-wrapper">
          <input
            id="file-upload"
            type="file"
            className="upload-input"
            onChange={(e) => setFile(e.target.files[0])}
          />

          <label htmlFor="file-upload" className="upload-label">
            Selecionar arquivo
          </label>
        </div>

        {file && (
          <div className="file-info">
            📄 {file.name}
            <button
              className="remove-file"
              onClick={() => setFile(null)}
            >
              ×
            </button>
          </div>
        )}

        <div className="upload-button-wrapper">
          <button
            className="upload-button"
            onClick={handleUpload}
            disabled={!file || isLoading}
          >
            {isLoading ? "Processando..." : "Analisar"}
          </button>
        </div>

        {uploadError && (
          <div className="error-message">{uploadError}</div>
        )}

        {uploadSuccess && (
          <div className="success-message">{uploadSuccess}</div>
        )}

      </div>

      {/* RESULTADO */}
      {pipelineData && (
        <div className="grid">

          {/* ORIGINAL */}
          <div className="card">
            <div className="card-header">Original</div>
            <div className="card-body">
              <img
                src={pipelineData.original}
                className="image"
                onClick={() => setZoomImage(pipelineData.original)}
              />
            </div>
          </div>

          {/* PIPELINE */}
          <div className="card">

            <div className="card-header">
              <div>
                <div>{steps[currentStep].title}</div>
                <small style={{ opacity: 0.8 }}>
                  {steps[currentStep].description}
                </small>
              </div>

              <span>{currentStep + 1}/{steps.length}</span>
            </div>

            <div className="card-body">
              <img
                src={pipelineData[steps[currentStep].key]}
                className="image"
                onClick={() => setZoomImage(pipelineData[steps[currentStep].key])}
              />
            </div>

            <div className="controls">
              <button
                className="btn btn-prev"
                onClick={() => setCurrentStep(s => Math.max(0, s - 1))}
              >
                ←
              </button>

              <button
                className="btn btn-next"
                onClick={() => setCurrentStep(s => Math.min(steps.length - 1, s + 1))}
              >
                →
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ZOOM */}
      {zoomImage && (
        <div className="zoom-overlay" onClick={() => setZoomImage(null)}>
          <img src={zoomImage} className="zoom-image" />
        </div>
      )}

    </div>
  );
}

export default App;