"use client";

import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useRouter, usePathname } from "next/navigation";

export default function TestLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isRootTestPage = pathname === "/test";

  return (
    <div className="min-h-screen bg-background">
      {!isRootTestPage && (
        <div className="border-b">
          <div className="container mx-auto px-4 py-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/test")}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Test Pages
            </Button>
          </div>
        </div>
      )}
      {children}
    </div>
  );
}