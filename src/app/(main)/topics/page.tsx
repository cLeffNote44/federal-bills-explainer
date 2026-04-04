"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Container } from "@/components/layout/container";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tag, ArrowRight } from "lucide-react";

export default function TopicsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["topics"],
    queryFn: async () => {
      const res = await fetch("/api/topics?pageSize=50");
      if (!res.ok) throw new Error("Failed to fetch topics");
      return res.json();
    },
  });

  const topics = data?.topics ?? [];

  return (
    <Container className="py-6">
      <div className="mb-6 space-y-2">
        <div className="flex items-center gap-2">
          <Tag className="size-5 text-primary" />
          <h1 className="text-xl font-bold">Topics</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Browse bills by policy area and subject matter.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {topics.map((topic: { name: string; count: number }) => (
            <Link key={topic.name} href={`/topics/${encodeURIComponent(topic.name)}`}>
              <Card className="group flex items-center justify-between p-4 transition-all hover:border-border hover:shadow-sm">
                <div>
                  <h3 className="text-sm font-semibold group-hover:text-primary">
                    {topic.name}
                  </h3>
                  <Badge variant="secondary" className="mt-1 text-[10px]">
                    {topic.count} bill{topic.count !== 1 ? "s" : ""}
                  </Badge>
                </div>
                <ArrowRight className="size-4 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </Container>
  );
}
