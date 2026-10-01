import type { ReactNode } from "react";

import { AppNavigation } from "@/components/AppNavigation";

export function AppHeader({ active, status }: { active: "dashboard" | "history" | "knowledge" | "models" | "system"; status: ReactNode }) {
  return (
    <header className="topbar">
      <div className="brand"><span className="brand-mark"><i /><i /><i /></span><div><strong>AI 스마트 팩토리</strong><small>AGENT OFFICE / 베어링 셀 01</small></div></div>
      <AppNavigation active={active} />
      {status}
    </header>
  );
}
