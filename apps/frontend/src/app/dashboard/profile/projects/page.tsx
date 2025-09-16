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
  FolderOpen,
  Calendar,
  Link as LinkIcon,
  ChevronLeft,
  Code,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { ProjectForm } from "@/components/profile/ProjectForm";
import { DeleteConfirmDialog } from "@/components/profile/DeleteConfirmDialog";
import {
  getProjectsApiV1ProfileProjectsGet,
  createProjectApiV1ProfileProjectsPost,
  updateProjectApiV1ProfileProjectsProjectIdPut,
  deleteProjectApiV1ProfileProjectsProjectIdDelete,
} from "@/lib/api/generated/api";
import type {
  ProjectResponse,
  ProjectCreateRequest,
  ProjectUpdateRequest,
} from "@/lib/api/generated/schemas";

// Using the generated ProjectResponse type
type Project = ProjectResponse;

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");

  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await getProjectsApiV1ProfileProjectsGet();
      setProjects(response.projects || []);
    } catch (error) {
      console.error("Failed to load projects:", error);
      toast("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: unknown) => {
    try {
      await createProjectApiV1ProfileProjectsPost(
        data as ProjectCreateRequest
      );
      toast("Project added successfully");
      setFormOpen(false);
      fetchProjects();
    } catch (error) {
      console.error("Failed to create project:", error);
      toast("Failed to add project");
    }
  };

  const handleUpdate = async (data: unknown) => {
    if (!selectedProject) return;
    try {
      await updateProjectApiV1ProfileProjectsProjectIdPut(
        selectedProject.id,
        data as ProjectUpdateRequest
      );
      toast("Project updated successfully");
      setFormOpen(false);
      fetchProjects();
    } catch (error) {
      console.error("Failed to update project:", error);
      toast("Failed to update project");
    }
  };

  const handleDelete = async () => {
    if (!selectedProject) return;
    try {
      await deleteProjectApiV1ProfileProjectsProjectIdDelete(
        selectedProject.id
      );
      toast("Project deleted successfully");
      setDeleteDialogOpen(false);
      setSelectedProject(null);
      fetchProjects();
    } catch (error) {
      console.error("Failed to delete project:", error);
      toast("Failed to delete project");
    }
  };

  const openCreateForm = () => {
    setSelectedProject(null);
    setFormMode("create");
    setFormOpen(true);
  };

  const openEditForm = (project: Project) => {
    setSelectedProject(project);
    setFormMode("edit");
    setFormOpen(true);
  };

  const openDeleteDialog = (project: Project) => {
    setSelectedProject(project);
    setDeleteDialogOpen(true);
  };

  const formatDate = (date?: string) => {
    if (!date) return "Present";
    const [year, month] = date.split("-");
    const monthNames = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ];
    return month ? `${monthNames[parseInt(month) - 1]} ${year}` : year;
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
            <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
            <p className="text-muted-foreground mt-2">
              Showcase your personal, professional, and open-source projects
            </p>
          </div>
          <Button onClick={openCreateForm}>
            <Plus className="h-4 w-4 mr-2" />
            Add Project
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
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FolderOpen className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No projects added yet</h3>
            <p className="text-sm text-muted-foreground text-center mb-6">
              Add your projects to showcase your skills and achievements
            </p>
            <Button onClick={openCreateForm}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((project) => (
            <Card key={project.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-4">
                <div className="flex justify-between items-start">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-xl">{project.project_name}</CardTitle>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openEditForm(project)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openDeleteDialog(project)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {project.description && (
                  <p className="text-sm text-muted-foreground">
                    {project.description}
                  </p>
                )}

                <div className="flex flex-wrap gap-3 text-sm">
                  {(project.start_date || project.end_date) && (
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      {formatDate(project.start_date)} - {formatDate(project.end_date)}
                    </div>
                  )}
                  {project.url && (
                    <a
                      href={project.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-primary hover:underline"
                    >
                      <ExternalLink className="h-4 w-4" />
                      View Project
                    </a>
                  )}
                  {project.github_url && (
                    <a
                      href={project.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-primary hover:underline"
                    >
                      <Code className="h-4 w-4" />
                      GitHub
                    </a>
                  )}
                </div>

                {project.technologies && project.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {project.technologies.split(",").map((tech, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {tech.trim()}
                      </Badge>
                    ))}
                  </div>
                )}

                {project.tasks && project.tasks.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-sm mb-2">Key Achievements:</h4>
                    <ul className="list-disc pl-5 space-y-1">
                      {project.tasks.map((task) => (
                        <li key={task.id} className="text-sm text-muted-foreground">
                          {task.description}
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

      <ProjectForm
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={formMode === "create" ? handleCreate : handleUpdate}
        initialData={selectedProject || undefined}
        mode={formMode}
      />

      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDelete}
        title="Delete Project"
        description={`Are you sure you want to delete "${selectedProject?.name}"? This action cannot be undone.`}
      />
    </div>
  );
}