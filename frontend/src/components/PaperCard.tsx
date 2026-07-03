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
    <div className="rounded-lg border bg-white p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-3">
        {selectable && (
          <input
            type="checkbox"
            checked={!!selected}
            onChange={onToggleSelect}
            className="mt-1.5 h-4 w-4 accent-indigo-600"
          />
        )}
        <div className="flex-1 min-w-0">
          <Link to={`/papers/${document.id}`} className="font-medium text-slate-900 hover:text-indigo-700">
            {document.title}
          </Link>
          <div className="text-xs text-slate-500 mt-1 flex gap-2 flex-wrap">
            {document.primary_category && (
              <span className="bg-slate-100 px-1.5 py-0.5 rounded">{document.primary_category}</span>
            )}
            {document.arxiv_id && <span>arXiv:{document.arxiv_id}</span>}
            {document.published_at && <span>{document.published_at.slice(0, 10)}</span>}
          </div>
          {snippet && <p className="text-sm text-slate-600 mt-2 line-clamp-2">{snippet}</p>}
          {meta && <p className="text-xs text-slate-400 mt-1">{meta}</p>}
        </div>
      </div>
    </div>
  );
}
