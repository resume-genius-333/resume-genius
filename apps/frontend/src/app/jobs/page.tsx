"use client";

import { listJobsApiV1JobsGet } from "@/lib/api/generated/api";
import { PaginatedResponseJobSchema } from "@/lib/api/generated/schemas";
import { useEffect, useState } from "react";
import { JobsDataTable } from "./jobs-data-table";
import { Button } from "@/components/ui/button";
import { Plus, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";

export default function JobsPage() {
  const [paginatedData, setPaginatedData] =
    useState<PaginatedResponseJobSchema | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const router = useRouter();

  const fetchJobs = async (page: number, size: number) => {
    setIsLoading(true);
    try {
      const response = await listJobsApiV1JobsGet({ page_size: size, page });
      setPaginatedData(response);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs(currentPage, pageSize);
  }, [currentPage, pageSize]);

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-200px)] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs Dashboard</h1>
          <p className="text-muted-foreground">
            View and manage all your job opportunities in one place
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => fetchJobs(currentPage, pageSize)}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => router.push("/jobs/new")} className="gap-2">
            <Plus className="h-4 w-4" />
            Add New Job
          </Button>
        </div>
      </div>

      <JobsDataTable
        data={paginatedData?.items || []}
        totalItems={paginatedData?.total || 0}
        currentPage={currentPage}
        pageSize={pageSize}
        totalPages={paginatedData?.total_pages || 0}
        onPageChange={setCurrentPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setCurrentPage(0); // Reset to first page when changing page size
        }}
        isLoading={isLoading}
      />
    </div>
  );
}
