"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Container } from "@/components/layout/container";
import { BillList } from "@/components/bills/bill-list";
import { ArrowLeft, Tag } from "lucide-react";

export default function TopicBillsPage({
  params,
}: {
  params: Promise<{ topic: string }>;
}) {
  const { topic } = use(params);
  const decodedTopic = decodeURIComponent(topic);

  const { data, isLoading } = useQuery({
    queryKey: ["topic-bills", decodedTopic],
    queryFn: async () => {
      const res = await fetch(
        `/api/topics/${encodeURIComponent(decodedTopic)}?pageSize=50`
      );
      if (!res.ok) throw new Error("Failed to fetch topic bills");
      return res.json();
    },
  });

  return (
    <Container className="py-6">
      <Link
        href="/topics"
        className="mb-4 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3" />
        All topics
      </Link>

      <div className="mb-6 flex items-center gap-2">
        <Tag className="size-5 text-primary" />
        <h1 className="text-xl font-bold">{decodedTopic}</h1>
        {data?.total != null && (
          <span className="text-sm text-muted-foreground">
            ({data.total} bill{data.total !== 1 ? "s" : ""})
          </span>
        )}
      </div>

      <BillList
        bills={data?.bills ?? []}
        isLoading={isLoading}
        emptyMessage={`No bills found for "${decodedTopic}".`}
      />
    </Container>
  );
}
