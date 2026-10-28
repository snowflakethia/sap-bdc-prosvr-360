import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getPage, type Filters, type Rows } from '@/lib/api';

/** Global filters (PRD 8.3): MD group (default Financial Services, or Firm-wide), fiscal-year range, size class. */
interface FilterContextType {
  filters: Filters;
  setFilters: (f: Partial<Filters>) => void;
  groups: Rows;
  years: number[];
  sizes: string[];
  project: string; // project selected for drill-down (P2 / P11)
  setProject: (p: string) => void;
}

const DEFAULT: Filters = { group: 'FS', fy0: 2022, fy1: 2026, size: 'ALL' };

const FilterContext = createContext<FilterContextType>({
  filters: DEFAULT,
  setFilters: () => {},
  groups: [],
  years: [],
  sizes: [],
  project: 'P-0615',
  setProject: () => {},
});

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, set] = useState<Filters>(DEFAULT);
  const [groups, setGroups] = useState<Rows>([]);
  const [years, setYears] = useState<number[]>([]);
  const [sizes, setSizes] = useState<string[]>([]);
  const [project, setProject] = useState('P-0615');

  useEffect(() => {
    getPage('filters', DEFAULT)
      .then((d) => {
        setGroups(d.f_groups);
        setYears(d.f_years.map((r) => Number(r.fiscal_year)));
        setSizes(d.f_sizes.map((r) => String(r.size_class)));
      })
      .catch(() => {});
  }, []);

  const setFilters = (f: Partial<Filters>) => set((old) => ({ ...old, ...f }));
  return React.createElement(
    FilterContext.Provider,
    { value: { filters, setFilters, groups, years, sizes, project, setProject } },
    children,
  );
}

export function useFilters() {
  return useContext(FilterContext);
}
