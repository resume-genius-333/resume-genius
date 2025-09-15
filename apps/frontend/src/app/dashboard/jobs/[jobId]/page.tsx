"use client";

import {
  EducationSelectionResult,
  ProcessingStatusOutput,
  streamProcessingStatus,
} from "@/lib/api/custom";
import {
  getEducationApiV1ResumesEducationsEducationIdGet,
  getJobApiV1JobsJobIdGet,
  getSelectedEducationsApiV1JobsJobIdSelectedEducationsGet,
} from "@/lib/api/generated/api";
import { JobSchema } from "@/lib/api/generated/schemas";
import { useEffect, useState, use, useCallback, useRef } from "react";
import rehypeStringify from "rehype-stringify";
import remarkFrontmatter from "remark-frontmatter";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";
import "@/markdown.css";
import z from "zod";

interface JobPageInput {
  params: Promise<{ jobId: string }>;
}

export default function JobPage({ params }: JobPageInput) {
  const { jobId } = use(params);
  const [status, _setStatus] = useState<ProcessingStatusOutput>({
    jobParsedAt: null,
    educationsSelectedAt: null,
    workExperiencesSelectedAt: null,
    projectsSelectedAt: null,
    skillsSelectedAt: null,
  });
  const statusRef = useRef<ProcessingStatusOutput>(status);
  const [reader, setReader] =
    useState<ReadableStreamDefaultReader<ProcessingStatusOutput> | null>(null);
  const [job, setJob] = useState<JobSchema | null>(null);
  const [jobDescription, setJobDescription] = useState<string | null>(null);
  const [educationSelected, setEducationSelected] =
    useState<EducationSelectionResult | null>(null);

  const setStatus = useCallback((status: ProcessingStatusOutput) => {
    _setStatus(status);
    statusRef.current = status;
    console.log("status set: ", status);
  }, []);

  const checkAndUpdateStatusFor = useCallback(
    (
      key: keyof ProcessingStatusOutput,
      newData: ProcessingStatusOutput
    ): boolean => {
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

  const fetchEducation = useCallback(async () => {
    const education =
      await getSelectedEducationsApiV1JobsJobIdSelectedEducationsGet(jobId);
    setEducationSelected(education);
  }, [jobId]);

  const updateStatus = useCallback(
    async (newStatus: ProcessingStatusOutput) => {
      const promises: Promise<unknown>[] = [];
      if (checkAndUpdateStatusFor("jobParsedAt", newStatus)) {
        promises.push(fetchJob());
      }
      if (checkAndUpdateStatusFor("educationsSelectedAt", newStatus)) {
        promises.push(fetchEducation());
      }
      await Promise.all(promises);
    },
    [checkAndUpdateStatusFor, fetchJob, fetchEducation]
  );

  async function createReader(jobId: string) {
    const result = await streamProcessingStatus(jobId);
    const reader = result.getReader();
    setReader(reader);
  }

  const read = useCallback(
    async (reader: ReadableStreamDefaultReader<ProcessingStatusOutput>) => {
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
      <div className="mt-4">
        <h3>Selected Educations</h3>
        {educationSelected &&
          educationSelected.selected_items.map((item) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
        <h3>Not Selected Educations</h3>
        {educationSelected &&
          educationSelected.not_selected_items.map((item) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
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
