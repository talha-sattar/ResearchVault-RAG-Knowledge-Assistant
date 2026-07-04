import { Link } from "react-router-dom";
import type { DocumentSummary } from "../api/types";

interface Props {
  document: DocumentSummary;
  snippet?: string;
  meta?: string;
  selectable?: boolean;
  selected?: boolean;
  onToggleSelect?: () => void;
}

export default function PaperCard({ document, snippet, meta, selectable, selected, onToggleSelect }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200/60 bg-white/60 backdrop-blur-md p-5 hover:bg-white hover:shadow-lg hover:shadow-indigo-100/50 hover:border-indigo-200 transition-all duration-300 group">
      <div className="flex items-start gap-4">
        {selectable && (
          <div className="pt-1">
            <input
              type="checkbox"
              checked={!!selected}
              onChange={onToggleSelect}
              className="h-5 w-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer transition-colors"
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <Link to={`/papers/${document.id}`} className="font-semibold text-[1.05rem] text-slate-800 group-hover:text-indigo-600 transition-colors inline-block mb-1">
            {document.title}
          </Link>
          <div className="text-[11px] font-medium text-slate-500 mt-1.5 flex gap-2 flex-wrap items-center">
            {document.primary_category && (
              <span className="bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full border border-indigo-100 shadow-sm">
                {document.primary_category}
              </span>
            )}
            {document.arxiv_id && (
              <span className="bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                arXiv:{document.arxiv_id}
              </span>
            )}
            {document.published_at && (
              <span className="text-slate-400">
                {document.published_at.slice(0, 10)}
              </span>
            )}
          </div>
          {snippet && (
            <p className="text-sm text-slate-600 mt-3 line-clamp-2 leading-relaxed">
              {snippet}
            </p>
          )}
          {meta && (
            <div className="mt-3 inline-flex items-center text-xs font-medium text-indigo-500 bg-indigo-50/50 px-2 py-1 rounded-md">
              {meta}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
