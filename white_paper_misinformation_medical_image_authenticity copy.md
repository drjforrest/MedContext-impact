# Medical Misinformation of Authentic Imaging: A Comprehensive Literature Review

## Abstract

Medical misinformation disseminated through images with false or misleading context represents an escalating public health threat in the digital age. This comprehensive literature review synthesizes evidence on the prevalence, taxonomies, examples, and mitigation strategies for visual medical misinformation, with particular emphasis on out-of-context (OOC) imagery—authentic images repurposed with deceptive narratives. Analysis of nearly 100 sources reveals that 87% of social media posts about popular medical tests mention benefits while only 15% acknowledge harms, with 68% of influencers maintaining undisclosed financial interests. During COVID-19's initial months, visuals appeared in over half of analyzed misinformation, predominantly as mislabeled authentic content rather than sophisticated manipulations. Detection methods span reverse image search tools, AI-powered forensic analysis, and blockchain authentication, while interventions include media literacy programs (effect size d=0.60), fact-checking labels (27.6% reduction in belief), and inoculation-based "prebunking" strategies. Healthcare professionals occupy a pivotal but underutilized position in combating this phenomenon, facing institutional barriers despite public trust ratings exceeding 80%. The review identifies critical research gaps including insufficient focus on misinformation driving medical overuse, limited understanding of platform-specific visual dynamics, and nascent frameworks for AI-generated medical image governance.

## Introduction

The proliferation of health misinformation online, particularly in social media, has been characterized by the World Health Organization as an "infodemic", defined as a deluge of false information that rivals the pandemic itself in its capacity to undermine public health. While textual misinformation has received substantial scholarly attention, visual misinformation remains comparatively understudied despite its unique persuasive power and ubiquity on image-centric platforms like Instagram and TikTok. Visual content's cognitive advantages—enhanced emotional arousal, improved memorability, and perceived evidentiary weight—render it particularly effective at conveying both truths and falsehoods.[1][2][3][4][5][6]
Out-of-context (OOC) medical misinformation, where authentic images are repurposed with false or misleading captions, represents one of the most prevalent and insidious forms of visual deception. This "cheapfake" approach requires minimal technical sophistication yet achieves remarkable effectiveness by exploiting the public's tendency to accept visual evidence at face value. A recent analysis of nearly 1,000 social media posts about medical screening tests—reaching approximately 200 million followers—found that 87% highlighted benefits while only 15% mentioned potential harms, and merely 6% acknowledged risks of overdiagnosis. This asymmetry exemplifies how visual medical content, when divorced from appropriate context or balanced information, can systematically mislead audiences toward potentially harmful health decisions.[4][7][8][9][10][11][12][13][14]
The COVID-19 pandemic crystallized the urgency of addressing visual health misinformation. Analysis of 96 misinformation instances from early 2020 revealed that visuals in over half explicitly served as purported evidence for false claims. Contrary to fears about sophisticated synthetic manipulations, most manipulations employed rudimentary tools, with mislabeled authentic images dominating the landscape. This pattern—authentic content weaponized through recontextualization—underscores a fundamental challenge: the problem is not primarily technological sophistication but rather the strategic exploitation of credibility cues inherent to visual media.[15][16][1]

## Prevalence and Scope

### Quantitative Evidence from Platform Studies

Recent empirical investigations provide alarming estimates of visual medical misinformation prevalence across major social media platforms. A landmark study analyzing 982 posts on Instagram and TikTok about five controversial medical tests (full-body MRI, multicancer early detection, antimüllerian hormone testing, coronary artery calcium scans, and continuous glucose monitors) revealed systematic patterns of misleading content. With a combined reach of 194 million followers, these posts demonstrated:[9][10]

- 87.1% mentioned test benefits versus 14.7% mentioning harms
- Only 6.1% referenced overdiagnosis or overtreatment risks
- Merely 6.4% cited scientific evidence
- 68% of account holders maintained explicit financial interests in test promotion
- Only 15.9% originated from identifiable physicians[10][9]
  The researchers characterized this landscape as an "open sewer of medical misinformation," noting that posts overwhelmingly adopted promotional rather than educational tones. Importantly, physician-created content proved more balanced, with significantly higher likelihood of mentioning harms and lower propensity for promotional framing, suggesting that credentialed professional engagement could partially offset pervasive commercial incentives.[9][10]

### COVID-19 as a Case Study in Visual Misinformation

The COVID-19 pandemic provided an unprecedented natural experiment for studying health misinformation dynamics. Brennen et al.'s mixed-methods analysis of 96 fact-checked misinformation examples from January-March 2020 identified six dominant frames: authoritative agency, virulence, medical efficacy, intolerance, prophecy, and satire. Visuals in 52% of cases explicitly functioned as evidence for false claims, with the vast majority representing mislabeled authentic content rather than manipulated imagery. Notably, sophisticated synthetic manipulations were entirely absent; all detected manipulations utilized accessible editing tools.[16][17][1][15]
This pattern diverges from apocalyptic narratives surrounding AI-generated content, suggesting that effective interventions must address not merely technological detection challenges but the broader information ecosystem enabling authentic imagery to be systematically divorced from accurate context. A subsequent scoping review synthesizing 70 sources on online health misinformation confirmed these findings, documenting consensus regarding misinformation's prevalence across platforms and its disproportionate impact on vulnerable populations facing social and economic inequalities.[2][3]

### Research Image Fraud

Beyond public-facing social media, medical image fraud extends into scientific research itself. A survey of 284 nuclear medicine researchers revealed that 13.7% admitted falsifying medical images within the preceding five years, while 38.7% reported witnessing colleagues engage in such practices. Common forms included cherry-picking images, unauthorized reuse, and misleading enhancements. While 1.1% acknowledged using AI to falsify images and 2.8% observed colleagues doing so, these percentages are likely to increase as generative AI capabilities become more accessible. Key drivers included publication pressure, competitive incentives, and aesthetic expectations imposed by journals.[18]
The implications extend beyond academic integrity to patient safety. Manipulated medical images in research can propagate false treatment standards, while fraudulent clinical images risk diagnostic errors and inappropriate interventions. Recent research demonstrates that AI-generated medical images—though potentially useful for training datasets when properly disclosed—can achieve such fidelity that radiologists cannot distinguish them from authentic scans, raising profound concerns about authentication protocols in clinical settings.[19][20][21][22][23]

### Taxonomies and Conceptual Frameworks

#### Three-Category Framework for Visual Misinformation

Heley et al. propose a tripartite taxonomy distinguishing visual misinformation by manipulation type:[5][4]

1. Visual Manipulation: Altering original visual content through editing

- Techniques: Photo enhancement, element addition/removal, color/lighting adjustment
- Medical context: Manipulated body images promoting unrealistic health standards, altered medical charts exaggerating treatment efficacy
- Includes sophisticated synthetic manipulations and simple touch-ups alike

2. Visual Misrepresentation: Using authentic visuals in misleading contexts

- Most prevalent category for medical misinformation[12][4]
- Also termed "cheapfakes" or "visual recontextualization"[13][14][4]
- Techniques: Out-of-context imagery, strategic cropping, mislabeling
- Example: Authentic image of hospital overflow from one country/time period presented as evidence of crisis elsewhere

3. Visual Fabrication: Creating entirely synthetic content

- Synthetic manipulations and AI-generated imagery
- Example: Fabricated medical scans showing non-existent conditions
- Growing concern as generative AI becomes more sophisticated and accessible[20][21][24]

### Functional Roles of Visuals in Misinformation

Complementing structural taxonomies, functional frameworks illuminate how visuals operate within misinformation ecosystems. Brennen et al. identify three primary functions:[17][1][15]
Illustration and Selective Emphasis: Visuals highlight particular narrative elements while obscuring others, directing attention toward conclusions favored by misinformation creators. For instance, images of crowded hospitals during COVID-19 illustrated narratives about either dangerous virulence (when authentic) or manufactured crisis (when misattributed).
Purported Evidence: Visuals masquerade as proof for claims, exploiting the psychological tendency to privilege visual information. Medical charts, laboratory imagery, and clinical photographs carry particular evidentiary weight, making their misuse especially pernicious.
Authority Impersonation: Visuals deploy credibility signifiers—white coats, institutional logos, medical equipment—to manufacture legitimacy for false information. The mere presence of these visual cues can bypass critical evaluation, particularly when audiences lack domain expertise to assess substantive accuracy.[4][5]

## Examples and Case Studies

### Medical Test Promotion on Social Media

The University of Sydney study examining 982 posts about five medical tests provides granular insights into contemporary visual medical misinformation. Full-body MRI scans, marketed as capable of detecting 500+ conditions, were promoted without evidence of benefit for asymptomatic populations and without disclosure of overdiagnosis risks. Multicancer early detection tests, still undergoing clinical trials, were advertised as screening tools for 50+ cancers despite absence of evidence that benefits would outweigh harms.[10][9]
Visual strategies included:

- Personal testimonials featuring before/after imagery
- Aesthetic medical facility photography suggesting high-quality care
- Graphics highlighting benefits while omitting harms
- Influencer endorsements leveraging parasocial relationships
- Strategic deployment of medical iconography (imaging equipment, laboratory settings) to connote scientific legitimacy
  Financial conflicts pervaded this landscape, with 68% of creators maintaining promotional relationships with test providers—yet these conflicts were rarely disclosed transparently. The study documented that physicians' posts were significantly more balanced, with odds ratios indicating 5-6 times greater likelihood of mentioning harms compared to non-physician creators.[9][10]

### COVID-19 Visual Misinformation Frames

The six frames identified in COVID-19 visual misinformation reveal how images construct distinct narratives:[1][17]
Authoritative Agency (29%): Visuals depicted government buildings, health officials, or institutional settings to make claims about policies or responses, often misrepresenting actual governmental positions or actions.
Virulence (28%): Images purportedly showing disease spread, severity, or mortality, frequently recycled from unrelated events or contexts to exaggerate or minimize pandemic severity.
Medical Efficacy (29%): Visuals suggested availability of cures, treatments, or preventatives, often featuring medical equipment, medications, or clinical settings to lend credibility to unproven interventions.
Intolerance (15%): Images deployed to advance racist, xenophobic, or discriminatory narratives about disease origins or affected populations.
Prophecy (10%): Visuals claiming pandemic prediction, often featuring old documents, books, or media retrospectively recontextualized.
Satire (6%): Humorous or satirical images that could be mistaken for factual claims when stripped of original context.

### Fabricated Medical Credibility

A particularly concerning development involves AI-generated synthetic manipulations impersonating medical professionals. Full Fact's investigation uncovered numerous TikTok videos featuring manipulated footage of Prof. David Taylor-Robinson and other medical experts, altered to promote supplements and discuss fabricated conditions like "thermometer leg". These synthetic manipulations achieved remarkable fidelity, with one featuring misogynistic language inappropriately attributed to the real physician. Platform removal required six weeks despite clear violations, illustrating challenges in content moderation at scale.[25]

## Detection and Mitigation Strategies

### Technological Detection Approaches

Reverse Image Search: The most accessible detection method leverages tools like Google Images, TinEye, and Yandex to trace image provenance. The WHO explicitly recommends reverse image searching as a habitual practice for evaluating online health content. This approach proved effective during COVID-19 for identifying recycled imagery from previous events or different geographical contexts.[26][27][28][29][4]
AI-Powered Forensic Analysis: Machine learning approaches have advanced substantially for detecting both OOC misinformation and synthetic imagery:

- Multimodal Large Language Models (MLLMs): Recent architectures like Sniffer, E2LVLM, and CMIE leverage vision-language integration to assess image-text consistency and generate explanations for detected inconsistencies. These systems outperform earlier approaches by 40%+ in detection accuracy while providing interpretable rationales.[8][30][31][32]
- Scene-Graph Based Methods: LLaVA-SNIPPER employs structured scene graphs to capture fine-grained semantic relationships, enabling transparent reasoning about cross-modal inconsistencies.[31]
- Evidence Retrieval and Reranking: E2LVLM and similar frameworks retrieve external evidence about authentic image contexts, then rerank and rewrite this evidence to align with LVLM inputs, achieving state-of-the-art performance on benchmark datasets.[30]
  Medical Image Forensics: Specialized approaches target clinical imagery:
- Copy-Move Forgery Detection: Algorithms identify duplicated regions within medical images, crucial for detecting research fraud. Recent methods achieve 90%+ precision and recall on medical datasets.[33][34]
- AI-Generated Image Detection: The MedForensics dataset encompasses six imaging modalities and twelve generative models, enabling development of detectors like DSKI (Dual-Stage Knowledge Infusing) that outperform general-purpose synthetic image detectors on medical content.[24][35]
- Watermarking and Blockchain Authentication: Crypto-watermarking embeds cryptographic signatures in medical images for authenticity verification while preserving diagnostic quality. Blockchain-based approaches create immutable audit trails for medical image provenance.[36][37][38][39]

### Educational Interventions

Media Literacy Programs: A meta-analysis of 49 experimental studies (N=81,155) demonstrates that media literacy interventions significantly improve resilience to misinformation (d=0.60 overall). Specific effects include:[40]

- Reduced belief in misinformation (d=0.27)
- Improved misinformation discernment (d=0.76)
- Decreased sharing intent (d=1.04)[40]
  Interventions prove more effective when delivered across multiple sessions rather than single exposures, and when culturally tailored to local contexts. Visual multimedia integration enhances effectiveness; participants receiving video-based education showed superior knowledge retention compared to text-only formats.[41][42][43][40]
  The "lateral reading" technique—borrowed from professional fact-checkers—teaches individuals to research authors, organizations, and citations using independent sources before engaging deeply with content. When implemented with third-year medical students through experiential learning, this approach significantly improved bias and misinformation detection capabilities.[44]
  Health-Specific Media Literacy: Targeted health literacy interventions face unique challenges. While health-focused programs increased skepticism of both accurate and inaccurate cancer news headlines (5.6% and 7.6% decreases in endorsement respectively), they did not improve overall discernment between the two. This suggests that domain-general critical thinking may prove more effective than health-specific heuristics that risk indiscriminate skepticism. Conversely, visual-based health interventions—using videos, pictograms, and multimedia—consistently improve comprehension of health-related material with effect sizes exceeding traditional text-based methods.[45][46][47]

### Inoculation Theory and Prebunking

Psychological inoculation—exposing individuals to weakened doses of misinformation techniques before encountering actual misinformation—has emerged as a promising prophylactic strategy. Analogous to vaccination, inoculation builds "cognitive antibodies" against manipulation tactics.[48][49][50][51]
The "Bad News" game, which teaches players to recognize common misinformation strategies through gamified role-playing, demonstrates cross-cultural effectiveness across Sweden, Germany, Poland, and Greece. Participants show significant reductions in perceived reliability of manipulative content, with effects persisting regardless of age, gender, education level, or political ideology. Crucially, the game does not inspire participants to create misinformation themselves, addressing a key concern about educational interventions.[49][50]
Meta-analyses confirm inoculation's effectiveness at reducing vulnerability to persuasion, with particular promise for health contexts where preventative approaches can preempt belief formation. Emergency physicians have adapted these principles for clinical encounters and social media engagement, developing frameworks that integrate inoculation with patient-centered communication.[51][52][48]

## Platform-Level Solutions

Fact-Checking and Warning Labels: Meta-analyses across 21 experiments (N=14,133) reveal that warning labels from professional fact-checkers reduce belief in false headlines by 27.6% and sharing intent by 24.7%. Critically, these effects persist even among individuals distrusting fact-checkers, with reductions of 12.9% (belief) and 16.7% (sharing) in the most skeptical subgroup.[53]
Label design matters substantially:

- Visibility: Within-frame placement outperforms below-content positioning[54]
- Color: Blue labels increase awareness by 15 percentage points versus light gray[54]
- Content: Disputed labels (explicitly contradicting claims) prove more effective than neutral warnings[55]
- Modality: Pictorial warnings outperform text-only alternatives, generating stronger emotional responses and behavioral intentions[56][57]
  However, warning labels face limitations. Meta's shift away from third-party fact-checking toward community notes has raised concerns about reduced effectiveness. Additionally, labels risk inadvertent amplification—corrective content generates engagement that algorithms may promote, potentially expanding rather than containing misinformation's reach.[58][59][9]
  Algorithmic Interventions: Social media algorithms fundamentally shape information exposure, yet their opacity complicates intervention design. Observational evidence from Twitter indicates that low-credibility COVID-19 and climate content achieves higher impressions than high-credibility equivalents, particularly for high-engagement, high-follower accounts. This algorithmic amplification reflects platforms' engagement-optimization imperatives, which privilege emotionally arousing content regardless of veracity.[60][61][62][63]
  Proposed interventions include:
- Promoting credible sources in recommendation algorithms
- Reducing visibility of content from accounts with histories of misinformation
- Prioritizing educational content over engagement metrics for health topics
- Implementing "friction" (e.g., prompts to read articles before sharing)[64]
  Pinterest's approach to vaccine searches—surfacing only content from authoritative health organizations—demonstrates feasibility of aggressive curation, though such interventions raise concerns about information access and paternalism.[64]

## Role of Healthcare Professionals

Healthcare professionals occupy a uniquely trusted position, with 81% of North Americans ranking physicians as their most trusted health information source, followed by pharmacists and nurses (both 79%). This credibility translates to substantial influence: physician recommendations for influenza vaccination increase uptake rates twofold, while HPV vaccine recommendations yield ninefold increases.[65][66]
Despite this potential, healthcare professionals face significant barriers to social media engagement:[67][68][69]
Intrapersonal Barriers:

- Lack of positive outcomes or recognition for correction efforts
- Time constraints amid clinical responsibilities
- Absence of training in misinformation detection and rebuttal strategies
  Interpersonal Barriers:
- Harassment and bullying from misinformation advocates
- Threats to professional reputation
- Emotional toll of persistent engagement with hostile audiences
  Institutional Barriers:
- Lack of employer support or encouragement
- Restrictive social media policies that deter professional engagement
- Absence of social media training in medical education
  Bautista et al.'s conceptual framework describes healthcare professionals' correction process as two-phased: authentication (internal and external verification of content accuracy) followed by correction actions (preparation and dissemination). Preparation involves reflecting on approach, disclosing expertise, connecting with affected individuals, and demonstrating respect. Correction encompasses private priming (direct messages), public priming (general educational content), public rebuttals (direct contradiction), and private rebuttals (one-on-one correction).[68]
  Recommendations for overcoming barriers include institutional social media training, development of professional guidelines specific to misinformation correction, cultivation of mentorship networks, and revision of hospital policies to support rather than deter physician engagement. The Netherlands Medical Association's TikTok campaign targeting vaping misinformation demonstrates successful orchestration—collaboration with media specialists, coordinated messaging across multiple physicians, and strategic platform selection yielded substantial reach and engagement.[52][66][69][67][68]

## Algorithmic Amplification and Engagement Dynamics

Social media algorithms, designed to maximize user engagement, inadvertently amplify misinformation by privileging emotionally arousing content over accuracy. Analysis of WeChat, Weibo, and video platforms in China revealed that health misinformation with negative sentiment generated significantly higher interactivity than neutral or positive content. Similarly, TikTok analysis of OCD-related content found that stereotype-driven videos—reinforcing misconceptions—received more views, likes, and shares than accurate educational content from healthcare providers.[61][63][70][60]
This dynamic reflects a fundamental misalignment between platform incentives (engagement, time-on-platform, advertising revenue) and public health goals (accurate information dissemination, informed decision-making). McLoughlin et al. argue that both human attentional biases and algorithmic amplification are individually insufficient to explain misinformation sharing; rather, their interaction creates a multiplicative effect whereby algorithms learn to surface content that triggers cognitive biases, while user engagement signals train algorithms to amplify similar content.[63]
The NewsCLIPpings dataset—a benchmark for OOC detection containing automatically generated image-caption mismatches from news media—illustrates the realistic threat of machine-driven image repurposing. By leveraging CLIP and other multimodal models, researchers demonstrated that convincing mismatches can be generated at scale, fooling both humans and automated detectors approximately 50% of the time in adversarially filtered scenarios. This underscores that technological solutions for OOC detection must contend not only with human-generated misinformation but also with algorithmically optimized deception.[71][72][73]

## Research Gaps and Future Directions

Despite growing scholarship, critical gaps persist:
Overuse Versus Underuse: Nearly all peer-reviewed interventions target misinformation that deters appropriate healthcare utilization, with scant attention to misinformation driving overuse, overdiagnosis, and wasteful medical consumption. This asymmetry is problematic given that overuse diverts resources from addressing underuse and exposes patients to unnecessary harm. The medical test study highlights this gap—social media promotes lucrative screening with minimal consideration of opportunity costs or adverse effects.[74][75][10][9]
Platform-Specific Dynamics: While COVID-19 research examined Twitter and Facebook extensively, platforms like TikTok and Instagram—dominant among younger demographics—remain understudied. Short-video formats present unique challenges; users process health misinformation differently across text-heavy versus video-dominant platforms. Endometriosis misinformation on TikTok, for instance, appeared in 23% of popular videos, with physicians creating only 17% of content.[70][76][77][4]
Long-Term Effectiveness: Most intervention studies assess immediate or short-term outcomes, with limited evidence regarding persistence of effects. Inoculation theory predicts decay over time, yet few studies track participants beyond initial exposure. This gap undermines confidence in real-world implementation where sustained resilience is necessary.[43][50][49][40]
AI-Generated Medical Images: Frameworks for governing synthetic medical imagery remain nascent despite rapid capability advances. Ethical questions—consent for training data, disclosure requirements, liability for diagnostic errors from AI-manipulated images—require urgent multidisciplinary attention. The radiologist-indistinguishable synthetic images reported by several studies suggest that technical detection alone will prove insufficient; robust governance, authentication protocols, and professional standards are imperative.[21][23][35][19][20][24]
Cross-Cultural Validation: Most studies originate from North America and Europe, limiting generalizability. Health misinformation manifests differently across cultural contexts, reflecting varying institutional trust, health beliefs, and digital literacy landscapes. Interventions proven effective in Western contexts may require substantial adaptation for implementation in low- and middle-income countries where Purpose Africa operates.[78][79][2][41][40]
Behavioral Outcomes: While studies document belief changes and sharing intentions, fewer examine actual health behaviors or clinical outcomes. The link between misinformation exposure and vaccine hesitancy is well-established, but evidence connecting specific visual misinformation to other health behaviors (treatment adherence, screening uptake, lifestyle modifications) remains limited. Modeling studies suggest substantial impacts—one SMIR (Susceptible-Misinformed-Infected-Recovered) simulation estimated that misinformation could amplify epidemic peaks sixfold and accelerate infections by two weeks, resulting in 14% additional infections—but empirical validation is needed.[80][81][82][83][10]

## Implications for Public Health Practice

The evidence synthesized in this review carries several implications for public health practitioners and policymakers:
Multi-Stakeholder Coordination: Effective mitigation requires orchestrated action across platforms, governments, healthcare institutions, educators, and civil society. The WHO competency framework for managing infodemics provides a useful organizing structure, emphasizing monitoring, intervention to minimize consequences, and primary prevention through improved information environments.[84][85][2][64]
Investment in Media Literacy: Given consistent evidence of media literacy's effectiveness, public health agencies should prioritize integration of these interventions into school curricula, community health programs, and professional training. Visual and multimedia formats enhance learning, suggesting that video-based modules may optimize impact.[42][86][41][43][40]
Healthcare Professional Empowerment: Institutions must revise policies to support physician engagement on social media, provide training in misinformation detection and correction, and recognize this work as legitimate professional contribution. The high trust physicians command represents an underutilized asset in combating misinformation.[66][69][52][67][68]
Platform Accountability: Self-regulation has proven insufficient; stronger government oversight and international coordination are needed. Options include mandatory fact-checking infrastructure, algorithmic transparency requirements, prohibition of health-related advertising without disclosure, and financial penalties for hosting misinformation.[87][74][64]
Prebunking Integration: Inoculation-based approaches should be incorporated into public health campaigns, ideally deployed before misinformation spreads rather than reactively after belief formation. Emergency departments, primary care offices, and vaccination clinics represent promising venues for prebunking interventions targeting patients before they encounter misinformation online.[48][49][51][52]

## Conclusion

Medical misinformation disseminated through images with false or misleading context constitutes a multifaceted public health challenge requiring sustained, coordinated response. The evidence demonstrates that OOC imagery—exploiting authentic visuals' credibility while divorcing them from accurate context—represents the dominant threat, far exceeding sophisticated synthetic manipulations in prevalence and impact. With 87% of social media posts about medical tests promoting benefits while only 15% mentioning harms, and financial conflicts pervading this landscape, the current information ecosystem systematically misleads audiences toward potentially harmful health decisions.
Effective mitigation demands technological, educational, and policy interventions deployed in concert. Reverse image search tools and AI-powered forensic analysis enable detection, while media literacy programs and inoculation-based prebunking build individual resilience. Platform-level fact-checking labels and algorithmic reforms can reshape information environments, though implementation faces commercial resistance. Healthcare professionals' unique credibility positions them as crucial actors, yet institutional barriers must be dismantled to unleash this potential.
Critical research gaps persist, particularly regarding misinformation driving overuse, platform-specific dynamics on visual-centric channels, long-term intervention effectiveness, and governance of AI-generated medical imagery. As Purpose Africa advances capacity for quality clinical research and evidence-based medicine across the continent, addressing visual medical misinformation must feature prominently—both as a threat to evidence uptake and as an opportunity to model effective countermeasures in resource-constrained, mobile-first contexts where visual communication dominates.
The stakes are substantial: misinformation has been estimated to cause 300,000+ unnecessary COVID-19 deaths in the United States alone, with 35% of Canadians reporting they avoided effective treatments due to false information. Yet the tools exist to combat this threat. Strategic deployment of detection technologies, educational interventions, platform reforms, and healthcare professional engagement can substantially reduce misinformation's impact, protecting public health while preserving the democratic and accessibility benefits of social media. The imperative now is implementation at scale, informed by rigorous evidence and responsive to evolving technological and social dynamics.[88][66]

## References

Empowering Third-Year Medical Students to Detect Bias and Medical Misinformation Online via Experiential Learning of "Lateral Reading"[44]
Mitigating GenAI-powered Evidence Pollution for Out-of-Context Multimodal Misinformation Detection[7]
Sniffer: Multimodal Large Language Model for Explainable Out-of-Context Misinformation Detection[8]
E2LVLM: Evidence-Enhanced Large Vision-Language Model for Multimodal Out-of-Context Misinformation Detection[30]
Beyond (Mis)Representation: Visuals in COVID-19 Misinformation[1]
Prevalence of Health Misinformation on Social Media—Challenges and Mitigation Before, During, and Beyond the COVID-19 Pandemic[3][2]
Addressing misleading medical information on social media[74]
Influencers promoting 'overwhelmingly' misleading information about medical tests on social media[9]
Image fraud in nuclear medicine research[18]
Social Media Posts About Medical Tests With Potential for Overdiagnosis[10]
Study evaluates the accuracy of medical images generated by artificial intelligence[19]
New research shows the problem of health misinformation in Canada is growing[88]
COVE: COntext and VEracity prediction for out-of-context images[11]
LLaVA-SNIPPER: Scene-Graph-based Inference with Multimodal LLMs for Explainable Out-of-Context Misinformation[31]
CMIE: Combining MLLM Insights with External Evidence for Explainable Out-of-Context Misinformation Detection[32]
Beyond (Mis)Representation: Visuals in COVID-19 Misinformation (International Journal of Press/Politics)[15][16][17]
Missing the Bigger Picture: The Need for More Research on Visual Health Misinformation[5][4]
Forgery detection in medical images with distinguished recognition of original and tampered regions[33]
Out-of-context photos are a powerful low-tech form of misinformation[12]
The Optimal Model for Copy-Move Forgery Detection in Medical Images[34]
Understanding how users identify health misinformation in short videos[76]
A Comprehensive Analysis of COVID-19 Misinformation, Public Health Impacts, and Communication Strategies[6]
Communication of COVID-19 Misinformation on Social Media by US Physicians[89]
How to use a reverse image search to spot fake news[26]
A Comprehensive Analysis of COVID-19 Misinformation (JMIR)[80]
Synthetic Manipulation of Medical Images: Eroding Trust in Medicine[20]
Let's flatten the infodemic curve (WHO)[27]
A comprehensive review of synthetic manipulations in medical imaging[21]
The 'Sift' strategy: A four-step method for spotting misinformation[28]
Possible Health Benefits and Risks of Synthetic Manipulation Videos[90]
Online disinformation ([Canada.ca](https://Canada.ca))[29]
How synthetic manipulations are threatening healthcare authenticity[22]
Media Literacy Interventions Improve Resilience to Misinformation: A Meta-Analytic Investigation[40]
Building resilience to misinformation in communities of color[41]
Health Misinformation on Social Media: A Review of Management and Innovation Perspectives[84]
The effectiveness of visual-based interventions on health literacy in health care[45]
Educational Video Intervention to Improve Health Misinformation Identification on WhatsApp[42]
The effectiveness of visual-based interventions on health literacy in health care: a systematic review and meta-analysis[46]
Educational Video Intervention to Improve Health Misinformation Identification on WhatsApp (JMIR)[43]
Potential Effectiveness of Pictorial Warning Labels That Feature Testimonial Photographs[56]
A Health Media Literacy Intervention Increases Skepticism of Cancer News[47]
Fact-checker warning labels are effective even for those who distrust fact-checkers[53]
Social media and the spread of misinformation (Health Promotion International)[64]
Warning Labels as a Public Health Intervention[57]
Warning labels could help regulate social media[54]
Synthetic Manipulations and Cheap Fakes (Data & Society)[13]
Using a digital media literacy intervention to motivate reverse image search[14]
Toward Medical Synthetic Manipulation Detection: A Comprehensive Dataset and Novel Method[24]
Synthesis of realistic medical images with pathologies using diffusion models[23]
Crypto-Watermarking of Transmitted Medical Images[36]
MedForensics dataset[35]
A watermarking framework for encrypted medical images[37]
Fighting health misinformation: Survey shows medical professionals among most trusted news sources[65]
A Blockchain-Based Scheme for Secure Sharing of X-Ray Images[38]
Medical Image Authentication using Watermarking and Blockchain[39]
Strategies and prerequisites for combating health misinformation on social media: a systematic review[85]
Examining the Effects of Social Media Warning Labels on Perceived Credibility and Intent to Engage with Health Misinformation[55]
Endometriosis on TikTok: Evaluating social media misinformation and the role of healthcare professionals[77]
Health Misinformation on Social Media in Bangladesh: Public Health Impact and Mitigation Strategies[79]
US Physicians' and Nurses' Motivations, Barriers, and Recommendations for Correcting Health Misinformation on Social Media[69][67][68]
Towards psychological herd immunity: Cross-cultural evidence for two prebunking interventions against COVID-19 misinformation[50][49][48]
How can doctors counter health misinformation on social media[66]
The role of emergency physicians in the fight against health misinformation[52]
Prebunking Against Misinformation in the Modern Digital Age[51]
AI synthetic manipulations of real doctors spreading health misinformation on social media[25]
An analysis of the factors influencing engagement metrics within the dissemination of health science misinformation[60]
Health Misinformation and social media: Analysing the effects of fake news content on public behaviour in Pakistan[61]
#OCD: A Content Analysis of Obsessive-Compulsive Disorder Stereotype Amplification and Misinformation on TikTok[70]
Evaluating Twitter's algorithmic amplification of low-credibility content[62]
NewsCLIPpings: Automatic Generation of Out-of-Context Multimodal Media[72][73][71]
Infodemics and misinformation negatively affect people's health behaviours[81]
Modeling the amplification of epidemic spread by misinformation[82]
Sequential mediation role of COVID‐19 threat and psychological distress[83]
Human-algorithm interactions help explain the spread of misinformation[63]
How Amplification May Be Giving Misinformation New Reach[59]
