The paper and public docs for Med‑MMHL do not specify how many of the image–claim pairs are *medical* images (e.g., radiology, histology, clinical photographs) versus decorative or screenshots, and they never report such a breakdown. The multimodal fake‑news task statistics only distinguish counts of texts that have any image and the total number of images, not image type. [github](https://github.com/styxsys0927/Med-MMHL)

From Table 2 of the Med‑MMHL paper, we know that for the multimodal fake‑news/claim tasks there are: [arxiv](https://arxiv.org/pdf/2306.08871.pdf)

- Real claims: 643 text items, 641 with images, 749 total images.  
- Fake claims: 1,135 text items, 1,102 with images, 1,102 images.  

However, the authors only describe qualitative patterns in image type (decorative versus screenshots) and then define a filtering rule for which claim–image pairs are used in the multimodal benchmark (true claims from AFP Fact Check and false claims from CheckYourFact and PolitiFact) to avoid trivial cues. They do not further categorize images into “medical” (e.g., radiographs, microscopy) vs non‑medical, nor provide counts by such a category. [github](https://github.com/styxsys0927/Med-MMHL)

So, with the information currently available, the number of image‑claim pairs in Med‑MMHL that are *truly medical images* cannot be determined; you would have to download the dataset and manually or programmatically re‑annotate the images by type.