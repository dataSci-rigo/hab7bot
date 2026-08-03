import {
  addDays,
  addWeeks,
  getISOWeek,
  getISOWeekYear,
  setISOWeek,
  setISOWeekYear,
  startOfISOWeek,
} from "date-fns";

export function isoWeekString(date: Date): string {
  const week = getISOWeek(date);
  const year = getISOWeekYear(date);
  return `${year}-W${String(week).padStart(2, "0")}`;
}

export function currentIsoWeek(): string {
  return isoWeekString(new Date());
}

export function parseIsoWeek(iso: string): Date {
  const [yearStr, weekStr] = iso.split("-W");
  let date = setISOWeekYear(new Date(), Number(yearStr));
  date = setISOWeek(date, Number(weekStr));
  return startOfISOWeek(date);
}

export function isoWeekDays(iso: string): Date[] {
  const monday = parseIsoWeek(iso);
  return Array.from({ length: 7 }, (_, i) => addDays(monday, i));
}

export function shiftIsoWeek(iso: string, deltaWeeks: number): string {
  return isoWeekString(addWeeks(parseIsoWeek(iso), deltaWeeks));
}
