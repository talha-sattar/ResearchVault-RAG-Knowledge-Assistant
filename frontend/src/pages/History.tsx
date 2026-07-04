import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getSearchHistory, getViewHistory } from "../api/client";

export default function History() {
  const searchHistoryQuery = useQuery({ queryKey: ["search-history"], queryFn: getSearchHistory });
  const viewHistoryQuery = useQuery({ queryKey: ["view-history"], queryFn: getViewHistory });

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
    }).format(d);
  };

  return (
    <div className="max-w-5xl mx-auto animation-fade-in pb-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <svg className="w-8 h-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Activity History
        </h1>
        <p className="text-slate-500 mt-1">Review your recent searches and read papers.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="bg-white/70 backdrop-blur-md rounded-3xl p-6 shadow-sm border border-slate-200/60">
          <h2 className="text-xl font-semibold text-slate-800 mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            Search Queries
          </h2>
          <div className="space-y-4">
            {searchHistoryQuery.data?.map((h) => (
              <div key={h.id} className="bg-white border border-slate-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow group cursor-default relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="font-medium text-slate-800 mb-2">{h.query_text}</div>
                <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                  <span className="bg-slate-100 px-2 py-1 rounded-md">{h.result_document_ids.length} results</span>
                  <span className="text-slate-400">{formatDate(h.created_at)}</span>
                </div>
              </div>
            ))}
            {searchHistoryQuery.data?.length === 0 && (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-2xl">
                <p className="text-sm text-slate-500">No recent searches.</p>
              </div>
            )}
            {searchHistoryQuery.isLoading && (
              <div className="flex justify-center py-10">
                <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white/70 backdrop-blur-md rounded-3xl p-6 shadow-sm border border-slate-200/60">
          <h2 className="text-xl font-semibold text-slate-800 mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            Recently Viewed Papers
          </h2>
          <div className="space-y-4">
            {viewHistoryQuery.data?.map((v) => (
              <div key={v.id} className="bg-white border border-slate-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden flex flex-col justify-between">
                <div className="absolute top-0 left-0 w-1 h-full bg-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <Link to={`/papers/${v.document_id}`} className="font-semibold text-indigo-600 hover:text-indigo-800 transition-colors mb-2 block truncate" title={v.document_title}>
                  {v.document_title || `Document ID: ${v.document_id.slice(0, 12)}...`}
                </Link>
                <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                  <span className="bg-slate-100 px-2 py-1 rounded-md capitalize">{v.view_type}</span>
                  <span className="text-slate-400">{formatDate(v.viewed_at)}</span>
                </div>
              </div>
            ))}
            {viewHistoryQuery.data?.length === 0 && (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-2xl">
                <p className="text-sm text-slate-500">No recently viewed papers.</p>
              </div>
            )}
            {viewHistoryQuery.isLoading && (
              <div className="flex justify-center py-10">
                <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
