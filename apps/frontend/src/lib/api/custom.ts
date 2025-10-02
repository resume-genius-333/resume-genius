import z from "zod";
import { customAxiosInstance } from "./client";
import {
  getJobSelectedEducationsApiV1JobsJobIdSelectedEducationsGetResponse,
  getStatusApiV1JobsJobIdStatusGetResponse,
} from "./generated/api.zod";

export const processingStatusSchema =
  getStatusApiV1JobsJobIdStatusGetResponse.transform((data) => {
    return {
      jobParsedAt: data.job_parsed_at ? new Date(data.job_parsed_at) : null,
      educationsSelectedAt: data.educations_selected_at
        ? new Date(data.educations_selected_at)
        : null,
      workExperiencesSelectedAt: data.work_experiences_selected_at
        ? new Date(data.work_experiences_selected_at)
        : null,
      projectsSelectedAt: data.projects_selected_at
        ? new Date(data.projects_selected_at)
        : null,
      skillsSelectedAt: data.skills_selected_at
        ? new Date(data.skills_selected_at)
        : null,
    };
  });

export type ProcessingStatusInput = z.input<typeof processingStatusSchema>;
export type ProcessingStatusOutput = z.output<typeof processingStatusSchema>;

/**
 * Stream job processing status via Server-Sent Events.
 * @summary Stream Status
 */
export const streamProcessingStatus = async (jobId: string) => {
  return await customAxiosInstance<typeof processingStatusSchema>({
    url: `/api/v1/jobs/${jobId}/status-stream`,
    method: "GET",
    responseType: "sse-stream",
    responseSchema: processingStatusSchema,
  });
};

export const resumeSelectionSchema =
  getJobSelectedEducationsApiV1JobsJobIdSelectedEducationsGetResponse;

export type ResumeSelectionResult = z.infer<typeof resumeSelectionSchema>;
export type ResumeSelectedItem = ResumeSelectionResult["selected_items"][0];
export type ResumeNotSelectedItem =
  ResumeSelectionResult["not_selected_items"][0];
