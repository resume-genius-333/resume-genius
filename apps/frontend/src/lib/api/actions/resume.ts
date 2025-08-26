"use server";

import { z } from "zod";
import { api } from "../client";
import { Education } from "../schemas/education";
import { Experience } from "../schemas/experience";
import { Project } from "../schemas/project";
import { displayResumeSchema, DisplayResumeOutput } from "../schemas/resume";

export async function getResumeData(
  userId: string,
  jobId: string,
  version?: string
): Promise<DisplayResumeOutput> {
  try {
    const endpoint = version 
      ? `/api/v1/users/${userId}/jobs/${jobId}/resumes/${version}`
      : `/api/v1/users/${userId}/jobs/${jobId}/resume`;
    
    const resume = await api.get(
      endpoint,
      displayResumeSchema
    );
    
    return resume;
  } catch (error) {
    console.error("Failed to fetch resume data:", error);
    throw new Error(
      error instanceof Error 
        ? error.message 
        : "Failed to fetch resume data"
    );
  }
}

export async function getResumeEducation(
  userId: string,
  jobId: string
): Promise<Education.DisplayOutput[]> {
  try {
    const response = await api.get(
      `/api/v1/users/${userId}/jobs/${jobId}/resume/education`,
      z.array(Education.displaySchema)
    );
    
    return response;
  } catch (error) {
    console.error("Failed to fetch education data:", error);
    throw new Error(
      error instanceof Error 
        ? error.message 
        : "Failed to fetch education data"
    );
  }
}

export async function getResumeExperience(
  userId: string,
  jobId: string
): Promise<Experience.DisplayOutput[]> {
  try {
    const response = await api.get(
      `/api/v1/users/${userId}/jobs/${jobId}/resume/experience`,
      z.array(Experience.displaySchema)
    );
    
    return response;
  } catch (error) {
    console.error("Failed to fetch experience data:", error);
    throw new Error(
      error instanceof Error 
        ? error.message 
        : "Failed to fetch experience data"
    );
  }
}

export async function getResumeProjects(
  userId: string,
  jobId: string
): Promise<Project.DisplayOutput[]> {
  try {
    const response = await api.get(
      `/api/v1/users/${userId}/jobs/${jobId}/resume/projects`,
      z.array(Project.displaySchema)
    );
    
    return response;
  } catch (error) {
    console.error("Failed to fetch projects data:", error);
    throw new Error(
      error instanceof Error 
        ? error.message 
        : "Failed to fetch projects data"
    );
  }
}