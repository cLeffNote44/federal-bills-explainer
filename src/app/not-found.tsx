import Link from "next/link";
import { FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4">
      <FileQuestion className="size-12 text-muted-foreground/40" />
      <h1 className="text-lg font-bold">Page Not Found</h1>
      <p className="text-sm text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist.
      </p>
      <Link href="/">
        <Button size="sm">Back to Home</Button>
      </Link>
    </div>
  );
}
