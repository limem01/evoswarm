'use client';

import { useState } from 'react';
import { Image as ImageIcon, X } from 'lucide-react';

export interface Screenshot {
  filename: string;
  url: string;
  timestamp: string;
}

interface ScreenshotViewerProps {
  screenshots: Screenshot[];
}

export default function ScreenshotViewer({
  screenshots,
}: ScreenshotViewerProps) {
  const [selected, setSelected] = useState<Screenshot | null>(null);

  if (screenshots.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-500">
        <ImageIcon size={40} className="mb-3" />
        <p className="text-sm">No screenshots captured</p>
      </div>
    );
  }

  return (
    <>
      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {screenshots.map((shot, index) => {
          const time = new Date(shot.timestamp).toLocaleTimeString();
          return (
            <button
              key={`${shot.filename}-${index}`}
              onClick={() => setSelected(shot)}
              className="group relative rounded-lg overflow-hidden border border-slate-700/50 hover:border-evo-primary/50 transition-all duration-200"
            >
              <img
                src={shot.url}
                alt={shot.filename}
                className="w-full h-32 object-cover bg-slate-900"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-200" />
              <div className="absolute bottom-0 left-0 right-0 px-2 py-1.5 bg-black/60 backdrop-blur-sm">
                <p className="text-xs text-white truncate">{shot.filename}</p>
                <p className="text-xs text-slate-400">{time}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Lightbox Modal */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setSelected(null)}
        >
          <div
            className="relative max-w-4xl max-h-[85vh] m-4"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelected(null)}
              className="absolute -top-3 -right-3 p-1.5 rounded-full bg-slate-800 border border-slate-600 text-slate-400 hover:text-white transition-colors z-10"
            >
              <X size={16} />
            </button>
            <img
              src={selected.url}
              alt={selected.filename}
              className="rounded-lg border border-slate-700/50 max-h-[80vh] object-contain"
            />
            <div className="mt-2 text-center">
              <p className="text-sm text-white">{selected.filename}</p>
              <p className="text-xs text-slate-400">
                {new Date(selected.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
