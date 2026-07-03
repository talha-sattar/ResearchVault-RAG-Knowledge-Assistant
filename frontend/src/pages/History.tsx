import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getSearchHistory, getViewHistory } from "../api/client";

export default function History() {
  const searchHistoryQuery = useQuery({ queryKey: ["search-history"], queryFn: getSearchHistory });
  const viewHistoryQuery = useQuery({ queryKey: ["view-history"], queryFn: getViewHistory });

  return (
    <div className="grid grid-cols-2 gap-8">
      <div>
        <h1 className="text-xl font-semibold mb-4">Search history</h1>
        <div className="space-y-2">
          {searchHistoryQuery.data?.map((h) => (
            <div key={h.id} className="bg-white border rounded-md p-2 text-sm">
              <div className="font-medium">{h.query_text}</div>
              <div className="text-xs text-slate-400">
                {h.search_type} · {h.result_document_ids.length} results · {h.created_at.slice(0, 16).replace("T", " ")}
              </div>
            </div>
          ))}
          {searchHistoryQuery.data?.length === 0 && <p className="text-sm text-slate-400">No searches yet.</p>}
        </div>
      </div>
      <div>
        <h1 className="text-xl font-semibold mb-4">Reading history</h1>
        <div className="space-y-2">
          {viewHistoryQuery.data?.map((v) => (
            <div key={v.id} className="bg-white border rounded-md p-2 text-sm flex justify-between">
              <Link to={`/papers/${v.document_id}`} className="text-indigo-600 hover:underline">
                {v.document_id.slice(0, 8)}...
              </Link>
              <span className="text-xs text-slate-400">
                {v.view_type} · {v.viewed_at.slice(0, 16).replace("T", " ")}
              </span>
            </div>
          ))}
          {viewHistoryQuery.data?.length === 0 && <p className="text-sm text-slate-400">No views yet.</p>}
        </div>
      </div>
    </div>
  );
}
