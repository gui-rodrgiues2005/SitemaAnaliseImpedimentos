import React, { useState } from "react";

const styles = {
  container: {
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    backgroundColor: "#f4f7f6",
    minHeight: "100vh",
    padding: "40px",
    color: "#333",
  },
  header: {
    textAlign: "center",
    marginBottom: "40px",
    borderBottom: "2px solid #2ecc71",
    paddingBottom: "20px",
  },
  title: {
    margin: 0,
    fontSize: "2.5rem",
    color: "#2c3e50",
  },
  subtitle: {
    margin: "10px 0 0",
    fontSize: "1.1rem",
    color: "#7f8c8d",
    fontWeight: "normal",
  },
  uploadSection: {
    backgroundColor: "#fff",
    padding: "30px",
    borderRadius: "8px",
    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
    marginBottom: "40px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "20px",
  },
  fileInput: {
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    width: "100%",
    maxWidth: "400px",
  },
  button: {
    backgroundColor: "#2ecc71",
    color: "white",
    border: "none",
    padding: "12px 24px",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "1rem",
    fontWeight: "bold",
    transition: "background-color 0.3s ease",
    textTransform: "uppercase",
    letterSpacing: "1px",
  },
  buttonDisabled: {
    backgroundColor: "#bdc3c7",
    cursor: "not-allowed",
  },
  pipelineGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "30px",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.08)",
    overflow: "hidden",
    transition: "transform 0.3s ease",
    display: "flex",
    flexDirection: "column",
  },
  cardHeader: {
    backgroundColor: "#34495e",
    color: "#fff",
    padding: "15px",
    fontWeight: "bold",
    fontSize: "1.1rem",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  stepNumber: {
    backgroundColor: "#2ecc71",
    color: "#fff",
    borderRadius: "50%",
    width: "30px",
    height: "30px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    fontSize: "0.9rem",
  },
  cardBody: {
    padding: "20px",
    flex: 1,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  image: {
    maxWidth: "100%",
    height: "auto",
    borderRadius: "4px",
    border: "1px solid #eee",
  },
  loading: {
    textAlign: "center",
    fontSize: "1.2rem",
    color: "#3498db",
    marginTop: "20px",
  },
};

function App() {
  const [file, setFile] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setIsLoading(true);
    setPipelineData(null); // Limpar dados anteriores

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("http://localhost:5000/process-image", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Falha no processamento");
      }

      const data = await res.json();
      setPipelineData(data);
    } catch (error) {
      console.error("Erro:", error);
      alert("Ocorreu um erro ao processar a imagem. Verifique o backend.");
    } finally {
      setIsLoading(false);
    }
  };

  // Definição dos passos para facilitar a renderização
  const steps = [
    { key: "original", title: "Imagem Original", description: "Upload do usuário" },
    { key: "gaussian", title: "1. Filtro Gaussiano", description: "Suavização e Redução de Ruído" },
    { key: "sobel", title: "2. Filtro Sobel", description: "Detecção de Bordas Spaciais" },
    { key: "morphology", title: "3. Operação Morfológica", description: "Binarização e Dilatação (Threshold)" },
    { key: "final", title: "4. Resultado Final (VAR)", description: "AddWeighted + Transformada de Hough" },
  ];

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Sistema de Análise de Impedimento</h1>
        <h2 style={styles.subtitle}>Processamento Digital de Imagens com OpenCV e Flask</h2>
      </header>

      <section style={styles.uploadSection}>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
          style={styles.fileInput}
        />
        <button
          onClick={handleUpload}
          style={{ ...styles.button, ...(isLoading || !file ? styles.buttonDisabled : {}) }}
          disabled={isLoading || !file}
        >
          {isLoading ? "Processando..." : "Analisar Imagem"}
        </button>
      </section>

      {isLoading && <div style={styles.loading}>Processando informações da imagem... Aguarde.</div>}

      {pipelineData && (
        <section style={styles.pipelineGrid}>
          {steps.map((step, index) => (
            <div key={step.key} style={styles.card}>
              <div style={styles.cardHeader}>
                <span>{step.title}</span>
                <div style={styles.stepNumber}>{index === 0 ? "★" : index}</div>
              </div>
              <div style={styles.cardBody}>
                <img
                  src={pipelineData[step.key]}
                  alt={step.description}
                  style={styles.image}
                  onLoad={(e) => { e.target.src = `${pipelineData[step.key]}?t=${new Date().getTime()}`; }}
                />
              </div>
              <div style={{ padding: "0 20px 20px", color: "#7f8c8d", fontSize: "0.9rem", textAlign: "center" }}>
                {step.description}
              </div>
            </div>
          ))}
        </section>
      )}
      {pipelineData && (
  <div style={{ textAlign: "center", marginTop: "30px" }}>
    <h2>
      Resultado:{" "}
      <span style={{ color: pipelineData.offside === "sim" ? "red" : "green" }}>
        {pipelineData.offside === "sim" ? "IMPEDIMENTO" : "LEGAL"}
      </span>
    </h2>
  </div>
)}
    </div>
  );
}

export default App;