"use client";

import { Search, X } from "lucide-react";
import { CarsQueryParams } from "@/types";

interface FilterBarProps {
  filters: CarsQueryParams;
  onFilterChange: (filters: CarsQueryParams) => void;
  onReset: () => void;
}

export default function FilterBar({ filters, onFilterChange, onReset }: FilterBarProps) {
  const update = (key: keyof CarsQueryParams, value: string) => {
    const numericKeys = ["year_min", "year_max", "price_min", "price_max"];
    const parsed = numericKeys.includes(key)
      ? value
        ? Number(value)
        : undefined
      : value || undefined;
    onFilterChange({ ...filters, [key]: parsed, page: 1 });
  };

  const hasFilters = filters.make || filters.model || filters.color || filters.year_min || filters.year_max || filters.price_min || filters.price_max;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Search className="w-4 h-4 text-gray-500" />
        <h3 className="text-sm font-semibold text-gray-700">Filter Cars</h3>
        {hasFilters && (
          <button onClick={onReset} className="ml-auto flex items-center gap-1 text-xs text-red-500 hover:text-red-700">
            <X className="w-3 h-3" /> Clear all
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        <input
          type="text"
          placeholder="Make"
          value={filters.make || ""}
          onChange={(e) => update("make", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
        <input
          type="text"
          placeholder="Model"
          value={filters.model || ""}
          onChange={(e) => update("model", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
        <input
          type="number"
          placeholder="Year from"
          value={filters.year_min || ""}
          onChange={(e) => update("year_min", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
        <input
          type="number"
          placeholder="Year to"
          value={filters.year_max || ""}
          onChange={(e) => update("year_max", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
        <input
          type="number"
          placeholder="Price min (¥)"
          value={filters.price_min || ""}
          onChange={(e) => update("price_min", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
        <input
          type="number"
          placeholder="Price max (¥)"
          value={filters.price_max || ""}
          onChange={(e) => update("price_max", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
        <input
          type="text"
          placeholder="Color"
          value={filters.color || ""}
          onChange={(e) => update("color", e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800"
        />
      </div>
    </div>
  );
}