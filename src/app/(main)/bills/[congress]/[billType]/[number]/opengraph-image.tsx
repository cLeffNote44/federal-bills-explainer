import { ImageResponse } from "next/og";
import { db } from "@/lib/db";
import { bills } from "@/lib/db/schema";
import { eq, and } from "drizzle-orm";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const runtime = "nodejs";

export default async function OGImage({
  params,
}: {
  params: Promise<{ congress: string; billType: string; number: string }>;
}) {
  const { congress, billType, number } = await params;

  const bill = await db.query.bills.findFirst({
    where: and(
      eq(bills.congress, Number(congress)),
      eq(bills.billType, billType),
      eq(bills.number, Number(number))
    ),
  });

  const title = bill?.title ?? "Bill Not Found";
  const identifier = `${billType.toUpperCase()}-${number}`;
  const status = bill?.status?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) ?? "";

  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "60px 80px",
          width: "100%",
          height: "100%",
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          color: "white",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
          <div
            style={{
              fontSize: "16px",
              fontWeight: 600,
              color: "#94a3b8",
              fontFamily: "monospace",
            }}
          >
            {identifier} — {congress}th Congress
          </div>
          {status && (
            <div
              style={{
                fontSize: "14px",
                fontWeight: 500,
                color: "#22c55e",
                background: "rgba(34, 197, 94, 0.1)",
                padding: "4px 12px",
                borderRadius: "6px",
              }}
            >
              {status}
            </div>
          )}
        </div>
        <div
          style={{
            fontSize: "40px",
            fontWeight: 700,
            lineHeight: 1.2,
            maxHeight: "240px",
            overflow: "hidden",
          }}
        >
          {title}
        </div>
        <div
          style={{
            marginTop: "auto",
            fontSize: "18px",
            color: "#94a3b8",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Federal Bills Explainer — AI-powered legislation made simple
        </div>
      </div>
    ),
    { ...size }
  );
}
