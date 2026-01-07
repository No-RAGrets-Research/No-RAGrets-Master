interface ViewModeToggleProps {
  mode: 'reference' | 'annotated';
  onModeChange: (mode: 'reference' | 'annotated') => void;
}

export const ViewModeToggle = ({ mode, onModeChange }: ViewModeToggleProps) => {
  return (
    <div className="flex gap-2 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
      <button
        onClick={() => onModeChange('reference')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          mode === 'reference'
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
        }`}
      >
        Reference
      </button>
      <button
        onClick={() => onModeChange('annotated')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          mode === 'annotated'
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
        }`}
      >
        Annotated
      </button>
    </div>
  );
};
