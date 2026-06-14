"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SkillCount, TrendPoint } from "@/lib/types";

const AXIS = "hsl(220 12% 60%)";
const GRID = "hsl(225 14% 18%)";
const PRIMARY = "hsl(250 90% 66%)";
const ACCENT = "hsl(190 90% 55%)";

const tooltipStyle = {
  background: "hsl(225 20% 9%)",
  border: `1px solid ${GRID}`,
  borderRadius: 8,
  fontSize: 12,
  color: "hsl(210 30% 96%)",
};

export function TrendChart({ title, data }: { title: string; data: TrendPoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
              <XAxis dataKey="date" stroke={AXIS} tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} stroke={AXIS} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={PRIMARY}
                strokeWidth={2.5}
                dot={{ r: 3, fill: PRIMARY }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export function SkillGapChart({ data }: { data: SkillCount[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Most common skill gaps</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 4, right: 12, left: 24, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} horizontal={false} />
              <XAxis type="number" stroke={AXIS} tick={{ fontSize: 11 }} allowDecimals={false} />
              <YAxis type="category" dataKey="skill" stroke={AXIS} tick={{ fontSize: 11 }} width={90} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "hsl(225 18% 12%)" }} />
              <Bar dataKey="count" fill={ACCENT} radius={[0, 4, 4, 0]} barSize={14} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export function CategoryRadar({ data }: { data: { category: string; score: number }[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Interview category scores</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data} outerRadius="70%">
              <PolarGrid stroke={GRID} />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 11, fill: AXIS }} />
              <Radar dataKey="score" stroke={PRIMARY} fill={PRIMARY} fillOpacity={0.35} />
              <Tooltip contentStyle={tooltipStyle} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
