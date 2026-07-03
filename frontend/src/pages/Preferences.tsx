import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getPreferences, updatePreferences } from "../api/client";

const FORMATS = ["concise", "detailed", "bullet_points"];
const CATEGORIES = ["cs.AI", "cs.CV", "cs.LG", "stat.ML"];

export default function Preferences() {
  const queryClient = useQueryClient();
  const prefsQuery = useQuery({ queryKey: ["preferences"], queryFn: getPreferences });
  const [format, setFormat] = useState("concise");
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    if (prefsQuery.data) {
      setFormat(prefsQuery.data.preferred_answer_format);
      setFavorites(prefsQuery.data.favorite_categories);
    }
  }, [prefsQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () => updatePreferences({ preferred_answer_format: format, favorite_categories: favorites }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["preferences"] }),
  });

  const toggleCategory = (cat: string) => {
    setFavorites((prev) => (prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]));
  };

  return (
    <div className="max-w-md">
      <h1 className="text-xl font-semibold mb-4">Preferences</h1>

      <div className="mb-6">
        <h2 className="text-sm font-medium mb-2">Preferred answer format</h2>
        <div className="flex gap-2">
          {FORMATS.map((f) => (
            <button
              key={f}
              onClick={() => setFormat(f)}
              className={`text-sm px-3 py-1.5 rounded-md border ${
                format === f ? "bg-indigo-600 text-white border-indigo-600" : "hover:bg-slate-50"
              }`}
            >
              {f.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h2 className="text-sm font-medium mb-2">Favorite topics</h2>
        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => toggleCategory(cat)}
              className={`text-sm px-3 py-1.5 rounded-md border ${
                favorites.includes(cat) ? "bg-indigo-600 text-white border-indigo-600" : "hover:bg-slate-50"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={() => saveMutation.mutate()}
        className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium"
      >
        Save preferences
      </button>
      {saveMutation.isSuccess && <p className="text-xs text-emerald-600 mt-2">Saved.</p>}
    </div>
  );
}
