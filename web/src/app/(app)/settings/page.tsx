"use client";

import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import {
  useGoogleStatus,
  useMe,
  useSettings,
  useTriggerGoogleSync,
  useUpdateSettings,
} from "@/lib/hooks";
import type { AppSettingsUpdate } from "@/lib/api-client";

function GoogleSyncSection() {
  const { data: status, isLoading } = useGoogleStatus();
  const { data: settings } = useSettings();
  const updateSettings = useUpdateSettings();
  const triggerSync = useTriggerGoogleSync();

  async function handleSyncNow() {
    const result = await triggerSync.mutateAsync();
    if (result.ok) {
      toast.success("Synced with Google");
    } else {
      toast.error(result.reason ?? "Sync failed");
    }
  }

  return (
    <section className="space-y-2">
      <Label>Google Calendar & Tasks sync</Label>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Checking…</p>
      ) : status?.connected ? (
        <p className="text-sm text-muted-foreground">
          Connected
          {status.last_synced_at
            ? ` · last synced ${new Date(status.last_synced_at).toLocaleString()}`
            : " · never synced yet"}
        </p>
      ) : (
        <p className="text-sm text-muted-foreground">
          Not connected. Run{" "}
          <code className="rounded bg-muted px-1">python -m scripts.google_oauth_setup</code>{" "}
          locally to authorize (opens a browser — can&apos;t be run on a headless server).
        </p>
      )}

      <div className="flex items-center gap-2">
        <Checkbox
          id="google-sync-enabled"
          checked={settings?.google_sync_enabled ?? true}
          onCheckedChange={(checked) =>
            updateSettings.mutate({ google_sync_enabled: checked === true })
          }
        />
        <Label htmlFor="google-sync-enabled" className="text-sm font-normal">
          Sync automatically
        </Label>
      </div>

      <Button
        size="sm"
        variant="outline"
        onClick={handleSyncNow}
        disabled={!status?.connected || triggerSync.isPending}
      >
        {triggerSync.isPending ? "Syncing…" : "Sync now"}
      </Button>
    </section>
  );
}

function ScheduledJobTimesSection() {
  const { data: settings } = useSettings();
  const updateSettings = useUpdateSettings();

  async function handleChange(field: keyof AppSettingsUpdate, value: string) {
    await updateSettings.mutateAsync({ [field]: value });
    toast.success("Settings saved");
  }

  return (
    <section className="space-y-4">
      <Label>Proactive check-ins</Label>

      <div className="space-y-2">
        <Label className="text-sm font-normal text-muted-foreground">Morning brief time</Label>
        <Input
          type="time"
          className="w-32"
          value={settings?.morning_brief_time ?? "07:30"}
          onChange={(e) => handleChange("morning_brief_time", e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-normal text-muted-foreground">Evening check-in time</Label>
        <Input
          type="time"
          className="w-32"
          value={settings?.evening_checkin_time ?? "21:00"}
          onChange={(e) => handleChange("evening_checkin_time", e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-normal text-muted-foreground">
          Weekly review generation time (Sunday)
        </Label>
        <Input
          type="time"
          className="w-32"
          value={settings?.weekly_review_time ?? "16:00"}
          onChange={(e) => handleChange("weekly_review_time", e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-normal text-muted-foreground">
          Weekly planning prompt time (Sunday)
        </Label>
        <Input
          type="time"
          className="w-32"
          value={settings?.weekly_planning_time ?? "17:00"}
          onChange={(e) => handleChange("weekly_planning_time", e.target.value)}
        />
      </div>
    </section>
  );
}

export default function SettingsPage() {
  const { data: settings } = useSettings();
  const { data: me } = useMe();
  const updateSettings = useUpdateSettings();
  // Google sync is owner-only (the OAuth token is the owner's; the API
  // returns 403 for anyone else) — hide the section rather than render
  // controls that can only fail.
  const isOwner = me?.role === "owner";

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-lg font-semibold">Settings</h1>

      <section className="space-y-2">
        <Label>Week starts on</Label>
        <Select
          value={settings?.week_start_day ?? "monday"}
          onValueChange={async (v) => {
            await updateSettings.mutateAsync({ week_start_day: v });
            toast.success("Settings saved");
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="monday">Monday</SelectItem>
            <SelectItem value="sunday">Sunday</SelectItem>
          </SelectContent>
        </Select>
      </section>

      {isOwner && (
        <>
          <Separator />
          <GoogleSyncSection />
        </>
      )}

      <Separator />

      <ScheduledJobTimesSection />

      <Separator />

      <section className="space-y-4 opacity-50">
        <p className="text-xs text-muted-foreground">
          The following settings arrive with their owning features in later phases.
        </p>

        <div className="space-y-2">
          <Label>Telegram pairing</Label>
          <p className="text-sm">Bot configured (live status check not yet built)</p>
        </div>

        <div className="space-y-2">
          <Label>Anthropic model</Label>
          <Input disabled placeholder="claude-sonnet-4-6" />
        </div>

        <div className="space-y-2">
          <Label>Data export</Label>
          <Button disabled variant="outline" size="sm">
            Export JSON
          </Button>
        </div>
      </section>
    </div>
  );
}
