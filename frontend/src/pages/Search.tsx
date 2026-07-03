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
    <div>
      <h1 className="text-xl font-semibold mb-4">Search papers</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (query.trim()) mutation.mutate(query.trim());
        }}
        className="flex gap-2 mb-6"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about methods, datasets, results..."
          className="flex-1 border rounded-md px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
        >
          {mutation.isPending ? "Searching..." : "Search"}
        </button>
      </form>

      {selected.size >= 2 && (
        <div className="mb-4 flex justify-end">
          <button
            className="text-sm bg-emerald-600 text-white px-3 py-1.5 rounded-md"
            onClick={() => navigate(`/compare?ids=${Array.from(selected).join(",")}`)}
          >
            Compare {selected.size} selected papers
          </button>
        </div>
      )}

      {mutation.isError && <p className="text-red-600 text-sm">Search failed. Is the backend running?</p>}

      <div className="space-y-3">
        {mutation.data?.results.map((r) => (
          <PaperCard
            key={r.document.id}
            document={r.document}
            snippet={r.snippet}
            meta={`${r.section_type} · p.${r.page_start}-${r.page_end} · score ${r.score.toFixed(2)}`}
            selectable
            selected={selected.has(r.document.id)}
            onToggleSelect={() => toggle(r.document.id)}
          />
        ))}
        {mutation.data && mutation.data.results.length === 0 && (
          <p className="text-slate-500 text-sm">No results. Try a different query.</p>
        )}
      </div>
    </div>
  );
}
