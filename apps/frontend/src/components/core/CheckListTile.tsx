import { ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { Label } from "../ui/label";
import { Checkbox } from "../ui/checkbox";

interface CheckListTileParams {
  isChecked: boolean;
  /// If onCheck is not passed in, CheckListTile will be disabled.
  onCheckedChange?: (newState: boolean) => void;
  title: ReactNode;
  subtitle?: ReactNode;
}

const MotionLabel = motion(Label);

export default function CheckListTile(params: CheckListTileParams) {
  const { isChecked, onCheckedChange, title, subtitle } = params;
  const titleIsString = typeof title === "string";
  const subtitleIsString = typeof subtitle === "string";
  return (
    <MotionLabel
      layout
      className="relative hover:bg-accent/50 flex items-center gap-3 rounded-lg border p-3 transition-colors has-[[aria-checked=true]]:border-blue-600 has-[[aria-checked=true]]:bg-blue-50 dark:has-[[aria-checked=true]]:border-blue-900 dark:has-[[aria-checked=true]]:bg-blue-950"
      animate={{
        scale: isChecked ? 1.015 : 1,
      }}
      initial={false}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.99 }}
      transition={{ type: "spring", stiffness: 350, damping: 28, mass: 0.7 }}
    >
      <div className="relative flex h-5 w-5 items-center justify-center">
        <Checkbox
          id="toggle-2"
          checked={isChecked}
          onCheckedChange={onCheckedChange}
          className="relative z-[1] data-[state=checked]:border-blue-600 data-[state=checked]:bg-blue-600 data-[state=checked]:text-white dark:data-[state=checked]:border-blue-700 dark:data-[state=checked]:bg-blue-700"
        />
      </div>
      <motion.div
        layout
        className="grid gap-1.5 font-normal"
        animate={{
          x: isChecked ? 4 : 0,
          opacity: isChecked ? 1 : 0.92,
        }}
        transition={{ type: "spring", stiffness: 250, damping: 20, mass: 0.7 }}
      >
        {titleIsString ? (
          <p className="text-sm leading-none font-medium">{title}</p>
        ) : (
          title
        )}
        <AnimatePresence mode="popLayout">
          {subtitle ? (
            <motion.div
              key="subtitle"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="text-muted-foreground text-sm"
            >
              {subtitleIsString ? <span>{subtitle}</span> : subtitle}
            </motion.div>
          ) : null}
        </AnimatePresence>
      </motion.div>
    </MotionLabel>
  );
}
