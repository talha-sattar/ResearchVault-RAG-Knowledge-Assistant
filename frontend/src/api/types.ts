export interface DocumentSummary {
  id: string;
  arxiv_id: string | null;
  title: string;
  primary_category: string | null;
  categories: string[];
  published_at: string | null;
  abs_url: string | null;
}

export interface DocumentOut extends DocumentSummary {
  abstract: string | null;
  pdf_url: string | null;
  authors: string[];
}

export interface Citation {
  doc_index: number;
  chunk_id: string;
  document_id: string;
  arxiv_id: string | null;
  page: number | null;
  marker_text: string;
}

export interface AnswerOut {
  text: string;
  citations: Citation[];
  is_refusal: boolean;
  provider: string;
  model: string;
  latency_ms: number;
}

export interface SearchResultItem {
  document: DocumentSummary;
  snippet: string;
  section_type: string;
  page_start: number | null;
  page_end: number | null;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}

export interface RecommendationItem {
  document: DocumentSummary;
  reason: string;
  score: number;
}

export interface MessageOut {
  id: string;
  role: string;
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: MessageOut;
}

export interface CollectionOut {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  document_count: number;
}

export interface CollectionWithDocuments extends CollectionOut {
  documents: DocumentSummary[];
}

export interface NoteOut {
  id: string;
  document_id: string;
  content: string;
  page_reference: number | null;
  created_at: string;
  updated_at: string;
}

export interface PreferencesOut {
  favorite_categories: string[];
  preferred_answer_format: string;
  default_top_k: number | null;
}

export interface SearchHistoryItem {
  id: string;
  query_text: string;
  search_type: string;
  result_document_ids: string[];
  created_at: string;
}

export interface DocumentViewItem {
  id: string;
  document_id: string;
  view_type: string;
  viewed_at: string;
}
