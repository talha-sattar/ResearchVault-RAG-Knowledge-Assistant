import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addDocumentToCollection,
  createNote,
  deleteNote,
  extractPaper,
  getPaper,
  listCollections,
  listNotes,
  relatedPapers,
  summarizePaper,
} from "../api/client";
import AnswerCard from "../components/AnswerCard";
import PaperCard from "../components/PaperCard";

export default function PaperDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [noteText, setNoteText] = useState("");

  const paperQuery = useQuery({ queryKey: ["paper", id], queryFn: () => getPaper(id!), enabled: !!id });
  const notesQuery = useQuery({ queryKey: ["notes", id], queryFn: () => listNotes(id!), enabled: !!id });
  const relatedQuery = useQuery({ queryKey: ["related", id], queryFn: () => relatedPapers(id!, 5), enabled: !!id });
  const collectionsQuery = useQuery({ queryKey: ["collections"], queryFn: listCollections });

  const summarizeMutation = useMutation({ mutationFn: () => summarizePaper(id!) });
  const extractMutation = useMutation({ mutationFn: () => extractPaper(id!) });

  const addNoteMutation = useMutation({
    mutationFn: () => createNote(id!, noteText),
    onSuccess: () => {
      setNoteText("");
      queryClient.invalidateQueries({ queryKey: ["notes", id] });
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: (noteId: string) => deleteNote(noteId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notes", id] }),
  });

  const addToCollectionMutation = useMutation({
    mutationFn: (collectionId: string) => addDocumentToCollection(collectionId, id!),
  });

  if (paperQuery.isLoading) return (
    <div className="flex justify-center items-center h-64">
      <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
    </div>
  );
  if (paperQuery.isError || !paperQuery.data) return (
    <div className="bg-red-50 text-red-600 p-6 rounded-2xl border border-red-100 text-center">Paper not found.</div>
  );
  const paper = paperQuery.data;

  return (
    <div className="max-w-4xl mx-auto space-y-8 animation-fade-in pb-12">
      <div className="bg-white/80 backdrop-blur-md rounded-3xl p-8 shadow-glass border border-white/60 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
        
        <h1 className="text-3xl font-bold text-slate-900 leading-tight mb-4">{paper.title}</h1>
        <p className="text-base text-slate-600 mb-6 font-medium leading-relaxed">{paper.authors.join(", ")}</p>
        
        <div className="flex gap-2 flex-wrap mb-8">
          {paper.categories.map((c) => (
            <span key={c} className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-xs font-semibold shadow-sm border border-indigo-100">
              {c}
            </span>
          ))}
          {paper.published_at && (
            <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-semibold shadow-sm border border-slate-200">
              {new Date(paper.published_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
            </span>
          )}
        </div>
        
        <div className="flex flex-wrap gap-4 mb-8">
          {paper.abs_url && (
            <a href={paper.abs_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors shadow-md hover:shadow-lg">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
              arXiv Abstract
            </a>
          )}
          {paper.pdf_url && (
            <a href={paper.pdf_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors shadow-sm hover:shadow-md">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              View PDF
            </a>
          )}
          <Link to={`/chat?doc=${paper.id}`} className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors shadow-sm hover:shadow-md">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
            Ask Questions
          </Link>
        </div>
        
        <div className="prose prose-slate max-w-none">
          <h3 className="text-lg font-semibold text-slate-800 mb-3">Abstract</h3>
          <p className="text-slate-700 leading-relaxed text-justify">{paper.abstract}</p>
        </div>
      </div>

      <div className="flex flex-col gap-8">
        
        {/* AI Analysis - Dark Theme */}
        <section className="bg-slate-900 rounded-3xl p-8 shadow-xl border border-slate-800 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500"></div>
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            AI Analysis
          </h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => summarizeMutation.mutate()}
              disabled={summarizeMutation.isPending}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3.5 rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 shadow-md flex justify-center items-center"
            >
              {summarizeMutation.isPending ? "Summarizing..." : "Generate Summary"}
            </button>
            <button
              onClick={() => extractMutation.mutate()}
              disabled={extractMutation.isPending}
              className="flex-1 bg-slate-800 hover:bg-slate-700 text-white px-5 py-3.5 rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 shadow-md border border-slate-700 flex justify-center items-center"
            >
              {extractMutation.isPending ? "Extracting..." : "Extract Methodology & Results"}
            </button>
          </div>
          
          <div className="mt-8 space-y-6">
            {summarizeMutation.data && (
              <div className="animation-fade-in">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Summary</h3>
                <AnswerCard answer={summarizeMutation.data} />
              </div>
            )}
            {extractMutation.data && (
              <div className="animation-fade-in">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Extracted Details</h3>
                <AnswerCard answer={extractMutation.data} />
              </div>
            )}
          </div>
        </section>

        {/* Personal Notes */}
        <section className="bg-white/80 backdrop-blur-md rounded-3xl p-8 shadow-sm border border-slate-200/60">
          <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            Personal Notes
          </h2>
          <div className="flex flex-col gap-4 mb-6">
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Add a personal insight, thought, or note..."
              className="w-full border-slate-200 rounded-xl px-5 py-4 text-base focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none bg-white shadow-inner resize-none transition-all"
              rows={3}
            />
            <button
              onClick={() => noteText.trim() && addNoteMutation.mutate()}
              disabled={!noteText.trim() || addNoteMutation.isPending}
              className="self-end bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-colors shadow-md disabled:opacity-50"
            >
              Save Note
            </button>
          </div>
          
          <div className="space-y-4">
            {notesQuery.data?.map((n) => (
              <div key={n.id} className="bg-amber-50/50 border border-amber-100 rounded-2xl p-5 shadow-sm relative group transition-colors hover:bg-amber-50">
                <p className="text-base text-slate-800 pr-8">{n.content}</p>
                <button
                  onClick={() => deleteNoteMutation.mutate(n.id)}
                  className="absolute top-4 right-4 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white rounded-full shadow-sm"
                  title="Delete note"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
                <div className="text-xs text-slate-400 mt-3 font-semibold uppercase tracking-wider">
                  {new Date(n.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
            {notesQuery.data?.length === 0 && (
              <p className="text-base text-slate-500 italic text-center py-6 bg-slate-50 rounded-2xl border border-slate-100">No notes added yet.</p>
            )}
          </div>
        </section>

        {/* Collections */}
        <section className="bg-white/80 backdrop-blur-md rounded-3xl p-8 shadow-sm border border-slate-200/60">
          <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>
            Collections
          </h2>
          <div className="flex gap-3 flex-wrap">
            {collectionsQuery.data?.map((c) => (
              <button
                key={c.id}
                onClick={() => addToCollectionMutation.mutate(c.id)}
                className="text-sm font-semibold border-2 border-slate-200 bg-white rounded-xl px-4 py-2 hover:bg-slate-50 hover:border-indigo-300 hover:text-indigo-700 transition-all shadow-sm"
              >
                + {c.name}
              </button>
            ))}
            {collectionsQuery.data?.length === 0 && (
              <p className="text-base text-slate-500">
                No collections yet. Create one on the{" "}
                <Link to="/collections" className="text-indigo-600 font-semibold hover:underline">
                  Collections page
                </Link>.
              </p>
            )}
          </div>
          {addToCollectionMutation.isSuccess && (
            <div className="mt-4 bg-emerald-50 text-emerald-700 text-sm font-medium px-4 py-3 rounded-xl border border-emerald-200 flex items-center gap-2 animation-fade-in">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              Successfully added to collection!
            </div>
          )}
        </section>

        {/* Related Papers */}
        <section className="bg-white/80 backdrop-blur-md rounded-3xl p-8 shadow-sm border border-slate-200/60">
          <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
            Related Papers
          </h2>
          <div className="space-y-4">
            {relatedQuery.data?.map((r) => (
              <PaperCard 
                key={r.document.id} 
                document={r.document} 
                meta={`Similarity ${(r.score * 100).toFixed(0)}%`} 
              />
            ))}
            {relatedQuery.data?.length === 0 && (
              <p className="text-base text-slate-500 italic text-center py-6 bg-slate-50 rounded-2xl border border-slate-100">No related papers found.</p>
            )}
          </div>
        </section>

      </div>
    </div>
  );
}
