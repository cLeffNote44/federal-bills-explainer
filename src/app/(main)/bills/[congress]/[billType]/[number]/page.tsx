"use client";

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  Scale,
  User,
  Users,
  ExternalLink,
  Building2,
  Tag,
} from "lucide-react";
import { Container } from "@/components/layout/container";
import { BillExplanation } from "@/components/bills/bill-explanation";
import { BookmarkButton } from "@/components/social/bookmark-button";
import { TrackButton } from "@/components/social/track-button";
import { ShareButton } from "@/components/social/share-button";
import { ExportButton } from "@/components/social/export-button";
import { Comments } from "@/components/social/comments";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useBillDetail } from "@/hooks/use-bills";
import { format } from "date-fns";
import type { Sponsor } from "@/types";

export default function BillDetailPage({
  params,
}: {
  params: Promise<{ congress: string; billType: string; number: string }>;
}) {
  const { congress, billType, number } = use(params);
  const {
    data: bill,
    isLoading,
    error,
  } = useBillDetail(Number(congress), billType, Number(number));

  if (isLoading) {
    return (
      <Container className="py-6">
        <Skeleton className="mb-4 h-6 w-32" />
        <Skeleton className="mb-2 h-8 w-3/4" />
        <Skeleton className="mb-6 h-4 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </Container>
    );
  }

  if (error || !bill) {
    return (
      <Container className="py-16 text-center">
        <p className="text-muted-foreground">Bill not found.</p>
        <Link href="/">
          <Button variant="outline" size="sm" className="mt-4">
            <ArrowLeft className="mr-1 size-3.5" />
            Back to browse
          </Button>
        </Link>
      </Container>
    );
  }

  const sponsor = bill.sponsor as Sponsor | null;
  const identifier = `${bill.billType.toUpperCase()}-${bill.number}`;
  const committees = bill.committees as string[] | null;
  const subjects = bill.subjects as string[] | null;

  return (
    <Container className="py-6">
      {/* Back link */}
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3" />
        Back to browse
      </Link>

      {/* Header */}
      <div className="mb-6 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-sm font-medium text-muted-foreground">
            {identifier}
          </span>
          <Badge variant="secondary" className="text-xs">
            {bill.status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </Badge>
          {bill.publicLawNumber && (
            <Badge variant="outline" className="gap-1 text-xs">
              <Scale className="size-3" />
              {bill.publicLawNumber}
            </Badge>
          )}
          <Badge variant="outline" className="text-xs">
            {congress}th Congress
          </Badge>
        </div>

        <h1 className="text-xl font-bold leading-tight sm:text-2xl">{bill.title}</h1>

        {/* Meta */}
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          {sponsor && (
            <span className="flex items-center gap-1.5">
              <User className="size-3.5" />
              {sponsor.name} ({sponsor.party}-{sponsor.state})
            </span>
          )}
          {bill.cosponsorsCount != null && bill.cosponsorsCount > 0 && (
            <span className="flex items-center gap-1.5">
              <Users className="size-3.5" />
              {bill.cosponsorsCount} cosponsor{bill.cosponsorsCount !== 1 ? "s" : ""}
            </span>
          )}
          {bill.introducedDate && (
            <span className="flex items-center gap-1.5">
              <Calendar className="size-3.5" />
              Introduced {format(new Date(bill.introducedDate), "MMM d, yyyy")}
            </span>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <BookmarkButton billId={bill.id} />
          <TrackButton billId={bill.id} />
          <ShareButton title={bill.title} />
          <ExportButton
            congress={bill.congress}
            billType={bill.billType}
            number={bill.number}
          />
          {bill.congressUrl && (
            <a
              href={bill.congressUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              Congress.gov
              <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="space-y-6 lg:col-span-2">
          {/* Summary */}
          {bill.summary && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold">Official Summary</h2>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {bill.summary}
              </p>
            </div>
          )}

          {/* AI Explanation */}
          {bill.explanation && <BillExplanation explanation={bill.explanation} />}

          {/* Latest Action */}
          {bill.latestActionText && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold">Latest Action</h2>
              <p className="text-sm text-muted-foreground">
                {bill.latestActionText}
              </p>
              {bill.latestActionDate && (
                <p className="text-xs text-muted-foreground/70">
                  {format(new Date(bill.latestActionDate), "MMMM d, yyyy")}
                </p>
              )}
            </div>
          )}

          {/* Comments */}
          <Comments billId={bill.id} />
        </div>

        {/* Sidebar */}
        <aside className="space-y-6">
          {/* Topics */}
          {bill.topics && bill.topics.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold">
                <Tag className="size-3.5" />
                Topics
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {bill.topics.map((topic) => (
                  <Link key={topic.id} href={`/topics/${encodeURIComponent(topic.topicName)}`}>
                    <Badge
                      variant="secondary"
                      className="cursor-pointer text-xs hover:bg-secondary/80"
                    >
                      {topic.topicName}
                    </Badge>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Committees */}
          {committees && committees.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold">
                <Building2 className="size-3.5" />
                Committees
              </h3>
              <ul className="space-y-1.5 text-xs text-muted-foreground">
                {committees.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Subjects */}
          {subjects && subjects.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="mb-2 text-sm font-semibold">Subjects</h3>
              <div className="flex flex-wrap gap-1">
                {subjects.map((s, i) => (
                  <Badge key={i} variant="outline" className="text-[10px]">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Policy Area */}
          {bill.policyArea && (
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="mb-2 text-sm font-semibold">Policy Area</h3>
              <p className="text-sm text-muted-foreground">{bill.policyArea}</p>
            </div>
          )}
        </aside>
      </div>
    </Container>
  );
}
