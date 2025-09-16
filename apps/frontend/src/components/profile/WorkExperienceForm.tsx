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

const employmentTypes = [
  { value: "full_time", label: "Full Time" },
  { value: "part_time", label: "Part Time" },
  { value: "contract", label: "Contract" },
  { value: "freelance", label: "Freelance" },
  { value: "internship", label: "Internship" },
  { value: "volunteer", label: "Volunteer" },
  { value: "other", label: "Other" },
] as const;

const dateFormatRegex = /^\d{4}-\d{2}$/;

const workExperienceSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  position_title: z.string().min(1, "Position title is required"),
  employment_type: z.enum([
    "full_time",
    "part_time",
    "contract",
    "freelance",
    "internship",
    "volunteer",
    "other",
  ]).optional(),
  location: z.string().optional(),
  start_date: z.string().regex(dateFormatRegex, "Date must be in YYYY-MM format").optional().or(z.literal("")),
  end_date: z.string().regex(dateFormatRegex, "Date must be in YYYY-MM format").optional().or(z.literal("")),
  responsibilities: z.array(z.string().min(1, "Responsibility cannot be empty")).optional(),
});

type WorkExperienceFormData = z.infer<typeof workExperienceSchema>;

interface WorkExperienceFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: WorkExperienceFormData) => Promise<void>;
  initialData?: Partial<WorkExperienceFormData>;
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

  const form = useForm<WorkExperienceFormData>({
    resolver: zodResolver(workExperienceSchema),
    defaultValues: {
      company_name: "",
      position_title: "",
      employment_type: "full_time",
      location: "",
      start_date: "",
      end_date: "",
      responsibilities: [],
    },
  });

  // Reset form when initialData changes (for edit mode)
  useEffect(() => {
    if (open && initialData) {
      form.reset({
        company_name: initialData.company_name || "",
        position_title: initialData.position_title || "",
        employment_type: initialData.employment_type || "full_time",
        location: initialData.location || "",
        start_date: initialData.start_date || "",
        end_date: initialData.end_date || "",
        responsibilities: initialData.responsibilities || [],
      });
    } else if (open && !initialData) {
      // Reset to empty form for create mode
      form.reset({
        company_name: "",
        position_title: "",
        employment_type: "full_time",
        location: "",
        start_date: "",
        end_date: "",
        responsibilities: [],
      });
    }
  }, [open, initialData, form]);

  const { fields, append, remove } = useFieldArray<WorkExperienceFormData, "responsibilities">({
    control: form.control,
    name: "responsibilities",
  });

  const handleSubmit = async (data: WorkExperienceFormData) => {
    setIsSubmitting(true);
    try {
      // Filter out empty responsibilities and handle date fields
      const filteredData = {
        ...data,
        responsibilities: data.responsibilities?.filter(r => r.trim() !== "") || [],
        start_date: data.start_date?.trim() || undefined,
        end_date: (data.end_date?.trim() && data.end_date.toLowerCase() !== "present") ? data.end_date.trim() : undefined,
      };
      console.log("Form data before submit:", JSON.stringify(filteredData, null, 2));
      await onSubmit(filteredData);
      form.reset();
      onOpenChange(false);
    } catch (error) {
      console.error("Error submitting work experience:", error);
    } finally {
      setIsSubmitting(false);
    }
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
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="company_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Company Name</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. Google" {...field} />
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
                      <Input placeholder="e.g. Software Engineer" {...field} />
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
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select employment type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {employmentTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
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
                      <Input placeholder="e.g. San Francisco, CA" {...field} />
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
                    <FormLabel>End Date (leave blank if current)</FormLabel>
                    <FormControl>
                      <Input placeholder="YYYY-MM" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-2">
              <FormLabel>Key Responsibilities & Achievements</FormLabel>
              <div className="space-y-2">
                {fields.map((field, index) => (
                  <div key={field.id} className="flex gap-2">
                    <FormField
                      control={form.control}
                      name={`responsibilities.${index}`}
                      render={({ field }) => (
                        <FormItem className="flex-1">
                          <FormControl>
                            <Textarea
                              placeholder="Describe a key responsibility or achievement..."
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
                Add Responsibility
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
                {mode === "create" ? "Add Experience" : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}