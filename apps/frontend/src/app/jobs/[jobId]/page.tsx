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

  async function connectToJobStatus() {
    const result = await streamJobStatus(jobId);
    const reader = result.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      console.log(value);
      setCounter(counter + 1);
      setStatus(value);
    }
  }

  useEffect(() => {
    connectToJobStatus();
  });

  return (
    <div>
      JobPage {counter}: {status?.job_updated_at}
    </div>
  );
}
