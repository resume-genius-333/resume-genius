import { ReactNode } from 'react';
import type { Education, Experience, Project } from '@/lib/api/schemas';
import {
  createMeasuringContainer,
  measureComponent,
  cleanupMeasuringContainer,
  wouldExceedPage,
  shouldStartNewPage,
} from './measureUtils';

export interface PageContent {
  sections: ReactNode[];
  currentHeight: number;
  pageNumber: number;
}

export interface ResumeData {
  fullName: string;
  email: string;
  phone?: string | null;
  location?: string | null;
  summary?: string | null;
  experience: Experience.DisplayOutput[];
  projects: Project.DisplayOutput[];
  education: Education.DisplayOutput[];
  skills: string[];
}

interface SectionConfig {
  type: 'header' | 'summary' | 'experience' | 'projects' | 'education' | 'skills';
  component: ReactNode;
  isMajor?: boolean;
  canSplit?: boolean;
}

/**
 * Main function to paginate resume content
 */
export async function paginateResume(
  resume: ResumeData,
  components: {
    Header: React.ComponentType<{ fullName: string; email: string; phone?: string | null; location?: string | null }>;
    Summary: React.ComponentType<{ summary: string }>;
    Experience: React.ComponentType<{ items: Experience.DisplayOutput[]; isPartial?: boolean }>;
    Projects: React.ComponentType<{ items: Project.DisplayOutput[]; isPartial?: boolean }>;
    Education: React.ComponentType<{ items: Education.DisplayOutput[]; isPartial?: boolean }>;
    Skills: React.ComponentType<{ items: string[] }>;
  }
): Promise<PageContent[]> {
  const pages: PageContent[] = [];
  const measuringContainer = createMeasuringContainer();
  
  try {
    let currentPage: PageContent = {
      sections: [],
      currentHeight: 0,
      pageNumber: 1,
    };
    
    // Always put header on first page
    const headerComponent = <components.Header {...resume} />;
    const headerHeight = await measureComponent(headerComponent, measuringContainer);
    currentPage.sections.push(headerComponent);
    currentPage.currentHeight = headerHeight;
    
    // Prepare sections
    const sections: SectionConfig[] = [];
    
    // Add summary if exists
    if (resume.summary) {
      sections.push({
        type: 'summary',
        component: <components.Summary summary={resume.summary} />,
        isMajor: false,
      });
    }
    
    // Add experience section if exists
    if (resume.experience.length > 0) {
      sections.push({
        type: 'experience',
        component: <components.Experience items={resume.experience} />,
        isMajor: true,
        canSplit: true,
      });
    }
    
    // Add projects section if exists
    if (resume.projects.length > 0) {
      sections.push({
        type: 'projects',
        component: <components.Projects items={resume.projects} />,
        isMajor: true,
        canSplit: true,
      });
    }
    
    // Add education section if exists
    if (resume.education.length > 0) {
      sections.push({
        type: 'education',
        component: <components.Education items={resume.education} />,
        isMajor: true,
        canSplit: true,
      });
    }
    
    // Add skills section if exists
    if (resume.skills.length > 0) {
      sections.push({
        type: 'skills',
        component: <components.Skills items={resume.skills} />,
        isMajor: false,
      });
    }
    
    // Process each section
    for (const section of sections) {
      const sectionHeight = await measureComponent(section.component, measuringContainer);
      
      // Check if we should start a new page
      if (shouldStartNewPage(currentPage.currentHeight, sectionHeight, section.isMajor)) {
        // Save current page and start new one
        pages.push(currentPage);
        currentPage = {
          sections: [],
          currentHeight: 0,
          pageNumber: pages.length + 1,
        };
      }
      
      // Check if section fits on current page
      if (!wouldExceedPage(currentPage.currentHeight, sectionHeight)) {
        // Section fits entirely
        currentPage.sections.push(section.component);
        currentPage.currentHeight += sectionHeight;
      } else if (section.canSplit && section.type !== 'summary') {
        // Section needs to be split across pages
        const splitSections = await splitSection(
          section,
          resume,
          components,
          currentPage.currentHeight,
          measuringContainer
        );
        
        for (const splitPart of splitSections) {
          const partHeight = await measureComponent(splitPart, measuringContainer);
          
          if (wouldExceedPage(currentPage.currentHeight, partHeight)) {
            // Start new page
            pages.push(currentPage);
            currentPage = {
              sections: [],
              currentHeight: 0,
              pageNumber: pages.length + 1,
            };
          }
          
          currentPage.sections.push(splitPart);
          currentPage.currentHeight += partHeight;
        }
      } else {
        // Can't split, must go on new page
        pages.push(currentPage);
        currentPage = {
          sections: [section.component],
          currentHeight: sectionHeight,
          pageNumber: pages.length + 1,
        };
      }
    }
    
    // Add final page if it has content
    if (currentPage.sections.length > 0) {
      pages.push(currentPage);
    }
    
    return pages;
  } finally {
    // Clean up measuring container
    cleanupMeasuringContainer(measuringContainer);
  }
}

/**
 * Splits a section into multiple parts that fit on pages
 */
async function splitSection(
  section: SectionConfig,
  resume: ResumeData,
  components: {
    Experience: React.ComponentType<{ items: Experience.DisplayOutput[]; isPartial?: boolean }>;
    Projects: React.ComponentType<{ items: Project.DisplayOutput[]; isPartial?: boolean }>;
    Education: React.ComponentType<{ items: Education.DisplayOutput[]; isPartial?: boolean }>;
  },
  currentPageHeight: number,
  measuringContainer: HTMLDivElement
): Promise<ReactNode[]> {
  const parts: ReactNode[] = [];
  
  switch (section.type) {
    case 'experience':
      parts.push(...await splitExperience(
        resume.experience,
        components.Experience,
        currentPageHeight,
        measuringContainer
      ));
      break;
    
    case 'projects':
      parts.push(...await splitProjects(
        resume.projects,
        components.Projects,
        currentPageHeight,
        measuringContainer
      ));
      break;
    
    case 'education':
      parts.push(...await splitEducation(
        resume.education,
        components.Education,
        currentPageHeight,
        measuringContainer
      ));
      break;
    
    default:
      // If can't split, return original
      parts.push(section.component);
  }
  
  return parts;
}

/**
 * Splits experience items across pages
 */
async function splitExperience(
  items: Experience.DisplayOutput[],
  Component: React.ComponentType<{ items: Experience.DisplayOutput[]; isPartial?: boolean }>,
  currentPageHeight: number,
  measuringContainer: HTMLDivElement
): Promise<ReactNode[]> {
  const parts: ReactNode[] = [];
  let currentBatch: Experience.DisplayOutput[] = [];
  let batchHeight = currentPageHeight;
  let isFirstBatch = true;
  
  for (const item of items) {
    // Measure single item
    const itemComponent = <Component items={[item]} isPartial={true} />;
    const itemHeight = await measureComponent(itemComponent, measuringContainer);
    
    if (wouldExceedPage(batchHeight, itemHeight)) {
      // Current batch is full, save it
      if (currentBatch.length > 0) {
        parts.push(
          <Component 
            key={`exp-batch-${parts.length}`} 
            items={currentBatch} 
            isPartial={!isFirstBatch || parts.length > 0}
          />
        );
        currentBatch = [item];
        batchHeight = itemHeight;
        isFirstBatch = false;
      } else {
        // Single item too large, add it anyway
        parts.push(itemComponent);
        batchHeight = 0;
      }
    } else {
      currentBatch.push(item);
      batchHeight += itemHeight;
    }
  }
  
  // Add remaining items
  if (currentBatch.length > 0) {
    parts.push(
      <Component 
        key={`exp-batch-${parts.length}`} 
        items={currentBatch} 
        isPartial={!isFirstBatch || parts.length > 0}
      />
    );
  }
  
  return parts;
}

/**
 * Splits project items across pages
 */
async function splitProjects(
  items: Project.DisplayOutput[],
  Component: React.ComponentType<{ items: Project.DisplayOutput[]; isPartial?: boolean }>,
  currentPageHeight: number,
  measuringContainer: HTMLDivElement
): Promise<ReactNode[]> {
  const parts: ReactNode[] = [];
  let currentBatch: Project.DisplayOutput[] = [];
  let batchHeight = currentPageHeight;
  let isFirstBatch = true;
  
  for (const item of items) {
    // Measure single item
    const itemComponent = <Component items={[item]} isPartial={true} />;
    const itemHeight = await measureComponent(itemComponent, measuringContainer);
    
    if (wouldExceedPage(batchHeight, itemHeight)) {
      // Current batch is full, save it
      if (currentBatch.length > 0) {
        parts.push(
          <Component 
            key={`proj-batch-${parts.length}`} 
            items={currentBatch} 
            isPartial={!isFirstBatch || parts.length > 0}
          />
        );
        currentBatch = [item];
        batchHeight = itemHeight;
        isFirstBatch = false;
      } else {
        // Single item too large, add it anyway
        parts.push(itemComponent);
        batchHeight = 0;
      }
    } else {
      currentBatch.push(item);
      batchHeight += itemHeight;
    }
  }
  
  // Add remaining items
  if (currentBatch.length > 0) {
    parts.push(
      <Component 
        key={`proj-batch-${parts.length}`} 
        items={currentBatch} 
        isPartial={!isFirstBatch || parts.length > 0}
      />
    );
  }
  
  return parts;
}

/**
 * Splits education items across pages
 */
async function splitEducation(
  items: Education.DisplayOutput[],
  Component: React.ComponentType<{ items: Education.DisplayOutput[]; isPartial?: boolean }>,
  currentPageHeight: number,
  measuringContainer: HTMLDivElement
): Promise<ReactNode[]> {
  const parts: ReactNode[] = [];
  let currentBatch: Education.DisplayOutput[] = [];
  let batchHeight = currentPageHeight;
  let isFirstBatch = true;
  
  for (const item of items) {
    // Measure single item
    const itemComponent = <Component items={[item]} isPartial={true} />;
    const itemHeight = await measureComponent(itemComponent, measuringContainer);
    
    if (wouldExceedPage(batchHeight, itemHeight)) {
      // Current batch is full, save it
      if (currentBatch.length > 0) {
        parts.push(
          <Component 
            key={`edu-batch-${parts.length}`} 
            items={currentBatch} 
            isPartial={!isFirstBatch || parts.length > 0}
          />
        );
        currentBatch = [item];
        batchHeight = itemHeight;
        isFirstBatch = false;
      } else {
        // Single item too large, add it anyway
        parts.push(itemComponent);
        batchHeight = 0;
      }
    } else {
      currentBatch.push(item);
      batchHeight += itemHeight;
    }
  }
  
  // Add remaining items
  if (currentBatch.length > 0) {
    parts.push(
      <Component 
        key={`edu-batch-${parts.length}`} 
        items={currentBatch} 
        isPartial={!isFirstBatch || parts.length > 0}
      />
    );
  }
  
  return parts;
}