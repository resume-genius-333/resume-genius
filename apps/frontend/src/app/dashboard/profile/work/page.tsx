"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Plus,
  Edit2,
  Trash2,
  Briefcase,
  Calendar,
  MapPin,
  Building,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";
import { WorkExperienceForm } from "@/components/profile/WorkExperienceForm";
import { DeleteConfirmDialog } from "@/components/profile/DeleteConfirmDialog";
import {
  getWorkExperiencesApiV1ProfileWorkExperiencesGet,
  createWorkExperienceApiV1ProfileWorkExperiencesPost,
  updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPut,
  deleteWorkExperienceApiV1ProfileWorkExperiencesWorkIdDelete,
} from "@/lib/api/generated/api";
import type {
  WorkExperienceResponse,
  WorkExperienceCreateRequest,
  WorkExperienceUpdateRequest,
} from "@/lib/api/generated/schemas";

// Using the generated WorkExperienceResponse type
type WorkExperience = WorkExperienceResponse;

export default function WorkExperiencePage() {
  const [workExperiences, setWorkExperiences] = useState<WorkExperience[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedWork, setSelectedWork] = useState<WorkExperience | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");

  useEffect(() => {
    fetchWorkExperiences();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchWorkExperiences = async () => {
    try {
      const response = await getWorkExperiencesApiV1ProfileWorkExperiencesGet();
      setWorkExperiences(response.work_experiences || []);
    } catch (error) {
      console.error("Failed to load work experiences:", error);
      toast("Failed to load work experiences");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: unknown) => {
    try {
      console.log("Creating work experience with data:", JSON.stringify(data, null, 2));
      await createWorkExperienceApiV1ProfileWorkExperiencesPost(
        data as WorkExperienceCreateRequest
      );
      toast("Work experience added successfully");
      setFormOpen(false);
      fetchWorkExperiences();
    } catch (error) {
      console.error("Failed to create work experience:", error);
      toast("Failed to add work experience");
    }
  };

  const handleUpdate = async (data: unknown) => {
    if (!selectedWork) return;
    try {
      await updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPut(
        selectedWork.id,
        data as WorkExperienceUpdateRequest
      );
      toast("Work experience updated successfully");
      setFormOpen(false);
      fetchWorkExperiences();
    } catch (error) {
      console.error("Failed to update work experience:", error);
      toast("Failed to update work experience");
    }
  };

  const handleDelete = async () => {
    if (!selectedWork) return;
    try {
      await deleteWorkExperienceApiV1ProfileWorkExperiencesWorkIdDelete(
        selectedWork.id
      );
      toast("Work experience deleted successfully");
      setDeleteDialogOpen(false);
      setSelectedWork(null);
      fetchWorkExperiences();
    } catch (error) {
      console.error("Failed to delete work experience:", error);
      toast("Failed to delete work experience");
    }
  };

  const openCreateForm = () => {
    setSelectedWork(null);
    setFormMode("create");
    setFormOpen(true);
  };

  const openEditForm = (work: WorkExperience) => {
    setSelectedWork(work);
    setFormMode("edit");
    setFormOpen(true);
  };

  const openDeleteDialog = (work: WorkExperience) => {
    setSelectedWork(work);
    setDeleteDialogOpen(true);
  };

  const getEmploymentTypeLabel = (type?: string) => {
    const labels: Record<string, string> = {
      full_time: "Full-time",
      part_time: "Part-time",
      contract: "Contract",
      internship: "Internship",
      freelance: "Freelance",
      volunteer: "Volunteer",
      other: "Other",
    };
    return type ? labels[type] || type : "Full-time";
  };

  const formatDate = (date?: string) => {
    if (!date) return "Present";
    const [year, month] = date.split("-");
    const monthNames = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Link href="/dashboard/profile">
            <Button variant="ghost" size="sm">
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back to Profile
            </Button>
          </Link>
        </div>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Work Experience</h1>
            <p className="text-muted-foreground mt-2">
              Manage your professional experience and career history
            </p>
          </div>
          <Button onClick={openCreateForm}>
            <Plus className="h-4 w-4 mr-2" />
            Add Experience
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : workExperiences.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Briefcase className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No work experience added yet</h3>
            <p className="text-sm text-muted-foreground text-center mb-6">
              Add your professional experience to showcase your career journey
            </p>
            <Button onClick={openCreateForm}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Experience
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {workExperiences.map((work) => (
            <Card key={work.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-4">
                <div className="flex justify-between items-start">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-xl">{work.position_title}</CardTitle>
                    <CardDescription className="flex items-center gap-2 text-base">
                      <Building className="h-4 w-4" />
                      {work.company_name}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openEditForm(work)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openDeleteDialog(work)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(work.start_date)} - {formatDate(work.end_date)}
                  </div>
                  {work.location && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {work.location}
                    </div>
                  )}
                  <Badge variant="secondary">
                    {getEmploymentTypeLabel(work.employment_type)}
                  </Badge>
                </div>

                {work.responsibilities && work.responsibilities.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Key Responsibilities:</h4>
                    <ul className="list-disc pl-5 space-y-1">
                      {work.responsibilities.map((resp, index) => (
                        <li key={index} className="text-sm text-muted-foreground">
                          {resp}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <WorkExperienceForm
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={formMode === "create" ? handleCreate : handleUpdate}
        initialData={selectedWork || undefined}
        mode={formMode}
      />

      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDelete}
        title="Delete Work Experience"
        description={`Are you sure you want to delete your experience at ${selectedWork?.company_name}? This action cannot be undone.`}
      />
    </div>
  );
}