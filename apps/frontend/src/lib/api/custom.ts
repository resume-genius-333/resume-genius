import z from "zod";
import { customAxiosInstance } from "./client";

export const jobStatusSchema = z
  .object({
    job_parsed_at: z.iso.datetime().nullish(),
  })
  .transform((data) => {
    return {
      jobParsedAt: data.job_parsed_at ? new Date(data.job_parsed_at) : null,
    };
  });

export type JobStatusInput = z.input<typeof jobStatusSchema>;
export type JobStatusOutput = z.output<typeof jobStatusSchema>;

/**
 * Stream job processing status via Server-Sent Events.
 * @summary Stream Status
 */
export const streamJobStatus = async (jobId: string) => {
  return await customAxiosInstance<typeof jobStatusSchema>({
    url: `/api/v1/jobs/${jobId}/status-stream`,
    method: "GET",
    responseType: "sse-stream",
    responseSchema: jobStatusSchema,
  });
};
