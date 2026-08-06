export const getParameterColor = (param: string): string => {
  const normalized = param.toLowerCase();
  switch (normalized) {
    case 'ph': return '#22d3ee'; // cyan-400
    case 'alkalinity': return '#f472b6'; // pink-400
    case 'calcium': return '#c084fc'; // purple-400
    case 'magnesium': return '#34d399'; // emerald-400
    case 'salinity': return '#60a5fa'; // blue-400
    case 'temperature': return '#fb923c'; // orange-400
    case 'nitrate': return '#f87171'; // red-400
    case 'phosphate': return '#a78bfa'; // violet-400
    default: return '#94a3b8'; // slate-400
  }
};
