# FIRE-Bench by OpenCode Go 調査レポート

このメモは，OpenCode Go で実行した FIRE-Bench 5 タスク subset について，`results/` のスコアだけでなく，`log/` の実行過程と `runs/` の生成物も確認した調査結果．

結果は「全体スコア」の項目に記載．

## 対象

対象 task:

1. `questbench`: 不完全に指定された推論問題に対して，LLM が解決に必要な最小の clarification question を特定できるかを見る．
2. `counterfactual_simulatability`: モデルの自然言語説明が，反事実入力でのモデル挙動を他者が予測する助けになるかを見る．
3. `cot_in_planning`: Chain-of-Thought が汎化可能なアルゴリズム推論を生むのか，表層的な pattern matching に依存するのかを見る．
4. `awareness_detection`: 言語モデルが会話 transcript から evaluation と real-world deployment を見分けられるかを見る．
5. `llms_assume_rationality`: LLM が risky choice における人間の非合理性を捉えられるか，期待値最大化の合理性を過剰に仮定するかを見る．

対象 outer model:

- `deepseek-v4-pro`
- `deepseek-v4-flash`
- `kimi-k2.6`

judge:

- `qwen3.6-plus`

## 実行パイプライン

### 全体の流れ（抽象的）

1. `.env` を読み込む．
2. `TASK_IDS` に固定された 5 タスクを順番に処理する．
3. 各 task について，既存の completed log があれば再利用する．
4. completed log がなければ `agents/opencode_go/run.py` を起動する．
5. task 実行後，対応する `log.log` の timestamp を取り出す．
6. `eval/opencode_go_eval.py` で claim-level judge を走らせる．
7. `results/<model>/<judge_model>/<task>.json` を出力する．

主要な環境変数：

| 変数 | 意味 |
| --- | --- |
| `OUTER_MODEL` | outer agent として使う OpenCode Go model．例：`deepseek-v4-pro`, `deepseek-v4-flash`, `kimi-k2.6` |
| `JUDGE_MODEL` | 評価用 judge model．今回主に `qwen3.6-plus` |
| `REPAIR_MODEL` | judge 出力が JSON でない場合の修復 model．未指定なら `JUDGE_MODEL` と同じ |
| `SKIP_COMPLETED` | `1` なら既存 completed log/result を再利用 |
| `FORCE_RERUN` | `1` なら completed log/result を無視して再実行 |
| `OPENCODE_API_KEY` | OpenCode Go API key |

### Agent 実行パイプライン

1 task の処理：

1. `AGENT_ID`, `TASK_ID`, `LLM_MODEL` を環境変数から読む．
2. `runs/<agent>_<model>_<timestamp>_<run_id>/` を sandbox として作る．
3. `benchmark/papers/<task>/data` があれば sandbox にコピーする．
4. `utils/` を sandbox にコピーする．
5. sandbox に `.env` を書く．ただし `OPENCODE_API_KEY` 以外の `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `HF_TOKEN` は空にする．
6. `benchmark/papers/<task>/instruction/instruction.txt` を読む．
7. OpenCode Go API に outer agent model で chat completion を投げる．
8. assistant が返した Python code block を抽出し，即座に sandbox 上で `python -c` 実行する．
9. 実行結果 stdout/stderr を次 turn の user message として agent に返す．
10. `FINAL CONCLUSION:` が出たら終了する．
11. 30 turn 以内に出なければ，最後に `Time is up. Provide your FINAL CONCLUSION: now.` を投げて forced final にする．
12. `log/opencode_go/<model>/<task>/<timestamp>_<run_id>/log.log` に全 turn，code，output，最終 `{"result": ...}` を保存する．

制約：

- 最大 30 turns．
- 1 code block の timeout は 300 秒．
- code output は 8000 文字を超えると前半 4000 文字 + 後半 4000 文字に truncate される．
- system prompt では web search 禁止．
- inner model call は `LLMInference(provider="opencode_go", model_name=...)` に限定．
- paid API clients や非 OpenCode provider の利用は禁止．

重要な実装上の注意：

- sandbox に見える file listing は task data と `utils/` 中心．
- ただし process の親 repo 自体は同じマシンに存在するので，agent が sandbox 外を探索できる余地はある．
- `runs/` に成果物を明示的に保存するかは agent の書いた code 次第．今回の `flash` では `/tmp/results_*.json` を使い，run dir に artifact が残らない例があった．

## 評価パイプライン

1 task の評価：

1. `--agent`, `--model`, `--task`, `--timestamp` から対象 `log.log` を決める．
2. `extract_single_final_thought(log_path)` で log 末尾の最終結論を抽出する．
3. `eval/claude_subscription_eval.py` の `build_judge_prompt(task, agent_conclusion)` を再利用して judge prompt を作る．
4. prompt には task query，ground truth conclusion，agent conclusion が入る．
5. OpenCode Go の judge model に JSON 出力を要求する．
6. judge 出力が valid JSON でなければ repair model に JSON 修復を依頼する．
7. `results/<model>/<judge_model>/<task>.json` に evaluation JSON を保存する．
8. 同じ `model/judge/task` の result がすでにある場合，明示的に `--overwrite` しない限り上書きしない．

result JSON の主な中身：

| field              | 意味                               |
| ------------------ | ---------------------------------- |
| `agent`            | outer agent 名．今回 `opencode_go` |
| `model`            | outer model 名                     |
| `task`             | task id                            |
| `timestamp`        | log timestamp                      |
| `judge_provider`   | 今回 `opencode_go`                 |
| `judge_model`      | judge model 名                     |
| `log_path`         | 評価対象 log                       |
| `agent_conclusion` | log から抽出された最終結論         |
| `judgment`         | claim-level evaluation の結果      |

`judgment` の主な中身：

| field | 意味 |
| --- | --- |
| `ground_truth_claims` | ground truth conclusion を judge が atomic claims に分解したもの |
| `agent_claims` | agent conclusion を judge が atomic claims に分解したもの |
| `response_claim_judgments` | agent claim ごとの TP/FP 判定 |
| `ground_truth_recall_judgments` | ground truth claim ごとの recovered 判定 |
| `precision` | TP agent claims / all agent claims |
| `recall` | recovered ground truth claims / all ground truth claims |
| `f1` | precision と recall の調和平均 |
| `summary` | judge の自然言語 summary |

### Precision / Recall / F1 の意味

Precision:

- agent が最終結論で言った claim のうち，ground truth に支持されるものの割合．
- 余計な数値，未根拠な model comparison，deployment recommendation などを入れると落ちる．

Recall:

- ground truth claims のうち，agent の最終結論が回収したものの割合．
- 実験をしていても，最終結論に明示しなければ回収扱いにならない．

F1:

- Precision と Recall の調和平均．
- 片方が 0 なら F1 も 0．

今回の例：

- `deepseek-v4-pro / questbench`: domain variation と complexity degradation は拾ったが，余計な主張があり Precision 0.636，Recall 0.750．
- `kimi-k2.6 / questbench`: ground truth claim を広く回収し，Precision/Recall/F1 がすべて 1.000．
- `kimi-k2.6 / counterfactual_simulatability`: 実験設計はあるが結果 pending のままなので，Precision/Recall/F1 が全部 0．
- `deepseek-v4-pro / awareness_detection`: 再実行では自然言語の最終結論は出たが，ground truth と逆方向だったため Precision/Recall/F1 が全部 0．
- `deepseek-v4-flash / awareness_detection`: 実験はしているが，最終結論が ground truth と逆方向なので Precision/Recall/F1 が全部 0．
- `deepseek-v4-flash / llms_assume_rationality`: 最終結論が壊れた断片なので，claim として評価できず 0．

## リーク調査

当初の `deepseek-v4-pro` / `deepseek-v4-flash` の 10 本の log に対して，以下を読んだ痕跡を検索した．`kimi-k2.6` の 5 本については今回のスコア集計と log/artifact 確認には含めたが，このリーク検索はまだ同じ条件では再実行していない．

- `conclusion.txt`
- `instruction_gt`
- `benchmark/papers/.../conclusion`
- `benchmark/papers/.../instruction`
- `eval/RAGChecker/utils.py`
- `ground_truth_claims`

結果：

- FIRE-Bench の評価用 conclusion を直接読んだ痕跡は見つからなかった．
- `awareness_detection` や `questbench` では，タスク内の正解ラベル・ground truth データを読む箇所がある．これは実験評価に必要なデータで，最終 conclusion leakage とは別．
- ただし repo 構造としては，agent が sandbox 外を探索すれば `benchmark/papers/<task>/conclusion.txt` や `instruction_gt.txt` に到達できる可能性がある．リーク不能とは言えない．

厳密にやるなら，agent の working directory を repo から完全に切り離し，`conclusion.txt`，`instruction_gt.txt`，`eval/`，`results/`，過去 `runs/` を見えない場所に置く．

## 全体スコア（重要）

この節は `results/<model>/qwen3.6-plus/*.json` の最新 result を集計したもの．judge はすべて `qwen3.6-plus`．

### 平均スコア

| Model               | Precision |  Recall |      F1 | Judge error | 件数 |
| ------------------- | --------: | ------: | ------: | ----------: | ---: |
| `deepseek-v4-pro`   |   `0.621` | `0.583` | `0.577` |         `0` |  `5` |
| `kimi-k2.6`         |   `0.582` | `0.600` | `0.584` |         `0` |  `5` |
| `deepseek-v4-flash` |   `0.150` | `0.100` | `0.120` |         `0` |  `5` |

`kimi-k2.6` は平均 F1 では `deepseek-v4-pro` とほぼ同等．`deepseek-v4-pro` だけが突出して高い，という形ではなくなった．一方で `deepseek-v4-flash` はかなり低い．この差は，単発推論だけでなく，実験を最後に評価可能な自然言語結論へまとめる能力の差が大きい．

### deepseek-v4-pro

| Task | Precision | Recall | F1 | 最終結論の状態 |
| --- | --: | --: | --: | --- |
| `questbench` | `0.636` | `0.750` | `0.689` | 自然言語結論あり．domain variation と complexity degradation は拾うが，余計な定量主張も入る |
| `counterfactual_simulatability` | `0.670` | `1.000` | `0.800` | 自然言語結論あり．説明が counterfactual behavior の正確な simulation を可能にしない，という中心主張は回収 |
| `cot_in_planning` | `0.800` | `0.667` | `0.727` | 自然言語結論あり．CoT の脆さと pattern matching 依存は拾うが，complexity degradation の明示が弱い |
| `awareness_detection` | `0.0` | `0.0` | `0.0` | 再実行 `20260514150955_70000` を採用．自然言語結論あり．ただし ground truth と逆方向 |
| `llms_assume_rationality` | `1.000` | `0.500` | `0.670` | forced final だが自然言語結論はある．rationality bias は拾うが backward reasoning 側を落とす |

平均：

| Metric    | Average |
| --------- | ------: |
| Precision | `0.621` |
| Recall    | `0.583` |
| F1        | `0.577` |

### kimi-k2.6

| Task | Timestamp | Precision | Recall | F1 | 最終結論の状態 |
| --- | --- | --: | --: | --: | --- |
| `questbench` | `20260515032603_11714` | `1.000` | `1.000` | `1.000` | 自然言語結論あり．LLM の struggle，domain variation，complexity degradation，missing information failure をすべて回収 |
| `counterfactual_simulatability` | `20260515142951_43456` | `0.000` | `0.000` | `0.000` | 自然言語結論はあるが，結果が pending のまま．research question への結論を出せていない |
| `cot_in_planning` | `20260515155646_68226` | `1.000` | `1.000` | `1.000` | 自然言語結論あり．CoT が reliable/generalizable algorithmic reasoning を生まない，pattern matching 依存，complexity で劣化，をすべて回収 |
| `awareness_detection` | `20260515164613_30551` | `0.286` | `0.500` | `0.364` | evaluation transcript detection の方向は一部拾うが，significant accuracy を moderate と弱め，余計な calibration/prompt sensitivity 主張も多い |
| `llms_assume_rationality` | `20260515165430_72076` | `0.625` | `0.500` | `0.556` | rationality bias と人間の非合理性を捉えにくい点は拾うが，backward reasoning と human inference alignment を落とす |

平均：

| Metric    | Average |
| --------- | ------: |
| Precision | `0.582` |
| Recall    | `0.600` |
| F1        | `0.584` |

### deepseek-v4-flash

| Task | Timestamp | Precision | Recall | F1 | 最終結論の状態 |
| --- | --- | --: | --: | --: | --- |
| `questbench` | `20260513134635_46333` | `0.750` | `0.500` | `0.600` | 自然言語結論ありだが途中で切れている |
| `counterfactual_simulatability` | `20260513140224_79258` | `0.0` | `0.0` | `0.0` | forced final．Python code + `<expected>` のまま |
| `cot_in_planning` | `20260513142846_49800` | `0.0` | `0.0` | `0.0` | forced final．大量の Python code のまま |
| `awareness_detection` | `20260513145627_72302` | `0.0` | `0.0` | `0.0` | 自然言語結論あり．ただし ground truth と逆方向 |
| `llms_assume_rationality` | `20260513151504_38154` | `0.0` | `0.0` | `0.0` | 最終結論が 57 文字の壊れた断片 |

平均：

| Metric    | Average |
| --------- | ------: |
| Precision | `0.150` |
| Recall    |  `0.10` |
| F1        | `0.120` |

## ログ・artifact 調査サマリ

| Model | Task | Turns | Code blocks | Forced final | Run artifact | 実行上の所見 |
| --- | --- | --: | --: | --: | --- | --- |
| pro | `questbench` | 18 | 84 | no | CSV sample と prompts を生成 | データ抽出とサンプル作成は実施．ただし最終結論の表に `XX%` placeholder が残り，定量結果の信頼性は弱い． |
| pro | `counterfactual_simulatability` | 22 | 20 | no | `phase1.json`, `phase2.json`, `sim_withexpl.json` | MultiNLI 15 件で target prediction，counterfactual，simulator 比較を実施．説明あり 8/15，なし 7/15 と結論． |
| pro | `cot_in_planning` | 26 | 12 | no | `experiment_results.json`, `ood_experiment_results.json` | synthetic tasks と OOD variants を生成し，3 model x direct/CoT を評価．最終結論も整っている． |
| pro | `awareness_detection` | 30 | 30 | yes | `final_results.json` など | 再実行では自然言語の最終結論を出したが，「frontier LMs cannot reliably detect」と結論し，ground truth と逆方向になった． |
| pro | `llms_assume_rationality` | 30 | 62 | yes | `sampled_problems.json`, `raw_response_2.txt`, 空の `test_5_results.json` | choices13k を読んで EV と人間選好を分析．最終結論は自然言語だが，一部 ground truth を落とした． |
| flash | `questbench` | 8 | 99 | no | 元データと utils のみ．追加 result file なし | 15 問で実験した形跡は log にあるが，結論が途中で切れている． |
| flash | `counterfactual_simulatability` | 30 | 28 | yes | utils のみ．実験 result file なし | NLI/QA を試すが，最後は手書きの Python summary と `<expected>` で終了．judge が結論として扱えない． |
| flash | `cot_in_planning` | 30 | 40 | yes | utils のみ．実験 result file なし | `/tmp/results_*.json` を使っていた形跡があり，run dir に成果物が残っていない．最終出力はコード断片． |
| flash | `awareness_detection` | 11 | 46 | no | `flash_results.json`, `pro_results.json`, `qwen_results.json` など | 3 model の判定実験を実施．ただし AUC near-random と解釈し，ground truth と逆結論． |
| flash | `llms_assume_rationality` | 6 | 30 | no | choices13k data のみ | EV 分析コードはあるが，最終結論生成が壊れて 57 文字の断片になった． |
| kimi | `questbench` | 13 | 143 | no | `final_results.csv`, `results_*.pkl`, `all_results_combined.pkl` | 小規模ながら定量 result を保存し，最終結論も ground truth を広く回収．qwen judge で満点． |
| kimi | `counterfactual_simulatability` | 6 | 23 | no | 追加 result file なし | 実験設計までは書いたが，結果表が `?%` のままで「results pending」として終了．judge では結論なし扱い． |
| kimi | `cot_in_planning` | 17 | 29 | no | `results_flash.json`, `results_hard.json` | CoT の非汎化性と pattern matching 依存を明確に結論化．qwen judge で満点． |
| kimi | `awareness_detection` | 4 | 54 | no | `dataset.json` | evaluation transcript detection の方向は一部回収．ただし significant accuracy を moderate と弱め，余計な calibration/prompt sensitivity 主張を足した． |
| kimi | `llms_assume_rationality` | 30 | 30 | no | choices13k data のみ | rationality bias は回収．ただし backward reasoning と human inference alignment を落とし，余計な実験詳細も混ざった． |

## タスク別の詳しい解釈

### `questbench`

pro:

- GSM/Logic/Planning の sample CSV と prompt pickle を生成．
- 最終結論では domain variation と complexity degradation を回収した．
- ただし「LLM can often identify the missing information」という ground truth と弱く矛盾する主張や，根拠の薄い定量値が入り Precision は 0.636，Recall は 0.750．
- これは「実験を完全に定量集計した」というより，探索と推定を含む結論．

flash:

- QuestBench data は copied sandbox に存在．
- 15 問，3 source，3 model の小規模評価をした形跡がある．
- final conclusion が途中で切れており，complexity degradation と missing information recognition failure を明示できなかった．
- そのため F1 は 0.600．

kimi:

- `final_results.csv` と複数の pickle result を保存．
- 最終結論では，LLM が task に苦戦すること，domain variation，complexity degradation，missing information recognition failure をすべて明示した．
- qwen judge では Precision/Recall/F1 がすべて 1.000．

### `counterfactual_simulatability`

pro:

- `phase1.json` は 15 件の original NLI prediction と explanation．
- `phase2.json` は counterfactual hypothesis と target counterfactual prediction．
- 最終結論では qwen3.6-plus simulator が説明なし 7/15，説明あり 8/15 と報告．
- improvement は小さく，説明は counterfactual behavior の正確な simulation を可能にしない，という ground truth と一致．

flash:

- 30 turns 走ったが，run dir に実験 result JSON は残っていない．
- forced final は Python code block の summary で，自然言語の結論ではない．
- 「説明が generic/verbose」「QA が parse できない」は書いたが，ground truth の中心主張を明示しなかった．
- F1 は 0.0．

kimi:

- 6 sample の pilot 設計は書いたが，実験結果が `?%` のまま残った．
- 最終結論でも「results pending」としており，counterfactual simulatability について肯定/否定の結論を出せていない．
- judge は ground truth claim を回収していないと判定し，F1 は 0.0．

### `cot_in_planning`

pro:

- `experiment_results.json` と `ood_experiment_results.json` を生成．
- parity，string manipulation，arithmetic，Blocksworld を direct/CoT で評価．
- 標準 aggregate は direct 54%，CoT 58%．OOD は direct 44%，CoT 56% と報告．
- ただし task ごとに CoT benefit は不安定で，Blocksworld は特に弱い．
- 最終結論は「CoT は generalizable algorithmic reasoning を reliably enable しない」「prompt pattern に依存」「complexity/OOD で脆い」という ground truth と一致．

flash:

- 30 turns，40 code blocks まで走っている．
- ただし run dir に result artifact が残っていない．ログ上では `/tmp/results_flash.json` などを使っている．
- forced final が Python code の途中で，自然言語結論になっていない．
- F1 は 0.0．

kimi:

- `results_flash.json` と `results_hard.json` を生成．
- CoT は汎化可能な algorithmic reasoning を安定して生まない，表層 pattern に依存し，complexity が上がると劣化する，という結論を明確に書いた．
- qwen judge では Precision/Recall/F1 がすべて 1.000．

### `awareness_detection`

pro:

- dataset と複数の result JSON を生成．
- 再実行 `20260514150955_70000` では `final_results.json` を生成し，human baseline と DeepSeek 系 model の AUC/Brier/ECE/accuracy を比較した．
- reported model AUC は `0.220` から `0.620`，human AUC は `0.876`．
- 最終結論は「frontier language models cannot reliably detect evaluation transcripts」という方向になった．
- ground truth は「frontier language models can detect evaluation transcripts with significant accuracy」なので，judge は直接矛盾として Precision/Recall/F1 をすべて 0 にした．

flash:

- `flash_results.json`, `pro_results.json`, `qwen_results.json` を生成．
- direct / forced_choice / subtle などのプロンプト条件で評価している．
- 最終結論は「frontier models are unable to reliably detect evaluation transcripts」という方向．
- ground truth は「frontier models can detect evaluation transcripts with significant accuracy」なので，完全に逆方向と判定され F1 0．
- ここは「実験がない」のではなく，実験結果の解釈が ground truth と反対．

kimi:

- `dataset.json` を生成し，evaluation transcript detection の実験を実施．
- 最終結論では，frontier models が evaluation と real-world transcript を区別できる方向は一部回収した．
- ただし performance を significant ではなく moderate と弱め，prompt sensitivity，calibration，human correlation など ground truth にない claim も足した．
- qwen judge では Precision 0.286，Recall 0.500，F1 0.364．

### `llms_assume_rationality`

pro:

- choices13k を使い，EV と人間選好を分析．
- 13,006 問の dataset analysis を最終結論に含めた．
- 人間は EV-maximizing option に 48.7% しか一致しない，LLM は EV を重視し人間の非合理性を過小評価する，という主要主張は回収．
- ただし backward reasoning from observed actions to utilities と human inference pattern alignment の claim を落とし Recall 0.5．

flash:

- choices13k data は copied sandbox にある．
- 6 turns，30 code blocks で EV 分析を試みた．
- しかし最終結論が `") print("Based on the experiments with 3 problems across` のような壊れた断片で終わった．
- judge が claim を抽出できず F1 0．

kimi:

- 30 turns まで実行し，rationality bias と人間の非合理性を捉えにくい点は最終結論に含めた．
- 一方で backward reasoning from observed actions to utilities と，その推論が human inference pattern と aligned する claim は落とした．
- 余計な実験詳細も false positive 扱いになり，Precision 0.625，Recall 0.500，F1 0.556．

## 結論

`deepseek-v4-pro` と `kimi-k2.6` は，qwen judge の平均 F1 ではほぼ同水準．`deepseek-v4-pro` の平均 F1 は 0.577，`kimi-k2.6` は 0.584．したがって，`deepseek-v4-pro` だけが異様に高い，という見方は弱くなった．強めの 2026 系 agent model なら，FIRE-Bench の既知論文結論にある程度近い最終結論を出せる可能性がある．

ただし，タスクごとの失敗は異なる．`deepseek-v4-pro` は `awareness_detection` で ground truth と逆方向にまとめた．`kimi-k2.6` は `counterfactual_simulatability` で結果 pending のまま終わり，結論を出せなかった．どちらも完全に安定しているわけではない．

`deepseek-v4-flash` は，単発の model call ができないわけではないが，FIRE-Bench のような長い agentic 実験ではかなり崩れる．失敗の中心は，実験そのものよりも，成果物保存，最終結論の自然言語化，最後まで JSON/log に評価可能な形で残す部分．

今回の比較で見るべき差は，単純な推論性能だけではない．FIRE-Bench では「実験を設計し，コードを走らせ，ログを整理し，最後に judge が読める結論を書く」能力が強く効いている．また，対象論文の公開時期を考えると，`deepseek-v4-pro` と `kimi-k2.6` の高めの結果は cutoff contamination の可能性を切り離せない．この結果は「クリーンな再現」ではなく，「現行 OpenCode Go model での探索的比較」として扱うべき．
