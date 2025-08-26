import { ReactNode } from 'react';
import { createRoot } from 'react-dom/client';

// A4 dimensions at 96 DPI
export const A4_DIMENSIONS = {
  WIDTH: 794, // 210mm in pixels at 96 DPI
  HEIGHT: 1122, // 297mm in pixels at 96 DPI
  MARGIN: 76, // 20mm in pixels at 96 DPI
  CONTENT_WIDTH: 642, // 170mm (210mm - 40mm margins)
  CONTENT_HEIGHT: 970, // 257mm (297mm - 40mm margins)
  // Leave some buffer for safety
  SAFE_CONTENT_HEIGHT: 920, // ~90% of content height
};

/**
 * Creates a hidden container for measuring component heights
 */
export function createMeasuringContainer(): HTMLDivElement {
  const container = document.createElement('div');
  container.id = 'resume-measure-container';
  container.style.cssText = `
    position: absolute;
    visibility: hidden;
    width: ${A4_DIMENSIONS.CONTENT_WIDTH}px;
    left: -9999px;
    top: -9999px;
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
  `;
  document.body.appendChild(container);
  return container;
}

/**
 * Measures the height of a React component
 */
export async function measureComponent(
  component: ReactNode,
  container: HTMLDivElement
): Promise<number> {
  return new Promise((resolve) => {
    const root = createRoot(container);
    root.render(component);
    
    // Use setTimeout to ensure React has rendered
    setTimeout(() => {
      const height = container.getBoundingClientRect().height;
      root.unmount();
      container.innerHTML = '';
      resolve(Math.ceil(height)); // Round up to avoid fractional pixels
    }, 0);
  });
}

/**
 * Measures the height of an HTML element
 */
export function measureElement(element: HTMLElement): number {
  return Math.ceil(element.getBoundingClientRect().height);
}

/**
 * Cleans up the measuring container
 */
export function cleanupMeasuringContainer(container: HTMLDivElement): void {
  if (container && container.parentNode) {
    container.parentNode.removeChild(container);
  }
}

/**
 * Estimates text height based on character count and line height
 * Useful for quick estimates without rendering
 */
export function estimateTextHeight(
  text: string,
  charsPerLine: number = 80,
  lineHeight: number = 24
): number {
  const lines = Math.ceil(text.length / charsPerLine);
  return lines * lineHeight;
}

/**
 * Checks if adding an element would exceed page height
 */
export function wouldExceedPage(
  currentHeight: number,
  elementHeight: number,
  maxHeight: number = A4_DIMENSIONS.SAFE_CONTENT_HEIGHT
): boolean {
  return currentHeight + elementHeight > maxHeight;
}

/**
 * Calculates remaining space on current page
 */
export function getRemainingSpace(
  currentHeight: number,
  maxHeight: number = A4_DIMENSIONS.SAFE_CONTENT_HEIGHT
): number {
  return Math.max(0, maxHeight - currentHeight);
}

/**
 * Determines if a section should start on a new page
 * (e.g., if it's a major section and current page is more than 70% full)
 */
export function shouldStartNewPage(
  currentHeight: number,
  sectionHeight: number,
  isMajorSection: boolean = false
): boolean {
  const pageUsageRatio = currentHeight / A4_DIMENSIONS.SAFE_CONTENT_HEIGHT;
  
  // Major sections (like Experience) should start fresh if page is >70% full
  if (isMajorSection && pageUsageRatio > 0.7) {
    return true;
  }
  
  // Any section should start fresh if it won't fit
  return wouldExceedPage(currentHeight, sectionHeight);
}