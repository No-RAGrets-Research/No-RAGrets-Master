import type { EntityType } from '../../types';

interface EntityTypeBadgeProps {
  type: EntityType;
  count?: number;
}

const entityTypeColors: Record<EntityType, { bg: string; text: string; darkBg: string; darkText: string }> = {
  chemical: { bg: 'bg-blue-100', text: 'text-blue-700', darkBg: 'dark:bg-blue-900', darkText: 'dark:text-blue-300' },
  organism: { bg: 'bg-green-100', text: 'text-green-700', darkBg: 'dark:bg-green-900', darkText: 'dark:text-green-300' },
  process: { bg: 'bg-amber-100', text: 'text-amber-700', darkBg: 'dark:bg-amber-900', darkText: 'dark:text-amber-300' },
  organelle: { bg: 'bg-purple-100', text: 'text-purple-700', darkBg: 'dark:bg-purple-900', darkText: 'dark:text-purple-300' },
  enzyme: { bg: 'bg-red-100', text: 'text-red-700', darkBg: 'dark:bg-red-900', darkText: 'dark:text-red-300' },
  protein: { bg: 'bg-pink-100', text: 'text-pink-700', darkBg: 'dark:bg-pink-900', darkText: 'dark:text-pink-300' },
  gene: { bg: 'bg-indigo-100', text: 'text-indigo-700', darkBg: 'dark:bg-indigo-900', darkText: 'dark:text-indigo-300' },
  metabolite: { bg: 'bg-cyan-100', text: 'text-cyan-700', darkBg: 'dark:bg-cyan-900', darkText: 'dark:text-cyan-300' },
  pathway: { bg: 'bg-teal-100', text: 'text-teal-700', darkBg: 'dark:bg-teal-900', darkText: 'dark:text-teal-300' },
  measurement: { bg: 'bg-orange-100', text: 'text-orange-700', darkBg: 'dark:bg-orange-900', darkText: 'dark:text-orange-300' },
  condition: { bg: 'bg-lime-100', text: 'text-lime-700', darkBg: 'dark:bg-lime-900', darkText: 'dark:text-lime-300' },
};

export const EntityTypeBadge = ({ type, count }: EntityTypeBadgeProps) => {
  const colors = entityTypeColors[type] || entityTypeColors.chemical;

  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
      <span className={`px-2 py-1 text-xs font-medium rounded ${colors.bg} ${colors.text} ${colors.darkBg} ${colors.darkText}`}>
        {type}
      </span>
      {count !== undefined && (
        <span className="text-sm text-gray-600 dark:text-gray-400">{count}</span>
      )}
    </div>
  );
};
