"use client";

import React, { useEffect, useState } from 'react';
import { A4Page } from './A4Page';
import {
  ResumeHeader,
  ResumeSummary,
  ResumeExperience,
  ResumeProjects,
  ResumeEducation,
  ResumeSkills,
} from './ResumeSections';
import { paginateResume, PageContent, ResumeData } from '@/lib/utils/resumePaginator';

interface ResumeDisplayProps {
  resume: ResumeData;
}

export function ResumeDisplay({ resume }: ResumeDisplayProps) {
  const [pages, setPages] = useState<PageContent[]>([]);
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const setupPages = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Wait a tick for DOM to be ready
        await new Promise(resolve => setTimeout(resolve, 0));
        
        // Paginate the resume content
        const paginatedPages = await paginateResume(resume, {
          Header: ResumeHeader,
          Summary: ResumeSummary,
          Experience: ResumeExperience,
          Projects: ResumeProjects,
          Education: ResumeEducation,
          Skills: ResumeSkills,
        });
        
        setPages(paginatedPages);
        
        // Signal to Playwright that rendering is complete
        if (typeof window !== 'undefined') {
          (window as Window & { __RESUME_READY__?: boolean }).__RESUME_READY__ = true;
        }
        
        setIsReady(true);
      } catch (err) {
        console.error('Error paginating resume:', err);
        setError('Failed to format resume for printing');
      } finally {
        setIsLoading(false);
      }
    };
    
    setupPages();
  }, [resume]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="a4-container">
        <div className="a4-page">
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-4 text-gray-600">Formatting resume...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="a4-container">
        <div className="a4-page">
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-xl font-bold text-red-600 mb-2">Error</h2>
              <p className="text-gray-600">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show paginated resume
  return (
    <div className="a4-container" data-ready={isReady}>
      {pages.map((page, index) => (
        <A4Page
          key={index}
          pageNumber={page.pageNumber}
          totalPages={pages.length}
          showPageNumber={pages.length > 1}
        >
          {page.sections.map((section, sectionIndex) => (
            <React.Fragment key={`${index}-${sectionIndex}`}>
              {section}
            </React.Fragment>
          ))}
        </A4Page>
      ))}
      
      {/* Fallback if no pages generated */}
      {pages.length === 0 && isReady && (
        <A4Page>
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">No resume content to display</p>
          </div>
        </A4Page>
      )}
    </div>
  );
}