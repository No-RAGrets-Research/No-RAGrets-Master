import type { Relation } from '../../types';
import { EntityTypeBadge } from '../entities';

interface RelationDetailProps {
  relation: Relation;
  onClose: () => void;
  onViewInGraph?: () => void;
}

export const RelationDetail = ({ relation, onClose, onViewInGraph }: RelationDetailProps) => {
  return (
    <div className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
      <div className="flex items-start justify-between mb-4">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
          Relation
        </h4>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          ✕
        </button>
      </div>

      <div className="space-y-3">
        {/* Subject */}
        <div>
          <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Subject</label>
          <div className="mt-1">
            <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
              {relation.subject.name}
            </div>
            <EntityTypeBadge type={relation.subject.type} />
          </div>
        </div>

        {/* Predicate */}
        <div>
          <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Predicate</label>
          <div className="mt-1">
            <span className="px-2 py-1 text-sm font-medium bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
              {relation.predicate}
            </span>
          </div>
        </div>

        {/* Object */}
        <div>
          <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Object</label>
          <div className="mt-1">
            <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
              {relation.object.name}
            </div>
            <EntityTypeBadge type={relation.object.type} />
          </div>
        </div>

        {/* Metadata */}
        <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
            <div>Section: <span className="font-medium">{relation.section}</span></div>
            {relation.pages && relation.pages.length > 0 && (
              <div>Pages: <span className="font-medium">{relation.pages.join(', ')}</span></div>
            )}
            {relation.confidence && (
              <div>Confidence: <span className="font-medium">{(relation.confidence * 100).toFixed(1)}%</span></div>
            )}
          </div>
        </div>

        {/* View in Graph Button */}
        {onViewInGraph && (
          <div className="pt-3">
            <button
              onClick={onViewInGraph}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              View in Graph
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
