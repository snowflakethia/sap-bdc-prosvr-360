import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { NAV_ITEMS, type PageId } from '@/components/Sidebar';
import { TOUR_STEPS, type TourStep } from '@/lib/presenter';

// Dependency-free guided tour: dims the page, spotlights a [data-tour] anchor and
// shows a step card next to it. Steps can switch pages and select tabs.
export const TOUR_DONE_KEY = 'sc360.tour.done';

const CARD_W = 340;
const GAP = 14;
const MARGIN = 12;
const PAD = 8;

type Rect = { top: number; left: number; width: number; height: number };

const find = (id: string) => document.querySelector<HTMLElement>(`[data-tour="${id}"]`);

function placeCard(r: Rect | null, cardH: number, pref: TourStep['placement'] = 'bottom') {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  if (!r) return { top: (vh - cardH) / 2, left: (vw - CARD_W) / 2 };
  const fits = {
    top: r.top - GAP - cardH >= MARGIN,
    bottom: r.top + r.height + GAP + cardH <= vh - MARGIN,
    left: r.left - GAP - CARD_W >= MARGIN,
    right: r.left + r.width + GAP + CARD_W <= vw - MARGIN,
  };
  const order = [pref, 'bottom', 'top', 'right', 'left'] as const;
  const side = order.find((s) => s && fits[s]);
  let top: number;
  let left: number;
  switch (side) {
    case 'top': top = r.top - GAP - cardH; left = r.left; break;
    case 'right': top = r.top; left = r.left + r.width + GAP; break;
    case 'left': top = r.top; left = r.left - GAP - CARD_W; break;
    case 'bottom': top = r.top + r.height + GAP; left = r.left; break;
    // Anchor fills the screen: float the card over its lower-right corner.
    default: top = vh - cardH - MARGIN * 2; left = vw - CARD_W - MARGIN * 2;
  }
  return {
    top: Math.min(Math.max(top, MARGIN), vh - cardH - MARGIN),
    left: Math.min(Math.max(left, MARGIN), vw - CARD_W - MARGIN),
  };
}

interface Props {
  onClose: () => void;
  activePage: PageId;
  setActivePage: (p: PageId) => void;
}

export default function GuidedTour({ onClose, activePage, setActivePage }: Props) {
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const [ready, setReady] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const cardRef = useRef<HTMLDivElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const anchorRef = useRef<HTMLElement | null>(null);

  const step = TOUR_STEPS[index];
  const last = index === TOUR_STEPS.length - 1;
  const pageLabel = NAV_ITEMS.find((n) => n.id === step.page)?.label ?? step.page;

  const finish = useCallback(() => {
    localStorage.setItem(TOUR_DONE_KEY, '1');
    onClose();
  }, [onClose]);
  const go = useCallback((i: number) => setIndex(Math.min(Math.max(i, 0), TOUR_STEPS.length - 1)), []);

  const measure = useCallback(() => {
    const el = anchorRef.current;
    if (!el || !el.isConnected) return setRect(null);
    const b = el.getBoundingClientRect();
    setRect({ top: b.top - PAD, left: b.left - PAD, width: b.width + PAD * 2, height: b.height + PAD * 2 });
  }, []);

  // Switch page / tab, then wait for the anchor to render (pages fetch data first).
  useEffect(() => {
    if (step.page !== activePage) setActivePage(step.page);
    setReady(false);
    anchorRef.current = null;
    let raf = 0;
    let tabDone = !step.activate;
    const start = performance.now();
    const poll = () => {
      if (!tabDone) {
        const tab = find(step.activate!);
        if (tab) {
          // Radix tabs select on focus (automatic activation mode).
          tab.focus({ preventScroll: true });
          tabDone = true;
        }
      }
      const el = tabDone && step.anchor ? find(step.anchor) : null;
      if (el && el.getBoundingClientRect().height > 0) {
        anchorRef.current = el;
        el.scrollIntoView({ block: 'center', behavior: 'instant' as ScrollBehavior });
        measure();
        setReady(true);
      } else if (!step.anchor || performance.now() - start > 1500) {
        measure();
        setReady(true);
      } else {
        raf = requestAnimationFrame(poll);
      }
    };
    raf = requestAnimationFrame(() => requestAnimationFrame(poll));
    return () => cancelAnimationFrame(raf);
    // activePage intentionally omitted: only a step change should trigger navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  // Track layout changes while a step is shown.
  useEffect(() => {
    if (!ready) return;
    const ro = new ResizeObserver(measure);
    if (anchorRef.current) ro.observe(anchorRef.current);
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, true);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', measure);
      window.removeEventListener('scroll', measure, true);
    };
  }, [ready, measure]);

  useLayoutEffect(() => {
    if (!ready) return;
    setPos(placeCard(rect, cardRef.current?.offsetHeight ?? 200, step.placement));
  }, [ready, rect, step.placement]);

  useEffect(() => {
    if (ready) nextRef.current?.focus({ preventScroll: true });
  }, [ready, index]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.preventDefault(); finish(); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); if (last) finish(); else go(index + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); go(index - 1); }
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [index, last, go, finish]);

  return (
    <div className="fixed inset-0 z-[1000]" aria-hidden={false}>
      {/* Click-blocker: keeps clicks during the tour from navigating away. */}
      <div className="absolute inset-0" style={{ background: rect && ready ? 'transparent' : 'rgba(2,6,23,.65)' }} />
      {rect && ready && (
        <div
          className="pointer-events-none absolute rounded-xl ring-2 ring-sky-400 transition-all duration-200"
          style={{ ...rect, boxShadow: '0 0 0 9999px rgba(2,6,23,.65)' }}
        />
      )}
      <div
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-title"
        aria-describedby="tour-body"
        className="absolute rounded-xl border border-slate-700 bg-slate-900 p-5 text-slate-200 shadow-2xl transition-[top,left,opacity] duration-200"
        style={{ width: CARD_W, top: pos.top, left: pos.left, opacity: ready ? 1 : 0 }}
      >
        <p className="text-[11px] font-bold uppercase tracking-wider text-sky-400">
          {pageLabel} · {index + 1} of {TOUR_STEPS.length}
        </p>
        <h2 id="tour-title" className="mt-2 text-lg font-bold text-white">{step.title}</h2>
        <p id="tour-body" aria-live="polite" className="mt-2 text-sm leading-relaxed text-slate-300">{step.body}</p>

        <div className="mt-5 flex items-center gap-2">
          <div className="flex gap-1.5">
            {TOUR_STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => go(i)}
                aria-label={`Go to step ${i + 1}`}
                aria-current={i === index ? 'step' : undefined}
                className={`h-1.5 rounded-full transition-all ${i === index ? 'w-5 bg-sky-400' : 'w-3 bg-slate-600 hover:bg-slate-500'}`}
              />
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button onClick={finish} className="whitespace-nowrap px-1 text-xs text-slate-400 hover:text-white">Skip tour</button>
            {index > 0 && (
              <button onClick={() => go(index - 1)} className="rounded-md border border-slate-600 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-800">
                Back
              </button>
            )}
            <button
              ref={nextRef}
              onClick={() => (last ? finish() : go(index + 1))}
              className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white ring-sky-300 hover:bg-sky-500 focus:outline-none focus-visible:ring-2"
            >
              {last ? 'Finish' : 'Next'}
            </button>
          </div>
        </div>
        <p className="mt-4 border-t border-slate-800 pt-3 text-[11px] text-slate-500">
          ← → to move · Esc to close · replay from Take the tour in the header
        </p>
      </div>
    </div>
  );
}
