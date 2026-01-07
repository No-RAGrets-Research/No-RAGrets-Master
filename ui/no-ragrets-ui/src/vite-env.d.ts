/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_PDF_DIRECTORY: string
  readonly VITE_ENABLE_LLM_ANALYSIS: string
  readonly VITE_ENABLE_CROSS_PAPER_VIEW: string
  readonly VITE_ENABLE_VISUAL_KNOWLEDGE: string
  readonly VITE_ENABLE_ADVANCED_GRAPH: string
  readonly VITE_ENABLE_PATH_FINDING: string
  readonly VITE_LLM_API_URL?: string
  readonly VITE_LLM_API_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
