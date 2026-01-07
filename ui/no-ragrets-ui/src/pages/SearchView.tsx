import { useState } from 'react';
import { useEntitySearch } from '../hooks/useEntitySearch';

export const SearchView = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: entities, isLoading } = useEntitySearch(
    { q: searchTerm, limit: 20 },
    searchTerm.length > 2
  );

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Search Entities
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Search for entities across all papers
        </p>

        <input
          type="text"
          placeholder="Search for entities (e.g., 'methanol', 'ATP', 'methane')..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-4 text-lg border border-gray-300 dark:border-gray-600 rounded-lg mb-6
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />

        {isLoading && searchTerm.length > 2 && (
          <p className="text-gray-600 dark:text-gray-400">Searching...</p>
        )}

        {entities && entities.length > 0 && (
          <div className="space-y-3">
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Found {entities.length} entities
            </p>
            {entities.map((entity) => (
              <div
                key={entity.id}
                className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg
                         hover:border-blue-500 dark:hover:border-blue-400 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                      {entity.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      ID: {entity.id}
                    </p>
                  </div>
                  <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 
                               text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium">
                    {entity.type}
                  </span>
                </div>
                {entity.namespace && (
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    Namespace: {entity.namespace}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {entities && entities.length === 0 && searchTerm.length > 2 && !isLoading && (
          <p className="text-gray-600 dark:text-gray-400">No entities found</p>
        )}

        {searchTerm.length <= 2 && searchTerm.length > 0 && (
          <p className="text-gray-500 dark:text-gray-500 text-sm">
            Type at least 3 characters to search
          </p>
        )}
      </div>
    </div>
  );
};
