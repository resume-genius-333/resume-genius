import * as z from "zod";

export namespace Experience {
  export const displaySchema = z
    .object({
      company_name: z.string(),
      location: z.string().nullish(),
      job_title: z.string(),
      start_date: z.string(),
      end_date: z.string().nullish(),
      description: z.string().nullish(),
      key_points: z.string().array(),
    })
    .transform((data) => ({
      companyName: data.company_name,
      location: data.location,
      jobTitle: data.job_title,
      startDate: data.start_date,
      endDate: data.end_date,
      description: data.description,
      keyPoints: data.key_points,
    }));

  export type DisplayInput = z.input<typeof displaySchema>;

  export type DisplayOutput = z.output<typeof displaySchema>;
}
