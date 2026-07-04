import React from "react";
import type { AnswerOut, Citation } from "../api/types";

export default function AnswerCard({ answer }: { answer: AnswerOut }) {
  // Regex to match "Doc 1" or "Doc 1, p.3"
  const citationRegex = /(Doc\s*(\d+)(?:\s*,\s*p\.?\s*(\d+(?:\s*-\s*\d+)?))?)/gi;

  const renderTextWithCitations = (text: string, citations: Citation[]) => {
    const parts = text.split(citationRegex);
    // parts array will look like: 
    // [ "Text before ", "Doc 1, p.3", "1", "3", "] More text" ]
    // The match is at index 1, doc_index at 2, page at 3, next text at 4.
    // However, split with regex with multiple capture groups is tricky.
    // Let's use a simpler approach with string.split combined with matched chunks
    
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;
    
    // We must use RegExp.exec to iterate
    const regex = new RegExp(citationRegex);
    let match;
    while ((match = regex.exec(text)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        elements.push(text.substring(lastIndex, match.index));
      }
      
      const docIndex = parseInt(match[2], 10);
      const citation = citations.find(c => c.doc_index === docIndex);
      
      if (citation) {
        const arxivUrl = citation.arxiv_id ? `https://arxiv.org/abs/${citation.arxiv_id}` : undefined;
        elements.push(
          <a
            key={match.index}
            href={arxivUrl}
            target="_blank"
            rel="noreferrer"
            className="text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 px-1 rounded transition-colors font-medium cursor-pointer"
            title={`arXiv:${citation.arxiv_id ?? "?"} p.${(match[3] || citation.page) ?? "?"}`}
          >
            {match[0]}
          </a>
        );
      } else {
        // Fallback if citation not found
        elements.push(<span key={match.index}>{match[0]}</span>);
      }
      
      lastIndex = regex.lastIndex;
    }
    
    if (lastIndex < text.length) {
      elements.push(text.substring(lastIndex));
    }
    
    return elements;
  };

  return (
    <div className={`rounded-2xl border p-5 shadow-sm hover:shadow-md transition-shadow duration-300 ${answer.is_refusal ? "bg-amber-50/80 border-amber-200 backdrop-blur-sm" : "bg-white/80 backdrop-blur-sm border-slate-200"}`}>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
        {renderTextWithCitations(answer.text, answer.citations)}
      </p>
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="text-[11px] font-medium text-slate-400 bg-slate-100/50 px-2 py-1 rounded-md">
          {answer.provider} / {answer.model} <span className="mx-1">&middot;</span> {answer.latency_ms}ms
        </div>
      </div>
    </div>
  );
}
