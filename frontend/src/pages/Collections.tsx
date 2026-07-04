import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCollection,
  deleteCollection,
  getCollection,
  listCollections,
  removeDocumentFromCollection,
} from "../api/client";
import PaperCard from "../components/PaperCard";

export default function Collections() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);

  const collectionsQuery = useQuery({ queryKey: ["collections"], queryFn: listCollections });
  const activeQuery = useQuery({
    queryKey: ["collection", activeId],
    queryFn: () => getCollection(activeId!),
    enabled: !!activeId,
  });

  const createMutation = useMutation({
    mutationFn: () => createCollection(name.trim()),
    onSuccess: () => {
      setName("");
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCollection(id),
    onSuccess: () => {
      if (activeId === id) setActiveId(null);
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });

  const removeDocMutation = useMutation({
    mutationFn: (documentId: string) => removeDocumentFromCollection(activeId!, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["collection", activeId] }),
  });

  return (
    <div className="max-w-6xl mx-auto animation-fade-in pb-12">
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <svg className="w-8 h-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            Collections
          </h1>
          <p className="text-slate-500 mt-1">Organize your research into custom folders.</p>
        </div>
        
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) createMutation.mutate();
          }}
          className="flex gap-2"
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New collection name..."
            className="border-slate-200 rounded-xl px-4 py-2 text-sm w-64 focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm transition-shadow"
          />
          <button 
            type="submit" 
            disabled={!name.trim() || createMutation.isPending}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-xl text-sm font-medium transition-colors shadow-sm disabled:opacity-50"
          >
            Create
          </button>
        </form>
      </div>

      <div className="grid md:grid-cols-[300px_1fr] gap-8 items-start">
        <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-slate-200/60 overflow-hidden flex flex-col max-h-[calc(100vh-12rem)]">
          <div className="bg-slate-50 border-b border-slate-100 p-4">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">Your Folders</h2>
          </div>
          <div className="overflow-y-auto custom-scrollbar p-3 space-y-1">
            {collectionsQuery.data?.map((c) => (
              <div 
                key={c.id} 
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl transition-all cursor-pointer ${
                  activeId === c.id 
                    ? "bg-indigo-50 border border-indigo-100 shadow-sm" 
                    : "hover:bg-slate-50 border border-transparent"
                }`}
                onClick={() => setActiveId(c.id)}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <svg className={`w-5 h-5 flex-shrink-0 ${activeId === c.id ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-500"}`} fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                  </svg>
                  <span className={`text-sm truncate ${activeId === c.id ? "font-semibold text-indigo-900" : "font-medium text-slate-700"}`}>
                    {c.name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${activeId === c.id ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-500"}`}>
                    {c.document_count}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteMutation.mutate(c.id);
                    }}
                    className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-full hover:bg-red-50"
                    title="Delete collection"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
            ))}
            {collectionsQuery.data?.length === 0 && (
              <div className="text-center py-10 px-4">
                <svg className="mx-auto h-10 w-10 text-slate-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <p className="text-sm text-slate-500">No collections yet.</p>
                <p className="text-xs text-slate-400 mt-1">Create one using the form above.</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-transparent">
          {activeQuery.data ? (
            <div className="space-y-6">
              <div className="flex items-center gap-3 pb-4 border-b border-slate-200">
                <h2 className="text-2xl font-bold text-slate-800">{activeQuery.data.name}</h2>
                <span className="bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-xs font-semibold">
                  {activeQuery.data.documents.length} papers
                </span>
              </div>
              
              <div className="space-y-4">
                {activeQuery.data.documents.map((d) => (
                  <div key={d.id} className="relative group">
                    <PaperCard document={d} />
                    <button
                      onClick={() => removeDocMutation.mutate(d.id)}
                      className="absolute top-4 right-4 bg-white border border-slate-200 text-slate-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all shadow-sm z-10"
                      title="Remove from collection"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
              
              {activeQuery.data.documents.length === 0 && (
                <div className="bg-white/60 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-12 text-center">
                  <div className="bg-indigo-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-800 mb-2">This collection is empty</h3>
                  <p className="text-slate-500 max-w-sm mx-auto">
                    You can add papers to this collection from any paper's detail page.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white/40 backdrop-blur-sm border border-slate-200/40 border-dashed rounded-2xl p-12 text-center h-full flex flex-col items-center justify-center min-h-[400px]">
              <svg className="w-16 h-16 text-slate-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
              </svg>
              <h3 className="text-lg font-medium text-slate-600">Select a collection</h3>
              <p className="text-slate-400 mt-2">Choose a collection from the sidebar to view its contents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
