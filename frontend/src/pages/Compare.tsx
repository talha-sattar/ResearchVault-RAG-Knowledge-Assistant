import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { comparePapers, getPaper } from "../api/client";
import AnswerCard from "../components/AnswerCard";

export default function Compare() {
  const [searchParams] = useSearchParams();
  const ids = (searchParams.get("ids") ?? "").split(",").filter(Boolean);
  const [aspect, setAspect] = useState("");

  const papersQuery = useQuery({
    queryKey: ["compare-papers", ids],
    queryFn: () => Promise.all(ids.map((id) => getPaper(id))),
    enabled: ids.length >= 2,
  });

  const mutation = useMutation({ mutationFn: () => comparePapers(ids, aspect.trim() || undefined) });

  if (ids.length < 2) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animation-fade-in">
        <div className="bg-indigo-50 p-4 rounded-full mb-4">
          <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-slate-800 mb-2">Not enough papers selected</h2>
        <p className="text-slate-500 max-w-md">
          Please select 2 or more papers from the Search page to compare their methodologies, datasets, and findings.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animation-fade-in space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2 flex items-center gap-3">
          <svg className="w-8 h-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Compare Papers
        </h1>
        <p className="text-slate-500">Synthesizing information across {ids.length} selected documents.</p>
      </div>

      <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-slate-200/60">
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Selected for Comparison</h3>
        <ul className="space-y-3 mb-6">
          {papersQuery.data?.map((p, i) => (
            <li key={p.id} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold mt-0.5">
                {i + 1}
              </span>
              <span className="text-slate-800 font-medium">{p.title}</span>
            </li>
          ))}
          {papersQuery.isLoading && (
            <li className="text-slate-400 flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-slate-200 border-t-indigo-500 rounded-full animate-spin"></div>
              Loading paper details...
            </li>
          )}
        </ul>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
          className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col sm:flex-row gap-3"
        >
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
              <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              value={aspect}
              onChange={(e) => setAspect(e.target.value)}
              placeholder="Optional: focus on specific aspects (e.g., datasets, architectures, results)"
              className="w-full bg-white border border-slate-200 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-shadow"
            />
          </div>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors shadow-sm whitespace-nowrap flex justify-center items-center min-w-[120px]"
          >
            {mutation.isPending ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> 
                Analyzing
              </span>
            ) : "Compare Now"}
          </button>
        </form>
      </div>

      {mutation.data && (
        <div className="animation-fade-in">
          <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            Comparison Results
          </h2>
          <AnswerCard answer={mutation.data} />
        </div>
      )}
    </div>
  );
}
