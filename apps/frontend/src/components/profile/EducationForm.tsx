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
import { Loader2 } from "lucide-react";
import { DegreeType } from "@/lib/api/generated/schemas";
import {
  createProfileEducationApiV1ProfileEducationsPostBody,
  getProfileEducationApiV1ProfileEducationsEducationIdGetResponse,
} from "@/lib/api/generated/api.zod";
import { NormalizationDefaultValues, useZodForm } from "@/hooks/use-zod-form";

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

const educationFormSchema =
  createProfileEducationApiV1ProfileEducationsPostBody;

type EducationFormValues = z.infer<typeof educationFormSchema>;

type EducationFormInitial = z.infer<
  typeof getProfileEducationApiV1ProfileEducationsEducationIdGetResponse
>;

const EDUCATION_DEFAULTS: NormalizationDefaultValues<EducationFormValues> = {
  focus_area: "",
  start_date: "",
  end_date: "",
  gpa: Number.NaN,
  max_gpa: 4,
};

interface EducationFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: EducationFormValues) => Promise<void>;
  initialData?: EducationFormInitial;
  mode: "create" | "edit";
}

export function EducationForm({
  open,
  onOpenChange,
  onSubmit,
  initialData,
  mode,
}: EducationFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const initialValues = useMemo<EducationFormValues>(() => {
    const base: EducationFormValues = {
      institution_name: initialData?.institution_name ?? "",
      degree: (initialData?.degree as DegreeType | undefined) ?? "bachelor",
      field_of_study: initialData?.field_of_study ?? "",
      max_gpa: initialData?.max_gpa ?? EDUCATION_DEFAULTS.max_gpa,
    };

    if (
      initialData?.focus_area !== undefined &&
      initialData.focus_area !== null
    ) {
      base.focus_area = initialData.focus_area;
    }
    if (initialData?.start_date) {
      base.start_date = initialData.start_date;
    }
    if (initialData?.end_date) {
      base.end_date = initialData.end_date;
    }
    if (initialData?.gpa !== undefined && initialData?.gpa !== null) {
      base.gpa = initialData.gpa;
    }

    return base;
  }, [initialData]);

  const { form, submit } = useZodForm({
    zodObject: educationFormSchema,
    initial: initialValues,
    defaults: EDUCATION_DEFAULTS,
    onUpdate: async (values) => {
      setIsSubmitting(true);
      try {
        const payload: EducationFormValues = {
          ...values,
          gpa:
            typeof values.gpa === "number" && !Number.isNaN(values.gpa)
              ? values.gpa
              : undefined,
        };

        await onSubmit(payload);
        if (mode === "create") {
          form.reset();
        }
        onOpenChange(false);
      } catch (error) {
        console.error("Error submitting education:", error);
      } finally {
        setIsSubmitting(false);
      }
    },
  });

  const degreeOptions = useMemo(() => Object.entries(degreeTypes), []);

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
          <form onSubmit={submit} className="space-y-4">
            <FormField
              control={form.control}
              name="institution_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Institution Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g. Harvard University"
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
                name="degree"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Degree Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select degree type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {degreeOptions.map(([value, label]) => (
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
                name="field_of_study"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Field of Study</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g. Computer Science"
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
              name="focus_area"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Focus Area (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g. Artificial Intelligence"
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
                    <FormLabel>End Date (or Expected)</FormLabel>
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
                name="gpa"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>GPA (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="3.85"
                        value={
                          typeof field.value === "number" &&
                          !Number.isNaN(field.value)
                            ? field.value
                            : ""
                        }
                        onChange={(event) => {
                          const raw = event.target.value;
                          if (raw === "") {
                            field.onChange(EDUCATION_DEFAULTS.gpa);
                            return;
                          }
                          const parsed = Number(raw);
                          field.onChange(
                            Number.isNaN(parsed)
                              ? EDUCATION_DEFAULTS.gpa
                              : parsed
                          );
                        }}
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
                        value={
                          typeof field.value === "number" &&
                          !Number.isNaN(field.value)
                            ? field.value
                            : ""
                        }
                        onChange={(event) => {
                          const raw = event.target.value;
                          if (raw === "") {
                            field.onChange(EDUCATION_DEFAULTS.max_gpa);
                            return;
                          }
                          const parsed = Number(raw);
                          field.onChange(
                            Number.isNaN(parsed)
                              ? EDUCATION_DEFAULTS.max_gpa
                              : parsed
                          );
                        }}
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
