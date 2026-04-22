import React, { useState, useRef } from "react";
import "./estilo.css";

function App() {
  const [file, setFile] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [zoomImage, setZoomImage] = useState(null);


  const [direcaoAtaque, setDirecaoAtaque] = useState("direita");
  const [lineAtacante, setLineAtacante] = useState(200);
  const [lineDefensor, setLineDefensor] = useState(300);
  const varImageRef = useRef(null);

  const steps = [
    { key: "gaussian", title: "Filtro Gaussiano", description: "Suavização e redução de ruído" },
    { key: "sobel", title: "Sobel (Bordas)", description: "Detecção de contornos" },
    { key: "realce", title: "Operação AbsDiff", description: "Recuperação de detalhes" },
    { key: "edges", title: "Canny", description: "Bordas mais fortes" },
    { key: "morph", title: "Dilatação", description: "Conexão de regiões" },
    { key: "final", title: "Resultado Final", description: "Segmentação completa" }
  ];

  const handleUpload = async () => {
    if (!file) return;
    setIsLoading(true);
    setPipelineData(null);
    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("http://localhost:5000/process-image", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setPipelineData(data);
    } catch (err) {
      alert("Erro ao conectar com o servidor.");
    } finally {
      setIsLoading(false);
    }
  };

  const getVeredito = () => {
    const isOffside = direcaoAtaque === "direita" 
      ? lineAtacante > lineDefensor 
      : lineAtacante < lineDefensor;
    return isOffside ? "IMPEDIDO" : "POSIÇÃO LEGAL";
  };

  const startDrag = (setter) => {
    const onMove = (e) => {
      if (!varImageRef.current) return;
      const rect = varImageRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      setter(x);
    };
    const onStop = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onStop);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onStop);
  };

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">⚽ VAR SIMPLES</h1>
        <p className="subtitle">Pipeline de visão computacional interativo</p>
      </div>

      <div className="upload-container">
        <div className="upload-input-wrapper">
          <input id="file-upload" type="file" className="upload-input" onChange={(e) => setFile(e.target.files[0])} />
          <label htmlFor="file-upload" className="upload-label">{file ? file.name : "Selecionar arquivo"}</label>
        </div>
        <button className="upload-button" onClick={handleUpload} disabled={!file || isLoading}>
          {isLoading ? "Processando..." : "Analisar"}
        </button>
      </div>

      {pipelineData && (
        <>
          <div className="grid">
            <div className="card">
              <div className="card-header">Original</div>
              <div className="card-body">
                <img src={pipelineData.original} className="image" onClick={() => setZoomImage(pipelineData.original)} alt="orig" />
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <div>{steps[currentStep].title}</div>
                <small>{steps[currentStep].description}</small>
              </div>
              <div className="card-body">
                <img src={pipelineData[steps[currentStep].key]} className="image" onClick={() => setZoomImage(pipelineData[steps[currentStep].key])} alt="step" />
              </div>
              <div className="controls">
                <button className="btn" onClick={() => setCurrentStep(s => Math.max(0, s - 1))}>←</button>
                <span>{currentStep + 1}/{steps.length}</span>
                <button className="btn" onClick={() => setCurrentStep(s => Math.min(steps.length - 1, s + 1))}>→</button>
              </div>
            </div>
          </div>

          
          <div className="var-section">
            <h2 className="section-title">🖥️ Mesa de Decisão VAR</h2>
            
            <div className="dir-controls">
              <span>Ataque para:</span>
              <button className={`btn-dir ${direcaoAtaque === "esquerda" ? "active" : ""}`} onClick={() => setDirecaoAtaque("esquerda")}>⬅ ESQUERDA</button>
              <button className={`btn-dir ${direcaoAtaque === "direita" ? "active" : ""}`} onClick={() => setDirecaoAtaque("direita")}>DIREITA ➡</button>
            </div>

            <div className={`veredito-display ${getVeredito().replace(" ", "-")}`}>
              {getVeredito()}
            </div>

            <div className="var-workspace" style={{ position: 'relative', display: 'inline-block' }}>
              <img ref={varImageRef} src={pipelineData.final} className="image-main-var" alt="final-var" />
              
              <div className="drag-line atacante" style={{ left: lineAtacante }} onMouseDown={() => startDrag(setLineAtacante)}>
                <div className="line-tag">ATACANTE</div>
              </div>

              <div className="drag-line defensor" style={{ left: lineDefensor }} onMouseDown={() => startDrag(setLineDefensor)}>
                <div className="line-tag">DEFENSOR</div>
              </div>
            </div>
            <p className="hint">Arraste as linhas coloridas para ajustar</p>
          </div>
        </>
      )}

      {zoomImage && <div className="zoom-overlay" onClick={() => setZoomImage(null)}><img src={zoomImage} className="zoom-image" alt="zoom" /></div>}
    </div>
  );
}

export default App;