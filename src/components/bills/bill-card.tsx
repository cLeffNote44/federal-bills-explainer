import Link from "next/link";
import { ArrowRight, Scale, Calendar, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { Bill, Sponsor } from "@/types";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

const STATUS_COLORS: Record<string, string> = {
  became_law: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  passed_house: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  passed_senate: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  enrolled: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
  in_committee: "bg-zinc-500/10 text-zinc-700 dark:text-zinc-400",
  introduced: "bg-zinc-500/10 text-zinc-600 dark:text-zinc-400",
  vetoed: "bg-red-500/10 text-red-700 dark:text-red-400",
};

const STATUS_LABELS: Record<string, string> = {
  became_law: "Became Law",
  passed_house: "Passed House",
  passed_senate: "Passed Senate",
  enrolled: "Enrolled",
  in_committee: "In Committee",
  introduced: "Introduced",
  vetoed: "Vetoed",
};

export function BillCard({ bill }: { bill: Bill }) {
  const sponsor = bill.sponsor as Sponsor | null;
  const identifier = `${bill.billType.toUpperCase()}-${bill.number}`;
  const href = `/bills/${bill.congress}/${bill.billType}/${bill.number}`;

  return (
    <Link href={href}>
      <Card className="group relative overflow-hidden border-border/50 p-4 transition-all hover:border-border hover:shadow-md dark:hover:border-border/80">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            {/* Identifier + Status */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-medium text-muted-foreground">
                {identifier}
              </span>
              <Badge
                variant="secondary"
                className={cn(
                  "text-[10px] font-medium uppercase tracking-wider",
                  STATUS_COLORS[bill.status] ?? STATUS_COLORS.introduced
                )}
              >
                {STATUS_LABELS[bill.status] ?? bill.status}
              </Badge>
              {bill.publicLawNumber && (
                <Badge variant="outline" className="text-[10px]">
                  <Scale className="mr-1 size-2.5" />
                  {bill.publicLawNumber}
                </Badge>
              )}
            </div>

            {/* Title */}
            <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-foreground group-hover:text-primary">
              {bill.title}
            </h3>

            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              {sponsor && (
                <span className="flex items-center gap-1">
                  <User className="size-3" />
                  {sponsor.name}
                  <span className="text-[10px]">
                    ({sponsor.party}-{sponsor.state})
                  </span>
                </span>
              )}
              <span className="flex items-center gap-1">
                <Calendar className="size-3" />
                {bill.congress}th Congress
              </span>
              {bill.latestActionDate && (
                <span>
                  {format(new Date(bill.latestActionDate), "MMM d, yyyy")}
                </span>
              )}
            </div>
          </div>

          {/* Arrow */}
          <ArrowRight className="size-4 shrink-0 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
        </div>
      </Card>
    </Link>
  );
}
