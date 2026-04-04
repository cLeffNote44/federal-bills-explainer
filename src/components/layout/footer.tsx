import { Landmark } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-muted/30">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-2 px-4 py-6 text-center text-sm text-muted-foreground sm:flex-row sm:justify-between sm:px-6 lg:px-8">
        <div className="flex items-center gap-1.5">
          <Landmark className="size-3.5" />
          <span>Federal Bills Explainer</span>
        </div>
        <p>
          Data sourced from{" "}
          <a
            href="https://api.congress.gov"
            className="underline underline-offset-2 hover:text-foreground"
            target="_blank"
            rel="noopener noreferrer"
          >
            Congress.gov
          </a>
          . AI explanations are for educational purposes only.
        </p>
      </div>
    </footer>
  );
}
