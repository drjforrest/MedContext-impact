Medical misinformation kills, and is challenging to detect with high accuracy.

We addressed this by developing an agentic system that detects a two-dimensional property we call contextual authenticity, composed of claim veracity (are the words true?) and image-context alignment (does the image support the claim?). Added to image integrity forensics, source verification, and blockchain provenance auditing, MedContext is a comprehensive suite for verifying truth.

Let's demo it. First, a story from the Kenyan news. I've uploaded an image and caption: "This is the HIV virus under a microscope." The claim is plausible on its own. But after processing, MedContext correctly identifies this image as a caterpillar, not HIV, and correctly labels this as misinformation.

Next is a post shared more than 16,000 times containing a sketch of a cell: "This is the most detailed image of a human cell to date, obtained using X-ray and electron microscopy." First, it assesses veracity and alignment; a synthesizing agent then computes scores and generates rationale. Misinformation likely missed by current tools—caught by MedContext with its multimodal, medically-trained approach.

One more. I've uploaded a malaria rapid diagnostic test captioned, "Positive malaria RDT showing infection. The control line confirms test validity; the Pf line indicates active or recent infection." Even though its model is running locally, it correctly identifies two lines as positive and verifies this as true.

Validation of MedContext powered by MedGemma Q4, and its unique detection methods for contextual authenticity approach, was conducted on 163 random samples from the Medical Multimodal Misinformation benchmark. And in partnership with Counterforce AI and the University of British Columbia, we implemented real-time monitoring of the Telegram bot and web app in the field.

Results showed that alignment is the dominant signal. Veracity alone achieved only 74% accuracy—insufficient for deployment. But veracity provides a critical safety net when alignment cannot resolve. The combined system achieves 91% accuracy with 96% precision. While this improvement appears modest, it translates to 27 million more accurate classifications daily across the 3 biggest social media networks.

And with thanks to the MedGemma Impact Challenge, MedContext is empirically-validated and production-ready.
