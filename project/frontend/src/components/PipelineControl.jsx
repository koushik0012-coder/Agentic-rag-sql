import React, { useState } from 'react';

export default function PipelineControl({ apiBase }) {
    const [question, setQuestion] = useState("");
    const [currentStep, setCurrentStep] = useState(0);

    // State for each step's data
    const [schemaData, setSchemaData] = useState(null);
    const [sqlData, setSqlData] = useState(null);
    const [validationData, setValidationData] = useState(null);
    const [finalResult, setFinalResult] = useState(null);

    const [loading, setLoading] = useState(false);

    // Helper to call API
    const callApi = async (endpoint, body) => {
        setLoading(true);
        try {
            const res = await fetch(`${apiBase}/pipeline/step/${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            setLoading(false);
            return data;
        } catch (e) {
            console.error(e);
            setLoading(false);
            alert("API Error");
            return null;
        }
    };

    const handleStep1 = async () => {
        if (!question) return;
        const data = await callApi("schema", { question });
        if (data) {
            setSchemaData(data);
            setCurrentStep(1);
        }
    };

    const handleStep2 = async () => {
        const data = await callApi("generate_sql", {
            question,
            table_schema: schemaData.table_schema
        });
        if (data) {
            setSqlData(data);
            setCurrentStep(2);
        }
    };

    const handleStep3 = async () => {
        const data = await callApi("validate_sql", {
            question,
            table_schema: schemaData.table_schema,
            sql_query: sqlData.sql_query
        });
        if (data) {
            setValidationData(data);
            // If validation failed, update SQL data to the fixed query so user sees it
            if (!data.sql_valid) {
                setSqlData(prev => ({ ...prev, sql_query: data.sql_query }));
            }
            setCurrentStep(3);
        }
    };

    const handleStep4 = async () => {
        const data = await callApi("execute", {
            question,
            sql_query: validationData.sql_query
        });
        if (data) {
            setFinalResult(data);
            setCurrentStep(4);
        }
    };

    return (
        <div className="pipeline-flow">
            {/* Input Stage */}
            <div className="input-section">
                <input
                    type="text"
                    placeholder="Ask a question about your data..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                />
                <button onClick={handleStep1} disabled={loading || !question}>
                    Start Pipeline
                </button>
            </div>

            {/* Step 1: Schema Extraction */}
            {(currentStep >= 1) && (
                <div className={`step-card ${currentStep === 1 ? 'active' : 'completed'}`}>
                    <div className="step-header">
                        <div className="step-title">
                            <div className={`step-status-icon ${currentStep === 1 ? 'status-active' : 'status-done'}`}>1</div>
                            Schema Extraction (RAG)
                        </div>
                    </div>
                    <div className="step-content">
                        <strong>Relevant Tables:</strong> {schemaData?.relevant_tables.join(", ")}
                        <hr style={{ borderColor: '#30363d', margin: '0.5rem 0' }} />
                        <div style={{ whiteSpace: 'pre-wrap' }}>{schemaData?.table_schema}</div>
                    </div>
                    {currentStep === 1 && (
                        <div className="step-actions">
                            <button className="step-btn" onClick={handleStep2} disabled={loading}>
                                {loading ? "Generating..." : "Generate SQL →"}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Step 2: SQL Generation */}
            {(currentStep >= 2) && (
                <div className={`step-card ${currentStep === 2 ? 'active' : 'completed'}`}>
                    <div className="step-header">
                        <div className="step-title">
                            <div className={`step-status-icon ${currentStep === 2 ? 'status-active' : 'status-done'}`}>2</div>
                            SQL Generation
                        </div>
                    </div>
                    <div className="step-content">
                        {sqlData?.sql_query}
                    </div>
                    {currentStep === 2 && (
                        <div className="step-actions">
                            <button className="step-btn" onClick={handleStep3} disabled={loading}>
                                {loading ? "Validating..." : "Validate SQL →"}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Step 3: Validation */}
            {(currentStep >= 3) && (
                <div className={`step-card ${currentStep === 3 ? 'active' : 'completed'}`}>
                    <div className="step-header">
                        <div className="step-title">
                            <div className={`step-status-icon ${currentStep === 3 ? 'status-active' : 'status-done'}`}>3</div>
                            Validation & Self-Correction
                        </div>
                    </div>
                    <div className="step-content">
                        <div>Status: <span style={{ color: validationData?.sql_valid ? '#238636' : '#da3633' }}>{validationData?.sql_valid ? "VALID" : "INVALID"}</span></div>
                        {!validationData?.sql_valid && (
                            <div style={{ marginTop: '0.5rem', color: '#da3633' }}>
                                Error: {validationData?.sql_error}
                                <br />
                                <strong>Correction Applied:</strong>
                                <pre>{validationData?.sql_query}</pre>
                            </div>
                        )}
                        {validationData?.sql_valid && <div>No errors found.</div>}
                    </div>
                    {currentStep === 3 && (
                        <div className="step-actions">
                            <button className="step-btn" onClick={handleStep4} disabled={loading}>
                                {loading ? "Executing..." : "Execute & Synthesize →"}
                            </button>
                            {!validationData?.sql_valid && (
                                <button className="step-btn" style={{ marginLeft: '10px', backgroundColor: '#d29922' }} onClick={handleStep3} disabled={loading}>
                                    Retry Validation ↻
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Step 4: Final Result */}
            {(currentStep >= 4) && (
                <div className={`step-card completed`}>
                    <div className="step-header">
                        <div className="step-title">
                            <div className="step-status-icon status-done">4</div>
                            Final Results
                        </div>
                    </div>
                    <div className="step-content">
                        <div style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>{finalResult?.final_answer}</div>

                        {finalResult?.query_result && Array.isArray(finalResult.query_result) && finalResult.query_result.length > 0 && (
                            <div className="data-table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            {Object.keys(finalResult.query_result[0]).map(key => <th key={key}>{key}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {finalResult.query_result.map((row, i) => (
                                            <tr key={i}>
                                                {Object.values(row).map((val, j) => <td key={j}>{val}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                    <div className="step-actions">
                        <button className="step-btn" onClick={() => setCurrentStep(0)} disabled={loading}>
                            Start Over
                        </button>
                    </div>
                </div>
            )}

        </div>
    );
}
