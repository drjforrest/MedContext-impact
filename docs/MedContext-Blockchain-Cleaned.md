# MedContext: Context Integrity, Blockchain Provenance & Real-Time Monitoring
## Complete Backend Architecture for Image Authenticity Verification & Learning System

**Prepared for:** Purpose Africa, HERO Organization, MedContext Project  
**Date:** January 14, 2026  
**Purpose:** Implement context integrity verification, immutable provenance tracking, and real-time learning architecture

---

## EXECUTIVE SUMMARY

This document specifies the **backend infrastructure** that powers MedContext's user-facing verification system:

**User-Facing Frontend:**
- Medical professional/journalist/public uploads image
- System analyzes and returns verdict within 3-4 minutes
- Simple visual interface: "Authentic" / "Manipulated" / "Uncertain"

**Hidden Backend Learning System:**
- Every image upload becomes training data
- Context alignment continuously improves
- Provenance genealogy accumulates as learning corpus
- Misinformation narratives tracked across all platforms
- Pattern recognition identifies emerging threats

**Key Components:**
1. **Context Integrity Module** - MedForensics dataset + DSKI neural network
2. **Blockchain Provenance System** - Immutable image genealogy tracking
3. **Real-Time Social Media Monitoring** - WhatsApp, Facebook, Twitter, Telegram integration
4. **Learning Algorithm** - Federated learning approach for continuous model improvement
5. **Pattern Recognition Engine** - Identifies new misinformation narratives proactively

---

## PART 1: DEEPFAKE DETECTION MODULE

### 1.1 The Problem: AI-Generated Medical Images

**Threat Level:** CRITICAL and INCREASING

By late 2025, generative AI tools (DALL-E 3, Midjourney, Stable Diffusion) can create photorealistic medical images:
- Fake chest X-rays showing "vaccine injury"
- Synthetic ultrasounds showing "fetal abnormality"
- Synthetic pathology slides
- Fabricated endoscopy images

**Detection Challenge:**
- Real images can be heavily compressed/modified (but still authentic)
- Some miscontextualized images are high quality; some real images are poor quality
- No single pixel-level artifact guarantees authenticity

**Solution:** Multi-modal detection (pixel analysis + semantic analysis + metadata forensics)

---

### 1.2 Detection Architecture

**Three-Layer Approach:**

```
Layer 1: Pixel-Level Forensics
  ├─ Compression artifact analysis (JPEG quantization patterns)
  ├─ Frequency domain analysis (FFT for generative patterns)
  ├─ Noise consistency checking
  └─ Local Binary Patterns (LBP)

Layer 2: Semantic/Content Analysis
  ├─ Medical plausibility scoring
  ├─ Anatomical consistency checking
  ├─ Radiological feature verification
  └─ Domain-specific anomaly detection

Layer 3: Metadata & Provenance
  ├─ EXIF data analysis
  ├─ File creation timestamps
  ├─ Camera signature analysis
  ├─ Blockchain provenance checking
  └─ Reverse image search history

ENSEMBLE DECISION:
  ├─ If all 3 layers agree: HIGH CONFIDENCE (95%+)
  ├─ If 2 of 3 agree: MEDIUM CONFIDENCE (70-85%)
  ├─ If 1 or 0 agree: LOW CONFIDENCE (flag for expert review)
```

---

### 1.3 Layer 1: Pixel-Level Forensics Implementation

**Tool:** DSKI (Deep Synthetic Knowledge Integration) neural network trained on MedForensics dataset

**Architecture:**

```python
import torch
import torch.nn as nn
from torchvision import models

class ContextIntegrityNetwork(nn.Module):
    """
    Multi-task context integrity verification combining:
    - Compression artifact detection
    - Frequency domain analysis
    - Medical domain anomaly detection
    """
    
    def __init__(self, pretrained=True):
        super(ContextIntegrityNetwork, self).__init__()
        
        # Backbone: EfficientNet-B7 (pretrained on ImageNet)
        self.backbone = models.efficientnet_b7(pretrained=pretrained)
        
        # Frequency domain branch (DCT analysis)
        self.dct_processor = DCTAnalyzer()
        
        # Compression artifact branch
        self.compression_analyzer = CompressionArtifactDetector()
        
        # Head 1: Authenticity classification (real/fake)
        self.authenticity_head = nn.Sequential(
            nn.Linear(2560, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Linear(512, 2)  # Binary: real vs fake
        )
        
        # Head 2: Confidence scoring
        self.confidence_head = nn.Sequential(
            nn.Linear(2560, 512),
            nn.ReLU(),
            nn.Linear(512, 1),
            nn.Sigmoid()  # 0-1 confidence
        )
        
        # Head 3: Manipulation type (if fake, what kind?)
        self.manipulation_type_head = nn.Sequential(
            nn.Linear(2560, 512),
            nn.ReLU(),
            nn.Linear(512, 4)  # Types: splicing, inpainting, GAN, unknown
        )
    
    def forward(self, image):
        """
        Args:
            image: Tensor of shape (batch_size, 3, 512, 512)
            
        Returns:
            dict: {
                'authenticity': [real_prob, fake_prob],
                'confidence': float (0-1),
                'manipulation_type': [prob_splicing, prob_inpainting, prob_gan, prob_unknown],
                'pixel_artifacts': dict of artifact scores
            }
        """
        
        # Extract features from backbone
        backbone_features = self.backbone.features(image)
        backbone_features = torch.nn.functional.adaptive_avg_pool2d(
            backbone_features, (1, 1)
        )
        backbone_features = backbone_features.view(backbone_features.size(0), -1)
        
        # DCT frequency analysis
        dct_features = self.dct_processor(image)
        
        # Compression artifact analysis
        compression_features = self.compression_analyzer(image)
        
        # Concatenate all features
        combined_features = torch.cat([
            backbone_features,
            dct_features,
            compression_features
        ], dim=1)
        
        # Multi-head outputs
        authenticity_logits = self.authenticity_head(combined_features)
        confidence_score = self.confidence_head(combined_features)
        manipulation_logits = self.manipulation_type_head(combined_features)
        
        return {
            'authenticity': torch.softmax(authenticity_logits, dim=1),
            'confidence': confidence_score.squeeze(),
            'manipulation_type': torch.softmax(manipulation_logits, dim=1),
            'raw_features': combined_features
        }


class DCTAnalyzer(nn.Module):
    """Discrete Cosine Transform frequency domain analysis"""
    
    def forward(self, image):
        """
        Analyze frequency domain for generative artifacts
        
        Real images: Natural frequency distribution
        AI-generated: Characteristic frequency patterns
        """
        from scipy.fftpack import dct
        
        # Convert to grayscale
        gray = image.mean(dim=1)  # (batch, height, width)
        
        dct_features = []
        for img in gray:
            # DCT 2D
            img_np = img.cpu().detach().numpy()
            dct_2d = dct(dct_2d(img_np, axis=0), axis=1)
            
            # Extract statistics from frequency bands
            features = {
                'low_freq_energy': np.mean(np.abs(dct_2d[:32, :32])),
                'mid_freq_energy': np.mean(np.abs(dct_2d[32:96, 32:96])),
                'high_freq_energy': np.mean(np.abs(dct_2d[96:, 96:])),
                'freq_std': np.std(dct_2d),
                'freq_entropy': -np.sum(dct_2d * np.log(np.abs(dct_2d) + 1e-10))
            }
            dct_features.append(list(features.values()))
        
        return torch.tensor(dct_features, device=image.device)


class CompressionArtifactDetector(nn.Module):
    """Analyze JPEG/PNG compression artifacts"""
    
    def forward(self, image):
        """
        Detect compression-based artifacts
        
        Real medical images: Consistent compression patterns from original equipment
        Synthetic manipulations: Recompression artifacts, inconsistent patterns
        """
        # Analyze blocking patterns (8x8 JPEG blocks)
        # Analyze DCT quantization inconsistencies
        # Analyze color subsampling
        
        artifact_features = []
        for img in image:
            # Block artifact detection
            img_np = img.cpu().detach().numpy()
            
            # 8x8 block analysis
            blocks = []
            for i in range(0, img_np.shape[1], 8):
                for j in range(0, img_np.shape[2], 8):
                    block = img_np[:, i:i+8, j:j+8]
                    blocks.append(np.std(block))
            
            features = {
                'block_variance_mean': np.mean(blocks),
                'block_variance_std': np.std(blocks),
                'block_boundary_transitions': self._count_block_boundaries(img_np),
                'color_channel_correlation': np.corrcoef(
                    img_np[0].flatten(), img_np[1].flatten()
                )[0, 1]
            }
            artifact_features.append(list(features.values()))
        
        return torch.tensor(artifact_features, device=image.device)
    
    def _count_block_boundaries(self, img_np):
        """Count suspicious discontinuities at 8x8 block boundaries"""
        count = 0
        for i in range(8, img_np.shape[1], 8):
            for j in range(8, img_np.shape[2], 8):
                # Check for edge discontinuity
                left = np.mean(img_np[:, i-1, j-1:j+1])
                right = np.mean(img_np[:, i, j-1:j+1])
                if abs(left - right) > 0.1:
                    count += 1
        return count


# Usage in MedContext Pipeline

def check_image_authenticity(image_path):
    """
    Complete context integrity pipeline
    
    Args:
        image_path: Path to medical image file
        
    Returns:
        dict: Authenticity assessment with confidence
    """
    
    # Load model (once, cached)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = ContextIntegrityNetwork(pretrained=True).to(device)
    model.eval()
    
    # Load image
    from PIL import Image
    img = Image.open(image_path).convert('RGB')
    
    # Preprocess: resize to 512x512, normalize
    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    # Forward pass
    with torch.no_grad():
        output = model(img_tensor)
    
    # Parse results
    auth_probs = output['authenticity'][0]  # [real_prob, fake_prob]
    confidence = output['confidence'][0].item()
    manipulation_probs = output['manipulation_type'][0]
    
    result = {
        "authenticity_verdict": "REAL" if auth_probs[0] > 0.5 else "FAKE",
        "authenticity_confidence": float(auth_probs[0]),
        "fake_probability": float(auth_probs[1]),
        "overall_confidence": confidence,
        "manipulation_type": {
            "splicing": float(manipulation_probs[0]),
            "inpainting": float(manipulation_probs[1]),
            "gan_generated": float(manipulation_probs[2]),
            "unknown": float(manipulation_probs[3])
        },
        "layer_1_verdict": "REAL" if auth_probs[0] > 0.7 else "FAKE" if auth_probs[1] > 0.7 else "UNCERTAIN",
        "layer_1_confidence": confidence
    }
    
    return result
```

---

### 1.4 Layer 2: Semantic/Medical Plausibility Analysis

```python
class MedicalPlausibilityChecker:
    """
    Verify that image content is medically plausible
    
    Use MedGemma to analyze image, then verify findings make sense
    """
    
    def __init__(self):
        self.medgemma = MedGemmaAnalyzer()  # From Part 2
        self.medical_knowledge = MedicalKnowledgeBase()
    
    def check_plausibility(self, image_path, medgemma_analysis):
        """
        Args:
            image_path: Path to image
            medgemma_analysis: Output from MedGemma (findings, pathologies, etc.)
            
        Returns:
            dict: Plausibility scoring
        """
        
        findings = medgemma_analysis['findings']
        pathologies = medgemma_analysis['pathologies_detected']
        modality = medgemma_analysis['image_modality']
        
        plausibility_scores = {}
        
        # Check 1: Are pathologies consistent with anatomical findings?
        for pathology in pathologies:
            consistency = self._check_pathology_consistency(
                pathology, findings, modality
            )
            plausibility_scores[f'pathology_{pathology}_consistency'] = consistency
        
        # Check 2: Do findings match expected distributions for this modality?
        modality_fit = self._check_modality_appropriateness(
            findings, modality
        )
        plausibility_scores['modality_fit'] = modality_fit
        
        # Check 3: Are anatomical proportions correct?
        anatomy_check = self._check_anatomical_proportions(image_path, modality)
        plausibility_scores['anatomical_proportions'] = anatomy_check
        
        # Check 4: Are artifacts consistent with imaging physics?
        physics_check = self._check_imaging_physics(image_path, modality)
        plausibility_scores['physics_consistency'] = physics_check
        
        # Overall plausibility score
        overall = np.mean(list(plausibility_scores.values()))
        
        return {
            "layer_2_verdict": "PLAUSIBLE" if overall > 0.7 else "IMPLAUSIBLE" if overall < 0.4 else "UNCERTAIN",
            "layer_2_confidence": overall,
            "plausibility_scores": plausibility_scores,
            "flagged_inconsistencies": [
                k for k, v in plausibility_scores.items()
                if v < 0.5
            ]
        }
    
    def _check_pathology_consistency(self, pathology, findings, modality):
        """Does the stated pathology match the visual findings?"""
        
        knowledge = self.medical_knowledge.get_pathology_info(pathology, modality)
        
        # Expected findings for this pathology
        expected_findings = knowledge['expected_findings']
        
        # Check overlap
        finding_words = ' '.join(findings).lower()
        matches = sum(1 for ef in expected_findings if ef.lower() in finding_words)
        
        consistency_score = matches / len(expected_findings) if expected_findings else 0.5
        
        return consistency_score
    
    def _check_modality_appropriateness(self, findings, modality):
        """Do findings make sense for this imaging modality?"""
        
        typical_findings = self.medical_knowledge.get_modality_findings(modality)
        
        finding_score = 0
        for finding in findings:
            if any(tf.lower() in finding.lower() for tf in typical_findings):
                finding_score += 1
        
        return finding_score / len(findings) if findings else 0.5
    
    def _check_anatomical_proportions(self, image_path, modality):
        """Verify anatomical structures have correct proportions"""
        
        from PIL import Image
        img = Image.open(image_path)
        width, height = img.size
        
        # For chest X-rays, typical ratios
        if 'chest' in modality.lower():
            # Heart should occupy ~40-50% of chest width
            # Lungs should be ~90% of total height
            
            # Use image segmentation to verify
            # (Simplified for this example)
            return 0.8  # Placeholder
        
        return 0.7
    
    def _check_imaging_physics(self, image_path, modality):
        """
        Verify image obeys physics of imaging modality
        
        E.g., for X-rays: proper attenuation gradients
            for ultrasound: realistic speckle patterns
            for CT: consistent HU values
        """
        
        return 0.75  # Placeholder
```

---

### 1.5 Layer 3: Metadata & Blockchain Provenance

**See Part 2: Blockchain Provenance System**

---

### 1.6 Ensemble Decision Making

```python
class ContextIntegrityEnsemble:
    """Combine 3 signals into final verdict"""
    
    def __init__(self):
        self.layer1 = ContextIntegrityNetwork()
        self.layer2 = MedicalPlausibilityChecker()
        self.layer3 = BlockchainProvenanceChecker()
    
    def detect_context_mismatch(self, image_path, medgemma_analysis=None):
        """
        Complete context integrity evaluation using all 3 layers
        
        Returns:
            dict: Final authenticity verdict with high confidence
        """
        
        # Layer 1: Pixel-level forensics
        layer1_result = self.layer1.check_image_authenticity(image_path)
        
        # Layer 2: Medical plausibility
        layer2_result = self.layer2.check_plausibility(
            image_path, 
            medgemma_analysis
        )
        
        # Layer 3: Provenance/metadata
        layer3_result = self.layer3.check_provenance(image_path)
        
        # Ensemble decision
        verdicts = [
            layer1_result['layer_1_verdict'],
            layer2_result['layer_2_verdict'],
            layer3_result['layer_3_verdict']
        ]
        
        confidences = [
            layer1_result['layer_1_confidence'],
            layer2_result['layer_2_confidence'],
            layer3_result['layer_3_confidence']
        ]
        
        # Majority voting
        real_votes = verdicts.count('REAL') + verdicts.count('PLAUSIBLE') + verdicts.count('ORIGINAL')
        fake_votes = verdicts.count('FAKE') + verdicts.count('IMPLAUSIBLE') + verdicts.count('MANIPULATED')
        uncertain_votes = verdicts.count('UNCERTAIN')
        
        if real_votes >= 2:
            final_verdict = "AUTHENTIC"
            final_confidence = np.mean([c for v, c in zip(verdicts, confidences) if 'REAL' in v or 'PLAUSIBLE' in v or 'ORIGINAL' in v])
        elif fake_votes >= 2:
            final_verdict = "MANIPULATED"
            final_confidence = np.mean([c for v, c in zip(verdicts, confidences) if 'FAKE' in v or 'IMPLAUSIBLE' in v or 'MANIPULATED' in v])
        else:
            final_verdict = "UNCERTAIN"
            final_confidence = np.mean(confidences)
        
        return {
            "final_verdict": final_verdict,
            "confidence": final_confidence,
            "layer_1": layer1_result,
            "layer_2": layer2_result,
            "layer_3": layer3_result,
            "recommendation": self._get_recommendation(final_verdict, final_confidence)
        }
    
    def _get_recommendation(self, verdict, confidence):
        """Clinical recommendation based on verdict"""
        
        if verdict == "AUTHENTIC" and confidence > 0.9:
            return "Image verified as authentic. Safe to use clinically."
        elif verdict == "AUTHENTIC" and confidence > 0.7:
            return "Image likely authentic, but recommend expert review for critical decisions."
        elif verdict == "MANIPULATED":
            return "Image shows signs of manipulation. Do not use for clinical decisions."
        elif verdict == "UNCERTAIN":
            return "Unable to verify authenticity. Recommend clinical expert review or seek original source."
        else:
            return "Insufficient data for recommendation."
```

---

## PART 2: BLOCKCHAIN PROVENANCE SYSTEM

### 2.1 Provenance Architecture

**Problem:** How do we create immutable record of where image came from and how it's been used?

**Traditional approach:** Centralized database
- Single point of failure
- Trust required in central authority
- Can be modified or deleted

**Blockchain approach:** Distributed immutable ledger
- No single point of failure
- Cryptographic verification
- Permanent, transparent history

**MedContext Implementation:** Hybrid approach

```
┌─────────────────────────────────────────────────────┐
│  MEDCONTEXT BLOCKCHAIN PROVENANCE SYSTEM            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Image Registration                              │
│     ├─ Calculate image hash (SHA-256)               │
│     ├─ Compress & store on IPFS                     │
│     ├─ Write metadata to blockchain                 │
│     └─ Generate provenance certificate              │
│                                                     │
│  2. Usage Tracking                                  │
│     ├─ Each new claim/context recorded              │
│     ├─ Hash of claim + image stored                 │
│     ├─ Timestamp and geographic location            │
│     └─ Trust score calculation                      │
│                                                     │
│  3. Genealogy Visualization                         │
│     ├─ Original source → current uses               │
│     ├─ Interactive timeline                         │
│     ├─ Geographic heat map                          │
│     └─ Narrative evolution tracking                 │
│                                                     │
│  4. Verification Query                              │
│     ├─ User uploads image                           │
│     ├─ System calculates hash                       │
│     ├─ Queries blockchain for provenance            │
│     ├─ Returns complete genealogy                   │
│     └─ Displays verdicts from all previous analyses │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### 2.2 Implementation: Ethereum Smart Contracts

**Technology Stack:**
- **Blockchain:** Ethereum (or Polygon for cheaper gas)
- **Storage:** IPFS (InterPlanetary File System)
- **Language:** Solidity
- **Node:** Infura API or self-hosted node

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedContextProvenance {
    
    // Events for indexing
    event ImageRegistered(
        bytes32 indexed imageHash,
        address indexed registrant,
        uint256 timestamp,
        string ipfsHash
    );
    
    event UsageRecorded(
        bytes32 indexed imageHash,
        bytes32 claimHash,
        string context,
        uint256 timestamp,
        address recorder
    );
    
    event AuthenticityVerdictRecorded(
        bytes32 indexed imageHash,
        string verdict,
        uint256 confidence,
        address verifier
    );
    
    // Data structures
    struct ImageRecord {
        bytes32 imageHash;              // SHA-256 of image
        address originalRegistrant;     // Who first registered it
        uint256 registrationTimestamp;
        string ipfsHash;               // Where full image stored
        string imageModality;          // X-ray, CT, MRI, etc.
        bytes32[] usageHistory;        // Links to all usages
        string currentVerdict;         // Latest authenticity verdict
        uint256 currentConfidence;     // Confidence in verdict
        uint256 totalInstancesTracked; // How many times seen online
    }
    
    struct UsageRecord {
        bytes32 imageHash;
        bytes32 claimHash;             // Hash of associated claim
        string claimContext;           // The claim made with image
        address recorder;
        uint256 timestamp;
        string platform;               // Where found: facebook, whatsapp, twitter, etc.
        string claimCategory;          // vaccine_injury, treatment_efficacy, etc.
        uint8 trustScore;              // 0-100, calculated by system
        bool isMisinformation;
    }
    
    struct AuthenticityVerdict {
        bytes32 imageHash;
        string verdict;                // AUTHENTIC, MANIPULATED, UNCERTAIN
        uint256 confidence;            // 0-100%
        address verifier;              // Who verified
        uint256 timestamp;
        string analysisDetails;        // JSON of layer results
    }
    
    // Storage
    mapping(bytes32 => ImageRecord) public images;
    mapping(bytes32 => UsageRecord[]) public usageRecords;
    mapping(bytes32 => AuthenticityVerdict[]) public verdictHistory;
    
    bytes32[] public allImageHashes;
    
    // Access control
    mapping(address => bool) public authorizedVerifiers;
    address public owner;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }
    
    modifier onlyAuthorized() {
        require(authorizedVerifiers[msg.sender], "Not authorized");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        authorizedVerifiers[msg.sender] = true;
    }
    
    // Register new image
    function registerImage(
        bytes32 imageHash,
        string memory ipfsHash,
        string memory modality
    ) public {
        require(images[imageHash].imageHash == 0, "Image already registered");
        
        ImageRecord storage record = images[imageHash];
        record.imageHash = imageHash;
        record.originalRegistrant = msg.sender;
        record.registrationTimestamp = block.timestamp;
        record.ipfsHash = ipfsHash;
        record.imageModality = modality;
        
        allImageHashes.push(imageHash);
        
        emit ImageRegistered(imageHash, msg.sender, block.timestamp, ipfsHash);
    }
    
    // Record a usage of image (claim made with it)
    function recordUsage(
        bytes32 imageHash,
        string memory claimText,
        string memory platform,
        string memory claimCategory,
        bool isIdentifiedAsMisinformation
    ) public {
        require(images[imageHash].imageHash != 0, "Image not registered");
        
        bytes32 claimHash = keccak256(abi.encodePacked(claimText, block.timestamp));
        
        UsageRecord memory usage = UsageRecord({
            imageHash: imageHash,
            claimHash: claimHash,
            claimContext: claimText,
            recorder: msg.sender,
            timestamp: block.timestamp,
            platform: platform,
            claimCategory: claimCategory,
            trustScore: calculateTrustScore(claimCategory, isIdentifiedAsMisinformation),
            isMisinformation: isIdentifiedAsMisinformation
        });
        
        usageRecords[imageHash].push(usage);
        images[imageHash].usageHistory.push(claimHash);
        images[imageHash].totalInstancesTracked++;
        
        emit UsageRecorded(
            imageHash,
            claimHash,
            claimText,
            block.timestamp,
            msg.sender
        );
    }
    
    // Record authenticity verdict
    function recordVerdict(
        bytes32 imageHash,
        string memory verdict,
        uint256 confidence,
        string memory analysisDetails
    ) public onlyAuthorized {
        require(images[imageHash].imageHash != 0, "Image not registered");
        
        AuthenticityVerdict memory v = AuthenticityVerdict({
            imageHash: imageHash,
            verdict: verdict,
            confidence: confidence,
            verifier: msg.sender,
            timestamp: block.timestamp,
            analysisDetails: analysisDetails
        });
        
        verdictHistory[imageHash].push(v);
        
        // Update current verdict
        images[imageHash].currentVerdict = verdict;
        images[imageHash].currentConfidence = confidence;
        
        emit AuthenticityVerdictRecorded(
            imageHash,
            verdict,
            confidence,
            msg.sender
        );
    }
    
    // Query complete genealogy
    function getImageGenealogy(bytes32 imageHash) public view returns (
        ImageRecord memory imageData,
        UsageRecord[] memory usages,
        AuthenticityVerdict[] memory verdicts
    ) {
        require(images[imageHash].imageHash != 0, "Image not found");
        
        return (
            images[imageHash],
            usageRecords[imageHash],
            verdictHistory[imageHash]
        );
    }
    
    // Calculate trust score based on claim type
    function calculateTrustScore(
        string memory claimCategory,
        bool isMisinformation
    ) internal pure returns (uint8) {
        if (isMisinformation) {
            // Misinformation gets low score
            if (keccak256(abi.encodePacked(claimCategory)) == 
                keccak256(abi.encodePacked("vaccine_injury"))) {
                return 10;  // Very harmful
            } else if (keccak256(abi.encodePacked(claimCategory)) == 
                      keccak256(abi.encodePacked("treatment_efficacy"))) {
                return 15;
            }
            return 20;
        } else {
            // Legitimate medical uses
            return 85;
        }
    }
    
    // Authorize verifier (admin function)
    function addVerifier(address verifierAddress) public onlyOwner {
        authorizedVerifiers[verifierAddress] = true;
    }
    
    // Statistics query
    function getImageStats(bytes32 imageHash) public view returns (
        uint256 totalUsages,
        uint256 misinformationUsages,
        uint256 legitimateUsages,
        string memory currentVerdict
    ) {
        UsageRecord[] memory usages = usageRecords[imageHash];
        uint256 misinformation = 0;
        
        for (uint i = 0; i < usages.length; i++) {
            if (usages[i].isMisinformation) {
                misinformation++;
            }
        }
        
        return (
            usages.length,
            misinformation,
            usages.length - misinformation,
            images[imageHash].currentVerdict
        );
    }
}
```

---

### 2.3 IPFS Storage Integration

**Why IPFS?** Distributed, immutable, content-addressed storage

```python
import ipfshttpclient
import hashlib
import json

class IPFSProvenanceStorage:
    """Store images and metadata on IPFS"""
    
    def __init__(self, ipfs_host='localhost', ipfs_port=5001):
        self.client = ipfshttpclient.connect(
            f'/ip4/{ipfs_host}/tcp/{ipfs_port}'
        )
    
    def store_image(self, image_path):
        """
        Store image on IPFS
        
        Returns:
            dict: {
                'ipfs_hash': QmXxxx (content hash),
                'file_hash': SHA-256 of image,
                'storage_fee': cost in wei,
                'pinned': boolean
            }
        """
        
        # Calculate image hash (will be used in blockchain)
        with open(image_path, 'rb') as f:
            image_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Add to IPFS
        result = self.client.add(image_path)
        ipfs_hash = result['Hash']
        
        # Pin to ensure persistence (optional, costs storage)
        self.client.pin.add(ipfs_hash)
        
        return {
            'ipfs_hash': ipfs_hash,
            'image_hash': image_hash,
            'pinned': True
        }
    
    def store_metadata(self, image_hash, metadata):
        """
        Store image metadata on IPFS
        
        Metadata includes: MedGemma analysis, claims, verdicts
        """
        
        # Convert metadata to JSON
        metadata_json = json.dumps({
            'image_hash': image_hash,
            'timestamp': metadata.get('timestamp'),
            'medgemma_analysis': metadata.get('medgemma_analysis'),
            'claims_extracted': metadata.get('claims_extracted'),
            'consensus': metadata.get('consensus'),
            'context_verdict': metadata.get('context_verdict'),
            'blockchain_tx': metadata.get('blockchain_tx')
        }, default=str)
        
        # Store temporarily and add to IPFS
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(metadata_json)
            temp_path = f.name
        
        result = self.client.add(temp_path)
        metadata_ipfs_hash = result['Hash']
        
        # Clean up
        import os
        os.remove(temp_path)
        
        return {
            'metadata_ipfs_hash': metadata_ipfs_hash,
            'metadata_stored': True
        }
    
    def retrieve_metadata(self, ipfs_hash):
        """Retrieve stored metadata from IPFS"""
        
        content = self.client.cat(ipfs_hash)
        metadata = json.loads(content)
        
        return metadata
```

---

### 2.4 Blockchain Integration with MedContext Pipeline

```python
from web3 import Web3

class BlockchainProvenanceRecorder:
    """Record image provenance on blockchain"""
    
    def __init__(self, contract_address, private_key, infura_url):
        self.w3 = Web3(Web3.HTTPProvider(infura_url))
        self.contract_address = contract_address
        self.account = self.w3.eth.account.from_key(private_key)
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=self.contract_abi
        )
    
    def register_image(self, image_hash, ipfs_hash, modality):
        """Register image on blockchain"""
        
        # Build transaction
        tx = self.contract.functions.registerImage(
            Web3.to_bytes(hexstr=image_hash),
            ipfs_hash,
            modality
        ).build_transaction({
            'from': self.account.address,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber'],
            'status': receipt['status']  # 1 = success
        }
    
    def record_usage(self, image_hash, claim_text, platform, claim_category, 
                     is_misinformation):
        """Record claim/usage on blockchain"""
        
        tx = self.contract.functions.recordUsage(
            Web3.to_bytes(hexstr=image_hash),
            claim_text,
            platform,
            claim_category,
            is_misinformation
        ).build_transaction({
            'from': self.account.address,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber']
        }
    
    def record_verdict(self, image_hash, verdict, confidence, analysis_details):
        """Record authenticity verdict on blockchain"""
        
        tx = self.contract.functions.recordVerdict(
            Web3.to_bytes(hexstr=image_hash),
            verdict,
            int(confidence * 100),  # Convert to 0-100
            json.dumps(analysis_details)
        ).build_transaction({
            'from': self.account.address,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return {
            'tx_hash': tx_hash.hex(),
            'verdict_recorded': True
        }
    
    def query_genealogy(self, image_hash):
        """Query complete image genealogy from blockchain"""
        
        image_data, usages, verdicts = self.contract.functions.getImageGenealogy(
            Web3.to_bytes(hexstr=image_hash)
        ).call()
        
        return {
            'image_data': image_data,
            'usage_records': usages,
            'verdict_history': verdicts
        }
```

---

## PART 3: REAL-TIME SOCIAL MEDIA MONITORING

### 3.1 Platform Integration Architecture

**Problem:** Medical image misinformation spreads across multiple platforms simultaneously

**Solution:** Distributed monitoring of 4 key platforms

```
┌──────────────────────────────────────────────────────────┐
│          REAL-TIME SOCIAL MEDIA MONITORING              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Platform 1: WhatsApp Health Groups                      │
│  ├─ User contributions (health groups they're in)        │
│  ├─ Consent-based monitoring                             │
│  ├─ De-identification before analysis                    │
│  └─ Frequency: Real-time                                 │
│                                                          │
│  Platform 2: Facebook Pages & Groups                     │
│  ├─ Public health pages (open API)                       │
│  ├─ Anti-vax groups (open monitoring)                    │
│  ├─ Alternative medicine pages                           │
│  └─ Frequency: Hourly                                    │
│                                                          │
│  Platform 3: Twitter/X                                   │
│  ├─ Public keyword search                                │
│  ├─ Keywords: "vaccine injury", "lung damage", etc.      │
│  ├─ Image trending analysis                              │
│  └─ Frequency: Real-time                                 │
│                                                          │
│  Platform 4: Telegram Channels                           │
│  ├─ Public health channels                               │
│  ├─ Anti-vax conspiracy channels                         │
│  ├─ Alternative medicine groups                          │
│  └─ Frequency: Hourly                                    │
│                                                          │
│  Central Pipeline:                                       │
│  ├─ Detect medical images in posts                       │
│  ├─ Extract surrounding text                             │
│  ├─ Hash image for duplicate detection                   │
│  ├─ Check blockchain for known images                    │
│  ├─ Run claim extraction & semantic clustering           │
│  ├─ Assess misinformation severity                       │
│  ├─ Alert if high-risk narrative detected                │
│  └─ Store in learning corpus                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

### 3.2 WhatsApp Integration (Consent-Based)

**Approach:** Users opt-in to monitor their WhatsApp health groups

```python
from whatsapp_business_cloud_api import WhatsAppBusinessCloudAPI
import hashlib

class WhatsAppMonitor:
    """
    Monitor medical images in WhatsApp health groups
    
    IMPORTANT: Only through explicit user consent
    """
    
    def __init__(self, api_key, phone_number_id):
        self.client = WhatsAppBusinessCloudAPI(api_key)
        self.phone_number_id = phone_number_id
    
    def process_incoming_message(self, webhook_data):
        """
        Process WhatsApp message webhook
        
        Triggered when user shares image in monitored group
        """
        
        # Extract message data
        message_data = webhook_data.get('entry')[0]['changes'][0]['value']['messages'][0]
        
        # Check if message contains image
        if message_data['type'] != 'image':
            return None
        
        media_id = message_data['image']['id']
        caption = message_data.get('caption', '')
        
        # Download image (with consent)
        image_data = self.client.download_media(media_id)
        image_hash = hashlib.sha256(image_data).hexdigest()
        
        # De-identify before analysis
        message_metadata = {
            'group_id': message_data['from'],  # Don't expose actual group
            'timestamp': message_data['timestamp'],
            'caption': caption,
            'user_id': None  # De-identified
        }
        
        # Send to analysis pipeline
        return {
            'image_hash': image_hash,
            'image_data': image_data,
            'metadata': message_metadata,
            'source_platform': 'whatsapp'
        }
    
    def query_group_history(self, group_id, date_range):
        """
        Query historical messages from group (if enabled)
        
        User can choose date range for analysis
        """
        
        messages = self.client.get_group_messages(
            group_id,
            date_from=date_range['start'],
            date_to=date_range['end']
        )
        
        image_messages = [
            m for m in messages
            if m['type'] == 'image' and self._appears_medical(m)
        ]
        
        return image_messages
    
    def _appears_medical(self, message):
        """Heuristic: Does message appear to contain medical content?"""
        
        caption = message.get('caption', '').lower()
        medical_keywords = ['vaccine', 'lung', 'injury', 'covid', 'diagnosis', 
                           'treatment', 'doctor', 'hospital', 'disease']
        
        return any(kw in caption for kw in medical_keywords)
```

---

### 3.3 Facebook Integration (Public API)

```python
import facebook
import requests

class FacebookMonitor:
    """Monitor medical image misinformation on Facebook"""
    
    def __init__(self, access_token):
        self.graph = facebook.GraphAPI(access_token)
        self.access_token = access_token
    
    def monitor_health_pages(self, page_ids):
        """
        Monitor known health-related Facebook pages
        
        Args:
            page_ids: List of public page IDs to monitor
        """
        
        for page_id in page_ids:
            try:
                # Get recent posts from page
                posts = self.graph.get_connections(
                    page_id,
                    'posts',
                    fields='id,message,created_time,picture,link',
                    limit=100
                )
                
                for post in posts['data']:
                    # Check if post contains image
                    if 'picture' in post:
                        yield self._process_post(post, page_id)
            
            except Exception as e:
                print(f"Error monitoring page {page_id}: {e}")
    
    def _process_post(self, post, page_id):
        """Extract image and context from Facebook post"""
        
        image_url = post.get('picture')
        caption = post.get('message', '')
        timestamp = post.get('created_time')
        
        # Download image
        try:
            image_response = requests.get(image_url)
            image_data = image_response.content
            image_hash = hashlib.sha256(image_data).hexdigest()
        except:
            return None
        
        return {
            'image_hash': image_hash,
            'image_data': image_data,
            'metadata': {
                'platform': 'facebook',
                'page_id': page_id,
                'post_id': post['id'],
                'caption': caption,
                'timestamp': timestamp,
                'engagement': self._get_engagement(post['id'])
            },
            'source_platform': 'facebook'
        }
    
    def _get_engagement(self, post_id):
        """Get likes, shares, comments count"""
        
        try:
            metrics = self.graph.get_connections(
                post_id,
                'insights',
                fields='type,values',
                metric='engagement'
            )
            return metrics
        except:
            return {}
    
    def search_health_claims(self, keywords, time_range):
        """Search for posts containing specific health misinformation keywords"""
        
        query = f"vaccination injury OR vaccine side effect OR {' OR '.join(keywords)}"
        
        results = self.graph.request('search', {'q': query, 'type': 'post'})
        
        posts = []
        for result in results.get('data', []):
            if 'picture' in result:
                posts.append(self._process_post(result, result.get('from', {}).get('id')))
        
        return posts
```

---

### 3.4 Twitter/X Integration

```python
import tweepy
import re

class TwitterMonitor:
    """Monitor medical image misinformation on Twitter"""
    
    def __init__(self, bearer_token):
        self.client = tweepy.Client(bearer_token=bearer_token)
    
    def search_health_misinformation(self, keywords, time_range):
        """Search Twitter for medical image-based claims"""
        
        # Build search query
        query = f"({' OR '.join(keywords)}) has:images -is:retweet lang:en"
        
        tweets = self.client.search_recent_tweets(
            query=query,
            start_time=time_range['start'],
            end_time=time_range['end'],
            max_results=100,
            tweet_fields=['public_metrics', 'created_at', 'author_id'],
            expansions=['author_id'],
            media_fields=['alt_text', 'type', 'url']
        )
        
        processed_tweets = []
        for tweet in tweets.data:
            if tweet.attachments and 'media_keys' in tweet.attachments:
                image_data = self._extract_image(tweet)
                if image_data:
                    processed_tweets.append({
                        'tweet_id': tweet.id,
                        'text': tweet.text,
                        'metrics': tweet.public_metrics,
                        'image_data': image_data
                    })
        
        return processed_tweets
    
    def _extract_image(self, tweet):
        """Download image from tweet"""
        
        # Use tweepy media field
        # (Implementation depends on specific media structure)
        pass
    
    def track_trending_claims(self):
        """Identify trending medical misinformation narratives"""
        
        # Keywords tracked
        vaccine_keywords = [
            'vaccine injury', 'side effect', 'myocarditis',
            'blood clot', 'adverse', 'damaged'
        ]
        
        # Get trend data
        trends = {}
        for keyword in vaccine_keywords:
            query = f"{keyword} has:images -is:retweet"
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=10
            )
            
            trends[keyword] = {
                'tweet_count': len(tweets.data),
                'engagement': sum(t.public_metrics['like_count'] for t in tweets.data),
                'sample_tweets': [t.text for t in tweets.data[:3]]
            }
        
        return trends
```

---

### 3.5 Central Pipeline: Processing Incoming Images

```python
class RealTimeAnalysisPipeline:
    """
    Process images from social media in real-time
    
    Every uploaded image becomes training data for improving the system
    """
    
    def __init__(self):
        self.blockchain_recorder = BlockchainProvenanceRecorder(...)
        self.ipfs_storage = IPFSProvenanceStorage()
        self.context_detector = ContextIntegrityEnsemble()
        self.medgemma = MedGemmaAnalyzer()
        self.claim_extractor = MedicalClaimExtractor()
        self.semantic_clusterer = ClaimFamilyIdentifier()
        self.consensus_calculator = ConsensusCalculator()
        self.learning_system = FederatedLearningSystem()
    
    async def process_image_from_social_media(self, image_data, metadata):
        """
        Complete pipeline for processing image from social media
        
        This is where LEARNING happens
        """
        
        # Step 1: Calculate image hash
        image_hash = hashlib.sha256(image_data).hexdigest()
        
        # Step 2: Check if we've seen this image before
        blockchain_history = self.blockchain_recorder.query_genealogy(image_hash)
        
        is_known_image = len(blockchain_history['usage_records']) > 0
        
        if is_known_image:
            # Already have this image; add new usage
            existing_verdict = blockchain_history['image_data'][10]  # currentVerdict
            print(f"Known image. Previous verdict: {existing_verdict}")
        else:
            # New image; full analysis
            print(f"New image detected: {image_hash[:8]}...")
            
            # Step 3: Deep fake detection
            # Context detector expects a filesystem path
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_image:
                temp_image.write(image_data)
                temp_image.flush()
                context_result = self.context_detector.detect_context_mismatch(temp_image.name)
            
            # Step 4: Medical image analysis (MedGemma)
            medgemma_result = self.medgemma.analyze_image(image_data)
            
            # Step 5: Register on blockchain
            ipfs_result = self.ipfs_storage.store_image_buffer(image_data)
            
            blockchain_tx = self.blockchain_recorder.register_image(
                image_hash=image_hash,
                ipfs_hash=ipfs_result['ipfs_hash'],
                modality=medgemma_result['image_modality']
            )
            
            # Step 6: Store image in IPFS
            metadata_with_analysis = {
                **metadata,
                'medgemma_analysis': medgemma_result,
                'context_verdict': context_result['final_verdict'],
                'blockchain_tx': blockchain_tx
            }
            
            metadata_ipfs = self.ipfs_storage.store_metadata(
                image_hash,
                metadata_with_analysis
            )
            
            # Step 7: Record authenticity verdict on blockchain
            self.blockchain_recorder.record_verdict(
                image_hash=image_hash,
                verdict=context_result['final_verdict'],
                confidence=context_result['confidence'],
                analysis_details=context_result
            )
        
        # Step 8: Extract claims from caption/context
        caption_text = metadata.get('caption', '')
        claims = self.claim_extractor.extract_claims(caption_text, image_id=image_hash[:8])
        
        # Step 9: Record usage on blockchain
        for claim in claims['claims']:
            is_misinformation = self._assess_misinformation(claim, medgemma_result)
            
            self.blockchain_recorder.record_usage(
                image_hash=image_hash,
                claim_text=claim['claim_text'],
                platform=metadata['source_platform'],
                claim_category=claim.get('claim_types', [{}])[0].get('type', 'unknown'),
                is_misinformation=is_misinformation
            )
        
        # Step 10: LEARNING: Add to training corpus
        self.learning_system.add_training_example({
            'image_hash': image_hash,
            'image_data': image_data,
            'medgemma_analysis': medgemma_result,
            'context_result': context_result,
            'claims': claims,
            'platform': metadata['source_platform'],
            'timestamp': metadata['timestamp']
        })
        
        # Step 11: Evaluate consensus & alert if high-risk
        consensus = self.consensus_calculator.calculate_consensus(
            image_hash,
            [claims],  # Claims from this instance
            medgemma_result,
            []  # Fact-checks
        )
        
        # Step 12: Alert if dangerous
        if self._is_high_risk(claims, medgemma_result):
            self._send_alert(
                image_hash=image_hash,
                risk_level='HIGH',
                claims=claims,
                recommendation='Flag to fact-checkers immediately'
            )
        
        return {
            'image_hash': image_hash,
            'is_known_image': is_known_image,
            'context_verdict': context_result['final_verdict'],
            'claims_extracted': len(claims['claims']),
            'misinformation_detected': any(
                c.get('flags') for c in claims['claims']
            ),
            'blockchain_recorded': True,
            'learning_corpus_updated': True
        }
    
    def _assess_misinformation(self, claim, medgemma_result):
        """Determine if claim is misinformation"""
        
        # Check if claim matches what image actually shows
        claim_text = claim['claim_text'].lower()
        
        for pathology in medgemma_result['pathologies_detected']:
            if pathology.lower() in claim_text:
                # Claim mentions what image shows; likely legitimate
                return False
        
        # Claim doesn't match image; likely misinformation
        return True
    
    def _is_high_risk(self, claims, medgemma_result):
        """Flag high-risk misinformation narratives"""
        
        high_risk_patterns = [
            ('vaccine injury', 'pneumonia'),  # Vaccine injury claims on COVID images
            ('poison', 'treatment'),           # Poison accusations
            ('conspiracy', 'medical')          # Conspiracy narratives
        ]
        
        for claim in claims['claims']:
            claim_text = claim['claim_text'].lower()
            for pattern in high_risk_patterns:
                if all(p in claim_text for p in pattern):
                    return True
        
        return False
    
    def _send_alert(self, image_hash, risk_level, claims, recommendation):
        """Alert fact-checkers and health authorities"""
        
        alert_message = f"""
        ⚠️ HIGH-RISK MEDICAL MISINFORMATION DETECTED
        
        Image Hash: {image_hash}
        Risk Level: {risk_level}
        Claims: {len(claims)}
        
        Top Claim: {claims['claims'][0]['claim_text'] if claims['claims'] else 'N/A'}
        
        Recommendation: {recommendation}
        
        Blockchain TX: [View on Etherscan]
        Full Analysis: [MedContext Dashboard]
        """
        
        # Send to alert system (Slack, email, SMS)
        # Implementation depends on notification system
        print(alert_message)
```

---

## PART 4: FEDERATED LEARNING SYSTEM

### 4.1 Continuous Improvement Through Learning

**Problem:** Every image analyzed provides signal for improving detection

**Traditional approach:** Centralized dataset → retrain model periodically
- Slow adaptation
- Privacy concerns (all data in one place)
- Requires centralized infrastructure

**MedContext approach:** Federated learning
- Models trained locally on user devices
- Only updates shared (not raw data)
- Privacy-preserving
- Real-time model improvement

```python
class FederatedLearningSystem:
    """
    Continuously improve context alignment model
    
    Uses data from every image analyzed in production
    """
    
    def __init__(self):
        self.global_model = ContextIntegrityNetwork()
        self.training_corpus = []
        self.model_version = "1.0"
        self.last_update = datetime.now()
    
    def add_training_example(self, example):
        """
        Add verified example to training corpus
        
        Args:
            example: {
                'image_hash': str,
                'image_data': bytes,
                'context_result': dict,  # System's verdict
                'verified_verdict': bool  # Ground truth (optional)
            }
        """
        
        self.training_corpus.append(example)
        
        # Trigger retraining if corpus large enough
        if len(self.training_corpus) >= 1000:  # Retrain every 1000 images
            self.retrain_model()
    
    def retrain_model(self):
        """Retrain context alignment model on new data"""
        
        print(f"Retraining model on {len(self.training_corpus)} images...")
        
        # Convert corpus to training batches
        train_loader = self._create_training_batches(self.training_corpus)
        
        # Fine-tune existing model
        updated_model = self._fine_tune_model(
            self.global_model,
            train_loader
        )
        
        # Evaluate on validation set
        val_accuracy = self._evaluate_model(updated_model, self._get_validation_set())
        
        # Only update if performance improved
        if val_accuracy > self._get_best_accuracy():
            self.global_model = updated_model
            self.model_version = f"{float(self.model_version) + 0.1:.1f}"
            self.last_update = datetime.now()
            
            print(f"✓ Model updated to v{self.model_version}")
            print(f"  Validation accuracy: {val_accuracy:.3f}")
            
            # Distribute new model to all nodes
            self._distribute_model_update(updated_model)
        else:
            print("✗ New model performance not better; keeping current version")
    
    def _create_training_batches(self, corpus):
        """Create training batches from corpus"""
        
        from torch.utils.data import DataLoader, Dataset
        
        class MedContextDataset(Dataset):
            def __init__(self, examples):
                self.examples = examples
            
            def __len__(self):
                return len(self.examples)
            
            def __getitem__(self, idx):
                example = self.examples[idx]
                image_data = example['image_data']
                
                # Label: 1 if context mismatch detected, 0 if aligned
                label = 1 if example['context_result']['final_verdict'] == 'MANIPULATED' else 0
                
                # Transform
                transform = transforms.Compose([
                    transforms.Resize((512, 512)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    )
                ])
                
                # Convert bytes to image
                from PIL import Image
                from io import BytesIO
                img = Image.open(BytesIO(image_data)).convert('RGB')
                img_tensor = transform(img)
                
                return img_tensor, label
        
        dataset = MedContextDataset(corpus)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        return loader
    
    def _fine_tune_model(self, model, train_loader):
        """Fine-tune model on new data"""
        
        import torch
        import torch.optim as optim
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        # Use lower learning rate for fine-tuning
        optimizer = optim.Adam(model.parameters(), lr=1e-4)
        criterion = torch.nn.CrossEntropyLoss()
        
        # Train for a few epochs
        for epoch in range(3):
            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                
                # Forward pass
                outputs = model(images)
                loss = criterion(outputs['authenticity'], labels)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        
        return model
    
    def _evaluate_model(self, model, val_loader):
        """Evaluate model on validation set"""
        
        import torch
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        model.eval()
        
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                
                outputs = model(images)
                auth_probs = outputs['authenticity']
                
                _, predicted = torch.max(auth_probs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        accuracy = correct / total
        return accuracy
    
    def _get_validation_set(self):
        """Get held-out validation set"""
        
        # Use standard context mismatch benchmark
        # (e.g., MedForensics test set)
        pass
    
    def _get_best_accuracy(self):
        """Get best validation accuracy so far"""
        
        # Read from checkpoint
        # (Implementation depends on checkpoint system)
        return 0.88  # Placeholder
    
    def _distribute_model_update(self, updated_model):
        """Distribute updated model to all nodes"""
        
        # Save model to cloud storage
        model_path = f"models/medgemma_v{self.model_version}.pt"
        torch.save(updated_model.state_dict(), model_path)
        
        # Upload to S3 or similar
        # Notify all clients to download update
        
        print(f"Model distributed to all nodes")
```

---

## PART 5: INTEGRATION: USER FRONTEND FLOW

### 5.1 Simple User Experience

**What users see:**

```
┌─────────────────────────────────────┐
│     MedContext Image Verifier       │
├─────────────────────────────────────┤
│                                     │
│  📸 Upload Medical Image            │
│  [Click to upload or drag & drop]   │
│                                     │
│  Optional: Add context/caption      │
│  [Text area for claims made with    │
│   image]                            │
│                                     │
│  🔍 Analyze Image                   │
│  [Button - takes 3-4 minutes]       │
│                                     │
│  ───────────────────────────────────│
│                                     │
│  RESULTS:                           │
│                                     │
│  ✓ AUTHENTIC (94% confidence)      │
│    └─ Image appears to be          │
│      genuine medical imaging       │
│                                     │
│  📊 Image History:                 │
│  ├─ First seen: Jan 2020           │
│  ├─ Total instances tracked: 487    │
│  ├─ Primary use: COVID-19 cases     │
│  ├─ Misinformation use: 29.8%       │
│  └─ Blockchain: View genealogy →    │
│                                     │
│  💬 Claims Found (3):               │
│  ├─ "COVID-19 pneumonia"            │
│  ├─ "Vaccine injury"                │
│  └─ "Unproven cancer cure"          │
│                                     │
│  📌 Fact-Check Sources (2):         │
│  ├─ AFP: FALSE (2021)               │
│  └─ PolitiFact: FALSE (2021)        │
│                                     │
│  👨‍⚕️ For Healthcare Providers:       │
│  [View clinical guidance]           │
│                                     │
│  📰 For Journalists:                │
│  [View investigation toolkit]       │
│                                     │
│  👥 For Public:                     │
│  [View simple explanation]          │
│                                     │
└─────────────────────────────────────┘
```

---

## CONCLUSION

**User-Facing System (Simple):**
- Upload image
- Receive verdict: Authentic / Manipulated / Uncertain
- View image history and fact-checks

**Hidden Backend System (Complex & Learning):**
- Context integrity verification via 3-layer ensemble
- Blockchain provenance tracking every use
- Real-time monitoring of all social media
- Federated learning continuously improving detection
- Every image analyzed becomes training data

**Key Innovation:** Users don't see the complexity. They just upload an image and get an answer. But behind that simple interface, the system is:
- Accumulating genealogy
- Tracking misinformation spread
- Learning from mistakes
- Getting smarter every day

---

**Document Version:** 1.0  
**Last Updated:** January 14, 2026  
**Contact:** Dr. Jamie Forrest, MedContext Project Lead


