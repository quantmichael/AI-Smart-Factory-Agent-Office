import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./styles.css";

export const metadata: Metadata = {
  title: "AI Smart Factory Agent Office",
  description: "실데이터 기반 설비 이상탐지와 근거 중심 진단을 위한 AI 스마트 팩토리 에이전트 오피스",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
