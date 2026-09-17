import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const norm = (status || '').toUpperCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  if (norm === 'CRITICAL' || norm === 'DISMISSED_AFTER_REVIEW') {
    colorClasses = 'bg-red-50 text-red-700 border-red-200 font-semibold';
  } else if (norm === 'HIGH' || norm === 'EN_ROUTE' || norm === 'DEGRADED') {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 font-medium';
  } else if (norm === 'MODERATE' || norm === 'ASSIGNED' || norm === 'LIKELY') {
    colorClasses = 'bg-yellow-50 text-yellow-800 border-yellow-200';
  } else if (norm === 'LOW' || norm === 'AVAILABLE' || norm === 'RESOLVED' || norm === 'CONFIRMED' || norm === 'APPROVED') {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-medium';
  } else if (norm === 'RECEIVED' || norm === 'CORROBORATED' || norm === 'ON_SCENE') {
    colorClasses = 'bg-blue-50 text-blue-700 border-blue-200 font-medium';
  } else if (norm === 'UNVERIFIED' || norm === 'UNKNOWN' || norm === 'OFFLINE' || norm === 'MAINTENANCE') {
    colorClasses = 'bg-slate-100 text-slate-600 border-slate-300';
  }

  const sizeClass = size === 'sm' ? 'text-[11px] px-2 py-0.5' : size === 'md' ? 'text-xs px-2.5 py-1' : 'text-sm px-3 py-1.5';

  return (
    <span className={`inline-flex items-center rounded-full border ${sizeClass} ${colorClasses} tracking-wide`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-75" />
      {status}
    </span>
  );
};
