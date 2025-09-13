import z from "zod";
import { customAxiosInstance } from "./orval-axios";

export const jobStatusSchema = z.object({
  job_updated_at: z.iso.datetime().nullish(),
});

/**
 * Stream job processing status via Server-Sent Events.
 * @summary Stream Status
 */
export const streamJobStatus = async (jobId: string) => {
  const result = await customAxiosInstance<typeof jobStatusSchema>({
    url: `/api/v1/jobs/${jobId}/status-stream`,
    method: "GET",
    responseType: "sse-stream",
    responseSchema: jobStatusSchema,
  });
  return result;
};
