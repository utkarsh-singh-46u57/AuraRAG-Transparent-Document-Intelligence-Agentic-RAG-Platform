import React, { useState, useEffect, useRef } from 'react';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, FileText, Maximize2 } from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';
import { useApp } from '../../context/AppContext';
import { getDocumentFileUrl } from '../../services/api';

// Set up worker
try {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
} catch (e) {
  console.warn('PDF.js worker setup fallback', e);
}

export const PDFViewerModal: React.FC = () => {
  const {
    isPDFModalOpen,
    setIsPDFModalOpen,
    activeDocument,
    sessionId,
    currentPDFPage,
    setCurrentPDFPage,
    highlightBbox,
    selectedCitation
  } = useApp();

  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.2);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isPDFModalOpen || !activeDocument) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    const docUrl = getDocumentFileUrl(activeDocument.document_id, sessionId);

    pdfjsLib.getDocument(docUrl).promise.then(
      (loadedPdf) => {
        if (!isMounted) return;
        setPdfDoc(loadedPdf);
        setTotalPages(loadedPdf.numPages);
        setLoading(false);
      },
      (err) => {
        if (!isMounted) return;
        console.error('Failed to load PDF doc', err);
        setError('Failed to load PDF document.');
        setLoading(false);
      }
    );

    return () => {
      isMounted = false;
    };
  }, [isPDFModalOpen, activeDocument, sessionId]);

  // Render the current page onto canvas
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    let isRenderCancelled = false;
    const pageNum = Math.min(Math.max(1, currentPDFPage), totalPages);

    pdfDoc.getPage(pageNum).then((page: any) => {
      if (isRenderCancelled) return;
      const viewport = page.getViewport({ scale });
      const canvas = canvasRef.current;
      if (!canvas) return;

      const context = canvas.getContext('2d');
      if (!context) return;

      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport
      };

      page.render(renderContext);
    });

    return () => {
      isRenderCancelled = true;
    };
  }, [pdfDoc, currentPDFPage, scale, totalPages]);

  if (!isPDFModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-150">
      <div className="relative w-full max-w-5xl h-[90vh] glass-panel rounded-2xl flex flex-col overflow-hidden shadow-2xl border border-purple-500/30">
        
        {/* Header Toolbar */}
        <div className="h-14 px-5 border-b border-purple-500/20 flex items-center justify-between bg-black/40">
          <div className="flex items-center space-x-3 overflow-hidden">
            <FileText className="w-4 h-4 text-purple-400 flex-shrink-0" />
            <span className="text-xs font-semibold text-slate-100 truncate">
              {activeDocument?.filename || 'PDF Document'}
            </span>
            {selectedCitation && (
              <span className="px-2 py-0.5 rounded bg-purple-900/60 border border-purple-500/30 text-purple-300 font-mono text-[10px]">
                Target: Page {selectedCitation.page} • {selectedCitation.chunk_id}
              </span>
            )}
          </div>

          {/* Navigation & Zoom controls */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 bg-black/50 px-2 py-1 rounded-lg border border-purple-500/20 text-xs font-mono">
              <button
                onClick={() => setCurrentPDFPage(Math.max(1, currentPDFPage - 1))}
                disabled={currentPDFPage <= 1}
                className="p-1 rounded text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="text-purple-300 px-1.5 font-medium">
                {currentPDFPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPDFPage(Math.min(totalPages, currentPDFPage + 1))}
                disabled={currentPDFPage >= totalPages}
                className="p-1 rounded text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Zoom */}
            <div className="flex items-center space-x-1 bg-black/50 px-1.5 py-1 rounded-lg border border-purple-500/20 text-xs">
              <button
                onClick={() => setScale(prev => Math.max(0.6, prev - 0.2))}
                className="p-1 rounded text-slate-400 hover:text-white transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[11px] font-mono text-slate-300 px-1">
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={() => setScale(prev => Math.min(2.5, prev + 0.2))}
                className="p-1 rounded text-slate-400 hover:text-white transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
            </div>

            <button
              onClick={() => setIsPDFModalOpen(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors ml-2"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* PDF Canvas Viewport Container */}
        <div
          ref={containerRef}
          className="flex-1 overflow-auto p-6 flex justify-center bg-black/50"
        >
          {loading && (
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="w-8 h-8 rounded-full border-2 border-purple-500 border-t-transparent animate-spin" />
              <p className="text-xs text-purple-300 font-mono">Loading PDF pages...</p>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center text-rose-400 text-xs">
              {error}
            </div>
          )}

          <div className="relative inline-block shadow-2xl rounded border border-purple-500/20">
            <canvas ref={canvasRef} className="block rounded" />

            {/* Coordinate Highlight Overlay */}
            {highlightBbox && selectedCitation?.page === currentPDFPage && (
              <div
                className="absolute border-2 border-purple-400 bg-purple-500/25 rounded pointer-events-none transition-all duration-300 shadow-[0_0_15px_rgba(168,85,247,0.5)] animate-pulse"
                style={{
                  left: `${highlightBbox[0]}%`,
                  top: `${highlightBbox[1]}%`,
                  width: `${Math.max(2, highlightBbox[2] - highlightBbox[0])}%`,
                  height: `${Math.max(2, highlightBbox[3] - highlightBbox[1])}%`,
                }}
              />
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
