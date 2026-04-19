'use client';

import React, { useState, useMemo } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const PARAMETERS = ['pH', 'Alkalinity', 'Calcium', 'Magnesium', 'Temperature'];
const TIME_RANGES = [
    { label: '1D', days: 1 },
    { label: '3D', days: 3 },
    { label: '1W', days: 7 }, // Capped at 1 week max
];

interface LogEntry {
    id: number;
    parameter: string;
    value: number;
    timestamp: string;
}

interface ParameterGraphProps {
    logs: LogEntry[];
}

export default function ParameterGraph({ logs }: ParameterGraphProps) {
    const [selectedParam, setSelectedParam] = useState('pH');
    const [timeRange, setTimeRange] = useState(7); // Default to 1 week

    const chartData = useMemo(() => {
        if (!logs || logs.length === 0) return [];

        // 1. Find the GLOBAL latest date across ALL logs to anchor the timeline
        const globalSortedLogs = [...logs].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        const latestGlobalDate = new Date(globalSortedLogs[globalSortedLogs.length - 1].timestamp);

        // 2. Filter by parameter and ensure we have data for the specific line
        const paramLogs = logs.filter(log => log.parameter.toLowerCase() === selectedParam.toLowerCase());
        if (paramLogs.length === 0) return [];

        const sortedParamLogs = [...paramLogs].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

        // 3. Calculate the cutoff date based on the GLOBAL latest log
        // (FIXED: Using latestGlobalDate instead of latestDate)
        const cutoffDate = new Date(latestGlobalDate);
        cutoffDate.setDate(cutoffDate.getDate() - timeRange);

        // 4. Filter and format the data
        const filteredLogs = sortedParamLogs.filter(log => new Date(log.timestamp) >= cutoffDate);

        return filteredLogs.map(log => {
            const date = new Date(log.timestamp);
            const formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const monthDay = date.toLocaleDateString([], { month: 'short', day: 'numeric' });

            return {
                time: `${monthDay} ${formattedTime}`,
                fullDate: date.toLocaleString(),
                [selectedParam]: log.value
            };
        });
    }, [logs, selectedParam, timeRange]);

    return (
        <div className="w-full bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg mb-6">
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-4">
                    <h2 className="text-lg font-bold text-cyan-400">Telemetry</h2>

                    {/* Strict 1D, 3D, 1W Range Selector */}
                    <div className="flex bg-black/50 border border-slate-700 rounded-lg p-1">
                        {TIME_RANGES.map(range => (
                            <button
                                key={range.label}
                                onClick={() => setTimeRange(range.days)}
                                className={`text-xs px-3 py-1 rounded-md transition-colors ${timeRange === range.days
                                    ? 'bg-cyan-600 text-white font-bold'
                                    : 'text-slate-400 hover:text-white'
                                    }`}
                            >
                                {range.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Apex-Style Dropdown */}
                <select
                    value={selectedParam}
                    onChange={(e) => setSelectedParam(e.target.value)}
                    className="bg-black/80 border border-slate-700 rounded-lg p-2 text-sm text-slate-200 focus:border-cyan-500 outline-none cursor-pointer"
                >
                    {PARAMETERS.map(param => (
                        <option key={param} value={param}>{param}</option>
                    ))}
                </select>
            </div>

            <div className="h-64 w-full">
                {chartData.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-slate-500 text-sm italic">
                        No data logged for {selectedParam} in the selected time range.
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis
                                dataKey="time"
                                stroke="#64748b"
                                fontSize={11}
                                tickMargin={10}
                                minTickGap={20}
                            />
                            <YAxis
                                domain={['dataMin', 'auto']}
                                stroke="#64748b"
                                fontSize={11}
                                tickFormatter={(val) => val.toFixed(1)}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc', borderRadius: '8px' }}
                                itemStyle={{ color: '#22d3ee', fontWeight: 'bold' }}
                                labelFormatter={(label, payload) => payload[0]?.payload.fullDate || label}
                            />
                            <Line
                                type="monotone"
                                dataKey={selectedParam}
                                name={selectedParam}
                                stroke="#22d3ee"
                                strokeWidth={3}
                                dot={{ r: 4, fill: '#0f172a', stroke: '#22d3ee', strokeWidth: 2 }}
                                activeDot={{ r: 6, fill: '#22d3ee', stroke: '#fff' }}
                                isAnimationActive={false} // Prevents graph from bugging out on single point live-updates
                            />
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}