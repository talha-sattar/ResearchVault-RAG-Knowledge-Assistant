import axios from "axios";
import type {
  AnswerOut,
  ChatResponse,
  CollectionOut,
  CollectionWithDocuments,
  DocumentOut,
  DocumentSummary,
  DocumentViewItem,
  NoteOut,
  PreferencesOut,
  RecommendationItem,
  SearchHistoryItem,
  SearchResponse,
} from "./types";

const api = axios.create({ baseURL: "/api" });

export const searchPapers = (query: string, top_k = 10, category?: string) =>
  api.post<SearchResponse>("/search", { query, top_k, category }).then((r) => r.data);

export const listPapers = (params: { category?: string; limit?: number; offset?: number } = {}) =>
  api.get<DocumentSummary[]>("/papers", { params }).then((r) => r.data);

export const getPaper = (id: string) => api.get<DocumentOut>(`/papers/${id}`).then((r) => r.data);

export const summarizePaper = (id: string, answer_format = "concise") =>
  api.post<AnswerOut>(`/papers/${id}/summarize`, null, { params: { answer_format } }).then((r) => r.data);

export const extractPaper = (id: string) => api.post<AnswerOut>(`/papers/${id}/extract`).then((r) => r.data);

export const relatedPapers = (id: string, top_k = 5) =>
  api.get<RecommendationItem[]>(`/papers/${id}/related`, { params: { top_k } }).then((r) => r.data);

export const askChat = (question: string, document_ids?: string[], conversation_id?: string) =>
  api.post<ChatResponse>("/chat", { question, document_ids, conversation_id }).then((r) => r.data);

export const comparePapers = (document_ids: string[], aspect?: string) =>
  api.post<{ answer: AnswerOut }>("/compare", { document_ids, aspect }).then((r) => r.data.answer);

export const listCollections = () => api.get<CollectionOut[]>("/collections").then((r) => r.data);

export const createCollection = (name: string, description?: string) =>
  api.post<CollectionOut>("/collections", { name, description }).then((r) => r.data);

export const getCollection = (id: string) =>
  api.get<CollectionWithDocuments>(`/collections/${id}`).then((r) => r.data);

export const addDocumentToCollection = (collectionId: string, documentId: string) =>
  api.post(`/collections/${collectionId}/documents`, { document_id: documentId });

export const removeDocumentFromCollection = (collectionId: string, documentId: string) =>
  api.delete(`/collections/${collectionId}/documents/${documentId}`);

export const deleteCollection = (id: string) => api.delete(`/collections/${id}`);

export const listNotes = (documentId: string) =>
  api.get<NoteOut[]>(`/notes/document/${documentId}`).then((r) => r.data);

export const createNote = (documentId: string, content: string, page_reference?: number) =>
  api.post<NoteOut>("/notes", { document_id: documentId, content, page_reference }).then((r) => r.data);

export const updateNote = (id: string, content: string, page_reference?: number) =>
  api.put<NoteOut>(`/notes/${id}`, { content, page_reference }).then((r) => r.data);

export const deleteNote = (id: string) => api.delete(`/notes/${id}`);

export const getPreferences = () => api.get<PreferencesOut>("/preferences").then((r) => r.data);

export const updatePreferences = (body: Partial<PreferencesOut>) =>
  api.put<PreferencesOut>("/preferences", body).then((r) => r.data);

export const getSearchHistory = () => api.get<SearchHistoryItem[]>("/history/search").then((r) => r.data);

export const getViewHistory = () => api.get<DocumentViewItem[]>("/history/views").then((r) => r.data);

export default api;
