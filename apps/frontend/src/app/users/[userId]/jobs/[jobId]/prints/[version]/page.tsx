import { getResumeData } from "@/lib/api/actions/resume";
import { ResumeDisplay } from "@/components/resume/ResumeDisplay";

interface PrintPageProps {
  params: Promise<{
    userId: string;
    jobId: string;
    version: string;
  }>;
}

export default async function PrintPage({ params }: PrintPageProps) {
  const { userId, jobId, version } = await params;
  
  let resume;
  try {
    resume = await getResumeData(userId, jobId, version);
  } catch (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Error Loading Resume</h1>
          <p className="mt-2 text-gray-600">
            {error instanceof Error ? error.message : "Failed to load resume data"}
          </p>
        </div>
      </div>
    );
  }

  // Pass resume data to client component for pagination
  return <ResumeDisplay resume={resume} />;
}