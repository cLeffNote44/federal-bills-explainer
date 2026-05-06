"use client";

import { useState } from "react";
import { Container } from "@/components/layout/container";
import { useAuth } from "@/hooks/use-auth";
import { useProfile, useUpdateProfile } from "@/hooks/use-profile";
import { useUIStore } from "@/stores/ui-store";
import { Loader2, LogOut, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import type { User } from "@supabase/supabase-js";

interface ProfileShape {
  displayName?: string | null;
  zipCode?: string | null;
  state?: string | null;
  emailNotifications?: boolean | null;
  notificationFrequency?: "realtime" | "daily" | "weekly" | null;
}

export default function SettingsPage() {
  const { user, loading: authLoading, signOut } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);

  if (authLoading) {
    return (
      <Container className="flex items-center justify-center py-24">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </Container>
    );
  }

  if (!user) {
    return (
      <Container className="flex flex-col items-center justify-center gap-4 py-24">
        <Settings className="size-10 text-muted-foreground/40" />
        <p className="text-sm text-muted-foreground">Sign in to manage your settings.</p>
        <Button onClick={() => openAuthModal("login")}>Sign In</Button>
      </Container>
    );
  }

  return <SettingsForm user={user} signOut={signOut} />;
}

function SettingsForm({
  user,
  signOut,
}: {
  user: User;
  signOut: () => Promise<void>;
}) {
  const { data: profile, isLoading } = useProfile(user.id);

  if (isLoading) {
    return (
      <Container className="flex items-center justify-center py-24">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </Container>
    );
  }

  // Re-mount the editable form whenever the loaded profile shape changes
  // so initial state is always seeded from the latest server data without
  // needing to call setState inside an effect.
  return (
    <ProfileEditor
      key={profileCacheKey(profile)}
      user={user}
      profile={profile ?? {}}
      signOut={signOut}
    />
  );
}

function profileCacheKey(profile: ProfileShape | undefined) {
  if (!profile) return "empty";
  return [
    profile.displayName ?? "",
    profile.zipCode ?? "",
    profile.state ?? "",
    profile.emailNotifications ?? "",
    profile.notificationFrequency ?? "",
  ].join("|");
}

function ProfileEditor({
  user,
  profile,
  signOut,
}: {
  user: User;
  profile: ProfileShape;
  signOut: () => Promise<void>;
}) {
  const updateProfile = useUpdateProfile();
  const [displayName, setDisplayName] = useState(profile.displayName ?? "");
  const [zipCode, setZipCode] = useState(profile.zipCode ?? "");
  const [state, setState] = useState(profile.state ?? "");
  const [emailNotifications, setEmailNotifications] = useState(
    profile.emailNotifications ?? true
  );
  const [notificationFrequency, setNotificationFrequency] = useState<
    "realtime" | "daily" | "weekly"
  >(profile.notificationFrequency ?? "daily");
  const [saved, setSaved] = useState(false);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    updateProfile.mutate(
      {
        displayName: displayName || undefined,
        zipCode: zipCode || undefined,
        state: state || undefined,
        emailNotifications,
        notificationFrequency,
      },
      {
        onSuccess: () => {
          setSaved(true);
          setTimeout(() => setSaved(false), 2000);
        },
      }
    );
  }

  return (
    <Container className="py-6">
      <div className="mb-6 flex items-center gap-2">
        <Settings className="size-5 text-primary" />
        <h1 className="text-xl font-bold">Settings</h1>
      </div>

      <form onSubmit={handleSave} className="max-w-xl space-y-4">
        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold">Account</h2>
          <p className="mb-4 text-xs text-muted-foreground">{user.email}</p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => signOut()}
            className="gap-1.5"
          >
            <LogOut className="size-3.5" />
            Sign out
          </Button>
        </Card>

        <Card className="p-4 space-y-3">
          <h2 className="text-sm font-semibold">Profile</h2>
          <div className="space-y-1.5">
            <Label htmlFor="displayName">Display name</Label>
            <Input
              id="displayName"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={100}
              placeholder="Anonymous"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="zipCode">Zip code</Label>
              <Input
                id="zipCode"
                value={zipCode}
                onChange={(e) => setZipCode(e.target.value)}
                maxLength={10}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="state">State</Label>
              <Input
                id="state"
                value={state}
                onChange={(e) => setState(e.target.value.toUpperCase())}
                maxLength={2}
                placeholder="CA"
              />
            </div>
          </div>
        </Card>

        <Card className="p-4 space-y-3">
          <h2 className="text-sm font-semibold">Notifications</h2>
          <label className="flex items-center justify-between text-sm">
            <span>Email notifications</span>
            <input
              type="checkbox"
              checked={emailNotifications}
              onChange={(e) => setEmailNotifications(e.target.checked)}
              className="size-4"
            />
          </label>
          <div className="space-y-1.5">
            <Label htmlFor="frequency">Frequency</Label>
            <select
              id="frequency"
              value={notificationFrequency}
              onChange={(e) =>
                setNotificationFrequency(
                  e.target.value as "realtime" | "daily" | "weekly"
                )
              }
              disabled={!emailNotifications}
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
            >
              <option value="realtime">Real-time</option>
              <option value="daily">Daily digest</option>
              <option value="weekly">Weekly digest</option>
            </select>
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Theme</h2>
          <ThemeToggle />
        </Card>

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={updateProfile.isPending}>
            {updateProfile.isPending && (
              <Loader2 className="mr-2 size-3.5 animate-spin" />
            )}
            Save changes
          </Button>
          {saved && (
            <span className="text-xs text-muted-foreground">Saved.</span>
          )}
          {updateProfile.isError && (
            <span className="text-xs text-destructive">
              Failed to save. Try again.
            </span>
          )}
        </div>
      </form>
    </Container>
  );
}
