# isitcredible vs one-shot on Williams et al. (2024): computed results

Generated 2026-11-10T20:26:16.228909+00:00 by `scripts/compare_isitcredible_williams.py summarize`. One paper; AI judges only. Coverage = share of reference (human) issues matched; overlap = share of the compared list's items that match a reference issue. Levels as in the v2 judge: strict = same concern; standard = also same concern at different scope; loose = also same target, different problem. Means over two replicates unless marked r1.

List sizes: isitcredible 11 issues (11 quotes verified); Nature referees 37 issues.

## strict

| Comparison | Claude judge (claude-opus-5-5, high) | GPT judge (gpt-5.6-terra, high, via Codex) |
|---|---|---|
| isitcredible review (SYNTHESIS): coverage of E1+E2 issues | 0.0% of 25 (reps [0.0, 0.0]) | 6.0% of 25 (reps [8.0, 4.0]) |
| Claude Opus 5.5, one-shot (condition A): coverage of E1+E2 issues | 6.0% of 25 (reps [4.0, 8.0]) | 24.0% of 25 (reps [16.0, 32.0]) |
| GPT-5.2 Pro, one-shot (focal run): coverage of E1+E2 issues | 16.0% of 25 (reps [12.0, 20.0]) | 26.0% of 25 (reps [24.0, 28.0]) |
| isitcredible review (SYNTHESIS): own items matching E1+E2 issues | 0.0% of 11 | 13.6% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items matching E1+E2 issues | 13.6% of 11 | 31.8% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items matching E1+E2 issues | 29.2% of 12 | 37.5% of 12 |
| isitcredible review (SYNTHESIS): coverage of curated list | 0.0% of 8 (reps [0.0, 0.0]) | 6.2% of 8 (reps [12.5, 0.0]) |
| Claude Opus 5.5, one-shot (condition A): coverage of curated list | 12.5% of 8 (reps [12.5, 12.5]) | 25.0% of 8 (reps [25.0, 25.0]) |
| GPT-5.2 Pro, one-shot (focal run): coverage of curated list | 12.5% of 8 (reps [12.5, 12.5]) | 25.0% of 8 (reps [25.0, 25.0]) |
| isitcredible review (SYNTHESIS): own items matching curated list | 0.0% of 11 | 4.5% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items matching curated list | 9.1% of 11 | 18.2% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items matching curated list | 8.3% of 12 | 16.7% of 12 |
| Human-human: E1 issues raised by E2 | 18.2% of 11 | 18.2% of 11 |
| Human-human: E2 issues raised by E1 | 21.4% of 14 | 10.7% of 14 |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams isit list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams opus list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams gpt list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Nature referees: E1+E2 issues they also raised | 4.0% of 25 | 12.0% of 25 |
| Nature referees r1: curated issues they also raised | 0.0% of 8 | 0.0% of 8 |
| isitcredible review (SYNTHESIS): own items repeating a Nature referee point | 50.0% of 11 | 31.8% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items repeating a Nature referee point | 27.3% of 11 | 27.3% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items repeating a Nature referee point | 41.7% of 12 | 41.7% of 12 |
| isitcredible review (SYNTHESIS): coverage (both reps) of the 20 E1+E2 issues no Nature referee raised (either judge) | 0 of 20 | 1 of 20 |
| Claude Opus 5.5, one-shot (condition A): coverage (both reps) of the 20 E1+E2 issues no Nature referee raised (either judge) | 1 of 20 | 2 of 20 |
| GPT-5.2 Pro, one-shot (focal run): coverage (both reps) of the 20 E1+E2 issues no Nature referee raised (either judge) | 3 of 20 | 4 of 20 |
| Human issues covered by isitcredible, not by Opus one-shot | 0: none | 0: none |
| Human issues covered by Opus one-shot, not by isitcredible | 1: E1::H03 | 1: E1::H03 |
| Covered by isitcredible, by neither one-shot | 0: none | 0: none |
| Covered by a one-shot, not by isitcredible | 3: E1::H03, E1::H06, E1::H10 | 3: E1::H03, E1::H04, E2::H13 |
| isitcredible review (SYNTHESIS): E1 / E2 issues covered (both reps) | E1 0/11, E2 0/14 | E1 0/11, E2 1/14 |
| Claude Opus 5.5, one-shot (condition A): E1 / E2 issues covered (both reps) | E1 1/11, E2 0/14 | E1 1/11, E2 1/14 |
| GPT-5.2 Pro, one-shot (focal run): E1 / E2 issues covered (both reps) | E1 3/11, E2 0/14 | E1 2/11, E2 2/14 |

## standard

| Comparison | Claude judge (claude-opus-5-5, high) | GPT judge (gpt-5.6-terra, high, via Codex) |
|---|---|---|
| isitcredible review (SYNTHESIS): coverage of E1+E2 issues | 2.0% of 25 (reps [4.0, 0.0]) | 12.0% of 25 (reps [12.0, 12.0]) |
| Claude Opus 5.5, one-shot (condition A): coverage of E1+E2 issues | 42.0% of 25 (reps [44.0, 40.0]) | 68.0% of 25 (reps [68.0, 68.0]) |
| GPT-5.2 Pro, one-shot (focal run): coverage of E1+E2 issues | 34.0% of 25 (reps [28.0, 40.0]) | 58.0% of 25 (reps [60.0, 56.0]) |
| isitcredible review (SYNTHESIS): own items matching E1+E2 issues | 4.5% of 11 | 27.3% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items matching E1+E2 issues | 40.9% of 11 | 54.5% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items matching E1+E2 issues | 37.5% of 12 | 58.3% of 12 |
| isitcredible review (SYNTHESIS): coverage of curated list | 0.0% of 8 (reps [0.0, 0.0]) | 6.2% of 8 (reps [12.5, 0.0]) |
| Claude Opus 5.5, one-shot (condition A): coverage of curated list | 25.0% of 8 (reps [25.0, 25.0]) | 37.5% of 8 (reps [37.5, 37.5]) |
| GPT-5.2 Pro, one-shot (focal run): coverage of curated list | 12.5% of 8 (reps [12.5, 12.5]) | 50.0% of 8 (reps [50.0, 50.0]) |
| isitcredible review (SYNTHESIS): own items matching curated list | 0.0% of 11 | 4.5% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items matching curated list | 18.2% of 11 | 27.3% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items matching curated list | 8.3% of 12 | 33.3% of 12 |
| Human-human: E1 issues raised by E2 | 31.8% of 11 | 40.9% of 11 |
| Human-human: E2 issues raised by E1 | 28.6% of 14 | 35.7% of 14 |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams isit list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams opus list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams gpt list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Nature referees: E1+E2 issues they also raised | 10.0% of 25 | 30.0% of 25 |
| Nature referees r1: curated issues they also raised | 0.0% of 8 | 0.0% of 8 |
| isitcredible review (SYNTHESIS): own items repeating a Nature referee point | 50.0% of 11 | 54.5% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items repeating a Nature referee point | 45.5% of 11 | 72.7% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items repeating a Nature referee point | 58.3% of 12 | 58.3% of 12 |
| isitcredible review (SYNTHESIS): coverage (both reps) of the 17 E1+E2 issues no Nature referee raised (either judge) | 0 of 17 | 1 of 17 |
| Claude Opus 5.5, one-shot (condition A): coverage (both reps) of the 17 E1+E2 issues no Nature referee raised (either judge) | 3 of 17 | 8 of 17 |
| GPT-5.2 Pro, one-shot (focal run): coverage (both reps) of the 17 E1+E2 issues no Nature referee raised (either judge) | 3 of 17 | 5 of 17 |
| Human issues covered by isitcredible, not by Opus one-shot | 0: none | 0: none |
| Human issues covered by Opus one-shot, not by isitcredible | 8: E1::H02, E1::H03, E1::H04, E1::H06, E1::H07, E1::H08, E1::H11, E2::H03 | 12: E1::H01, E1::H03, E1::H04, E1::H06, E1::H07, E1::H11, E2::H01, E2::H02, E2::H03, E2::H04, E2::H09, E2::H13 |
| Covered by isitcredible, by neither one-shot | 0: none | 0: none |
| Covered by a one-shot, not by isitcredible | 10: E1::H02, E1::H03, E1::H04, E1::H06, E1::H07, E1::H08, E1::H10, E1::H11, E2::H03, E2::H12 | 13: E1::H01, E1::H03, E1::H04, E1::H06, E1::H07, E1::H11, E2::H01, E2::H02, E2::H03, E2::H04, E2::H09, E2::H12, E2::H13 |
| isitcredible review (SYNTHESIS): E1 / E2 issues covered (both reps) | E1 0/11, E2 0/14 | E1 1/11, E2 1/14 |
| Claude Opus 5.5, one-shot (condition A): E1 / E2 issues covered (both reps) | E1 7/11, E2 2/14 | E1 8/11, E2 8/14 |
| GPT-5.2 Pro, one-shot (focal run): E1 / E2 issues covered (both reps) | E1 5/11, E2 2/14 | E1 7/11, E2 5/14 |

## loose

| Comparison | Claude judge (claude-opus-5-5, high) | GPT judge (gpt-5.6-terra, high, via Codex) |
|---|---|---|
| isitcredible review (SYNTHESIS): coverage of E1+E2 issues | 28.0% of 25 (reps [32.0, 24.0]) | 62.0% of 25 (reps [56.0, 68.0]) |
| Claude Opus 5.5, one-shot (condition A): coverage of E1+E2 issues | 58.0% of 25 (reps [56.0, 60.0]) | 82.0% of 25 (reps [72.0, 92.0]) |
| GPT-5.2 Pro, one-shot (focal run): coverage of E1+E2 issues | 68.0% of 25 (reps [52.0, 84.0]) | 86.0% of 25 (reps [96.0, 76.0]) |
| isitcredible review (SYNTHESIS): own items matching E1+E2 issues | 54.5% of 11 | 81.8% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items matching E1+E2 issues | 63.6% of 11 | 72.7% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items matching E1+E2 issues | 66.7% of 12 | 83.3% of 12 |
| isitcredible review (SYNTHESIS): coverage of curated list | 56.2% of 8 (reps [62.5, 50.0]) | 87.5% of 8 (reps [87.5, 87.5]) |
| Claude Opus 5.5, one-shot (condition A): coverage of curated list | 68.8% of 8 (reps [62.5, 75.0]) | 93.8% of 8 (reps [100.0, 87.5]) |
| GPT-5.2 Pro, one-shot (focal run): coverage of curated list | 68.8% of 8 (reps [75.0, 62.5]) | 93.8% of 8 (reps [87.5, 100.0]) |
| isitcredible review (SYNTHESIS): own items matching curated list | 36.4% of 11 | 81.8% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items matching curated list | 50.0% of 11 | 59.1% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items matching curated list | 45.8% of 12 | 70.8% of 12 |
| Human-human: E1 issues raised by E2 | 59.1% of 11 | 90.9% of 11 |
| Human-human: E2 issues raised by E1 | 35.7% of 14 | 64.3% of 14 |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams isit list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams opus list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Placebo r1: Chuard_et_al._2022 E1+E2 issues covered by Williams gpt list | 0.0% of 17 (same_study=no) | 0.0% of 17 (same_study=no) |
| Nature referees: E1+E2 issues they also raised | 18.0% of 25 | 70.0% of 25 |
| Nature referees r1: curated issues they also raised | 12.5% of 8 | 100.0% of 8 |
| isitcredible review (SYNTHESIS): own items repeating a Nature referee point | 59.1% of 11 | 77.3% of 11 |
| Claude Opus 5.5, one-shot (condition A): own items repeating a Nature referee point | 81.8% of 11 | 100.0% of 11 |
| GPT-5.2 Pro, one-shot (focal run): own items repeating a Nature referee point | 66.7% of 12 | 83.3% of 12 |
| isitcredible review (SYNTHESIS): coverage (both reps) of the 3 E1+E2 issues no Nature referee raised (either judge) | 0 of 3 | 1 of 3 |
| Claude Opus 5.5, one-shot (condition A): coverage (both reps) of the 3 E1+E2 issues no Nature referee raised (either judge) | 0 of 3 | 1 of 3 |
| GPT-5.2 Pro, one-shot (focal run): coverage (both reps) of the 3 E1+E2 issues no Nature referee raised (either judge) | 1 of 3 | 1 of 3 |
| Human issues covered by isitcredible, not by Opus one-shot | 0: none | 0: none |
| Human issues covered by Opus one-shot, not by isitcredible | 8: E1::H02, E1::H03, E1::H06, E1::H07, E1::H08, E1::H11, E2::H03, E2::H13 | 5: E1::H06, E1::H07, E1::H11, E2::H03, E2::H13 |
| Covered by isitcredible, by neither one-shot | 0: none | 0: none |
| Covered by a one-shot, not by isitcredible | 12: E1::H02, E1::H03, E1::H06, E1::H07, E1::H08, E1::H10, E1::H11, E2::H03, E2::H06, E2::H11, E2::H12, E2::H13 | 7: E1::H06, E1::H07, E1::H09, E1::H11, E2::H03, E2::H12, E2::H13 |
| isitcredible review (SYNTHESIS): E1 / E2 issues covered (both reps) | E1 2/11, E2 3/14 | E1 5/11, E2 9/14 |
| Claude Opus 5.5, one-shot (condition A): E1 / E2 issues covered (both reps) | E1 8/11, E2 5/14 | E1 9/11, E2 8/14 |
| GPT-5.2 Pro, one-shot (focal run): E1 / E2 issues covered (both reps) | E1 7/11, E2 6/14 | E1 9/11, E2 10/14 |

## Cost

Estimated API spend $1.857 over 57 calls: extract $0.006, judge_claude $1.844, judge_codex $0.000, normalize $0.006. GPT judge calls ran on the ChatGPT subscription.
