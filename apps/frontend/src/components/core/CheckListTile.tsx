import { ReactNode } from "react";
import { Label } from "../ui/label";
import { Checkbox } from "../ui/checkbox";

interface CheckListTileParams {
  isChecked: boolean;
  /// If onCheck is not passed in, CheckListTile will be disabled.
  onCheckedChange?: (newState: boolean) => void;
  title: ReactNode;
  subtitle?: ReactNode;
}

export default function CheckListTile(params: CheckListTileParams) {
  const { isChecked, onCheckedChange, title, subtitle } = params;
  const titleIsString = typeof title === "string";
  const subtitleIsString = typeof subtitle === "string";
  return (
    <Label className="hover:bg-accent/50 flex items-start gap-3 rounded-lg border p-3 has-[[aria-checked=true]]:border-blue-600 has-[[aria-checked=true]]:bg-blue-50 dark:has-[[aria-checked=true]]:border-blue-900 dark:has-[[aria-checked=true]]:bg-blue-950">
      <Checkbox
        id="toggle-2"
        checked={isChecked}
        onCheckedChange={onCheckedChange}
        className="data-[state=checked]:border-blue-600 data-[state=checked]:bg-blue-600 data-[state=checked]:text-white dark:data-[state=checked]:border-blue-700 dark:data-[state=checked]:bg-blue-700"
      />
      <div className="grid gap-1.5 font-normal">
        {titleIsString ? (
          <p className="text-sm leading-none font-medium">{title}</p>
        ) : (
          title
        )}
        {subtitleIsString ? (
          <p className="text-muted-foreground text-sm">{subtitle}</p>
        ) : (
          subtitle
        )}
      </div>
    </Label>
  );
}
