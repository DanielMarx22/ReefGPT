"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Camera, Trash2, Upload, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MediaGalleryProps {
  id: string;
  type: 'single-image' | 'gallery';
  title?: string;
  onRemove?: (id: string) => void;
}

export default function MediaGallery({ id, type, title = "Tank Progression", onRemove }: MediaGalleryProps) {
  const [images, setImages] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load from local storage
  useEffect(() => {
    const saved = localStorage.getItem(`media_${id}`);
    if (saved) {
      try {
        setImages(JSON.parse(saved));
      } catch (e) {}
    }
  }, [id]);

  // Gallery auto-rotation
  useEffect(() => {
    if (type !== 'gallery' || images.length <= 1) return;
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % images.length);
    }, 5000); // 5 seconds
    return () => clearInterval(interval);
  }, [type, images.length]);

  const saveImages = (newImages: string[]) => {
    setImages(newImages);
    try {
      localStorage.setItem(`media_${id}`, JSON.stringify(newImages));
    } catch (err) {
      console.error("Failed to save to local storage (quota exceeded?)", err);
    }
  };

  const compressImage = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const MAX_WIDTH = 800; // Resize heavily to avoid local storage limits
          const MAX_HEIGHT = 800;
          let width = img.width;
          let height = img.height;

          if (width > height) {
            if (width > MAX_WIDTH) {
              height *= MAX_WIDTH / width;
              width = MAX_WIDTH;
            }
          } else {
            if (height > MAX_HEIGHT) {
              width *= MAX_HEIGHT / height;
              height = MAX_HEIGHT;
            }
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx?.drawImage(img, 0, 0, width, height);
          
          // Export as highly compressed JPEG
          resolve(canvas.toDataURL('image/jpeg', 0.6));
        };
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // Compress all selected files
    const promises = files.map(file => compressImage(file));
    const base64Images = await Promise.all(promises);

    if (type === 'single-image') {
      saveImages([base64Images[0]]); // overwrite
    } else {
      saveImages([...images, ...base64Images].slice(0, 10)); // cap at 10
    }
    
    // Reset file input
    if (fileInputRef.current) {
       fileInputRef.current.value = "";
    }
  };

  const removeImage = (index: number) => {
    const newImages = [...images];
    newImages.splice(index, 1);
    saveImages(newImages);
    if (currentIndex >= newImages.length) {
      setCurrentIndex(Math.max(0, newImages.length - 1));
    }
  };

  return (
    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden p-6 flex flex-col gap-4 shadow-2xl relative group">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-xl font-bold text-white flex gap-2 items-center">
          <Camera size={20} className="text-cyan-400" /> 
          {type === 'single-image' ? 'Single Photo' : title}
        </h3>
        {onRemove && (
          <button onClick={() => onRemove(id)} className="text-slate-500 hover:text-red-400 transition-colors z-20">
            <Trash2 size={16} />
          </button>
        )}
      </div>

      <div className="relative">
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept="image/*"
          multiple={type === 'gallery'}
          onChange={handleFileUpload}
        />

        {images.length === 0 ? (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="w-full h-[180px] rounded-lg border-2 border-dashed border-slate-700 bg-slate-900/50 hover:bg-slate-800/50 hover:border-cyan-500/50 transition-colors flex flex-col items-center justify-center cursor-pointer text-slate-500 hover:text-cyan-400 group/upload"
          >
            <Upload size={32} className="mb-2 opacity-50 group-hover/upload:opacity-100" />
            <span className="text-sm font-medium">Click to upload photo{type === 'gallery' ? 's' : ''}</span>
          </div>
        ) : type === 'single-image' ? (
          <div className="w-full h-[220px] rounded-lg bg-slate-800/80 relative overflow-hidden group/img border border-white/5">
            <img src={images[0]} alt="Tank" className="w-full h-full object-cover" />
            <div className="absolute top-2 right-2 opacity-0 group-hover/img:opacity-100 transition-opacity">
              <button 
                onClick={(e) => { e.stopPropagation(); removeImage(0); }}
                className="bg-black/60 hover:bg-red-900/80 text-white p-1.5 rounded backdrop-blur-md"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ) : (
          <div className="w-full h-[220px] rounded-lg bg-slate-800/80 relative overflow-hidden group/img border border-white/5">
            <AnimatePresence mode="wait">
              <motion.img 
                key={currentIndex}
                src={images[currentIndex]} 
                alt="Tank" 
                className="w-full h-full object-cover absolute inset-0" 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.8 }}
              />
            </AnimatePresence>
            
            <div className="absolute top-2 right-2 opacity-0 group-hover/img:opacity-100 transition-opacity flex gap-2 z-20">
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="bg-black/60 hover:bg-cyan-900/80 text-white p-1.5 rounded backdrop-blur-md"
                title="Add Photo"
              >
                <Plus size={14} />
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); removeImage(currentIndex); }}
                className="bg-black/60 hover:bg-red-900/80 text-white p-1.5 rounded backdrop-blur-md"
                title="Remove Photo"
              >
                <Trash2 size={14} />
              </button>
            </div>
            
            <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5 z-20">
              {images.map((_, i) => (
                <div 
                  key={i} 
                  className={`h-1.5 rounded-full transition-all duration-300 ${i === currentIndex ? 'w-5 bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]' : 'w-1.5 bg-white/40'}`} 
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
