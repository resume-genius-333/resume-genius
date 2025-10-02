"use client";

import {
  ResumeSelectionResult,
  ProcessingStatusOutput,
  streamProcessingStatus,
} from "@/lib/api/custom";
import {
  getJobApiV1JobsJobIdGet,
  getJobSelectedEducationsApiV1JobsJobIdSelectedEducationsGet,
  getJobSelectedProjectsApiV1JobsJobIdSelectedProjectsGet,
  getJobSelectedSkillsApiV1JobsJobIdSelectedSkillsGet,
  getJobSelectedWorkExperiencesApiV1JobsJobIdSelectedWorkExperiencesGet,
} from "@/lib/api/generated/api";
import {
  JobSchema,
  NotSelectedItem,
  SelectedItem,
} from "@/lib/api/generated/schemas";
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
    useState<ResumeSelectionResult | null>(null);
  const [workExperienceSelected, setWorkExperienceSelected] =
    useState<ResumeSelectionResult | null>(null);
  const [projectSelected, setProjectSelected] =
    useState<ResumeSelectionResult | null>(null);
  const [skillSelected, setSkillSelected] =
    useState<ResumeSelectionResult | null>(null);

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
      await getJobSelectedEducationsApiV1JobsJobIdSelectedEducationsGet(jobId);
    setEducationSelected(education);
  }, [jobId]);

  const fetchWorkExperience = useCallback(async () => {
    const workExperience =
      await getJobSelectedWorkExperiencesApiV1JobsJobIdSelectedWorkExperiencesGet(
        jobId
      );
    setWorkExperienceSelected(workExperience);
  }, [jobId]);

  const fetchProject = useCallback(async () => {
    const project =
      await getJobSelectedProjectsApiV1JobsJobIdSelectedProjectsGet(jobId);
    setProjectSelected(project);
  }, [jobId]);

  const fetchSkill = useCallback(async () => {
    const skill =
      await getJobSelectedSkillsApiV1JobsJobIdSelectedSkillsGet(jobId);
    setSkillSelected(skill);
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
      if (checkAndUpdateStatusFor("workExperiencesSelectedAt", newStatus)) {
        promises.push(fetchWorkExperience());
      }
      if (checkAndUpdateStatusFor("projectsSelectedAt", newStatus)) {
        promises.push(fetchProject());
      }
      if (checkAndUpdateStatusFor("skillsSelectedAt", newStatus)) {
        promises.push(fetchSkill());
      }
      await Promise.all(promises);
    },
    [
      checkAndUpdateStatusFor,
      fetchJob,
      fetchEducation,
      fetchWorkExperience,
      fetchProject,
      fetchSkill,
    ]
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
          educationSelected.selected_items.map((item: SelectedItem) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
        <h3>Not Selected Educations</h3>
        {educationSelected &&
          educationSelected.not_selected_items.map((item: NotSelectedItem) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
      </div>
      <div className="mt-4">
        <h3>Selected Work Experiences</h3>
        {workExperienceSelected &&
          workExperienceSelected.selected_items.map((item: SelectedItem) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
        <h3>Not Selected Work Experiences</h3>
        {workExperienceSelected &&
          workExperienceSelected.not_selected_items.map(
            (item: NotSelectedItem) => (
              <li key={item.id}>
                {item.id}: {item.justification}
              </li>
            )
          )}
      </div>
      <div className="mt-4">
        <h3>Selected Projects</h3>
        {projectSelected &&
          projectSelected.selected_items.map((item: SelectedItem) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
        <h3>Not Selected Projects</h3>
        {projectSelected &&
          projectSelected.not_selected_items.map((item: NotSelectedItem) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
      </div>
      <div className="mt-4">
        <h3>Selected Skills</h3>
        {skillSelected &&
          skillSelected.selected_items.map((item: SelectedItem) => (
            <li key={item.id}>
              {item.id}: {item.justification}
            </li>
          ))}
        <h3>Not Selected Skills</h3>
        {skillSelected &&
          skillSelected.not_selected_items.map((item: NotSelectedItem) => (
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
