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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Plus, X } from "lucide-react";
import { EmploymentType } from "@/lib/api/generated/schemas";
import {
  createProfileWorkExperienceApiV1ProfileWorkExperiencesPostBody,
  getProfileWorkExperienceApiV1ProfileWorkExperiencesWorkIdGetResponse,
} from "@/lib/api/generated/api.zod";
import { NormalizationDefaultValues, useZodForm } from "@/hooks/use-zod-form";

const employmentTypes: Record<EmploymentType, string> = {
  full_time: "Full Time",
  part_time: "Part Time",
  contract: "Contract",
  freelance: "Freelance",
  internship: "Internship",
  volunteer: "Volunteer",
  other: "Other",
};

const workExperienceFormSchema =
  createProfileWorkExperienceApiV1ProfileWorkExperiencesPostBody;

type WorkExperienceFormValues = z.infer<typeof workExperienceFormSchema>;

type WorkExperienceFormInitial = Partial<
  z.infer<
    typeof getProfileWorkExperienceApiV1ProfileWorkExperiencesWorkIdGetResponse
  >
>;

const WORK_DEFAULTS: NormalizationDefaultValues<WorkExperienceFormValues> = {
  location: "",
  start_date: "",
  end_date: "",
};

interface WorkExperienceFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: WorkExperienceFormValues) => Promise<void>;
  initialData?: Partial<WorkExperienceFormInitial>;
  mode: "create" | "edit";
}

export function WorkExperienceForm({
  open,
  onOpenChange,
  onSubmit,
  initialData,
  mode,
}: WorkExperienceFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const initialValues = useMemo<WorkExperienceFormValues>(() => {
    // Extract responsibility descriptions from the array of objects
    let responsibilities: string[] = [];
    if (
      initialData?.responsibilities &&
      Array.isArray(initialData.responsibilities)
    ) {
      responsibilities = initialData.responsibilities
        .map((resp) =>
          typeof resp === "string"
            ? resp
            : (resp as { description?: string })?.description || ""
        )
        .filter((desc: string) => desc.length > 0);
    }

    const base: WorkExperienceFormValues = {
      company_name: initialData?.company_name ?? "",
      position_title: initialData?.position_title ?? "",
      employment_type:
        (initialData?.employment_type as EmploymentType | undefined) ??
        "full_time",
      location: initialData?.location ?? undefined,
      start_date: initialData?.start_date ?? undefined,
      end_date: initialData?.end_date ?? undefined,
      responsibilities: responsibilities.length > 0 ? responsibilities : [],
    };

    return base;
  }, [initialData]);

  const { form, submit } = useZodForm({
    zodObject: workExperienceFormSchema,
    initial: initialValues,
    defaults: WORK_DEFAULTS,
    onUpdate: async (values) => {
      setIsSubmitting(true);
      try {
        const cleanedResponsibilities = values.responsibilities
          ?.map((resp) => resp.trim())
          .filter((resp) => resp.length > 0);

        const payload: WorkExperienceFormValues = {
          ...values,
          responsibilities:
            cleanedResponsibilities && cleanedResponsibilities.length > 0
              ? cleanedResponsibilities
              : [],
        };

        await onSubmit(payload);
        if (mode === "create") {
          form.reset();
        }
        onOpenChange(false);
      } catch (error) {
        console.error("Error submitting work experience:", error);
      } finally {
        setIsSubmitting(false);
      }
    },
  });

  const employmentTypeOptions = useMemo(
    () => Object.entries(employmentTypes),
    []
  );

  const handleAddResponsibility = () => {
    const current = form.getValues("responsibilities") || [];
    form.setValue("responsibilities", [...current, ""]);
  };

  const handleRemoveResponsibility = (index: number) => {
    const current = form.getValues("responsibilities") || [];
    form.setValue(
      "responsibilities",
      current.filter((_, i) => i !== index)
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Add Work Experience" : "Edit Work Experience"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add your professional work experience"
              : "Update your work experience information"}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="company_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Company Name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g. Google"
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
                name="position_title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Position Title</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g. Software Engineer"
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
                name="employment_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Employment Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select employment type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {employmentTypeOptions.map(([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="location"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Location</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g. San Francisco, CA"
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
                    <FormLabel>End Date (leave blank if current)</FormLabel>
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

            <FormField
              control={form.control}
              name="responsibilities"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Responsibilities</FormLabel>
                  <div className="space-y-2">
                    {(field.value || []).map((resp, index) => (
                      <div key={index} className="flex gap-2">
                        <FormControl>
                          <Textarea
                            placeholder="Describe a key responsibility..."
                            className="min-h-[60px]"
                            value={resp}
                            onChange={(e) => {
                              const newResponsibilities = [
                                ...(field.value || []),
                              ];
                              newResponsibilities[index] = e.target.value;
                              field.onChange(newResponsibilities);
                            }}
                          />
                        </FormControl>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveResponsibility(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleAddResponsibility}
                      className="w-full"
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add Responsibility
                    </Button>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

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
                {mode === "create" ? "Add Experience" : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
