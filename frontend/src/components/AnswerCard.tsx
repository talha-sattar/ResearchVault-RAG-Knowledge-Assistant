import type { AnswerOut } from "../api/types";

export default function AnswerCard({ answer }: { answer: AnswerOut }) {
  return (
    <div className={`rounded-lg border p-4 ${answer.is_refusal ? "bg-amber-50 border-amber-200" : "bg-white"}`}>
      <p className="whitespace-pre-wrap text-sm leading-relaxed">{answer.text}</p>
      {answer.citations.length > 0 && (
        <div className="mt-3 pt-3 border-t flex flex-wrap gap-2">
          {answer.citations.map((c, i) => (
            <a
              key={i}
              href={c.arxiv_id ? `https://arxiv.org/abs/${c.arxiv_id}` : undefined}
              target="_blank"
              rel="noreferrer"
              className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded hover:bg-indigo-100"
              title={`arXiv:${c.arxiv_id ?? "?"} p.${c.page ?? "?"}`}
            >
              arXiv:{c.arxiv_id} p.{c.page}
            </a>
          ))}
        </div>
      )}
      <div className="mt-2 text-[11px] text-slate-400">
        {answer.provider}/{answer.model} · {answer.latency_ms}ms
      </div>
    </div>
  );
}
