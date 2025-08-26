import React from 'react';

interface A4PageProps {
  children: React.ReactNode;
  pageNumber?: number;
  totalPages?: number;
  showPageNumber?: boolean;
  className?: string;
}

export function A4Page({
  children,
  pageNumber,
  totalPages,
  showPageNumber = true,
  className = '',
}: A4PageProps) {
  return (
    <div className={`a4-page ${className}`}>
      <div className="a4-page-content">
        {children}
      </div>
      {showPageNumber && pageNumber && totalPages && (
        <div className="a4-page-footer">
          Page {pageNumber} of {totalPages}
        </div>
      )}
    </div>
  );
}