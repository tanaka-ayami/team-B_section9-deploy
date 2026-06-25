// frontend/types/document.ts
export interface Document {
  id: string;
  title: string | null;
  category_id: string | null;
  categoryName: string | null;
  group_id: string;
  image_url: string;
  has_deadline: boolean;
  deadline_date: string | null;
  is_done: boolean;
  created_by: string;
  created_at: string;
}

export interface PatchDocumentRequest {
  title?: string;
  category_id?: string | null;
  has_deadline?: boolean;
  deadline_date?: string | null;
  is_done?: boolean;
}