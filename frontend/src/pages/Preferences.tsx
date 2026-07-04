import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getPreferences, updatePreferences } from "../api/client";

const FORMATS = ["concise", "detailed", "bullet_points"];
const CATEGORIES = ["cs.AI", "cs.CV", "cs.LG", "stat.ML"];
const CATEGORY_NAMES: Record<string, string> = {
  "cs.AI": "Artificial Intelligence",
  "cs.CV": "Computer Vision",
  "cs.LG": "Machine Learning",
  "stat.ML": "Statistical Machine Learning",
};

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      setTimeout(() => saveMutation.reset(), 3000);
    },
  });

  const toggleCategory = (cat: string) => {
    setFavorites((prev) => (prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]));
  };

  return (
    <div className="max-w-2xl mx-auto animation-fade-in pb-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <svg className="w-8 h-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          System Preferences
        </h1>
        <p className="text-slate-500 mt-1">Customize how the AI assistant responds and filters content.</p>
      </div>

      <div className="bg-white/80 backdrop-blur-md rounded-3xl p-8 shadow-sm border border-slate-200/60 space-y-10">
        
        <section>
          <div className="mb-4">
            <h2 className="text-lg font-bold text-slate-800">Preferred Answer Format</h2>
            <p className="text-sm text-slate-500 mt-1">Control the verbosity and structure of AI generated answers.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {FORMATS.map((f) => (
              <button
                key={f}
                onClick={() => setFormat(f)}
                className={`relative overflow-hidden rounded-2xl p-5 text-left transition-all border-2 ${
                  format === f 
                    ? "bg-indigo-50 border-indigo-500 shadow-md shadow-indigo-100" 
                    : "bg-white border-slate-200 hover:border-indigo-300 hover:bg-slate-50"
                }`}
              >
                {format === f && (
                  <div className="absolute top-4 right-4 text-indigo-500">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  </div>
                )}
                <div className={`font-semibold capitalize mb-1 ${format === f ? "text-indigo-900" : "text-slate-700"}`}>
                  {f.replace("_", " ")}
                </div>
                <div className="text-xs text-slate-500">
                  {f === "concise" && "Short and direct answers without extra fluff."}
                  {f === "detailed" && "Comprehensive explanations with deep analysis."}
                  {f === "bullet_points" && "Structured lists for easy scanning."}
                </div>
              </button>
            ))}
          </div>
        </section>

        <section>
          <div className="mb-4">
            <h2 className="text-lg font-bold text-slate-800">Favorite Topics</h2>
            <p className="text-sm text-slate-500 mt-1">Select arXiv categories you are most interested in to personalize recommendations.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all border-2 ${
                  favorites.includes(cat) 
                    ? "bg-indigo-600 border-indigo-600 text-white shadow-md" 
                    : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-indigo-50"
                }`}
              >
                {favorites.includes(cat) ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                ) : (
                  <svg className="w-4 h-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                )}
                {CATEGORY_NAMES[cat] || cat}
              </button>
            ))}
          </div>
        </section>

        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
          <div className="flex-1">
            {saveMutation.isSuccess && (
              <div className="animation-fade-in flex items-center gap-2 text-emerald-600 bg-emerald-50 px-4 py-2 rounded-lg font-medium text-sm border border-emerald-100 inline-flex">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Preferences saved successfully
              </div>
            )}
          </div>
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || saveMutation.isSuccess}
            className="bg-slate-900 hover:bg-indigo-600 text-white px-8 py-3 rounded-xl text-sm font-semibold transition-colors disabled:opacity-50 shadow-md flex items-center gap-2"
          >
            {saveMutation.isPending ? "Saving..." : "Save Preferences"}
          </button>
        </div>
      </div>
    </div>
  );
}
