"use client";

import { useState, useEffect } from "react";
import { Check, X, Fish } from "lucide-react";

interface Action {
  action: string;
  id?: number;
  species?: string;
  category?: string;
  date_added?: string;
  summary?: string;
}

interface ActionPopupProps {
  actions: Action[];
  onConfirm: (actions: Action[]) => void;
  onDismiss: () => void;
}

export default function ActionPopup({ actions, onConfirm, onDismiss }: ActionPopupProps) {
  // Filter unsupported actions hallucinates by the AI
  const validActions = actions?.filter(a => ['add_inhabitant', 'monitor_parameters'].includes(a.action)) || [];

  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (validActions.length > 0) {
      setSelectedIndices(new Set(validActions.map((_, i) => i)));
    }
  }, [actions]);

  if (validActions.length === 0) return null;

  const toggleSelection = (idx: number) => {
    const next = new Set(selectedIndices);
    if (next.has(idx)) {
      next.delete(idx);
    } else {
      next.add(idx);
    }
    setSelectedIndices(next);
  };

  const selectedCount = selectedIndices.size;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-slate-900 border-2 border-cyan-500/50 shadow-[0_0_50px_rgba(6,182,212,0.4)] rounded-2xl p-6 flex flex-col items-center gap-6 max-w-md w-full animate-in zoom-in-95 duration-300">
        <div className="bg-cyan-600/20 p-4 rounded-full text-cyan-400 mb-2">
          <Fish size={48} />
        </div>
        
        <div className="flex-1 w-full flex flex-col text-center">
          <h4 className="text-xl font-bold text-white mb-2">
            Confirm Actions?
          </h4>
          <p className="text-sm text-slate-300 mb-4">
            I have prepared the following {validActions.length} action{validActions.length > 1 ? 's' : ''}. Shall I execute them?
          </p>
          
          <div className="max-h-48 overflow-y-auto w-full flex flex-col gap-2 rounded-xl bg-slate-800/50 p-3 border border-slate-700/50">
            {validActions.map((action, idx) => {
              const isSelected = selectedIndices.has(idx);
              return (
                <div 
                  key={idx} 
                  onClick={() => toggleSelection(idx)}
                  className={`rounded-lg p-3 text-left border flex items-center gap-3 cursor-pointer transition-colors ${isSelected ? 'bg-slate-800 border-cyan-500/50' : 'bg-slate-900/50 border-slate-800 opacity-50'}`}
                >
                  <div className={`w-5 h-5 rounded flex items-center justify-center border shrink-0 transition-colors ${isSelected ? 'bg-cyan-500 border-cyan-400' : 'border-slate-600'}`}>
                    {isSelected && <Check size={14} className="text-white" />}
                  </div>
                  <div className="flex flex-col flex-1 min-w-0">
                    <span className={`text-xs font-bold uppercase tracking-wider mb-1 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`}>
                      {action.action.replace("_inhabitant", "").toUpperCase()}
                    </span>
                    <span className={`text-sm font-medium ${isSelected ? 'text-white' : 'text-slate-400'}`}>
                      {action.species || action.summary || "Tank Item"} {action.size && `(${action.size})`}
                    </span>
                    {action.notes && (
                      <span className="text-xs text-slate-300 italic mt-1 break-words line-clamp-2">"{action.notes}"</span>
                    )}
                    {action.date_added && (
                      <span className="text-xs text-slate-500 mt-1">Date: {action.date_added.split('T')[0]}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex w-full gap-3 mt-2">
          <button 
            onClick={onDismiss}
            className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <X size={20} /> Cancel
          </button>
          <button 
            onClick={() => {
              const selectedActions = validActions.filter((_, idx) => selectedIndices.has(idx));
              if (selectedActions.length > 0) {
                onConfirm(selectedActions);
              } else {
                onDismiss();
              }
            }}
            disabled={selectedCount === 0}
            className={`flex-1 font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 ${selectedCount > 0 ? 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-900/50' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
          >
            <Check size={20} /> Confirm ({selectedCount})
          </button>
        </div>
      </div>
    </div>
  );
}
