import Link from "next/link";

const ITEMS = [
  { href: "/", label: "통합 관제", key: "dashboard", enabled: true },
  { href: "/history", label: "진단 이력", key: "history", enabled: true },
  { href: "/knowledge", label: "기술지식", key: "knowledge", enabled: true },
  { href: "/models", label: "AI 모델", key: "models", enabled: true },
  { href: "/system", label: "시스템", key: "system", enabled: true },
] as const;

export function AppNavigation({ active }: { active: "dashboard" | "history" | "knowledge" | "models" | "system" }) {
  return (
    <nav aria-label="주요 메뉴">
      {ITEMS.map((item) => item.enabled ? (
        <Link className={active === item.key ? "active" : ""} href={item.href} key={item.key}>
          {item.label}
        </Link>
      ) : <button disabled key={item.key}>{item.label}</button>)}
    </nav>
  );
}
