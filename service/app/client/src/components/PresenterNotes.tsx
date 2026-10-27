import { Presentation } from 'lucide-react';
import type { PresenterNote } from '@/lib/presenter';

// Hover badge in the page header with the presenter talk track.
export default function PresenterNotes({ note }: { note: PresenterNote }) {
  return (
    <div className="group/notes relative">
      <span className="inline-flex cursor-help items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
        <Presentation className="h-3.5 w-3.5" />
        Presenter Notes
      </span>
      <div className="pointer-events-none absolute right-0 top-8 z-50 w-[420px] rounded-xl border border-amber-200 bg-white p-4 text-sm text-gray-700 opacity-0 shadow-2xl transition-opacity group-hover/notes:pointer-events-auto group-hover/notes:opacity-100">
        <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700">Business aspiration / problem</p>
        <p className="mt-1">{note.aspiration}</p>
        <p className="mt-3 text-[11px] font-bold uppercase tracking-wider text-sf-primary">How Snowflake solves it</p>
        <ul className="mt-1 list-disc space-y-0.5 pl-4">
          {note.snowflake.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
        <p className="mt-3 rounded-lg bg-sky-50 p-2 text-xs italic text-sf-dark">
          <span className="font-semibold not-italic">Say this: </span>
          {note.sayThis}
        </p>
      </div>
    </div>
  );
}
