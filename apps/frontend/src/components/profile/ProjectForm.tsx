"use client";

import { useState, useEffect } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Plus, X } from "lucide-react";

const dateFormatRegex = /^\d{4}-\d{2}$/;

const projectSchema = z.object({
  project_name: z.string().min(1, "Project name is required"),
  description: z.string().optional(),
  start_date: z.string().regex(dateFormatRegex, "Date must be in YYYY-MM format").optional().or(z.literal("")),
  end_date: z.string().regex(dateFormatRegex, "Date must be in YYYY-MM format").optional().or(z.literal("")),
  project_url: z.string().url().optional().or(z.literal("")),
  repository_url: z.string().url().optional().or(z.literal("")),
  tasks: z.array(z.string().min(1, "Task cannot be empty")).optional(),
});

type ProjectFormData = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ProjectFormData) => Promise<void>;
  initialData?: Partial<ProjectFormData>;
  mode: "create" | "edit";
}

export function ProjectForm({
  open,
  onOpenChange,
  onSubmit,
  initialData,
  mode,
}: ProjectFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      project_name: "",
      description: "",
      start_date: "",
      end_date: "",
      project_url: "",
      repository_url: "",
      tasks: [],
    },
  });

  // Reset form when initialData changes (for edit mode)
  useEffect(() => {
    if (open && initialData) {
      form.reset({
        project_name: initialData.project_name || "",
        description: initialData.description || "",
        start_date: initialData.start_date || "",
        end_date: initialData.end_date || "",
        project_url: initialData.project_url || "",
        repository_url: initialData.repository_url || "",
        tasks: initialData.tasks || [],
      });
    } else if (open && !initialData) {
      // Reset to empty form for create mode
      form.reset({
        project_name: "",
        description: "",
        start_date: "",
        end_date: "",
        project_url: "",
        repository_url: "",
        tasks: [],
      });
    }
  }, [open, initialData, form]);

  const { fields, append, remove } = useFieldArray<ProjectFormData, "tasks">({
    control: form.control,
    name: "tasks",
  });

  const handleSubmit = async (data: ProjectFormData) => {
    setIsSubmitting(true);
    try {
      // Filter out empty tasks and handle date fields
      const filteredData = {
        ...data,
        tasks: data.tasks?.filter(t => t.trim() !== "") || [],
        project_url: data.project_url || undefined,
        repository_url: data.repository_url || undefined,
        start_date: data.start_date?.trim() || undefined,
        end_date: (data.end_date?.trim() && data.end_date.toLowerCase() !== "present") ? data.end_date.trim() : undefined,
      };
      await onSubmit(filteredData);
      form.reset();
      onOpenChange(false);
    } catch (error) {
      console.error("Error submitting project:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Add Project" : "Edit Project"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add a project you've worked on"
              : "Update your project information"}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="project_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Project Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. E-commerce Platform" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Brief description of the project..."
                      className="min-h-[80px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />


            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start Date</FormLabel>
                    <FormControl>
                      <Input placeholder="YYYY-MM" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>End Date (leave blank if ongoing)</FormLabel>
                    <FormControl>
                      <Input placeholder="YYYY-MM" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="project_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Project URL (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        type="url"
                        placeholder="https://example.com"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="repository_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Repository URL (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        type="url"
                        placeholder="https://github.com/..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-2">
              <FormLabel>Key Tasks & Achievements</FormLabel>
              <div className="space-y-2">
                {fields.map((field, index) => (
                  <div key={field.id} className="flex gap-2">
                    <FormField
                      control={form.control}
                      name={`tasks.${index}`}
                      render={({ field }) => (
                        <FormItem className="flex-1">
                          <FormControl>
                            <Textarea
                              placeholder="Describe a key task or achievement..."
                              className="min-h-[60px]"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    {fields.length > 0 && (
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => remove(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => append("")}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Task
              </Button>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {mode === "create" ? "Add Project" : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}