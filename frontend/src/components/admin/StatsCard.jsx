const StatsCard = ({ title, value, icon, color, subtitle }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-2">{subtitle}</p>}
        </div>
        <div
          className={`${color} w-14 h-14 rounded-full flex items-center justify-center text-2xl shadow-md`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
};

export default StatsCard;