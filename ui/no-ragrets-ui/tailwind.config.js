/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors for knowledge graph
        entity: {
          chemical: '#3b82f6',      // blue
          organism: '#10b981',      // green
          process: '#f59e0b',       // amber
          organelle: '#8b5cf6',     // purple
          enzyme: '#ec4899',        // pink
          default: '#6b7280',       // gray
        },
        relation: {
          produces: '#10b981',
          converts: '#3b82f6',
          powers: '#f59e0b',
          default: '#6b7280',
        }
      },
      boxShadow: {
        'highlight': '0 0 0 3px rgba(59, 130, 246, 0.5)',
      }
    },
  },
  plugins: [],
}
