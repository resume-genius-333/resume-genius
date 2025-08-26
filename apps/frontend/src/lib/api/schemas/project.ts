import * as z from "zod";

export namespace Project {
  export const displaySchema = z
    .object({
      project_name: z.string(),
      location: z.string().nullish(),
      role: z.string(),
      start_date: z.string(),
      end_date: z.string().nullish(),
      description: z.string().nullish(),
      key_points: z.string().array(),
    })
    .transform((data) => ({
      projectName: data.project_name,
      location: data.location,
      role: data.role,
      startDate: data.start_date,
      endDate: data.end_date,
      description: data.description,
      keyPoints: data.key_points,
    }));

  export type DisplayInput = z.input<typeof displaySchema>;

  export type DisplayOutput = z.output<typeof displaySchema>;
}