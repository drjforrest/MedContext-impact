import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import copyToClipboard from 'copy-to-clipboard';

/**
 * Generates a PDF from the results section and downloads it
 * @param {HTMLElement} element - The DOM element to convert to PDF
 * @param {string} filename - The filename for the downloaded PDF
 */
export const downloadAsPDF = async (element, filename = 'medcontext-results.pdf') => {
  if (!element) {
    console.error('Element not provided for PDF generation');
    return;
  }

  try {
    // Use html2canvas to capture the element
    const canvas = await html2canvas(element, {
      scale: 2, // Higher resolution
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#1c1e26', // Match the dark theme
    });
    
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const imgWidth = 210; // A4 width in mm
    const pageHeight = 297; // A4 height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    // Add additional pages if content is taller than one page
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, Math.abs(position), imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    pdf.save(filename);
  } catch (error) {
    console.error('Error generating PDF:', error);
    alert('There was an error generating the PDF. Please try again.');
  }
};

/**
 * Copies the results content to clipboard as plain text
 * @param {HTMLElement} element - The DOM element whose content to copy
 */
export const copyToClipboardText = (element) => {
  if (!element) {
    console.error('Element not provided for copying to clipboard');
    return;
  }

  try {
    // Extract text content from the element
    const textContent = element.innerText || element.textContent || '';
    
    // Copy to clipboard
    copyToClipboard(textContent);
    
    // Show success feedback
    alert('Results copied to clipboard!');
  } catch (error) {
    console.error('Error copying to clipboard:', error);
    alert('There was an error copying to clipboard. Please try again.');
  }
};

/**
 * Copies the results content to clipboard as HTML
 * @param {HTMLElement} element - The DOM element whose content to copy
 */
export const copyToClipboardHTML = (element) => {
  if (!element) {
    console.error('Element not provided for copying to clipboard');
    return;
  }

  try {
    // Get the HTML content of the element
    const htmlContent = element.innerHTML;
    
    // Create a temporary textarea to hold the HTML content
    const tempTextArea = document.createElement('textarea');
    tempTextArea.value = htmlContent;
    document.body.appendChild(tempTextArea);
    tempTextArea.select();
    
    // Copy the content
    document.execCommand('copy');
    
    // Clean up
    document.body.removeChild(tempTextArea);
    
    // Show success feedback
    alert('Results copied to clipboard as HTML!');
  } catch (error) {
    console.error('Error copying HTML to clipboard:', error);
    alert('There was an error copying to clipboard. Please try again.');
  }
};