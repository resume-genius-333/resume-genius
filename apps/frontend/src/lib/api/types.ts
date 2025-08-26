export type { Education } from "./schemas/education";
export type { Experience } from "./schemas/experience";
export type { Project } from "./schemas/project";

import type { Education } from "./schemas/education";
import type { Experience } from "./schemas/experience";
import type { Project } from "./schemas/project";

export interface Resume {
  id: string;
  userId: string;
  jobId: string;
  fullName: string;
  email: string;
  phone?: string | null;
  location?: string | null;
  summary?: string | null;
  education: Education.DisplayOutput[];
  experience: Experience.DisplayOutput[];
  projects: Project.DisplayOutput[];
  skills: string[];
  createdAt: string;
  updatedAt: string;
}