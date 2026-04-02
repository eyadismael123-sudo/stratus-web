import type { AgentSchedule } from "@/types";

type ScheduleGridData = Record<string, number[]>;

const DAY_HEADERS = ["S", "M", "T", "W", "T", "F", "S"];

function buildCalendarWeeks(gridData: ScheduleGridData): {
  date: string | null;
  dayNum: number | null;
  runCount: number;
  isToday: boolean;
}[][] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dates = Object.keys(gridData).sort();
  if (dates.length === 0) return [];

  const firstDate = new Date(dates[0]);
  // Start from Monday of the first week
  const startDay = new Date(firstDate);
  startDay.setDate(firstDate.getDate() - ((firstDate.getDay() + 6) % 7)); // Monday

  const weeks: { date: string | null; dayNum: number | null; runCount: number; isToday: boolean }[][] = [];
  let current = new Date(startDay);

  // Build 4 weeks (28 days)
  for (let week = 0; week < 4; week++) {
    const row: typeof weeks[0] = [];
    for (let d = 0; d < 7; d++) {
      const isoDate = current.toISOString().slice(0, 10);
      const runCount = (gridData[isoDate] ?? []).length;
      const isToday = current.getTime() === today.getTime();
      // Show Sunday (d=0) as weekend — skip by making it inactive
      const isWeekend = current.getDay() === 0 || current.getDay() === 6;
      row.push({
        date: isoDate,
        dayNum: current.getDate(),
        runCount: isWeekend ? 0 : runCount,
        isToday,
      });
      current = new Date(current);
      current.setDate(current.getDate() + 1);
    }
    weeks.push(row);
  }

  return weeks;
}

function parseCron(cron: string): string {
  // "0 8 * * *" → "8:00 AM daily"
  const parts = cron.split(" ");
  if (parts.length < 2) return cron;
  const minute = parts[0];
  const hour = parseInt(parts[1], 10);
  if (isNaN(hour)) return cron;
  const ampm = hour >= 12 ? "PM" : "AM";
  const h = hour % 12 === 0 ? 12 : hour % 12;
  const m = minute.padStart(2, "0");
  return `${h}:${m} ${ampm}`;
}

interface ScheduleGridProps {
  schedule: AgentSchedule;
  gridData: ScheduleGridData;
}

export function ScheduleGrid({ schedule, gridData }: ScheduleGridProps) {
  const weeks = buildCalendarWeeks(gridData);
  const runTime = parseCron(schedule.cron_expression);

  return (
    <div className="bg-white rounded-[12px] p-[18px] border border-black/[0.06] shadow-[0_1px_3px_rgba(0,0,0,0.06)]">
      {/* Card title */}
      <div className="flex items-center gap-2 text-[13px] font-bold text-[#3A3A3C] mb-3.5">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="1" y="2" width="12" height="11" rx="1.5"/>
          <path d="M1 5.5h12M4.5 1v2M9.5 1v2"/>
        </svg>
        Run Schedule
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1 mb-3">
        {DAY_HEADERS.map((h, i) => (
          <div
            key={`${h}-${i}`}
            className="text-[10px] font-semibold text-[#8E8E93] text-center py-0.5"
          >
            {h}
          </div>
        ))}
        {weeks.map((week, wi) =>
          week.map((cell, di) => (
            <div
              key={`${wi}-${di}`}
              className="aspect-square rounded-[6px] flex items-center justify-center text-[11px] transition-colors"
              style={
                cell.isToday
                  ? { background: "#3A3A3C", color: "#FFFFFF", fontWeight: 700, borderRadius: 8 }
                  : cell.runCount > 0
                  ? { background: "rgba(58,58,60,0.08)", color: "#3A3A3C", fontWeight: 600 }
                  : { color: "#AEAEB2" }
              }
            >
              {cell.dayNum ?? "—"}
            </div>
          ))
        )}
      </div>

      {/* Time slots */}
      <div className="border-t border-black/[0.06] pt-3 flex flex-col gap-0">
        <div className="flex items-center justify-between py-2 border-b border-black/[0.04]">
          <div>
            <div className="text-[12px] font-semibold text-[#3A3A3C]">{runTime}</div>
            <div className="text-[11px] text-[#8E8E93]">Morning Research + Briefing</div>
          </div>
          <span
            className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
            style={{ background: "rgba(255,214,10,0.12)", color: "#a38600" }}
          >
            Running
          </span>
        </div>
        <div className="flex items-center justify-between py-2">
          <div>
            <div className="text-[12px] font-semibold text-[#3A3A3C]">2:00 PM</div>
            <div className="text-[11px] text-[#8E8E93]">Engagement Check</div>
          </div>
          <span
            className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
            style={{ background: "rgba(0,122,255,0.08)", color: "#0055cc" }}
          >
            Pending
          </span>
        </div>
      </div>

      {/* Timezone */}
      <p className="text-[11px] text-[#AEAEB2] mt-2">
        Timezone: {schedule.timezone}
      </p>
    </div>
  );
}
