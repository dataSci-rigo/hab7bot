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
import { Separator } from "@/components/ui/separator";
import { useSettings, useUpdateSettings } from "@/lib/hooks";

export default function SettingsPage() {
  const { data: settings } = useSettings();
  const updateSettings = useUpdateSettings();

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-lg font-semibold">Settings</h1>

      <section className="space-y-2">
        <Label>Week starts on</Label>
        <Select
          value={settings?.week_start_day ?? "monday"}
          onValueChange={async (v) => {
            await updateSettings.mutateAsync(v);
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

      <Separator />

      <section className="space-y-4 opacity-50">
        <p className="text-xs text-muted-foreground">
          The following settings arrive with their owning features in later phases.
        </p>

        <div className="space-y-2">
          <Label>Telegram pairing</Label>
          <p className="text-sm">Not connected (Phase 4)</p>
        </div>

        <div className="space-y-2">
          <Label>Morning check-in time</Label>
          <Input disabled placeholder="7:30 AM" />
        </div>

        <div className="space-y-2">
          <Label>Evening check-in time</Label>
          <Input disabled placeholder="9:00 PM" />
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
