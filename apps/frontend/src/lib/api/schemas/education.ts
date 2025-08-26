import * as z from "zod";

export namespace Education {
  export const displaySchema = z
    .object({
      school_name: z.string(),
      city: z.string().nullish(),
      country: z.string().nullish(),
      degree: z.string(),
      start_date: z.string(),
      end_date: z.string(),
      points: z.string().array(),
    })
    .transform((data) => ({
      schoolName: data.school_name,
      city: data.city,
      country: data.country,
      degree: data.degree,
      startDate: data.start_date,
      endDate: data.end_date,
      points: data.points,
    }));

  export type DisplayInput = z.input<typeof displaySchema>;

  export type DisplayOutput = z.output<typeof displaySchema>;
}
