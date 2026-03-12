/** TypeScript types matching backend Pydantic schemas exactly. */

export interface Car {
  id: number;
  external_id: string;
  make: string;
  model: string;
  year: number;
  price: number;
  color: string | null;
  link: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedCars {
  items: Car[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CarsQueryParams {
  page?: number;
  per_page?: number;
  make?: string;
  model?: string;
  year_min?: number;
  year_max?: number;
  price_min?: number;
  price_max?: number;
  color?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}