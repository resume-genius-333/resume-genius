"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
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
import { Loader2 } from "lucide-react";
import { DegreeType } from "@/lib/api/generated/schemas";
import { getProfileEducationApiV1ProfileEducationsEducationIdGetResponse } from "@/lib/api/generated/api.zod";

const degreeTypes: Record<DegreeType, string> = {
  high_school: "High School",
  associate: "Associate",
  bachelor: "Bachelor's",
  master: "Master's",
  doctorate: "Doctorate",
  professional: "Professional",
  certificate: "Certificate",
  diploma: "Diploma",
  exchange: "Exchange",
  other: "Other",
};

const educationFormSchemaWithoutId =
  getProfileEducationApiV1ProfileEducationsEducationIdGetResponse.omit({
    id: true,
    user_id: true,
    job_id: true,
    parent_id: true,
    created_at: true,
    updated_at: true,
  });

const educationFormSchema = educationFormSchemaWithoutId.extend({
  focus_area: z.string(),
  start_date: z.string(),
  end_date: z.string(),
  gpa: z.number(),
  max_gpa: z.number(),
});

type EducationFormData = z.infer<typeof educationFormSchema>;

const educationFormInputConverter =
  educationFormSchemaWithoutId.transform<EducationFormData>((data) => {
    return {
      ...data,
      focus_area: data.focus_area || "",
      start_date: data.start_date || "",
      end_date: data.end_date || "",
      gpa: data.gpa || 0,
      max_gpa: data.max_gpa || 0,
    };
  });

type EducationFormInput = z.input<typeof educationFormInputConverter>;

type EducationFormInput2 = z.input<typeof educationFormSchemaWithoutId>;

interface EducationFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: EducationFormData) => Promise<void>;
  initialData?: EducationFormInput;
  mode: "create" | "edit";
}

export function EducationForm({
  open,
  onOpenChange,
  onSubmit,
  initialData: initialInputData,
  mode,
}: EducationFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const initialData = initialInputData
    ? educationFormInputConverter.parse(initialInputData)
    : null;
  const form = useForm<EducationFormData>({
    resolver: zodResolver(educationFormSchema),
    defaultValues: {
      institution_name: initialData?.institution_name || "",
      degree: initialData?.degree || "bachelor",
      field_of_study: initialData?.field_of_study || "",
      focus_area: initialData?.focus_area || "",
      start_date: initialData?.start_date || "",
      end_date: initialData?.end_date || "",
      gpa: initialData?.gpa,
      max_gpa: initialData?.max_gpa || 4.0,
    },
  });

  // Reset form when initialData changes (for edit mode)
  useEffect(() => {
    if (open && initialData) {
      form.reset({
        institution_name: initialData.institution_name || "",
        degree: initialData.degree || "bachelor",
        field_of_study: initialData.field_of_study || "",
        focus_area: initialData.focus_area || "",
        start_date: initialData.start_date || "",
        end_date: initialData.end_date || "",
        gpa: initialData.gpa,
        max_gpa: initialData.max_gpa || 4.0,
      });
    } else if (open && !initialData) {
      // Reset to empty form for create mode
      form.reset({
        institution_name: "",
        degree: "bachelor",
        field_of_study: "",
        focus_area: "",
        start_date: "",
        end_date: "",
        gpa: undefined,
        max_gpa: 4.0,
      });
    }
  }, [open, initialData, form]);

  const handleSubmit = async (data: EducationFormData) => {
    setIsSubmitting(true);
    try {
      // Handle date fields properly
      const filteredData = {
        ...data,
        start_date: data.start_date?.trim() || undefined,
        end_date: data.end_date?.trim() || undefined,
        gpa: data.gpa || undefined,
        max_gpa: data.max_gpa || undefined,
      };
      await onSubmit(educationFormSchema.parse(filteredData));
      form.reset();
      onOpenChange(false);
    } catch (error) {
      console.error("Error submitting education:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Add Education" : "Edit Education"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add your educational background"
              : "Update your education information"}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="institution_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Institution Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Harvard University" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="degree"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Degree Type</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select degree type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.keys(degreeTypes).map((key) => (
                          <SelectItem key={key} value={key}>
                            {degreeTypes[key as DegreeType]}
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
                name="field_of_study"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Field of Study</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. Computer Science" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="focus_area"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Focus Area (Optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Machine Learning" {...field} />
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
                    <FormLabel>End Date (or Expected)</FormLabel>
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
                name="gpa"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>GPA (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="3.85"
                        {...field}
                        onChange={(e) =>
                          field.onChange(parseFloat(e.target.value))
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="max_gpa"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max GPA</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="4.0"
                        {...field}
                        onChange={(e) =>
                          field.onChange(parseFloat(e.target.value))
                        }
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
                {mode === "create" ? "Add Education" : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
