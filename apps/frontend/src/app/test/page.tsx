"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { FileText, Layout, TestTube } from "lucide-react";

interface TestPage {
  title: string;
  description: string;
  path: string;
  icon: React.ReactNode;
}

const testPages: TestPage[] = [
  {
    title: "UI Components",
    description: "Test and preview UI components like CheckListTile",
    path: "/test/ui",
    icon: <Layout className="h-6 w-6" />,
  },
  {
    title: "Resume Upload",
    description: "Test resume upload workflow with checksum validation and extraction",
    path: "/test/upload",
    icon: <FileText className="h-6 w-6" />,
  },
];

export default function TestPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <TestTube className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">Test Pages</h1>
        </div>
        <p className="text-muted-foreground">
          Interactive test pages for validating features and components
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {testPages.map((page) => (
          <Card
            key={page.path}
            className="flex h-full flex-col hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => router.push(page.path)}
          >
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="text-primary">{page.icon}</div>
                <CardTitle>{page.title}</CardTitle>
              </div>
              <CardDescription>{page.description}</CardDescription>
            </CardHeader>
            <CardContent className="mt-auto pt-0">
              <Button variant="outline" className="w-full">
                Open Test Page
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
