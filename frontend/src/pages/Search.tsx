import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { searchPapers } from "../api/client";
import PaperCard from "../components/PaperCard";

export default function Search() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const mutation = useMutation({ mutationFn: (q: string) => searchPapers(q, 10) });

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className={`max-w-4xl mx-auto animation-fade-in flex flex-col ${!mutation.data && !mutation.isPending ? 'justify-center min-h-[70vh]' : ''}`}>
      <div className="text-center mb-10 mt-8">
        <h1 className="text-4xl font-extrabold mb-3 text-slate-800 tracking-tight">Explore the Vault</h1>
        <p className="text-slate-500 max-w-2xl mx-auto">
          Search across methodology, datasets, and results of all indexed papers using semantic understanding.
        </p>
      </div>

      <div className="bg-white/80 backdrop-blur-md p-2 rounded-2xl shadow-glass border border-white mb-8">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (query.trim()) mutation.mutate(query.trim());
          }}
          className="flex gap-2 relative"
        >
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about methods, datasets, results..."
            className="flex-1 bg-transparent border-0 px-12 py-4 text-slate-800 placeholder:text-slate-400 focus:ring-0 outline-none text-lg"
          />
          <button
            type="submit"
            disabled={mutation.isPending || !query.trim()}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-medium disabled:opacity-50 transition-all shadow-md hover:shadow-lg"
          >
            {mutation.isPending ? "Searching..." : "Search"}
          </button>
        </form>
      </div>

      {!mutation.data && !mutation.isPending && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 mb-8 text-center px-4">
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-3xl border border-white/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-lg shadow-inner">1</div>
            <h3 className="font-bold text-slate-800 mb-2">Search a Topic</h3>
            <p className="text-sm text-slate-600">Enter a research topic like "Brain tumor classification" to query the vault.</p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-3xl border border-white/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 bg-purple-100 text-purple-700 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-lg shadow-inner">2</div>
            <h3 className="font-bold text-slate-800 mb-2">Review Papers</h3>
            <p className="text-sm text-slate-600">Browse the list of relevant semantic results matching your research.</p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-3xl border border-white/80 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 bg-pink-100 text-pink-700 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-lg shadow-inner">3</div>
            <h3 className="font-bold text-slate-800 mb-2">Open & Analyze</h3>
            <p className="text-sm text-slate-600">Open any paper to extract methodology, generate summaries, and take notes.</p>
          </div>
        </div>
      )}

      {selected.size >= 2 && (
        <div className="mb-6 flex justify-end">
          <button
            className="text-sm bg-slate-800 hover:bg-slate-900 text-white px-5 py-2.5 rounded-xl transition-all shadow-md hover:shadow-lg font-medium flex items-center gap-2"
            onClick={() => navigate(`/compare?ids=${Array.from(selected).join(",")}`)}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Compare {selected.size} selected
          </button>
        </div>
      )}

      {mutation.isError && (
        <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl mb-6">
          Search failed. Is the backend running?
        </div>
      )}

      <div className="space-y-4">
        {mutation.data?.results.map((r) => (
          <PaperCard
            key={r.document.id}
            document={r.document}
            snippet={r.snippet}
            meta={`${r.section_type} · p.${r.page_start}-${r.page_end} · score ${(r.score * 100).toFixed(0)}%`}
            selectable
            selected={selected.has(r.document.id)}
            onToggleSelect={() => toggle(r.document.id)}
          />
        ))}
        {mutation.data && mutation.data.results.length === 0 && (
          <div className="text-center py-16 bg-white/40 rounded-2xl border border-white/60 backdrop-blur-sm">
            <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-slate-900">No results</h3>
            <p className="mt-1 text-sm text-slate-500">We couldn't find anything matching that query.</p>
          </div>
        )}
      </div>
    </div>
  );
}
