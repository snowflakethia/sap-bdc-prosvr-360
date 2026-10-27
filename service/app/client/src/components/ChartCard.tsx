import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { kpiInfo } from '@/lib/presenter';
import InfoTip from '@/components/InfoTip';

interface ChartCardProps {
  title: string;
  children: ReactNode;
  className?: string;
  subtitle?: string;
  tourId?: string;
}

export default function ChartCard({ title, children, className, subtitle, tourId }: ChartCardProps) {
  // Chart titles like "Scrap Rate by Plant" reuse the KPI they plot.
  const tip = kpiInfo(title) ?? kpiInfo(title.replace(/\s+(by|trend|forecast|over time).*$/i, ''));
  return (
    <div
      data-tour={tourId}
      className={cn(
        'rounded-xl border border-gray-200 bg-white p-6 shadow-md transition-shadow hover:shadow-lg',
        className
      )}
    >
      <div className="mb-4">
        <h3 className="flex items-center gap-2 text-lg font-bold text-gray-900">
          {title}
          {tip && <InfoTip info={tip} />}
        </h3>
        {subtitle && <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>}
      </div>
      <div className="min-h-[280px]">
        {children}
      </div>
    </div>
  );
}
