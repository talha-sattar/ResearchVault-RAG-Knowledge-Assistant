import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { askChat } from "../api/client";
import type { MessageOut } from "../api/types";
import AnswerCard from "../components/AnswerCard";

export default function Chat() {
  const [searchParams] = useSearchParams();
  const docParam = searchParams.get("doc");
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string; msg?: MessageOut }[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, mutation.isPending]);

  const mutation = useMutation({
    mutationFn: (q: string) => askChat(q, docParam ? [docParam] : undefined, conversationId),
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: data.message.content, msg: data.message }]);
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    mutation.mutate(q);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col animation-fade-in">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Ask across your papers</h1>
        <p className="text-sm font-medium text-slate-500 mt-1 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${docParam ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
          {docParam ? "Scoped to one selected paper." : "Searching across your entire indexed collection."}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto pr-4 pb-4 space-y-6 custom-scrollbar">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <svg className="w-16 h-16 mb-4 text-indigo-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p>Start a conversation by asking a question below.</p>
          </div>
        )}
        
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 text-white text-sm rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl shadow-md">
                {m.content}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start max-w-3xl">
              {m.msg && (
                <AnswerCard
                  answer={{
                    text: m.msg.content,
                    citations: m.msg.citations,
                    is_refusal: false,
                    provider: "",
                    model: "",
                    latency_ms: 0,
                  }}
                />
              )}
            </div>
          )
        )}
        {mutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-white/60 backdrop-blur-sm border border-slate-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm flex items-center gap-2 text-slate-500 text-sm">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
              <span className="ml-2">Searching & thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-auto pt-4 border-t border-slate-200/50">
        <form onSubmit={submit} className="flex gap-3 bg-white/80 backdrop-blur-md p-2 rounded-2xl shadow-glass border border-white">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 bg-transparent border-0 px-4 py-2 text-slate-800 placeholder:text-slate-400 focus:ring-0 outline-none"
            disabled={mutation.isPending}
          />
          <button 
            type="submit" 
            disabled={mutation.isPending || !question.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
