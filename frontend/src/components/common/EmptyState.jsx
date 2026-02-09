const EmptyState = ({ icon = '📭', title, message, actionText, onAction }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-12 text-center">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-6">{message}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
