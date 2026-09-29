"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment } from "react";
import { getToolGuide } from "@/lib/tool-guides";
import { getCategory, getTool } from "@/lib/tools-catalog";

function labelFor(segment: string, index: number, parts: string[]): string {
  if (segment === "tools") {
    return "Tools";
  }
  if (segment === "learn") {
    return "Lessons";
  }
  if (parts[0] === "tools" && index === 1) {
    return getCategory(segment)?.title ?? segment;
  }
  if (parts[0] === "tools" && index === 2) {
    return getTool(parts[1] ?? "", segment)?.tool.name ?? segment;
  }
  if (parts[0] === "tools" && index === 3) {
    const match = getToolGuide(parts[1] ?? "", parts[2] ?? "", segment);
    if (match) {
      return match.guide.signature ?? match.guide.title;
    }
  }
  return segment
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function Breadcrumbs(): React.JSX.Element | null {
  const pathname = usePathname();
  if (!pathname || pathname === "/") {
    return null;
  }

  const parts = pathname.split("/").filter(Boolean);
  const crumbs = [
    { href: "/", label: "Home" },
    ...parts.map((segment, index) => {
      const href = `/${parts.slice(0, index + 1).join("/")}`;
      return { href, label: labelFor(segment, index, parts) };
    }),
  ];

  return (
    <nav aria-label="Breadcrumb" className="min-w-0">
      <ol className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
        {crumbs.map((crumb, index) => {
          const last = index === crumbs.length - 1;
          return (
            <Fragment key={crumb.href}>
              {index > 0 ? (
                <span aria-hidden className="px-0.5 text-muted-foreground/50">
                  /
                </span>
              ) : null}
              <li className="min-w-0 truncate">
                {last ? (
                  <span className="font-medium text-foreground" aria-current="page">
                    {crumb.label}
                  </span>
                ) : (
                  <Link href={crumb.href} className="transition-colors hover:text-foreground">
                    {crumb.label}
                  </Link>
                )}
              </li>
            </Fragment>
          );
        })}
      </ol>
    </nav>
  );
}
