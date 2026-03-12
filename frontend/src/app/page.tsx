"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Database, RefreshCw } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import { getCarsApi } from "@/lib/api";
import { CarsQueryParams } from "@/types";
import Navbar from "@/components/Navbar";
import FilterBar from "@/components/FilterBar";
import CarTable from "@/components/CarTable";
import Pagination from "@/components/Pagination";

const DEFAULT_FILTERS: CarsQueryParams = {
  page: 1,
  per_page: 20,
  sort_by: "created_at",
  sort_order: "desc",
};

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, initialize } = useAuthStore();
  const [filters, setFilters] = useState<CarsQueryParams>(DEFAULT_FILTERS);
  const [ready, setReady] = useState(false);

  // Initialize auth from localStorage
  useEffect(() => {
    initialize();
    setReady(true);
  }, [initialize]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (ready && !isAuthenticated) {
      router.push("/login");
    }
  }, [ready, isAuthenticated, router]);

  // Fetch cars with TanStack Query
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["cars", filters],
    queryFn: () => getCarsApi(filters),
    enabled: ready && isAuthenticated,
  });

  // Handle sort toggle
  const handleSort = (column: string) => {
    setFilters((prev) => ({
      ...prev,
      sort_by: column,
      sort_order: prev.sort_by === column && prev.sort_order === "asc" ? "desc" : "asc",
      page: 1,
    }));
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Handle filter reset
  const handleReset = () => {
    setFilters(DEFAULT_FILTERS);
  };

  // Show nothing while checking auth
  if (!ready || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Car Listings</h2>
            <p className="text-sm text-gray-500 mt-1">
              {data ? (
                <>
                  <span className="font-medium">{data.total}</span> cars from carsensor.net
                </>
              ) : (
                "Loading..."
              )}
            </p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Filters */}
        <FilterBar filters={filters} onFilterChange={setFilters} onReset={handleReset} />

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500">Loading car listings...</p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700 font-medium">Failed to load car listings</p>
            <p className="text-red-500 text-sm mt-1">Please check your connection and try again.</p>
            <button
              onClick={() => refetch()}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Car Table */}
        {data && !isLoading && (
          <>
            <CarTable
              cars={data.items}
              sortBy={filters.sort_by || "created_at"}
              sortOrder={filters.sort_order || "desc"}
              onSort={handleSort}
            />
            <Pagination
              page={data.page}
              pages={data.pages}
              total={data.total}
              perPage={data.per_page}
              onPageChange={handlePageChange}
            />
          </>
        )}

        {/* Footer info */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
            <Database className="w-3 h-3" />
            Data sourced from carsensor.net | Auto-refreshed every 30 minutes
          </p>
        </div>
      </main>
    </div>
  );
}