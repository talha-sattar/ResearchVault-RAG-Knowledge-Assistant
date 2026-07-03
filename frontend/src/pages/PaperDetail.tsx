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

  if (paperQuery.isLoading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (paperQuery.isError || !paperQuery.data) return <p className="text-sm text-red-600">Paper not found.</p>;
  const paper = paperQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{paper.title}</h1>
        <p className="text-sm text-slate-500 mt-1">{paper.authors.join(", ")}</p>
        <div className="text-xs text-slate-400 mt-1 flex gap-2 flex-wrap">
          {paper.categories.map((c) => (
            <span key={c} className="bg-slate-100 px-1.5 py-0.5 rounded">
              {c}
            </span>
          ))}
          {paper.published_at && <span>{paper.published_at.slice(0, 10)}</span>}
        </div>
        <div className="mt-2 flex gap-3 text-sm">
          {paper.abs_url && (
            <a href={paper.abs_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
              arXiv abstract
            </a>
          )}
          {paper.pdf_url && (
            <a href={paper.pdf_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
              PDF
            </a>
          )}
          <Link to={`/chat?doc=${paper.id}`} className="text-indigo-600 hover:underline">
            Ask questions about this paper
          </Link>
        </div>
        <p className="text-sm text-slate-700 mt-3">{paper.abstract}</p>
      </div>

      <section className="flex gap-3">
        <button
          onClick={() => summarizeMutation.mutate()}
          disabled={summarizeMutation.isPending}
          className="bg-indigo-600 text-white px-3 py-1.5 rounded-md text-sm disabled:opacity-50"
        >
          {summarizeMutation.isPending ? "Summarizing..." : "Summarize"}
        </button>
        <button
          onClick={() => extractMutation.mutate()}
          disabled={extractMutation.isPending}
          className="bg-slate-700 text-white px-3 py-1.5 rounded-md text-sm disabled:opacity-50"
        >
          {extractMutation.isPending ? "Extracting..." : "Extract methodology/datasets/results"}
        </button>
      </section>

      {summarizeMutation.data && (
        <div>
          <h2 className="text-sm font-semibold mb-2">Summary</h2>
          <AnswerCard answer={summarizeMutation.data} />
        </div>
      )}
      {extractMutation.data && (
        <div>
          <h2 className="text-sm font-semibold mb-2">Extracted details</h2>
          <AnswerCard answer={extractMutation.data} />
        </div>
      )}

      <section>
        <h2 className="text-sm font-semibold mb-2">Add to collection</h2>
        <div className="flex gap-2 flex-wrap">
          {collectionsQuery.data?.map((c) => (
            <button
              key={c.id}
              onClick={() => addToCollectionMutation.mutate(c.id)}
              className="text-xs border rounded px-2 py-1 hover:bg-slate-50"
            >
              + {c.name}
            </button>
          ))}
          {collectionsQuery.data?.length === 0 && (
            <p className="text-xs text-slate-400">
              No collections yet - create one on the{" "}
              <Link to="/collections" className="text-indigo-600 hover:underline">
                Collections page
              </Link>
              .
            </p>
          )}
        </div>
        {addToCollectionMutation.isSuccess && <p className="text-xs text-emerald-600 mt-1">Added.</p>}
      </section>

      <section>
        <h2 className="text-sm font-semibold mb-2">Notes</h2>
        <div className="flex gap-2 mb-3">
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add a personal note..."
            className="flex-1 border rounded-md px-2 py-1.5 text-sm"
            rows={2}
          />
          <button
            onClick={() => noteText.trim() && addNoteMutation.mutate()}
            className="bg-indigo-600 text-white px-3 py-1.5 rounded-md text-sm h-fit"
          >
            Save
          </button>
        </div>
        <div className="space-y-2">
          {notesQuery.data?.map((n) => (
            <div key={n.id} className="bg-white border rounded-md p-2 text-sm flex justify-between items-start">
              <span>{n.content}</span>
              <button
                onClick={() => deleteNoteMutation.mutate(n.id)}
                className="text-xs text-slate-400 hover:text-red-600 ml-2"
              >
                delete
              </button>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold mb-2">Related papers</h2>
        <div className="space-y-2">
          {relatedQuery.data?.map((r) => (
            <PaperCard key={r.document.id} document={r.document} meta={`similarity ${r.score.toFixed(2)}`} />
          ))}
        </div>
      </section>
    </div>
  );
}
