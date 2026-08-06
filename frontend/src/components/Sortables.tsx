"use client";

import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { motion } from 'framer-motion';

const getParamColor = (param: string) => {
  const p = param.toLowerCase();
  if (p.includes('ph')) return 'text-cyan-400';
  if (p.includes('alk')) return 'text-pink-400';
  if (p.includes('calc')) return 'text-purple-400';
  if (p.includes('mag')) return 'text-emerald-400';
  if (p.includes('temp')) return 'text-orange-400';
  if (p.includes('nitra')) return 'text-red-400';
  if (p.includes('phos')) return 'text-yellow-400';
  return 'text-blue-400';
};

const getParamBgGlow = (param: string) => {
  const p = param.toLowerCase();
  if (p.includes('ph')) return 'group-hover:shadow-[0_0_20px_rgba(34,211,238,0.2)]';
  if (p.includes('alk')) return 'group-hover:shadow-[0_0_20px_rgba(244,114,182,0.2)]';
  if (p.includes('calc')) return 'group-hover:shadow-[0_0_20px_rgba(192,132,252,0.2)]';
  if (p.includes('mag')) return 'group-hover:shadow-[0_0_20px_rgba(52,211,153,0.2)]';
  if (p.includes('temp')) return 'group-hover:shadow-[0_0_20px_rgba(251,146,60,0.2)]';
  if (p.includes('nitra')) return 'group-hover:shadow-[0_0_20px_rgba(248,113,113,0.2)]';
  if (p.includes('phos')) return 'group-hover:shadow-[0_0_20px_rgba(250,204,21,0.2)]';
  return 'group-hover:shadow-[0_0_20px_rgba(96,165,250,0.2)]';
};

const getMockSparkline = (param: string) => {
  // Generates a random-looking SVG path based on string length to simulate a 24h sparkline
  const points = [];
  const seed = param.length;
  let y = 15;
  for (let i = 0; i <= 100; i += 10) {
    y += (Math.sin(i * seed) * 10);
    if (y < 2) y = 2;
    if (y > 28) y = 28;
    points.push(`${i},${y}`);
  }
  return `M ${points.join(' L ')}`;
};

export function TelemetryTile({ paramKey, val, isOverlay = false }: { paramKey: string, val: number, isOverlay?: boolean }) {
  const color = getParamColor(paramKey);
  const glow = getParamBgGlow(paramKey);
  const sparkline = getMockSparkline(paramKey);

  return (
    <div className={`relative group bg-black/40 backdrop-blur-xl border ${isOverlay ? 'border-white/30 scale-105 z-50' : 'border-white/10 hover:border-white/20'} ${glow} p-2 md:p-4 rounded-xl flex flex-col items-center justify-center shadow-2xl overflow-hidden cursor-grabbing transition-colors duration-300`}>
      <svg className="absolute bottom-0 left-0 w-full h-8 opacity-20 pointer-events-none" viewBox="0 0 100 30" preserveAspectRatio="none">
        <path d={sparkline} fill="none" stroke="currentColor" strokeWidth="2" className={color} />
      </svg>
      <div className={`text-[8px] md:text-[10px] ${color} font-bold uppercase tracking-widest mb-1 z-10 drop-shadow-md`}>{paramKey}</div>
      <div className="text-xl md:text-2xl font-black text-white tracking-tight z-10">{val}</div>
    </div>
  );
}

export function SortableTelemetryTile({ id, paramKey, val, index }: { id: string, paramKey: string, val: number, index: number }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 0 : 1,
    opacity: isDragging ? 0.3 : 1,
  };

  const color = getParamColor(paramKey);
  const glow = getParamBgGlow(paramKey);
  const sparkline = getMockSparkline(paramKey);

  return (
    <div ref={setNodeRef} style={style}>
        <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05, duration: 0.3 }}
        whileHover={{ scale: 1.05 }}
        className={`relative group bg-black/40 backdrop-blur-xl border border-white/10 hover:border-white/20 ${glow} p-2 md:p-4 rounded-xl flex flex-col items-center justify-center shadow-2xl overflow-hidden h-full transition-colors duration-300`}
      >
        <svg className="absolute bottom-0 left-0 w-full h-8 opacity-20 pointer-events-none" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path d={sparkline} fill="none" stroke="currentColor" strokeWidth="2" className={color} />
        </svg>
        <div 
          {...attributes} 
          {...listeners}
          className="absolute top-1 left-1 md:top-2 md:left-2 text-slate-500 hover:text-white cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity outline-none"
        >
          <GripVertical size={14} />
        </div>
        <div className={`text-[8px] md:text-[10px] ${color} font-bold uppercase tracking-widest mb-0.5 md:mb-1 z-10 drop-shadow-md`}>{paramKey}</div>
        <div className="text-xl md:text-2xl font-black text-white tracking-tight z-10">{val}</div>
      </motion.div>
    </div>
  );
}

export function SortableGraphWrapper({ id, children, index }: { id: string, children: React.ReactNode, index: number }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 0 : 1,
    opacity: isDragging ? 0.3 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="mb-4">
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1, duration: 0.4 }}
        className="relative group"
      >
        <div 
          {...attributes} 
          {...listeners}
          className="absolute top-2 left-2 z-50 text-slate-500 hover:text-cyan-400 cursor-grab active:cursor-grabbing p-1 bg-black/50 rounded outline-none"
        >
          <GripVertical size={16} />
        </div>
        {children}
      </motion.div>
    </div>
  );
}
