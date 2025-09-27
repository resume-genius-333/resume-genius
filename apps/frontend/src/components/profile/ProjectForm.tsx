"use client";

import { useMemo, useState } from "react";
import z from "zod";
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
import { Loader2 } from "lucide-react";
import { createProfileProjectApiV1ProfileProjectsPostBody } from "@/lib/api/generated/api.zod";
import type { ProfileProjectSchema } from "@/lib/api/generated/schemas";
import { NormalizationDefaultValues, useZodForm } from "@/hooks/use-zod-form";

const dateFormatRegex = /^\d{4}-\d{2}$/;

const projectFormSchema =
  createProfileProjectApiV1ProfileProjectsPostBody.extend({
    project_name: z.string().min(1, "Project name is required"),
    description: z.string().max(1000).nullable().optional(),
    start_date: z
      .string()
      .regex(dateFormatRegex, "Date must be in YYYY-MM format")
      .or(z.literal(""))
      .nullable()
      .optional(),
    end_date: z
      .string()
      .regex(dateFormatRegex, "Date must be in YYYY-MM format")
      .or(z.literal(""))
      .nullable()
      .optional(),
    project_url: z
      .string()
      .url("Enter a valid URL")
      .or(z.literal(""))
      .nullable()
      .optional(),
    repository_url: z
      .url("Enter a valid URL")
      .or(z.literal(""))
      .nullable()
      .optional(),
    tasks: z
      .array(z.string().min(1, "Task cannot be empty"))
      .nullable()
      .optional(),
  });

type ProjectFormValues = z.infer<typeof projectFormSchema>;

type ProjectFormInitial = ProfileProjectSchema & { tasks?: string[] | null };

const PROJECT_DEFAULTS: NormalizationDefaultValues<ProjectFormValues> = {
  description: "",
  start_date: "",
  end_date: "",
  project_url: "",
  repository_url: "",
};

interface ProjectFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ProjectFormValues) => Promise<void>;
  initialData?: Partial<ProjectFormInitial>;
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

  const initialValues = useMemo<ProjectFormValues>(() => {
    const tasks = Array.isArray(initialData?.tasks)
      ? (initialData?.tasks ?? [])
      : [];

    const base: ProjectFormValues = {
      project_name: initialData?.project_name ?? "",
      description: initialData?.description ?? undefined,
      start_date: initialData?.start_date ?? undefined,
      end_date: initialData?.end_date ?? undefined,
      project_url: initialData?.project_url ?? undefined,
      repository_url: initialData?.repository_url ?? undefined,
      tasks,
    };

    return base;
  }, [initialData]);

  const { form, submit } = useZodForm({
    zodObject: projectFormSchema,
    initial: initialValues,
    defaults: PROJECT_DEFAULTS,
    onUpdate: async (values) => {
      setIsSubmitting(true);
      try {
        const cleanedTasks = values.tasks
          ?.map((task) => task.trim())
          .filter((task) => task.length > 0);

        const payload: ProjectFormValues = {
          ...values,
          tasks:
            cleanedTasks && cleanedTasks.length > 0 ? cleanedTasks : undefined,
        };

        await onSubmit(payload);
        if (mode === "create") {
          form.reset();
        }
        onOpenChange(false);
      } catch (error) {
        console.error("Error submitting project:", error);
      } finally {
        setIsSubmitting(false);
      }
    },
  });

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
          <form onSubmit={submit} className="space-y-4">
            <FormField
              control={form.control}
              name="project_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Project Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g. E-commerce Platform"
                      {...field}
                      value={field.value ?? ""}
                    />
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
                      value={field.value ?? ""}
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
                      <Input
                        placeholder="YYYY-MM"
                        {...field}
                        value={field.value ?? ""}
                      />
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
                      <Input
                        placeholder="YYYY-MM"
                        {...field}
                        value={field.value ?? ""}
                      />
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
                        value={field.value ?? ""}
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
                        value={field.value ?? ""}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
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
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {mode === "create" ? "Add Project" : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
