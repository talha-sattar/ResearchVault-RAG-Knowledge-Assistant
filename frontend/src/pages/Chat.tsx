import { useState } from "react";
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
    <div className="max-w-3xl">
      <h1 className="text-xl font-semibold mb-1">Ask across your papers</h1>
      <p className="text-sm text-slate-500 mb-4">
        {docParam ? "Scoped to one paper." : "Searches across your whole indexed collection."}
      </p>

      <div className="space-y-4 mb-4">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="text-right">
              <span className="inline-block bg-indigo-600 text-white text-sm rounded-lg px-3 py-2 max-w-lg text-left">
                {m.content}
              </span>
            </div>
          ) : (
            <div key={i}>
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
        {mutation.isPending && <p className="text-sm text-slate-400">Thinking...</p>}
      </div>

      <form onSubmit={submit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 border rounded-md px-3 py-2 text-sm"
        />
        <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium">
          Send
        </button>
      </form>
    </div>
  );
}
