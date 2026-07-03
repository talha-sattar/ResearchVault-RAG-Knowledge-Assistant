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
      setActiveId(null);
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });

  const removeDocMutation = useMutation({
    mutationFn: (documentId: string) => removeDocumentFromCollection(activeId!, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["collection", activeId] }),
  });

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Collections</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) createMutation.mutate();
        }}
        className="flex gap-2 mb-6"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New collection name"
          className="border rounded-md px-3 py-2 text-sm w-64"
        />
        <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium">
          Create
        </button>
      </form>

      <div className="grid grid-cols-[240px_1fr] gap-6">
        <div className="space-y-1">
          {collectionsQuery.data?.map((c) => (
            <div key={c.id} className="flex items-center gap-1">
              <button
                onClick={() => setActiveId(c.id)}
                className={`flex-1 text-left px-3 py-2 rounded-md text-sm ${
                  activeId === c.id ? "bg-indigo-100 text-indigo-700" : "hover:bg-slate-100"
                }`}
              >
                {c.name} <span className="text-xs text-slate-400">({c.document_count})</span>
              </button>
              <button
                onClick={() => deleteMutation.mutate(c.id)}
                className="text-xs text-slate-300 hover:text-red-600 px-1"
              >
                x
              </button>
            </div>
          ))}
          {collectionsQuery.data?.length === 0 && <p className="text-sm text-slate-400">No collections yet.</p>}
        </div>

        <div>
          {activeQuery.data ? (
            <div className="space-y-3">
              <h2 className="font-medium">{activeQuery.data.name}</h2>
              {activeQuery.data.documents.map((d) => (
                <div key={d.id} className="flex items-start gap-2">
                  <div className="flex-1">
                    <PaperCard document={d} />
                  </div>
                  <button
                    onClick={() => removeDocMutation.mutate(d.id)}
                    className="text-xs text-slate-400 hover:text-red-600 mt-2"
                  >
                    remove
                  </button>
                </div>
              ))}
              {activeQuery.data.documents.length === 0 && (
                <p className="text-sm text-slate-400">
                  No papers yet - add some from a paper's detail page.
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Select a collection to view its papers.</p>
          )}
        </div>
      </div>
    </div>
  );
}
