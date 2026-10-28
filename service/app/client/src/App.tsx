import { useEffect, useState } from 'react';
import { FilterProvider, useFilters } from '@/hooks/useFilters';
import Sidebar, { NAV_ITEMS, type PageId } from '@/components/Sidebar';
import { BusinessOverview, DashboardOverview, DemoOverview } from '@/pages/Context';
import Architecture from '@/pages/Architecture';
import Overview from '@/pages/Overview';
import Portfolio from '@/pages/Portfolio';
import ProjectHealth from '@/pages/ProjectHealth';
import TimeMix from '@/pages/TimeMix';
import People from '@/pages/People';
import Pipeline from '@/pages/Pipeline';
import AiProductivity from '@/pages/AiProductivity';
import Reasoning from '@/pages/Reasoning';
import Lineage from '@/pages/Lineage';
import Trust from '@/pages/Trust';
import Advisor from '@/pages/Advisor';
import Assets from '@/pages/Assets';

export type Navigate = (p: PageId) => void;

function Shell() {
  // The app opens on C1 (PRD 8.3); #p8 etc. deep-links a page (presenter bookmarks).
  const fromHash = (): PageId => {
    const h = window.location.hash.slice(1).toLowerCase();
    return (NAV_ITEMS.some((n) => n.id === h) ? h : 'c1') as PageId;
  };
  const [page, setPage] = useState<PageId>(fromHash);
  const { setProject } = useFilters();
  useEffect(() => {
    const onHash = () => setPage(fromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const nav: Navigate = (p) => { setPage(p); window.history.replaceState(null, '', `#${p}`); window.scrollTo(0, 0); };
  const openProject = (id: string) => { setProject(id); nav('p2'); };

  const pages: Record<PageId, JSX.Element> = {
    c1: <BusinessOverview nav={nav} />,
    c2: <DashboardOverview nav={nav} />,
    c3: <DemoOverview nav={nav} />,
    c4: <Architecture />,
    p0: <Overview nav={nav} openProject={openProject} />,
    p1: <Portfolio openProject={openProject} />,
    p2: <ProjectHealth nav={nav} />,
    p3: <TimeMix />,
    p4: <People />,
    p5: <Pipeline />,
    p6: <AiProductivity />,
    p7: <Reasoning openProject={openProject} />,
    p8: <Lineage />,
    p9: <Trust />,
    p10: <Advisor />,
    p11: <Assets openProject={openProject} />,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar activePage={page} onNavigate={nav} />
      <main className="ml-64 p-8" data-page={NAV_ITEMS.find((n) => n.id === page)?.code}>{pages[page]}</main>
    </div>
  );
}

export default function App() {
  return (
    <FilterProvider>
      <Shell />
    </FilterProvider>
  );
}
