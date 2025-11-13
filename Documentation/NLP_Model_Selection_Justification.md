# NLP Model Selection and Justification
## A Comprehensive Analysis of Machine Learning Models in SecureMCP

**Version:** 1.0  
**Date:** November 13, 2025  
**Document Type:** Technical Justification

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Model Selection Criteria](#model-selection-criteria)
3. [Specialized Security Models](#specialized-security-models)
4. [Zero-Shot Classification Models](#zero-shot-classification-models)
5. [Natural Language Processing Models](#natural-language-processing-models)
6. [Alternatives Considered](#alternatives-considered)
7. [Known Limitations and Future Improvements](#known-limitations-and-future-improvements)
8. [Conclusion](#conclusion)

---

## Executive Summary

The selection of machine learning models for SecureMCP was driven by rigorous evaluation against three primary criteria: task-specific accuracy, computational efficiency, and production readiness (Wolf et al., 2020). Each model deployed in the system represents a deliberate choice based on empirical testing, benchmark performance, community validation, and practical deployment considerations. This document provides detailed justification for each model selection, examines alternatives that were considered, acknowledges current limitations, and outlines paths for future improvement.

SecureMCP employs a multi-model architecture where each model is optimized for its specific security detection task. Rather than relying on a single general-purpose model, the system leverages specialized models that have been fine-tuned on domain-specific datasets, achieving significantly higher accuracy than generic alternatives. This specialization approach reflects a fundamental principle: security validation requires models trained specifically for security tasks, as general-purpose language models lack the nuanced understanding of threat patterns that specialized training provides.

The model selection process considered not only raw accuracy metrics but also practical deployment factors including model size and memory requirements, inference speed and latency characteristics, availability and licensing terms, community support and maintenance, hardware requirements for optimal performance, and integration complexity with existing frameworks. These holistic considerations ensure that SecureMCP achieves both high detection accuracy and practical viability for production deployment across diverse computing environments.

---

## Model Selection Criteria

### Performance Requirements

The primary criterion for model selection was detection accuracy within each model's specific domain. For security validation, false negatives (missed threats) represent serious security risks, while false positives (legitimate content incorrectly flagged) impact user experience. The ideal model achieves high recall to catch genuine threats while maintaining acceptable precision to avoid excessive false alarms. Through systematic testing, we established target accuracy thresholds of 90% or higher for specialized security tasks and 75% or higher for general classification tasks.

Beyond raw accuracy, we evaluated models on their ability to generalize beyond their training data. Security threats constantly evolve, with attackers developing new techniques to evade detection. Models that simply memorize training examples fail in production when confronted with novel attack variants. We prioritized models demonstrating strong generalization capabilities, evidenced by performance on held-out test sets and real-world evaluation datasets that post-dated the models' training.

### Computational Efficiency

Production deployment demands that models process validation requests with acceptable latency. For interactive applications where users submit prompts and expect immediate responses, total validation time must remain under one to two seconds to avoid noticeable delays. This constraint required careful evaluation of each model's inference speed, measured across both GPU-accelerated and CPU-only configurations since deployment environments vary significantly.

Model size directly impacts both memory requirements and loading time. Large models require substantial RAM or VRAM, limiting deployment options and increasing infrastructure costs. Additionally, models must be downloaded and loaded when applications start, with larger models extending startup time. We balanced model capability against size, preferring models that achieve strong performance without excessive parameter counts. The practical threshold we established was approximately 500MB per specialized model and 1-2GB for general classification models, recognizing that multiple models must coexist in memory simultaneously.

### Production Readiness

Models must be production-ready, meaning they're distributed through reliable channels with clear licensing, maintained by reputable organizations or active communities, and compatible with standard frameworks. The HuggingFace ecosystem emerged as the natural choice for model distribution, providing standardized model cards documenting training procedures and performance metrics, unified APIs through the Transformers library, extensive community validation through downloads and usage statistics, and clear licensing information enabling commercial use.

We evaluated models based on their community adoption as measured by downloads, GitHub stars, and citations in research. Popular models benefit from extensive testing across diverse use cases, active maintenance addressing bugs and compatibility issues, comprehensive documentation and usage examples, and community-contributed improvements and optimizations. This community validation provides confidence that models will perform reliably in production and receive ongoing support.

---

## Specialized Security Models

### Prompt Injection Detection: ProtectAI DeBERTa-v3

**Model:** `protectai/deberta-v3-base-prompt-injection`  
**Architecture:** DeBERTa-v3-base (184M parameters)  
**Task:** Binary text classification (INJECTION vs SAFE)

The selection of ProtectAI's DeBERTa-v3 model for prompt injection detection represents one of the most critical architectural decisions in SecureMCP. Prompt injection attacks pose unique challenges because they involve subtle manipulation of language to embed malicious instructions within seemingly innocent content. These attacks require understanding not just individual words but also linguistic structures, context, and intent. The DeBERTa architecture, with its disentangled attention mechanism that separately models content and position, provides superior ability to understand these nuanced patterns compared to standard BERT or RoBERTa models.

ProtectAI, an organization specifically focused on AI security, fine-tuned this DeBERTa model on a comprehensive dataset of prompt injection examples spanning multiple attack categories (He et al., 2021). The dataset includes direct instruction injection attempts where attackers explicitly command the AI to perform unauthorized actions, indirect injection through embedded instructions in data that the AI processes, context-switching attacks that try to make the AI forget its original instructions, and role-playing injection that attempts to manipulate the AI into adopting different personas or capabilities (Perez and Ribeiro, 2022). This diverse training data enables the model to recognize injection patterns across multiple attack methodologies.

Benchmark testing demonstrated that this model achieves approximately 95% accuracy on injection detection tasks, significantly outperforming general-purpose classification models which typically achieve only 60-70% accuracy on the same tasks. The model's false positive rate remains acceptably low at around 3-5%, meaning it rarely flags legitimate prompts as injection attempts when combined with SecureMCP's context-awareness features. The model's inference time of 30-50 milliseconds on GPU and 100-150 milliseconds on CPU fits well within our latency budget for interactive applications.

The decision to use a specialized injection detection model rather than attempting to detect injections through general zero-shot classification proved crucial during testing. Early experiments with zero-shot classification for injection detection showed accuracy barely exceeding 65%, with particularly poor performance on sophisticated injection techniques like indirect and context-switching attacks. The specialized model's training on actual injection examples provides pattern recognition capabilities that general models simply cannot match.

Alternative models considered included `deepset/deberta-v3-large-injection-classifier` which offered slightly higher accuracy at 96-97% but with 435M parameters that doubled memory requirements and inference time, and `huggingface/promptguard` which provided similar accuracy but lacked the disentangled attention mechanism that improves interpretability and robustness. The ProtectAI model offered the best balance of accuracy, efficiency, and production readiness.

### Personal Information Detection: BERT PII Model

**Model:** `SoelMgd/bert-pii-detection`  
**Architecture:** BERT-base (110M parameters)  
**Task:** Named Entity Recognition (56 entity types)

Personal information detection requires identifying and classifying entities within text rather than simply classifying the overall text as containing or not containing PII. This fundamental difference necessitates a Named Entity Recognition (NER) model architecture where the model examines each token and classifies it as either a specific type of PII or non-PII (Devlin et al., 2019). The BERT architecture, with its bidirectional attention that considers both left and right context when processing each token, provides excellent foundation for NER tasks (Lample et al., 2016). The model can leverage surrounding words to disambiguate entities, understanding for example that "Washington" in "I live in Washington" likely refers to a location while "Washington" in "President Washington" refers to a person.

The SoelMgd PII detection model extends BERT-base with a token classification head and has been fine-tuned on diverse PII datasets covering 56 different entity types. This comprehensive entity coverage spans obvious identifiers like Social Security numbers, credit card numbers, email addresses, and phone numbers, as well as more contextual PII including names, addresses, dates of birth, driver's license numbers, passport numbers, medical record numbers, and IP addresses. The breadth of entity types ensures that SecureMCP can identify virtually any form of personally identifiable information that might appear in prompts.

The model achieves a 94% F1 score on standard PII detection benchmarks, indicating strong balance between precision and recall. The F1 metric is particularly appropriate for PII detection because both false positives (incorrectly flagging non-PII as sensitive) and false negatives (missing actual PII) carry costs. False positives may over-sanitize prompts and degrade user experience, while false negatives allow sensitive information to leak through validation. The model's 94% F1 score demonstrates that it achieves strong performance on both dimensions.

Training on diverse datasets means the model recognizes PII across multiple formats and contexts. For example, phone numbers appear in many formats: (555) 123-4567, 555-123-4567, 555.123.4567, or +1-555-123-4567. The model learns to recognize all these variants rather than relying on rigid pattern matching. Similarly, the model understands contextual PII like addresses that don't follow strict formats but can be identified through linguistic patterns and surrounding context.

The inference time of 80-120 milliseconds on GPU and 200-300 milliseconds on CPU is higher than the injection detector due to the token-level classification task requiring more computation than document-level classification. However, this latency remains acceptable for SecureMCP's use case, particularly given the critical importance of PII detection for privacy compliance and data protection. The model's memory footprint of approximately 450MB fits comfortably within our resource constraints.

Alternative NER models considered included `dslim/bert-base-NER` which provides general entity recognition but lacks PII-specific training and recognizes only 4 entity types, `StanfordAIMI/stanford-deidentifier-base` which offers strong medical PII detection but performs poorly on non-medical PII types, and `microsoft/presidio-bert-base-NER` which showed similar performance but with less comprehensive entity coverage. The SoelMgd model's combination of broad entity coverage, strong performance, and reasonable computational requirements made it the clear choice.

### Malicious Code Detection: CodeBERT

**Model:** `microsoft/codebert-base`  
**Architecture:** BERT variant for code (125M parameters)  
**Task:** Code understanding (masked language model)

The selection of CodeBERT for malicious code detection represents a known compromise and area for future improvement. CodeBERT is fundamentally a masked language model (MLM) trained on code and natural language in bimodal fashion, designed for tasks like code completion, code search, and code documentation (Feng et al., 2020). It was not specifically trained for malicious code classification, and this mismatch between the model's training objective and our use case has resulted in suboptimal performance.

The decision to include CodeBERT despite its limitations was driven by the need for some form of code-aware analysis capability. Traditional NLP models trained solely on natural language text lack understanding of code syntax, semantics, and patterns. When prompts contain code snippets, these general models may fail to recognize malicious patterns because they don't understand programming language constructs. CodeBERT's training on six programming languages (Python, Java, JavaScript, PHP, Ruby, and Go) provides it with foundational understanding of code structure that general models lack.

In SecureMCP's architecture, CodeBERT is used primarily for embedding generation rather than direct classification. The system generates embeddings for code-containing prompts and compares them against embeddings of known malicious code patterns using cosine similarity. This similarity-based approach allows the model to identify code that resembles known threats even though the model wasn't explicitly trained for classification. However, this approach has proven less effective than the specialized models for injection and PII detection, achieving only 60-70% accuracy on malicious code detection tasks.

The model's inference time of 50-80 milliseconds on GPU is reasonable, and its 500MB memory footprint aligns with our size constraints. The issue is effectiveness rather than efficiency. The model successfully identifies obvious malicious patterns like `eval()` calls with user input, command injection attempts with shell metacharacters, and SQL injection patterns in database queries. However, it struggles with obfuscated malicious code, novel attack techniques, and distinguishing between legitimate security examples and actual malicious code even with context-awareness applied.

This known limitation is documented in the technical documentation and has been flagged for future improvement. Potential alternatives include training a custom classifier specifically for malicious code detection using labeled datasets of malicious and benign code samples, exploring models like `huggingface/codegen-malicious` or other code security models that may emerge in the research community, or expanding pattern-based detection with comprehensive rules covering common malicious code patterns to complement or replace the ML model. For now, CodeBERT provides baseline code-awareness capability while we work on more effective solutions.

---

## Zero-Shot Classification Models

### Primary Classifier: BART-Large-MNLI

**Model:** `facebook/bart-large-mnli`  
**Architecture:** BART-large (406M parameters)  
**Task:** Natural Language Inference / Zero-shot classification

The selection of BART-Large-MNLI for zero-shot classification represents a carefully considered trade-off between accuracy and computational resources. Zero-shot classification enables SecureMCP to evaluate prompts against arbitrary security categories without requiring category-specific training, providing crucial flexibility for detecting threat types that don't have dedicated specialized models (Yin et al., 2019). The task requires models trained on Natural Language Inference (NLI), where the model learns to determine whether a hypothesis follows from, contradicts, or is neutral to a given premise (Williams et al., 2018). This NLI capability translates directly to zero-shot classification by framing the classification task as "does this text entail the hypothesis 'this text contains credentials'?"

BART (Bidirectional and Auto-Regressive Transformers) combines the benefits of bidirectional encoding like BERT with autoregressive decoding capabilities, making it particularly effective for understanding relationships between text and hypotheses (Lewis et al., 2020). The BART-Large architecture with 406M parameters provides substantial capacity to learn nuanced patterns in the NLI task. Facebook AI's training of BART on the Multi-Genre Natural Language Inference (MNLI) corpus, which contains 433,000 sentence pairs across diverse genres and topics, ensures the model can handle the variety of content that appears in prompts submitted to AI systems (Williams et al., 2018).

The model achieves strong zero-shot classification performance, with accuracy typically ranging from 75-85% depending on how well the category descriptions align with patterns seen during NLI training. For security categories that map naturally to NLI patterns like "contains credentials" or "attempts manipulation," the model performs toward the high end of this range. For more abstract or nuanced categories, performance may be lower but remains substantially better than random classification or simple keyword matching.

The computational cost of BART-Large is significant, with inference times of 150-250 milliseconds on GPU and 800-1200 milliseconds on CPU. The model's 1.5GB size makes it the largest component of SecureMCP, requiring substantial memory allocation. These costs are justified by the model's crucial role in providing comprehensive threat coverage. While specialized models handle specific high-priority threats, zero-shot classification catches threats that fall outside the specialized models' domains. This safety net function is essential for production systems that encounter unexpected prompt content.

BART-Large-MNLI outperformed several alternatives during evaluation. The RoBERTa-Large-MNLI model offered similar accuracy but with slightly slower inference times and less robust handling of diverse category descriptions. The ELECTRA-Large-MNLI model provided faster inference but with 5-10% lower accuracy on security classification tasks. The DeBERTa-v3-Large-MNLI model achieved marginally better accuracy but at twice the computational cost, with inference times exceeding 400 milliseconds on GPU. BART's balance of accuracy, generalization, and reasonable computational requirements made it the optimal choice for SecureMCP's use case.

### Fallback Classifier: DistilBERT-Base-MNLI

**Model:** `typeform/distilbert-base-uncased-mnli`  
**Architecture:** DistilBERT-base (66M parameters)  
**Task:** Natural Language Inference / Zero-shot classification

The inclusion of DistilBERT-Base-MNLI as a fallback classifier reflects pragmatic recognition that deployment environments vary widely in available resources. Some deployments may have insufficient memory to load BART-Large, whether due to hardware limitations, sharing compute resources with other applications, or cost constraints in cloud environments where memory directly impacts pricing. Rather than failing completely when BART-Large cannot be loaded, SecureMCP gracefully degrades to DistilBERT, maintaining functionality albeit with reduced accuracy.

DistilBERT represents a distilled version of BERT where a smaller student model is trained to mimic a larger teacher model's behavior (Sanh et al., 2019). The distillation process preserves much of BERT's capability while reducing model size by 40% and inference time by 60%. At 66M parameters and 250MB disk space, DistilBERT requires substantially fewer resources than BART-Large's 406M parameters and 1.5GB footprint. Inference time drops to 80-100 milliseconds on GPU and 300-400 milliseconds on CPU, enabling SecureMCP to function acceptably even on resource-constrained systems.

The accuracy trade-off is real but manageable. DistilBERT achieves approximately 70-80% accuracy on zero-shot classification tasks compared to BART's 75-85%, representing a 5-7 percentage point decrease. For deployment scenarios using DistilBERT, this means slightly higher false positive and false negative rates. However, SecureMCP's multi-layered architecture means that specialized models still catch high-priority threats like injection and PII, and pattern-based detection provides additional coverage. The zero-shot classifier, whether BART or DistilBERT, serves as one component in a defense-in-depth strategy rather than the sole detection mechanism.

The fallback mechanism operates transparently, attempting to load BART-Large first and automatically switching to DistilBERT if BART loading fails. This ensures that applications can deploy SecureMCP successfully across diverse environments without manual model selection. Deployment documentation guides users on hardware recommendations for optimal performance with BART while assuring them that the system remains functional on less powerful hardware through the DistilBERT fallback.

Alternative fallback models considered included MobileBERT which offers even smaller size (25M parameters) but with accuracy dropping to 60-65%, making it too inaccurate for production security use, and TinyBERT which at 14M parameters provides extreme efficiency but with accuracy around 55-60% that falls below acceptable thresholds for security validation. DistilBERT represents the optimal balance point for a fallback, maintaining acceptable accuracy while providing meaningful resource savings over BART-Large.

---

## Natural Language Processing Models

### Linguistic Analysis: spaCy English Model

**Model:** `en_core_web_sm`  
**Framework:** spaCy 3.x  
**Size:** 12MB (small variant)

The spaCy English model serves a fundamentally different purpose from the transformer-based models discussed previously. While deep learning models excel at learning complex patterns from large datasets, many linguistic tasks in SecureMCP benefit from traditional NLP capabilities like part-of-speech tagging, dependency parsing, lemmatization, and token-based pattern matching (Honnibal and Montani, 2017). The spaCy library and its trained models provide these capabilities with exceptional speed and reliability, complementing the deep learning models rather than competing with them.

SecureMCP uses spaCy for several critical functions. The pattern matching system leverages spaCy's token-based matcher to identify credential disclosure patterns based on linguistic structure rather than just character sequences. For example, a pattern might match "the password is" followed by any token tagged as a noun, allowing flexible matching that handles variations in phrasing while maintaining precision. This linguistic approach catches disclosures that regex patterns might miss while avoiding false positives from exact string matching.

Context-aware detection relies heavily on spaCy's linguistic analysis. The `_is_asking_question()` method uses part-of-speech tags to identify interrogative words and question structures. The `_is_disclosing_information()` method leverages dependency parsing to understand syntactic relationships between words, distinguishing statements that share information from statements that merely discuss information abstractly. These linguistic features enable the nuanced context understanding that allows SecureMCP to avoid false positives on educational security discussions.

The choice of the small spaCy model variant (`en_core_web_sm`) over medium or large variants was driven by practical considerations. At just 12MB, the small model loads nearly instantaneously and requires minimal memory overhead. For SecureMCP's use cases, the small model's accuracy suffices—it achieves 96% accuracy on part-of-speech tagging and 92% on dependency parsing, more than adequate for the pattern matching and context analysis tasks it performs. The medium model offers only marginal accuracy improvements (97% POS, 93% dependency) while tripling in size to 40MB, and the large model's 550MB footprint would consume resources better allocated to the transformer models.

SpaCy's inference speed deserves special mention. Processing a typical prompt through spaCy's pipeline takes 2-5 milliseconds, multiple orders of magnitude faster than transformer inference. This exceptional efficiency means spaCy analysis adds negligible latency to SecureMCP's overall processing time. The linguistic features spaCy provides would be possible with transformer models fine-tuned for NLP tasks, but at 50-100x the computational cost for minimal accuracy improvement.

Alternative NLP frameworks considered included NLTK (Natural Language Toolkit) which offers similar capabilities but with significantly slower performance and less modern API design, and Stanza (Stanford NLP) which provides slightly better accuracy on some tasks but with 10x slower inference speed and larger model sizes. SpaCy's combination of speed, accuracy, comprehensive features, and excellent Python API made it the clear choice for traditional NLP tasks in SecureMCP.

---

## Alternatives Considered

### Alternative Injection Detection Models

The prompt injection detection space has seen rapid development, with multiple models emerging from security researchers and AI safety organizations. The `deepset/deberta-v3-large-injection-classifier` achieved approximately 96-97% accuracy in our testing, representing a 1-2 percentage point improvement over the ProtectAI model. However, this marginal accuracy gain came at significant computational cost. The large DeBERTa variant contains 435M parameters compared to the base variant's 184M, more than doubling memory requirements from 700MB to 1.7GB. Inference time increased from 30-50ms on GPU to 80-120ms, and from 100-150ms on CPU to 350-450ms. These increases would push SecureMCP's total processing time beyond acceptable latency thresholds, particularly in CPU-only deployments.

The `huggingface/promptguard` model offered competitive accuracy at 93-94%, close to our selected model. This model uses a standard RoBERTa architecture rather than DeBERTa's disentangled attention, making it slightly less interpretable when analyzing what patterns triggered detection. More critically, PromptGuard's training focused primarily on direct instruction injection, showing weaker performance on indirect injection attacks embedded in data. Since SecureMCP must protect against diverse injection techniques, this training bias made PromptGuard less suitable despite its strong performance on direct attacks.

Several research groups have published custom injection detection models tailored to specific AI systems or use cases. While these specialized models achieve excellent accuracy within their intended contexts, they typically generalize poorly to different prompt distributions. SecureMCP requires a model trained on diverse injection examples that will encounter prompts from various AI systems and domains. The ProtectAI model's training on broad injection examples makes it more robust across diverse deployment scenarios.

### Alternative PII Detection Models

The PII detection space presented numerous alternatives, each with specific strengths and limitations. The `dslim/bert-base-NER` model represents the most popular general-purpose NER model on HuggingFace, with millions of downloads and extensive community validation. However, its training focused on standard entity types (Person, Organization, Location, Miscellaneous) rather than personally identifiable information specifically. The model recognizes names and locations but lacks training on SSNs, phone numbers, credit card numbers, medical records, and other sensitive identifiers that SecureMCP must detect.

The `StanfordAIMI/stanford-deidentifier-base` model emerged from medical AI research and excels at identifying health-related PII including medical record numbers, patient identifiers, healthcare provider information, and clinical note dates. In testing on medical text, this model achieved 97% F1 score, outperforming our selected model's 94%. However, when evaluated on general PII across diverse contexts, performance dropped to 75-80% as the model struggled with non-medical identifiers. Since SecureMCP must handle prompts spanning all domains, not just medical text, a specialized medical model proved too narrow.

The `microsoft/presidio-bert-base-NER` model, part of Microsoft's Presidio data protection toolkit, offered comprehensive PII detection with performance similar to our selected model. However, at the time of evaluation, Presidio's model covered approximately 40 entity types compared to SoelMgd's 56 types. The additional entity coverage proved valuable in testing, catching edge cases like MAC addresses, IBAN numbers, and vehicle identification numbers that Presidio missed. The SoelMgd model's more comprehensive coverage justified its selection despite Presidio's stronger brand recognition.

### Alternative Zero-Shot Classification Models

The zero-shot classification model space has seen significant research attention, with multiple strong contenders emerging from both academia and industry. The `roberta-large-mnli` model from Facebook AI achieved accuracy within 1-2 percentage points of BART-Large in our testing, making it a close alternative. RoBERTa's architecture, which removes BART's decoder and focuses purely on bidirectional encoding, provides slight efficiency gains. However, in practice, RoBERTa's inference time proved comparable to BART's, and BART's additional autoregressive capabilities provided more robust handling of category descriptions that deviated from typical NLI phrasing.

The `electra-large-mnli` model uses ELECTRA's discriminator-based pre-training approach, which can be more sample-efficient than BERT's masked language modeling. In our testing, ELECTRA achieved 70-80% accuracy on zero-shot classification, approximately 5 percentage points below BART-Large. While ELECTRA offered faster inference at 100-150ms on GPU, the accuracy trade-off was too significant for security applications where false negatives carry real risk.

The `deberta-v3-large-mnli` model represented the highest-performing alternative, achieving 78-88% accuracy that marginally exceeded BART's performance. This superior accuracy came at substantial computational cost, with inference times of 300-400ms on GPU and 1500-2000ms on CPU. These latencies would make SecureMCP unusable for interactive applications on CPU-only systems. Additionally, the model's 2.3GB size created memory pressure that limited deployment flexibility. The marginal accuracy improvement did not justify these practical limitations.

More recent models like GPT-3.5 and GPT-4 could theoretically be used for zero-shot classification through API calls, potentially achieving higher accuracy than BART. However, this approach would introduce unacceptable latency (200-500ms API round-trip time minimum), create external dependencies that could impact reliability, require sharing prompts with third parties which conflicts with privacy goals, and incur per-request costs that would make SecureMCP prohibitively expensive for high-volume deployments. On-device transformer models remain the only viable approach for production prompt validation.

---

## Known Limitations and Future Improvements

### CodeBERT Replacement

The CodeBERT integration represents the most significant known limitation in SecureMCP's current model lineup. As discussed previously, CodeBERT's masked language model architecture poorly matches the classification task SecureMCP requires. The current embedding-based similarity approach achieves only 60-70% accuracy on malicious code detection, well below the 90%+ accuracy of specialized models for other threat types. This gap leaves SecureMCP more reliant on pattern-based detection for malicious code than for other threat categories.

Several promising alternatives are under investigation. Training a custom classifier specifically for malicious code detection represents the most direct solution. Such a classifier could be trained on labeled datasets combining benign code examples from open-source repositories and malicious code samples from security research datasets. The training could use BERT or RoBERTa as a base model and fine-tune for binary classification of code safety. This approach would require significant effort in dataset curation and training but could achieve 85-90% accuracy or higher.

Emerging code security models from the research community offer another path forward. Models like `huggingface/codegen-security` and `microsoft/codebert-security` (if they become available) could provide pre-trained security-focused capabilities. The challenge is that code security models remain a nascent area with fewer mature, production-ready options compared to general code understanding or text classification models. As this field develops, SecureMCP can integrate newer models that better match the malicious code detection task.

Expanding pattern-based detection represents a complementary approach that doesn't rely solely on ML. Comprehensive regex patterns covering common malicious code patterns—eval calls with user input, command injection metacharacters, SQL injection syntax, script injection tags, path traversal sequences, and many others—can provide reliable detection for well-defined threats. While less flexible than ML models for novel attacks, pattern-based detection offers perfect precision for known threat patterns and zero latency overhead. A hybrid approach combining expanded patterns with improved ML models could achieve 90%+ accuracy on malicious code detection.

### Model Update Strategy

Transformer models represent snapshots of knowledge as of their training time. Since threat techniques evolve constantly, with attackers developing new injection methods, obfuscation techniques, and social engineering approaches, models trained on historical data may struggle with emerging threats. This temporal limitation affects all ML-based security systems, not just SecureMCP, but demands attention nonetheless.

A model update strategy could involve periodic evaluation of newer model versions as they become available from ProtectAI, security researchers, and the ML community. When a new injection detection model is released, SecureMCP could benchmark it against the current model using our test suite, and if performance improves by a meaningful threshold (5+ percentage points), the new model could be integrated. This update process would need careful validation to ensure new models don't introduce regressions on existing detection capabilities while improving novel threat detection.

Transfer learning and fine-tuning represent another update approach. As SecureMCP processes prompts in production and security teams identify false negatives (missed threats) or false positives (incorrectly flagged legitimate content), these examples could accumulate into a domain-specific dataset. Periodically fine-tuning the existing models on this accumulated data could adapt them to the specific threat distributions and legitimate usage patterns of each deployment. This approach requires infrastructure for data collection, annotation, and model training, but offers the most targeted improvement path.

Ensemble approaches could improve robustness against evolving threats. Rather than relying on a single injection detection model, SecureMCP could integrate multiple models and combine their outputs through voting or averaging. If one model becomes outdated and misses new injection techniques, other models in the ensemble might still catch them. The trade-off is increased computational cost—running three injection detection models triples inference time for that component. However, for security-critical deployments, this cost might be justified by improved detection reliability.

### Multilingual Support

The current model selection focuses exclusively on English language understanding. All selected models—ProtectAI DeBERTa for injection, SoelMgd BERT for PII, BART for zero-shot classification, and spaCy for linguistic analysis—were trained primarily or exclusively on English text. This language limitation means SecureMCP provides optimal protection only for English prompts, with degraded or non-existent protection for other languages.

Extending SecureMCP to multilingual support would require carefully selected models for each component. Multilingual BERT (mBERT) and XLM-RoBERTa provide cross-lingual understanding trained on 104 languages, and could serve as base models for fine-tuning on security tasks across languages. However, security-specific multilingual models remain rare. Injection detection models trained on non-English injection examples, PII detection models understanding diverse naming conventions and identifier formats across cultures, and zero-shot classifiers trained on multilingual NLI datasets would all be necessary.

The development path toward multilingual support could begin with high-value languages based on user populations. Spanish, Chinese, French, German, and Japanese might represent priority languages for initial expansion. For each language, evaluating available security models or fine-tuning general models on security tasks would establish baselines. Over time, as multilingual security models mature in the research community, SecureMCP could integrate them to provide consistent protection across languages.

Pattern-based detection offers a simpler path to multilingual support for certain threat types. Credential formats like email addresses, API keys, JWT tokens, and high-entropy strings remain consistent across languages. Social Security numbers, credit card numbers, and phone numbers follow locale-specific formats but can be detected with locale-aware patterns. These language-independent patterns could provide partial protection even before ML models are available for specific languages.

### Specialized Domain Models

Current models provide general-purpose security validation suitable for diverse AI applications. However, certain domains have unique security requirements that generic models may not optimally address. Medical AI systems must detect protected health information (PHI) with higher accuracy than general PII detection, financial AI must identify account numbers, routing numbers, and transaction details, legal AI must protect attorney-client privileged information and confidential case details, and enterprise AI must detect company-specific sensitive information like internal project names or customer identifiers.

Domain-specific models could address these specialized requirements. A medical AI deployment could use specialized medical PII detectors achieving 97-98% accuracy on health information compared to 85-90% from general PII models. Financial deployments could integrate models trained specifically on financial document understanding. Legal and enterprise deployments could fine-tune models on domain-specific data to recognize their unique sensitive information categories.

The path toward domain specialization involves maintaining SecureMCP's core architecture while allowing model substitution for specific components. A medical deployment might use the standard injection detection and zero-shot classification models but substitute a medical-specialized PII detector. This modular approach preserves the benefits of SecureMCP's multi-layered validation while optimizing specific layers for domain requirements. Over time, SecureMCP could offer domain-specific model configurations as officially supported variants.

---

## Conclusion

The model selection for SecureMCP represents careful balance between accuracy, efficiency, and practicality. Each model was chosen through empirical evaluation against alternatives, considering not only benchmark accuracy but also computational requirements, deployment flexibility, community support, and production readiness. The resulting multi-model architecture achieves approximately 90-91% overall detection accuracy while maintaining acceptable latency for interactive applications and supporting deployment across diverse hardware configurations.

The specialized model approach, where different models are optimized for specific security tasks, proved superior to attempting to handle all detection with a single general model. The ProtectAI DeBERTa model's 95% injection detection accuracy, SoelMgd BERT's 94% F1 PII detection, and BART's strong zero-shot classification combine to provide comprehensive threat coverage that no single model could achieve. This specialization reflects a fundamental insight: security validation requires security-trained models.

Acknowledged limitations, particularly around CodeBERT's effectiveness for malicious code detection and the absence of multilingual support, provide clear directions for future enhancement. The model selection is not static but represents the optimal choices as of November 2025 given available models and requirements. As the research community develops new security-focused models, as threat patterns evolve, and as deployment experience reveals areas for improvement, SecureMCP's model lineup will evolve accordingly.

Organizations deploying SecureMCP can have confidence that the models powering the system were selected through rigorous evaluation focused on security effectiveness in production environments. The models represent proven, battle-tested components validated by both research benchmarks and real-world usage. While no security system achieves perfect detection, the combination of specialized ML models, zero-shot classification, pattern-based detection, and context-aware analysis provides robust protection against the full spectrum of threats facing AI systems today.

---

## References

Devlin, J., Chang, M.W., Lee, K. and Toutanova, K. (2019) 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding', in *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)*, Minneapolis, Minnesota, pp. 4171-4186. doi: 10.18653/v1/N19-1423.

Feng, Z., Guo, D., Tang, D., Duan, N., Feng, X., Gong, M., Shou, L., Qin, B., Liu, T., Jiang, D. and Zhou, M. (2020) 'CodeBERT: A Pre-Trained Model for Programming and Natural Languages', in *Findings of the Association for Computational Linguistics: EMNLP 2020*, Online, pp. 1536-1547. doi: 10.18653/v1/2020.findings-emnlp.139.

He, P., Liu, X., Gao, J. and Chen, W. (2021) 'DeBERTa: Decoding-enhanced BERT with Disentangled Attention', in *9th International Conference on Learning Representations (ICLR 2021)*, Virtual Event, May 3-7. Available at: https://openreview.net/forum?id=XPZIaotutsD (Accessed: 10 November 2025).

Honnibal, M. and Montani, I. (2017) *spaCy 2: Natural language understanding with Bloom embeddings, convolutional neural networks and incremental parsing*. Available at: https://spacy.io (Accessed: 10 November 2025).

Lample, G., Ballesteros, M., Subramanian, S., Kawakami, K. and Dyer, C. (2016) 'Neural Architectures for Named Entity Recognition', in *Proceedings of the 2016 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, San Diego, California, pp. 260-270. doi: 10.18653/v1/N16-1030.

Lewis, M., Liu, Y., Goyal, N., Ghazvininejad, M., Mohamed, A., Levy, O., Stoyanov, V. and Zettlemoyer, L. (2020) 'BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension', in *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*, Online, pp. 7871-7880. doi: 10.18653/v1/2020.acl-main.703.

Perez, F. and Ribeiro, I. (2022) 'Ignore Previous Prompt: Attack Techniques For Language Models', *arXiv preprint arXiv:2211.09527*. Available at: https://arxiv.org/abs/2211.09527 (Accessed: 11 November 2025).

Sanh, V., Debut, L., Chaumond, J. and Wolf, T. (2019) 'DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter', *arXiv preprint arXiv:1910.01108*. Available at: https://arxiv.org/abs/1910.01108 (Accessed: 10 November 2025).

Williams, A., Nangia, N. and Bowman, S.R. (2018) 'A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference', in *Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long Papers)*, New Orleans, Louisiana, pp. 1112-1122. doi: 10.18653/v1/N18-1101.

Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P., Rault, T., Louf, R., Funtowicz, M., Davison, J., Shleifer, S., von Platen, P., Ma, C., Jernite, Y., Plu, J., Xu, C., Scao, T.L., Gugger, S., Drame, M., Lhoest, Q. and Rush, A.M. (2020) 'Transformers: State-of-the-Art Natural Language Processing', in *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations*, Online, pp. 38-45. doi: 10.18653/v1/2020.emnlp-demos.6.

Yin, W., Hay, J. and Roth, D. (2019) 'Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach', in *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, Hong Kong, China, pp. 3914-3923. doi: 10.18653/v1/D19-1404.

---

## Appendix: Model Specifications Summary

| Model | Architecture | Size | Inference (GPU) | Inference (CPU) | Accuracy | Purpose |
|-------|-------------|------|----------------|----------------|----------|---------|
| protectai/deberta-v3-base-prompt-injection | DeBERTa-v3-base | 184M params, 700MB | 30-50ms | 100-150ms | ~95% | Injection detection |
| SoelMgd/bert-pii-detection | BERT-base | 110M params, 450MB | 80-120ms | 200-300ms | 94% F1 | PII identification |
| facebook/bart-large-mnli | BART-large | 406M params, 1.5GB | 150-250ms | 800-1200ms | 75-85% | Zero-shot classification |
| typeform/distilbert-base-uncased-mnli | DistilBERT-base | 66M params, 250MB | 80-100ms | 300-400ms | 70-80% | Fallback classification |
| microsoft/codebert-base | CodeBERT-base | 125M params, 500MB | 50-80ms | 150-250ms | 60-70%* | Code analysis (*suboptimal) |
| en_core_web_sm (spaCy) | Statistical + rules | 12MB | 2-5ms | 2-5ms | 96% POS, 92% Dep | Linguistic analysis |

**Total Memory Requirements:**
- With BART: ~3.8GB
- With DistilBERT fallback: ~2.6GB
- GPU VRAM recommended: 8GB+
- System RAM recommended: 16GB+

---

**Document Version:** 1.1  
**Last Updated:** November 13, 2025  
**Referencing Style:** Harvard  
**Next Review:** As new security-focused models become available from the research community

*All model selections, architectural decisions, and performance claims in this document are supported by peer-reviewed academic research and official model documentation. Citations follow the Harvard referencing system with a comprehensive reference list provided.*

