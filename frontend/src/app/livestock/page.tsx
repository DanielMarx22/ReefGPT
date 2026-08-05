"use client";

import { useState, useEffect, useRef } from "react";
import { Fish, Plus, Image as ImageIcon, ChevronDown, ChevronUp, Droplets, Anchor, Cpu, UploadCloud, Pencil } from "lucide-react";

const SUGGESTIONS: Record<string, string[]> = {
  Fish: [
    "Yellow Tang", "Blue Hippo Tang", "Kole Tang", "Purple Tang", "Sailfin Tang", "Naso Tang", "Powder Blue Tang", "Powder Brown Tang", "Achilles Tang", "Gem Tang",
    "Ocellaris Clownfish", "Maroon Clownfish", "Tomato Clownfish", "Clarkii Clownfish", "Percula Clownfish", "Pink Skunk Clownfish",
    "Six Line Wrasse", "Melanurus Wrasse", "Yellow Coris Wrasse", "Leopard Wrasse", "Fairy Wrasse", "Flasher Wrasse", "Silver Belly Wrasse", "Christmas Wrasse",
    "Coral Beauty Angelfish", "Flame Angelfish", "Emperor Angelfish", "Bicolor Angelfish", "Regal Angelfish", "Majestic Angelfish",
    "Royal Gramma", "Banggai Cardinalfish", "Pajama Cardinalfish", "Orchid Dottyback", "Bicolor Dottyback",
    "Firefish", "Purple Firefish", "Diamond Goby", "Watchman Goby", "Mandarin Goby", "Engineer Goby", "Yasha Goby", "Clown Goby",
    "Lawnmower Blenny", "Tailspot Blenny", "Bicolor Blenny", "Starry Blenny", "Midas Blenny",
    "Foxface Rabbitfish", "Magnificent Foxface", "One Spot Foxface",
    "Green Chromis", "Blue Reef Chromis", "Anthias (Lyretail)", "Anthias (Bartlett's)", "Anthias (Dispar)",
    "Longnose Hawkfish", "Flame Hawkfish", "Marine Betta", "Copperband Butterflyfish", "Peppermint Angelfish"
  ],
  Coral: [
    "Torch Coral", "Hammer Coral", "Frogspawn Coral", "Octospawn", "Galaxea",
    "Zoanthids", "Palythoa", "Mushroom Coral", "Ricordea", "Yuma Mushroom", "Rhodactis",
    "Green Star Polyps (GSP)", "Xenia", "Clove Polyps", "Blue Sympodium",
    "Acropora", "Montipora Cap", "Montipora Digitata", "Birdsnest (Seriatopora)", "Stylophora", "Pocillopora",
    "Duncan Coral", "Acanthastrea (Acan)", "Micromussa", "Scolymia", "Trachyphyllia",
    "Brain Coral", "Favia", "Favites", "Blastomussa", "Lobophyllia", "Symphyllia",
    "Chalice Coral", "Cyphastrea", "Goniopora", "Alveopora", "Leptastrea",
    "Leather Coral", "Toadstool Leather", "Devil's Hand Leather", "Finger Leather", "Cabbage Leather", "Gorgonian"
  ],
  Invertebrate: [
    "Cleaner Shrimp", "Blood Fire Shrimp", "Peppermint Shrimp", "Pistol Shrimp", "Coral Banded Shrimp", "Harlequin Shrimp",
    "Emerald Crab", "Hermit Crab (Blue Leg)", "Hermit Crab (Red Leg)", "Halloween Hermit Crab", "Porcelain Crab", "Pom Pom Crab",
    "Trochus Snail", "Astrea Snail", "Cerith Snail", "Nassarius Snail", "Mexican Turbo Snail", "Bumble Bee Snail", "Margarita Snail",
    "Rose Bubble Tip Anemone (RBTA)", "Green Bubble Tip Anemone", "Rock Flower Anemone", "Carpet Anemone", "Mini Maxi Carpet Anemone", "Sebae Anemone",
    "Maxima Clam", "Derasa Clam", "Crocea Clam", "Squamosa Clam",
    "Feather Duster", "Coco Worm", "Christmas Tree Worm",
    "Tuxedo Urchin", "Pincushion Urchin", "Longspine Urchin", "Pencil Urchin",
    "Sand Sifting Starfish", "Serpent Starfish", "Brittle Starfish", "Linckia Starfish", "Chocolate Chip Starfish"
  ],
  Equipment: [
    "Ecotech Radion XR15", "Ecotech Radion XR30", "AquaIllumination Prime 16HD", "AquaIllumination Hydra 32HD", "AquaIllumination Hydra 64HD",
    "AquaIllumination Blade", "Kessil A360X", "Kessil A160WE", "Kessil AP9X", "Kessil A80", "ReefBreeders Photon", "Orphek Atlantik",
    "Ecotech Vortech MP10", "Ecotech Vortech MP40", "Ecotech Vortech MP60",
    "Maxspect Gyre", "Nero 3", "Nero 5", "Nero 7", "IceCap Gyre", "Tunze Nanostream", "Tunze Turbelle",
    "Neptune Apex Controller", "Neptune DOS", "Neptune Trident", "Neptune ATK", "Neptune COR", "Neptune WAV",
    "Ecotech Vectra S2", "Ecotech Vectra M2", "Ecotech Vectra L2",
    "Sicce Syncra Silent", "Sicce SDC", "Sicce Micra", "Abyzz Pump",
    "Reef Octopus Skimmer", "Nyos Quantum Skimmer", "Tunze DOC Skimmer", "Deltec Skimmer", "Bubble King Skimmer",
    "Red Sea ReefMat", "Clarisea Roller", "AquaMaxx Roller",
    "Tunze Osmolator ATO", "XP Aqua Duetto ATO", "AutoAqua Smart ATO",
    "Brs Titanium Heater", "Eheim Jager Heater", "Cobalt Neo-Therm", "Inkbird Temperature Controller",
    "Pentair UV Sterilizer", "AquaUV Sterilizer", "Kamoer Doser", "GHL Profilux", "GHL Doser"
  ],
  Other: [
    "Live Rock", "Dry Rock", "Marco Rock", "CaribSea LifeRock", "Fiji Rock", "Pukani Rock",
    "Live Sand", "Aragonite Sand", "Crushed Coral", "Bare Bottom",
    "Macroalgae (Chaeto)", "Mangrove", "Caulerpa", "Dragon's Breath", "Gracilaria",
    "Copepods", "Amphipods", "Phytoplankton", "Rotifers"
  ]
};

export default function LivestockPage() {
  const [inhabitants, setInhabitants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("Equipment");
  const [visibleTabs, setVisibleTabs] = useState<string[]>(["Equipment"]);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCategoryDropdownOpen, setIsCategoryDropdownOpen] = useState(false);
  const [expandedNotes, setExpandedNotes] = useState<Record<number, boolean>>({});
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const autocompleteRef = useRef<HTMLDivElement>(null);

  // Form State
  const [formCategory, setFormCategory] = useState("Fish");
  const [formSpecies, setFormSpecies] = useState("");
  const [formName, setFormName] = useState("");
  const [formCount, setFormCount] = useState(1);
  const [formSize, setFormSize] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formImageUrl, setFormImageUrl] = useState("");
  const [formDateAdded, setFormDateAdded] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const PREDEFINED_CATEGORIES = ["Fish", "Coral", "Invertebrate", "Equipment", "Other"];

  useEffect(() => {
    fetchInhabitants();
    
    // Close dropdowns on outside click
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsCategoryDropdownOpen(false);
      }
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchInhabitants = async () => {
    try {
      const res = await fetch(`http://localhost:8000/get-inhabitants?t=${Date.now()}`);
      const data = await res.json();
      if (data.data) {
        setInhabitants(data.data);
        
        // Compute active tabs from data
        const cats = Array.from(new Set(data.data.map((i: any) => i.category || 'Fish'))) as string[];
        if (!cats.includes("Equipment")) cats.unshift("Equipment");
        
        // Merge with any manually added tabs that don't have data yet
        setVisibleTabs(prev => {
          const merged = new Set([...prev, ...cats]);
          return Array.from(merged);
        });

        // Smart default tab: select the first category that actually has items
        if (data.data.length > 0) {
          setActiveTab(data.data[0].category || "Fish");
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload-image", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.url) {
        setFormImageUrl(data.url);
      } else {
        alert("Upload failed. No URL returned.");
      }
    } catch (err) {
      console.error("Upload failed", err);
      alert("Error uploading image.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleEditItem = (item: any) => {
    setEditingItemId(item.id);
    setFormCategory(item.category || "Fish");
    setFormSpecies(item.species || "");
    setFormName(item.name || "");
    setFormCount(item.count || 1);
    setFormSize(item.size || "");
    setFormNotes(item.notes || item.care_info || "");
    setFormImageUrl(item.image_url || "");
    
    if (item.date_added) {
      // Convert to YYYY-MM-DD for the date input
      setFormDateAdded(new Date(item.date_added).toISOString().split('T')[0]);
    } else {
      setFormDateAdded("");
    }
    
    setIsModalOpen(true);
  };

  const handleDeleteItem = async () => {
    if (!editingItemId) return;
    if (!confirm(`Are you sure you want to delete this ${formCategory}?`)) return;
    
    try {
      const res = await fetch(`http://localhost:8000/delete-inhabitant/${editingItemId}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (!res.ok || data.status === "error") {
        alert("Failed to delete: " + (data.message || data.error || "Unknown Error"));
        return;
      }
      setIsModalOpen(false);
      setEditingItemId(null);
      fetchInhabitants();
    } catch (err) {
      console.error(err);
      alert("Network error while trying to delete.");
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const endpoint = editingItemId ? "update-inhabitant" : "add-inhabitant";
      
      const payload: any = {
        category: formCategory,
        species: formSpecies,
        name: formName,
        count: formCount,
        size: formSize,
        notes: formNotes,
        image_url: formImageUrl,
        care_info: formNotes
      };
      
      if (editingItemId) {
        payload.id = editingItemId;
      }
      
      if (formDateAdded) {
        // Date input gives YYYY-MM-DD, convert to ISO datetime format for backend
        payload.date_added = new Date(formDateAdded).toISOString();
      }

      const res = await fetch(`http://localhost:8000/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      const data = await res.json();
      if (!res.ok || data.status === "error") {
        alert("Failed to save: " + (data.message || data.error || "Unknown Error"));
        return;
      }
      
      setIsModalOpen(false);
      
      // Reset form
      setEditingItemId(null);
      setFormSpecies("");
      setFormName("");
      setFormCount(1);
      setFormSize("");
      setFormNotes("");
      setFormImageUrl("");
      setFormDateAdded("");
      
      // Switch tab to the category
      setActiveTab(formCategory);
      
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
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className={`relative w-full h-32 border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer overflow-hidden transition-all duration-300 ${
                      formImageUrl 
                        ? 'border-cyan-500 bg-black/50' 
                        : 'border-slate-700 bg-slate-800/30 hover:bg-slate-800/80 hover:border-slate-500'
                    }`}
                  >
                    {isUploading ? (
                      <div className="flex flex-col items-center text-cyan-400 animate-pulse">
                        <UploadCloud size={32} className="mb-2" />
                        <span className="text-sm font-bold">Uploading...</span>
                      </div>
                    ) : formImageUrl ? (
                      <>
                        <img src={formImageUrl} alt="Preview" className="absolute inset-0 w-full h-full object-cover opacity-60" />
                        <div className="relative z-10 flex flex-col items-center text-white drop-shadow-md bg-black/30 p-2 rounded-lg">
                          <ImageIcon size={24} className="mb-1" />
                          <span className="text-xs font-bold">Change Image</span>
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-col items-center text-slate-400">
                        <UploadCloud size={32} className="mb-2" />
                        <span className="text-sm font-medium">Click to upload photo</span>
                      </div>
                    )}
                    <input 
                      type="file" 
                      accept="image/*" 
                      className="hidden" 
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-5 gap-4">
                  <div className="col-span-3">
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                      {formCategory === 'Equipment' ? 'Make / Model' : 'Species / Type'}
                    </label>
                    <div className="relative" ref={autocompleteRef}>
                      <input 
                        type="text" 
                        value={formSpecies} 
                        onChange={(e) => {
                          setFormSpecies(e.target.value);
                          setShowSuggestions(true);
                        }}
                        onFocus={() => setShowSuggestions(true)}
                        placeholder={formCategory === 'Equipment' ? "e.g. Radion XR15" : "e.g. Yellow Tang"}
                        className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none placeholder-slate-600"
                        required
                        autoComplete="off"
                      />
                      {showSuggestions && formSpecies.length > 0 && filteredSuggestions.length > 0 && (
                        <ul className="absolute z-50 w-full bg-slate-800 border border-slate-600 rounded-lg mt-1 max-h-48 overflow-y-auto shadow-2xl overflow-hidden">
                          {filteredSuggestions.map(s => (
                            <li 
                              key={s}
                              className="px-4 py-2 text-sm text-slate-200 hover:bg-cyan-700 hover:text-white cursor-pointer transition-colors border-b border-slate-700/50 last:border-0"
                              onClick={() => {
                                setFormSpecies(s);
                                setShowSuggestions(false);
                              }}
                            >
                              {s}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                      Date Added
                    </label>
                    <input 
                      type="date" 
                      value={formDateAdded} 
                      onChange={(e) => setFormDateAdded(e.target.value)}
                      className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none placeholder-slate-600"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2">
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                      {formCategory === 'Equipment' ? 'Component Name (Optional)' : 'Name (Optional)'}
                    </label>
                    <input 
                      type="text" 
                      value={formName} 
                      onChange={(e) => setFormName(e.target.value)}
                      placeholder={formCategory === 'Equipment' ? "e.g. Main Return" : "e.g. Bubbles"}
                      className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none placeholder-slate-600"
                    />
                  </div>
                  <div className="col-span-1">
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                      Quantity
                    </label>
                    <input 
                      type="number" 
                      min="1"
                      value={formCount} 
                      onChange={(e) => setFormCount(parseInt(e.target.value) || 1)}
                      className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none"
                      required
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                    {formCategory === 'Equipment' ? 'Power / Rating (Optional)' : 'Size (Optional)'}
                  </label>
                  <input 
                    type="text" 
                    value={formSize} 
                    onChange={(e) => setFormSize(e.target.value)}
                    placeholder={formCategory === 'Equipment' ? "e.g. 150W" : "e.g. 2 inches"}
                    className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none placeholder-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                    {formCategory === 'Equipment' ? 'Maintenance Notes' : 'Notes & Care Info'}
                  </label>
                  <textarea 
                    value={formNotes} 
                    onChange={(e) => setFormNotes(e.target.value)}
                    placeholder={formCategory === 'Equipment' ? "Filter sock schedules, cleaning routine..." : "Feeding habits, quarantine info..."}
                    className="w-full h-24 bg-black/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:border-cyan-500 outline-none resize-none placeholder-slate-600"
                  />
                </div>
                
                <div className="mt-2 flex justify-between items-center gap-3 border-t border-slate-800 pt-5">
                  <div>
                    {editingItemId && (
                      <button 
                        type="button"
                        onClick={handleDeleteItem}
                        className="px-4 py-2 rounded-lg text-sm font-bold text-red-400 hover:text-white hover:bg-red-900/50 border border-transparent hover:border-red-500/50 transition-colors"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <button 
                      type="button" 
                      onClick={() => {
                        setIsModalOpen(false);
                        setEditingItemId(null);
                      }}
                      className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition-colors"
                    >
                      Cancel
                    </button>
                    <button 
                      type="submit"
                      disabled={isUploading}
                      className="bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-6 py-2 rounded-lg text-sm font-bold transition-colors shadow-lg"
                    >
                      {editingItemId ? 'Update' : 'Save'} {formCategory}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
