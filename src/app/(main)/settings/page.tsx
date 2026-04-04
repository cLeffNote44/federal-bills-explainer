"use client";

import { Container } from "@/components/layout/container";
import { useAuth } from "@/hooks/use-auth";
import { useUIStore } from "@/stores/ui-store";
import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function SettingsPage() {
  const { user, loading } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);

  if (!loading && !user) {
    return (
      <Container className="flex flex-col items-center justify-center gap-4 py-24">
        <Settings className="size-10 text-muted-foreground/40" />
        <p className="text-sm text-muted-foreground">Sign in to manage your settings.</p>
        <Button onClick={() => openAuthModal("login")}>Sign In</Button>
      </Container>
    );
  }

  return (
    <Container className="py-6">
      <div className="mb-6 flex items-center gap-2">
        <Settings className="size-5 text-primary" />
        <h1 className="text-xl font-bold">Settings</h1>
      </div>

      <div className="max-w-xl space-y-4">
        <Card className="p-4">
          <h2 className="mb-2 text-sm font-semibold">Account</h2>
          <p className="text-xs text-muted-foreground">{user?.email}</p>
        </Card>

        <Card className="p-4">
          <h2 className="mb-2 text-sm font-semibold">Notifications</h2>
          <p className="text-xs text-muted-foreground">
            Notification preferences will be available here.
          </p>
        </Card>

        <Card className="p-4">
          <h2 className="mb-2 text-sm font-semibold">Theme</h2>
          <p className="text-xs text-muted-foreground">
            Use the theme toggle in the header to switch between light and dark mode.
          </p>
        </Card>
      </div>
    </Container>
  );
}
