"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  perPage: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, pages, total, perPage, onPageChange }: PaginationProps) {
  if (pages <= 1) return null;

  const from = (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);

  // Generate page numbers to show
  const getVisiblePages = (): (number | string)[] => {
    if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);

    const visible: (number | string)[] = [];
    if (page <= 3) {
      visible.push(1, 2, 3, 4, "...", pages);
    } else if (page >= pages - 2) {
      visible.push(1, "...", pages - 3, pages - 2, pages - 1, pages);
    } else {
      visible.push(1, "...", page - 1, page, page + 1, "...", pages);
    }
    return visible;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-4">
      <p className="text-sm text-gray-600">
        Showing <span className="font-medium">{from}</span> to <span className="font-medium">{to}</span> of{" "}
        <span className="font-medium">{total}</span> results
      </p>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="p-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {getVisiblePages().map((p, i) =>
          typeof p === "string" ? (
            <span key={`ellipsis-${i}`} className="px-2 text-gray-400">
              ...
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`min-w-[36px] h-9 rounded-lg text-sm font-medium transition ${
                p === page
                  ? "bg-blue-600 text-white"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-100"
              }`}
            >
              {p}
            </button>
          )
        )}

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          className="p-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}