"use client";

import { jobStatusSchema, streamJobStatus } from "@/lib/api/custom";
import { useEffect, useState, use } from "react";
import z from "zod";

interface JobPageInput {
  params: Promise<{ jobId: string }>;
}

export default function JobPage({ params }: JobPageInput) {
  const { jobId } = use(params);
  const [counter, setCounter] = useState(0);
  const [status, setStatus] = useState<z.infer<typeof jobStatusSchema> | null>(
    null
  );

  useEffect(() => {
    let reader: ReadableStreamDefaultReader<z.infer<typeof jobStatusSchema>> | null = null;
    let aborted = false;

    async function connectToJobStatus() {
      try {
        console.log(
          "[connectToJobStatus] Connecting to job status stream for jobId:",
          jobId
        );
        const result = await streamJobStatus(jobId);
        reader = result.getReader();
        let messageCount = 0;

        while (!aborted) {
          const { done, value } = await reader.read();
          if (done) {
            console.log(
              "[connectToJobStatus] Stream closed after",
              messageCount,
              "messages."
            );
            break;
          }
          messageCount++;
          console.log("[connectToJobStatus] Received value:", value);
          setCounter(prev => prev + 1); // Use functional update to avoid stale closure
          setStatus(value);
        }
      } catch (error) {
        console.error("[connectToJobStatus] Error in SSE stream:", error);
      }
    }

    connectToJobStatus();

    // Cleanup function
    return () => {
      aborted = true;
      if (reader) {
        reader.cancel().catch(console.error);
      }
    };
  }, [jobId]); // Only run when jobId changes

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Job Status Page</h1>
      <div className="space-y-2">
        <p>Job ID: {jobId}</p>
        <p>Messages received: {counter}</p>
        <p>Job parsed at: {status?.job_parsed_at || "Not yet parsed"}</p>
      </div>
      <div className="mt-4">
        <p className="text-sm text-gray-600">
          Check the browser console for detailed SSE debugging information
        </p>
      </div>
    </div>
  );
}
