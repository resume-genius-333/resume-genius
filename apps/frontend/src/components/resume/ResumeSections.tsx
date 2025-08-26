import React from 'react';
import type { Education, Experience, Project } from '@/lib/api/schemas';

interface HeaderProps {
  fullName: string;
  email: string;
  phone?: string | null;
  location?: string | null;
}

export function ResumeHeader({ fullName, email, phone, location }: HeaderProps) {
  return (
    <header className="resume-section border-b-2 border-gray-800 pb-4">
      <h1 className="text-3xl font-bold text-gray-900">{fullName}</h1>
      <div className="mt-2 text-sm text-gray-600 flex flex-wrap gap-4">
        <span>{email}</span>
        {phone && <span>{phone}</span>}
        {location && <span>{location}</span>}
      </div>
    </header>
  );
}

interface SummaryProps {
  summary: string;
}

export function ResumeSummary({ summary }: SummaryProps) {
  return (
    <section className="resume-section avoid-break">
      <h2 className="text-xl font-bold text-gray-800 mb-2">Professional Summary</h2>
      <p className="text-gray-700 leading-relaxed">{summary}</p>
    </section>
  );
}

interface ExperienceProps {
  items: Experience.DisplayOutput[];
  isPartial?: boolean;
}

export function ResumeExperience({ items, isPartial = false }: ExperienceProps) {
  if (items.length === 0) return null;
  
  return (
    <section className="resume-section">
      {!isPartial && (
        <h2 className="text-xl font-bold text-gray-800 mb-3">Experience</h2>
      )}
      {isPartial && items.length > 0 && (
        <h2 className="text-xl font-bold text-gray-800 mb-3">Experience (continued)</h2>
      )}
      <div className="space-y-4">
        {items.map((exp: Experience.DisplayOutput, index: number) => (
          <div key={index} className="border-l-2 border-gray-300 pl-4 avoid-break">
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-semibold text-gray-900">{exp.jobTitle}</h3>
              <span className="text-sm text-gray-600">
                {exp.startDate} - {exp.endDate || "Present"}
              </span>
            </div>
            <div className="text-gray-700 mb-1">
              {exp.companyName}
              {exp.location && <span> • {exp.location}</span>}
            </div>
            {exp.description && (
              <p className="text-gray-600 text-sm mb-2">{exp.description}</p>
            )}
            {exp.keyPoints.length > 0 && (
              <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
                {exp.keyPoints.map((point: string, idx: number) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

interface ProjectsProps {
  items: Project.DisplayOutput[];
  isPartial?: boolean;
}

export function ResumeProjects({ items, isPartial = false }: ProjectsProps) {
  if (items.length === 0) return null;
  
  return (
    <section className="resume-section">
      {!isPartial && (
        <h2 className="text-xl font-bold text-gray-800 mb-3">Projects</h2>
      )}
      {isPartial && items.length > 0 && (
        <h2 className="text-xl font-bold text-gray-800 mb-3">Projects (continued)</h2>
      )}
      <div className="space-y-4">
        {items.map((project: Project.DisplayOutput, index: number) => (
          <div key={index} className="border-l-2 border-gray-300 pl-4 avoid-break">
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-semibold text-gray-900">{project.projectName}</h3>
              <span className="text-sm text-gray-600">
                {project.startDate} - {project.endDate || "Present"}
              </span>
            </div>
            <div className="text-gray-700 mb-1">
              {project.role}
              {project.location && <span> • {project.location}</span>}
            </div>
            {project.description && (
              <p className="text-gray-600 text-sm mb-2">{project.description}</p>
            )}
            {project.keyPoints.length > 0 && (
              <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
                {project.keyPoints.map((point: string, idx: number) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

interface EducationProps {
  items: Education.DisplayOutput[];
  isPartial?: boolean;
}

export function ResumeEducation({ items, isPartial = false }: EducationProps) {
  if (items.length === 0) return null;
  
  return (
    <section className="resume-section">
      {!isPartial && (
        <h2 className="text-xl font-bold text-gray-800 mb-3">Education</h2>
      )}
      {isPartial && items.length > 0 && (
        <h2 className="text-xl font-bold text-gray-800 mb-3">Education (continued)</h2>
      )}
      <div className="space-y-3">
        {items.map((edu: Education.DisplayOutput, index: number) => (
          <div key={index} className="border-l-2 border-gray-300 pl-4 avoid-break">
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-semibold text-gray-900">{edu.degree}</h3>
              <span className="text-sm text-gray-600">
                {edu.startDate} - {edu.endDate}
              </span>
            </div>
            <div className="text-gray-700 mb-1">
              {edu.schoolName}
              {edu.city && edu.country && <span> • {edu.city}, {edu.country}</span>}
            </div>
            {edu.points.length > 0 && (
              <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
                {edu.points.map((point: string, idx: number) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

interface SkillsProps {
  items: string[];
}

export function ResumeSkills({ items }: SkillsProps) {
  if (items.length === 0) return null;
  
  return (
    <section className="resume-section avoid-break">
      <h2 className="text-xl font-bold text-gray-800 mb-3">Skills</h2>
      <div className="flex flex-wrap gap-2">
        {items.map((skill: string, index: number) => (
          <span
            key={index}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-sm print:bg-gray-100"
          >
            {skill}
          </span>
        ))}
      </div>
    </section>
  );
}