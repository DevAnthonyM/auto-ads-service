"use client";

import { ExternalLink, ArrowUp, ArrowDown } from "lucide-react";
import { Car, CarsQueryParams } from "@/types";

interface CarTableProps {
  cars: Car[];
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSort: (column: string) => void;
}

/** Format price in JPY with comma separators. */
function formatPrice(price: number): string {
  return `¥${price.toLocaleString("ja-JP", { maximumFractionDigits: 0 })}`;
}

/** Sortable column header. */
function SortHeader({
  label,
  column,
  currentSort,
  currentOrder,
  onSort,
}: {
  label: string;
  column: string;
  currentSort: string;
  currentOrder: string;
  onSort: (col: string) => void;
}) {
  const isActive = currentSort === column;
  return (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-blue-600 select-none"
      onClick={() => onSort(column)}
    >
      <div className="flex items-center gap-1">
        {label}
        {isActive &&
          (currentOrder === "asc" ? (
            <ArrowUp className="w-3 h-3 text-blue-600" />
          ) : (
            <ArrowDown className="w-3 h-3 text-blue-600" />
          ))}
      </div>
    </th>
  );
}

export default function CarTable({ cars, sortBy, sortOrder, onSort }: CarTableProps) {
  if (cars.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <p className="text-gray-500 text-lg">No cars found</p>
        <p className="text-gray-400 text-sm mt-1">Try adjusting your filters or wait for the scraper to collect data.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <SortHeader label="Make" column="make" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Model</th>
              <SortHeader label="Year" column="year" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <SortHeader label="Price" column="price" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <SortHeader label="Color" column="color" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Link</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {cars.map((car) => (
              <tr key={car.id} className="hover:bg-blue-50/50 transition-colors">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{car.make}</td>
                <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate" title={car.model}>
                  {car.model}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{car.year}</td>
                <td className="px-4 py-3 text-sm font-medium text-green-700">{formatPrice(car.price)}</td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {car.color ? (
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        className="w-3 h-3 rounded-full border border-gray-300"
                        style={{
                          backgroundColor:
                            car.color.toLowerCase() === "white"
                              ? "#f5f5f5"
                              : car.color.toLowerCase() === "pearl white"
                              ? "#fafafa"
                              : car.color.toLowerCase(),
                        }}
                      />
                      {car.color}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm">
                  <a
                    href={car.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 transition"
                  >
                    View <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}