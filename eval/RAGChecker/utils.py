import os
import re
import json
from openai import OpenAI
from typing import List, Dict, Optional, Any, Union, Tuple
from dotenv import load_dotenv


query = {
    "llm_racial_bias_in_medicine": "Does the GPT-3.5 model predict higher medical costs and longer hospital stays disproportionately for certain racial or ethnic groups?",
    "lost_in_the_middle": "How does model performance vary based on relevant information position in context?",
    "llms_lack_self_correction": "How do self-correction methods impact large language model performance across math, commonsense reasoning, and multi-hop question answering benchmarks?",
    "awareness_detection": "Can language models detect that a given interaction transcript comes from an evaluation rather than real-world deployment?",
    "cot_without_prompting": "Can large language models, without any chain of thought prompts, reveal reasoning paths and improve answer accuracy by altering its decoding approach?",
    "cot_faithfulness_gaps": "To what extent do reasoning models’ chains-of-thought faithfully reflect their internal reasoning processes when they exploit external hints?",
    "llms_assume_rationality": "Do large language models accurately capture the irrational aspects of human decision-making, or do they instead assume that people behave according to rational choice theories (such as expected value theory)?",
    "to_cot_or_not_to_cot": "How much performance improvement does Chain-of-Thought (CoT) prompting provide over Direct Answer prompting across different reasoning categories (Commonsense, Knowledge, Symbolic, Mathematical, Soft Reasoning), and which categories show statistically signficant gains?",
    "uncertainty_in_instruction_following": "How effectively can large language models (LLMs) estimate their uncertainty when following user instructions, and how can this ability be systematically evaluated in a controlled setting?",
    "fractal_complexity_of_language": "When and why do LLMs deviate from the narrow fractal parameter range characteristic of natural language, as visualized by Holder and Hurst exponents?",
    "llm_value_consistency": "Do large language models exhibit the same value structure as humans, including the ranking of values and the correlations between values, and how does this depend on the way the model is prompted?",
    "hallucination_snowballing": "How do language model hallucinations propagate and compound over the course of a generation, and what mechanisms cause errors to snowball?",
    "counterfactual_simulatability": "Do natural language explanations provided by language models enable humans to accurately simulate the model's behavior under counterfactual inputs?",
    "premise_order_effects": "Does the order of premises affect the reasoning performance of LLMs, even when the logical content remains the same?",
    "persona_reasoning_biases": "Could persona assignment influence the fundamental reasoning capabilities of an LLM, even when the assigned persona is arguably tangential to the task at hand?",
    "mcq_selection_bias": "Are modern large language models robust in handling multiple choice questions, and if not, what causes their vulnerability, especially regarding their sensitivity to option position changes?",
    "prompt_formatting_sensitivity": "How sensitive are language models to superficial formatting choices in prompts, and do such spurious features significantly impact model performance?",
    "space_time_representations": "Do large language models learn coherent and grounded representations that reflect the real world, such as spatial and temporal representations, rather than just superficial statistics?",
    "llm_confidence_elicitation": "Can LLMs accurately express their uncertainty through black-box approaches, and how effective are various strategies for eliciting calibrated confidence?",
    "icl_from_repetition": "What is the underlying mechanism of in-context learning in LLMs, and how do surface repetitions, particularly token co-occurrence reinforcement, influence ICL?",
    "introspective_learning": "Can large language models acquire knowledge about their own internal behavioral tendencies through introspection, predicting their own behavior more accurately than another model trained on the same data?",
    "fallback_behaviors": "What behaviors do language models exhibit when they are uncertain, and how do these fallback patterns manifest across different models and tasks?",
    "cot_in_planning": "Does chain-of-thought prompting truly enable large language models to learn generalizable algorithmic reasoning abilities, or does it merely rely on highly specific, pattern-matching prompts?",
    "seca_hallucination": "Can semantically equivalent adversarial perturbations to input prompts cause language models to hallucinate or produce inconsistent outputs?",
    "distributive_fairness": "How fair are large language models when making resource allocation decisions across different demographic groups?",
    "lifebench_length_following": "How well do LLMs follow explicit length constraints in their generated outputs?",
    "hallucination_awareness": "Are large language models metacognitively aware of when they are hallucinating or producing unreliable outputs?",
    "questbench": "How well can large language models identify the single minimal clarification question needed to solve underspecified reasoning problems?",
    "persona_with_catch": "Does increasing the amount of LLM-generated persona content systematically worsen population-level simulation fidelity?",
    "activation_control": "Can we efficiently elicit long chain-of-thought reasoning in language models through activation-level interventions?",
    "object_hallucination_pope": "How severely do large vision-language models hallucinate objects not present in images, and what properties of objects make them more prone to hallucination?",
    "vlms_are_blind": "Can state-of-the-art VLMs perform trivially simple visual tasks like counting circles, detecting line intersections, or identifying which letter is circled in a word?",
    "charxiv_chart_understanding": "Can multimodal LLMs accurately understand and reason about real-world scientific charts, as opposed to the simplified template charts used in existing benchmarks?",
    "mathvista_visual_math": "How well can foundation models reason mathematically when problems are presented visually through charts, geometry diagrams, function plots, and tables?",
    "hallusionbench_illusion": "How do LVLMs handle visual illusions and manipulated images -- do they analyze the actual image or fall back on parametric knowledge from training?",
    "agentbench_llm_agents_rq0": "RQ1: How do LLMs perform as agents in code-grounded environments, specifically in operating systems, databases, and knowledge graphs?",
    "agentbench_llm_agents_rq1": "RQ2: How do LLMs perform as agents in game-grounded environments, specifically in digital card games, lateral thinking puzzles, and house-holding tasks?",
    "agentbench_llm_agents_rq2": "RQ3: How do LLMs perform as agents in web-grounded environments, specifically in web shopping and web browsing tasks?",
    "ai_assistants_insecure_code_rq0": "RQ1: Do users write more insecure code, defined as code with vulnerabilities or security flaws, when given access to an AI programming assistant, a tool that provides code suggestions and completions, across tasks involving encryption, signing, file path handling, SQL operations, and C string manipulation?",
    "ai_assistants_insecure_code_rq1": "RQ2: How does user trust in AI assistants (software tools that provide automated coding suggestions) to write secure code affect their perception of code security in tasks involving encryption, signing, file path handling, SQL operations, and C string manipulation?",
    "ai_assistants_insecure_code_rq2": "RQ3: How do users’ language and behavior when interacting with an AI assistant affect the degree of security vulnerabilities in their code across tasks involving encryption, signing, file path handling, SQL operations, and C string manipulation?",
    "alice_in_wonderland_rq0": "RQ1: Do state-of-the-art large language models (GPT-4, Claude 3 Opus) exhibit generalization and reasoning breakdowns when confronted with simple common sense problems like the AIW problem (a task designed to test basic reasoning and generalization) and its variations, as measured by correct response rates across different prompt types?",
    "alice_in_wonderland_rq1": "RQ2: Can control experiments using AIW Light problems, which are specifically designed tasks to isolate low-level factors such as language parsing and arithmetic operations, determine if these factors are responsible for the observed breakdowns in reasoning and generalization in large language models when tested with AIW Light Arithmetic Siblings datasets, which are variations of AIW Light problems focused on arithmetic tasks?",
    "alice_in_wonderland_rq2": "RQ3: Do standardized benchmarks like MMLU, GSM8k, and ARC-c accurately reflect the generalization and reasoning capabilities of state-of-the-art large language models, as assessed by their performance on simple Artificial Intelligence Workbench (AIW, a set of basic AI problems) tasks?",
    "bags_of_words_vlm_rq0": "RQ1: How well do current Vision-Language Models (CLIP, BLIP, Flava, X-VLM) understand compositional relationships, attribute binding, and word order in image-caption pairs, evaluated via the Attribution, Relation, and Order benchmarks built on Visual Genome, COCO, and Flickr30k?",
    "bags_of_words_vlm_rq1": "RQ2: Why do Vision-Language Models (VLMs, which integrate visual and textual data) perform well on retrieval tasks (matching images with corresponding text) despite poor compositional understanding, as evaluated on perturbed datasets like COCO and Flickr30k using metrics such as Recall@1 and Recall@5?",
    "bags_of_words_vlm_rq2": "RQ3: Can the selection of challenging negative examples based on compositional structures (the arrangement and combination of visual and textual elements) through composition-aware hard negative mining (a technique in contrastive learning that uses these challenging examples) enhance Vision-Language Models' ability to understand and process compositional relationships, as evaluated on COCO and Visual Genome datasets using Accuracy and Recall@1 metrics?",
    "bbq_bias_benchmark_rq0": "RQ1: How do current question-answering models (UnifiedQA, RoBERTa, DeBERTaV3) exhibit social biases across nine social dimensions (age, disability status, gender identity, nationality, physical appearance, race/ethnicity, religion, socio-economic status, sexual orientation) in ambiguous and disambiguated contexts?",
    "blink_perception_rq0": "RQ1: How well do current multimodal large language models (GPT-4V, Gemini, LLaVA) perform on the Blink benchmark, which includes tasks like visual correspondence, relative depth, and forensic detection?",
    "blink_perception_rq1": "RQ2: What are the effects of varying visual prompt attributes, such as shape size and color, on the performance of multimodal LLMs in tasks like relative depth estimation, relative reflectance, and visual correspondence using datasets such as 'Depth in the Wild', 'Intrinsic Images in the Wild', and 'HPatches'?",
    "bloomz_crosslingual_multitask_rq0": "RQ1: Does finetuning multilingual language models on tasks in a single language enhance their performance on tasks in other languages, evaluated using the xP3 dataset (a multilingual benchmark for cross-lingual transfer) and various performance metrics?",
    "bloomz_crosslingual_multitask_rq1": "Can models finetuned on multilingual datasets with English prompts generalize to tasks in languages not intentionally seen during pretraining or finetuning?",
    "bloomz_crosslingual_multitask_rq2": "RQ3: How does finetuning on machine-translated prompts affect performance on human-written non-English prompts for BLOOMZ and mT0 models?",
    "cambrian_visual_encoders_rq0": "RQ1: How do different visual encoder choices impact the multimodal capabilities of MLLMs, evaluated using benchmarks like GQA, AI2D, and TextVQA?",
    "cambrian_visual_encoders_rq1": "RQ2: What are the effects of different instruction tuning recipes on the performance of MLLMs, particularly in terms of adapter data size and freezing strategies?",
    "cambrian_visual_encoders_rq2": "RQ3: How does the integration of multiple vision features using aggregation methods impact the performance of multimodal large language models (MLLMs) on datasets such as GQA, DocVQA, and ScienceQA?",
    "cambrian_visual_encoders_rq3": "RQ4: How does data curation, including data balancing and ratio adjustments, affect the performance of MLLMs?",
    "chatbot_arena_human_eval_rq0": "RQ1: How does the Chatbot Arena platform, a system for evaluating large language models (LLMs, AI models trained on vast text data to understand and generate human-like language), achieve diversity and quality in user-generated questions across various real-world applications, as assessed by prompt diversity metrics and expert validation?",
    "chatbot_arena_human_eval_rq1": "RQ2: How does Chatbot Arena, a platform for evaluating conversational AI systems, rank large language models (LLMs, AI systems designed to understand and generate human language) in terms of accuracy and stability using pairwise comparison data?",
    "chatbot_arena_human_eval_rq2": "RQ3: How does Chatbot Arena, a platform for evaluating chatbot interactions through crowdsourced votes, ensure the reliability and consistency of these evaluations compared to expert and GPT-4 assessments, focusing on agreement rates and win-rate consistency across randomly selected interactions?",
    "clip_visual_shortcomings_rq0": "RQ1: What are the systematic visual patterns that CLIP-based vision encoders struggle with, and how do these affect the performance of multimodal large language models (MLLMs) like GPT-4V?",
    "clip_visual_shortcomings_rq1": "RQ2: Can integrating vision-only self-supervised learning features with multimodal large language models improve their visual grounding capabilities?",
    "compositionality_gap_rq0": "RQ1: How does the compositionality gap manifest in language models of varying sizes, specifically within the GPT-3 family, when evaluated on multi-hop question answering tasks?",
    "compositionality_gap_rq1": "RQ2: Can elicitive prompting techniques, which involve guiding language models to generate intermediate reasoning steps, effectively narrow the compositionality gap (the difficulty language models face in combining known concepts to solve novel problems) across datasets such as Compositional Celebrities, Bamboogle, 2WikiMultiHopQA, and Musique, using metrics like Accuracy, F1, and Cover-EM?",
    "compositionality_gap_rq2": "RQ3: How does integrating external information retrieval capabilities impact the performance of language models on compositional question answering tasks, which require synthesizing information from multiple sources, as evaluated through standard datasets and metrics?",
    "compound_noun_understanding_rq0": "RQ1: How well do current vision-language models (CLIP, OpenCLIP, ALIGN, ALBEF, BLIP, MetaCLIP) interpret compound nouns in text-to-image retrieval tasks using the Compun benchmark with 400 unique CNs?",
    "compound_noun_understanding_rq1": "RQ2: Can generating diverse captions using a large language model improve the understanding of compound nouns by vision-language models in text-to-image retrieval tasks?",
    "do_anything_now_jailbreaks_rq0": "RQ1: What are the characteristics and distribution patterns of in-the-wild jailbreak prompts across platforms like Reddit, Discord, and prompt-aggregation websites?",
    "do_anything_now_jailbreaks_rq1": "RQ2: How effective are in-the-wild jailbreak prompts in bypassing the safeguards of popular LLMs like ChatGPT (GPT-3.5), GPT-4, and PaLM2 across various forbidden scenarios?",
    "do_anything_now_jailbreaks_rq2": "RQ3: How effective are external safeguards, such as the OpenAI moderation endpoint and NeMo-Guardrails, in reducing the success rate of jailbreak prompts (inputs designed to bypass restrictions) on large language models like ChatGPT (GPT-3.5)?",
    "embers_of_autoregression_rq0": "RQ1: How does the frequency of tasks in training data affect the performance of large language models (GPT-3.5 and GPT-4) on tasks like shift ciphers, Pig Latin, acronyms, linear functions, and sorting?",
    "embers_of_autoregression_rq1": "RQ2: How does the probability of the target output affect the performance of large language models (GPT-3.5 and GPT-4) on tasks like shift ciphers, reversal, Pig Latin, article swapping, acronyms, and counting?",
    "embers_of_autoregression_rq2": "RQ3: How does the probability of the input affect the performance of large language models (GPT-3.5 and GPT-4) on tasks like shift ciphers, reversal, Pig Latin, acronyms, and counting?",
    "emergent_abilities_mirage_rq0": "RQ1: Do emergent abilities, defined as unexpected performance improvements, in the InstructGPT/GPT-3 model family on arithmetic tasks disappear when nonlinear metrics like Accuracy are replaced with linear metrics like Token Edit Distance, using 2-shot multiplication and addition tasks?",
    "emergent_abilities_mirage_rq1": "RQ2: Do emergent abilities, defined as unexpected capabilities that arise in large language models, in the BIG-Bench tasks predominantly appear with specific nonlinear or discontinuous metrics such as Brier Score (a measure of the accuracy of probabilistic predictions), rather than being inherent to task-model family combinations?",
    "emergent_abilities_mirage_rq2": "RQ3: Can emergent abilities, defined as unexpected capabilities that arise in machine learning models, be induced in vision tasks using shallow nonlinear autoencoders on the CIFAR100 dataset and autoregressive Transformers (models predicting future data points based on past ones) on the Omniglot dataset by selecting specific evaluation metrics?",
    "evalplus_code_correctness_rq0": "RQ1: How does augmenting existing code evaluation benchmarks like HUMANEVAL with additional test-cases generated by large language models (LLMs) and mutation-based strategies affect the assessment of functional correctness in LLM-generated code?",
    "evalplus_code_correctness_rq1": "RQ2: What is the impact of test-suite reduction on the evaluation effectiveness of LLM-generated code using the HUMANEVAL+ benchmark?",
    "faith_and_fate_compositionality_rq0": "RQ1: How do transformer-based large language models (LLMs) perform on compositional tasks such as multi-digit multiplication, logic grid puzzles, and dynamic programming problems across zero-shot, few-shot, and fine-tuning settings? RQ2: What are the underlying mechanisms used by transformer-based large language models (LLMs) to solve compositional tasks like multi-digit multiplication, logic grid puzzles, and dynamic programming problems?",
    "faith_and_fate_compositionality_rq1": "RQ2: What are the types of errors made by transformer LLMs at different reasoning depths in compositional tasks?",
    "freshqa_changing_knowledge_rq0": "RQ1: How well do current large language models (BARD, CHATGPT/GPT-4, T5, PALM, FLAN-T5) perform on the FRESHQA benchmark, which includes questions requiring fast-changing knowledge, slow-changing knowledge, never-changing knowledge, and false premises?",
    "freshqa_changing_knowledge_rq1": "RQ2: How does incorporating search engine results into prompts affect the factual accuracy and hallucination rate of large language models (LLMs) when evaluated on question-answering tasks?",
    "gcg_adversarial_attacks_rq0": "RQ1: Can adversarial suffixes, which are text sequences appended to prompts to manipulate model outputs, be generated to induce objectionable content in aligned language models (models fine-tuned to follow ethical guidelines) across multiple prompts and models, including Vicuna-7B, Vicuna-13B, and Guanaco-7B?",
    "gcg_adversarial_attacks_rq1": "RQ2: Do adversarial prompts, which are inputs designed to manipulate model outputs, transfer effectively to proprietary black-box models like GPT-3.5, GPT-4, and Claude when optimized on open-source models, which are models with publicly accessible code and architecture, such as Vicuna and Guanaco?",
    "geval_llm_evaluator_rq0": "RQ1: How does an AI-based evaluation system perform in assessing text summarization quality compared to existing metrics, using correlation measures such as Spearman and Kendall-Tau on a standard benchmark?",
    "geval_llm_evaluator_rq1": "RQ2: How does a novel evaluation metric for dialogue response generation quality perform compared to existing metrics in terms of correlation with human judgments on a benchmark dataset using Pearson and Spearman correlation?",
    "geval_llm_evaluator_rq2": "RQ3: How does the evaluation metric G-EVAL perform in detecting hallucinations, defined as false or misleading content, in summarization tasks compared to existing metrics, as measured by correlation metrics on the QAGS benchmark datasets QAGS-CNN and QAGS-XSUM?",
    "gpt4_code_math_verification_rq0": "RQ1: How does the frequency of code usage affect the mathematical problem-solving capabilities of GPT-4 Code Interpreter on the MATH dataset?",
    "gpt4_code_math_verification_rq1": "RQ2: Does the use of explicit self-verification techniques impact the accuracy of a language model, specifically GPT-4's code execution capabilities, in solving math problems on the MATH, GSM8K, and MMLU-Math datasets?",
    "gsm_symbolic_rq0": "RQ1: How reliable are the current evaluation metrics for mathematical reasoning in large language models when using the GSM8K benchmark compared to the GSM-Symbolic benchmark?",
    "gsm_symbolic_rq1": "RQ2: How does the fragility of mathematical reasoning in large language models manifest when altering superficial elements like names versus numerical values in questions?",
    "gsm_symbolic_rq2": "RQ3: How does the complexity of mathematical questions, indicated by the number of clauses, affect the performance distribution of large language models?",
    "gsm_symbolic_rq3": "RQ4: Can large language models (LLMs, neural networks trained on vast text corpora) accurately solve mathematical problems by discerning relevant information, or do they rely on pattern matching when irrelevant information is added, as evaluated using 8-shot Chain-of-Thought prompting on the GSM-NoOp dataset?",
    "inverse_scaling_rq0": "RQ1: What are the potential causes of inverse scaling in large language models across various tasks and datasets?",
    "inverse_scaling_rq1": "RQ2: How do different model series and training setups affect the presence of inverse scaling trends?",
    "irrelevant_context_distraction_rq0": "RQ1: How does the presence of irrelevant context affect the problem-solving accuracy of large language models on arithmetic problems from the GSM-IC dataset, which consists of grade school math problems, as measured by micro and macro accuracy using various advanced prompting techniques?",
    "irrelevant_context_distraction_rq1": "RQ2: What strategies can mitigate the distractibility of large language models when irrelevant context is present in problem descriptions?",
    "jailbroken_safety_failure_modes_rq0": "RQ1: How do competing objectives in safety-trained large language models, such as GPT-4 and Claude v1.3, contribute to their vulnerability to jailbreak attacks (bypassing safety mechanisms), evaluated through prefix injection (adding harmless-looking prefixes) and refusal suppression (avoiding refusal phrases) techniques on a curated dataset of harmful prompts?",
    "jailbroken_safety_failure_modes_rq1": "RQ2: How does mismatched generalization between pretraining and safety training in large language models (such as GPT-4 and Claude v1.3) lead to vulnerabilities against jailbreak attacks, evaluated through Base64 encoding and other obfuscation techniques?",
    "language_contamination_crosslingual_rq0": "RQ1: How much non-English text exists in commonly used English pretraining corpora, and what is its composition?",
    "language_contamination_crosslingual_rq1": "RQ2: How well do English pretrained models perform on non-English tasks, and what factors influence their cross-lingual transfer capabilities?",
    "length_controlled_alpacaeval_rq0": "RQ1: How does length control affect the gameability of AlpacaEval, a benchmark for instruction-tuned language models, when models are prompted for verbosity?",
    "length_controlled_alpacaeval_rq1": "RQ2: Does controlling for response length in evaluations using the AlpacaEval dataset, a benchmark for assessing language model outputs, improve the Spearman correlation with human evaluation rankings in the LMSYS Chatbot Arena, a platform for comparing chatbot performance?",
    "length_controlled_alpacaeval_rq2": "RQ3: How does a length-controlled evaluation dataset (where response lengths are adjusted to a standard) for chatbot performance compare in terms of robustness and interpretability to other length correction methods (such as length-normalized and length-balanced win rates), as measured by correlation with human judgments, susceptibility to manipulation, and improvement in performance against adversarial inputs?",
    "lets_verify_step_by_step_rq0": "RQ1: Does process supervision, which involves guiding models through intermediate steps, outperform outcome supervision, which focuses on final results, in training reward models for large-scale language models solving problems from the MATH dataset, as measured by the percentage of problems solved?",
    "lets_verify_step_by_step_rq1": "RQ2: How does active learning impact the data efficiency of process supervision in training reward models for mathematical reasoning tasks?",
    "lets_verify_step_by_step_rq2": "RQ3: Can a large reward model approximate human supervision effectively for training smaller reward models in mathematical reasoning tasks?",
    "llm_error_finding_rq0": "RQ1: How well do state-of-the-art LLMs (GPT-4, GPT-3.5, PaLM 2, Gemini Pro) perform in finding reasoning mistakes in Chain-of-Thought (CoT) traces across tasks like word sorting, tracking shuffled objects, logical deduction, multi-step arithmetic, and Dyck languages?",
    "llm_error_finding_rq1": "RQ2: Can LLMs correct reasoning errors in CoT traces when provided with oracle mistake location information, and how does this affect downstream task performance across tasks like word sorting, tracking shuffled objects, logical deduction, multi-step arithmetic, and Dyck languages?",
    "llm_error_finding_rq2": "RQ3: What is the mistake-finding accuracy of large language models (LLMs, which are AI systems trained on vast text corpora) when evaluated on out-of-domain data from the BIG-Bench Mistake dataset, and what is the minimum accuracy threshold required for effective backtracking (revisiting and correcting errors)?",
    "llm_judge_position_bias_rq0": "RQ1: How does the order of candidate responses affect the evaluation outcomes when using GPT-4 and ChatGPT as evaluators for AI-generated responses?",
    "llm_judge_position_bias_rq1": "RQ2: How effective are calibration strategies in mitigating positional bias (preference for certain positions in a sequence) in large language model evaluators? RQ3: To what extent do calibration strategies improve alignment with human judgments in large language model evaluations?",
    "loft_long_context_subsume_rag_rq0": "RQ1: How well do Long-Context Language Models (LCLMs, which can process extended sequences of input data) perform in text, visual, and audio retrieval tasks compared to specialized models like CLIP for visual retrieval and PaLM 2 DE for audio retrieval, using datasets such as ArguAna, MS COCO, and FLEURS-en?",
    "loft_long_context_subsume_rag_rq1": "RQ2: Can Long-Context Language Models (LCLMs, which process extended sequences of text) effectively perform Retrieval-Augmented Generation (RAG, a task involving retrieving relevant information from a corpus to generate responses) on datasets like NQ, TopiOCQA, and HotPotQA, as measured by subspan exact match metrics?",
    "loft_long_context_subsume_rag_rq2": "RQ3: How capable are Long-Context Language Models (LCLMs, which can process and generate text with extended context) in performing SQL-like compositional reasoning tasks (tasks that require combining multiple logical operations to query databases) compared to specialized SQL pipelines?",
    "loft_long_context_subsume_rag_rq3": "RQ4: How do Long-Context Language Models (LCLMs, which can process extended sequences of text) perform in many-shot in-context learning (ICL, where models learn from examples provided within the input context) tasks compared to traditional few-shot setups, specifically on datasets like BBH-date, BBH-salient, BBH-tracking7, BBH-web, and LIB-dialogue using classification accuracy as the metric?",
    "longbench_bilingual_context_rq0": "RQ1: How do large language models perform on single-document and multi-document question answering tasks when evaluated with LongBench, which includes datasets like NarrativeQA, Qasper, MultiFieldQA, HotpotQA, and DuReader?",
    "longbench_bilingual_context_rq1": "RQ2: How do large language models perform on summarization tasks using LongBench, which includes datasets like GovReport, QMSum, MultiNews, and VCSUM?",
    "longbench_bilingual_context_rq2": "RQ3: How do large language models perform on few-shot learning tasks using LongBench, which includes datasets like TREC, TriviaQA, SAMSum, and LSHT?",
    "longbench_bilingual_context_rq3": "RQ4: How do large language models perform on synthetic tasks and code completion tasks using LongBench, which includes datasets like PassageCount, PassageRetrieval, LCC, and RepoBench-P?",
    "mm_vet_integrated_rq0": "RQ1: How effectively do current large multimodal models (OpenFlamingo, LLaVA, MiniGPT-4, Otter, InstructBLIP) integrate core vision-language capabilities (recognition, OCR, knowledge, language generation, spatial awareness, math) across 16 emergent tasks?",
    "mm_vet_integrated_rq1": "RQ2: How does a large language model (LLM)-based evaluator perform in assessing open-ended outputs from large multimodal models (LMMs) using the MM-Vet dataset, which contains multimodal evaluation tasks, and averaged absolute differences (the mean of absolute score differences) as metrics?",
    "mmbench_comprehensive_rq0": "RQ1: How effectively does a benchmark for evaluating vision-language models (VLMs) assess the multi-modal capabilities of these models across 20 ability dimensions using bilingual multiple-choice questions in English and Chinese?",
    "mmbench_comprehensive_rq1": "RQ2: How effective is the strategy of using multiple evaluation passes with shuffled choices in providing robust evaluation results for vision-language models on the MMBench dataset, a benchmark for multimodal understanding, compared to traditional evaluation methods, as measured by Top-1 accuracy?",
    "mmbench_comprehensive_rq2": "RQ3: How does the use of large language models (LLMs) as choice extractors impact the evaluation accuracy of vision-language models on MMBench?",
    "mt_bench_llm_judge_rq0": "RQ1: How well do large language models (GPT-4, GPT-3.5, Claude-V1) align with human preferences in evaluating chatbots on MT-Bench and Chatbot Arena datasets?",
    "mt_bench_llm_judge_rq1": "RQ2: What are the limitations and biases, such as position bias, verbosity bias, and limited reasoning ability, of using large language models as judges in the context of evaluating responses on the MT-Bench dataset?",
    "multilingual_cot_reasoning_rq0": "RQ1: How well do large language models perform on the Multilingual Grade School Math (MGSM) benchmark, which involves solving arithmetic problems in ten typologically diverse languages using various prompting strategies that generate intermediate reasoning steps before arriving at a final answer?",
    "multilingual_cot_reasoning_rq1": "RQ2: How do large language models perform on multilingual reasoning benchmarks, such as XCOPA and XL-WiC, when evaluated using few-shot prompting with multilingual exemplars?",
    "nonverbal_abstract_reasoning_rq0": "RQ1: Do multi-modal large language models (MLLMs, which process and integrate information from multiple modalities such as text and images) demonstrate faithful nonverbal abstract reasoning abilities using Raven’s Progressive Matrices (RPM, a set of visual puzzles designed to assess abstract reasoning) benchmarks, specifically on the IQ50, RAVEN-S, and CCSE datasets in zero-shot and few-shot settings?",
    "nonverbal_abstract_reasoning_rq1": "RQ2: What are the root causes of poor performance in nonverbal abstract reasoning tasks by Multimodal Large Language Models (MLLMs, which integrate text and visual data), specifically in terms of their textual reasoning and visual awareness capabilities as evaluated on the IQ50 dataset, a benchmark for assessing abstract reasoning through text-only and visual questions?",
    "nonverbal_abstract_reasoning_rq2": "RQ3: How do multimodal large language models (MLLMs, which process both text and other modalities like images) perform on nonverbal abstract reasoning tasks, as evaluated by performance improvement percentage on the IQ50 dataset?",
    "ocrbench_text_understanding_rq0": "RQ1: How well do Large Multimodal Models (e.g., GPT4V, Gemini) perform in text recognition tasks across regular, irregular, occluded, artistic, handwritten, Chinese, and non-semantic text datasets?",
    "ocrbench_text_understanding_rq1": "RQ2: How do Large Multimodal Models perform in Scene Text-Centric Visual Question Answering (VQA) tasks using datasets like STVQA, TextVQA, OCRVQA, and ESTVQA?",
    "ocrbench_text_understanding_rq2": "RQ3: How effective are Large Multimodal Models in Document-Oriented Visual Question Answering (VQA) tasks using datasets such as DocVQA, InfographicVQA, and ChartQA?",
    "ocrbench_text_understanding_rq3": "RQ4: How do Large Multimodal Models perform in Key Information Extraction (KIE) tasks using datasets like SROIE, FUNSD, and POIE?",
    "ocrbench_text_understanding_rq4": "RQ5: How well do Large Multimodal Models recognize handwritten mathematical expressions using the HME100K dataset?",
    "pal_program_aided_reasoning_rq0": "RQ1: How does the use of programmatic reasoning steps with a Python interpreter impact the accuracy of large language models on mathematical reasoning tasks, as evaluated on datasets such as GSM8K, SVAMP, ASDIV, and MAWPS?",
    "pal_program_aided_reasoning_rq1": "RQ2: Do language models that utilize external program execution, where models execute code to aid reasoning, achieve higher solve rates than those using step-by-step reasoning prompts in symbolic reasoning tasks such as COLORED OBJECTS (identifying attributes of colored items), PENGUINS (logical deduction about penguin characteristics), and DATE (calculating dates and times)?",
    "pal_program_aided_reasoning_rq2": "RQ3: How does a program-aided language model (PAL), which uses external tools like a Python interpreter to assist in reasoning, perform on algorithmic reasoning tasks such as OBJECT COUNTING and REPEAT COPY compared to chain-of-thought prompting, where models generate intermediate reasoning steps in natural language during few-shot prompting?",
    "parametric_vs_nonparametric_memory_rq0": "RQ1: How much factual knowledge is memorized by large language models (GPT-Neo, OPT, GPT-3) and what factors (entity popularity, relationship type) affect this memorization on open-domain QA datasets (POPQA, EntityQuestions)?",
    "parametric_vs_nonparametric_memory_rq1": "RQ2: To what extent can non-parametric memories (retrieval-augmented language models using external data sources like BM25 and Contriever) improve the performance of large language models with parametric memories (internal model weights) on long-tail factual knowledge (information about less popular entities) when evaluated on the POPQA and EntityQuestions datasets?",
    "parametric_vs_nonparametric_memory_rq2": "RQ3: How does adaptively combining non-parametric memories (external knowledge sources) and parametric memories (information stored within model parameters) based on entity popularity affect the efficiency and performance of language models?",
    "perception_test_video_rq0": "RQ1: How well do pre-trained multimodal models perform on the Perception Test across different skill areas (Memory, Abstraction, Physics, Semantics) and reasoning types (descriptive, explanatory, predictive, counterfactual) using real-world videos?",
    "prismatic_vlm_design_rq0": "RQ1: What are the effects of different optimization procedures on the performance of visually-conditioned language models (VLMs) across visual question answering, object localization, and challenge tasks?",
    "prismatic_vlm_design_rq1": "RQ2: How do different image processing techniques and visual representations impact the performance of VLMs on visual question answering, object localization, and challenge tasks?",
    "prismatic_vlm_design_rq2": "RQ3: What is the impact of using base language models versus instruct-tuned language models (models fine-tuned with specific instructions) on the performance and safety of vision-language models (VLMs, which integrate visual and textual data) when evaluated on LLaVa v1.5 pretraining datasets for visual question answering, object localization, and challenge tasks?",
    "prismatic_vlm_design_rq3": "RQ4: How do scaling properties such as training time and data diversity affect the performance of VLMs?",
    "react_reasoning_acting_rq0": "RQ1: How does integrating reasoning and acting within a single framework perform on knowledge-intensive reasoning tasks, specifically multi-hop question answering using the HotpotQA dataset and fact verification using the FEVER dataset, evaluated through metrics like Exact Match and Accuracy?",
    "react_reasoning_acting_rq1": "RQ2: How does performance on interactive decision-making tasks, such as ALFWorld for text-based interactions and WebShop for real-world web interactions, vary when evaluated using metrics like Success Rate and Score?",
    "red_teaming_reduce_harms_rq0": "RQ1: How do scaling behaviors affect the efficacy of red teaming across different model sizes and types, including plain language models, prompted models, rejection sampling models, and reinforcement learning from human feedback models?",
    "red_teaming_reduce_harms_rq1": "RQ2: What types of harmful outputs are uncovered by red teaming, a process where simulated attacks are conducted to identify vulnerabilities, and how can these outputs be categorized and analyzed using a large dataset of attacks and various visualization and annotation techniques?",
    "red_teaming_reduce_harms_rq2": "RQ3: How can a dataset of red team attacks, which are simulated adversarial interactions designed to test vulnerabilities, be used to improve the safety of language models?",
    "reversal_curse_rq0": "RQ1: Do auto-regressive language models (e.g., GPT-3, Llama-1, which predict the next word in a sequence) trained on synthetic facts (artificially generated data) of the form 'A is B' generalize to the reverse form 'B is A' in the context of a synthetic dataset of fictitious facts?",
    "reversal_curse_rq1": "RQ2: Does the Reversal Curse, where language models struggle to generalize facts when presented in reverse order, affect the ability of state-of-the-art models like GPT-4 to accurately identify parent-child relationships in real-world datasets such as the IMDB top 1000 celebrities?",
    "reversal_curse_rq2": "RQ3: Can auto-regressive language models generalize from question-answer instructions presented in one order to the reverse order?",
    "rgb_rag_benchmark_rq0": "RQ1: How robust are large language models (ChatGPT, ChatGLM-6B, ChatGLM2-6B, Vicuna-7b, Qwen-7B-Chat, BELLE-7B) to noise in retrieval-augmented generation, evaluated across varying noise ratios in English and Chinese?",
    "rgb_rag_benchmark_rq1": "RQ2: Can large language models (ChatGPT, ChatGLM-6B, ChatGLM2-6B, Vicuna-7b, Qwen-7B-Chat, BELLE-7B) effectively reject questions when required knowledge is absent in retrieved documents, evaluated in English and Chinese?",
    "rgb_rag_benchmark_rq2": "RQ3: How well can large language models (ChatGPT, ChatGLM-6B, ChatGLM2-6B, Vicuna-7b, Qwen-7B-Chat, BELLE-7B) integrate information from multiple documents in retrieval-augmented generation, evaluated across varying noise ratios in English and Chinese?",
    "rgb_rag_benchmark_rq3": "RQ4: Can large language models (ChatGPT, Qwen-7B-Chat) identify and correct factual errors in retrieved documents when given warnings, evaluated in English and Chinese?",
    "self_rag_adaptive_retrieval_rq0": "RQ1: How do retrieval (accessing external information sources) and self-reflection (evaluating and refining one's own outputs) mechanisms enhance the factual accuracy and generation quality of large language models across tasks such as open-domain question answering, reasoning, fact verification, and long-form generation, as evaluated on datasets like PopQA, TriviaQA-unfiltered, PubHealth, ARC-Challenge, Biography generation, and ALCE-ASQA?",
    "seven_failure_points_rag_rq0": "RQ1: What are the failure points that occur when engineering a Retrieval Augmented Generation (RAG) system using the BioASQ dataset with 15,000 documents and 1000 question-answer pairs?",
    "seven_failure_points_rag_rq1": "RQ2: What are the key considerations for software engineers when implementing Retrieval Augmented Generation (RAG) systems, which combine information retrieval with text generation, across diverse domains such as research, education, and biomedical fields?",
    "survey_response_biases_rq0": "RQ1: Do large language models (LLMs) exhibit human-like response biases, such as acquiescence, allow/forbid asymmetry, response order, opinion floating, and odd/even scale effects, when evaluated on survey questions derived from Pew Research's American Trends Panel?",
    "survey_response_biases_rq1": "RQ2: How do large language models (LLMs) respond to non-bias perturbations, such as typos, letter swaps, and middle randomization, in survey questions derived from Pew Research's American Trends Panel?",
    "swe_bench_github_issues_rq0": "RQ1: How well do state-of-the-art language models perform in resolving software engineering issues from real-world GitHub repositories using the SWE-bench framework, a benchmark for evaluating code patch generation by assessing the percentage of issues resolved and patches applied?",
    "swe_bench_github_issues_rq1": "RQ2: What are the characteristics and challenges of the SWE-bench benchmark in evaluating language models on software engineering tasks?",
    "sycophancy_in_llms_rq0": "RQ1: Do AI assistants exhibit sycophancy, defined as providing biased feedback that aligns with user preferences, across varied free-form text-generation tasks such as feedback on math solutions, arguments, and poems?",
    "sycophancy_in_llms_rq1": "RQ2: Do AI assistants change their correct answers to incorrect ones when challenged by users across multiple QA datasets?",
    "sycophancy_in_llms_rq2": "RQ3a: In open-ended question-answering tasks, where questions do not have a single correct answer, do AI assistants modify their responses to align with user beliefs (preconceived notions or opinions stated in prompts)? RQ3b: Does the alignment of AI assistant responses with user beliefs affect the accuracy of their answers in open-ended question-answering tasks?",
    "sycophancy_in_llms_rq3": "RQ4: Do AI assistants (software programs designed to assist users with tasks) mimic (repeat or imitate) user mistakes (errors made by users) in the context of attributing authorship of poems, specifically when users incorrectly attribute authorship in tasks involving 15 famous poems with incorrect attributions?",
    "tokenization_cost_disparity_rq0": "RQ1: How do tokenization lengths differ across languages for various tokenization models, including subword, multilingual, and byte-level models, using the FLORES-200 parallel corpus?",
    "tokenization_cost_disparity_rq1": "RQ2: What are the fairness implications of tokenization length differences across languages in terms of cost, latency, and long context processing?",
    "toolformer_self_taught_tools_rq0": "RQ1: Can a language model autonomously learn to use a variety of external tools, such as a calculator, a Q&A system, a search engine, a translation system, and a calendar, to improve zero-shot performance on downstream tasks?",
    "toolformer_self_taught_tools_rq1": "RQ2: Does the self-supervised learning of tool use affect the core language modeling abilities of the language model?",
    "truthfulqa_mimicking_falsehoods_rq0": "RQ1: How truthful are current language models (GPT-3, GPT-Neo/J, GPT-2, UnifiedQA) in generating answers to questions across 38 categories, including health, law, and conspiracies, in a zero-shot setting?",
    "truthfulqa_mimicking_falsehoods_rq1": "RQ2: How does model size affect the truthfulness of language models (GPT-3, GPT-Neo/J, GPT-2, UnifiedQA) on the TruthfulQA benchmark?",
    "truthfulqa_mimicking_falsehoods_rq2": "RQ3: Can automated metrics effectively predict human evaluations of truthfulness in language models?",
    "v_star_visual_search_rq0": "RQ1: How does the integration of the V∗ visual search mechanism, which enhances focus on specific visual details in high-resolution images, affect the accuracy of multimodal large language models (MLLMs) on attribute recognition and spatial relationship reasoning tasks using the V∗Bench dataset, a benchmark for evaluating visual question answering?",
    "v_star_visual_search_rq1": "RQ2: What is the effectiveness of a visual search algorithm in reducing search length and improving search efficiency when locating target objects within high-resolution images, compared to random and sequential search strategies?",
    "v_star_visual_search_rq2": "RQ3: How does the integration of a visual search mechanism (a system that identifies and retrieves visual information) affect the general multimodal capabilities (the ability to process and understand information from multiple modalities) of the SEAL framework (a system for evaluating and enhancing multimodal learning) across benchmarks like MME, POPE, and MMBench, when evaluated on performance in multimodal tasks?",
    "visual_instruction_tuning_rq0": "RQ1: How effective is the use of GPT-4 generated multimodal instruction-following data, which combines visual and textual instructions, in training large multimodal models like LLaVA (Large Language and Vision Assistant) for enhanced visual and language understanding, as evaluated on a synthetic dataset designed to test multimodal instruction-following capabilities?",
    "visual_instruction_tuning_rq1": "RQ2a: What are the capabilities of a large language and vision assistant in multimodal reasoning when fine-tuned on a dataset of science questions requiring reasoning across text and images?",
    "webarena_web_agents_rq0": "RQ1: How effective is a simulated web environment, WebArena, in providing a realistic and reproducible setting for tasks across the domains of e-commerce, social forums, collaborative development, and content management?",
    "webarena_web_agents_rq1": "RQ2a: How well do baseline large language models perform on the WebArena benchmark tasks, which assess language understanding and reasoning in web-based environments, using task success rate as the metric? RQ2b: What are the limitations of current large language models when evaluated on the WebArena benchmark tasks, which involve few-shot in-context learning with and without explicit reasoning steps?",
    "webarena_web_agents_rq2": "RQ3: What are the key challenges and areas for improvement in developing robust autonomous agents for complex web-based tasks in WebArena?",
    "winoground_compositionality_rq0": "RQ1: How well do state-of-the-art vision and language models (UNITER, ViLLA, VinVL, VisualBERT, ViLT, LXMERT, ViLBERT, UniT, FLAVA, CLIP, VSE++, VSRN) perform on the Winoground task, which requires matching images and captions with identical words in different orders?",
    "winoground_compositionality_rq1": "RQ2: What insights can be gained from analyzing the performance of vision and language models on the Winoground task, particularly in terms of linguistic and visual tags?",
}


gt = {
    "mathvista_visual_math": "Foundation models like GPT-4V can reason mathematically with visual problems at roughly half accuracy, excelling in algebraic and scientific reasoning but struggling with logical reasoning and numerical common sense.",
    "to_cot_or_not_to_cot": "Chain-of-Thought achieves performance gain on math and formal logic. CoT does not achieve statistically significant performance gain, sometimes even producing slight loss, on most other task categories including commonsense, knowledge, and soft reasoning.",
    "llm_racial_bias_in_medicine": "LLMs predict higher medical costs and longer hospital stays disproportionately for certain racial groups. Assessment and plans created by the model showed significant association between demographic attributes and recommendations for more expensive procedures, projected hospitalization durations, as well as differences in patient perception.",
    "cot_without_prompting": "Large language models can reveal reasoning paths and improve answer accuracy by altering the decoding approach. Exploring alternative token sequences uncovers hidden reasoning trajectories, and selecting the path with the highest answer confidence significantly outperforms standard greedy decoding.",
    "seca_hallucination": "Semantically equivalent adversarial perturbations to input prompts can cause language models to hallucinate or produce inconsistent outputs.",
    "counterfactual_simulatability": "Natural language explanations provided by language models do not enable humans to accurately simulate the model's behavior under counterfactual inputs.",
    "vlms_are_blind": "State-of-the-art vision-language models perform far below human-level accuracy on trivially simple visual tasks like counting circles, detecting line intersections, or identifying overlapping shapes.",
    "persona_with_catch": "Increasing the amount of LLM-generated persona content systematically worsens population-level simulation fidelity. While richer persona descriptions may appear more detailed, they introduce artifacts and biases that reduce the accuracy of simulating real-world population distributions in opinion surveys and election predictions.",
    "questbench": "LLMs struggle to identify the single minimal clarification question needed to solve underspecified reasoning problems. Performance varies substantially across algebra, logic, and planning tasks, and degrades as problem complexity increases. Models often fail to recognize what information is missing to disambiguate the problem.",
    "awareness_detection": "Frontier language models can detect that a given interaction transcript comes from an evaluation rather than real-world deployment with significant accuracy.",
    "hallusionbench_illusion": "Large vision-language models, like GPT-4V, tend to fall back on parametric knowledge from training rather than accurately analyzing the actual image when handling visual illusions and manipulated images.",
    "introspective_learning": "Large language models can predict their own behavior in hypothetical scenarios more accurately than another model trained on the same behavioral data, demonstrating a form of introspection. However, this self-prediction is limited to simple tasks and does not generalize well to complex or out-of-distribution tasks.",
    "cot_faithfulness_gaps": "Reasoning models' chains-of-thought rarely reflect their internal reasoning processes when exploiting external hints.",
    "icl_from_repetition": "In-context learning in Large Language Models is driven by token co-occurrence reinforcement, where repeated contextual co-occurrences in demonstration examples strengthen token relationships. This mechanism explains both the beneficial functions and detrimental effects of ICL, including instances where spurious correlations in demonstrations mislead the model.",
    "distributive_fairness": "Large language models are poorly aligned with human distributional fairness preferences in resource allocation decisions across different demographic groups. They struggle to use resources like money to reduce inequality and are sensitive to prompt and template changes, though they perform better when selecting from predefined options.",
    "premise_order_effects": "The order of premises significantly affects the reasoning performance of LLMs, with models performing best when premises are in the ground-truth proof order. Random or permuted orderings can drastically reduce accuracy, and this sensitivity is consistent across different model sizes and architectures.",
    "object_hallucination_pope": "Large vision-language models hallucinate objects severely, often identifying objects not present in images. Objects that frequently appear in training data or co-occur with ground-truth image objects are more prone to hallucination.",
    "cot_in_planning": "Chain-of-thought prompting does not reliably enable large language models to learn generalizable algorithmic reasoning abilities. It relies on highly specific, pattern-matching prompts, and performance degrades with increased problem complexity.",
    "fractal_complexity_of_language": "LLMs deviate from the narrow fractal parameter range characteristic of natural language when factors like decoding temperature and prompting method are adjusted, even if log-perplexity scores remain stable.",
    "mcq_selection_bias": "Modern large language models are not robust in handling multiple choice questions due to a strong selection bias towards certain option IDs. This bias is caused by token-level prior probabilities rather than position-order preference. Debiasing methods that estimate and subtract the option-ID prior can effectively mitigate this issue.",
    "persona_reasoning_biases": "Persona assignment can influence the fundamental reasoning capabilities of an LLM, reducing reasoning performance across diverse tasks.",
    "lost_in_the_middle": "Large Language Model performance is better when relevant information is positioned at the very beginning or end of the input context, and it degrades significantly when the information is located in the middle.",
    "llms_lack_self_correction": "Self-correction methods do not improve large language model performance across math, commonsense reasoning, and multi-hop question answering benchmarks, as accuracies either drop or remain nearly the same.",
    "hallucination_snowballing": "Language model hallucinations propagate and compound over a generation because models often commit to an initial incorrect answer early on and then generate further incorrect explanations. This occurs despite the model's ability to recognize these errors in isolation, leading to a snowballing effect.",
    "fallback_behaviors": "Language models exhibit a consistent ordering of fallback behaviors under uncertainty, shifting from sequence repetitions to degenerate text to hallucinations as they become more advanced. This pattern also appears within single-generation trajectories as uncertainty increases.",
    "lifebench_length_following": "LLMs follow short-length instructions reasonably well but struggle significantly with longer constraints, often failing to reach vendor-claimed maximum output lengths. Long-context LLMs do not reliably improve adherence to length instructions, while reasoning models perform better at following length constraints than specialized long-text generation models.",
    "prompt_formatting_sensitivity": "Widely used open-source large language models are highly sensitive to subtle changes in prompt formatting in few-shot settings, with performance sometimes varying significantly across the accuracy range. This sensitivity is consistent across different model sizes, few-shot examples, and instruction tuning, and format-specific performance correlates weakly across models.",
    "hallucination_awareness": "Large language models are not metacognitively aware of when they are hallucinating or producing unreliable outputs, as they often fail to express internal signals about truthfulness and confidence when generating answers.",
    "activation_control": "Efficiently eliciting long chain-of-thought reasoning in language models is possible through activation-level interventions. By amplifying a small set of high-impact activations in the last few layers and inserting wait tokens, long-form reasoning can be invoked without additional training, enhancing self-reflection rates and accuracy.",
    "llm_confidence_elicitation": "Large language models (LLMs) tend to be overconfident when expressing their uncertainty. Human-inspired prompting strategies can mitigate this overconfidence, though their effectiveness decreases with more advanced models. Sampling strategies combined with specific aggregators can improve failure prediction.",
    "charxiv_chart_understanding": "Multimodal LLMs struggle to accurately understand and reason about real-world scientific charts, achieving less than half accuracy on reasoning questions and performing significantly worse than humans.",
    "space_time_representations": "Large language models learn coherent and grounded representations that reflect real-world spatial and temporal information, as evidenced by their ability to encode geographic coordinates and temporal data through specific neurons.",
    "llm_value_consistency": "Different large language models do not consistently exhibit the same value structure as humans. The consistency of value profiles in LLMs depends on the way the model is prompted, with personality-endowed prompts improving consistency.",
    "uncertainty_in_instruction_following": "Large language models can estimate their uncertainty to some degree when following instructions, but effectiveness varies with task complexity. Verbalized self-evaluation methods are more effective on simpler tasks, while internal model states provide more reliable uncertainty signals across both simple and realistic settings.",
    "llms_assume_rationality": "LLMs struggle to predict or simulate human behavior in a classic risky choice setting, assuming that people make decisions more rationally than we actually do. LLMs also assume people act rationally when reasoning backwards from observed actions to internal utilities, aligning with how humans make inferences about others' choices",
    "agentbench_llm_agents_rq0": "LLMs perform with varying success as agents in code-grounded environments, with commercial models generally outperforming open-source ones. They struggle with complex SQL tasks, often failing due to syntax errors, and show limited ability to navigate and query large knowledge graphs effectively.",
    "agentbench_llm_agents_rq1": "LLMs perform with basic strategic reasoning in digital card games but struggle against complex strategies. They have difficulty with lateral thinking puzzles, often failing to find correct solutions. In household tasks, LLMs show limited ability to complete multi-step tasks.",
    "agentbench_llm_agents_rq2": "LLMs can perform basic shopping tasks in web-grounded environments but struggle with complex queries and show limited ability to navigate complex web environments effectively.",
    "ai_assistants_insecure_code_rq0": "Users write more insecure code when given access to an AI programming assistant, except for tasks involving C string manipulation where the effect was not significant.",
    "ai_assistants_insecure_code_rq1": "Users with AI assistance often overestimate the security of their code.",
    "ai_assistants_insecure_code_rq2": "Users' language and behavior, specifically through effective prompt strategies and parameter adjustments, can improve the security of their code when interacting with an AI assistant across tasks involving encryption, signing, file path handling, SQL operations, and C string manipulation.",
    "alice_in_wonderland_rq0": "State-of-the-art large language models exhibit generalization and reasoning breakdowns when confronted with simple common sense problems like the AIW problem, as evidenced by low correct response rates and strong performance fluctuations across different prompt types.",
    "alice_in_wonderland_rq1": "Control experiments using AIW Light problems indicate that low-level factors such as language parsing and arithmetic operations are not responsible for the observed breakdowns in reasoning and generalization in large language models when tested with AIW Light Arithmetic Siblings datasets.",
    "alice_in_wonderland_rq2": "Standardized benchmarks like MMLU, GSM8k, and ARC-c do not accurately reflect the generalization and reasoning capabilities of state-of-the-art large language models, as they fail to reveal severe function deficits in these models.",
    "bags_of_words_vlm_rq0": "Current Vision-Language Models (CLIP, BLIP, Flava, X-VLM) exhibit significant deficiencies in understanding compositional relationships, attribute binding, and word order in image-caption pairs, often performing at or below chance level on the Attribution, Relation, and Order benchmarks.",
    "bags_of_words_vlm_rq1": "VLMs perform well on retrieval tasks because they rely on shortcut strategies rather than true compositional understanding.",
    "bags_of_words_vlm_rq2": "The selection of challenging negative examples based on compositional structures through composition-aware hard negative mining can enhance Vision-Language Models' ability to understand and process compositional relationships, as evidenced by improved performance on compositional tasks.",
    "bbq_bias_benchmark_rq0": "Current question-answering models (UnifiedQA, RoBERTa, DeBERTaV3) exhibit social biases by often selecting biased answers instead of 'UNKNOWN', indicating reliance on these biases across the nine social dimensions. They show higher accuracy when the correct answer aligns with social biases, suggesting that biases persist even in contexts where the answer is clear.",
    "blink_perception_rq0": "Current multimodal large language models (GPT-4V, Gemini, LLaVA) perform poorly on the Blink benchmark, struggling with visual correspondence, relative depth estimation, and forensic detection tasks compared to human performance.",
    "blink_perception_rq1": "Varying visual prompt attributes, such as circle size and color, significantly affects the performance of multimodal LLMs, with red circles generally yielding better results. Optimal prompt settings vary by task, indicating the importance of robust prompt design for accuracy.",
    "bloomz_crosslingual_multitask_rq0": "Finetuning multilingual language models on tasks in a single language, specifically English, enhances their performance on tasks in other languages.",
    "bloomz_crosslingual_multitask_rq1": "Models finetuned on multilingual datasets with English prompts can generalize to tasks in languages not intentionally seen during pretraining or finetuning.",
    "bloomz_crosslingual_multitask_rq2": "Finetuning on machine-translated prompts improves performance on human-written non-English prompts for both BLOOMZ and mT0 models.",
    "cambrian_visual_encoders_rq0": "Different visual encoder choices impact the multimodal capabilities of MLLMs by allowing language-supervised models to generally outperform others, while self-supervised models like DINOv2 demonstrate competitive performance on vision-centric tasks.",
    "cambrian_visual_encoders_rq1": "Two-stage training with more adapter data improves the performance of MLLMs across all domains.",
    "cambrian_visual_encoders_rq2": "The integration of multiple vision features using aggregation methods, specifically SVA, improves the performance of multimodal large language models (MLLMs) on datasets such as GQA, DocVQA, and ScienceQA, particularly excelling in OCR and Chart tasks.",
    "cambrian_visual_encoders_rq3": "Balanced data ratios improve the performance of MLLMs across benchmarks.",
    "chatbot_arena_human_eval_rq0": "The Chatbot Arena platform achieves diversity and quality in user-generated questions by ensuring the prompts are diverse and effective in distinguishing model strengths.",
    "chatbot_arena_human_eval_rq1": "Chatbot Arena ranks large language models in terms of accuracy and stability using pairwise comparison data through an effective and statistically valid system.",
    "chatbot_arena_human_eval_rq2": "Chatbot Arena ensures the reliability and consistency of evaluations by achieving high agreement rates between crowdsourced votes and expert evaluations.",
    "clip_visual_shortcomings_rq0": "CLIP-based vision encoders struggle with straightforward visual questions, leading to MLLMs like GPT-4V performing below random guessing levels.",
    "clip_visual_shortcomings_rq1": "Integrating vision-only self-supervised learning features with multimodal large language models can improve their visual grounding capabilities.",
    "compositionality_gap_rq0": "The compositionality gap manifests as a roughly constant 40% across different sizes of the GPT-3 family when evaluated on multi-hop question answering tasks.",
    "compositionality_gap_rq1": "Elicitive prompting techniques, specifically self-ask methods, effectively narrow the compositionality gap across datasets like Compositional Celebrities, Bamboogle, 2WikiMultiHopQA, and Musique, with self-ask outperforming chain of thought and direct prompting, particularly on the Bamboogle dataset.",
    "compositionality_gap_rq2": "Integrating external information retrieval capabilities, such as a search engine, improves the performance of language models on compositional question answering tasks.",
    "compound_noun_understanding_rq0": "Current vision-language models like CLIP and OpenCLIP have limited understanding of compound nouns in text-to-image retrieval tasks, as evidenced by their improved performance with the proposed method.",
    "compound_noun_understanding_rq1": "Generating diverse captions using a large language model can improve the understanding of compound nouns by vision-language models in text-to-image retrieval tasks, as evidenced by an 8.25% improvement in CLIP's performance and a 2.35% improvement in OpenCLIP's performance on Compun.",
    "do_anything_now_jailbreaks_rq0": "Jailbreak prompts are characterized by their increasing presence on prompt-aggregation websites, with a significant number of user accounts involved in their creation and dissemination.",
    "do_anything_now_jailbreaks_rq1": "In-the-wild jailbreak prompts are highly effective in bypassing the safeguards of popular LLMs like ChatGPT (GPT-3.5), GPT-4, and PaLM2 across various forbidden scenarios, as evidenced by their high attack success rates (ASR).",
    "do_anything_now_jailbreaks_rq2": "External safeguards, such as the OpenAI moderation endpoint and NeMo-Guardrails, are limited in their effectiveness at reducing the success rate of jailbreak prompts on large language models like ChatGPT (GPT-3.5).",
    "embers_of_autoregression_rq0": "The frequency of tasks in training data affects the performance of large language models by enabling better performance on more common tasks, such as common shift levels like rot-13 and common Pig Latin variants, compared to rarer ones like rot-2 and less common Pig Latin variants.",
    "embers_of_autoregression_rq1": "The probability of the target output affects the performance of large language models like GPT-3.5 and GPT-4 by enabling better performance on tasks when the outputs are high-probability compared to low-probability ones.",
    "embers_of_autoregression_rq2": "Input probability has a moderate effect on encoding accuracy and shows inconsistent effects on counting accuracy for large language models like GPT-3.5 and GPT-4.",
    "emergent_abilities_mirage_rq0": "Emergent abilities in the InstructGPT/GPT-3 model family on arithmetic tasks disappear when nonlinear metrics like Accuracy are replaced with linear metrics like Token Edit Distance.",
    "emergent_abilities_mirage_rq1": "Emergent abilities in the BIG-Bench tasks predominantly appear with specific nonlinear or discontinuous metrics.",
    "emergent_abilities_mirage_rq2": "Emergent abilities can be induced in vision tasks by selecting specific evaluation metrics, supporting the hypothesis that these abilities are not inherent to the model.",
    "evalplus_code_correctness_rq0": "Augmenting existing code evaluation benchmarks like HUMANEVAL with additional test-cases generated by large language models and mutation-based strategies significantly improves the detection of incorrect code, reducing pass@k by up to 19.3-28.9%.",
    "evalplus_code_correctness_rq1": "Test-suite reduction maintains similar evaluation effectiveness on LLM-generated code as the full HUMANEVAL+ benchmark, despite using 47 times fewer test cases.",
    "faith_and_fate_compositionality_rq0": "RQ1: Transformer-based large language models (LLMs) perform poorly on compositional tasks such as multi-digit multiplication, logic grid puzzles, and dynamic programming problems, especially as complexity increases and in out-of-domain scenarios. \n\nRQ2: The underlying mechanisms used by transformer-based LLMs struggle with generalization and complexity, leading to limited performance on compositional tasks.",
    "faith_and_fate_compositionality_rq1": "Transformer LLMs primarily make propagation errors, indicating difficulty in composing multiple reasoning steps, and restoration errors, suggesting a tendency towards memorization rather than reasoning.",
    "freshqa_changing_knowledge_rq0": "Current large language models struggle with fast-changing and false-premise questions on the FRESHQA benchmark, indicating significant room for improvement.",
    "freshqa_changing_knowledge_rq1": "Incorporating search engine results into prompts significantly improves the factual accuracy of large language models, particularly for fast-changing and false-premise questions.",
    "gcg_adversarial_attacks_rq0": "Adversarial suffixes can be generated to induce objectionable content in aligned language models across multiple prompts and models, including Vicuna-7B, Vicuna-13B, and Guanaco-7B, with high success rates.",
    "gcg_adversarial_attacks_rq1": "Adversarial prompts transfer effectively to proprietary black-box models like GPT-3.5, GPT-4, and Claude when optimized on open-source models.",
    "geval_llm_evaluator_rq0": "An AI-based evaluation system, G-EVAL-4, performs better in assessing text summarization quality compared to existing metrics on the SummEval benchmark.",
    "geval_llm_evaluator_rq1": "G-EVAL substantially surpasses all previous state-of-the-art evaluators in terms of correlation with human judgments on the Topical-Chat benchmark.",
    "geval_llm_evaluator_rq2": "G-EVAL-4 performs better than all state-of-the-art evaluators in detecting hallucinations in summarization tasks, particularly on the QAGS-Xsum dataset.",
    "gpt4_code_math_verification_rq0": "Higher code usage frequency improves the mathematical problem-solving capabilities of GPT-4 Code Interpreter on the MATH dataset, particularly for more complex problems.",
    "gpt4_code_math_verification_rq1": "The use of explicit self-verification techniques significantly improves the accuracy of GPT-4's code execution capabilities in solving math problems, particularly on the MATH dataset, and enhances performance across multiple datasets.",
    "gsm_symbolic_rq0": "Current evaluation metrics for mathematical reasoning in large language models are unreliable when using the GSM8K benchmark compared to the GSM-Symbolic benchmark, as evidenced by significant variance and a performance drop on GSM-Symbolic.",
    "gsm_symbolic_rq1": "The fragility of mathematical reasoning in large language models manifests as greater sensitivity to changes in numerical values compared to changes in names.",
    "gsm_symbolic_rq2": "Performance decreases and variance increases as the complexity of mathematical questions, indicated by the number of clauses, increases.",
    "gsm_symbolic_rq3": "Large language models rely on pattern matching rather than accurately discerning relevant information when solving mathematical problems, as evidenced by significant performance drops when irrelevant information is added.",
    "inverse_scaling_rq0": "The potential causes of inverse scaling in large language models include their tendency to correct errors rather than repeat them, increased likelihood of producing memorized sequences, difficulty adapting to redefined symbols, and greater susceptibility to prompt injection attacks.",
    "inverse_scaling_rq1": "Larger models tend to exhibit inverse scaling trends by failing to apply logical reasoning correctly, struggling to break repetitive patterns, failing to identify useful new information, and having difficulty with negation in questions.",
    "irrelevant_context_distraction_rq0": "The presence of irrelevant context decreases the problem-solving accuracy of large language models on arithmetic problems from the GSM-IC dataset.",
    "irrelevant_context_distraction_rq1": "Self-consistency and instructed prompting are strategies that can mitigate the distractibility of large language models when irrelevant context is present in problem descriptions.",
    "jailbroken_safety_failure_modes_rq0": "Competing objectives in safety-trained large language models contribute to their vulnerability to jailbreak attacks by allowing prefix injection to exploit these objectives and provide harmful information, and by enabling refusal suppression to increase the likelihood of unsafe responses by limiting refusal options.",
    "jailbroken_safety_failure_modes_rq1": "Mismatched generalization between pretraining and safety training in large language models leads to vulnerabilities against jailbreak attacks by allowing Base64 encoding and other obfuscation techniques to bypass safety mechanisms.",
    "language_contamination_crosslingual_rq0": "Commonly used English pretraining corpora contain between 300,000 to 406 million tokens of non-English text. The composition includes primarily non-English lines, with some bilingual and translated lines also present.",
    "language_contamination_crosslingual_rq1": "English pretrained models like RoBERTa perform better than BERT on non-English tasks, particularly when fine-tuned, and their cross-lingual transfer capabilities are strongly influenced by the amount of target language data encountered during pretraining.",
    "length_controlled_alpacaeval_rq0": "Length control significantly reduces the gameability of AlpacaEval when models are prompted for verbosity.",
    "length_controlled_alpacaeval_rq1": "Controlling for response length in evaluations using the AlpacaEval dataset improves the Spearman correlation with human evaluation rankings in the LMSYS Chatbot Arena, increasing it from 0.94 to 0.98.",
    "length_controlled_alpacaeval_rq2": "A length-controlled evaluation dataset for chatbot performance demonstrates superior robustness and interpretability compared to other length correction methods, as it shows better correlation with human judgments and improved performance against adversarial inputs.",
    "lets_verify_step_by_step_rq0": "Process supervision significantly outperforms outcome supervision in training reward models for solving problems from the MATH dataset.",
    "lets_verify_step_by_step_rq1": "Active learning improves the data efficiency of process supervision in training reward models for mathematical reasoning tasks by 2.6 times.",
    "lets_verify_step_by_step_rq2": "A large reward model can effectively approximate human supervision for training smaller reward models in mathematical reasoning tasks.",
    "llm_error_finding_rq0": "State-of-the-art LLMs struggle with finding reasoning mistakes in Chain-of-Thought traces, with GPT-4 achieving the highest accuracy among them.",
    "llm_error_finding_rq1": "LLMs can correct reasoning errors in CoT traces when provided with oracle mistake location information, improving downstream task performance across tasks like word sorting, tracking shuffled objects, logical deduction, multi-step arithmetic, and Dyck languages.",
    "llm_error_finding_rq2": "The mistake-finding accuracy of large language models on out-of-domain data from the BIG-Bench Mistake dataset can be improved by using a small classifier trained on this data. The conclusion does not specify the minimum accuracy threshold required for effective backtracking.",
    "llm_judge_position_bias_rq0": "The order of candidate responses significantly affects evaluation outcomes, as LLMs like GPT-4 and ChatGPT show substantial positional bias, leading to high conflict rates when response positions are swapped.",
    "llm_judge_position_bias_rq1": "Calibration strategies like MEC and BPC are effective in mitigating positional bias in large language model evaluators. They significantly enhance alignment with human judgments.",
    "loft_long_context_subsume_rag_rq0": "Long-Context Language Models (LCLMs) perform comparably to specialized models in text, visual, and audio retrieval tasks at a 128k context length but degrade with larger contexts. Gemini 1.5 Pro outperforms CLIP in visual retrieval and performs comparably to PaLM 2 DE in audio retrieval, with notable performance in Hindi.",
    "loft_long_context_subsume_rag_rq1": "Long-Context Language Models (LCLMs) can effectively perform Retrieval-Augmented Generation (RAG) on multi-hop datasets, as they outperform RAG pipelines in these cases. However, they struggle with multi-target datasets.",
    "loft_long_context_subsume_rag_rq2": "Long-Context Language Models (LCLMs) are reasonably capable of performing SQL-like compositional reasoning tasks but are less effective than specialized SQL pipelines.",
    "loft_long_context_subsume_rag_rq3": "Long-Context Language Models (LCLMs) generally perform better in many-shot in-context learning tasks compared to traditional few-shot setups, as they show improved classification accuracy with more examples. However, this improvement may be less pronounced for complex tasks.",
    "longbench_bilingual_context_rq0": "Large language models generally perform better on single-document and multi-document question answering tasks when they are commercial models, compared to open-source ones. However, their performance can significantly decline as the context length increases.",
    "longbench_bilingual_context_rq1": "Large language models perform with varying degrees of success on summarization tasks using LongBench, with some datasets like GovReport, QMSum, MultiNews, and VCSUM proving more challenging than others.",
    "longbench_bilingual_context_rq2": "Large language models exhibit varying performance on few-shot learning tasks using LongBench, with some models demonstrating strong capabilities.",
    "longbench_bilingual_context_rq3": "Large language models exhibit varying performance on synthetic tasks and code completion tasks using LongBench. Some models demonstrate strong capabilities in code completion, while other tasks present significant challenges.",
    "mm_vet_integrated_rq0": "Current large multimodal models show varying effectiveness in integrating core vision-language capabilities across 16 emergent tasks.",
    "mm_vet_integrated_rq1": "GPT-4 performs effectively in assessing open-ended outputs from large multimodal models, showing the closest alignment with human evaluations.",
    "mmbench_comprehensive_rq0": "The benchmark effectively assesses the multi-modal capabilities of vision-language models across 20 ability dimensions using bilingual multiple-choice questions in English and Chinese.",
    "mmbench_comprehensive_rq1": "Using multiple evaluation passes with shuffled choices is more effective in providing robust evaluation results for vision-language models on the MMBench dataset, as it reveals a more significant performance gap between different models compared to traditional evaluation methods.",
    "mmbench_comprehensive_rq2": "LLM-based choice extraction significantly improves the evaluation accuracy of vision-language models on MMBench by aligning predictions with human annotations.",
    "mt_bench_llm_judge_rq0": "GPT-4 aligns well with human preferences in evaluating chatbots, achieving an 85% agreement rate with human experts and a similar agreement level with crowd judges.",
    "mt_bench_llm_judge_rq1": "Large language models as judges exhibit significant position bias, favoring the first position, and verbosity bias, though GPT-4 is more resistant. They also have limitations in grading math and reasoning questions.",
    "multilingual_cot_reasoning_rq0": "Large language models perform well on the Multilingual Grade School Math (MGSM) benchmark, with intermediate reasoning steps enhancing their performance.",
    "multilingual_cot_reasoning_rq1": "Large language models like PaLM-540B perform at state-of-the-art levels on multilingual reasoning benchmarks such as XCOPA and XL-WiC when evaluated using few-shot prompting with multilingual exemplars. However, performance does not improve with chain-of-thought prompting.",
    "nonverbal_abstract_reasoning_rq0": "Open-source multi-modal large language models do not demonstrate faithful nonverbal abstract reasoning abilities on Raven’s Progressive Matrices benchmarks, but closed-source models like GPT-4V show non-trivial abilities.",
    "nonverbal_abstract_reasoning_rq1": "The root causes of poor performance in nonverbal abstract reasoning tasks by MLLMs are their struggles with precise visual details and reasoning.",
    "nonverbal_abstract_reasoning_rq2": "Multimodal large language models (MLLMs) show improved performance on nonverbal abstract reasoning tasks when corrective hints and chain-of-thought (CoT) prompting are used, particularly for closed-source models.",
    "ocrbench_text_understanding_rq0": "Large Multimodal Models perform comparably to state-of-the-art supervised models in recognizing regular, irregular, occluded, and artistic text but struggle with handwritten, Chinese, and non-semantic text.",
    "ocrbench_text_understanding_rq1": "Large Multimodal Models with higher input resolutions perform better in Scene Text-Centric Visual Question Answering tasks, but they still face challenges compared to domain-specific methods.",
    "ocrbench_text_understanding_rq2": "Large Multimodal Models show limited proficiency in Document-Oriented Visual Question Answering tasks.",
    "ocrbench_text_understanding_rq3": "Large Multimodal Models face challenges in Key Information Extraction tasks, particularly when dealing with smaller input resolutions.",
    "ocrbench_text_understanding_rq4": "Large Multimodal Models struggle with recognizing handwritten mathematical expressions using the HME100K dataset due to complex spatial structures and indirect representation.",
    "pal_program_aided_reasoning_rq0": "The use of programmatic reasoning steps with a Python interpreter significantly improves the accuracy of large language models on mathematical reasoning tasks, achieving state-of-the-art accuracy and surpassing other models by 15% top-1 accuracy on datasets such as GSM8K, SVAMP, ASDIV, and MAWPS.",
    "pal_program_aided_reasoning_rq1": "Language models that utilize external program execution achieve higher solve rates than those using step-by-step reasoning prompts in symbolic reasoning tasks such as COLORED OBJECTS, PENGUINS, and DATE.",
    "pal_program_aided_reasoning_rq2": "A program-aided language model (PAL) performs significantly better on algorithmic reasoning tasks such as OBJECT COUNTING and REPEAT COPY compared to chain-of-thought prompting.",
    "parametric_vs_nonparametric_memory_rq0": "Larger language models memorize more popular factual knowledge more effectively, but they have difficulty with less popular knowledge.",
    "parametric_vs_nonparametric_memory_rq1": "Retrieval augmentation significantly improves the performance of large language models on long-tail factual knowledge.",
    "parametric_vs_nonparametric_memory_rq2": "Adaptively combining non-parametric and parametric memories based on entity popularity improves performance and reduces inference costs, particularly for larger language models.",
    "perception_test_video_rq0": "Pre-trained multimodal models perform below human baseline and frequency-based dummy baseline on the Perception Test across different skill areas and reasoning types using real-world videos.",
    "prismatic_vlm_design_rq0": "Single-stage training improves the performance of visually-conditioned language models (VLMs) across visual question answering, object localization, and challenge tasks, while also reducing compute cost compared to multi-stage training.",
    "prismatic_vlm_design_rq1": "Fused DINOv2 and SigLIP backbones with naive image resizing enhance the performance of VLMs on visual question answering, object localization, and challenge tasks.",
    "prismatic_vlm_design_rq2": "Base language models match or exceed the performance of instruct-tuned language models on vision-language tasks, with co-training on language-only data being important for safety.",
    "prismatic_vlm_design_rq3": "Increasing data diversity and extending training time significantly enhance the performance of VLMs.",
    "react_reasoning_acting_rq0": "Integrating reasoning and acting within a single framework, as demonstrated by ReAct, performs competitively on knowledge-intensive reasoning tasks, specifically multi-hop question answering and fact verification. ReAct outperforms both CoT and Act-only methods, highlighting the importance of external knowledge retrieval.",
    "react_reasoning_acting_rq1": "Performance on interactive decision-making tasks, such as ALFWorld and WebShop, varies with ReAct significantly outperforming Act-only and imitation learning methods in terms of Success Rate and Score.",
    "red_teaming_reduce_harms_rq0": "Scaling behaviors make RLHF models harder to red team, whereas other models exhibit a flat trend in efficacy across different sizes and types.",
    "red_teaming_reduce_harms_rq1": "Red teaming uncovers harmful outputs such as offensive language, misinformation, and solicitation of harmful activities.",
    "red_teaming_reduce_harms_rq2": "A dataset of red team attacks can improve the safety of language models by helping to understand model vulnerabilities and develop automated red teaming techniques.",
    "reversal_curse_rq0": "Auto-regressive language models trained on synthetic facts do not generalize to the reverse form, as they show near 0% accuracy.",
    "reversal_curse_rq1": "The Reversal Curse affects GPT-4's ability to accurately identify parent-child relationships, as it is more accurate at identifying parents than children.",
    "reversal_curse_rq2": "Auto-regressive language models fail to generalize from question-answer instructions presented in one order to the reverse order.",
    "rgb_rag_benchmark_rq0": "Large language models demonstrate strong robustness to noise in retrieval-augmented generation, but their accuracy significantly decreases as the noise ratio increases.",
    "rgb_rag_benchmark_rq1": "Large language models struggle to effectively reject questions when required knowledge is absent, often generating incorrect answers instead.",
    "rgb_rag_benchmark_rq2": "Large language models struggle with integrating information from multiple documents in retrieval-augmented generation, particularly when noise is present, resulting in lower accuracy.",
    "rgb_rag_benchmark_rq3": "Large language models like ChatGPT and Qwen-7B-Chat struggle to identify and correct factual errors in retrieved documents, even when given warnings, in both English and Chinese.",
    "self_rag_adaptive_retrieval_rq0": "Retrieval and self-reflection mechanisms enhance the factual accuracy and generation quality of large language models by enabling SELF-RAG to outperform baseline models in these areas.",
    "seven_failure_points_rag_rq0": "The failure points in engineering a Retrieval Augmented Generation (RAG) system using the BioASQ dataset include missing content, missed top-ranked documents, and incorrect specificity.",
    "seven_failure_points_rag_rq1": "Key considerations for software engineers implementing Retrieval Augmented Generation (RAG) systems across diverse domains include chunking strategies, embedding choices, and continuous calibration.",
    "survey_response_biases_rq0": "Large language models (LLMs) do not generally exhibit human-like response biases, such as acquiescence, allow/forbid asymmetry, response order, opinion floating, and odd/even scale effects, when evaluated on survey questions derived from Pew Research's American Trends Panel.",
    "survey_response_biases_rq1": "Large language models (LLMs) exhibit significant changes in their responses to non-bias perturbations, such as typos, letter swaps, and middle randomization, in survey questions.",
    "swe_bench_github_issues_rq0": "State-of-the-art language models perform poorly in resolving software engineering issues from real-world GitHub repositories using the SWE-bench framework, with the best model resolving only 1.96% of issues.",
    "swe_bench_github_issues_rq1": "SWE-bench is characterized by its diverse tasks, large codebases, and complex dependencies. A challenge is maintaining its robustness while allowing for continuous updates with new task instances.",
    "sycophancy_in_llms_rq0": "AI assistants exhibit sycophancy by providing more positive feedback that aligns with user preferences across varied free-form text-generation tasks.",
    "sycophancy_in_llms_rq1": "AI assistants often change their correct answers to incorrect ones when challenged by users across multiple QA datasets.",
    "sycophancy_in_llms_rq2": "AI assistants modify their responses to align with user beliefs, and this alignment with user-suggested incorrect answers reduces their accuracy in open-ended question-answering tasks.",
    "sycophancy_in_llms_rq3": "AI assistants often mimic user mistakes in attributing authorship of poems.",
    "tokenization_cost_disparity_rq0": "Tokenization lengths differ significantly across languages, with some requiring more tokens than English. Tokenizers targeting specific languages show better parity but still have disparities. Multilingual models improve parity but do not achieve uniformity, and byte-level models also exhibit significant disparities for some language pairs.",
    "tokenization_cost_disparity_rq1": "Languages with higher tokenization premiums incur higher costs, experience longer processing times, and have reduced long context processing capabilities.",
    "toolformer_self_taught_tools_rq0": "A language model like Toolformer can autonomously learn to use a variety of external tools, such as a calculator, a Q&A system, a translation system, and a calendar, to improve zero-shot performance on downstream tasks. However, its performance varies with different tools and does not consistently surpass all models, such as GPT-3, particularly in search engine interactions.",
    "toolformer_self_taught_tools_rq1": "The self-supervised learning of tool use does not affect the core language modeling abilities of the language model, as Toolformer maintains language modeling performance without increasing perplexity.",
    "truthfulqa_mimicking_falsehoods_rq0": "Current language models, specifically GPT-3-175B with a helpful prompt, are truthful on 58% of questions across 38 categories in a zero-shot setting.",
    "truthfulqa_mimicking_falsehoods_rq1": "Larger model sizes generally decrease truthfulness, with the largest models producing more imitative falsehoods on the TruthfulQA benchmark.",
    "truthfulqa_mimicking_falsehoods_rq2": "Automated metrics like GPT-judge can effectively predict human evaluations of truthfulness in language models, achieving 90-96% accuracy.",
    "v_star_visual_search_rq0": "The integration of the V∗ visual search mechanism improves the accuracy of multimodal large language models on attribute recognition and spatial relationship reasoning tasks.",
    "v_star_visual_search_rq1": "The visual search algorithm V∗ significantly reduces search length compared to random and sequential search strategies.",
    "v_star_visual_search_rq2": "The integration of a visual search mechanism in the SEAL framework maintains its general multimodal capabilities while improving visual search performance.",
    "visual_instruction_tuning_rq0": "The use of GPT-4 generated multimodal instruction-following data is effective in training large multimodal models like LLaVA, as evidenced by LLaVA achieving an 85.1% relative score compared with GPT-4 on a synthetic dataset designed to test multimodal instruction-following capabilities.",
    "visual_instruction_tuning_rq1": "LLaVA, when fine-tuned on a dataset of science questions requiring reasoning across text and images, achieves a state-of-the-art accuracy of 92.53% in multimodal reasoning when combined with GPT-4.",
    "webarena_web_agents_rq0": "WebArena is effective in providing a realistic and reproducible setting for tasks across the domains of e-commerce, social forums, collaborative development, and content management.",
    "webarena_web_agents_rq1": "RQ2a: Baseline large language models, including GPT-4, perform with limited success rates on the WebArena benchmark tasks. \n\nRQ2b: Current large language models face limitations in executing complex tasks, particularly in few-shot in-context learning with and without explicit reasoning steps.",
    "webarena_web_agents_rq2": "The key challenges in developing robust autonomous agents for complex web-based tasks in WebArena are early stopping, observation bias, and failure in observation interpretation.",
    "winoground_compositionality_rq0": "State-of-the-art vision and language models generally perform close to or below random chance on the Winoground task, indicating poor visio-linguistic compositional reasoning capabilities.",
    "winoground_compositionality_rq1": "Models perform poorly on the Winoground task across all categories, indicating significant areas for improvement in model design, particularly concerning linguistic and visual tags.",
}


def get_latest_log_file(base_directory):
    """
    Finds the most recently modified folder under the given base directory
    and returns the full path to the 'log.log' file inside it.

    Parameters:
        base_directory (str): The path to the directory containing log folders.

    Returns:
        str or None: Full path to 'log.log' in the latest folder, or None if not found.
    """
    # Get list of subdirectories with their modification times
    try:
        subdirs = [
            os.path.join(base_directory, d)
            for d in os.listdir(base_directory)
            if os.path.isdir(os.path.join(base_directory, d))
        ]
    except FileNotFoundError:
        print(f"Directory not found: {base_directory}")
        return None

    if not subdirs:
        print("No subdirectories found.")
        return None

    # Sort subdirectories by last modified time, descending
    latest_subdir = max(subdirs, key=os.path.getmtime)

    # Construct the path to log.log inside the latest directory
    log_file_path = os.path.join(latest_subdir, "log.log")

    if os.path.isfile(log_file_path):
        return log_file_path
    else:
        print(f"'log.log' not found in {latest_subdir}")
        return None


def read_log_metadata(log_file_path):
    """
    Reads the agent_id, task_id, and llm_model from the top of the given log file.
    Returns a dictionary with those values.
    """
    metadata = {}
    with open(log_file_path, "r") as f:
        for line in range(3):
            entry = f.readline()
            if not entry:
                break
            key, value = entry.strip().split(":", 1)
            metadata[key.strip()] = value.strip()
    return metadata
    

def extract_json_from_markdown(response: str) -> str:
    if response and response.strip().startswith('```') and '```' in response:
        code_content = response.split('```', 2)[1]
        if code_content.startswith('json'):
            code_content = code_content[4:].strip()
        response = code_content.strip()
    return response


def parse_json_response(response: str, default_value: Any = None) -> Any:
    if not response:
        return default_value
    
    response = extract_json_from_markdown(response)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"\nWarning: Failed to parse JSON response: {e}")
        print(f"Response was: {response[:100]}..." if len(response) > 100 else f"Response was: {response}")
        return default_value


def parse_gpt_response(response: str, expected_fields: List[str] = None, field_defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    if field_defaults is None:
        field_defaults = {}
    
    result = parse_json_response(response, {})
    
    if not expected_fields:
        return result
    
    output = {}
    for field in expected_fields:
        output[field] = result.get(field, field_defaults.get(field))
    
    return output


def parse_nested_json_response(response: str) -> Tuple[Dict[str, Any], bool]:
    extracted = extract_json_from_markdown(response)
    
    try:
        result = json.loads(extracted)
        
        if isinstance(result, dict) and len(result) == 1 and next(iter(result.values())).startswith('{'):
            key = next(iter(result.keys()))
            try:
                nested_json = json.loads(result[key])
                return nested_json, True
            except json.JSONDecodeError:
                pass
        
        return result, True
    except json.JSONDecodeError as e:
        print(f"\nWarning: Failed to parse JSON response: {e}")
        return {}, False


def extract_core_idea(conclusion, client, eval_model):
    response = client.chat.completions.create(
        model=eval_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert summarizer. "
                    "Given a conclusion, your task is to extract only the core insight or main idea, "
                    "omitting all concrete values, specific numbers, background details, methods, "
                    "file names, or references to artifacts. "
                    "Focus on general trends or main conclusions/findings, and express them in a "
                    "generalized way without referring to any precise data or background context. "
                    "DO NOT infer any detail, context information, or background knowledge that is not mentioned "
                    "in the original conclusion."
                ),
            },
            {"role": "user", "content": f"Input: {conclusion}"}
        ]
    )
    return response.choices[0].message.content


import re
import json

def extract_single_final_thought(log_path):
    final_thought = ""
    paper = ""

    # Regex for OpenHands logs
    import re

    openhands_pattern = re.compile(
        r"final_thought\s*=\s*(?:'|\")(.+?)(?:'|\"),\s*outputs=",
        re.DOTALL
    )

    # Timestamp pattern for Codex-like logs (e.g., [2025-09-19T10:05:41])
    codex_timestamp_pattern = re.compile(r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\]")

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

        extracted = None

        # --- 1. OpenHands format (last occurrence) ---
        matches = openhands_pattern.findall(content)
        if matches:
            extracted = matches[-1].encode("utf-8").decode("unicode_escape").strip()
            print(extracted)

        # --- 2. Codex format (between third-last and second-last timestamp) ---
        if extracted is None:
            timestamps = list(codex_timestamp_pattern.finditer(content))
            if len(timestamps) >= 3:
                start = timestamps[-3].start()
                end = timestamps[-1].start()
                extracted = content[start:end].strip()

        # --- 3. Claude format (JSON in last line) ---
        if extracted is None:
            last_line = content.strip().splitlines()[-1]
            try:
                parsed = json.loads(last_line)
                if isinstance(parsed, dict) and "result" in parsed:
                    extracted = parsed["result"].strip()
            except json.JSONDecodeError:
                pass

    except Exception as e:
        print(f"Error reading file: {e}")

    return extracted