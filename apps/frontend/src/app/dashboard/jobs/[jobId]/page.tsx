"use client";

import { JobStatusOutput, streamJobStatus } from "@/lib/api/custom";
import { getJobApiV1JobsJobIdGet } from "@/lib/api/generated/api";
import { JobSchema } from "@/lib/api/generated/schemas";
import { useEffect, useState, use, useCallback, useRef } from "react";
import rehypeStringify from "rehype-stringify";
import remarkFrontmatter from "remark-frontmatter";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";
import "@/markdown.css";

interface JobPageInput {
  params: Promise<{ jobId: string }>;
}

export default function JobPage({ params }: JobPageInput) {
  const { jobId } = use(params);
  const [status, _setStatus] = useState<JobStatusOutput>({ jobParsedAt: null });
  const statusRef = useRef<JobStatusOutput>(status);
  const [reader, setReader] =
    useState<ReadableStreamDefaultReader<JobStatusOutput> | null>(null);
  const [job, setJob] = useState<JobSchema | null>(null);
  const [jobDescription, setJobDescription] = useState<string | null>(null);

  const setStatus = useCallback((status: JobStatusOutput) => {
    _setStatus(status);
    statusRef.current = status;
    console.log("status set: ", status);
  }, []);

  const checkAndUpdateStatusFor = useCallback(
    (key: keyof JobStatusOutput, newData: JobStatusOutput): boolean => {
      const currVal = statusRef.current[key];
      const newVal = newData[key];
      if (!newVal) return false;
      if (!currVal) {
        setStatus({
          ...statusRef.current,
          [key]: newVal,
        });
        return true;
      }
      if (newVal <= currVal) return false;
      setStatus({
        ...statusRef.current,
        [key]: newVal,
      });
      return true;
    },
    [setStatus]
  );

  const parseJobDescriptionToHtml = useCallback(async (description: string) => {
    const result = await unified()
      .use(remarkParse)
      .use(remarkFrontmatter)
      .use(remarkGfm)
      .use(remarkRehype)
      .use(rehypeStringify)
      .process(description);
    setJobDescription(String(result));
  }, []);

  const fetchJob = useCallback(async () => {
    const job = await getJobApiV1JobsJobIdGet(jobId);
    setJob(job);
    await parseJobDescriptionToHtml(job.job_description);
  }, [jobId, parseJobDescriptionToHtml]);

  const updateStatus = useCallback(
    async (newStatus: JobStatusOutput) => {
      const promises: Promise<unknown>[] = [];
      if (checkAndUpdateStatusFor("jobParsedAt", newStatus)) {
        console.log("TODO: Implement fetching job");
        promises.push(fetchJob());
      }
      await Promise.all(promises);
    },
    [checkAndUpdateStatusFor, fetchJob]
  );

  async function createReader(jobId: string) {
    const result = await streamJobStatus(jobId);
    const reader = result.getReader();
    setReader(reader);
  }

  const read = useCallback(
    async (reader: ReadableStreamDefaultReader<JobStatusOutput>) => {
      while (true) {
        const { done, value } = await reader.read();
        if (value) {
          updateStatus(value);
        }
        if (done) {
          console.log("Finished receiving updates");
          break;
        }
      }
    },
    [updateStatus]
  );

  useEffect(() => {
    if (reader) {
      read(reader);
    }
  }, [reader, read]);

  useEffect(() => {
    createReader(jobId);
    return () => {};
  }, [jobId]);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Job Status Page</h1>
      <div className="space-y-2">
        <p>Job ID: {jobId}</p>
        <p>
          Job parsed at:{" "}
          {status.jobParsedAt?.toLocaleString() || "Not yet parsed"}
        </p>
      </div>
      <div className="mt-4">
        <p className="text-sm text-gray-600">
          Check the browser console for detailed SSE debugging information
        </p>
      </div>
      <div>
        <p>Job Title: {job ? job.position_title : "Not loaded"}</p>
        {jobDescription && (
          <div
            className={`markdown-body`}
            dangerouslySetInnerHTML={{ __html: jobDescription }}
          />
        )}
      </div>
    </div>
  );
}
