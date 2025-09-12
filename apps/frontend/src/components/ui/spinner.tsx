import { cn } from "@/lib/utils";
// cn is a utility from shadcn/ui for conditionally joining class names

export function Spinner() {
  return (
    <div
      className={cn(
        "h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent"
      )}
    />
  );
}
