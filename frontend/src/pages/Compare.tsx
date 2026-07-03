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
      <p className="text-sm text-slate-500">
        Select 2 or more papers from the Search page to compare them.
      </p>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-semibold mb-4">Compare papers</h1>
      <ul className="text-sm mb-4 list-disc list-inside space-y-1">
        {papersQuery.data?.map((p) => (
          <li key={p.id}>{p.title}</li>
        ))}
      </ul>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="flex gap-2 mb-4"
      >
        <input
          value={aspect}
          onChange={(e) => setAspect(e.target.value)}
          placeholder="Optional: focus on a specific aspect (e.g. datasets, architecture)"
          className="flex-1 border rounded-md px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
        >
          {mutation.isPending ? "Comparing..." : "Compare"}
        </button>
      </form>
      {mutation.data && <AnswerCard answer={mutation.data} />}
    </div>
  );
}
