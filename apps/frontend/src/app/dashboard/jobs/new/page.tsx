"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createJobApiV1JobsCreatePost } from "@/lib/api/generated/api";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import z from "zod";

const newJobFormSchema = z.object({
  jobUrl: z.url(),
  jobDescription: z.string(),
});

type JobFormSchema = z.infer<typeof newJobFormSchema>;

export default function NewJobPage() {
  const router = useRouter();
  const form = useForm<JobFormSchema>({
    resolver: zodResolver(newJobFormSchema),
  });
  async function onSubmit(input: JobFormSchema) {
    const result = await createJobApiV1JobsCreatePost({
      job_description: input.jobDescription,
      job_url: input.jobUrl,
    });
    router.push(`/jobs/${result.job_id}`);
  }
  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="w-1/2">
        <CardHeader>
          <CardTitle>Create a New Job</CardTitle>
          <CardDescription>
            Create a new job by uploading the job url and description.
          </CardDescription>
        </CardHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="jobUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Job URL</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter the Job URL" {...field} />
                    </FormControl>
                    <FormDescription>
                      We use the job url to fetch jobs.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="jobDescription"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Job Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Enter the Job Description"
                        className="h-32"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      We use the job description to help analyze your resume.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="mt-4 flex">
              <Button type="submit" className="w-full">
                Click Me
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>
    </div>
  );
}
