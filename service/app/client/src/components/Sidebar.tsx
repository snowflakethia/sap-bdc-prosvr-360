import { useFilters } from '@/hooks/useFilters';
import { cn } from '@/lib/utils';

export type PageId =
  | 'c1' | 'c2' | 'c3' | 'c4'
  | 'p0' | 'p1' | 'p2' | 'p3' | 'p4' | 'p5' | 'p6' | 'p7' | 'p8' | 'p9' | 'p10' | 'p11';

export interface NavItem { id: PageId; code: string; label: string }

/** Sidebar groups (PRD 8.3). */
export const NAV_GROUPS: { title: string; items: NavItem[] }[] = [
  { title: 'Context', items: [
    { id: 'c1', code: 'C1', label: 'Business Overview' },
    { id: 'c2', code: 'C2', label: 'Dashboard Overview' },
    { id: 'c3', code: 'C3', label: 'Demo Overview' },
    { id: 'c4', code: 'C4', label: 'Platform Architecture' },
  ] },
  { title: 'ProServe360', items: [
    { id: 'p0', code: 'P0', label: 'ProServe360 Overview' },
    { id: 'p7', code: 'P7', label: 'Context & Reasoning' },
    { id: 'p10', code: 'P10', label: 'Ask the Advisor' },
  ] },
  { title: 'Operational Excellence', items: [
    { id: 'p1', code: 'P1', label: 'Portfolio & Pareto' },
    { id: 'p2', code: 'P2', label: 'Project Health' },
    { id: 'p11', code: 'P11', label: 'Asset Library' },
  ] },
  { title: 'Value Creation', items: [{ id: 'p5', code: 'P5', label: 'Pipeline & Pursuit' }] },
  { title: 'People Development', items: [
    { id: 'p3', code: 'P3', label: 'Time Mix & Bench' },
    { id: 'p4', code: 'P4', label: 'People Intelligence' },
    { id: 'p6', code: 'P6', label: 'AI Productivity & Learning' },
  ] },
  { title: 'Data', items: [
    { id: 'p8', code: 'P8', label: 'BDC Sources & Lineage' },
    { id: 'p9', code: 'P9', label: 'Data Trust' },
  ] },
];

export const NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);

function Filters() {
  const { filters, setFilters, groups, years, sizes } = useFilters();
  const sel = 'w-full rounded-md border border-white/20 bg-white/10 px-2 py-1 text-xs text-white focus:outline-none';
  return (
    <div className="space-y-2 border-b border-white/10 px-4 pb-4">
      <label className="block text-[10px] font-semibold uppercase tracking-wider text-sf-pale">MD group</label>
      <select className={sel} value={filters.group} onChange={(e) => setFilters({ group: e.target.value })}>
        {groups.map((g) => <option key={g.md_group_id} value={g.md_group_id} className="text-gray-900">{g.md_group_name}</option>)}
        <option value="ALL" className="text-gray-900">Firm-wide</option>
      </select>
      <label className="block text-[10px] font-semibold uppercase tracking-wider text-sf-pale">Fiscal years</label>
      <div className="flex gap-1">
        <select className={sel} value={filters.fy0} onChange={(e) => setFilters({ fy0: Number(e.target.value) })}>
          {years.filter((y) => y <= filters.fy1).map((y) => <option key={y} value={y} className="text-gray-900">FY{y % 100}</option>)}
        </select>
        <select className={sel} value={filters.fy1} onChange={(e) => setFilters({ fy1: Number(e.target.value) })}>
          {years.filter((y) => y >= filters.fy0).map((y) => <option key={y} value={y} className="text-gray-900">FY{y % 100}</option>)}
        </select>
      </div>
      <label className="block text-[10px] font-semibold uppercase tracking-wider text-sf-pale">Size class</label>
      <select className={sel} value={filters.size} onChange={(e) => setFilters({ size: e.target.value })}>
        <option value="ALL" className="text-gray-900">All sizes</option>
        {sizes.map((s) => <option key={s} value={s} className="text-gray-900">{s}</option>)}
      </select>
    </div>
  );
}

export default function Sidebar({ activePage, onNavigate }: { activePage: PageId; onNavigate: (p: PageId) => void }) {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-gradient-to-b from-sf-deeper to-sf-dark text-white">
      <div className="flex items-center gap-2 px-4 py-4">
        <img src="/snowflake_logo.svg" alt="" className="h-7 w-7" />
        <div>
          <p className="text-sm font-bold leading-tight">ACoCo ProServe360</p>
          <p className="text-[10px] text-sf-pale">Partner MD Command Center</p>
        </div>
      </div>
      <Filters />
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV_GROUPS.map((g) => (
          <div key={g.title} className="mb-3">
            <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-sf-pale/80">{g.title}</p>
            {g.items.map((it) => (
              <button key={it.id} onClick={() => onNavigate(it.id)}
                className={cn('flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition',
                  activePage === it.id ? 'bg-white/15 font-semibold text-white' : 'text-white/80 hover:bg-white/10')}>
                <span className="w-7 shrink-0 text-[10px] text-sf-light">{it.code}</span>{it.label}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <p className="px-4 py-3 text-[10px] text-sf-pale/70">SAP Business Data Cloud + Snowflake - as of 1 Oct 2026</p>
    </aside>
  );
}
