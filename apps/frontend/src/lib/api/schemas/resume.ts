import z from "zod";
import { Experience } from "./experience";
import { Education } from "./education";
import { Project } from "./project";

export const displayResumeSchema = z
  .object({
    id: z.string(),
    user_id: z.string(),
    job_id: z.string(),
    full_name: z.string(),
    email: z.string(),
    phone: z.string().nullish(),
    location: z.string().nullish(),
    summary: z.string().nullish(),
    education: z.array(Education.displaySchema),
    experience: z.array(Experience.displaySchema),
    projects: z.array(Project.displaySchema),
    skills: z.array(z.string()),
    created_at: z.string(),
    updated_at: z.string(),
  })
  .transform((data) => ({
    id: data.id,
    userId: data.user_id,
    jobId: data.job_id,
    fullName: data.full_name,
    email: data.email,
    phone: data.phone,
    location: data.location,
    summary: data.summary,
    education: data.education,
    experience: data.experience,
    projects: data.projects,
    skills: data.skills,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }));

export type DisplayResumeInput = z.input<typeof displayResumeSchema>;

export type DisplayResumeOutput = z.output<typeof displayResumeSchema>;

