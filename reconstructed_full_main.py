import json

async def summarize_telemetry(client, raw_logs: str) -> dict:
    """
    Condenses thousands of raw telemetry data points into a short 2-3 sentence summary.
    """
    if not raw_logs or len(raw_logs) < 10:
        return {"type": "telemetry", "content": "No recent telemetry logs available.", "tokens": 0}
        
    prompt = f"""
    You are an expert marine biologist analyzing telemetry logs for a reef tank.
    Review the following raw parameter logs (oldest to newest):
    {raw_logs}
    
    In 2 to 3 sentences, summarize the current stability of the tank. 
    Explicitly call out any significant drops, spikes, or dangerous trends in Alkalinity, Calcium, Magnesium, pH, Temp, or Salinity.
    If everything is stable, state that clearly.
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "telemetry",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

async def summarize_history(client, tank_profile: str, past_messages: str) -> dict:
    """
    Summarizes the tank profile and recent conversational history.
    """
    prompt = f"""
    You are an expert marine biologist reviewing a client's tank history.
    
    Tank Profile (Livestock/Equipment):
    {tank_profile}
    
    Recent Chat History:
    {past_messages}
    
    In 2 to 3 sentences, summarize the tank's contents and any recent issues the user has been discussing.
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "history",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

async def retrieve_knowledge(client, user_prompt: str) -> dict:
    """
    Queries for relevant playbooks or general biological facts based on user symptoms.
    """
    prompt = f"""
    You are an expert reef knowledge retriever.
    The user is asking: "{user_prompt}"
    
    If they are describing a disease or coral issue (e.g., bleaching, RTN, white spots), output 2-3 sentences of expert factual knowledge about potential causes. 
    For example, if they mention mushrooms bleaching, mention amino acid toxicity or light shock.
    If it's just a general question or adding a fish, output "No specific playbook needed."
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "knowledge",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

async def analyze_equipment_and_notes(client, tank_profile: str, tank_events: str, user_prompt: str) -> dict:
    """
    Analyzes equipment logged by the user and any specific tank notes to see if missing equipment relates to the user's issue.
    """
    prompt = f"""
    You are an Equipment & Tank Notes Analyst.
    
    Tank Profile (Livestock/Equipment):
    {tank_profile}
    
    Tank Notes (Events):
    {tank_events}
    
    User Issue: "{user_prompt}"
    
    Review the user's issue. Identify if they are missing any critical equipment that might relate to their issue (e.g. no skimmer for high nutrients, no heater for temp drops). 
    Check if they have explicitly noted that they DO NOT have that equipment in their Tank Notes.
    Output 1-2 sentences summarizing relevant equipment they have, are missing, or notes indicating they don't have it.
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "equipment_notes",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

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
    
    now = datetime.now(timezone.utc)
    
      } else {
        alert("Upload failed. No URL returned.");
      }
    } catch (err) {
        setUpdateParamValue("");
      }
      // Fetch fresh data from backend to ensure we have the real DB IDs and sync
      fetchData();
    } catch (err) {
      alert("Failed to save log");
      // Revert optimistic update if failed by fetching true state
      fetchData();
    }
  };

  const deleteLogs = async (paramName?: string) => {
    const msg = paramName ? `Delete all logs for ${paramName}?` : "Clear all parameter logs?";
    if (!confirm(msg)) return;

    const url = paramName
      ? `http://localhost:8000/delete-logs?parameter=${encodeURIComponent(paramName)}`
      : `http://localhost:8000/delete-logs`;

    await fetch(url, { method: "DELETE" });
    fetchData();
  };

  const deleteSingleLog = async (id: number) => {
    // Optimistically remove from UI
    setLogs((prev) => prev.filter(log => log.id !== id));
    await fetch(`http://localhost:8000/delete-log/${id}`, { method: "DELETE" });
    fetchData();
  };

  const sendMessage = async (userMessage: string) => {
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const endpoint = useV2 ? "chat-v2" : "chat";
      const res = await fetch(`http://localhost:8000/${endpoint}?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage }),
      });
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "ai", content: data.reply }]);
      if (data.debug_xray) {
        setSessionXrays((prev) => {
          const updated = [...prev, data.debug_xray];
          return updated.slice(-10); // Keep only the last 10 in state
        });
      }
      if (data.proposed_actions && data.proposed_actions.length > 0) {
        const validActions = data.proposed_actions.filter((a: any) => {
          if (a.action === "add_inhabitant" && !a.species && !a.name) return false;
          return true;
        });
        if (validActions.length > 0) {
          setPendingActions(validActions);
        }
      }
    } catch (err) { }
  };

  const handleConfirmAction = async (actions: any[]) => {
    let successCount = 0;
    let failCount = 0;
    let errors: string[] = [];

    for (const action of actions) {
      try {
        if (action.action === "add_inhabitant") {
          const res = await fetch(`http://localhost:8000/add-inhabitant`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              category: action.category || "Other",
              species: action.species || "Unknown Species",
              name: action.name || action.species || "Unknown Item",
              count: action.count || 1,
              size: action.size || "",
              notes: action.notes || action.summary || "",
              care_info: action.care_info || "",
              image_url: "",
              date_added: action.date_added || new Date().toISOString()
            }),
          });
          if (res.ok) successCount++;
          else failCount++;
        } else if (action.action === "log_event") {
          const res = await fetch(`http://localhost:8000/log-event`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              summary: action.summary,
              event_type: "general"
            }),
          });
          if (res.ok) successCount++;
          else failCount++;
        } else if (action.action === "update_inhabitant" && action.id) {
          const res = await fetch(`http://localhost:8000/patch-inhabitant/${action.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
      fetchInhabitants();
    } catch (err) {
      console.error(err);
      alert("Network error while trying to save.");
    }
  };

  const toggleNotes = (id: number) => {
    setExpandedNotes(prev => ({ ...prev, [id]: !prev[id] }));
  };
  
  const handleAddTab = (category: string) => {
    if (!visibleTabs.includes(category)) {
      setVisibleTabs(prev => [...prev, category]);
    }
    setActiveTab(category);
    setIsCategoryDropdownOpen(false);
  };

  // Sort tabs (Equipment always first, then alphabetical)
  const sortedTabs = [...visibleTabs].sort((a, b) => {
    if (a === "Equipment") return -1;
    if (b === "Equipment") return 1;
    return a.localeCompare(b);
  });

  const activeInhabitants = inhabitants.filter(i => (i.category || 'Fish') === activeTab);

  const getCategoryIcon = (cat: string) => {
    switch(cat.toLowerCase()) {
      case "fish": return <Fish size={18} />;
      case "coral": return <Droplets size={18} />;
      case "invertebrate": return <Anchor size={18} />;
      case "equipment": return <Cpu size={18} />;
      default: return <Fish size={18} />;
    }
  };

  const filteredSuggestions = (SUGGESTIONS[formCategory] || []).filter(
    s => s.toLowerCase().includes(formSpecies.toLowerCase()) && s.toLowerCase() !== formSpecies.toLowerCase()
  );

  return (
    <div className="h-full w-full bg-slate-950 p-6 md:p-8 overflow-y-auto relative">
      <div className="max-w-7xl mx-auto flex flex-col h-full">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-black text-cyan-400">Tank Profile</h1>
            <p className="text-slate-400 text-sm mt-1">Manage and track your reef's ecosystem and hardware.</p>
          </div>
        </div>

        {/* Dynamic Tabs */}
        <div className="flex flex-wrap items-center gap-2 mb-6 border-b border-slate-800 pb-4 relative">
          {sortedTabs.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-300 flex items-center gap-2 ${
                activeTab === tab 
                  ? "bg-cyan-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]" 
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {getCategoryIcon(tab)} {tab}
            </button>
          ))}
          
          {/* Add Category Dropdown Button */}
          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setIsCategoryDropdownOpen(!isCategoryDropdownOpen)}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 w-9 h-9 rounded-lg flex items-center justify-center transition-colors shadow-sm ml-1"
              title="Add New Category Tab"
            >
              <Plus size={20} />
            </button>
            
            {isCategoryDropdownOpen && (
              <div className="absolute top-12 left-0 w-48 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-40 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="px-3 py-2 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-950/50 border-b border-slate-800">
                  New Category
                </div>
                <div className="p-1">
                  {PREDEFINED_CATEGORIES.filter(c => !visibleTabs.includes(c)).map(cat => (
                    <button
                      key={cat}
                      onClick={() => handleAddTab(cat)}
                      className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-cyan-900/40 hover:text-cyan-300 rounded-lg flex items-center gap-3 transition-colors"
                    >
                      {getCategoryIcon(cat)} {cat}
                    </button>
                  ))}
                  {PREDEFINED_CATEGORIES.filter(c => !visibleTabs.includes(c)).length === 0 && (
                    <div className="px-3 py-4 text-xs text-slate-500 text-center">
                      All categories added!
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex-1"></div>
          
          <button 
            onClick={() => {
              setEditingItemId(null);
              setFormSpecies("");
              setFormName("");
              setFormCount(1);
              setFormSize("");
              setFormNotes("");
              setFormImageUrl("");
              setFormDateAdded("");
              setFormCategory(activeTab);
              setIsModalOpen(true);
            }}
            className="bg-cyan-900/40 border border-cyan-500/50 hover:bg-cyan-800/60 text-cyan-300 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors font-medium text-sm"
          >
            <Plus size={16} /> Add {activeTab}
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center flex-1 text-slate-500">
            Loading {activeTab}...
          </div>
        ) : activeInhabitants.length === 0 ? (
          <div className="flex flex-col items-center justify-center flex-1 bg-slate-900/50 rounded-2xl border border-slate-800 border-dashed p-12 text-center mt-8">
            <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4 text-cyan-600/50">
              {getCategoryIcon(activeTab)}
            </div>
            <h3 className="text-xl font-bold text-slate-300 mb-2">No {activeTab} yet</h3>
            <p className="text-slate-500 max-w-sm mb-6">
              Click the Add button above to manually log a new item, or just tell ReefGPT about it in the Chat!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {activeInhabitants.map((item) => (
              <div 
                key={item.id} 
                className="bg-slate-900 border border-slate-800 hover:border-cyan-500/30 rounded-xl overflow-hidden transition-all duration-300 shadow-lg group relative"
              >
                {/* Edit Button overlay */}
                <button 
                  onClick={() => handleEditItem(item)}
                  className="absolute top-3 left-3 bg-black/60 hover:bg-cyan-600 text-white p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-300 z-20 backdrop-blur-md border border-white/10 shadow-lg"
                  title="Edit Item"
                >
                  <Pencil size={16} />
                </button>

                <div className="aspect-video w-full bg-slate-800 relative flex items-center justify-center overflow-hidden">
                  {item.image_url ? (
                    <img src={item.image_url} alt={item.species} className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500" />
                  ) : (
                    <div className="text-slate-600 group-hover:scale-110 transition-transform duration-500">
                      <ImageIcon size={48} />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-90"></div>
                  
                  {/* Count Badge */}
                  {item.count > 1 && (
                    <div className="absolute top-3 right-3 bg-cyan-600 text-white text-xs font-black px-2 py-1 rounded-md shadow-lg shadow-black/50 z-10 border border-cyan-400/30">
                      x{item.count}
                    </div>
                  )}

                  <div className="absolute bottom-3 left-4 right-4 z-10">
                    <div className="flex justify-between items-end">
                      <div>
                        <div className="text-xs text-cyan-400 font-bold uppercase tracking-wider mb-1">
                          {item.species}
                        </div>
                        {/* Only display the name if it exists and is not exactly the same as species */}
                        <div className="text-lg font-bold text-white leading-tight">
                          {item.name && item.name.toLowerCase() !== item.species.toLowerCase() ? item.name : ''}
                        </div>
                      </div>
                      {item.size && (
                        <div className="bg-black/60 backdrop-blur-md px-2 py-1 rounded border border-white/10 text-xs text-slate-300 font-mono ml-2 shrink-0">
                          {item.size}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-slate-900 flex flex-col h-full">
                  <div className="text-xs text-slate-500 font-mono mb-3">
                    Added: {item.date_added ? new Date(item.date_added).toLocaleDateString('en-US', { timeZone: 'UTC' }) : 'Unknown'}
                  </div>
                  
                  {item.notes || item.care_info ? (
                    <div className="border-t border-slate-800 pt-3 mt-auto">
                      <button 
                        onClick={() => toggleNotes(item.id)}
                        className="flex items-center justify-between w-full text-xs font-bold text-slate-400 hover:text-cyan-400 transition-colors uppercase tracking-wider mb-2"
                      >
                        {item.category === 'Equipment' ? 'Maintenance & Notes' : 'Notes & Care Guide'}
                        {expandedNotes[item.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                      
                      {expandedNotes[item.id] && (
                        <div className="text-sm text-slate-300 bg-black/40 p-3 rounded border border-slate-800/50 leading-relaxed mt-2 animate-in slide-in-from-top-2 fade-in duration-200">
                          {item.notes || item.care_info}
                        </div>
                      )}
                    </div>
                  ) : (
                     <div className="border-t border-slate-800 pt-3 mt-auto text-xs text-slate-600 italic">
                        No notes available.
                     </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add / Edit Item Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]">
            <div className="bg-slate-800/50 p-5 border-b border-slate-700 flex justify-between items-center shrink-0">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                {getCategoryIcon(formCategory)} {editingItemId ? 'Edit' : 'Add'} {formCategory}
              </h2>
              <button 
                onClick={() => {
                  setIsModalOpen(false);
                  setEditingItemId(null);
                }} 
                className="text-slate-400 hover:text-white transition-colors"
              >
                 <Plus size={24} className="rotate-45" />
              </button>
            </div>
            
            <div className="overflow-y-auto p-5 scrollbar-hide">
              <form onSubmit={handleAddItem} className="flex flex-col gap-5">
                
                {/* Image Upload Area */}
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Photo</label>
        
        # Create a unique filename
        filename = f"{int(pd.Timestamp.now().timestamp())}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"url": f"/uploads/{filename}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get-events")
def get_events():
    try:
        response = supabase.table("tank_events").select("*").eq("user_id", user_id_ctx.get()).order("date", desc=True).execute()
        return {"data": response.data}
    except Exception as e:
        return {"data": [], "error": str(e)}


        {/* RIGHT PANEL: Chat & X-Ray */}
        <Panel defaultSize={60} minSize={30} className="bg-black/20 border-l border-slate-800 flex flex-col relative">
          <div className="absolute top-3 right-3 z-50 flex gap-2">
            <button
              onClick={() => setUseV2(!useV2)}
              className={`text-xs px-3 py-1 rounded border transition-colors ${useV2 ? "bg-purple-500/20 border-purple-500 text-purple-300" : "bg-slate-800 border-slate-600 text-slate-400 hover:text-white"}`}
            >
              {useV2 ? "Engine: V2 (Agentic)" : "Engine: V1 (Standard)"}
            </button>
            <button
              onClick={() => setDevMode(!devMode)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${devMode ? "bg-cyan-500/20 border-cyan-500 text-cyan-300" : "bg-slate-800 border-slate-600 text-slate-400 hover:text-white"
                }`}
            >
              {devMode ? "X-Ray: ON" : "X-Ray: OFF"}
            </button>
          </div>

          {devMode ? (
            <Group orientation="vertical">
              <Panel defaultSize={50} className="flex flex-col">
                <Chatbot messages={messages} sendMessage={sendMessage} />
              </Panel>
              <Separator className="h-2 bg-slate-900 cursor-row-resize transition-colors hover:bg-cyan-900/30" />
              <Panel defaultSize={50} className="bg-slate-950 p-4 overflow-y-auto font-mono text-xs border-t border-slate-800 scrollbar-hide">
                <h3 className="text-cyan-400 font-bold mb-3 border-b border-cyan-900 pb-2 flex justify-between">
                  <span>🧠 Agent X-Ray (Session Log)</span>
                  <span className="text-slate-500">{sessionXrays.length} turns</span>
                </h3>

                {sessionXrays.length > 0 ? (
                  <div className="space-y-4 flex flex-col">
                    {sessionXrays.map((xray, idx) => (
                      <div key={idx} className="bg-black/50 p-3 rounded-lg border border-slate-800 shadow-inner">
                        <div className="flex justify-between items-center text-slate-500 mb-2 border-b border-slate-800/50 pb-1 font-bold">
                          <span>Turn {idx + 1}</span>
                          {xray.token_usage && (
                            <span className="text-purple-400/80 text-[10px]">
                              Total Tokens: {xray.token_usage.total_tokens || xray.token_usage.layer_1_tokens}
                              {xray.token_usage.total_saved && <span className="text-green-500 ml-2">(Saved ~{xray.token_usage.total_saved})</span>}
                            </span>
                          )}
                        </div>
                        {xray.reasoning_steps ? (
                          <div className="space-y-2 mt-2">
                            {xray.reasoning_steps.map((step: any, sIdx: number) => (
                              <div key={sIdx} className="border-l-2 border-cyan-700/50 pl-3 py-1">
                                <div className="text-cyan-500/80 text-[10px] uppercase font-bold tracking-wider mb-1 flex justify-between">
                                  <span>{step.node}</span>
                                  <span className="text-slate-500">{step.tokens} tkns</span>
                                </div>
                                <div className="text-slate-300 text-xs">{step.summary}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <pre className="text-green-400 whitespace-pre-wrap">{JSON.stringify(xray, null, 2)}</pre>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">Submit a prompt to begin logging reasoning...</p>
                )}
              </Panel>
            </Group>
          ) : (
            <Chatbot messages={messages} sendMessage={sendMessage} />
          )}
        </Panel>

      </Group>
    </div>
  );
}
                      placeholder={formCategory === 'Equipment' ? "e.g. Main Return" : "e.g. Bubbles"}
                      className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none placeholder-slate-600"
                    />
                  </div>
            avg_ph = avg_alk = avg_ca = 0
            has_critical = has_warning = False
            is_fluctuating = False
            stability_ratio = 1.0
            is_declining = False

        # 5. Current State Logic
        p, c, m, a = current['pH'], current['Calcium'], current['Magnesium'], current['Alkalinity']
        if 8.0 <= p <= 8.4 and 400 <= c <= 450 and 1250 <= m <= 1450 and 8.0 <= a <= 9.5:
            current_state = 0
        elif 7.5 <= p < 8.0 and 350 <= c < 400 and 1100 <= m < 1250 and 7.0 <= a < 8.0:
            current_state = 1
        else:
            current_state = 2

        if has_critical or is_declining:
            final_state, final_name = 2, "CRITICAL"
        elif is_fluctuating or has_warning or stability_ratio < 0.5:
            final_state, final_name = 1, "WARNING"
        else:
            final_state, final_name = current_state, "STABLE"

        return {
            "current_state": {
                "state_id": final_state,
                "state_name": final_name,
                "confidence": 0.95,
                "params": {"pH": p, "Calcium": c, "Magnesium": m, "Alkalinity": a},
                "stability": {
                    "ph_variance": round(ph_variance, 2),
                    "alk_variance": round(alk_variance, 2),
                    "ca_variance": round(ca_variance, 2),
                    "is_fluctuating": is_fluctuating,
                    "is_declining": is_declining,
                    "stability_ratio": round(stability_ratio, 2),
                    "days_analyzed": round(len(recent_readings) / 24, 1) if recent_readings else 0
                }
            }
        }
    except Exception as e:
        import traceback
        print(f"TANK STATUS ERROR: {str(e)}")
        print(traceback.format_exc())
        return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}, "error": str(e)}
                        type="button"
                        onClick={handleDeleteItem}
                        className="px-4 py-2 rounded-lg text-sm font-bold text-red-400 hover:text-white hover:bg-red-900/50 border border-transparent hover:border-red-500/50 transition-colors"
                      >
                        Delete
                      </button>
        if len(current_vals) >= 4:
            p = current_vals.get('pH', 8.0)
            c = current_vals.get('Calcium', 420)
            m = current_vals.get('Magnesium', 1350)
            a = current_vals.get('Alkalinity', 8.0)
            ml_features = np.array([[p, c, m, a, 78.0]])  # pH, Ca, Mg, Alk, Temp
            models = get_ml_models()
            xgb = models['xgb']
            scaler = models['scaler']
            ml_features_s = scaler.transform(ml_features)
            xgb_pred = xgb.predict(ml_features_s)[0]
            ml_labels = {0: "STABLE", 1: "WARNING", 2: "CRITICAL"}
            ml_prediction = ml_labels.get(int(xgb_pred), state_name)
            ml_confidence = metrics.get('xgb_test', 95.0)
    except Exception as e:
        ml_prediction = state_name
        ml_confidence = metrics.get('xgb_test', 95.0)

    # 3. Fetch Chat History (Moved UP so RAG can use it)
    try:
        raw_history = supabase.table("chat_history").select("role,content").eq("user_id", user_id_ctx.get()).order("id", desc=True).limit(6).execute()
        past_messages = raw_history.data[::-1] if raw_history.data else []
    except Exception:
        past_messages = []

    # 4. RAG Context (Smart Context-Aware Search)
    try:
        from rag.rag import get_diagnosis_context
        from rag.vector_db import get_vector_context
        
        current_vals = {}
        if chrono_logs: # <--- Updated to use your new list
            for row in chrono_logs: # <--- Updated
                param = row.get("parameter", "")
                val = row.get("value", 0)
                if param and val:
                    current_vals[param] = val
        
        # --- THE FIX: Only append history if it's a follow-up ---
        search_query = req.text
        follow_up_triggers = ["it", "they", "them", "this", "that", "he", "she"]
        words = req.text.lower().split()
        is_follow_up = len(words) < 8 or any(word in words for word in follow_up_triggers)

        if is_follow_up and past_messages:
            for msg in reversed(past_messages):
                if msg["role"] == "user":
                    search_query = f"Previous context: {msg['content']} | Current question: {req.text}"
                    break
                
        rag_context = get_diagnosis_context(search_query, list(current_vals.keys()), current_vals)
        vector_context = get_vector_context(search_query, k=3)
        
        full_context = f"--- VECTOR DATABASE RESULTS ---\n{vector_context}\n\n--- EXPERT OVERRIDE RULES (HIGHEST PRIORITY) ---\n{rag_context}"
    except Exception as e:
        full_context = f"(RAG unavailable: {e})"

    # 5. Build LLM Messages with Memory with ML Pipeline
    # 5. Build LLM Messages with Memory with ML Pipeline
    # 5. Build LLM Messages with Memory with ML Pipeline
    system_instruction = f"""
You are ReefGPT, an elite clinical diagnostic engine for high-end reef aquariums. 

### PRIORITY OF TRUTH:
1. **LIVE TELEMETRY & ML ALERTS (CRITICAL):** If the ML models or live data flag a CRITICAL or WARNING state, address the anomaly first.
2. **KNOWLEDGE BOUNDARY (RAG):** Rely on the provided Vector DB. Never guess.
3. **CHAT HISTORY (LOW PRIORITY):** Use only to resolve pronouns. The chat history may say an item was deleted, but if it is still listed in TANK LIVESTOCK, the action was rejected by the user. ALWAYS trust TANK LIVESTOCK as the absolute source of truth.

### DIAGNOSTIC & TONE RULES:
- **Duplicate Verifier (CRITICAL):** Before proposing an `add_inhabitant` action, check CURRENT TANK LIVESTOCK. If the exact same species already exists, DO NOT output an `add_inhabitant` action. Instead, ask the user: "You already have a [Species]. Are you adding a second one, or did you mean to update the existing one?"
- **Anti-Hallucination (CRITICAL):** Your ML models are Classifiers, NOT Regressors. If the user asks for a forecast, DO NOT invent specific numerical ranges (e.g., never say "pH will be 8.1"). Instead, state the predicted classification (STABLE/WARNING/CRITICAL) and cite the model's overall Test Accuracy as your confidence level.
- **Action Confirmation (CRITICAL):** When proposing a database action (add, update, delete), DO NOT say you have already done it. Say "I have prepared an action to X, please confirm."
- **Be Succinct:** Keep your `reply` to 2-4 sentences maximum. 
- **The 95% Rule:** Speak naturally and confidently. No bulleted lists.
- **Secondary Causes:** For normal diagnostic questions (e.g., coral health, algae), solve the primary issue, but briefly mention 1-2 other possible causes at the end just in case.
- **The Prediction Exception:** If asked for a status/forecast or if the ML flags an anomaly, explicitly state the ML's classification (Safe/Warning/Critical) and confidence score in your reply.

### CURRENT SYSTEM CONTEXT:
- **OFFICIAL TANK STATE (from XGBoost):** {ml_prediction} (Confidence: {ml_confidence:.1f}%, pH Variance: ±{ph_var}, Alk Variance: ±{alk_var})
- **ML METRICS:** 
  * XGBoost Accuracy: {metrics['xgb_test']}% (R²: {metrics['xgb_r2']})
- **CURRENT TANK LIVESTOCK (ABSOLUTE TRUTH):** 
{tank_livestock}
- **USER'S RECENT PARAMETERS:** {tank_data}
{full_context}

### OUTPUT SCHEMA (STRICT JSON):
{{
  "xray": {{
    "step_1_intent": "1 sentence defining the exact user problem.",
    "step_2_telemetry_check": "Parameters considered vs. explicitly IGNORED.",
    "step_3_ml_inference": "XGBoost model prediction: {ml_prediction} with {ml_confidence:.1f}% confidence.",
    "step_4_rag_knowledge": "Specific pathology retrieved.",
    "step_5_logic": "How the Agent combined ML and RAG to reach the answer."
  }},
  "proposed_actions": [
    {{
      "action": "add_inhabitant or log_event or update_inhabitant or delete_inhabitant",
      "id": "If updating or deleting, you MUST provide the integer ID of the item",
      "species": "If adding/updating/deleting, the species name/make.",
      "name": "If adding/updating, the specific name or nickname of the inhabitant (optional).",
      "category": "If adding an inhabitant, one of: Fish, Coral, Invertebrate, Equipment, Other",
      "size": "If adding/updating, the size of the inhabitant (e.g., '3 inches', 'small').",
      "notes": "If adding/updating, any additional notes, personality traits, or status provided by the user.",
      "count": "If adding/updating, the quantity of the item (defaults to 1).",
      "date_added": "If adding/updating the date_added, provide the ISO date (e.g. 2025-07-01T00:00:00Z)",
      "summary": "If logging an event, the summary of the event."
    }}
  ],
  "reply": "Your succinct, 2-4 sentence conversational response."
}}
"""

# Build LLM Messages with Fenced History
    llm_messages = [{"role": "system", "content": "You must respond in JSON format only. " + system_instruction}]
    
    if past_messages:
        llm_messages.append({"role": "system", "content": "[START STALE CHAT HISTORY]"})
        for msg in past_messages:
            role = "assistant" if msg["role"] == "ai" else "user"
            llm_messages.append({"role": role, "content": str(msg.get("content", ""))})
        llm_messages.append({"role": "system", "content": "[END STALE CHAT HISTORY - FOCUS ON NEWEST DATA BELOW]"})
        
    llm_messages.append({"role": "user", "content": req.text})        

    # Save User Message to DB
    supabase.table("chat_history").insert({"role": "user", "content": req.text, "user_id": user_id_ctx.get()}).execute()

    # 6. Call LLM
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=llm_messages,
        response_format={"type": "json_object"}
    )
    
    raw_reply = response.choices[0].message.content
    
    try:
        json_data = json.loads(raw_reply)
        user_reply = json_data.get("reply", "I encountered an error processing that.")
        if not isinstance(user_reply, str):
            user_reply = json.dumps(user_reply, indent=2)
            
        # Expose the raw RAG context to the frontend X-Ray for debugging
        json_data["rag_sources_retrieved"] = full_context
        
    except json.JSONDecodeError:
        json_data = {"error": "Failed to parse JSON", "raw": raw_reply}
        user_reply = raw_reply
    
    # Save AI Message to DB
    supabase.table("chat_history").insert({
        "role": "ai", 
        "content": user_reply, 
        "user_id": user_id_ctx.get(),
        "agent_reasoning": json_data
    }).execute()

    return {
        "reply": user_reply,
        "proposed_actions": json_data.get("proposed_actions", []),
        "debug_xray": json_data
    }

# Tank Classification Endpoint
@app.get("/tank-status")
def get_tank_status():
    """Get current tank status based on multi-day stability"""
    try:
        import datetime
        three_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=3)).isoformat()
        res = supabase.table("metrics_log").select("parameter,value,timestamp").gte("timestamp", three_days_ago).order("timestamp", desc=True).execute()
        
        if not res.data:
            return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}}

        # 1. Sort chronological (oldest to newest)
        raw_logs_asc = sorted(res.data, key=lambda x: str(x.get('timestamp', '')))
        
        running_state = {}
        all_params = []
        
        # 2. Build timeline safely
        for log in raw_logs_asc:
            param_name = log.get('parameter')
            raw_value = log.get('value')
            
            # Skip invalid rows safely
            if not param_name or raw_value is None:
                continue
                
            if param_name in ['pH', 'Calcium', 'Magnesium', 'Alkalinity']:
                try:
                    running_state[param_name] = float(raw_value)
                except (ValueError, TypeError):
                    continue # Skip if value isn't a number
            
            # Save snapshot if we have all 4
            if len(running_state) == 4:
                all_params.append({
                    'timestamp': log.get('timestamp'),
                    'pH': running_state['pH'],
                    'Calcium': running_state['Calcium'],
                    'Magnesium': running_state['Magnesium'],
                    'Alkalinity': running_state['Alkalinity']
                })

        if not all_params:
            print("DEBUG: all_params is empty. We never collected all 4 metrics.")
            return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}}

        # 3. Sort descending (newest first)
        all_params = sorted(all_params, key=lambda x: x['timestamp'], reverse=True)
        current = all_params[0]

        # 4. Time-Windowing for Variance
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        recent_readings = []
        for r in all_params:
            try:
                # Slice the string to keep only 'YYYY-MM-DDTHH:MM:SS'
                # This strips the timezone/milliseconds, making it safely offset-naive
                ts_str = str(r['timestamp'])[:19] 
                
                if datetime.datetime.fromisoformat(ts_str) >= yesterday:
                    recent_readings.append(r)
            except ValueError:
                continue

        if len(recent_readings) >= 3:
            ph_values = [r['pH'] for r in recent_readings]
            alk_values = [r['Alkalinity'] for r in recent_readings]
            ca_values = [r['Calcium'] for r in recent_readings]
            
            ph_variance = max(ph_values) - min(ph_values)
            alk_variance = max(alk_values) - min(alk_values)
            ca_variance = max(ca_values) - min(ca_values)
            
            avg_ph = sum(ph_values) / len(ph_values)
            avg_alk = sum(alk_values) / len(alk_values)
            avg_ca = sum(ca_values) / len(ca_values)
            
            period_states = []
            for r in recent_readings:
                p, c, m, a = r['pH'], r['Calcium'], r['Magnesium'], r['Alkalinity']
                if 8.0 <= p <= 8.4 and 400 <= c <= 450 and 1250 <= m <= 1450 and 8.0 <= a <= 9.5:
                    period_states.append(0) 
                elif 7.5 <= p < 8.0 and 350 <= c < 400 and 1100 <= m < 1250 and 7.0 <= a < 8.0:
                    period_states.append(1) 
                else:
                    period_states.append(2) 
            alk_trend = current['Alkalinity'] - avg_alk
            is_declining = alk_trend < -0.5 
        else:
            ph_variance = alk_variance = ca_variance = 0
            avg_ph = avg_alk = avg_ca = 0
            has_critical = has_warning = False
            is_fluctuating = False
            stability_ratio = 1.0
            is_declining = False

        # 5. Current State Logic
        p, c, m, a = current['pH'], current['Calcium'], current['Magnesium'], current['Alkalinity']
        if 8.0 <= p <= 8.4 and 400 <= c <= 450 and 1250 <= m <= 1450 and 8.0 <= a <= 9.5:
            current_state = 0
        elif 7.5 <= p < 8.0 and 350 <= c < 400 and 1100 <= m < 1250 and 7.0 <= a < 8.0:
            current_state = 1
        else:
            current_state = 2

        if has_critical or is_declining:
            final_state, final_name = 2, "CRITICAL"
        elif is_fluctuating or has_warning or stability_ratio < 0.5:
            final_state, final_name = 1, "WARNING"
        else:
            final_state, final_name = current_state, "STABLE"

        return {
            "current_state": {
                "state_id": final_state,
                "state_name": final_name,
                "confidence": 0.95,
                "params": {"pH": p, "Calcium": c, "Magnesium": m, "Alkalinity": a},
                "stability": {
                    "ph_variance": round(ph_variance, 2),
                    "alk_variance": round(alk_variance, 2),
                    "ca_variance": round(ca_variance, 2),
                    "is_fluctuating": is_fluctuating,
                    "is_declining": is_declining,
                    "stability_ratio": round(stability_ratio, 2),
                    "days_analyzed": round(len(recent_readings) / 24, 1) if recent_readings else 0
                }
            }
        }
    except Exception as e:
        import traceback
        print(f"TANK STATUS ERROR: {str(e)}")
        return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}, "error": str(e)}

@app.post("/chat-v2")
                    "days_analyzed": round(len(recent_readings) / 24, 1) if recent_readings else 0
                }
            }
        }
    except Exception as e:
        import traceback
        print(f"TANK STATUS ERROR: {str(e)}")
        return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}, "error": str(e)}

@app.post("/chat-v2")
async def chat_v2_endpoint(req: ChatRequest):
    from rag.summarizers import summarize_telemetry, summarize_history, retrieve_knowledge, analyze_equipment_and_notes
    from rag.router import route_intent
    import asyncio
    
    # 1. Fetch raw data to feed the workers (same as v1 but we don't send it to the 70B model directly)
    parameters = ["pH", "Temperature", "Alkalinity", "Calcium", "Magnesium"]
    chrono_logs = []
    for param in parameters:
        limit = 8 if param in ["pH", "Temperature"] else 2
        res = supabase.table("metrics_log").select("*").eq("parameter", param).order("timestamp", desc=True).limit(limit).execute()
        if res.data:
            chrono_logs.extend(res.data)
            
    chrono_logs = sorted(chrono_logs, key=lambda x: x['timestamp'])
    raw_telemetry = "\n".join([f"[{log['timestamp'][:16]}] {log['parameter']}: {log['value']}" for log in chrono_logs]) if chrono_logs else "No logs"
    
    try:
        profile = supabase.table("inhabitants").select("*").eq("user_id", user_id_ctx.get()).execute()
        tank_livestock = json.dumps(profile.data) if profile.data else "No livestock"
    except Exception:
        tank_livestock = "No livestock"
        
    try:
        raw_history = supabase.table("chat_history").select("role,content").eq("user_id", user_id_ctx.get()).order("id", desc=True).limit(6).execute()
        past_messages = json.dumps(raw_history.data[::-1]) if raw_history.data else "No chat history"
    except Exception:
        past_messages = "No chat history"
        
    try:
        raw_events = supabase.table("tank_events").select("*").eq("user_id", user_id_ctx.get()).order("date", desc=True).execute()
        tank_events = json.dumps(raw_events.data) if raw_events.data else "No tank notes"
    except Exception:
        tank_events = "No tank notes"
        
    # 2. RUN ORCHESTRATOR FIRST
    router_response = await route_intent(async_client, req.text, past_messages)
    router_content = router_response['content']
    selected_subagents = router_content.get('subagents', ["telemetry", "historian", "equipment", "knowledge"])
    
    if router_content.get('status') == "SHORT_CIRCUIT":
        reply_text = router_content.get('reply', 'I need more information to proceed.')
        return {
            "reply": reply_text,
            "proposed_actions": [],
            "debug_xray": {
                "orchestrator": {
                    "decision": selected_subagents,
                    "status": "SHORT_CIRCUIT",
                    "tokens": router_response['tokens']
                },
                "subagents": [],
                "master": None,
                "severity": "INFO"
            }
        }

    # 3. RUN SELECTED SUBAGENTS IN PARALLEL
    tasks = []
    task_names = []
    
    if "telemetry" in selected_subagents:
        tasks.append(summarize_telemetry(async_client, raw_telemetry))
        task_names.append("telemetry")
    if "historian" in selected_subagents:
        tasks.append(summarize_history(async_client, tank_livestock, past_messages))
        task_names.append("historian")
    if "equipment" in selected_subagents:
        tasks.append(analyze_equipment_and_notes(async_client, tank_livestock, tank_events, req.text))
        task_names.append("equipment")
    if "knowledge" in selected_subagents:
        tasks.append(retrieve_knowledge(async_client, req.text))
        task_names.append("knowledge")
        
    subagent_results = await asyncio.gather(*tasks) if tasks else []
    
    subagents_trace = []
    layer_1_summaries = ""
    
    for name, res in zip(task_names, subagent_results):
        node_name = name.capitalize()
        if name == "equipment": node_name = "Equipment & Notes Analyst"
        if name == "knowledge": node_name = "Knowledge Retriever"
        if name == "historian": node_name = "Historian"
        if name == "telemetry": node_name = "Telemetry Summarizer"
        
        subagents_trace.append({
            "node": node_name,
            "summary": res['content'],
            "tokens": res['tokens']
        })
        layer_1_summaries += f"{node_name.upper()}: {res['content']}\n"
    
    if not layer_1_summaries:
        layer_1_summaries = "No subagents were run for this prompt."
        
    # 4. MASTER DIAGNOSTICIAN (70B)
    master_prompt = f"""
    You are ReefGPT, an elite clinical diagnostic engine.
    
    --- LAYER 1 SUMMARIES ---
    {layer_1_summaries}
    
    USER PROMPT: "{req.text}"
    
    DIRECTIONS:
    1. Respond to the user with expert, nuanced advice based ONLY on the Layer 1 Summaries.
    2. CONVERSATIONAL & SUCCINCT: Write no more than 2-3 sentences. Sound like a knowledgeable human LFS employee talking to a customer. DO NOT write essays.
    3. You MUST ALWAYS return a valid JSON object at the end of your response, starting with `JSON_START` and ending with `JSON_END`.
    4. Inside the JSON, you must include a `severity` field ("CRITICAL", "WARNING", or "INFO").
    5. Inside the JSON, you must include an `internal_thoughts` field explaining your logical deduction BEFORE forming your reply.
    6. If the user's prompt implies they are adding livestock or logging data, include an `actions` array in the JSON.
    7. EQUIPMENT CHECK (CRITICAL): If the user has an issue that requires specific equipment (e.g. high nutrients and skimmers) and the EQUIPMENT & NOTES summary indicates it is missing from their profile/notes, ASK them if they have it. If they explicitly state they DO NOT have it, you MUST propose a `log_event` action with a summary like "User confirmed they do not have a [Equipment]" to permanently save it as a tank note.

    Example Response:
    That Purple Tang is a great addition, but watch out for aggression with your other fish. Let me add him to your tank profile. How is he eating so far?
    
    JSON_START
    {
      "internal_thoughts": "The historian noted aggression with tangs. The user is adding one. I should warn them.",
      "severity": "INFO",
      "actions": [
        {
          "action": "add_inhabitant",
          "name": "Yellow Tang",
          "species": "Zebrasoma flavescens",
          "category": "Fish",
          "size": "3 inches"
        }
      ]
    }
    JSON_END
    """
    
    response = await async_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": master_prompt}],
        temperature=0.2
    )
    
    full_text = response.choices[0].message.content
