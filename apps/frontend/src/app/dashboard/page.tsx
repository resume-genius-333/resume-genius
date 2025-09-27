"use client";

import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  FileText,
  Target,
  TrendingUp,
  Sparkles,
  Clock,
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  const stats = [
    {
      title: "Total Jobs",
      value: "0",
      icon: Target,
      description: "Active opportunities",
      trend: "neutral",
    },
    {
      title: "Applications",
      value: "0",
      icon: FileText,
      description: "Submitted this month",
      trend: "neutral",
    },
    {
      title: "Success Rate",
      value: "0%",
      icon: TrendingUp,
      description: "Interview conversion",
      trend: "neutral",
    },
  ];

  const recentActivity = [
    // This would be populated from API
  ];

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Welcome back, {user?.first_name || "there"}!
        </h1>
        <p className="text-muted-foreground">
          Here&apos;s an overview of your job search progress
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stat.description}
                </p>
                <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-primary/5" />
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions and Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quick Actions */}
        <Card className="relative overflow-hidden">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle>Quick Actions</CardTitle>
            </div>
            <CardDescription>
              Get started with your job search journey
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              className="w-full justify-between group"
              onClick={() => router.push("/dashboard/jobs/new")}
            >
              <span className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Create New Job Application
              </span>
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button
              variant="outline"
              className="w-full justify-between group"
              onClick={() => router.push("/dashboard/jobs")}
            >
              <span className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                View All Jobs
              </span>
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button
              variant="outline"
              className="w-full justify-between group"
              onClick={() => router.push("/dashboard/profile")}
            >
              <span className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Update Profile
              </span>
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              <CardTitle>Recent Activity</CardTitle>
            </div>
            <CardDescription>
              Your latest job applications and updates
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentActivity.length > 0 ? (
              <div className="space-y-4">
                {/* Activity items would go here */}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="h-12 w-12 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  No recent activity to show
                </p>
                <Button
                  size="sm"
                  onClick={() => router.push("/dashboard/jobs/new")}
                >
                  Start Your First Application
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tips Section */}
      <Card className="mt-6 bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 border-primary/20">
        <CardHeader>
          <CardTitle className="text-lg">💡 Pro Tip</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Keep your profile updated with your latest skills and experiences.
            This helps our AI create more tailored resumes for each job
            application.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
