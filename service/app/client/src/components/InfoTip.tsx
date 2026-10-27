import { Info } from 'lucide-react';
import type { KpiInfo } from '@/lib/presenter';

// Hover "i" icon showing a KPI definition, formula and source (pure CSS hover).
export default function InfoTip({ info, align = 'left' }: { info: KpiInfo; align?: 'left' | 'right' }) {
  return (
    <span className="group/info relative inline-flex align-middle">
      <Info className="h-3.5 w-3.5 cursor-help text-gray-400 transition-colors group-hover/info:text-sf-primary" aria-label="Definition" />
      <span
        className={`pointer-events-none absolute top-5 z-50 w-72 rounded-lg border border-gray-200 bg-white p-3 text-left text-xs normal-case tracking-normal text-gray-700 opacity-0 shadow-xl transition-opacity group-hover/info:opacity-100 ${
          align === 'right' ? 'right-0' : 'left-0'
        }`}
      >
        <span className="block font-medium text-gray-900">{info.definition}</span>
        {info.formula && (
          <span className="mt-2 block">
            <span className="font-semibold text-sf-primary">Calculation: </span>
            <code className="font-mono text-[11px]">{info.formula}</code>
          </span>
        )}
        <span className="mt-1.5 block text-gray-500">
          <span className="font-semibold">Source: </span>
          {info.source}
        </span>
      </span>
    </span>
  );
}
