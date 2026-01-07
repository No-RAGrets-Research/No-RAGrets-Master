import { useEffect, useRef, useState } from 'react';
import type { BoundingBox } from '../../types';

interface BoundingBoxOverlayProps {
  bboxes: Array<{
    page: number;
    bbox: BoundingBox;
  }>;
  currentPage: number;
  scale: number;
  pageWidth: number;
  pageHeight: number;
}

export const BoundingBoxOverlay = ({
  bboxes,
  currentPage,
  scale,
  pageWidth,
  pageHeight,
}: BoundingBoxOverlayProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Update canvas dimensions when scale or page changes
  useEffect(() => {
    const width = pageWidth * scale;
    const height = pageHeight * scale;
    setDimensions({ width, height });
  }, [pageWidth, pageHeight, scale]);

  // Draw bounding boxes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Filter bboxes for current page
    const pageBboxes = bboxes.filter((b) => b.page === currentPage);

    // Draw each bounding box
    pageBboxes.forEach(({ bbox }) => {
      // Convert PDF coordinates to canvas coordinates
      // PDF uses points (1/72 inch), we need to scale appropriately
      let x, y, width, height;

      if (bbox.coord_origin === 'BOTTOMLEFT') {
        // Bottom-left origin: (0,0) is bottom-left corner
        x = bbox.l * scale;
        y = (pageHeight - bbox.t) * scale; // Flip Y coordinate
        width = (bbox.r - bbox.l) * scale;
        height = (bbox.t - bbox.b) * scale;
      } else {
        // Top-left origin: (0,0) is top-left corner
        x = bbox.l * scale;
        y = bbox.t * scale;
        width = (bbox.r - bbox.l) * scale;
        height = (bbox.b - bbox.t) * scale;
      }

      // Draw semi-transparent yellow rectangle
      ctx.fillStyle = 'rgba(255, 255, 0, 0.3)';
      ctx.fillRect(x, y, width, height);

      // Draw border
      ctx.strokeStyle = 'rgba(255, 200, 0, 0.8)';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, width, height);
    });
  }, [bboxes, currentPage, scale, pageWidth, pageHeight, dimensions]);

  if (dimensions.width === 0 || dimensions.height === 0) return null;

  return (
    <canvas
      ref={canvasRef}
      width={dimensions.width}
      height={dimensions.height}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        pointerEvents: 'none',
        zIndex: 10,
      }}
    />
  );
};
