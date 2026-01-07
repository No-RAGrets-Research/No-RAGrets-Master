import { usePapers } from '../hooks/usePaperData';
import { useNavigate } from 'react-router-dom';

export const Dashboard = () => {
  const { data: papers, isLoading, error } = usePapers();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-600 dark:text-gray-400">Loading papers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600 dark:text-red-400">Error: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Knowledge Graph Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Explore {papers?.length || 0} research papers and their extracted knowledge
        </p>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Total Papers
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              {papers?.length || 0}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Total Entities
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              {papers?.reduce((sum, p) => sum + (p.total_entities || 0), 0) || 0}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Total Relations
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              {papers?.reduce((sum, p) => sum + (p.total_relations || 0), 0) || 0}
            </p>
          </div>
        </div>

        {/* Papers Grid */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Recent Papers
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {papers?.map((paper) => (
              <div
                key={paper.id}
                onClick={() => navigate(`/papers/${encodeURIComponent(paper.id)}`)}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer"
              >
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                  {paper.title || paper.filename}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {paper.filename}
                </p>
                <div className="flex gap-4 text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    <span className="font-medium">{paper.total_entities}</span> entities
                  </span>
                  <span className="text-gray-600 dark:text-gray-400">
                    <span className="font-medium">{paper.total_relations}</span> relations
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
