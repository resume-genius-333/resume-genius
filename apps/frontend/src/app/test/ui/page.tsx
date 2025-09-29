"use client";

import CheckListTile from "@/components/core/CheckListTile";
import { useState } from "react";

export default function TestUiPage() {
  const [isChecked, setIsChecked] = useState(false);
  return (
    <div className="flex items-center justify-center h-screen">
      <CheckListTile
        isChecked={isChecked}
        title={"checklist"}
        onCheckedChange={setIsChecked}
      />
    </div>
  );
}
