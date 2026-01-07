// Feature flags from environment variables
export const features = {
  llmAnalysis: import.meta.env.VITE_ENABLE_LLM_ANALYSIS === 'true',
  crossPaperView: import.meta.env.VITE_ENABLE_CROSS_PAPER_VIEW !== 'false',
  visualKnowledge: import.meta.env.VITE_ENABLE_VISUAL_KNOWLEDGE !== 'false',
  advancedGraph: import.meta.env.VITE_ENABLE_ADVANCED_GRAPH !== 'false',
  pathFinding: import.meta.env.VITE_ENABLE_PATH_FINDING === 'true',
};

// API configuration
export const apiConfig = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  pdfDirectory: import.meta.env.VITE_PDF_DIRECTORY || '/papers',
};

// LLM configuration
export const llmConfig = {
  apiUrl: import.meta.env.VITE_LLM_API_URL || 'http://localhost:8000',
  apiKey: import.meta.env.VITE_LLM_API_KEY || '',
};
