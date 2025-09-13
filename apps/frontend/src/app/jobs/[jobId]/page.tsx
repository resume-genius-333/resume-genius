"use client";

interface JobPageInput {
  params: { jobId: string };
}

export default function JobPage({ params }: JobPageInput) {
  const { jobId } = params;
}
