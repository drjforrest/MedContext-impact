import copyToClipboard from 'copy-to-clipboard';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const LOGO_PATH = '/MedContext-Logo-Set/logo-w-tagline.png';

// Layout constants (mm, A4)
const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN = 10;
const HEADER_H = 28;   // reserved height for logo + title band
const FOOTER_H = 12;   // reserved height for footer
const CONTENT_W = PAGE_W - MARGIN * 2;
const CONTENT_H = PAGE_H - HEADER_H - FOOTER_H;

/**
 * Pre-load the logo as a base64 data URL so jsPDF can embed it.
 * Falls back gracefully if the image can't be fetched.
 * Returns an object with dataUrl and intrinsic dimensions, or null on failure.
 */
async function loadLogoDataUrl() {
  try {
    const res = await fetch(LOGO_PATH);
    if (!res.ok) return null;
    const blob = await res.blob();
    const dataUrl = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(blob);
    });
    if (!dataUrl) return null;
    // Load image to get intrinsic dimensions
    const img = await new Promise((resolve) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => resolve(null);
      image.src = dataUrl;
    });
    if (!img) return null;
    return { dataUrl, width: img.width, height: img.height };
  } catch {
    return null;
  }
}

/**
 * Draw branded header on the current PDF page.
 */
function drawHeader(pdf, logoInfo, timestamp) {
  // Header background
  pdf.setFillColor(28, 30, 38);        // #1c1e26
  pdf.rect(0, 0, PAGE_W, HEADER_H, 'F');

  // Accent line below header
  pdf.setFillColor(91, 141, 239);       // #5b8def
  pdf.rect(0, HEADER_H - 0.6, PAGE_W, 0.6, 'F');

  // Logo (left side) - preserve aspect ratio, max 20mm height
  if (logoInfo) {
    const { dataUrl, width, height } = logoInfo;
    const aspectRatio = width / height;
    const targetHeight = 20; // max height in mm
    const targetWidth = targetHeight * aspectRatio;
    pdf.addImage(dataUrl, 'PNG', MARGIN, 4, targetWidth, targetHeight);
  }

  // Title text
  const textX = logoInfo ? MARGIN + 23 : MARGIN;
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(14);
  pdf.setTextColor(233, 238, 244);       // #e9eef4
  pdf.text('MedContext Analysis Report', textX, 13);

  // Subtitle / timestamp
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(8.5);
  pdf.setTextColor(155, 160, 175);       // #9ba0af
  pdf.text(timestamp, textX, 19);
  pdf.text('Contextual Authenticity Assessment', textX, 23.5);
}

/**
 * Draw branded footer on the current PDF page.
 */
function drawFooter(pdf, pageNum, totalPages) {
  const footerY = PAGE_H - FOOTER_H;

  // Footer background
  pdf.setFillColor(28, 30, 38);
  pdf.rect(0, footerY, PAGE_W, FOOTER_H, 'F');

  // Accent line above footer
  pdf.setFillColor(45, 49, 66);          // #2d3142
  pdf.rect(0, footerY, PAGE_W, 0.4, 'F');

  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(7.5);
  pdf.setTextColor(107, 114, 128);       // #6b7280

  pdf.text('MedContext — Real images can mislead. We verify the claims, not just the image.', MARGIN, footerY + 5);
  pdf.text(`drjforrest.com`, MARGIN, footerY + 9);

  const pageLabel = `Page ${pageNum} of ${totalPages}`;
  pdf.text(pageLabel, PAGE_W - MARGIN - pdf.getTextWidth(pageLabel), footerY + 7);
}

/**
 * Generates a branded PDF from the results section and downloads it.
 */
export const downloadAsPDF = async (element, filename = 'medcontext-results.pdf') => {
  if (!element) return;

  try {
    // Load logo and capture DOM in parallel
    const [logoDataUrl, canvas] = await Promise.all([
      loadLogoDataUrl(),
      html2canvas(element, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#1c1e26',
      }),
    ]);

    const timestamp = new Date().toLocaleString(undefined, {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

    // Scale the captured content to fit within the content area
    const scaledImgHeight = (canvas.height * CONTENT_W) / canvas.width;
    const totalPages = Math.ceil(scaledImgHeight / CONTENT_H);
    const pixelsPerMM = canvas.height / scaledImgHeight;

    const pdf = new jsPDF('p', 'mm', 'a4');

    for (let page = 0; page < totalPages; page++) {
      if (page > 0) pdf.addPage();

      // Draw header & footer
      drawHeader(pdf, logoDataUrl, timestamp);
      drawFooter(pdf, page + 1, totalPages);

      // Slice the canvas for this page
      const srcY = Math.round(page * CONTENT_H * pixelsPerMM);
      const remaining = scaledImgHeight - page * CONTENT_H;
      const sliceH = Math.min(CONTENT_H, remaining);
      const slicePixelH = Math.round(sliceH * pixelsPerMM);

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = canvas.width;
      tempCanvas.height = slicePixelH;
      const ctx = tempCanvas.getContext('2d');
      ctx.drawImage(canvas, 0, srcY, canvas.width, slicePixelH, 0, 0, canvas.width, slicePixelH);

      const sliceData = tempCanvas.toDataURL('image/png');
      pdf.addImage(sliceData, 'PNG', MARGIN, HEADER_H, CONTENT_W, sliceH);
    }

    pdf.save(filename);
  } catch (error) {
    console.error('Error generating PDF:', error);
    alert('There was an error generating the PDF. Please try again.');
  }
};

/**
 * Copies the results content to clipboard as plain text.
 */
export const copyToClipboardText = (element) => {
  if (!element) return;

  try {
    const textContent = element.innerText || element.textContent || '';
    const success = copyToClipboard(textContent);
    alert(success ? 'Results copied to clipboard!' : 'Failed to copy results to clipboard');
  } catch (error) {
    console.error('Error copying to clipboard:', error);
    alert('There was an error copying to clipboard. Please try again.');
  }
};
