import { cn } from '@/lib/utils';
import { kpiInfo, type KpiInfo } from '@/lib/presenter';
import InfoTip from '@/components/InfoTip';
import {
  Factory,
  CheckCircle2,
  Timer,
  TrendingUp,
  Gauge,
  Trash2,
  Truck,
  RotateCw,
  type LucideIcon,
} from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  icon?: LucideIcon;
  accent?: string;
  className?: string;
  info?: KpiInfo;
  tourId?: string;
}

export default function MetricCard({ title, value, icon: Icon, accent, className, info, tourId }: MetricCardProps) {
  const tip = info ?? kpiInfo(title);
  return (
    <div
      data-tour={tourId}
      className={cn(
        'relative rounded-xl border p-5 shadow-sm transition-transform hover:scale-[1.02]',
        accent ?? 'border-sf-primary/30 bg-gradient-to-br from-blue-50 to-sky-50',
        className
      )}
    >
      {Icon && (
        <div className="pointer-events-none absolute right-1 top-1 overflow-hidden opacity-10">
          <Icon className="h-16 w-16" />
        </div>
      )}
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
        {title}
        {tip && <InfoTip info={tip} />}
      </p>
      <p className="mt-2 text-3xl font-extrabold text-gray-900">{value}</p>
    </div>
  );
}

export { Factory, CheckCircle2, Timer, TrendingUp, Gauge, Trash2, Truck, RotateCw };
