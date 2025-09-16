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
  GraduationCap,
  Calendar,
  Award,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";
import { EducationForm } from "@/components/profile/EducationForm";
import { DeleteConfirmDialog } from "@/components/profile/DeleteConfirmDialog";
import {
  getEducationsApiV1ProfileEducationsGet,
  createEducationApiV1ProfileEducationsPost,
  updateEducationApiV1ProfileEducationsEducationIdPut,
  deleteEducationApiV1ProfileEducationsEducationIdDelete,
} from "@/lib/api/generated/api";
import type {
  EducationResponse,
  EducationCreateRequest,
  EducationUpdateRequest,
} from "@/lib/api/generated/schemas";

// Using the generated EducationResponse type
type Education = EducationResponse;

export default function EducationPage() {
  const [educations, setEducations] = useState<Education[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedEducation, setSelectedEducation] = useState<Education | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");

  useEffect(() => {
    fetchEducations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchEducations = async () => {
    try {
      const response = await getEducationsApiV1ProfileEducationsGet();
      setEducations(response.educations || []);
    } catch (error) {
      console.error("Failed to load educations:", error);
      toast("Failed to load educations");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: unknown) => {
    try {
      await createEducationApiV1ProfileEducationsPost(data as EducationCreateRequest);
      toast("Education added successfully");
      setFormOpen(false);
      fetchEducations();
    } catch (error) {
      console.error("Failed to create education:", error);
      toast("Failed to add education");
    }
  };

  const handleUpdate = async (data: unknown) => {
    if (!selectedEducation) return;
    try {
      await updateEducationApiV1ProfileEducationsEducationIdPut(
        selectedEducation.id,
        data as EducationUpdateRequest
      );
      toast("Education updated successfully");
      setFormOpen(false);
      fetchEducations();
    } catch (error) {
      console.error("Failed to update education:", error);
      toast("Failed to update education");
    }
  };

  const handleDelete = async () => {
    if (!selectedEducation) return;
    try {
      await deleteEducationApiV1ProfileEducationsEducationIdDelete(selectedEducation.id);
      toast("Education deleted successfully");
      setDeleteDialogOpen(false);
      setSelectedEducation(null);
      fetchEducations();
    } catch (error) {
      console.error("Failed to delete education:", error);
      toast("Failed to delete education");
    }
  };

  const openCreateForm = () => {
    setSelectedEducation(null);
    setFormMode("create");
    setFormOpen(true);
  };

  const openEditForm = (education: Education) => {
    setSelectedEducation(education);
    setFormMode("edit");
    setFormOpen(true);
  };

  const openDeleteDialog = (education: Education) => {
    setSelectedEducation(education);
    setDeleteDialogOpen(true);
  };

  const getDegreeLabel = (degree: string) => {
    const labels: Record<string, string> = {
      high_school: "High School",
      associate: "Associate",
      bachelor: "Bachelor's",
      master: "Master's",
      doctorate: "Doctorate",
      certificate: "Certificate",
      bootcamp: "Bootcamp",
      other: "Other",
    };
    return labels[degree] || degree;
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
            <h1 className="text-3xl font-bold tracking-tight">Education</h1>
            <p className="text-muted-foreground mt-2">
              Manage your educational background and qualifications
            </p>
          </div>
          <Button onClick={openCreateForm}>
            <Plus className="h-4 w-4 mr-2" />
            Add Education
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
      ) : educations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <GraduationCap className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Education Added</h3>
            <p className="text-muted-foreground text-center mb-4">
              Start building your educational profile by adding your qualifications
            </p>
            <Button onClick={openCreateForm}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Education
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {educations.map((education) => (
            <Card key={education.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <CardTitle className="text-xl">
                      {education.institution_name}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <Badge variant="secondary">
                        {getDegreeLabel(education.degree)}
                      </Badge>
                      <span>{education.field_of_study}</span>
                      {education.focus_area && (
                        <span className="text-sm">• {education.focus_area}</span>
                      )}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openEditForm(education)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openDeleteDialog(education)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  {(education.start_date || education.end_date) && (
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>
                        {formatDate(education.start_date)} -{" "}
                        {formatDate(education.end_date)}
                      </span>
                    </div>
                  )}
                  {education.gpa && (
                    <div className="flex items-center gap-1">
                      <Award className="h-3 w-3" />
                      <span>
                        GPA: {education.gpa}
                        {education.max_gpa && ` / ${education.max_gpa}`}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <EducationForm
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={formMode === "create" ? handleCreate : handleUpdate}
        initialData={selectedEducation || undefined}
        mode={formMode}
      />

      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDelete}
        title="Delete Education"
        description={`Are you sure you want to delete your education at ${selectedEducation?.institution_name}? This action cannot be undone.`}
      />
    </div>
  );
}