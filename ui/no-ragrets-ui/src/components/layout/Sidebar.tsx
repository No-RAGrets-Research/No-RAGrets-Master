import { Link, useLocation } from 'react-router-dom';
import { usePapers } from '../../hooks/usePaperData';

export const Sidebar = () => {
  const location = useLocation();
  const { data: papers, isLoading } = usePapers();

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen">
      {/* Logo/Title */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          No-RAGrets
        </h1>
        <p className="text-xs text-gray-600 dark:text-gray-400">
          Knowledge Graph Explorer
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          <Link
            to="/"
            className={`block px-4 py-2 rounded-lg transition-colors ${
              isActive('/')
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            Dashboard
          </Link>
          
          <Link
            to="/graph"
            className={`block px-4 py-2 rounded-lg transition-colors ${
              isActive('/graph')
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            Knowledge Graph
          </Link>

          {/* Search link hidden - functionality integrated into Knowledge Graph */}
          {/* <Link
            to="/search"
            className={`block px-4 py-2 rounded-lg transition-colors ${
              isActive('/search')
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            Search
          </Link> */}
        </div>

        {/* Papers List */}
        <div className="mt-6">
          <h3 className="px-4 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            Papers
          </h3>
          {isLoading ? (
            <p className="px-4 text-sm text-gray-500">Loading...</p>
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {papers?.slice(0, 20).map((paper) => (
                <Link
                  key={paper.id}
                  to={`/papers/${encodeURIComponent(paper.id)}`}
                  className={`block px-4 py-2 text-sm rounded-lg transition-colors ${
                    location.pathname === `/papers/${encodeURIComponent(paper.id)}`
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  title={paper.title || paper.filename}
                >
                  <div className="truncate font-medium">
                    {paper.title || paper.filename}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-500">
                    {paper.total_entities} entities
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </nav>
    </aside>
  );
};
