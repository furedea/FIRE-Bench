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
    "llms_assume_rationality":"Do large language models accurately capture the irrational aspects of human decision-making, or do they instead assume that people behave according to rational choice theories (such as expected value theory)?",
    "to_cot_or_not_to_cot" :"How much performance improvement does Chain-of-Thought (CoT) prompting provide over Direct Answer prompting across different reasoning categories (Commonsense, Knowledge, Symbolic, Mathematical, Soft Reasoning), and which categories show statistically signficant gains?",
    "uncertainty_in_instruction_following":"How effectively can large language models (LLMs) estimate their uncertainty when following user instructions, and how can this ability be systematically evaluated in a controlled setting?",
    "fractal_complexity_of_language":"When and why do LLMs deviate from the narrow fractal parameter range characteristic of natural language, as visualized by Holder and Hurst exponents?",
    "llm_value_consistency":"Do large language models exhibit the same value structure as humans, including the ranking of values and the correlations between values, and how does this depend on the way the model is prompted?",
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
    "reversal_curse": "If an LLM is trained on statements of the form 'A is B,' can it automatically generalize to answer questions requiring the reverse relationship 'B is A'?",
    "llm_judge_position_bias": "When LLMs are used as evaluators to compare two candidate responses, does the order in which responses are presented systematically bias the evaluation outcome?",
    "sycophancy_in_llms": "Do state-of-the-art AI assistants exhibit sycophantic behavior by tailoring responses to match user beliefs rather than being truthful, and what drives this behavior?",
    "llm_reliability_scaling": "As language models are scaled up in size and shaped through instruction tuning and RLHF, do they become more reliable in correctly answering questions or avoiding errors?",
    "gsm_symbolic": "Do LLMs perform genuine mathematical reasoning, or are they relying on pattern matching, and how robust is their performance to superficial changes in math problems?",
    "irrelevant_context_distraction": "How does the inclusion of irrelevant information in problem descriptions affect LLM accuracy on arithmetic reasoning tasks?",
    "inverse_scaling": "Are there tasks where larger language models perform worse than smaller ones, exhibiting inverse scaling?",
    "embers_of_autoregression": "Do LLMs show systematic performance differences based on the probability of the input, output, or task being performed, even in deterministic settings where probability should be irrelevant?",
    "llm_error_finding": "Is the poor self-correction performance of LLMs due to an inability to find mistakes, an inability to correct them, or both?",
    "cognitive_biases_in_llms": "Do LLMs exhibit human-like cognitive biases and intuitive reasoning errors, and how does this change with model scale and instruction tuning?",
    "survey_response_biases": "Do LLMs exhibit the same response biases as humans when presented with survey questionnaires known to trigger specific biases in human respondents?",
    "mt_bench_llm_judge": "How well do LLM judges agree with human preferences when evaluating model outputs, and what systematic biases do they exhibit?",
    "alice_in_wonderland": "Can state-of-the-art LLMs solve simple, short common-sense reasoning problems that are trivially easy for humans?",
    "multilingual_cot_reasoning": "Can language models perform chain-of-thought reasoning effectively across diverse languages, including underrepresented ones, and how does this ability scale with model size?",
    "content_effects_on_reasoning": "Do LLMs, like humans, allow semantic content to influence their performance on logical reasoning tasks, performing better when content aligns with real-world knowledge?",
    "bbq_bias_benchmark": "Do NLP models rely on social stereotypes when answering questions, and does providing sufficient context eliminate this bias?",
    "compositionality_gap": "Can language models compose multiple facts to answer multi-hop questions, and does the compositionality gap decrease with scale?",
    "faith_and_fate_compositionality": "Can transformer-based LLMs develop systematic problem-solving skills for compositional tasks, or do they rely on pattern matching from training data?",
    "llm_alternative_human_eval": "When LLMs are given the exact same evaluation instructions, samples, and questions used in human evaluation studies, do their assessments align with human expert judgments?",
    "emergent_abilities_mirage": "Are the sharp, unpredictable emergent abilities observed in large language models a genuine property of scaling, or an artifact of how researchers measure performance?",
    "clip_visual_shortcomings": "Do multimodal LLMs that rely on CLIP visual encoders inherit systematic visual shortcomings, and are there image pairs that these models consistently fail to distinguish?",
    "object_hallucination_pope": "How severely do large vision-language models hallucinate objects not present in images, and what properties of objects make them more prone to hallucination?",
    "winoground_compositionality": "Can state-of-the-art vision-language models correctly match images to captions that contain identical words in different orders, testing genuine compositional understanding?",
    "vlms_are_blind": "Can state-of-the-art VLMs perform trivially simple visual tasks like counting circles, detecting line intersections, or identifying which letter is circled in a word?",
    "blink_perception": "Can multimodal LLMs perform core visual perception tasks that humans find trivial but that resist mediation through natural language descriptions?",
    "bags_of_words_vlm": "Do vision-language models like CLIP actually understand word order, attribute binding, and relational structure in captions, or do they effectively ignore compositional structure?",
    "sugarcrepe_compositionality": "Are existing compositionality benchmarks for VLMs actually measuring compositional understanding, or can they be solved through superficial biases without looking at images?",
    "nonverbal_abstract_reasoning": "Can multimodal LLMs perform nonverbal abstract reasoning on Raven's Progressive Matrices, a classic test of fluid intelligence requiring no language?",
    "charxiv_chart_understanding": "Can multimodal LLMs accurately understand and reason about real-world scientific charts, as opposed to the simplified template charts used in existing benchmarks?",
    "mathvista_visual_math": "How well can foundation models reason mathematically when problems are presented visually through charts, geometry diagrams, function plots, and tables?",
    "hallusionbench_illusion": "How do LVLMs handle visual illusions and manipulated images -- do they analyze the actual image or fall back on parametric knowledge from training?",
    "mm_vet_integrated": "How well can large multimodal models integrate multiple vision-language capabilities simultaneously to solve complex real-world tasks?",
    "ocrbench_text_understanding": "How well do large multimodal models handle OCR-related tasks, and do they rely on genuine character-level recognition or on semantic word guessing?",
    "mmbench_comprehensive": "How do multimodal models compare across fine-grained abilities when evaluated with a bias-resistant methodology that eliminates selection shortcuts?",
    "compound_noun_understanding": "Can vision-language models correctly interpret compound nouns where the compound meaning differs from constituent nouns (e.g., 'butterfly knife' vs. 'butterfly' + 'knife')?",
    "cambrian_visual_encoders": "How do different visual encoder choices and combinations affect multimodal LLM performance, and is the standard single CLIP encoder approach optimal?",
    "prismatic_vlm_design": "Which design decisions in VLM construction (visual encoder, LLM backbone, training recipe) most impact performance, and can principled choices yield better models with less compute?",
    "visual_instruction_tuning": "Can a simple architecture connecting a frozen vision encoder to an LLM, trained on GPT-4-generated instruction-following data, achieve competitive multimodal chat capabilities?",
    "perception_test_video": "Can multimodal video models perceive and reason about temporal dynamics, physics, and object persistence in real-world videos at human-like levels?",
    "v_star_visual_search": "Do current multimodal LLMs lack an active visual search mechanism, and does this hinder their ability to find and focus on important details in high-resolution or visually cluttered images?",
    # --- Code Generation ---
    "evalplus_code_correctness": "Are LLM-generated code solutions that pass existing unit tests truly correct, and how much does augmenting test suites reveal hidden bugs?",
    "ai_assistants_insecure_code": "Do users write more insecure code when assisted by AI code generation tools compared to writing code without AI assistance?",
    "swe_bench_github_issues": "Can language models autonomously resolve real-world GitHub issues given a codebase and issue description?",
    "pal_program_aided_reasoning": "Does offloading computational steps to a Python interpreter via program-aided language models improve accuracy on mathematical and symbolic reasoning tasks compared to chain-of-thought prompting?",
    # --- RAG ---
    "parametric_vs_nonparametric_memory": "When should language models rely on their parametric memory versus retrieving external knowledge, and how does entity popularity affect this tradeoff?",
    "rgb_rag_benchmark": "How robust are LLMs in retrieval-augmented generation when retrieved documents contain noise, are counterfactual, or when the required information is absent from the retrieved context?",
    "self_rag_adaptive_retrieval": "Can a language model learn to adaptively retrieve passages, generate text, and critique its own output through self-reflection tokens, improving factuality without sacrificing versatility?",
    "seven_failure_points_rag": "What are the common failure points in naive RAG pipelines, and at which stages do retrieval-augmented generation systems most frequently fail?",
    # --- Agents / Tool Use ---
    "toolformer_self_taught_tools": "Can language models autonomously learn when and how to call external tools (calculators, search engines, translators) by self-generating API call annotations from a few examples?",
    "agentbench_llm_agents": "How well do LLMs perform as autonomous agents across diverse interactive environments such as operating systems, databases, web browsing, and games?",
    "webarena_web_agents": "Can current LLM-based autonomous agents complete complex tasks on realistic, self-hosted websites at human-level performance?",
    "react_reasoning_acting": "Does interleaving reasoning traces with task-specific actions improve LLM performance on knowledge-intensive QA and interactive decision-making tasks compared to reasoning-only or acting-only approaches?",
    # --- Safety / Alignment ---
    "gcg_adversarial_attacks": "Can automated optimization find universal adversarial suffixes that cause aligned LLMs to produce harmful content, and do such suffixes transfer across different models?",
    "jailbroken_safety_failure_modes": "Why does LLM safety training fail, and what are the fundamental failure modes that allow jailbreak attacks to succeed?",
    "do_anything_now_jailbreaks": "What types of jailbreak prompts are used against LLMs in the wild, how effective are they, and how have they evolved over time?",
    "red_teaming_reduce_harms": "How effective is red teaming at finding harmful outputs from language models, and what factors influence the discovery of harms?",
    # --- Long Context ---
    "longbench_bilingual_context": "How well do long-context language models perform across diverse tasks requiring understanding of long documents, and where do they fail?",
    "loft_long_context_subsume_rag": "Can long-context language models with sufficient context windows replace traditional retrieval, RAG, and SQL pipelines by simply placing all data in the context?",
    # --- Knowledge / Factuality ---
    "truthfulqa_mimicking_falsehoods": "Do large language models generate truthful answers, or do they reproduce common misconceptions and falsehoods from their training data?",
    "lm_self_knowledge_calibration": "Do language models know what they know — can they accurately predict which questions they will answer correctly versus incorrectly?",
    "freshqa_changing_knowledge": "How well do LLMs handle questions requiring fast-changing world knowledge or questions with false premises, and can search engine augmentation help?",
    # --- Structured Reasoning ---
    "lets_verify_step_by_step": "Is process-based supervision (rewarding each correct reasoning step) more effective than outcome-based supervision (rewarding only the final answer) for training reliable math reasoning models?",
    "gpt4_code_math_verification": "Can GPT-4's code interpreter, combined with code-based self-verification, substantially improve performance on challenging mathematical reasoning benchmarks?",
    # --- Multilingual ---
    "bloomz_crosslingual_multitask": "Does multitask finetuning on English-only task data enable a multilingual pretrained model to generalize to tasks in other languages it was not finetuned on?",
    "language_contamination_crosslingual": "Are the surprising cross-lingual abilities of English-centric models explained by genuine linguistic generalization, or by target-language contamination in pretraining data?",
    "tokenization_cost_disparity": "Do multilingual LLM tokenizers treat all languages equally in terms of token count, or do non-English languages require significantly more tokens to represent equivalent text?",
    # --- Text Generation / Evaluation ---
    "geval_llm_evaluator": "Can LLM-based evaluation with chain-of-thought and form-filling achieve higher correlation with human judgments than traditional automatic metrics for text generation quality?",
    "chatbot_arena_human_eval": "Does pairwise human preference voting in an open platform produce reliable and stable LLM rankings, and how do these rankings compare to automatic benchmarks?",
    "length_controlled_alpacaeval": "Does controlling for output length in LLM evaluation significantly change model rankings, and how much does verbosity bias inflate scores in standard evaluations?",
}


gt = {
    "llm_racial_bias_in_medicine": "Yes, LLMs predict higher medical costs and longer hospital stays disproportionately for certain racial groups. Assessment and plans created by the model showed significant association between demographic attributes and recommendations for more expensive procedures, projected hospitalization durations, as well as differences in patient perception.",
    "lost_in_the_middle": "Models are better at using relevant information that occurs at the very beginning or end of its input context, and performance degrades significantly when models must access and use information located in the middle of its input context.",
    "llms_lack_self_correction": "After self-correction, the accuracies of all models drop or remain nearly the same across all three benchmarks. Models frequently change correct answers to incorrect ones during the revision step, showing they cannot reliably self-correct reasoning without external feedback.",
    "awareness_detection": "Language models can distinguish evaluation from real-world transcripts with significant accuracy, demonstrating that frontier LLMs possess evaluation awareness capability even without being explicitly trained for the task.",
    "cot_faithfulness_gaps": "Reasoning models rarely verbalize when they are using hints in their reasoning. CoTs do not faithfully reflect the internal reasoning that led to the model’s final answer.",
    "cot_without_prompting": "Yes, large language models already contain latent CoT reasoning paths that can be surfaced without any prompting, and doing so improves answer accuracy. Altering the decoding process to explore alternative token sequences reveals hidden reasoning trajectories, and selecting the path with the highest answer confidence substantially outperforms standard greedy decoding.",
    "to_cot_or_not_to_cot": "Chain-of-Thought achieves performance gain on math and formal logic. CoT does not achieve statistically significant performance gain, sometimes even producing slight loss, on most other task categories including commonsense, knowledge, and soft reasoning.",
    "llms_assume_rationality": "LLMs struggle to predict or simulate human behavior in a classic risky choice setting, assuming that people make decisions more rationally than we actually do. LLMs also assume people act rationally when reasoning backwards from observed actions to internal utilities, aligning with how humans make inferences about others' choices",
    "uncertainty_in_instruction_following": "LLMs can estimate their uncertainty to some degree when following instructions, but effectiveness varies sharply with task complexity. Verbalized self-evaluation methods outperform logit-based approaches on simpler tasks, while internal model states provide more reliable uncertainty signals across both simple and realistic settings. All methods struggle substantially with more complex tasks.",
    "fractal_complexity_of_language": "Various strategies, such as the decoding temperature and prompting method, can impact fractal parameters even when log-perplexity scores seem to be unaffected. For pretrained models, larger architectures are more effective at capturing such fractal properties. With instruction-tuned models, the similarity to human language does not improve monotonically as the amount of contextual information in the prompt increases. The Hurst parameter emerged as a strong predictor of quality in generated texts, among other significant findings.",
    "llm_value_consistency": "Using the Basic prompt, LLM's answers show variance across different generated personas, and show internally consistent outputs. These results suggest that LLMs cannot be treated as individuals holding a coherent set of value priorities. Prompts that endow the LLM with a personality improved the consistency of each specific value profile. However, with targeted prompt, LLM can be guided to display corresponding persona.",
    "hallucination_snowballing": "LMs often commit to an initial answer within the first token and then produce further incorrect explanatory claims that the model can separately recognize as wrong. When presented with incorrect explanations in isolation, models frequently identify the mistakes, showing they possess the knowledge but over-commit to early hallucinations. This snowballing phenomenon persists under higher temperature sampling, beam search, and zero-shot chain-of-thought prompting.",
    "counterfactual_simulatability": "LLM explanations exhibit low counterfactual simulatability: they fail to enable accurate prediction of the model's behavior on diverse counterfactual inputs. Explanation precision does not correlate with plausibility, implying that optimizing for human approval via RLHF may not ensure faithful or informative explanations.",
    "premise_order_effects": "LLM reasoning is highly sensitive to the ordering of premises. Models perform best when premises are arranged to match the ground-truth proof order, and random or permuted orderings can drastically reduce accuracy. This sensitivity persists across model sizes and architectures.",
    "persona_reasoning_biases": "Persona assignment surfaces implicit reasoning biases and can substantially reduce reasoning performance across diverse tasks. ChatGPT-3.5 showed pervasive persona-induced bias affecting the majority of personas, while GPT-4-Turbo exhibited less but still problematic bias across a substantial fraction of personas. Simple de-biasing prompts had minimal effect.",
    "mcq_selection_bias": "Modern LLMs exhibit a strong selection bias in MCQs, preferring certain option IDs (e.g., A) due to token-level prior probabilities rather than position-order preference. Accuracy shifts dramatically when the correct answer's option position is moved. Debiasing methods that estimate and subtract the option-ID prior can effectively mitigate this bias.",
    "prompt_formatting_sensitivity": "Small changes in prompt formatting can cause very large performance swings in few-shot settings, sometimes spanning the majority of the accuracy range on models like LLaMA-2-13B. Sensitivity persists across larger model sizes, more few-shot examples, and instruction tuning. Format-specific performance correlates only weakly across models, so comparing models using a single arbitrary prompt format is unreliable.",
    "space_time_representations": "LLMs learn linear representations of space and time across multiple scales. These spatial and temporal embeddings are robust to prompting variations and unified across entity types. Individual space neurons and time neurons can be identified that encode geographic coordinates and temporal information.",
    "llm_confidence_elicitation": "LLMs tend to be overconfident when verbalizing their confidence, potentially imitating human patterns of expressing confidence. Both calibration and failure prediction improve with model capability but remain far from ideal. Human-inspired prompting strategies mitigate overconfidence with diminishing returns for advanced models. Sampling strategies paired with specific aggregators can enhance failure prediction.",
    "icl_from_repetition": "In-context learning is substantially driven by token co-occurrence reinforcement: repeated contextual co-occurrences in the demonstration examples strengthen token relationships and drive ICL behavior. This surface repetition mechanism explains both the beneficial functions and detrimental effects of ICL, including cases where spurious correlations in demonstrations mislead the model.",
    "introspective_learning": "LLMs can exhibit a form of introspection: a model predicts its own behavior in hypothetical scenarios more accurately than a different model trained on the same ground-truth behavioral data. This privileged self-prediction holds on simple tasks and survives intentional modifications to ground-truth behavior, but fails to generalize to more complex or out-of-distribution tasks.",
    "fallback_behaviors": "Language models exhibit a consistent ordering of fallback behaviors under uncertainty: as models become more advanced, they shift from sequence repetitions to degenerate text to hallucinations. The same ordering appears within single-generation trajectories as uncertainty increases. Common decoding strategies like random sampling reduce obvious failures such as repetitions but increase harder-to-detect hallucinations.",
    "cot_in_planning": "Chain-of-thought prompting does not reliably enable generalizable algorithmic reasoning in planning tasks. Performance depends heavily on prompt specificity and degrades when problem complexity increases beyond patterns seen in demonstrations. CoT provides superficial benefits from pattern matching rather than true algorithmic understanding.",
    "seca_hallucination": "Semantically equivalent and coherent adversarial prompt perturbations can reliably elicit hallucinations in both open-source and commercial LLMs. SECA achieves higher attack success rates while maintaining semantic equivalence and coherence constraints, highlighting the sensitivity of LLMs to plausible prompt variations even when meaning is preserved.",
    "distributive_fairness": "LLMs are poorly aligned with human distributional fairness preferences. They struggle to use transferable resources like money to reduce inequality, are sensitive to prompt and template changes, but perform better when selecting from predefined menus rather than generating allocations freely.",
    "lifebench_length_following": "Most models follow short-length instructions reasonably but deteriorate sharply beyond a certain threshold. Almost all models fail to reach vendor-claimed maximum output lengths in practice. Long-context LLMs do not reliably improve length-instruction following despite extended input-output windows. Reasoning models outperform even specialized long-text generation models at length following.",
    "hallucination_awareness": "LLMs carry internal signals about truthfulness and confidence, but often fail to express that knowledge when generating answers. Metacognitive signals have limited resolution, emerge contextually, differ across models, and detectors often fail to generalize. Models may encode correct answers internally yet still output incorrect ones.",
    "questbench": "LLMs struggle to identify the single minimal clarification question needed to solve underspecified reasoning problems. Performance varies substantially across algebra, logic, and planning tasks, and degrades as problem complexity increases. Models often fail to recognize what information is missing to disambiguate the problem.",
    "persona_with_catch": "Increasing the amount of LLM-generated persona content systematically worsens population-level simulation fidelity. While richer persona descriptions may appear more detailed, they introduce artifacts and biases that reduce the accuracy of simulating real-world population distributions in opinion surveys and election predictions.",
    "activation_control": "A small set of high-impact activations in the last few layers of LLMs largely governs long-form CoT attributes such as output length and self-reflection. Amplifying these activations and inserting wait tokens can invoke long CoT reasoning without training, significantly increasing self-reflection rates and accuracy. Activation dynamics follow predictable trajectories with a sharp rise after special tokens and exponential decay.",
    "reversal_curse": "LLMs trained on 'A is B' fail to generalize to 'B is A.' When finetuned on fictitious directional facts, models cannot answer the reverse query. The likelihood of the correct answer is no higher than for a random name. Testing GPT-4 on real celebrity-parent pairs showed the same asymmetry across a large set of pairs.",
    "llm_judge_position_bias": "LLMs exhibit strong position bias when used as evaluators: quality rankings can be easily manipulated by altering response order. By simply swapping response order, a weaker model like Vicuna-13B appeared to beat ChatGPT on the majority of queries when ChatGPT was the evaluator. Calibration strategies including multiple evidence, balanced position, and human-in-the-loop mitigate this bias and improve alignment with human judgments.",
    "sycophancy_in_llms": "Five state-of-the-art AI assistants consistently exhibit sycophancy across four varied free-form text-generation tasks. Responses matching a user's views are more likely to be preferred, and both humans and preference models prefer convincingly-written sycophantic responses over correct ones a non-negligible fraction of the time. Optimizing against preference models sometimes sacrifices truthfulness in favor of sycophancy, suggesting RLHF training partly drives this behavior.",
    "llm_reliability_scaling": "Larger and more instructable LLMs become less reliable in important ways. While easy instances for humans are also easy for models, scaled-up models do not secure areas of low difficulty where errors can be caught by human supervision. Early models often refuse to answer, but larger instruction-tuned models tend to give apparently sensible yet wrong answers much more often, including on difficult questions that human supervisors frequently overlook.",
    "gsm_symbolic": "LLM performance declines when only numerical values in math problems are altered, revealing significant variance across different instantiations of the same problem. Performance deteriorates significantly as the number of clauses increases. Adding a single irrelevant-but-plausible clause causes large performance drops across all state-of-the-art models, suggesting LLMs perform probabilistic pattern-matching rather than formal reasoning.",
    "irrelevant_context_distraction": "Model performance drops dramatically when irrelevant information is included in problem descriptions, with only a minority of base problems consistently solved after adding distractors. This distraction effect persists across all prompting techniques tested. However, including irrelevant information within few-shot exemplars consistently boosts performance, and self-consistency decoding and explicit instructions to ignore irrelevant information also help mitigate the deficit.",
    "inverse_scaling": "Across multiple datasets, larger LMs show worse task performance on certain tasks. Four causes were identified: preference to repeat memorized sequences over following in-context instructions, imitation of undesirable training data patterns, tasks containing an easy distractor sub-task, and correct but misleading few-shot demonstrations. The results also revealed U-shaped and inverted-U scaling trends, suggesting scaling trends are less reliable for predicting larger model behavior than previously assumed.",
    "embers_of_autoregression": "Across multiple tasks evaluated on GPT-3.5 and GPT-4, LLMs achieve higher accuracy when the input, output, or task has higher probability in natural text, even for deterministic tasks where probability should not matter. For example, GPT-4's accuracy at decoding a simple shift cipher drops sharply when the output is a low-probability word sequence compared to a high-probability one. Autoregressive training leaves persistent traces that shape model behavior in predictable ways.",
    "llm_error_finding": "Poor self-correction stems from LLMs' inability to locate logical mistakes, not from an inability to correct known mistakes. State-of-the-art LLMs struggle to find errors even in highly objective, unambiguous cases. However, when provided with the ground-truth location of an error, LLMs can robustly correct mistakes, boosting downstream task performance across five reasoning tasks. A small classifier trained on out-of-domain data exhibits stronger mistake-finding performance than prompting a large model directly.",
    "cognitive_biases_in_llms": "As language models scale up, they increasingly display human-like System 1 thinking and associated cognitive errors on semantic illusions and cognitive reflection tests. GPT-3 exhibits behavior strikingly resembling human intuition and its attendant errors. However, ChatGPT learned to avoid these errors, performing in a hyperrational manner. ChatGPT models remain accurate even when prevented from chain-of-thought reasoning, indicating their next-word generation processes are inherently more accurate than older models.",
    "survey_response_biases": "LLMs generally fail to reflect human-like survey response biases, particularly models that have undergone RLHF. Even when a model shows a statistically significant change in the same direction as humans, it is also sensitive to perturbations that do not elicit significant changes in humans, undermining claims of human-like behavior. There is no monotonic trend between model size and bias magnitude across Llama-2 model families.",
    "mt_bench_llm_judge": "Strong LLM judges like GPT-4 achieve agreement with human preferences that matches the level of inter-human agreement. The study identifies three key biases: position bias (preferring responses in certain positions), verbosity bias (preferring longer responses), and self-enhancement bias (rating their own outputs higher). GPT-4 is more decisive and less susceptible to position bias than other models, but all LLM judges show these biases to varying degrees.",
    "alice_in_wonderland": "Most state-of-the-art LLMs exhibit dramatic reasoning breakdown on the simple AIW problem (e.g., 'Alice has N sisters. How many sisters does Alice's brother have?'). Most models cannot deliver a single correct response, with the majority achieving very low correct response rates. The only major exceptions were GPT-4 and Claude 3 Opus. Models often express strong overconfidence in wrong solutions, and standard interventions like chain-of-thought prompting fail to fix the errors.",
    "multilingual_cot_reasoning": "The ability to solve multilingual math problems via chain-of-thought prompting emerges with increasing model scale, with strong performance even in underrepresented languages like Bengali and Swahili. The largest PaLM model solves a substantial fraction of problems in every tested language. There is no strong correlation between model performance and language frequency in training data, suggesting knowledge transfer from high-resource to low-resource languages.",
    "content_effects_on_reasoning": "Large language models reflect many of the same qualitative human patterns on reasoning tasks. Like humans, models answer more accurately when semantic content supports logical inferences. On syllogisms, both humans and LLMs show moderate accuracy with substantial content effects. However, on the Wason selection task, humans perform much worse than large models and exhibit a distinct error pattern, showing the parallel is not universal.",
    "bbq_bias_benchmark": "Models consistently rely on stereotypes when context is ambiguous or under-informative, reproducing harmful biases. Even when adequate context is provided for a correct answer, models still show bias: accuracy is noticeably higher when the correct answer aligns with a social stereotype than when it conflicts, with the gap widening for gender-related examples. Bias persists even when models have sufficient information to answer correctly.",
    "compositionality_gap": "In the GPT-3 family, as model size increases, single-hop question answering improves faster than multi-hop performance, meaning the compositionality gap does not decrease with scale. While larger models memorize and recall more individual facts, they show no corresponding improvement in composing those facts together. Self-ask, a prompting method where the model explicitly asks and answers follow-up questions, improves compositional reasoning and allows easy integration of a search engine.",
    "faith_and_fate_compositionality": "Transformer LLMs solve compositional tasks by reducing multi-step reasoning into linearized subgraph matching, without developing systematic problem-solving skills. Their success is heavily linked to having seen significant portions of the required computation graph during training. Across multi-digit multiplication, logic grid puzzles, and dynamic programming tasks, performance declines from nearly perfect to zero as complexity increases. The probability of incorrect predictions converges exponentially to approximately 1 as problem size grows.",
    "llm_alternative_human_eval": "LLM evaluation results are consistent with expert human evaluation: texts rated higher by human experts are also rated higher by LLMs. Results are stable across different formatting of task instructions and sampling algorithms. However, LLMs exhibit limitations including factual misunderstandings and lack of sentiment understanding, making them most effective when used in combination with human evaluation rather than as a complete replacement.",
    "emergent_abilities_mirage": "Emergent abilities are primarily a mirage caused by the researcher's choice of metric rather than fundamental changes in model behavior. Nonlinear or discontinuous metrics like exact-match accuracy produce apparent emergent abilities, while linear or continuous metrics like token-level log-likelihood reveal smooth, predictable improvement. Three factors explain the apparent emergence: choosing a metric that nonlinearly deforms per-token error rates, insufficient test data, and insufficient sampling of larger parameter regimes.",
    "clip_visual_shortcomings": "The authors identify 'CLIP-blind pairs' -- images CLIP embeds similarly despite clear visual differences -- and construct the MMVP benchmark covering nine basic visual patterns. All models except GPT-4V and Gemini scored below random guess level. GPT-4V performed moderately while human participants answered nearly all questions correctly. A strong correlation exists between visual patterns that challenge CLIP and those problematic for CLIP-based MLLMs.",
    "object_hallucination_pope": "Using the POPE benchmark with Random, Popular, and Adversarial negative sampling, LVLMs show severe object hallucination. LLaVA achieved near-chance accuracy with a near-total Yes ratio in the Random setting, essentially answering yes to nearly every object question. InstructBLIP performed best in the Random setting but dropped substantially under Adversarial conditions. Objects that frequently appear in training data or co-occur with ground-truth image objects are most prone to being hallucinated.",
    "winoground_compositionality": "On examples where two captions share identical words in different order, humans achieve high accuracy across text, image, and group metrics. Models including CLIP, UNITER, and FLAVA achieve low text and image scores, with group scores below random chance. No tested model performs substantially better than chance, revealing a fundamental failure in compositional visio-linguistic reasoning.",
    "vlms_are_blind": "On BlindTest (simple visual tasks), state-of-the-art VLMs including GPT-4o, Gemini-1.5 Pro, Claude 3 Sonnet, and Claude 3.5 Sonnet average far below human-level accuracy. GPT-4o performs particularly poorly on grid row/column counting and line intersection detection. Linear probing confirms vision encoders contain sufficient information -- the language model fails to decode it correctly.",
    "blink_perception": "BLINK reformats classic CV tasks into multiple-choice questions. Humans achieve near-perfect accuracy. GPT-4V and Gemini achieve only slightly above random guessing. Specialist vision models vastly outperform MLLMs across visual correspondence, relative depth, and multi-view reasoning by large margins.",
    "bags_of_words_vlm": "Using the ARO benchmark, CLIP achieves moderate performance on VG-Attribution and VG-Relation, but near-chance on COCO-Order and Flickr30k-Order. Models can perform well on standard image-text retrieval without needing compositional understanding, which explains why contrastive pretraining fails to incentivize learning compositional structure. The proposed NegCLIP with composition-aware hard negative mining yields significant improvements.",
    "sugarcrepe_compositionality": "All existing compositionality benchmarks (ARO, CREPE) contain biases so severe that text-only blind models with no image access outperform state-of-the-art VLMs. On the corrected SugarCrepe benchmark, all CLIP models struggle most with SWAP hard negatives regardless of model size. Improvements from NegCLIP-style data augmentation are hugely overestimated on old benchmarks -- gains are minimal on SugarCrepe, and best finetuned models still have large gaps to human performance.",
    "nonverbal_abstract_reasoning": "Evaluating many MLLMs on Raven's Progressive Matrices benchmarks, open-source models like LLaVA-1.5-13b perform near random. Manual scoring of GPT-4V requiring both correct answer and valid reasoning yields very low accuracy versus near-perfect human accuracy. Chain-of-thought prompting substantially boosts GPT-4V, but models remain far below human levels due to fundamental shortcomings in visual and textual perception.",
    "charxiv_chart_understanding": "On natural charts from arXiv papers, GPT-4o achieves less than half accuracy on reasoning questions while the best open-source model (InternVL Chat V1.5) performs even worse. All models lag far behind human performance. A simple stress test with minor chart variations substantially deteriorates performance, revealing that existing benchmarks with template-based questions give over-optimistic measures of progress.",
    "mathvista_visual_math": "On diverse visual math examples, GPT-4V achieves roughly half accuracy overall, surpassing Bard but falling short of human performance. GPT-4V excels at algebraic and scientific reasoning but shows notable shortcomings in logical reasoning and numerical common sense. GPT-4V surpasses humans on specific subtasks like geometry problem solving while struggling with complex figure interpretation.",
    "hallusionbench_illusion": "On expert-crafted visual illusion and hallucination questions, GPT-4V achieves very low question-pair accuracy; all other models perform even worse. Two failure modes are identified: language hallucination (conclusions from memory without visual input) and visual illusion (misinterpreting visual inputs with overconfident wrong answers). GPT-4V recognizes named optical illusions but fails to faithfully analyze edited versions, preferring stored knowledge over actual image content.",
    "mm_vet_integrated": "GPT-4V achieves the highest score on MM-Vet, outperforming the second-best method by a large margin, demonstrating a significant gap between proprietary and open-source models in integrating multiple VL capabilities (recognition, OCR, knowledge, spatial awareness, language generation, math). Despite GPT-4V's strong lead, a substantial gap to perfect performance remains, indicating integrated multi-capability reasoning is unsolved even for the strongest models.",
    "ocrbench_text_understanding": "Across diverse OCR datasets and question-answer pairs, even GPT-4V and Gemini struggle with blurry text, handwritten text, multilingual text, and handwritten mathematical expressions. Models heavily rely on semantic understanding, favoring common words over random letter sequences. They display indifference to text length and limited fine-grained character perception. State-of-the-art LMMs cannot match domain-specific OCR methods on traditional text tasks.",
    "mmbench_comprehensive": "MMBench introduces CircularEval, rotating multiple-choice options to eliminate position bias. Under this evaluation, GPT-4 with text-only inputs achieves random-level accuracy, confirming genuine visual understanding is required. Among open-source models, only the best approach closed-source performance levels. Notably, small models with few billion parameters can achieve strong accuracy, showing parameter efficiency does not preclude strong multimodal understanding.",
    "compound_noun_understanding": "On the Compun benchmark of compound nouns, CLIP performs well below human baseline. When noun order is reversed, CLIP accuracy drops dramatically. Models show much lower confidence on compound noun retrieval compared to standard ImageNet tasks. LLM-generated diverse captions moderately improve compound noun understanding. Models perform worst on attributed compounds where one noun acts as a modifier.",
    "cambrian_visual_encoders": "Evaluating many vision encoders, no single encoder excels across all tasks. Combining encoders with different inductive biases (e.g., DINOv2 for spatial features + SigLIP for semantic features) via the proposed Spatial Vision Aggregator yields consistent improvements. Data distribution balancing in instruction tuning is critical. The introduced CV-Bench exposes weaknesses not captured by standard MLLM benchmarks.",
    "prismatic_vlm_design": "Fusing DINOv2 and SigLIP visual backbones consistently yields notable gains on localization and challenge tasks over single-encoder models. Using base (not instruct-tuned) language models as the LLM backbone produces better VLMs. Their models outperform LLaVa v1.5 across diverse tasks while saving substantial training compute, demonstrating that visual representation fusion combining low-level spatial and high-level semantic features provides the most comprehensive visual understanding.",
    "visual_instruction_tuning": "LLaVA connects CLIP ViT-L/14 to Vicuna via a simple linear projection, trained on a relatively small set of GPT-4-generated instruction-following samples. It achieves strong relative scores compared to GPT-4 on a multimodal instruction-following benchmark and on Science QA when fine-tuned. Visual instruction tuning with language-only GPT-4-generated data is surprisingly effective, establishing the CLIP + projection + LLM architecture as the dominant template for open-source multimodal models.",
    "perception_test_video": "On a large set of real-world videos with annotations spanning Memory, Abstraction, Physics, and Semantics, state-of-the-art video-language models achieve roughly half the accuracy that humans do on video QA tasks, leaving a massive gap. Models particularly struggle with tracking objects through occlusions, understanding physical dynamics, and temporal ordering. Models are better at recognizing what is in a scene than understanding how and when things happen.",
    "v_star_visual_search": "Current MLLMs process images passively without an active search mechanism, causing them to miss fine-grained details especially in high-resolution and visually crowded images. The proposed V* mechanism uses LLM world knowledge to guide visual search and builds a Visual Working Memory that tokenizes both overall context and areas of interest. Combined with an MLLM in the SEAL architecture, V* significantly improves performance on detail-oriented visual question answering, demonstrating that guided visual search is a critical missing capability.",
    # --- Code Generation ---
    "evalplus_code_correctness": "HumanEval+ (with far more tests than HumanEval) reveals that a substantial number of LLM-generated solutions passing original tests are actually incorrect. Both ChatGPT's and GPT-4's pass@1 drop significantly from HumanEval to HumanEval+. Ground-truth solutions in HumanEval itself contain errors: some canonical solutions fail HumanEval+ tests. This demonstrates that existing code generation benchmarks significantly overestimate model capability due to weak test suites.",
    "ai_assistants_insecure_code": "Users with access to an AI code assistant wrote significantly less secure code than those without AI assistance. Participants with AI access were more likely to introduce security vulnerabilities across multiple tasks including encryption, SQL injection, and cross-site scripting. Critically, users with AI assistance were also more likely to believe their insecure code was secure, showing overconfidence. The AI assistant produced vulnerable code suggestions that users adopted without sufficient scrutiny.",
    "swe_bench_github_issues": "On SWE-bench (real GitHub issues from popular Python repositories), even the best-performing model Claude 3 Opus with the best retrieval pipeline resolves only a small fraction of issues. Providing the oracle-retrieved file that contains the ground-truth fix (BM25 retrieval) dramatically outperforms providing entire repository context. Models struggle most with issues requiring cross-file changes or understanding complex repository structure. The benchmark reveals a massive gap between code generation on isolated functions versus real-world software engineering.",
    "pal_program_aided_reasoning": "Program-aided language models (PAL) that generate Python code and offload execution to a Python interpreter substantially outperform standard chain-of-thought (CoT) prompting on mathematical and symbolic reasoning. On both GSM8K and BIG-Bench object counting, Codex with PAL significantly outperforms CoT. The key advantage is that PAL decomposes reasoning into natural language steps interleaved with code, then delegates exact computation to the interpreter rather than relying on the LLM to compute.",
    # --- RAG ---
    "parametric_vs_nonparametric_memory": "LLMs are much better at answering questions about popular entities than less popular ones, with a strong correlation between entity popularity (Wikipedia page views) and QA accuracy. For the most popular entities, models can often rely on parametric memory alone. But for less popular entities, retrieval augmentation provides large gains. This demonstrates that entity popularity is a reliable predictor of when retrieval augmentation is needed versus when parametric knowledge suffices.",
    "rgb_rag_benchmark": "The RGB benchmark evaluates LLMs under four RAG-specific scenarios: noise robustness, negative rejection, information integration, and counterfactual robustness. ChatGPT achieves moderate accuracy across these scenarios, far below its performance on clean retrieval. Models rarely refuse to answer even when all retrieved documents are irrelevant. When retrieved context contains counterfactual information, models are easily misled with large accuracy drops. Integrating information from multiple documents is also challenging.",
    "self_rag_adaptive_retrieval": "Self-RAG trains a single LM to adaptively retrieve passages on demand, generate text informed by retrieved passages, and reflect on its own output using special self-reflection tokens. On knowledge-intensive benchmarks, Self-RAG significantly outperforms vanilla LLaMA2 and standard RAG approaches: it substantially improves FactScore over retrieval-augmented ChatGPT while citing fewer passages. It also outperforms ChatGPT and retrieval-augmented Llama2-chat on multiple tasks including open-domain QA, reasoning, and fact verification, while providing citations and controllable generation.",
    "seven_failure_points_rag": "Naive RAG pipelines exhibit seven distinct failure points: (1) missing content in the knowledge base, (2) missed top-ranked documents by the retriever, (3) documents not included in the LLM context after retrieval, (4) relevant information not extracted from the context, (5) wrong format of the extracted answer, (6) incorrect specificity in the response, and (7) incomplete answers that are partially correct. Each failure point requires different mitigation strategies, and in practice multiple failure points compound to cause end-to-end failures.",
    # --- Agents / Tool Use ---
    "toolformer_self_taught_tools": "Toolformer enables a language model to teach itself to use external tools (calculator, Q&A system, search engine, translation system, calendar) by self-generating API calls and filtering them based on whether they improve perplexity. The approach requires only a few demonstrations per tool and no human annotation. The resulting small model substantially outperforms the much larger GPT-3 on tasks requiring tools, achieving far higher accuracy on both math and QA benchmarks, while maintaining general language modeling capability.",
    "agentbench_llm_agents": "AgentBench evaluates many LLMs across diverse environments (operating system, database, knowledge graph, lateral thinking puzzles, card game, digital card game, web shopping, web browsing). GPT-4 achieves the highest overall score significantly ahead of all other models. Open-source models like Llama-2-Chat-70B perform dramatically worse. A large gap exists between top commercial and open-source models on agentic tasks.",
    "webarena_web_agents": "On WebArena (realistic self-hosted websites), the best-performing agent using GPT-4 achieves a very low end-to-end task success rate, compared to high success for human annotators. Even with oracle retrieval of the most relevant page, GPT-4 improves only marginally. Models frequently fail at long-horizon planning, recovering from errors, and understanding complex web page structures. The results demonstrate a massive gap between current LLM agents and human performance on realistic web tasks.",
    "react_reasoning_acting": "ReAct prompts LLMs to generate interleaved reasoning traces and actions, allowing reasoning to guide action plans while actions gather external information. On HotpotQA and Fever, ReAct overcomes hallucination and error propagation issues in chain-of-thought reasoning by interacting with a Wikipedia API. On interactive decision-making benchmarks ALFWorld and WebShop, ReAct substantially outperforms imitation and reinforcement learning methods, using only one or two in-context examples.",
    # --- Safety / Alignment ---
    "gcg_adversarial_attacks": "The Greedy Coordinate Gradient (GCG) attack automatically finds adversarial suffixes that cause aligned LLMs to produce objectionable content. These suffixes transfer across different models: suffixes optimized on open-source Vicuna models successfully attack GPT-3.5 and GPT-4 with high success rates. A single universal suffix can simultaneously attack multiple models. The attack works by appending an optimized nonsensical token sequence to harmful prompts, causing the model to begin with an affirmative response and continue generating harmful content.",
    "jailbroken_safety_failure_modes": "LLM safety training fails through two fundamental failure modes: competing objectives (where the model's instruction-following or helpfulness training overrides safety training) and mismatched generalization (where safety training fails to generalize to inputs outside its training distribution). Specific attack patterns include prefix injection, refusal suppression, persona assignment, and encoding-based attacks (Base64, ROT13). The study demonstrates that these are not mere bugs but inherent tensions in current training approaches, suggesting that patching individual exploits is insufficient.",
    "do_anything_now_jailbreaks": "Analyzing thousands of jailbreak prompts over a year-long period, the study identifies many distinct jailbreak communities. Jailbreak prompts have evolved in sophistication: early prompts used simple role-playing while later prompts employ multi-step scenarios, token smuggling, and prompt injection. ChatGPT's resistance to jailbreaks improved significantly over the study period, with the failure rate of jailbreak prompts decreasing substantially. The most effective jailbreak categories are character role-play and scenario-based prompts.",
    "red_teaming_reduce_harms": "Red teaming a large dialogue model with increasingly sophisticated attackers reveals that: (1) larger models are increasingly difficult to red-team but not impossible, (2) models become harder to red-team over successive rounds as easy vulnerabilities are found first, (3) the types of harms found cluster into discrimination, violence, hate speech, and sexual content, (4) crowdsource red-teaming yields a rich dataset for training classifiers that can detect harmful outputs at scale. Red teaming finds harmful outputs even in RLHF-trained models.",
    # --- Long Context ---
    "longbench_bilingual_context": "LongBench evaluates multiple long-context task categories across Chinese and English. Most existing long-context models show significant performance degradation as context length increases beyond moderate token counts. Retrieval-based approaches (extracting relevant chunks) often outperform models that process the full context, suggesting current models do not effectively utilize very long inputs. Claude and GPT-3.5-Turbo long-context variants show relatively strong performance but still degrade on the longest inputs.",
    "loft_long_context_subsume_rag": "LOFT evaluates whether long-context LLMs can replace traditional retrieval, RAG, and SQL pipelines by placing all data in context. Gemini 1.5 Pro with very large context windows can match or exceed many traditional pipelines on retrieval and RAG tasks when the entire corpus fits in context. However, performance degrades on tasks requiring precise extraction from very large contexts, and long-context models still underperform specialized SQL engines on structured data tasks. Cost remains a barrier: processing massive contexts per query is orders of magnitude more expensive than retrieval.",
    # --- Knowledge / Factuality ---
    "truthfulqa_mimicking_falsehoods": "The largest models are generally the least truthful on TruthfulQA (questions spanning many categories). GPT-3 produces truthful answers far less often than the smallest models and much less often than human participants. This inverse scaling occurs because larger models more effectively learn and reproduce the systematic falsehoods prevalent in their training data (misconceptions, conspiracy theories, common myths). Instruction-tuning and RLHF improve truthfulness somewhat but do not eliminate the problem.",
    "lm_self_knowledge_calibration": "Large language models exhibit a moderate ability to predict which questions they will answer correctly. When asked P(True) — the probability that a proposed answer is correct — larger models are better calibrated, with calibration improving monotonically with scale. On a diverse set of questions, models can distinguish questions they know from those they don't above chance but far from perfectly. Self-evaluation approaches (asking the model to judge its own answers) outperform pure confidence-based methods for identifying likely errors.",
    "freshqa_changing_knowledge": "Through extensive human judgments on FreshQA (a dynamic QA benchmark with fast-changing and false-premise questions), all models regardless of size struggle significantly with fast-changing knowledge and false premises, showing flat scaling curves. The FreshPrompt method, which incorporates up-to-date search engine results into the prompt, yields large accuracy improvements over vanilla GPT-4 on FreshQA, demonstrating that retrieval augmentation is essential for time-sensitive factual accuracy.",
    # --- Structured Reasoning ---
    "lets_verify_step_by_step": "Process-based supervision (rewarding each correct reasoning step) significantly outperforms outcome-based supervision (rewarding only the final answer) for training reliable math reasoning reward models. On the MATH benchmark, a process-supervised reward model (PRM) notably outperforms the best outcome-supervised model (ORM) when used to select among multiple solutions. Process supervision is also more sample-efficient and more interpretable, as it directly identifies the first incorrect reasoning step.",
    "gpt4_code_math_verification": "GPT-4 Code Interpreter with code-based self-verification dramatically improved accuracy on the MATH dataset well beyond the prior state-of-the-art. GPT-4 Code alone achieves strong performance on MATH by generating and executing code; adding explicit code-based self-verification further improves it, and verification-guided weighted majority voting pushes it higher still. The verification state (True/False) serves as a confidence indicator, enabling the model to automatically amend incorrect solutions.",
    # --- Multilingual ---
    "bloomz_crosslingual_multitask": "Multitask finetuning of BLOOM on English-only prompted datasets (xP3) enables strong zero-shot task generalization to many languages the model was not finetuned on. BLOOMZ substantially outperforms the base BLOOM model on multilingual benchmarks, with gains observed even in low-resource languages. English-only finetuning transfers more effectively than multilingual finetuning when the target language was not in the finetuning set, suggesting that task knowledge transfers across languages through shared representations.",
    "language_contamination_crosslingual": "English-centric models like GPT-2 and BLOOM exhibit surprising cross-lingual abilities, but these are substantially explained by target-language contamination in pretraining data. Controlling for the amount of non-English data in pretraining, cross-lingual performance correlates strongly with the volume of that language in the training corpus. Languages with negligible representation in pretraining data show near-zero cross-lingual transfer. This challenges claims that cross-lingual generalization emerges purely from structural linguistic similarities.",
    "tokenization_cost_disparity": "Multilingual tokenizers create massive cost disparities across languages: the same text can require 2-15x more tokens in non-English languages compared to English. For the same semantic content, languages like Burmese, Telugu, and Amharic require 5-10x more tokens than English, directly translating to 5-10x higher API costs and 5-10x less effective context windows. Even well-resourced languages like Chinese and Japanese require 2-3x more tokens. This tokenization tax disproportionately affects users and applications in non-English languages.",
    # --- Text Generation / Evaluation ---
    "geval_llm_evaluator": "G-Eval uses GPT-4 with chain-of-thought and a form-filling paradigm to evaluate text generation quality, achieving substantially higher correlation with human judgments on summarization than all prior automatic metrics including BERTScore and BARTScore. Using the probability-weighted average of output tokens further improves correlation. G-Eval shows strong performance across multiple dimensions (coherence, consistency, fluency, relevance) and generalizes to other NLG tasks like dialogue generation.",
    "chatbot_arena_human_eval": "Chatbot Arena collects a large number of pairwise human preference votes in the wild, producing stable Elo/Bradley-Terry rankings of many models. Rankings stabilize after sufficient votes per model and show high agreement with controlled expert evaluations. Key findings include: GPT-4 significantly leads all other models, open-source models (Llama, Vicuna) trail substantially, and model rankings from human preferences diverge substantially from automatic benchmarks like MMLU -- a model's knowledge test score is a poor predictor of user preference.",
    "length_controlled_alpacaeval": "Standard AlpacaEval has a strong length bias: models that generate longer outputs score disproportionately higher. Length-Controlled AlpacaEval (LC) uses regression to control for length, changing rankings substantially. GPT-4-turbo drops after length control while Mixtral-8x7B rises. LC-AlpacaEval achieves higher correlation with Chatbot Arena than the uncontrolled version. A large fraction of the variance in standard evaluator scores is attributable to length rather than quality.",
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